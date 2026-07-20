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

import unicodedata
from dataclasses import dataclass
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
PARTIAL_ADVANCE_PATIENCE = 2  # turns before a near-covered beat advances anyway
# Hard ceiling on how many turns one beat may stay active, regardless of its
# declared budget or how many anchors remain. Beyond this the scene is moving
# on: a beat held longer makes the Director re-stage the same tableau (measured
# on the portais scene, where a 5-turn beat produced three identical turns).
# Drive over completeness - a stuck beat replans into a fresh situation.
HARD_BEAT_TURN_CAP = 3
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


def _beat_records(history: list[TurnRecord], since_turn: int) -> list[TurnRecord]:
    return [
        rec
        for rec in history
        if rec.turn_number >= since_turn and rec.content_type in _PROGRESS_RECORD_TYPES
    ]


def collect_beat_evidence(roteiro: Roteiro, texts: list[str]) -> list[str]:
    """Anchors of the current beat newly witnessed in ``texts`` (never duplicated).

    Called by the runner with the AUTHORITATIVE evidence of a beat: the typed
    perception events the Director staged, plus what the characters themselves
    said or did. Deliberately not the prose: the renderer paraphrases, and
    audible speech never reaches it at all — measuring coverage there punished
    the Director for obeying (a whole beat's murmur staged three times, unseen).
    """
    beat = roteiro.beat
    if beat is None:
        return []
    return [
        anchor
        for anchor in beat.expected_anchors
        if anchor not in roteiro.anchors_seen
        and any(anchor_matched(anchor, text) for text in texts)
    ]


