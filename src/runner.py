"""Runner — stateless orchestrator of the roleplay flow.

Each method loads/saves its own state. Does NOT have ``self.game`` or
``self.turn`` — local variables in each method, avoiding race conditions
between concurrent sessions.
"""

from __future__ import annotations

import asyncio
import copy
import re
import unicodedata
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from src.agents.character import CharacterOutput
from src.agents.character import act as character_act
from src.agents.narrator import (
    build_narrator_messages,
    narrate,
    redact_whisper_leaks,
)
from src.agents.narrator import (
    suggest_openings as narrator_suggest_openings,
)
from src.agents.perspective import (
    capture_memory,
    initialize_perspective,
    needs_identity_update,
    needs_memory_revision,
    revise_memory,
    update_identity,
)
from src.agents.prose import render_narration
from src.agents.suggest import suggest_moves
from src.agents.summarizer import summarize
from src.alignment import derive_alignment_impulse
from src.compaction import (
    CompactionDraft,
    CompactionProgress,
    CompactionStage,
    CompactionTrigger,
    ProgressSink,
    build_plugin_delta,
    canonical_hash,
    history_hash,
    invert_plugin_delta,
)
from src.confidentiality import hidden_whisper_tokens, redact_tokens
from src.disposition import (
    apply_gravity,
    appraise_relationships,
    integrate_appraisal,
)
from src.drive import evaluate_event_hazard, generate_event_seed
from src.llm.debug_log import (
    log_audible_speech_drop,
    log_burst,
    log_command_input,
    log_command_result,
    log_compact,
    log_compaction_status,
    log_drive_decision,
    log_effective_turn_input,
    log_presence_change,
    log_presence_undo,
    log_restore_compaction,
    log_roteiro_decision,
    log_scenario_contract_warning,
    log_session_setup_change,
    log_time_skip,
    log_turn_input,
    log_unanswered_player,
    log_undo,
)
from src.llm.tokens import estimate_prompt_tokens
from src.models import (
    CompactionStackEntry,
    GameState,
    Player,
    PresenceEditEntry,
    TurnRecord,
    default_present_characters,
    dict_to_disposition_state,
    dict_to_perspective,
    dict_to_roteiro,
    dict_to_turn_record,
    game_state_to_dict,
    perspective_to_dict,
    validate_present_characters,
)
from src.perception import (
    comparable_text,
    eligible_witnesses,
    render_events_for_viewer,
    repeats_event_text,
    similar_text,
)
from src.plugins.contracts import Hook
from src.plugins.runtime import PluginRuntime
from src.prompt_contract import operator_ontology_hits
from src.roteiro import (
    ReplanDecision,
    collect_beat_evidence,
    describe_roteiro_for_director,
    evaluate_roteiro,
    generate_roteiro,
    replan_roteiro,
)
from src.store.locks import session_lock
from src.store.sessions import (
    SessionNotFoundError,
    generate_session_id,
    load_compaction_checkpoint,
    load_game,
    next_compaction_id,
    save_game,
    write_compaction_checkpoint,
)
from src.watcher import (
    RUNG_ALLOW_SILENCE,
    RUNG_CAUSAL_DISRUPTION,
    LadderContext,
    audit_delta,
    generate_causal_intervention,
    select_recovery_step,
)

# Task 40 v2 — exact invite text validated by replay (position: hint channel).
CLOCK_SKIP_INVITE = (
    "CLOCK SIGNAL: the scene has produced no material change for 2 turns; "
    "only waiting remains. Compress time now (time_skip_ticks) unless "
    "someone is visibly mid-action."
)

# Multi-beat continuation (Task 45): how many opening beats of a burst keep the
# controlled character out of next_speakers so the world reacts before the story
# can pull the human back. Owner decision (2026-07-20): 2, so the return is not
# too fast. From this beat on, the protagonist is eligible again.
BURST_PROTAGONIST_EXCLUDE_BEATS = 2

# What a turn returns when not one beat produced anything to show.
_EMPTY_BEAT: dict[str, Any] = {
    "narration": "",
    "character_responses": [],
    "next_speakers": [],
    "scene_update": None,
    "turn_number": 0,
}

# An audible_speech event that near-repeats a line already in history is the
# Director re-voicing the scene, not a new fact. Persisting it doubles the
# record, feeds the repetition back as context, and teaches the model that
# restating counts as progress (task 54, finding 2). Same threshold the
# Character agent uses for its own echo guard, for the same reason.
_SPEECH_ECHO_THRESHOLD = 0.88
_SPEECH_ECHO_MIN_CHARS = 30
# Counted in TURNS, not records. A record window (it was 8) is a moving target:
# at a 21-character cast eight records is about one turn, and every one of the
# seven verbatim duplicates measured in session 20d4cdb3 sat 10-19 records back
# — three of them above the threshold, blocked only by the window being too
# short to see them. Turns are the unit the defect actually recurs in.
_SPEECH_ECHO_LOOKBACK_TURNS = 4


# Physical facts are durable, unbounded and never pruned: the only prune path
# clears them on a LOCATION change, and the Director reliably re-emits the
# identical location string, so it never fires. Measured on the battery runs, a
# 38-turn session accumulated 54 keys / 3169 chars of Director prompt, 10 of
# them near-synonym pairs (ceiling_crack / crack_in_ceiling / ceil_crack_widened)
# and 18 per-character transient state.
# A SAFETY VALVE, not the policy. The intake filters below are what actually
# bound the channel: replayed against the 38-turn session they refuse 63 keys and
# take the peak from 54 to 32. The cap only exists so pathological growth cannot
# run away. Sized above that observed peak on purpose — at 24 it evicted 8 facts
# that nothing else objected to, and eviction is dangerous here: dropping
# `main_doors: trancadas` is precisely what would let the Director seal the doors
# again, so a cap set too low causes the defect it is meant to help with.
_MAX_PHYSICAL_FACTS = 40
_FACT_SYNONYM_THRESHOLD = 0.75
# Per-character transient state. Where someone is standing belongs in
# zone_moves, how they feel in mood_updates; neither is a durable world fact,
# and writing them here is what filled a third of the budget.
_TRANSIENT_FACT_KEY = re.compile(r"_(action|position|stance|state|status)$")


def _canonical_fact_key(key: str) -> str:
    """A fact key reduced to its sorted word set.

    Compared raw, ``crack_in_ceiling`` and ``ceiling_crack`` score 0.48 — a
    character-level ratio cannot see word reordering, which is exactly how the
    Director spells the same fact twice. Sorting the words first takes that pair
    to 0.90 while pushing unrelated keys further APART (``main_doors`` vs
    ``crack_in_ceiling``: 0.31 raw, 0.15 canonical), so the separation improves
    in both directions.
    """
    return " ".join(sorted(comparable_text(key).replace("_", " ").split()))


def _fact_key_admissible(key: str, facts: dict[str, str]) -> bool:
    """Whether a new physical-fact key may join the scene.

    Rejects per-character transient state and near-synonyms of a key already
    present, so the same crack cannot be tracked under three names at once. An
    exact re-write of an existing key is always allowed: that is an UPDATE, and
    updating a fact is the whole point of the channel.

    Deliberately conservative. Refusing a genuinely new fact loses world state;
    admitting a near-duplicate only costs prompt budget, which the eviction cap
    already bounds. So borderline pairs are let through.
    """
    if key in facts:
        return True
    if _TRANSIENT_FACT_KEY.search(key):
        return False
    canonical = _canonical_fact_key(key)
    return not any(
        similar_text(canonical, _canonical_fact_key(existing)) > _FACT_SYNONYM_THRESHOLD
        for existing in facts
    )


def _evict_oldest_facts(facts: dict[str, str]) -> None:
    """Keep the fact budget bounded, dropping the least recently written first.

    Python dicts preserve insertion order and ``_update_scene`` re-inserts on
    every write, so iteration order is already least-recently-written first.
    """
    while len(facts) > _MAX_PHYSICAL_FACTS:
        facts.pop(next(iter(facts)))


def _echoes_recent_speech(game: GameState, subject: str, spoken: str) -> bool:
    """True when this line near-repeats recent speech by the same voice.

    "The same voice" includes the ``Player`` sentinel when the subject is the
    controlled character: the Director reformulating the human's own input as
    ``Link diz: ...`` is the exact duplication this guards against.

    Comparison runs on the frame-stripped payload (``comparable_text``): the
    Director re-voices a line wrapped in an attribution ("Lorde Cassian Aurel
    comenta em voz alta: '<line>'"), and that wrapper alone dropped raw
    similarity from 1.0 to 0.82-0.86 — under the threshold, so the duplicate was
    persisted as a fresh speech record and fed back through RECENT EVENTS every
    following turn (docs/cases/20-repetition-baseline-2026-08-01.md).
    """
    if len(spoken) < _SPEECH_ECHO_MIN_CHARS:
        return False
    voices = {subject}
    if subject == game.player.controlled_character_id:
        voices.add("Player")
    turns = sorted({record.turn_number for record in game.history})
    recent_turns = set(turns[-_SPEECH_ECHO_LOOKBACK_TURNS:])
    for record in game.history:
        if record.turn_number not in recent_turns:
            continue
        if record.content_type not in ("speech", "action") or record.speaker not in voices:
            continue
        if similar_text(spoken, record.content) >= _SPEECH_ECHO_THRESHOLD:
            return True
    return False


# Character ids are `C1`..`Cn` (`^C\d+$`). Matching the SHAPE only would refuse
# "C4" in a scenario where C4 is a plastic explosive rather than a student, so
# candidates are confirmed against this session's own cast.
_INTERNAL_ID_RE = re.compile(r"\bC\d+\b")


def _leaks_internal_id(game: GameState, spoken: str) -> bool:
    """True when the text carries a raw character id from this session's cast.

    `oldcode-P1-r1` T39 persisted *"C17 ordena que C20 permaneça com os
    estilhaços e que C18 a acompanhe"* — three ids in one line the player could
    read. Task 36 stripped ids from the prose and summarizer prompts, but the
    Director legitimately receives them (it routes by id) and this channel copies
    the Director's text into history verbatim, so it is the one path by which an
    id still reaches the reader.
    """
    return any(match.group() in game.characters for match in _INTERNAL_ID_RE.finditer(spoken))


# English vs Portuguese function words. Both lists exclude the tokens that exist
# in BOTH languages — "for" (English preposition / Portuguese subjunctive of
# *ser*), and "a", "as", "no", "do", "e" — because those collisions are what
# produced the only overlap between the two populations when this was measured.
_EN_MARKERS = frozenset(
    (
        "the", "and", "that", "with", "was", "were", "his", "her", "their", "they",
        "this", "there", "would", "could", "should", "which", "while", "from",
        "have", "has", "had", "been", "into", "about", "when", "what", "who",
        "will", "said", "says", "she", "he", "it", "of", "to", "in", "is", "are",
        "at", "on", "but", "not", "you", "your", "them", "then", "than",
    )
)  # fmt: skip
_PT_MARKERS = frozenset(
    (
        "que", "de", "da", "das", "dos", "não", "uma", "um", "para", "com", "por",
        "os", "se", "na", "nas", "nos", "ao", "aos", "ele", "ela", "eles", "elas",
        "seu", "sua", "seus", "suas", "mas", "como", "mais", "já", "ainda",
        "quando", "sobre", "pelo", "pela", "está", "estão", "é", "são", "foi",
        "ser", "ter", "tem", "isso", "essa", "esse", "esta", "este", "em", "o",
    )
)  # fmt: skip
_LANGUAGE_WORD_RE = re.compile(r"[a-zà-ÿ']+")
# Measured over all 3,936 speech/narration/action records in the 16 archived
# sessions: the two populations do not touch. The most English-looking Portuguese
# record scores 0.012 (one loanword in 263 words); the nine English records all
# score 1.000. The threshold sits in an empty band 82 times wider than it needs
# to be. Two markers is the floor because the shortest true positive carries
# exactly two ("Guard, report! What breached the wall?"), and of the 415 records
# with fewer than two markers none scores above the line anyway.
_LANGUAGE_FOREIGN_RATIO = 0.5
_LANGUAGE_MIN_MARKERS = 2


def _foreign_language(spoken: str, language: str) -> bool:
    """True when the text reads as English under a Portuguese-pinned session.

    `null-P1-r2` T2 emitted four `audible_speech` events in English — *"Asword
    said that Link's portal showed precise control…"* — and every one of them
    persisted. Across the whole archive **all nine** English records came through
    this channel: zero character replies and zero narration records ever flipped.

    Deliberately narrow. It answers "is this English in a Portuguese session",
    which is what was measured and the only flip the corpus contains; it is not a
    language identifier. Any other pinned language returns False rather than
    guessing, because the marker lists cannot separate a pair they were not built
    for (French *on* would read as English). Extending it means measuring the new
    pair first, the same way this one was.
    """
    if "portug" not in language.strip().lower():
        return False
    words = _LANGUAGE_WORD_RE.findall(spoken.lower())
    english = sum(1 for word in words if word in _EN_MARKERS)
    local = sum(1 for word in words if word in _PT_MARKERS)
    markers = english + local
    if markers < _LANGUAGE_MIN_MARKERS:
        return False
    return english / markers >= _LANGUAGE_FOREIGN_RATIO


