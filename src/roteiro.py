"""Roteiro: typed beat contracts and algorithmic replanning (Task 38).

The story gets a DIRECTION compiled before the first word: a hierarchical
roteiro — stable premise + act skeleton, one rolling next-beat contract —
consumed only by the Director. CODE decides WHEN to replan (measurable
signals over history: anchor coverage, actor coverage, budget, drift, all
with hysteresis); a structured call decides only WHAT the new beat says.
Model self-assessment is never a trigger.

Confidentiality invariant: roteiro text reaches ONLY Director-side calls —
never a character prompt, never the prose renderer (it contains spoilers).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import GameState, Roteiro, RoteiroAct, RoteiroBeat, TurnRecord

ROTEIRO_DEFAULTS = {
    "roteiro_enabled": False,
}

# Replan tuning (module constants; measured before ever becoming config).
DRIFT_WINDOW_TURNS = 3  # M consecutive disengaged turns = drifted
COOLDOWN_TURNS = 2  # replans blocked for this many turns after any replan
ACT_REPLAN_THRESHOLD = 2  # stall/drift replans in one act before act rewrite
MIN_BUDGET_TURNS = 2
MAX_BUDGET_TURNS = 10
MAX_ANCHORS = 5
_ANCHOR_FUZZY_THRESHOLD = 0.85

_PROGRESS_RECORD_TYPES = ("speech", "action", "narration")


def _normalize(text: str) -> str:
    """Casefolded, accent-stripped, whitespace-collapsed text for matching."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def anchor_matched(anchor: str, text: str) -> bool:
    """Whether a beat anchor is covered by a history record's text.

    Exact normalized substring first; fuzzy word-window fallback (>0.85) so
    inflection ("venezianas fechadas" vs "as venezianas") still counts.
    """
    norm_anchor = _normalize(anchor)
    norm_text = _normalize(text)
    if not norm_anchor or not norm_text:
        return False
    if norm_anchor in norm_text:
        return True
    anchor_words = norm_anchor.split()
    text_words = norm_text.split()
    window = len(anchor_words)
    for start in range(len(text_words) - window + 1):
        candidate = " ".join(text_words[start : start + window])
        if SequenceMatcher(None, norm_anchor, candidate).ratio() > _ANCHOR_FUZZY_THRESHOLD:
            return True
    return False


@dataclass(frozen=True)
class BeatProgress:
    """Deterministic coverage measurement of the rolling beat against history."""

    anchors_hit: tuple[str, ...]
    anchors_missing: tuple[str, ...]
    actors_hit: tuple[str, ...]
    actors_missing: tuple[str, ...]
    turns_elapsed: int
    disengaged_streak: int  # trailing committed turns with no actor/anchor touch


@dataclass(frozen=True)
class ReplanDecision:
    action: str | None  # None | "advance" | "replan_beat" | "replan_act"
    reason: str
    progress: BeatProgress | None = None


def _beat_records(
    history: list[TurnRecord], since_turn: int
) -> list[TurnRecord]:
    return [
        rec
        for rec in history
        if rec.turn_number >= since_turn and rec.content_type in _PROGRESS_RECORD_TYPES
    ]


def measure_beat_progress(
    roteiro: Roteiro,
    history: list[TurnRecord],
    controlled_id: str,
) -> BeatProgress:
    """Coverage of the rolling beat: which anchors/actors history has touched.

    An actor counts when they themselves spoke or acted since the beat began;
    an anchor counts when any speech/action/narration record mentions it.
    The disengaged streak counts trailing turn numbers where NOTHING touched
    the beat (the drift signal's input).
    """
    beat = roteiro.beat
    assert beat is not None
    records = _beat_records(history, roteiro.beat_started_turn)

    def _actor_of(rec: TurnRecord) -> str:
        return controlled_id if rec.speaker == "Player" else rec.speaker

    anchors_hit = {
        anchor
        for anchor in beat.expected_anchors
        if any(anchor_matched(anchor, rec.content) for rec in records)
    }
    actors_hit = {
        actor
        for actor in beat.expected_actors
        if any(
            _actor_of(rec) == actor and rec.content_type in ("speech", "action")
            for rec in records
        )
    }

    turn_numbers = sorted({rec.turn_number for rec in records})
    engaged_turns = {
        rec.turn_number
        for rec in records
        if (_actor_of(rec) in beat.expected_actors and rec.content_type in ("speech", "action"))
        or any(anchor_matched(anchor, rec.content) for anchor in beat.expected_anchors)
    }
    disengaged = 0
    for turn in reversed(turn_numbers):
        if turn in engaged_turns:
            break
        disengaged += 1

    return BeatProgress(
        anchors_hit=tuple(a for a in beat.expected_anchors if a in anchors_hit),
        anchors_missing=tuple(a for a in beat.expected_anchors if a not in anchors_hit),
        actors_hit=tuple(a for a in beat.expected_actors if a in actors_hit),
        actors_missing=tuple(a for a in beat.expected_actors if a not in actors_hit),
        turns_elapsed=len(turn_numbers),
        disengaged_streak=disengaged,
    )