def measure_beat_progress(
    roteiro: Roteiro,
    history: list[TurnRecord],
    controlled_id: str,
) -> BeatProgress:
    """Coverage of the rolling beat: which anchors/actors the story has touched.

    Anchors come from ``roteiro.anchors_seen`` (accumulated from authoritative
    evidence, see ``collect_beat_evidence``) plus this beat's history records,
    so an anchor a character speaks about also counts. An actor counts when
    they themselves spoke or acted since the beat began. The disengaged streak
    counts trailing turn numbers where NOTHING touched the beat (drift input).
    """
    beat = roteiro.beat
    assert beat is not None
    records = _beat_records(history, roteiro.beat_started_turn)

    def _actor_of(rec: TurnRecord) -> str:
        return controlled_id if rec.speaker == "Player" else rec.speaker

    anchors_hit = {
        anchor
        for anchor in beat.expected_anchors
        if anchor in roteiro.anchors_seen
        or any(anchor_matched(anchor, rec.content) for rec in records)
    }
    actors_hit = {
        actor
        for actor in beat.expected_actors
        if any(
            _actor_of(rec) == actor and rec.content_type in ("speech", "action") for rec in records
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

    # Partial-coverage advance: a beat that has landed its actors and all but
    # one stubborn anchor should MOVE ON rather than grind to a budget-stall on
    # the holdout — holding identical beat text across many turns is what pins
    # the scene into re-staged stimuli and re-injected lore (round-1 critic:
    # a beat missing one anchor pinned the story for five turns). Drive over
    # completeness: the roteiro is guidance, not a checklist.
    substantial = (
        not progress.actors_missing
        and len(progress.anchors_hit) >= 1
        and len(progress.anchors_missing) <= 1
    )
    if substantial and progress.turns_elapsed >= PARTIAL_ADVANCE_PATIENCE:
        return ReplanDecision(action="advance", reason="coverage_sufficient", progress=progress)

    # A beat stalls at its declared budget OR the hard turn cap, whichever comes
    # first — the cap guarantees no beat can pin the scene into static repetition.
    stall_at = min(roteiro.beat.budget_turns, HARD_BEAT_TURN_CAP)
    stalled = progress.turns_elapsed >= stall_at
    drifted = (
        progress.turns_elapsed >= DRIFT_WINDOW_TURNS
        and progress.disengaged_streak >= DRIFT_WINDOW_TURNS
    )
    if not stalled and not drifted:
        return ReplanDecision(action=None, reason="in_progress", progress=progress)
    if next_turn < roteiro.cooldown_until_turn:
        return ReplanDecision(action=None, reason="cooldown", progress=progress)
    # Disengaged (the scene moved away) is labelled "drifted"; an engaged beat
    # that simply ran out of time is "stalled". Both replan; the label is the
    # evidence signal.
    reason = "drifted" if drifted else "stalled"
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
    pending = [a for a in beat.expected_anchors if a not in roteiro.anchors_seen]
    if pending:
        # Only what has NOT landed yet: an anchor already in play would just
        # invite the Director to stage the same prop twice.
        lines.append(
            f"    Not in play yet — introduce as concrete perception events: {', '.join(pending)}"
        )
    if beat.exit_condition:
        lines.append(f"    The beat ends when: {beat.exit_condition}")
    lines.append(
        "    This beat may span turns: each turn ADVANCE the situation with a "
        "new development or pressure toward its end. Never restage what already "
        "happened or repeat a prior beat's framing; if it is already in play, "
        "push it forward."
    )
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


def _validate_beat(raw: object, game: GameState, fallback_id: str) -> RoteiroBeat:
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
        try:
            duration = int(item.get("duration_ticks", 0))
        except (TypeError, ValueError):
            duration = 0
        acts.append(
            RoteiroAct(
                act_id=str(item.get("act_id") or f"act{index + 1}").strip(),
                summary=str(item["summary"]).strip(),
                exit_condition=str(item.get("exit_condition", "")).strip(),
                duration_ticks=max(0, min(12, duration)),
                world_event=str(item.get("world_event", "")).strip()[:300],
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
        rec for rec in game.history[-recent_turns:] if rec.content_type in _PROGRESS_RECORD_TYPES
    ]
    if recent:
        lines.append("RECENT EVENTS (oldest to newest):")
        for rec in recent:
            speaker = controlled if rec.speaker == "Player" else rec.speaker
            name = game.characters[speaker].mind.name if speaker in game.characters else rec.speaker
            lines.append(f"  {name}: {rec.content[:160]}")
    return lines


_ARCHITECT_RULES = (
    "You are the story architect for a multi-character roleplay. You write a\n"
    "PRIVATE roteiro consumed only by the scene Director — the characters and\n"
    "the reader never see it.\n"
    "Rules:\n"
    "- Beats plan SITUATIONS and pressures, never anyone's decisions. The\n"
    "  protagonist's choices are sacred: plan around them, not for them.\n"
    "- ESCALATE. Every beat must raise the stakes with a NEW external pressure\n"
    "  that physically enters or changes the scene (an arrival, a threat, a\n"
    "  discovery, a thing breaking, a deadline closing). The world does not\n"
    "  wait for the protagonist; danger and events advance on their own. Tension\n"
    "  must rise from act to act, never plateau in talk.\n"
    "- SITUATIONS, NOT EXPOSITION. Never plan a beat whose content is a\n"
    "  character telling backstory, lore, or history, or the cast discussing the\n"
    "  past. Reveal the past ONLY through a present physical event the scene can\n"
    "  show. A beat is something that HAPPENS, not something explained.\n"
    "- expected_actors: character IDs (never the protagonist) who should get\n"
    "  stage time during the beat.\n"
    "- expected_anchors: 2-4 short CONCRETE tokens (objects, places, names) that\n"
    "  physically ENTER or CHANGE in the scene when the beat lands, not topics\n"
    "  of conversation. Measurable, not abstract.\n"
    "- exit_condition: one observable sentence describing how the beat ends.\n"
    "- budget_turns: how many turns the beat deserves (2-10).\n"
    "- Each act declares duration_ticks (2-8 turns it deserves) and world_event:\n"
    "  ONE concrete event the WORLD performs to force the act's conclusion if\n"
    "  the cast has not finished by then (the bell rings and the first pair is\n"
    "  announced; the guards arrive; the fire reaches the door). The world\n"
    "  never waits for conversation to finish. It must CONCLUDE this act's\n"
    "  business, not open an unrelated thread.\n"
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
                            "duration_ticks": {"type": "integer"},
                            "world_event": {"type": "string"},
                        },
                        "required": [
                            "act_id",
                            "summary",
                            "exit_condition",
                            "duration_ticks",
                            "world_event",
                        ],
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
    status = {
        "advance": "The current beat COMPLETED (its actors and anchors all landed).",
        "coverage_complete": "The current beat COMPLETED (its actors and anchors all landed).",
        "coverage_sufficient": (
            "The current beat is essentially DONE (actors and nearly all anchors "
            "landed); move the story on rather than dwell."
        ),
        "stalled": (
            "The current beat STALLED: the scene is STUCK, circling one topic "
            "without a new development (measured: the same events/subject repeat). "
            "The next beat MUST be a concrete external DISRUPTION that happens THIS "
            "turn - an arrival, an interruption, something breaking or bursting in - "
            "that changes what the scene is ABOUT. Never continue or rephrase the "
            "stalled topic."
        ),
        "drifted": (
            "The story DRIFTED away from the current beat: recent turns touch "
            "neither its actors nor its anchors. Plan from where the story actually "
            "is, and open the next beat with a concrete event that happens now."
        ),
        "no_beat": "There is no current beat.",
        "act_deadline": (
            "The narrative CLOCK expired this act: its world_event just happened "
            "(it is already staged). Open the NEXT act with a beat that follows "
            "directly from that event."
        ),
    }.get(reason, reason)
    lines = _story_context_lines(game)
    lines.append("")
    lines.append(f"PREMISE: {roteiro.premise}")
    for index, item in enumerate(roteiro.acts):
        marker = " <- current" if index == roteiro.act_index else ""
        lines.append(
            f"ACT {item.act_id}: {item.summary} | exits when: {item.exit_condition}{marker}"
        )
    if beat is not None:
        lines.append(f"CURRENT BEAT ({beat.beat_id}): {beat.intent} | exit: {beat.exit_condition}")
    if roteiro.beat_log:
        lines.append("BEAT LOG: " + "; ".join(roteiro.beat_log[-6:]))
    lines.append(f"STATUS: {status}")
    if scope == "act":
        task = (
            "The current act plan no longer fits the story. Rewrite the acts that\n"
            "come AFTER the current one (keep the premise; the current act and any\n"
            "already played stay as they are — do NOT restate them). Then produce\n"
            "the next beat contract. Also return act_completed for whether the\n"
            "current act's exit condition has been met."
        )
    else:
        task = (
            "Produce the NEXT beat contract. Follow STATUS above: if the scene\n"
            "stalled, the beat must be a concrete disruption that changes the\n"
            "subject, even mid-act; otherwise continue the current act (or open the\n"
            "next act if its exit condition has been met). Set act_completed\n"
            "accordingly."
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
    current_tick: int = 0,
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
            # Defensive dedupe: the model tends to restate the current act as
            # its first "new" one, which would leave two identical acts in the
            # skeleton — drop any rewrite act that near-repeats a kept one.
            kept = acts[: act_index + 1]
            kept_summaries = [_normalize(a.summary) for a in kept]
            deduped = [
                act
                for act in new_acts
                if not any(
                    SequenceMatcher(None, _normalize(act.summary), kept_summary).ratio() > 0.85
                    for kept_summary in kept_summaries
                )
            ]
            acts = kept + deduped
        replans_in_act = 0
    if (
        bool(result.get("act_completed"))
        and act_index < len(acts) - 1
        and decision.reason != "act_deadline"  # deadline advance is code-owned
    ):
        act_index += 1
        replans_in_act = 0
    if decision.action == "replan_beat" and decision.reason in ("stalled", "drifted"):
        replans_in_act += 1

    outcome = decision.reason if decision.action != "advance" else "completed"
    old_id = roteiro.beat.beat_id if roteiro.beat else "none"
    started_tick = current_tick if act_index != roteiro.act_index else roteiro.act_started_tick
    return Roteiro(
        premise=roteiro.premise,
        acts=acts,
        act_index=act_index,
        beat=beat,
        beat_started_turn=turn_number,
        act_started_tick=started_tick,
        anchors_seen=[],  # new beat, coverage starts empty
        cooldown_until_turn=turn_number + COOLDOWN_TURNS,
        beat_replans_in_act=replans_in_act,
        beat_log=(roteiro.beat_log + [f"{old_id}: {outcome}"])[-20:],
    )