def _is_own_speech_intent(event: dict[str, Any], viewer_id: str) -> bool:
    """True when this event is the viewer's OWN line to speak this turn."""
    return event.get("event_kind") == "audible_speech" and event.get("subject_id") == viewer_id


_INTENT_WORD_RE = re.compile(r"[a-zà-ÿ]+")
# Function words and the Director's reporting verbs. Left in, they make any two
# Portuguese sentences look related; the question here is whether the FACT
# survived, and a fact is carried by its content words.
_INTENT_STOPWORDS = frozenset(
    (
        "que", "de", "da", "das", "dos", "nao", "uma", "para", "com", "por", "os",
        "as", "se", "na", "no", "nas", "nos", "ao", "aos", "ele", "ela", "eles",
        "elas", "seu", "sua", "seus", "suas", "mas", "como", "mais", "ja", "ainda",
        "quando", "sobre", "pelo", "pela", "esta", "estao", "ser", "ter", "tem",
        "isso", "essa", "esse", "este", "em", "sao", "foi", "voz", "alta", "diz",
        "disse", "fala", "falou", "anuncia", "anunciou", "comenta", "comentou",
        "responde", "respondeu", "pergunta", "perguntou", "afirma", "declara",
        "ordena", "avisa", "todos", "todas",
    )
)  # fmt: skip
# The same instrument, at the same threshold, that measured this task's three
# populations against the archive (65 "⚠ 65a's premise did not survive
# verification"): shared content words over the smaller set. 0.5 was called
# there "a defensible reading" of restatement, and the reading is the same one
# here — did this sentence and that sentence carry the same fact.
_INTENT_CARRIED_RATIO = 0.5


def _intent_words(text: str) -> set[str]:
    folded = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in folded if unicodedata.category(c) != "Mn")
    return {
        word
        for word in _INTENT_WORD_RE.findall(stripped)
        if len(word) > 3 and word not in _INTENT_STOPWORDS
    }


def _carries_intent(spoken: str, intent: str) -> bool:
    """True when a character's line carries the fact the Director ruled aloud.

    Deliberately NOT a similarity score between two sentences. The character is
    told to rephrase, so wording is expected to diverge; what may not diverge is
    the fact. An intent with no content words of its own ("she speaks up") has
    nothing checkable in it and is treated as carried, because refusing it would
    send an empty fact down the degradation path forever.

    This is the one threshold in the task that could NOT be measured before
    shipping: it judges compliance with a prompt that did not exist until now,
    so the archive has no positives for it. It is calibrated at the checkpoint
    against `mandate_ignored` counts in ``debug.jsonl``, and the falsifier is
    written into the task.
    """
    wanted = _intent_words(intent)
    if not wanted:
        return True
    if not spoken.strip():
        return False
    shared = wanted & _intent_words(spoken)
    return len(shared) / len(wanted) >= _INTENT_CARRIED_RATIO


def _undo_anchor(game: GameState) -> tuple[int, dict[str, Any] | None]:
    """The clock and screenplay as they are right now, for this beat's records."""
    return game.narrative_tick, (asdict(game.roteiro) if game.roteiro is not None else None)


def _stamp_undo_anchor(
    game: GameState, step: int, anchor: tuple[int, dict[str, Any] | None]
) -> None:
    """Write the pre-beat clock and screenplay onto every record of this beat.

    Records are appended at different moments of a beat - the player's input
    before the Director runs, the narration after - so the anchor is stamped
    once, at commit, instead of being read from a moving ``game``.
    """
    tick, roteiro = anchor
    for record in reversed(game.history):
        if record.turn_number != step:
            break
        record.narrative_tick_snapshot = tick
        record.roteiro_snapshot = copy.deepcopy(roteiro)


def _current_turn(game: GameState) -> int:
    """The turn number an out-of-band event belongs to (0 before the first turn)."""
    return game.history[-1].turn_number if game.history else 0


def _next_turn_number(game: GameState) -> int:
    """The number every record and model call of the next step will share."""
    return (game.history[-1].turn_number + 1) if game.history else 1


def _adopt_state(target: GameState, source: GameState) -> None:
    """Copy every field of ``source`` into ``target``, in place.

    Used when a caller already holds a GameState reference that has to reflect
    state committed by another operation (compaction inside a running turn).
    Declared field by field, so adding a field to GameState cannot silently skip
    it the way mutating ``__dict__`` could.
    """
    for field_info in fields(GameState):
        setattr(target, field_info.name, copy.deepcopy(getattr(source, field_info.name)))


@dataclass(slots=True)
class TurnInput:
    """One submitted move, after the plugin filter and routing resolution.

    ``narrator_hint`` is the PENDING hint the first beat starts from; a burst's
    later beats resolve their own (see ``Runner._resolve_beat_hint``).
    """

    speech: str
    thought: str
    action: str
    force_speaker: str | None
    narrator_hint: str
    skip: bool
    audience: list[str] | None
    transformed_fields: list[str]
    # None when the requested speaker is absent or unknown: the Director routes.
    effective_force_speaker: str | None

    @property
    def effective_input(self) -> dict[str, str]:
        """What the frontend echoes back as the move that actually happened."""
        return {"speech": self.speech, "thought": self.thought, "action": self.action}


@dataclass(slots=True)
class BurstState:
    """Accumulators of one autonomous continuation (Task 37)."""

    beats: list[dict[str, Any]] = field(default_factory=list)
    # Event texts already told this burst, so a stimulus is resolved once.
    event_texts: list[str] = field(default_factory=list)
    narrator_only_streak: int = 0
    stop_reason: str = "budget_exhausted"


class PresenceRevisionConflictError(ValueError):
    """Raised by ``Runner.set_presence`` when the caller's revision is stale."""


class ConversationAlreadyStartedError(LookupError):
    """Raised when an opening-only operation reaches a session that has history."""