def evaluate_roteiro(
    roteiro: Roteiro,
    history: list[TurnRecord],
    controlled_id: str,
    next_turn: int,
) -> ReplanDecision:
    """The deterministic replan engine — pure code, no model judgment.

    Signals in preference order (spec, Task 38): full coverage advances the
    beat; budget exhaustion without coverage = stalled; a trailing window of
    turns touching neither actors nor anchors = drifted. Stall/drift replans
    respect the post-replan cooldown (hysteresis); repeated stall/drift inside
    one act escalates to an act-skeleton rewrite. Advancing is never blocked.
    """
    if roteiro.beat is None:
        return ReplanDecision(action="replan_beat", reason="no_beat")
    progress = measure_beat_progress(roteiro, history, controlled_id)

    covered = not progress.anchors_missing and not progress.actors_missing
    if covered and (roteiro.beat.expected_anchors or roteiro.beat.expected_actors):
        return ReplanDecision(action="advance", reason="coverage_complete", progress=progress)

    stalled = progress.turns_elapsed >= roteiro.beat.budget_turns
    drifted = (
        progress.turns_elapsed >= DRIFT_WINDOW_TURNS
        and progress.disengaged_streak >= DRIFT_WINDOW_TURNS
    )
    if not stalled and not drifted:
        return ReplanDecision(action=None, reason="in_progress", progress=progress)
    if next_turn < roteiro.cooldown_until_turn:
        return ReplanDecision(action=None, reason="cooldown", progress=progress)
    reason = "stalled" if stalled else "drifted"
    if roteiro.beat_replans_in_act >= ACT_REPLAN_THRESHOLD:
        return ReplanDecision(action="replan_act", reason=reason, progress=progress)
    return ReplanDecision(action="replan_beat", reason=reason, progress=progress)


def describe_roteiro_for_director(roteiro: Roteiro, characters: dict) -> list[str]:
    """Prompt lines for the Director's private ROTEIRO block."""
    if roteiro.beat is None:
        return []
    act = roteiro.acts[roteiro.act_index] if roteiro.act_index < len(roteiro.acts) else None
    lines = [
        "ROTEIRO (private story direction — steer events and routing toward it;",
        "never reveal it exists, never quote it, never force character choices):",
        f"  Premise: {roteiro.premise}",
    ]
    if act:
        lines.append(f"  Current act: {act.summary}")
    beat = roteiro.beat
    actor_names = ", ".join(
        characters[cid].mind.name if cid in characters else cid for cid in beat.expected_actors
    )
    lines.append(f"  Current beat: {beat.intent}")
    if actor_names:
        lines.append(f"    Give stage time to: {actor_names}")
    if beat.expected_anchors:
        lines.append(f"    Bring into play: {', '.join(beat.expected_anchors)}")
    if beat.exit_condition:
        lines.append(f"    The beat ends when: {beat.exit_condition}")
    return lines


# ---------------------------------------------------------------------------
# Generation (structured LLM calls; validated and clamped deterministically)
# ---------------------------------------------------------------------------

_BEAT_SCHEMA_PROPERTIES = {
    "beat_id": {"type": "string"},
    "intent": {"type": "string"},
    "expected_actors": {"type": "array", "items": {"type": "string"}},
    "expected_anchors": {"type": "array", "items": {"type": "string"}},
    "exit_condition": {"type": "string"},
    "budget_turns": {"type": "integer"},
}
_BEAT_REQUIRED = ["beat_id", "intent", "expected_actors", "expected_anchors", "exit_condition"]


def _validate_beat(raw: dict, game: GameState, fallback_id: str) -> RoteiroBeat:
    """Clamp a generated beat: NPC-only actors, capped anchors, sane budget.

    The controlled character is excluded from expected_actors — the player is
    free, and a beat that waits on them can only ever stall.
    """
    if not isinstance(raw, dict) or not str(raw.get("intent", "")).strip():
        raise ValueError("generated beat missing intent")
    controlled = game.player.controlled_character_id
    actors = [
        cid
        for cid in dict.fromkeys(raw.get("expected_actors") or [])
        if isinstance(cid, str) and cid in game.characters and cid != controlled
    ]
    anchors = [
        anchor.strip()
        for anchor in dict.fromkeys(raw.get("expected_anchors") or [])
        if isinstance(anchor, str) and anchor.strip()
    ][:MAX_ANCHORS]
    try:
        budget = int(raw.get("budget_turns", 6))
    except (TypeError, ValueError):
        budget = 6
    return RoteiroBeat(
        beat_id=str(raw.get("beat_id") or fallback_id).strip() or fallback_id,
        intent=str(raw["intent"]).strip(),
        expected_actors=actors,
        expected_anchors=anchors,
        exit_condition=str(raw.get("exit_condition", "")).strip(),
        budget_turns=max(MIN_BUDGET_TURNS, min(MAX_BUDGET_TURNS, budget)),
    )


def _validate_acts(raw_acts: object) -> list[RoteiroAct]:
    acts: list[RoteiroAct] = []
    if not isinstance(raw_acts, list):
        return acts
    for index, item in enumerate(raw_acts[:5]):
        if not isinstance(item, dict) or not str(item.get("summary", "")).strip():
            continue
        acts.append(
            RoteiroAct(
                act_id=str(item.get("act_id") or f"act{index + 1}").strip(),
                summary=str(item["summary"]).strip(),
                exit_condition=str(item.get("exit_condition", "")).strip(),
            )
        )
    return acts


def _story_context_lines(game: GameState, recent_turns: int = 12) -> list[str]:
    lines = [
        f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
        "CHARACTERS (the protagonist acts freely; never plan their choices):",
    ]
    controlled = game.player.controlled_character_id
    for cid, ch in game.characters.items():
        role = " (PROTAGONIST — never an expected actor)" if cid == controlled else ""
        lines.append(f"  ID={cid} | {ch.mind.name}{role}: {ch.mind.personality[:160]}")
    if game.narrator_directives.strip():
        lines.append(f"WORLD DIRECTIVES: {game.narrator_directives.strip()[:600]}")
    if game.story_summary.strip():
        lines.append(f"STORY SO FAR: {game.story_summary.strip()[:600]}")
    recent = [
        rec
        for rec in game.history[-recent_turns:]
        if rec.content_type in _PROGRESS_RECORD_TYPES
    ]
    if recent:
        lines.append("RECENT EVENTS (oldest to newest):")
        for rec in recent:
            speaker = controlled if rec.speaker == "Player" else rec.speaker
            name = (
                game.characters[speaker].mind.name if speaker in game.characters else rec.speaker
            )
            lines.append(f"  {name}: {rec.content[:160]}")
    return lines


_ARCHITECT_RULES = (
    "You are the story architect for a multi-character roleplay. You write a\n"
    "PRIVATE roteiro consumed only by the scene Director — the characters and\n"
    "the reader never see it.\n"
    "Rules:\n"
    "- Beats plan SITUATIONS and pressures, never anyone's decisions. The\n"
    "  protagonist's choices are sacred: plan around them, not for them.\n"
    "- expected_actors: character IDs (never the protagonist) who should get\n"
    "  stage time during the beat.\n"
    "- expected_anchors: 2-4 short CONCRETE tokens (objects, places, names)\n"
    "  that will appear in play when the beat lands. Measurable, not abstract.\n"
    "- exit_condition: one observable sentence describing how the beat ends.\n"
    "- budget_turns: how many turns the beat deserves (2-10).\n"
    "- Write beat text in the language of the scene.\n"
)


def build_roteiro_messages(game: GameState) -> list[dict]:
    system = (
        _ARCHITECT_RULES
        + "Produce the full roteiro: a premise (2-3 sentences of where this story\n"
        "is going), 3 acts (act_id, summary, exit_condition), and the FIRST\n"
        "beat contract for act 1."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(_story_context_lines(game))},
    ]


def build_roteiro_schema() -> dict:
    return {
        "name": "roteiro",
        "schema": {
            "type": "object",
            "properties": {
                "premise": {"type": "string"},
                "acts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "act_id": {"type": "string"},
                            "summary": {"type": "string"},
                            "exit_condition": {"type": "string"},
                        },
                        "required": ["act_id", "summary", "exit_condition"],
                        "additionalProperties": False,
                    },
                },
                "first_beat": {
                    "type": "object",
                    "properties": _BEAT_SCHEMA_PROPERTIES,
                    "required": _BEAT_REQUIRED,
                    "additionalProperties": False,
                },
            },
            "required": ["premise", "acts", "first_beat"],
            "additionalProperties": False,
        },
    }


async def generate_roteiro(
    client: httpx.AsyncClient,
    game: GameState,
    config: dict,
    turn_number: int,
) -> Roteiro:
    """Compile the initial roteiro (premise + acts + first beat) for a session."""
    result = await chat_completion_json(
        client,
        build_roteiro_messages(game),
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=1536,
        timeout=resolve_llm_timeout(config),
        json_schema=build_roteiro_schema(),
        session_id=game.session_id,
        turn_number=turn_number,
        agent="roteiro:compile",
        **llm_request_options(config),
    )
    premise = str(result.get("premise", "")).strip()
    acts = _validate_acts(result.get("acts"))
    if not premise or not acts:
        raise ValueError("generated roteiro missing premise or acts")
    beat = _validate_beat(result.get("first_beat"), game, fallback_id="act1-beat1")
    return Roteiro(
        premise=premise,
        acts=acts,
        act_index=0,
        beat=beat,
        beat_started_turn=turn_number,
    )