class Runner:
    """Stateless orchestrator. Each method loads/saves its own state."""

    def __init__(
        self,
        llm_client: httpx.AsyncClient,
        config: dict,
        plugins: PluginRuntime | None = None,
    ) -> None:
        self.client = llm_client
        self.config = config
        # An empty runtime is the null object: every hook call resolves to an
        # empty registration list, so no caller needs a "do I have plugins?"
        # branch. Only tests construct a Runner without one.
        self.plugins = plugins if plugins is not None else PluginRuntime()

    # ── Public Methods ────────────────────────────────────────────────────

    async def start_session(self, session_config: dict | None = None) -> str:
        """Creates GameState with default (or custom) characters, scene, and Player.

        No LLM call — only file writing and the session lifecycle hooks.

        Args:
            session_config: Optional. Can contain 'characters', 'scene',
                            'controlled_character_id', 'narrator_directives'
                            keys to customize.

        Returns:
            session_id (8-character string).

        Raises:
            ValueError: If there is not at least one character.
        """
        cfg = copy.deepcopy(session_config or {})
        cfg = await self.plugins.hooks.filter(Hook.SESSION_START, cfg, {"runner": self})
        session_id = generate_session_id()
        scenario_data: dict | None = None

        if "characters" not in cfg or "scene" not in cfg:
            from src.store.scenarios import list_builtin_scenarios, load_builtin_scenario

            defaults = list_builtin_scenarios()
            if defaults:
                scenario_data = load_builtin_scenario(defaults[0])

        if "characters" in cfg:
            characters = cfg["characters"]
            if not characters:
                raise ValueError("The session needs at least one character.")
        else:
            from src.models import dict_to_character

            if scenario_data is None:
                raise ValueError(
                    "The session needs at least one character, and no default scenario was found."
                )
            if not scenario_data or not scenario_data.get("character_preset_ids"):
                raise ValueError(
                    "The session needs at least one character, and the default "
                    "scenario is corrupted."
                )
            from src.store.presets import load_preset

            characters = {
                cid: dict_to_character(preset["character"])
                for cid, preset_name in scenario_data["character_preset_ids"].items()
                if (preset := load_preset(preset_name)) is not None
            }
            if len(characters) != len(scenario_data["character_preset_ids"]):
                raise ValueError("The default scenario links a missing character preset.")
        if "scene" in cfg:
            scene = cfg["scene"]
        elif scenario_data and "scene" in scenario_data:
            from src.models import Scene

            sdata = scenario_data["scene"]
            # The scenario's own present_characters only means anything paired with
            # its own characters. When the caller supplied custom characters but no
            # scene, borrowing this scene's location/time/facts is fine, but its
            # present_characters would reference IDs foreign to the caller's set —
            # leave it absent so the block below materializes the correct default.
            borrowed_present_characters = (
                list(sdata.get("present_characters", [])) if "characters" not in cfg else []
            )
            scene = Scene(
                location=sdata["location"],
                time_of_day=sdata["time_of_day"],
                present_characters=borrowed_present_characters,
                physical_facts=dict(sdata.get("physical_facts", {})),
            )
        else:
            raise ValueError("No default scene available.")

        # controlled_character_id must exist; otherwise, use the first character.
        controlled_id: str = cfg.get("controlled_character_id") or ""
        if controlled_id not in characters:
            controlled_id = next(iter(characters))

        player = Player(controlled_character_id=controlled_id)

        # present_characters is scene state, not derived registration state. An absent
        # value defaults to "everyone present"; a supplied value is validated, never
        # silently corrected.
        if scene.present_characters:
            scene.present_characters = validate_present_characters(
                scene.present_characters, characters, controlled_id
            )
        else:
            scene.present_characters = default_present_characters(characters)

        character_preset_ids = dict(
            cfg.get("character_preset_ids")
            or (
                (scenario_data or {}).get("character_preset_ids", {})
                if "characters" not in cfg
                else {}
            )
        )
        if set(character_preset_ids) - set(characters):
            raise ValueError("A preset can only be linked to a character in this session.")
        if len(set(character_preset_ids.values())) != len(character_preset_ids):
            raise ValueError("A character preset can only be linked once in a session.")
        if character_preset_ids:
            from src.store.presets import load_preset

            for preset_name in character_preset_ids.values():
                if load_preset(preset_name) is None:
                    raise ValueError(f"Character preset '{preset_name}' was not found.")

        game = GameState(
            session_id=session_id,
            characters=characters,
            player=player,
            scene=scene,
            created_at=datetime.now(UTC).isoformat(),
            narrator_directives=cfg.get("narrator_directives", ""),
            character_preset_ids=character_preset_ids,
            scenario_source_id=str(cfg.get("scenario_source_id", "")),
        )
        game = await self.plugins.hooks.filter(
            Hook.SESSION_BEFORE_COMMIT, game, {"kind": "start", "runner": self}
        )
        save_game(game)
        self._warn_on_directive_contract(game)
        await self.plugins.hooks.action(Hook.SESSION_AFTER_COMMIT, {"game": game, "kind": "start"})
        return session_id

    @staticmethod
    def _warn_on_directive_contract(game: GameState) -> None:
        """Record it when a scenario's own directives name the operator.

        `narrator_directives` reach the Director, the Historian, both suggestion
        paths and the Architect. A scenario that says "the player controls Link"
        therefore tells every one of them that a human exists — the thing
        AGENTS.md section 3 promises they never learn.

        Scenarios written by their owner are theirs. Rewriting somebody's
        narrative text behind their back would be worse than the leak, so this
        only writes the finding to the session log where the debug drawer and
        the tools can show it.
        """
        hits = operator_ontology_hits(game.narrator_directives)
        if hits:
            log_scenario_contract_warning(game.session_id, phrases=sorted(set(hits)))

    async def execute_command(
        self, session_id: str, command_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Run a plugin utility command under the session transaction lock.

        Commands receive an isolated state snapshot and cannot advance history,
        revision, or any narrative state.
        """
        from src.plugins.commands import CommandError

        registration = self.plugins.commands.get(command_name)
        if registration is None:
            raise CommandError("command_not_found", f"Command /{command_name} is not available.")

        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise CommandError("session_not_found", f"Session {session_id} was not found.")
            turn_number = (game.history[-1].turn_number + 1) if game.history else 1
            operation_id = uuid4().hex
            result_kind = registration.descriptor["result_kind"]
            log_command_input(
                session_id,
                turn_number,
                operation_id=operation_id,
                command=command_name,
                plugin_id=registration.plugin_id,
                plugin_version=registration.plugin_version,
                input_metadata=self.plugins.commands.log_metadata(payload),
            )
            try:
                result = await self.plugins.commands.invoke(
                    registration,
                    payload,
                    {
                        "game": copy.deepcopy(game),
                        "turn_number": turn_number,
                        "runner": self,
                        "operation_id": operation_id,
                    },
                )
            except BaseException as error:
                log_command_result(
                    session_id,
                    turn_number,
                    operation_id=operation_id,
                    command=command_name,
                    plugin_id=registration.plugin_id,
                    plugin_version=registration.plugin_version,
                    status="error",
                    result_kind=result_kind,
                    error_type=type(error).__name__,
                    error=str(error) or repr(error),
                )
                if isinstance(error, CommandError):
                    raise
                public_code = getattr(error, "code", None)
                if isinstance(public_code, str) and public_code:
                    public_field = getattr(error, "field", None)
                    raise CommandError(
                        public_code,
                        str(error) or "The command could not be completed.",
                        field=public_field if isinstance(public_field, str) else None,
                    ) from error
                raise
            log_command_result(
                session_id,
                turn_number,
                operation_id=operation_id,
                command=command_name,
                plugin_id=registration.plugin_id,
                plugin_version=registration.plugin_version,
                status="ok",
                result_kind=result_kind,
            )
            return {
                "status": "ok",
                "operation_id": operation_id,
                "command": command_name,
                "plugin_id": registration.plugin_id,
                "plugin_version": registration.plugin_version,
                "result_kind": result_kind,
                "result": result,
            }

    async def player_turn(
        self,
        session_id: str,
        speech: str = "",
        thought: str = "",
        action: str = "",
        force_speaker: str | None = None,
        narrator_hint: str = "",
        skip: bool = False,
        audience: list[str] | None = None,
    ) -> dict:
        """Processes a Player's turn.

        Flow:
        1. load_game + lock
        2. Persists the human's speech/thought/action in the history (marked "Player" internally,
           but never rendered this way in prompts — turns into the last entry of
           HISTORY read by the blind Narrator)
        3. Calls Narrator
        4. Records narration in history
        5. Who acts next is ``force_speaker`` (manual override, if provided)
           or the Narrator's ``next_speakers`` queue. Each present, non-controlled
           entry gets a character call in order, seeing the previous replies.
           The queue stops at the controlled character: control returns to the
           human and the runner never generates their speech.
        6. Updates scene and moods
        7. save_game → returns results

        Args:
            session_id: Session ID.
            speech: Player's audible speech.
            thought: Player character's private thought.
            action: Player's physical action.
            force_speaker: Manual trigger — ID of a present character or
                "Narrator", to force who acts next instead of letting the
                Narrator decide.
            audience: Optional whisper — character IDs that perceive this turn's
                speech/action (everyone else stays unaware). A character reply in
                the same turn inherits the audience when the speaker belongs to it.

        Returns:
            Dict with: narration, character_responses, next_speakers,
            scene_update, turn_number.
        """
        # One place decides what a valid submission is, for every caller: HTTP,
        # the playtest harness, the MCP tools and plugin code all land here.
        if skip:
            if speech.strip() or thought.strip() or action.strip():
                raise ValueError("skip cannot be combined with speech, thought, or action")
        elif not any(value.strip() for value in (speech, thought, action, narrator_hint)):
            raise ValueError("A turn needs speech, thought, action, narrator_hint, or skip")
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)

            # All records and model calls from this step share one number.
            step = _next_turn_number(game)
            turn = await self._resolve_turn_input(
                game,
                step,
                speech=speech,
                thought=thought,
                action=action,
                force_speaker=force_speaker,
                narrator_hint=narrator_hint,
                skip=skip,
                audience=self._validate_audience(game, audience, speech, action),
            )
            automatic_compaction = await self._maybe_automatic_compaction(game, turn, step)
            self._persist_player_input(game, turn, step)

            # Bounded autonomous burst (Task 37): on a bare skip turn the world
            # may play several beats before control returns. Each beat commits
            # as its OWN turn (undo pops one beat; a crash leaves only complete
            # beats). Stop conditions are deterministic; a manual force always
            # means exactly one beat.
            max_beats = 1
            if turn.skip and not turn.effective_force_speaker:
                max_beats = max(1, int(self.config.get("autonomous_burst_max_beats", 1)))
            burst = BurstState()
            pending_hint = turn.narrator_hint
            for beat_index in range(max_beats):
                if beat_index:
                    step = _next_turn_number(game)
                # Captured before the roteiro can be replanned and before the
                # clock advances, so undoing this beat restores the world the
                # player acted in. Each beat commits as its own turn, so each
                # one carries its own anchor.
                beat_anchor = _undo_anchor(game)

                hint, injected_event, hint_is_control = await self._resolve_beat_hint(
                    game, step, beat_index, turn, pending_hint
                )
                narrator_raw = await self._director_beat(
                    game,
                    step,
                    turn,
                    beat_index,
                    hint,
                    multi_beat=max_beats > 1,
                    burst=burst,
                    hint_is_control=hint_is_control,
                )

                # A manual force wins over whatever the Director (or a plugin filter)
                # returned — the queue collapses to the forced speaker alone.
                queue: list[str] = (
                    [turn.effective_force_speaker]
                    if turn.effective_force_speaker
                    else list(narrator_raw["next_speakers"])
                )
                controlled = game.player.controlled_character_id

                # Observability for the "the world ignored my message" symptom:
                # the player wrote something and the Director routed nobody. The
                # queue is already normalized to ["Narrator"] by then, so this is
                # the only place the two cases are still distinguishable.
                if (
                    beat_index == 0
                    and not turn.skip
                    and (turn.speech or turn.action)
                    and queue == ["Narrator"]
                ):
                    log_unanswered_player(
                        game.session_id,
                        step,
                        present_characters=len(
                            [c for c in game.scene.present_characters if c != "Player"]
                        ),
                    )

                scene_up = self._apply_canon(game, narrator_raw)
                self._apply_time_skip(game, narrator_raw, step)
                narration = await self._render_and_prepare(
                    game, narrator_raw, queue, step, multi_beat=max_beats > 1
                )
                # The Director decides WHAT is said aloud; the character decides
                # the words (task 65). Owners get their intent as a mandate in
                # the call they were already making; the rest are routed after.
                speech_intents = self._admissible_speech_intents(game, narrator_raw, step)
                owners = set(self._callable_speakers(game, queue))
                mandates: dict[str, list[str]] = {}
                for event, spoken, _ in speech_intents:
                    subject = str(event["subject_id"])
                    if subject in owners:
                        mandates.setdefault(subject, []).append(spoken)
                character_responses = await self._run_speaker_queue(
                    game, queue, narrator_raw, turn, step, intents=mandates
                )
                await self._resolve_speech_intents(
                    game, speech_intents, owners, character_responses, step
                )

                # A beat that left NO trace never happened. It reaches here when
                # the burst's anti-repetition filter empties its events and the
                # queue holds nobody the runner may voice, so there is nothing to
                # narrate and nobody to answer. Committing it anyway burned a turn
                # number that `_next_turn_number` (which reads the last RECORD)
                # handed out again, so two beats shared one number and undo popped
                # both. Dropping it un-commits everything the beat touched in
                # memory, because nothing is saved.
                #
                # "No trace" is deliberately narrow: a beat that compressed the
                # clock or changed the scene DID happen even with no record of its
                # own, and must keep its turn.
                if (
                    not any(record.turn_number == step for record in game.history)
                    and not scene_up
                    and not int(narrator_raw.get("time_skip_ticks") or 0)
                ):
                    burst.stop_reason = "beat_produced_nothing"
                    break

                _stamp_undo_anchor(game, step, beat_anchor)
                game = await self._commit_beat(
                    game, narrator_raw, character_responses, step, injected_event
                )

                burst.beats.append(
                    {
                        "narration": narration,
                        "character_responses": character_responses,
                        "next_speakers": queue,
                        "scene_update": scene_up,
                        "turn_number": step,
                    }
                )
                pending_hint = ""
                if self._beat_settled(
                    burst,
                    queue,
                    narrator_raw,
                    character_responses,
                    controlled,
                    multi_beat=max_beats > 1,
                ):
                    break

            if max_beats > 1 and burst.beats:
                log_burst(
                    game.session_id,
                    burst.beats[-1]["turn_number"],
                    beat_count=len(burst.beats),
                    stop_reason=burst.stop_reason,
                    first_turn=burst.beats[0]["turn_number"],
                )
            # A skip whose very first beat produced nothing leaves no beat at
            # all; the caller still gets a coherent, honest answer.
            last_beat = burst.beats[-1] if burst.beats else _EMPTY_BEAT
            return {
                **last_beat,
                "beats": burst.beats,
                "burst_stop_reason": burst.stop_reason if max_beats > 1 else None,
                "effective_input": turn.effective_input,
                "transformed_fields": turn.transformed_fields,
                "automatic_compaction": automatic_compaction,
            }

    # ── Turn stages ───────────────────────────────────────────────────────
    # player_turn above reads as the sequence of these; each one owns a single
    # step of the beat and can be read (or tested) without the others.

    def _validate_audience(
        self, game: GameState, audience: list[str] | None, speech: str, action: str
    ) -> list[str] | None:
        """Check a whisper audience against the scene and deduplicate it."""
        if audience is None:
            return None
        if not speech.strip() and not action.strip():
            raise ValueError("audience (whisper) requires speech or action")
        if not audience:
            raise ValueError("audience cannot be an empty list")
        unknown = [cid for cid in audience if cid not in game.characters]
        if unknown:
            raise ValueError(f"audience references unknown character IDs: {unknown}")
        absent = [cid for cid in audience if cid not in game.scene.present_characters]
        if absent:
            raise ValueError(f"audience references absent characters: {absent}")
        return list(dict.fromkeys(audience))

    async def _resolve_turn_input(
        self,
        game: GameState,
        step: int,
        *,
        speech: str,
        thought: str,
        action: str,
        force_speaker: str | None,
        narrator_hint: str,
        skip: bool,
        audience: list[str] | None,
    ) -> TurnInput:
        """Log the raw submission, run the plugin filter, resolve the routing.

        Both the submitted and the effective input are logged: a plugin that
        rewrites a turn must be auditable against what the human actually sent.
        """
        raw: dict[str, Any] = {
            "speech": speech,
            "thought": thought,
            "action": action,
            "force_speaker": force_speaker,
            "narrator_hint": narrator_hint,
            "skip": skip,
        }
        original = copy.deepcopy(raw)
        log_turn_input(
            session_id=game.session_id,
            turn_number=step,
            speech=speech,
            thought=thought,
            action=action,
            requested_force_speaker=force_speaker,
            narrator_hint=narrator_hint,
            skip=skip,
        )
        filtered = await self.plugins.hooks.filter(
            Hook.TURN_INPUT, raw, {"game": game, "turn_number": step, "runner": self}
        )
        raw_force = filtered["force_speaker"]
        resolved_force = str(raw_force) if raw_force is not None else None
        force_speaker_present = (
            resolved_force in game.characters and resolved_force in game.scene.present_characters
        )
        turn = TurnInput(
            speech=str(filtered["speech"]),
            thought=str(filtered["thought"]),
            action=str(filtered["action"]),
            force_speaker=resolved_force,
            narrator_hint=str(filtered["narrator_hint"]),
            skip=bool(filtered["skip"]),
            audience=audience,
            transformed_fields=[
                field
                for field in ("speech", "thought", "action")
                if filtered[field] != original[field]
            ],
            effective_force_speaker=(
                resolved_force
                if resolved_force and (force_speaker_present or resolved_force == "Narrator")
                else None
            ),
        )
        log_effective_turn_input(
            game.session_id,
            step,
            filtered,
            effective_force_speaker=turn.effective_force_speaker,
            transformed_fields=turn.transformed_fields,
        )
        return turn

    async def _maybe_automatic_compaction(
        self, game: GameState, turn: TurnInput, step: int
    ) -> dict[str, Any] | None:
        """Compact before the turn commits when the estimated context is too large.

        The estimate is measured on a PROBE that already contains this turn's
        input, so the decision reflects the prompt the Director is about to get.
        """
        context_max = self.config.get("context_max")
        if not self.config.get("automatic_compaction_enabled", False) or not isinstance(
            context_max, int
        ):
            return None

        probe = copy.deepcopy(game)
        if not turn.skip:
            for content, content_type in (
                (turn.speech, "speech"),
                (turn.thought, "thought"),
                (turn.action, "action"),
            ):
                if content:
                    self._append_history(probe, "Player", content, content_type, step)
        max_tokens = int(self.config.get("max_tokens_narrator", 2048))
        messages = build_narrator_messages(
            scene=probe.scene,
            characters=probe.characters,
            player_controlled_id=probe.player.controlled_character_id,
            history=probe.history,
            narrator_directives=probe.narrator_directives,
            context_max=None,
            max_tokens_narrator=max_tokens,
            story_summary=probe.story_summary,
            forced_speaker=turn.effective_force_speaker,
            narrator_hint=turn.narrator_hint,
        )
        estimated = estimate_prompt_tokens(messages) + max_tokens
        threshold = int(
            context_max * int(self.config.get("automatic_compaction_threshold_percent", 80)) / 100
        )
        if estimated < threshold:
            reason = "Estimated context remains below the threshold."
            log_compaction_status(
                game.session_id,
                step,
                status="not_needed",
                trigger="automatic",
                estimated_context_tokens=estimated,
                threshold_tokens=threshold,
                reason=reason,
            )
            return self._compaction_result(
                "not_needed", reason, game, estimated=estimated, threshold=threshold
            )
        try:
            return await self._compact_loaded_game(
                game,
                trigger="automatic",
                turn_number=step,
                estimated_context_tokens=estimated,
                threshold_tokens=threshold,
            )
        except Exception as error:
            reason = "Automatic compaction failed before commit."
            log_compaction_status(
                game.session_id,
                step,
                status="failed",
                trigger="automatic",
                estimated_context_tokens=estimated,
                threshold_tokens=threshold,
                reason=reason,
                error=error,
            )
            return self._compaction_result(
                "failed", reason, game, estimated=estimated, threshold=threshold
            )

    def _compaction_result(
        self,
        status: str,
        reason: str | None,
        game: GameState,
        *,
        estimated: int | None,
        threshold: int | None,
        trigger: CompactionTrigger = "automatic",
    ) -> dict[str, Any]:
        """The shape every NON-compacted outcome reports back to the caller."""
        return {
            "status": status,
            "trigger": trigger,
            "compacted": False,
            "reason": reason,
            "estimated_context_tokens": estimated,
            "threshold_tokens": threshold,
            "context_max": self.config.get("context_max"),
            "undo_depth": len(game.compaction_stack),
        }

    def _persist_player_input(self, game: GameState, turn: TurnInput, step: int) -> None:
        """Commit the human's move BEFORE the Narrator sees it (it stays blind).

        A skip persists nothing: the Narrator reacts to the current state alone.
        """
        if turn.skip:
            return
        for content, content_type, audience in (
            (turn.speech, "speech", turn.audience),
            (turn.thought, "thought", None),
            (turn.action, "action", turn.audience),
        ):
            if content:
                self._append_history(
                    game,
                    "Player",
                    content,
                    content_type,
                    step,
                    content_type in turn.transformed_fields,
                    audience=audience,
                )

    async def _resolve_beat_hint(
        self, game: GameState, step: int, beat_index: int, turn: TurnInput, pending: str
    ) -> tuple[str, bool]:
        """Decide this beat's UPCOMING EVENT line, and whether the code injected it.

        Four producers share one blind channel, in strict precedence:

        1. the hint the player wrote (or a plugin set) — never overridden;
        2. the drive scheduler's autonomous event (Task 33), first beat of a skip;
        3. the time-compression invite (Task 40 v2), same position;
        4. the act deadline's staged world_event (Task 40), any beat;
        5. the watcher's causal disruption (Task 33b), the semantic fallback that
           only speaks when everything gentler left the scene standing still.

        Returns the hint, whether it came from the world rather than the human
        (which is what ``turns_since_injected_event`` counts), and whether it is a
        CONTROL SIGNAL rather than an event — the clock invite instructs the
        Director, it is not something a character can perceive, so it must not be
        held to the event-materialization contract.
        """
        hint = pending
        injected = False
        is_control_signal = False
        opening_skip = beat_index == 0 and turn.skip

        if opening_skip and not hint.strip():
            # CODE decides whether the world receives an autonomous event; a small
            # structured call only writes WHAT the event is. The seed is always an
            # external world event for the blind Narrator — never a move for the
            # human's character.
            decision = evaluate_event_hazard(game, self.config)
            event_seed = ""
            if decision.fired:
                event_seed = await generate_event_seed(self.client, game, self.config, step)
                if event_seed:
                    hint = event_seed
                    injected = True
            log_drive_decision(
                game.session_id,
                step,
                fired=injected,
                probability=decision.probability,
                quiet_turns=decision.quiet_turns,
                roll=decision.roll,
                event_seed=event_seed,
            )

        if opening_skip and not hint.strip():
            # The player passing is the human "summary mode" signal. The Director
            # DECIDES the skip; the code only invites and later clamps the result.
            # Validated: a live scene never skips even when invited.
            hint = CLOCK_SKIP_INVITE
            is_control_signal = True

        # Roteiro maintenance (Task 38): CODE decides whether the story direction
        # needs a new rolling beat (coverage/budget/drift over history, with
        # hysteresis); a structured call only writes WHAT the beat says. Runs per
        # beat so bursts stay on-plan too, but the beat's budget only advances on
        # the FIRST beat: the unit is the player's action, not the turns one
        # action commits.
        clock_event = await self._maintain_roteiro(game, step, first_beat=(beat_index == 0))
        if clock_event and not hint.strip():
            # The act deadline's world_event stages THIS beat via the UPCOMING
            # EVENT contract (the same channel the drive uses).
            hint = clock_event
            injected = True

        if not hint.strip():
            watch_hint = await self._maybe_watcher_recovery(game, step)
            if watch_hint:
                hint = watch_hint
                injected = True
        return hint, injected, is_control_signal

    async def _director_beat(
        self,
        game: GameState,
        step: int,
        turn: TurnInput,
        beat_index: int,
        hint: str,
        *,
        multi_beat: bool,
        burst: BurstState,
        hint_is_control: bool = False,
    ) -> dict[str, Any]:
        """Run the Director call for one beat, with the plugin surfaces around it.

        ``narrator.context``/``narrator.schema`` let a plugin add read-only prompt
        lines and one output key without a provider- or plugin-specific branch
        here; ``narrator.call`` can replace the whole operation.
        """
        extra_context: list[str] = await self.plugins.hooks.filter(
            Hook.NARRATOR_CONTEXT, [], {"game": game, "turn_number": step, "runner": self}
        )
        schema_extension = await self.plugins.hooks.filter(
            Hook.NARRATOR_SCHEMA,
            {"properties": {}, "required": []},
            {"game": game, "turn_number": step, "runner": self},
        )
        # Hybrid protagonist routing (Task 45): keep the controlled character out
        # of next_speakers for the first BURST_PROTAGONIST_EXCLUDE_BEATS beats of
        # a continuation so the world reacts before the story can pull the human
        # back in; from then on they are eligible again, and the Narrator choosing
        # them ends the burst (player_addressed).
        narrator_raw: dict[str, Any] = await self.plugins.hooks.call_wrapped(
            Hook.NARRATOR_CALL,
            partial(
                self._call_narrator,
                game,
                step,
                turn.effective_force_speaker,
                hint,
                hint_is_control_signal=hint_is_control,
                extra_context=extra_context,
                extra_schema_properties=dict(schema_extension.get("properties", {})),
                extra_schema_required=list(schema_extension.get("required", [])),
                exclude_controlled=beat_index < BURST_PROTAGONIST_EXCLUDE_BEATS,
            ),
            {"game": game, "turn_number": step, "runner": self},
        )
        narrator_raw = await self.plugins.hooks.filter(
            Hook.NARRATOR_OUTPUT,
            narrator_raw,
            {"game": game, "turn_number": step, "runner": self},
        )
        if multi_beat:
            # Within a burst a stimulus must be resolved once: events that
            # near-duplicate an earlier beat's event are dropped so the renderer
            # never tells the same thud-and-whinny three times (Task 37).
            fresh_events = [
                event
                for event in narrator_raw["perception_events"]
                if not repeats_event_text(event["content"], burst.event_texts)
            ]
            narrator_raw["perception_events"] = fresh_events
            burst.event_texts.extend(event["content"] for event in fresh_events)
        return narrator_raw

    def _apply_canon(self, game: GameState, narrator_raw: dict[str, Any]) -> dict[str, Any] | None:
        """Reconcile the scene BEFORE the prose renders (Task 41).

        The renderer must stage the reconciled scene, not the stale one: rendering
        old canon against new events made the prose invent its own reconciliation
        ("he enters the hall" while the event had him racing through the city).
        Witness clamps were already computed from the pre-move scene inside
        ``narrate()``, so perception fairness ("arrival counts next beat") is
        unchanged.
        """
        scene_up = narrator_raw.get("scene_update")
        zone_moves = narrator_raw.get("zone_moves") or {}
        if zone_moves and scene_up and "location" in scene_up:
            # Partial movement is expressed by zones; the stage location only
            # changes when the WHOLE scene moves. The model often emits both (zone
            # split + a location change that would drag the rest of the cast along
            # in canon) — clamp the location change unless every present character
            # moved.
            present = {cid for cid in game.scene.present_characters if cid in game.characters}
            if not present.issubset(set(zone_moves)):
                scene_up = {k: v for k, v in scene_up.items() if k != "location"}
        if scene_up:
            self._update_scene(game, scene_up)

        new_zones = [z for z in zone_moves.values() if z not in game.scene.zones]
        if new_zones and not game.scene.zones:
            # First split of a zone-less stage: name the stage and place EVERYONE
            # on it, movers included. Before this beat they were all standing in
            # the same place, and the mover's origin is what the new zone links
            # back to — the move loop below overwrites their position anyway.
            stage = (game.scene.location or "").strip()[:60] or "palco"
            game.scene.zones[stage] = []
            for cid in game.scene.present_characters:
                if cid in game.characters:
                    game.scene.positions[cid] = stage
        self._open_new_zones(game, zone_moves, new_zones)
        for moved_id, zone in zone_moves.items():
            game.scene.positions[moved_id] = zone
        for zone, audible in (narrator_raw.get("zone_link_updates") or {}).items():
            if zone in game.scene.zones:
                game.scene.zones[zone] = [other for other in audible if other in game.scene.zones]
        return scene_up

    @staticmethod
    def _open_new_zones(
        game: GameState, zone_moves: dict[str, str], new_zones: list[str]
    ) -> None:
        """Create each new zone already audible from where its movers came.

        A new zone used to start deaf to everything, and the Director was told so
        in its own contract. It ignored that and kept using ``zone_moves`` for
        positions inside one room: in the live session `1cad8c55`, "C18 walks to
        the central table" turned an open hall into two sealed spaces and left 12
        records with an empty audience, including the player shouting a warning
        that reached nobody (task 54, finding 1).

        So the default is inverted: sound carries within a place unless something
        stops it, and stopping it is exactly what ``zone_link_updates`` is for —
        applied after this, so an explicit seal still wins. Erring toward hearing
        costs nothing in secrecy: a zone audience is ``audience_origin="zone"``,
        which the model layer already declares to be perception and never a
        secrecy source.
        """
        for zone in new_zones:
            if zone in game.scene.zones:
                continue
            origins = {
                game.scene.positions.get(mover)
                for mover, destination in zone_moves.items()
                if destination == zone
            }
            audible = sorted(
                origin for origin in origins if origin and origin in game.scene.zones
            )
            game.scene.zones[zone] = audible
            for origin in audible:
                if zone not in game.scene.zones[origin]:
                    game.scene.zones[origin].append(zone)

    def _apply_time_skip(self, game: GameState, narrator_raw: dict[str, Any], step: int) -> None:
        """Apply a Director-requested time compression, clamped by the code (Task 40 v2).

        The offstage change enters the world as a typed observation every present
        character witnesses, so prose, perspectives and history inherit it through
        the normal channels — the clock itself only ever moves forward.
        """
        raw_ticks = narrator_raw.get("time_skip_ticks")
        ticks = max(0, min(8, raw_ticks)) if isinstance(raw_ticks, int) else 0
        if not ticks:
            return
        summary = str(narrator_raw.get("time_skip_summary") or "").strip()[:300]
        game.narrative_tick += ticks
        if summary:
            narrator_raw["perception_events"].append(
                {
                    "event_kind": "observation",
                    "subject_id": "Narrator",
                    "content": summary,
                    "witness_ids": [
                        cid for cid in game.scene.present_characters if cid in game.characters
                    ],
                }
            )
        log_time_skip(
            game.session_id,
            step,
            ticks=ticks,
            summary=summary,
            narrative_tick_after=game.narrative_tick,
        )

    async def _render_and_prepare(
        self,
        game: GameState,
        narrator_raw: dict[str, Any],
        queue: list[str],
        step: int,
        *,
        multi_beat: bool,
    ) -> str:
        """Render the prose while the routed speakers' ledgers are prepared.

        Decision -> Prose split (Task 36): the two share no data dependency and
        the latency concentrates at this beat boundary, so they run concurrently.
        The merge stays deterministic — the narration record is always appended
        before any character record, whatever finishes first.
        """
        controlled = game.player.controlled_character_id
        prepare_ids = list(
            dict.fromkeys(
                speaker
                for speaker in queue
                if speaker != controlled
                and speaker in game.characters
                and speaker in game.scene.present_characters
            )
        )
        if multi_beat and not narrator_raw["perception_events"]:
            # A burst beat with zero novel events narrates NOTHING: the atmospheric
            # fallback would only re-describe the standing tableau (a null recap
            # turn). Routed characters still speak.
            await asyncio.gather(
                *(self._ensure_perspective(game, viewer, step) for viewer in prepare_ids)
            )
            return ""
        render_results = await asyncio.gather(
            self._render_narration(game, narrator_raw["perception_events"], step),
            *(self._ensure_perspective(game, viewer, step) for viewer in prepare_ids),
        )
        narration = str(render_results[0] or "")
        if narration:
            self._append_history(game, "Narrator", narration, "narration", step)
        return narration

    def _callable_speakers(self, game: GameState, queue: list[str]) -> list[str]:
        """The queue entries the runner may actually voice, in order.

        Factored out because two paths need the same answer and a copy of this
        filter that drifts would silently change WHO owns a line: the reply loop
        calls these, and `_resolve_speech_intents` treats exactly the others as
        needing a call of their own.
        """
        controlled = game.player.controlled_character_id
        speakers: list[str] = []
        for speaker in queue:
            if speaker == controlled:
                break
            if speaker not in game.characters or speaker not in game.scene.present_characters:
                continue
            speakers.append(speaker)
        return speakers

    async def _run_speaker_queue(
        self,
        game: GameState,
        queue: list[str],
        narrator_raw: dict[str, Any],
        turn: TurnInput,
        step: int,
        intents: dict[str, list[str]] | None = None,
    ) -> list[dict[str, Any]]:
        """Let each routed character speak, in order, seeing the previous replies.

        No Narrator call happens in between: each response is appended to history
        before the next character call, so a later speaker perceives the earlier
        ones through the normal visibility filter. The Narrator is blind and can
        route to the controlled character — the queue stops there and control
        returns to the human (the runner never generates their speech). A
        whispered exchange stays whispered: when a replying character is part of
        the turn's audience, its reply keeps the same audience.

        ``intents`` carries the facts the Director ruled this speaker says aloud
        (task 65). They are handed over as an obligation to voice rather than
        left in the perception stream, and they are REMOVED from that stream for
        this viewer — read as ambient perception the character treats them as
        something that already happened and answers it, which is how the same
        beat ended up spoken twice in two voices.
        """
        intents = intents or {}
        responses: list[dict[str, Any]] = []
        for speaker in self._callable_speakers(game, queue):
            reply_audience = (
                turn.audience if turn.audience is not None and speaker in turn.audience else None
            )
            await self._ensure_perspective(game, speaker, step)
            # Each speaker receives only the typed perception events they witness
            # (zone-clamped upstream), projected through their own identity ledger.
            ctx = render_events_for_viewer(
                [
                    event
                    for event in narrator_raw["perception_events"]
                    if not _is_own_speech_intent(event, speaker)
                ],
                speaker,
                game.characters,
                game.character_perspectives.get(speaker),
            )
            if not ctx.strip():
                # An empty perception void invites the model to hallucinate a
                # stimulus (an isolated character greeted a visitor that does not
                # exist). State the deterministic fact instead.
                ctx = (
                    "Nothing new reaches your senses right now; you are "
                    "alone with your current activity and thoughts."
                )
            # Deterministic guard behind the Narrator's whisper rule: the "denial
            # that reveals" pattern ("you did not hear the password X")
            # occasionally leaks whispered content into an event rendered for a
            # character outside the whisper's audience. Strip it here, before the
            # character ever sees it; audience members unaffected.
            ctx = redact_whisper_leaks(ctx, game.history, speaker, game.characters, game.scene)
            response = await self.plugins.hooks.call_wrapped(
                Hook.CHARACTER_CALL,
                partial(
                    self._call_character,
                    game,
                    speaker,
                    ctx,
                    step,
                    reply_audience=reply_audience,
                    speech_intents=intents.get(speaker),
                ),
                {"game": game, "character_id": speaker, "turn_number": step, "runner": self},
            )
            response = await self.plugins.hooks.filter(
                Hook.CHARACTER_OUTPUT,
                response,
                {"game": game, "character_id": speaker, "turn_number": step, "runner": self},
            )
            if response["thought"]:
                self._append_history(game, speaker, response["thought"], "thought", step)
            if response["speech"]:
                self._append_history(
                    game, speaker, response["speech"], "speech", step, audience=reply_audience
                )
            if response.get("action_intent"):
                # An intent is an ATTEMPT: it becomes an action record (the
                # existing physics — resolved by the next beat's Director), never
                # an outcome. Zone-scoped audience is computed by _append_history
                # like any physical act.
                self._append_history(game, speaker, response["action_intent"], "action", step)
            responses.append({"character_id": speaker, **response})
        return responses

    def _admissible_speech_intents(
        self, game: GameState, narrator_raw: dict[str, Any], step: int
    ) -> list[tuple[dict[str, Any], str, list[str] | None]]:
        """The Director's audible_speech events that may still reach the room.

        Returns ``(event, spoken, heard_by)`` for the survivors, in the
        Director's own order. Everything refused here is refused for reasons
        that hold whoever ends up writing the words, so the filter runs ONCE and
        both the mandate path and the routed path consume the same list.

        Four refusals, every one logged. A refusal is a line the reader never
        sees, so a silent drop would be invisible content loss and
        ``log_audible_speech_drop`` is what makes the channel's losses countable
        at the checkpoint.

        - ``echo`` — the Director re-voiced a line already in history.
        - ``internal_id`` / ``foreign_language`` — the deterministic guards from
          task 65 item 4.
        - ``whisper_leak`` — the Director sometimes re-narrates a WHISPER with a
          broad "just audible to those nearby" scope but the secret content
          inside. The transient render path redacts that per viewer; a shared
          record cannot, so the event is dropped whole. A public reveal of
          Director canon carries no whisper token and survives.
        """
        out: list[tuple[dict[str, Any], str, list[str] | None]] = []
        for event in narrator_raw["perception_events"]:
            if event.get("event_kind") != "audible_speech":
                continue
            spoken = str(event.get("content", "")).strip()
            subject = event.get("subject_id")
            if not spoken or subject not in game.characters:
                continue
            if _echoes_recent_speech(game, subject, spoken):
                log_audible_speech_drop(game.session_id, step, subject, "echo", spoken[:160])
                continue
            if _leaks_internal_id(game, spoken):
                log_audible_speech_drop(game.session_id, step, subject, "internal_id", spoken[:160])
                continue
            if _foreign_language(spoken, str(self.config.get("language", ""))):
                log_audible_speech_drop(
                    game.session_id, step, subject, "foreign_language", spoken[:160]
                )
                continue
            present_others = {
                cid
                for cid in game.scene.present_characters
                if cid in game.characters and cid != subject
            }
            witnesses = {w for w in event.get("witness_ids", []) if w in game.characters}
            heard_by = None if witnesses >= present_others else sorted(witnesses)
            listeners = present_others if heard_by is None else set(heard_by)
            if any(
                redact_tokens(
                    spoken, hidden_whisper_tokens(game.history, vid, game.characters, game.scene)
                )
                != spoken
                for vid in listeners
            ):
                log_audible_speech_drop(
                    game.session_id, step, subject, "whisper_leak", spoken[:160]
                )
                continue
            out.append((event, spoken, heard_by))
        return out

    async def _resolve_speech_intents(
        self,
        game: GameState,
        intents: list[tuple[dict[str, Any], str, list[str] | None]],
        owners: set[str],
        responses: list[dict[str, Any]],
        step: int,
    ) -> None:
        """Give every intent a voice that is allowed to own it (task 65).

        A fact voiced to the room — a decoded cipher, a name, a verdict — is a
        real world event, and WT-09 requires every witness to be able to RECALL
        it later, not only whoever replied this turn. That requirement stays.
        What changes is the producer: `AGENTS.md` §3 gives speech to the
        character, and this channel used to persist the DIRECTOR's sentence
        under the character's byline on 639 archived records.

        Three populations, measured over the archive before this was built:

        - the subject already speaks this turn (**403 of 639**). The intent was
          handed to them as a mandate by `_run_speaker_queue`; if their reply
          carries it, their own record is the only one there should be and
          nothing happens here.
        - the subject is silent this turn (**209**). They get a call of their
          own, and every such call in a beat is issued in ONE ``gather`` — they
          are independent by construction, and the archive's worst turn wants
          three of them, which serially is three round trips for one beat.
        - the intent restated a line the subject had already spoken (**27**),
          which `_admissible_speech_intents` already dropped as an echo.

        The degradation path catches what routing cannot serve: a reply that did
        not carry the mandate, a call that failed, a subject who cannot be
        voiced. Then the fact is persisted as a NARRATOR report of the speech
        rather than a quote of it — world-event territory, which §3 does give the
        Narrator — and it is counted, never silent. What must never happen again
        is a record claiming a character said words the character did not write.
        """
        if not intents:
            return
        spoken_by: dict[str, str] = {}
        for response in responses:
            line = str(response.get("speech") or "")
            if line:
                spoken_by[str(response["character_id"])] = line

        pending: list[tuple[dict[str, Any], str, list[str] | None]] = []
        for event, spoken, heard_by in intents:
            subject = str(event["subject_id"])
            if subject == game.player.controlled_character_id:
                # The runner never writes the human's dialogue, so this one can
                # be neither mandated nor routed. It is NOT dropped: the player's
                # own action can reveal something they never typed — WT-09's
                # founding case is exactly that, a cipher read aloud by the
                # player's character whose content exists only in this event. So
                # the Narrator reports it and every witness can still recall it.
                # The other half — the Director paraphrasing what the human
                # actually submitted (`base-P2-r1` T2, "Link responde... que
                # continua aqui") — never reaches here: `_echoes_recent_speech`
                # already counts the Player sentinel as the same voice.
                self._report_speech(game, subject, spoken, heard_by, step, "player_voice")
                continue
            if subject not in owners:
                pending.append((event, spoken, heard_by))
                continue
            if _carries_intent(spoken_by.get(subject, ""), spoken):
                log_audible_speech_drop(
                    game.session_id, step, subject, "voiced_by_owner", spoken[:160]
                )
                continue
            self._report_speech(game, subject, spoken, heard_by, step, "mandate_ignored")

        if not pending:
            return
        routed = await asyncio.gather(
            *(
                self._route_speech_intent(game, str(event["subject_id"]), spoken, step)
                for event, spoken, _ in pending
            ),
            return_exceptions=True,
        )
        # Persisted in the Director's order, never in completion order: the
        # gather is a latency device and must not become a source of nondeterminism.
        for (event, spoken, heard_by), line in zip(pending, routed, strict=True):
            subject = str(event["subject_id"])
            if isinstance(line, BaseException) or not line:
                self._report_speech(game, subject, spoken, heard_by, step, "routing_failed")
                continue
            if not _carries_intent(line, spoken):
                self._report_speech(game, subject, spoken, heard_by, step, "mandate_ignored")
                continue
            self._append_history(
                game, subject, line, "speech", step, audience=heard_by, audience_origin="zone"
            )

    async def _route_speech_intent(
        self, game: GameState, subject: str, spoken: str, step: int
    ) -> str:
        """One character call whose only job is to voice one intent."""
        if subject not in game.characters or subject not in game.scene.present_characters:
            return ""
        if subject == game.player.controlled_character_id:
            return ""  # the runner never generates the human's speech
        await self._ensure_perspective(game, subject, step)
        response = await self._call_character(
            game,
            subject,
            "You are about to speak to the room; nothing else has changed.",
            step,
            speech_intents=[spoken],
        )
        return str(response.get("speech") or "")

    def _report_speech(
        self,
        game: GameState,
        subject: str,
        spoken: str,
        heard_by: list[str] | None,
        step: int,
        reason: str,
    ) -> None:
        """The degradation path: the Narrator REPORTS the speech, never quotes it.

        The fact still reaches every witness's memory (WT-09), and no record
        claims the character authored words they did not write.
        """
        log_audible_speech_drop(game.session_id, step, subject, reason, spoken[:160])
        self._append_history(
            game,
            "Narrator",
            spoken,
            "narration",
            step,
            audience=heard_by,
            audience_origin="zone",
        )

    async def _commit_beat(
        self,
        game: GameState,
        narrator_raw: dict[str, Any],
        character_responses: list[dict[str, Any]],
        step: int,
        injected_event: bool,
    ) -> GameState:
        """Apply the beat's remaining state and save it as one transaction."""
        mood_updates = narrator_raw.get("mood_updates")
        if mood_updates:
            self._update_moods(game, mood_updates)

        # Each plugin validates and applies its own narrator.schema property (if
        # present in narrator_raw) to this same-turn draft. A plugin that finds
        # its own proposal invalid returns the draft unchanged instead of raising —
        # raising here would trip the shared crash policy and disable the plugin,
        # which is reserved for genuine bugs, not routine LLM validation failures.
        game = await self.plugins.hooks.filter(
            Hook.NARRATOR_RESULT,
            game,
            {"narrator_output": narrator_raw, "turn_number": step, "runner": self},
        )
        game = await self.plugins.hooks.filter(
            Hook.TURN_BEFORE_COMMIT, game, {"kind": "turn", "runner": self}
        )
        game.turns_since_injected_event = (
            0 if injected_event else game.turns_since_injected_event + 1
        )
        # Roteiro coverage (Task 38): record which of the current beat's anchors
        # this beat actually put in play, measured on the AUTHORITATIVE evidence —
        # the Director's typed events and the characters' own words/acts — not the
        # lossy prose. Audible speech never reaches the renderer, so the prose can
        # never be the coverage surface without punishing the Director for obeying.
        if game.roteiro is not None and game.roteiro.beat is not None:
            evidence_texts = [event["content"] for event in narrator_raw["perception_events"]]
            for response in character_responses:
                if response.get("speech"):
                    evidence_texts.append(response["speech"])
                if response.get("action_intent"):
                    evidence_texts.append(response["action_intent"])
            newly_seen = collect_beat_evidence(game.roteiro, evidence_texts)
            if newly_seen:
                game.roteiro.anchors_seen.extend(newly_seen)
        game.narrative_tick += 1
        await self._audit_turn_for_watcher(game, step)
        await self._apply_disposition_feedback(game, step)
        game.revision += 1
        save_game(game)
        await self.plugins.hooks.action(Hook.TURN_AFTER_COMMIT, {"game": game, "kind": "turn"})
        return game

    def _beat_settled(
        self,
        burst: BurstState,
        queue: list[str],
        narrator_raw: dict[str, Any],
        character_responses: list[dict[str, Any]],
        controlled: str,
        *,
        multi_beat: bool,
    ) -> bool:
        """Whether the burst stops here, recording why on ``burst.stop_reason``."""
        if controlled in queue:
            burst.stop_reason = "player_addressed"
            return True
        if narrator_raw.get("return_control"):
            burst.stop_reason = "protagonist_decision"
            return True
        if character_responses:
            burst.narrator_only_streak = 0
            return False
        if multi_beat and not narrator_raw["perception_events"]:
            # Nothing new happened and nobody spoke: the beat settled.
            burst.stop_reason = "beat_settled"
            return True
        burst.narrator_only_streak += 1
        if burst.narrator_only_streak >= 2:
            burst.stop_reason = "beat_settled"
            return True
        return False


    async def get_state(self, session_id: str) -> GameState | None:
        """Load one consistent state snapshot after active mutations finish."""
        async with session_lock(session_id):
            return load_game(session_id)

    async def get_history(self, session_id: str, limit: int = 50) -> list[TurnRecord]:
        """Return the last N records from a transactionally consistent snapshot."""
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                return []
            return game.history[-limit:]

    async def undo_turn(self, session_id: str) -> dict:
        """Undoes the entire last player turn step.

        Undoes one step per call — repeated calls undo multiple levels. A
        "step" is every record sharing the highest ``turn_number`` (human move
        + narration + Character reply, see ``_append_history``). All of them
        carry the same scene, mood, plugin, perspective and disposition snapshots
        (those states change only after the records are appended), so any record
        can restore the complete pre-step state.

        Returns:
            Dict with ``state`` (serialized GameState) and ``undone`` (bool).
            If there is nothing to undo, returns ``{"undone": False}``.
        """
        from src.models import game_state_to_dict

        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)

            # No history -> nothing to undo
            if not game.history:
                return {"undone": False}

            # Remove all records sharing the highest turn_number and restore scene +
            # moods from snapshot.
            last_turn_number = game.history[-1].turn_number
            restore: TurnRecord | None = None
            removed = 0
            while game.history and game.history[-1].turn_number == last_turn_number:
                restore = game.history.pop()
                removed += 1

            assert restore is not None, "loop above runs at least once"
            game.scene = copy.deepcopy(restore.scene_snapshot)
            for cid, mood in restore.mood_snapshot.items():
                if cid in game.characters:
                    game.characters[cid].mind.current_mood = mood
            game.plugin_state = copy.deepcopy(restore.plugin_state_snapshot)
            game.character_perspectives = {
                viewer_id: dict_to_perspective(item)
                for viewer_id, item in restore.perspective_snapshot.items()
            }
            game.dispositions = dict_to_disposition_state(restore.disposition_snapshot)
            game.narrative_tick = restore.narrative_tick_snapshot
            game.roteiro = (
                dict_to_roteiro(copy.deepcopy(restore.roteiro_snapshot))
                if restore.roteiro_snapshot is not None
                else None
            )

            game = await self.plugins.hooks.filter(
                Hook.UNDO_BEFORE_COMMIT,
                game,
                {"turn_number": last_turn_number, "removed": removed, "runner": self},
            )
            game.revision += 1
            save_game(game)
            await self.plugins.hooks.action(
                Hook.UNDO_AFTER_COMMIT,
                {"game": game, "turn_number": last_turn_number, "removed": removed},
            )
            log_undo(session_id, last_turn_number, removed)
            return {"undone": True, "state": game_state_to_dict(game)}

    async def suggest_actions(self, session_id: str) -> dict:
        """Asks the (blind) Narrator for possible move suggestions for the controlled character.

        Manual trigger "suggest to me" (Task 6): does not persist anything — just returns
        suggestions for the frontend to fill the speech/action input boxes. The Narrator
        does not know the target character is the human.

        Returns:
            Dict with ``suggestions`` (list of ``{"speech", "action"}``).
        """
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)

            target_id = game.player.controlled_character_id
            turn_number = game.history[-1].turn_number if game.history else 0
            suggestions = await suggest_moves(
                client=self.client,
                scene=game.scene,
                characters=game.characters,
                target_id=target_id,
                history=game.history,
                config=self.config,
                narrator_directives=game.narrator_directives,
                session_id=game.session_id,
                turn_number=turn_number,
                viewer_perspective=game.character_perspectives.get(target_id),
            )
            suggestions = await self.plugins.hooks.filter(
                Hook.SUGGESTIONS_OUTPUT,
                suggestions,
                {"game": game, "target_id": target_id, "runner": self},
            )
            return {"suggestions": suggestions}

    async def suggest_openings(self, session_id: str) -> dict:
        """Generate three ephemeral scenario-only hints before the first turn."""
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            if game.history:
                raise ConversationAlreadyStartedError(
                    "Opening suggestions are available only before the first turn."
                )
            suggestions = await narrator_suggest_openings(
                client=self.client,
                scene=game.scene,
                config=self.config,
                narrator_directives=game.narrator_directives,
                session_id=game.session_id,
            )
            return {"suggestions": suggestions}

    async def compact_session(
        self,
        session_id: str,
        *,
        progress: ProgressSink | None = None,
    ) -> dict[str, Any]:
        """Compact one session under its canonical transaction lock."""
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            return await self._compact_loaded_game(game, trigger="manual", progress=progress)

    async def _compact_loaded_game(
        self,
        game: GameState,
        *,
        trigger: CompactionTrigger,
        turn_number: int | None = None,
        estimated_context_tokens: int | None = None,
        threshold_tokens: int | None = None,
        progress: ProgressSink | None = None,
    ) -> dict[str, Any]:
        """Compact an already-loaded game while the caller owns its session lock."""
        checkpoint_id = next_compaction_id(game.session_id)
        sequence = 0

        def emit(
            stage: CompactionStage,
            completed: int = 0,
            total: int = 0,
            *,
            agent: str | None = None,
            result: dict[str, Any] | None = None,
            error: BaseException | None = None,
        ) -> None:
            nonlocal sequence
            if progress is None:
                return
            sequence += 1
            progress(
                CompactionProgress(
                    operation_id=checkpoint_id,
                    sequence=sequence,
                    stage=stage,
                    completed_units=completed,
                    total_units=total,
                    agent=agent,
                    result=result,
                    error_type=type(error).__name__ if error is not None else None,
                )
            )

        emit("checking")
        keep_recent = self.config.get("compaction_keep_recent_turns", 200)
        turn_numbers = list(dict.fromkeys(record.turn_number for record in game.history))
        if (
            trigger == "automatic"
            and estimated_context_tokens is not None
            and threshold_tokens is not None
            and estimated_context_tokens > threshold_tokens
            and len(turn_numbers) <= keep_recent
            and len(turn_numbers) > 8
        ):
            # Under real context pressure the configured retention window must
            # not block the automatic compaction it exists to serve: shrink it
            # adaptively to the most recent half (never below 4 turns), so the
            # session compacts instead of silently trimming history away
            # (Task 23 — trim/compaction gap).
            keep_recent = max(4, len(turn_numbers) // 2)
        if len(turn_numbers) <= keep_recent:
            status = (
                "blocked_by_retention_window"
                if trigger == "automatic" and estimated_context_tokens is not None
                else "not_needed"
            )
            result = self._compaction_result(
                status,
                "History smaller than the retained window.",
                game,
                estimated=estimated_context_tokens,
                threshold=threshold_tokens,
                trigger=trigger,
            )
            if trigger == "automatic":
                log_compaction_status(
                    game.session_id,
                    turn_number or (turn_numbers[-1] if turn_numbers else 0),
                    status=status,
                    trigger=trigger,
                    estimated_context_tokens=estimated_context_tokens,
                    threshold_tokens=threshold_tokens,
                    reason=str(result["reason"]),
                )
            emit("skipped", result=result)
            return result

        cutoff = turn_numbers[-keep_recent]
        evicted = [record for record in game.history if record.turn_number < cutoff]
        kept = [record for record in game.history if record.turn_number >= cutoff]
        # One model unit: the world summary. Private memory is the perspective
        # ledger's continuous job now (Task 39) - no per-character fan-out.
        total_units = 1
        completed_units = 0
        emit("summarizing", completed_units, total_units)

        def model_completed(agent: str) -> None:
            nonlocal completed_units
            completed_units += 1
            emit(
                "model_completed",
                completed_units,
                total_units,
                agent=agent,
            )

        try:
            new_summary = await summarize(
                client=self.client,
                characters=game.characters,
                controlled_id=game.player.controlled_character_id,
                story_summary=game.story_summary,
                evicted_turns=evicted,
                config=self.config,
                narrator_directives=game.narrator_directives,
                session_id=game.session_id,
                turn_number=turn_number if turn_number is not None else cutoff,
                on_model_completed=model_completed,
            )

            draft = CompactionDraft(
                history=copy.deepcopy(kept),
                story_summary=new_summary,
                plugin_state=copy.deepcopy(game.plugin_state),
            )
            emit("before_commit", completed_units, total_units)
            draft = await self.plugins.hooks.filter_strict(
                Hook.COMPACTION_BEFORE_COMMIT,
                draft,
                {"cutoff": cutoff, "evicted": copy.deepcopy(evicted), "runner": self},
            )
            if not isinstance(draft, CompactionDraft):
                raise TypeError("compaction.before_commit must return CompactionDraft")

            compacted = copy.deepcopy(game)
            compacted.history = copy.deepcopy(draft.history)
            compacted.story_summary = draft.story_summary
            compacted.plugin_state = copy.deepcopy(draft.plugin_state)
            committed_revision = game.revision + 1
            parent_id = game.compaction_stack[-1].checkpoint_id if game.compaction_stack else None
            checkpoint = {
                "schema_version": 1,
                "checkpoint_id": checkpoint_id,
                "parent_id": parent_id,
                "trigger": trigger,
                "created_at": datetime.now(UTC).isoformat(),
                "base_revision": game.revision,
                "cutoff_turn_number": cutoff,
                "max_turn_number": turn_numbers[-1],
                "evicted_history": [asdict(record) for record in evicted],
                "before_story_summary": game.story_summary,
                "after_history_hash": history_hash(compacted.history),
                "after_story_summary_hash": canonical_hash(compacted.story_summary),
                "plugin_state_delta": build_plugin_delta(game.plugin_state, compacted.plugin_state),
            }
            emit("checkpointing", completed_units, total_units)
            checkpoint_path = Path(
                write_compaction_checkpoint(game.session_id, checkpoint_id, checkpoint)
            )
            compacted.compaction_stack.append(
                CompactionStackEntry(
                    checkpoint_id=checkpoint_id,
                    parent_id=parent_id,
                    trigger=trigger,
                    created_at=checkpoint["created_at"],
                    cutoff_turn_number=cutoff,
                    max_turn_number=turn_numbers[-1],
                    committed_revision=committed_revision,
                )
            )
            compacted.revision = committed_revision
            emit("committing", completed_units, total_units)
            try:
                save_game(compacted)
            except BaseException:
                checkpoint_path.unlink(missing_ok=True)
                raise
            # The caller (a turn in progress) holds this exact object and must
            # see the compacted history from here on, so the committed state is
            # copied into it field by field.
            _adopt_state(game, compacted)

            result = {
                "status": "compacted",
                "trigger": trigger,
                "compaction_id": checkpoint_id,
                "compacted": True,
                "reason": None,
                "cutoff_turn_number": cutoff,
                "evicted_records": len(evicted),
                "kept_records": len(compacted.history),
                "estimated_context_tokens": estimated_context_tokens,
                "threshold_tokens": threshold_tokens,
                "context_max": self.config.get("context_max"),
                "undo_depth": len(compacted.compaction_stack),
            }
            log_compact(
                game.session_id,
                cutoff,
                len(evicted),
                len(compacted.history),
                checkpoint_id=checkpoint_id,
                trigger=trigger,
                turn_number=turn_number if turn_number is not None else cutoff,
                estimated_context_tokens=estimated_context_tokens,
                threshold_tokens=threshold_tokens,
            )
            await self.plugins.hooks.action(
                Hook.COMPACTION_AFTER_COMMIT,
                {
                    "game": compacted,
                    "cutoff": cutoff,
                    "evicted": len(evicted),
                    "result": result,
                },
            )
            emit("completed", completed_units, total_units, result=result)
            return result
        except BaseException as error:
            emit("failed", completed_units, total_units, error=error)
            raise

    async def restore_last_compaction(self, session_id: str) -> dict:
        """Undo the newest compaction while preserving every later turn."""
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            result: dict[str, Any]
            if not game.compaction_stack:
                result = {
                    "restored": False,
                    "undone": False,
                    "reason": "No compaction checkpoint found.",
                    "remaining_undo_depth": 0,
                }
                log_restore_compaction(session_id, False, result["reason"], _current_turn(game))
                return result

            entry = game.compaction_stack[-1]
            try:
                checkpoint = load_compaction_checkpoint(session_id, entry.checkpoint_id)
                if checkpoint["schema_version"] != 1:
                    raise ValueError("Unsupported compaction checkpoint schema")
                if checkpoint["checkpoint_id"] != entry.checkpoint_id:
                    raise ValueError("Compaction checkpoint identity mismatch")
                expected_parent = (
                    game.compaction_stack[-2].checkpoint_id
                    if len(game.compaction_stack) > 1
                    else None
                )
                if checkpoint["parent_id"] != expected_parent:
                    raise ValueError("Compaction checkpoint parent mismatch")

                max_turn = int(checkpoint["max_turn_number"])
                compacted_prefix = [
                    record for record in game.history if record.turn_number <= max_turn
                ]
                later = [record for record in game.history if record.turn_number > max_turn]
                if history_hash(compacted_prefix) != checkpoint["after_history_hash"]:
                    raise ValueError("Compacted history prefix diverged")
                if canonical_hash(game.story_summary) != checkpoint["after_story_summary_hash"]:
                    raise ValueError("Story summary diverged after compaction")

                restored_plugin_state, conflicts = invert_plugin_delta(
                    game.plugin_state, checkpoint["plugin_state_delta"]
                )
                unresolved: dict[str, list[str]] = {}
                for plugin_id, paths in conflicts.items():
                    if not self.plugins.hooks.has_registration(
                        Hook.COMPACTION_UNDO_CONFLICT, "filter", plugin_id
                    ):
                        unresolved[plugin_id] = paths
                        continue
                    current_namespace = copy.deepcopy(game.plugin_state.get(plugin_id))
                    resolved = await self.plugins.hooks.filter_for_plugin(
                        Hook.COMPACTION_UNDO_CONFLICT,
                        plugin_id,
                        current_namespace,
                        {
                            "paths": paths,
                            "checkpoint_id": entry.checkpoint_id,
                            "runner": self,
                        },
                    )
                    if resolved is None:
                        restored_plugin_state.pop(plugin_id, None)
                    else:
                        restored_plugin_state[plugin_id] = resolved
                if unresolved:
                    reason = "Plugin state changed after compaction; undo requires a resolver."
                    result = {
                        "restored": False,
                        "undone": False,
                        "reason": reason,
                        "plugin_conflicts": sorted(unresolved),
                        "remaining_undo_depth": len(game.compaction_stack),
                    }
                    log_restore_compaction(session_id, False, reason, _current_turn(game))
                    return result

                evicted = [dict_to_turn_record(record) for record in checkpoint["evicted_history"]]
                draft = copy.deepcopy(game)
                draft.history = [*evicted, *compacted_prefix, *later]
                draft.story_summary = str(checkpoint["before_story_summary"])
                draft.plugin_state = restored_plugin_state
                draft.compaction_stack.pop()
                draft.revision += 1
                save_game(draft)
                result = {
                    "restored": True,
                    "undone": True,
                    "compaction_id": entry.checkpoint_id,
                    "restored_records": len(evicted),
                    "history_length": len(draft.history),
                    "preserved_through_turn": max(
                        (record.turn_number for record in later), default=max_turn
                    ),
                    "remaining_undo_depth": len(draft.compaction_stack),
                    "plugin_conflicts": [],
                }
            except (KeyError, OSError, ValueError) as error:
                result = {
                    "restored": False,
                    "undone": False,
                    "reason": str(error),
                    "remaining_undo_depth": len(game.compaction_stack),
                }
            log_restore_compaction(
                session_id,
                result.get("restored", False),
                result.get("reason", ""),
                _current_turn(game),
            )
            if result.get("restored"):
                await self.plugins.hooks.action(
                    Hook.COMPACTION_RESTORE_AFTER_COMMIT,
                    {"game": load_game(session_id), "result": result},
                )
            return result

    async def set_presence(
        self, session_id: str, present_characters: list[str], expected_revision: int
    ) -> dict:
        """Administrative, out-of-band presence edit — no turn, no LLM call, no history.

        Guards against overwriting a concurrent turn/edit via ``expected_revision``
        (the client's whole view of the session). The previous list is pushed onto
        ``presence_edit_stack`` so ``undo_last_presence_edit`` can revert it later.
        """
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            if game.revision != expected_revision:
                raise PresenceRevisionConflictError(
                    "Session was modified concurrently; reload and retry with the current revision."
                )
            validated = validate_present_characters(
                present_characters, game.characters, game.player.controlled_character_id
            )
            before = list(game.scene.present_characters)
            changed_ids = sorted(set(before) ^ set(validated))
            entry = PresenceEditEntry(
                edit_id=uuid4().hex[:8],
                created_at=datetime.now(UTC).isoformat(),
                origin="human",
                before=before,
                after=validated,
                committed_revision=game.revision + 1,
            )
            game.scene.present_characters = validated
            game.presence_edit_stack.append(entry)
            game.revision += 1
            save_game(game)
            log_presence_change(
                session_id,
                origin=entry.origin,
                changed_ids=changed_ids,
                revision=game.revision,
                edit_id=entry.edit_id,
                turn_number=_current_turn(game),
            )
            return {
                "changed": True,
                "present_characters": validated,
                "revision": game.revision,
                "edit_id": entry.edit_id,
            }

    async def update_session_setup(
        self,
        session_id: str,
        *,
        characters: dict[str, Any],
        scene: Any,
        narrator_directives: str,
        character_preset_ids: dict[str, str],
        controlled_character_id: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Replace editable fields on one materialized session snapshot."""
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            if game.revision != expected_revision:
                raise PresenceRevisionConflictError(
                    "Session was modified concurrently; reload and retry with the current revision."
                )
            if list(characters) != list(game.characters):
                raise ValueError("Active-session character IDs and order cannot be changed.")
            if controlled_character_id not in characters:
                raise ValueError("The controlled character must exist in this session.")
            if set(character_preset_ids) - set(characters):
                raise ValueError("A character source can only refer to a session character.")
            if len(set(character_preset_ids.values())) != len(character_preset_ids):
                raise ValueError("A character source can only be linked once in a session.")
            from src.store.presets import load_preset

            missing = [
                source_id
                for source_id in character_preset_ids.values()
                if load_preset(source_id) is None
            ]
            if missing:
                raise ValueError(f"Character source '{missing[0]}' was not found.")
            scene.present_characters = validate_present_characters(
                scene.present_characters,
                characters,
                controlled_character_id,
            )
            changed_fields = []
            for field_name, before, after in (
                ("characters", game.characters, characters),
                ("scene", game.scene, scene),
                ("narrator_directives", game.narrator_directives, narrator_directives),
                ("character_preset_ids", game.character_preset_ids, character_preset_ids),
                (
                    "controlled_character_id",
                    game.player.controlled_character_id,
                    controlled_character_id,
                ),
            ):
                if before != after:
                    changed_fields.append(field_name)
            if not changed_fields:
                return {"changed": False, "state": game_state_to_dict(game)}
            game.characters = copy.deepcopy(characters)
            game.scene = copy.deepcopy(scene)
            game.narrator_directives = narrator_directives
            game.character_preset_ids = dict(character_preset_ids)
            game.player.controlled_character_id = controlled_character_id
            game.revision += 1
            save_game(game)
            log_session_setup_change(
                session_id,
                revision=game.revision,
                fields=changed_fields,
                turn_number=_current_turn(game),
            )
            return {"changed": True, "state": game_state_to_dict(game)}

    async def undo_last_presence_edit(self, session_id: str) -> dict:
        """Undo the newest out-of-band admin presence edit — strictly LIFO.

        Only ever touches ``presence_edit_stack[-1]``. Before restoring, compares
        the CURRENT presence against that entry's recorded ``after`` — the same
        content-divergence check ``restore_last_compaction`` uses (not a revision
        comparison), so a later Narrator ``presence_update`` or another admin edit is
        never silently overwritten; the restore is rejected explicitly instead.
        """
        async with session_lock(session_id):
            game = load_game(session_id)
            if game is None:
                raise SessionNotFoundError(session_id)
            if not game.presence_edit_stack:
                reason = "No presence edit found."
                log_presence_undo(session_id, False, reason, _current_turn(game))
                return {"restored": False, "reason": reason, "remaining_undo_depth": 0}

            entry = game.presence_edit_stack[-1]
            if list(game.scene.present_characters) != entry.after:
                reason = (
                    "Presence changed again since this edit; undo would overwrite a later change."
                )
                log_presence_undo(session_id, False, reason, _current_turn(game))
                return {
                    "restored": False,
                    "reason": reason,
                    "remaining_undo_depth": len(game.presence_edit_stack),
                }

            try:
                restored = validate_present_characters(
                    entry.before, game.characters, game.player.controlled_character_id
                )
            except ValueError as error:
                log_presence_undo(session_id, False, str(error), _current_turn(game))
                return {
                    "restored": False,
                    "reason": str(error),
                    "remaining_undo_depth": len(game.presence_edit_stack),
                }

            game.scene.present_characters = restored
            game.presence_edit_stack.pop()
            game.revision += 1
            save_game(game)
            log_presence_undo(session_id, True, "", _current_turn(game))
            return {
                "restored": True,
                "present_characters": restored,
                "revision": game.revision,
                "remaining_undo_depth": len(game.presence_edit_stack),
            }

    # ── Private Methods ───────────────────────────────────────────────────

    async def _audit_turn_for_watcher(self, game: GameState, turn_number: int) -> None:
        """Accumulate the roteiro watcher's immobility signal (Task 33b, piece 1).

        One blind delta-audit call per committed turn: if the story moved, the
        quiet counter and the silence grace reset; if it stood still, the quiet
        counter climbs. No-op unless the watcher is enabled.
        """
        if not bool(self.config.get("watcher_enabled", False)):
            return
        audit = await audit_delta(self.client, game, self.config, turn_number)
        if audit.moved:
            game.watcher_quiet_turns = 0
            game.watcher_silence_spent = False
        else:
            game.watcher_quiet_turns += 1

    async def _apply_disposition_feedback(self, game: GameState, turn_number: int) -> None:
        """Fold the turn's relationship shifts into the disposition substrate
        (Task 43, Phase 3). One blind appraisal call per committed turn integrates
        directional trust/warmth deltas (the surviving measured axes);
        then every live axis relaxes one step toward its baseline, so a one-off nudge
        fades over calm turns while a sustained shift accumulates. No-op unless the
        feedback loop is enabled (OFF by default — it is an extra call per turn).
        """
        if not bool(self.config.get("disposition_feedback_enabled", False)):
            return
        deltas = await appraise_relationships(self.client, game, self.config, turn_number)
        integrate_appraisal(game.dispositions, deltas)
        apply_gravity(game.dispositions)

    async def _maybe_watcher_recovery(self, game: GameState, turn_number: int) -> str | None:
        """Run the recovery ladder; return a causal-disruption hint or None.

        The ladder is pure code (piece 2). The clock (Task 40) already owns the
        `execute_promised_transition` rung, so the wired ladder handles the rungs
        below it: it tolerates one beat of silence, then grows a causal
        intervention (piece 3) from an open thread. The `adjudicate_attempt` and
        `reincorporate_thread` rungs stay dormant until their state derivation
        exists (they never fire while their flags are False).
        """
        if not bool(self.config.get("watcher_enabled", False)):
            return None
        ctx = LadderContext(
            quiet_turns=game.watcher_quiet_turns,
            turns_since_intervention=game.narrative_tick - game.watcher_last_intervention_tick,
            silence_spent=game.watcher_silence_spent,
        )
        step = select_recovery_step(ctx, self.config)
        if step.rung == RUNG_ALLOW_SILENCE:
            game.watcher_silence_spent = True
            return None
        if step.rung != RUNG_CAUSAL_DISRUPTION:
            return None
        intervention = await generate_causal_intervention(
            self.client, game, self.config, turn_number
        )
        if not intervention.grounded:
            return None
        game.watcher_last_intervention_tick = game.narrative_tick
        game.watcher_quiet_turns = 0
        game.watcher_silence_spent = False
        return intervention.event_now

    async def _maintain_roteiro(
        self, game: GameState, turn_number: int, first_beat: bool = True
    ) -> str | None:
        """Compile the roteiro on first need; replan when the code signals say so.

        The replan TRIGGER is deterministic (``evaluate_roteiro``); the LLM only
        writes beat content. Every evaluation is logged so acceptance runs can
        audit that zero triggers came from model self-assessment.

        ``first_beat`` marks the opening beat of a player action. The beat's
        replan budget is spent per ACTION, so a multi-beat continuation costs it
        exactly one — see ``evaluate_roteiro``.
        """
        if not bool(self.config.get("roteiro_enabled", False)):
            return None
        next_turn = (game.history[-1].turn_number + 1) if game.history else 1
        if game.roteiro is None:
            game.roteiro = await generate_roteiro(self.client, game, self.config, turn_number)
            game.roteiro.act_started_tick = game.narrative_tick
            return None
        if first_beat:
            game.roteiro.beat_actions_elapsed += 1

        # Narrative clock (Task 40): when the current act's tick deadline
        # expires, the CODE stages its world_event (returned to the caller as
        # this beat's UPCOMING EVENT) and advances the act - the world never
        # waits for the conversation to finish. Deterministic; the LLM only
        # wrote the event text at planning time.
        act = (
            game.roteiro.acts[game.roteiro.act_index]
            if game.roteiro.act_index < len(game.roteiro.acts)
            else None
        )
        if (
            act is not None
            and act.duration_ticks > 0
            and game.narrative_tick - game.roteiro.act_started_tick >= act.duration_ticks
        ):
            world_event = act.world_event.strip()
            log_roteiro_decision(
                game.session_id,
                turn_number,
                action="act_deadline",
                reason="clock",
                beat_id=game.roteiro.beat.beat_id if game.roteiro.beat else "none",
                anchors_missing=[],
                actors_missing=[],
            )
            # The act advance is CODE-owned: the deadline concluded it, whatever
            # the conversation was doing. The replan only writes the next act's
            # opening beat (its status text says the world_event just happened).
            #
            # On the LAST act there is nowhere to advance to, and the previous
            # code still reset the tick and returned the world_event — so the
            # terminal act re-fired its climax every `duration_ticks`, forever.
            # Measured in base-P1-r1: 17 act deadlines in 38 turns, the same
            # world_event injected as a MANDATORY UPCOMING EVENT twelve times
            # (turns 11-37), and the Director duly re-sealed the same doors seven
            # times (docs/cases/20-repetition-baseline-2026-08-01.md).
            #
            # A story that runs out of acts gets NEW acts. Scope "act" is the
            # right tool and already exists: it keeps the premise, keeps every
            # act already played, and splices the rewrite after them — which at
            # the terminal act means appending. Regenerating from scratch would
            # mint a fresh premise and restart the story instead of continuing
            # it.
            acts_before = len(game.roteiro.acts)
            terminal = game.roteiro.act_index + 1 >= acts_before
            if not terminal:
                game.roteiro.act_index += 1
            game.roteiro.act_started_tick = game.narrative_tick
            game.roteiro.beat_replans_in_act = 0
            game.roteiro = await replan_roteiro(
                self.client,
                game,
                ReplanDecision(
                    action="replan_act" if terminal else "replan_beat",
                    reason="act_deadline",
                ),
                self.config,
                turn_number,
                current_tick=game.narrative_tick,
            )
            if terminal:
                # Own the landing deterministically; `replan_roteiro` advances
                # only when the model volunteers `act_completed`, and the clock
                # must not depend on that.
                grew = len(game.roteiro.acts) > acts_before
                # Safety valve: a replan that returns no usable act must STOP the
                # clock, never re-fire it. Otherwise one bad generation trades a
                # repeated event for a repeated expensive call.
                game.roteiro.act_index = acts_before if grew else len(game.roteiro.acts)
                game.roteiro.act_started_tick = game.narrative_tick
                log_roteiro_decision(
                    game.session_id,
                    turn_number,
                    action="act_regenerate" if grew else "act_clock_stopped",
                    reason="acts_exhausted",
                    beat_id=game.roteiro.beat.beat_id if game.roteiro.beat else "none",
                    anchors_missing=[],
                    actors_missing=[],
                )
            return world_event or None
        decision = evaluate_roteiro(
            game.roteiro, game.history, game.player.controlled_character_id, next_turn
        )
        log_roteiro_decision(
            game.session_id,
            turn_number,
            action=decision.action or "none",
            reason=decision.reason,
            beat_id=game.roteiro.beat.beat_id if game.roteiro.beat else "none",
            anchors_missing=list(decision.progress.anchors_missing) if decision.progress else [],
            actors_missing=list(decision.progress.actors_missing) if decision.progress else [],
        )
        if decision.action:
            game.roteiro = await replan_roteiro(
                self.client,
                game,
                decision,
                self.config,
                turn_number,
                current_tick=game.narrative_tick,
            )
        return None

    async def _call_narrator(
        self,
        game: GameState,
        turn_number: int,
        forced_speaker: str | None = None,
        narrator_hint: str = "",
        hint_is_control_signal: bool = False,
        extra_context: list[str] | None = None,
        extra_schema_properties: dict[str, Any] | None = None,
        extra_schema_required: list[str] | None = None,
        exclude_controlled: bool = True,
    ) -> dict:
        """Calls Narrator agent (blind) with full context. Returns result."""
        # The player initiated this turn (actively or by skipping/passing), so exclude them
        # from being chosen as the next speaker to prevent immediate dialogue loops. During a
        # multi-beat continuation (Task 45) this holds for the first BURST_PROTAGONIST_EXCLUDE_BEATS
        # beats so the world reacts first, then the protagonist becomes eligible again and the
        # Narrator choosing them ends the burst.
        exclude_speaker = game.player.controlled_character_id if exclude_controlled else None

        roteiro_lines = (
            describe_roteiro_for_director(game.roteiro, game.characters)
            if game.roteiro is not None
            else None
        )
        return await narrate(
            client=self.client,
            scene=game.scene,
            characters=game.characters,
            player_controlled_id=game.player.controlled_character_id,
            history=game.history,
            config=self.config,
            narrator_directives=game.narrator_directives,
            session_id=game.session_id,
            turn_number=turn_number,
            story_summary=game.story_summary,
            forced_speaker=forced_speaker,
            narrator_hint=narrator_hint,
            hint_is_control_signal=hint_is_control_signal,
            exclude_speaker=exclude_speaker,
            extra_context=extra_context,
            extra_schema_properties=extra_schema_properties,
            extra_schema_required=extra_schema_required,
            roteiro_lines=roteiro_lines,
        )

    async def _render_narration(
        self,
        game: GameState,
        events: list[dict[str, Any]],
        turn_number: int,
    ) -> str:
        """Blind prose renderer boundary (Task 36) — injectable like the other agents."""
        return await render_narration(
            self.client,
            game.scene,
            game.characters,
            game.player.controlled_character_id,
            game.history,
            events,
            self.config,
            session_id=game.session_id,
            turn_number=turn_number,
        )

    async def _ensure_perspective(
        self,
        game: GameState,
        viewer_id: str,
        turn_number: int,
    ) -> None:
        """Initialize/refresh one viewer's identity ledger inside the turn draft.

        Lazy and transactional: the ledger is compiled from the viewer's priors
        the first time this viewer is about to speak, and the small identity
        updater runs only when the deterministic predicate says it can matter
        (strangers remain AND new speech became visible to the viewer). Both
        calls commit with the turn or not at all.
        """
        perspective = game.character_perspectives.get(viewer_id)
        if perspective is None:
            perspective = await initialize_perspective(
                self.client,
                viewer_id,
                game.characters,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )
            game.character_perspectives[viewer_id] = perspective
        if needs_identity_update(game.history, viewer_id, perspective):
            await update_identity(
                self.client,
                viewer_id,
                perspective,
                game.history,
                game.characters,
                game.player.controlled_character_id,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )
        # Durable memory (Task 39): fold what this viewer has perceived since it
        # last spoke into its ledger memory — deterministic, no LLM, so rapport
        # accumulates within the session without waiting for a compaction.
        capture_memory(
            perspective,
            game.history,
            viewer_id,
            game.characters,
            game.player.controlled_character_id,
        )
        if needs_memory_revision(perspective):
            # Semantic revision (Task 39 inc.2): condense the older digest into
            # memory_summary instead of losing it to the MAX bound. Maintenance
            # call - failures are swallowed inside and retried on a later turn.
            await revise_memory(
                self.client,
                viewer_id,
                perspective,
                game.characters,
                self.config,
                session_id=game.session_id,
                turn_number=turn_number,
            )

    async def _alignment_impulse(self, game: GameState, character_id: str, turn_number: int) -> str:
        """Task 44 Toggle 2: a transient dramatic impulse for an expected actor of the
        current beat, tilting their CHOICE toward it (never dictating the action).

        No-op unless BOTH roteiro flags are on. NEVER applied to the controlled
        character (agency lock). Leak-safe by construction: the impulse is one of a
        fixed vocabulary, the private beat only feeds an enum-constrained Director-side
        call whose output never reaches the character as free text.
        """
        if not (
            self.config.get("roteiro_enabled")
            and self.config.get("character_roteiro_alignment_enabled")
        ):
            return ""
        if character_id == game.player.controlled_character_id:
            return ""
        roteiro = game.roteiro
        if roteiro is None or roteiro.beat is None:
            return ""
        if character_id not in roteiro.beat.expected_actors:
            return ""
        return await derive_alignment_impulse(
            self.client,
            roteiro.beat.intent,
            game.characters[character_id],
            self.config,
            session_id=game.session_id,
            turn_number=turn_number,
        )

    async def _call_character(
        self,
        game: GameState,
        character_id: str,
        context: str,
        turn_number: int,
        reply_audience: list[str] | None = None,
        speech_intents: list[str] | None = None,
    ) -> CharacterOutput:
        """Calls Character agent with filtered context. Returns the content."""
        return await character_act(
            client=self.client,
            character=game.characters[character_id],
            context=context,
            history=game.history,
            characters=game.characters,
            controlled_id=game.player.controlled_character_id,
            character_id=character_id,
            config=self.config,
            session_id=game.session_id,
            turn_number=turn_number,
            scene=game.scene,
            reply_audience=reply_audience,
            viewer_perspective=game.character_perspectives.get(character_id),
            dispositions=game.dispositions,
            alignment_impulse=await self._alignment_impulse(game, character_id, turn_number),
            speech_intents=speech_intents,
        )

    def _update_scene(self, game: GameState, scene_update: dict | None) -> None:
        """Applies reserved Scene fields and physical-fact deltas.

        ``location`` and ``time_of_day`` belong to ``Scene`` itself and must
        never be persisted as physical facts. Moving to a different location
        also discards facts from the previous scene before applying the new
        delta. A ``None`` value removes a physical fact, but cannot erase a
        required reserved field.
        """
        if not scene_update:
            return

        location = scene_update.get("location")
        if isinstance(location, str) and location.strip():
            normalized_location = location.strip()
            if normalized_location != game.scene.location:
                game.scene.location = normalized_location
                game.scene.physical_facts.clear()

        time_of_day = scene_update.get("time_of_day")
        if isinstance(time_of_day, str) and time_of_day.strip():
            game.scene.time_of_day = time_of_day.strip()

        for key, value in scene_update.items():
            if key in {"location", "time_of_day"}:
                continue
            if value is not None and not _fact_key_admissible(key, game.scene.physical_facts):
                continue
            if value is None:
                game.scene.physical_facts.pop(key, None)
            else:
                game.scene.physical_facts[key] = value
                _evict_oldest_facts(game.scene.physical_facts)

    def _update_moods(self, game: GameState, mood_updates: dict[str, str]) -> None:
        """Applies the new mood decided by the Narrator to each affected character."""
        for character_id, mood in mood_updates.items():
            if character_id in game.characters:
                game.characters[character_id].mind.current_mood = mood

    def _append_history(
        self,
        game: GameState,
        speaker: str,
        content: str,
        content_type: str,
        turn_number: int,
        input_transformed: bool = False,
        audience: list[str] | None = None,
        audience_origin: str | None = None,
    ) -> None:
        """Creates a TurnRecord with deepcopy of the Scene/moods and adds it to history.

        ```turn_number`` is explicit — all records of the same turn
        (human speech/thought/action, narration, Character speech) share the
        same number and the same snapshot, a pre-requisite for undo to revert
        the entire step (scene and moods).

        With a zone graph, perception is structural: a speech/action record's
        effective audience is computed from who can physically perceive the
        speaker's zone. A supplied whisper audience is intersected with it (you
        cannot whisper to someone who cannot hear you); a public record that not
        everyone can perceive becomes zone-scoped by construction, reusing the
        whisper visibility machinery end to end.

        ``audience_origin`` defaults to the usual rule (``whisper`` when an
        audience is supplied, else ``zone``) AND runs the zone recomputation.
        Passing it explicitly takes the given ``audience`` as AUTHORITATIVE
        (no zone recompute) with that origin — used to persist a Director
        ``audible_speech`` event, whose ``witness_ids`` are already zone-clamped
        and are perception scoping, never a whisper secret.
        """
        # An explicit origin means the caller's audience is already authoritative
        # (a Director audible_speech event), so the zone recompute is skipped.
        if audience_origin is None:
            audience_origin = "whisper" if audience is not None else "zone"
            if game.scene.zones and content_type in ("speech", "action"):
                subject = game.player.controlled_character_id if speaker == "Player" else speaker
                if subject in game.characters:
                    eligible = eligible_witnesses(game.scene, game.characters, subject)
                    others = {
                        cid
                        for cid in game.scene.present_characters
                        if cid in game.characters and cid != subject
                    }
                    if audience is None:
                        if eligible != others:
                            audience = sorted(eligible)
                    else:
                        audience = sorted(set(audience) & (eligible | {subject}))
        record = TurnRecord(
            turn_number=turn_number,
            speaker=speaker,
            content=content,
            content_type=content_type,
            scene_snapshot=copy.deepcopy(game.scene),
            input_transformed=input_transformed,
            mood_snapshot={cid: ch.mind.current_mood for cid, ch in game.characters.items()},
            plugin_state_snapshot=copy.deepcopy(game.plugin_state),
            audience=list(audience) if audience is not None else None,
            audience_origin=audience_origin,
            perspective_snapshot={
                viewer_id: perspective_to_dict(perspective)
                for viewer_id, perspective in game.character_perspectives.items()
            },
            disposition_snapshot=asdict(game.dispositions),
        )
        game.history.append(record)