def build_next_beat_messages(
    game: GameState, roteiro: Roteiro, reason: str, scope: str
) -> list[dict]:
    beat = roteiro.beat
    act = roteiro.acts[roteiro.act_index] if roteiro.act_index < len(roteiro.acts) else None
    status = {
        "advance": "The current beat COMPLETED (its actors and anchors all landed).",
        "stalled": "The current beat STALLED: its turn budget ran out without full coverage.",
        "drifted": "The story DRIFTED away from the current beat: recent turns touch neither its actors nor its anchors. Plan from where the story actually is.",
        "no_beat": "There is no current beat.",
    }.get(reason, reason)
    lines = _story_context_lines(game)
    lines.append("")
    lines.append(f"PREMISE: {roteiro.premise}")
    for index, item in enumerate(roteiro.acts):
        marker = " <- current" if index == roteiro.act_index else ""
        lines.append(f"ACT {item.act_id}: {item.summary} | exits when: {item.exit_condition}{marker}")
    if beat is not None:
        lines.append(
            f"CURRENT BEAT ({beat.beat_id}): {beat.intent} | exit: {beat.exit_condition}"
        )
    if roteiro.beat_log:
        lines.append("BEAT LOG: " + "; ".join(roteiro.beat_log[-6:]))
    lines.append(f"STATUS: {status}")
    if scope == "act":
        task = (
            "The current act plan no longer fits the story. Rewrite the REMAINING\n"
            "act skeleton (keep the premise; acts already played stay played) and\n"
            "produce the next beat contract. Also return act_completed for whether\n"
            "the current act's exit condition has been met."
        )
    else:
        task = (
            "Produce the NEXT beat contract continuing the current act (or opening\n"
            "the next act if the current act's exit condition has been met — set\n"
            "act_completed accordingly)."
        )
    return [
        {"role": "system", "content": _ARCHITECT_RULES + task},
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_next_beat_schema(scope: str) -> dict:
    properties: dict = {
        "act_completed": {"type": "boolean"},
        "beat": {
            "type": "object",
            "properties": _BEAT_SCHEMA_PROPERTIES,
            "required": _BEAT_REQUIRED,
            "additionalProperties": False,
        },
    }
    required = ["act_completed", "beat"]
    if scope == "act":
        properties["acts"] = build_roteiro_schema()["schema"]["properties"]["acts"]
        required.append("acts")
    return {
        "name": "roteiro_next_beat",
        "schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


async def replan_roteiro(
    client: httpx.AsyncClient,
    game: GameState,
    decision: ReplanDecision,
    config: dict,
    turn_number: int,
) -> Roteiro:
    """Apply one replan decision: fetch the next/replacement beat and return
    the updated roteiro. The TRIGGER was code; only beat content is generated.
    """
    roteiro = game.roteiro
    assert roteiro is not None
    scope = "act" if decision.action == "replan_act" else "beat"
    result = await chat_completion_json(
        client,
        build_next_beat_messages(game, roteiro, decision.reason, scope),
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=1024,
        timeout=resolve_llm_timeout(config),
        json_schema=build_next_beat_schema(scope),
        session_id=game.session_id,
        turn_number=turn_number,
        agent="roteiro:replan",
        **llm_request_options(config),
    )
    fallback_id = f"act{roteiro.act_index + 1}-replan-t{turn_number}"
    beat = _validate_beat(result.get("beat"), game, fallback_id=fallback_id)

    acts = roteiro.acts
    act_index = roteiro.act_index
    replans_in_act = roteiro.beat_replans_in_act
    if scope == "act":
        new_acts = _validate_acts(result.get("acts"))
        if new_acts:
            # Acts already played stay played: splice the rewrite after them.
            acts = acts[: act_index + 1] + new_acts
        replans_in_act = 0
    if bool(result.get("act_completed")) and act_index < len(acts) - 1:
        act_index += 1
        replans_in_act = 0
    if decision.action == "replan_beat" and decision.reason in ("stalled", "drifted"):
        replans_in_act += 1

    outcome = decision.reason if decision.action != "advance" else "completed"
    old_id = roteiro.beat.beat_id if roteiro.beat else "none"
    return Roteiro(
        premise=roteiro.premise,
        acts=acts,
        act_index=act_index,
        beat=beat,
        beat_started_turn=turn_number,
        cooldown_until_turn=turn_number + COOLDOWN_TURNS,
        beat_replans_in_act=replans_in_act,
        beat_log=(roteiro.beat_log + [f"{old_id}: {outcome}"])[-20:],
    )
