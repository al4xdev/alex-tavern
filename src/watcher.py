"""Roteiro watcher (Task 33b): delta auditor (piece 1) + recovery ladder (piece 2).

A stalled scene is not a scene where nothing is *said* — the characters keep
talking — it is one where nothing materially *changes*: no decision is taken,
no information is revealed, no position shifts, no attempt earns a consequence.
Lexical anchors (task 23) miss this: the words move, the story does not.

Piece 1 (LLM) isolates ONE structured call that reads the most recent narrating
turn against the scene that preceded it and reports which material deltas — if
any — that turn realized. An empty verdict (or the explicit ``none``) is the
signal of semantic immobility. Like ``drive.py`` it is a blind, isolated
auditor: it never plays a move and never sees which arm produced the turn.

Piece 2 (pure code) is the recovery ladder that CONSUMES that signal against
the task-40 narrative clock. As immobility persists it climbs a fixed
escalation — execute a promised transition, adjudicate a dangling attempt,
allow one beat of silence, reincorporate an open thread, and only THEN disrupt
with a causal intervention (piece 3). The ladder never talks to the model: it
decides which recovery *kind* to take, deterministically, from an explicit
context. Toggle OFF by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import GameState, speaker_label

# The material-delta taxonomy (design freeze, 2026-07-19). ``none`` is the
# explicit immobility verdict — kept in the enum so the model can assert "I
# looked and nothing changed" rather than returning an ambiguous empty list.
DELTA_CATEGORIES: tuple[str, ...] = (
    "decision_taken",
    "information_revealed",
    "position_or_access_changed",
    "attempt_got_consequence",
    "relationship_changed",
    "threat_advanced",
    "possibility_opened_or_closed",
    "none",
)


@dataclass(frozen=True)
class DeltaAudit:
    """Verdict for the most recent narrating turn.

    ``moved`` is the single bit the ladder acts on: True when the turn carried
    at least one real material delta, False when the scene stood still.
    """

    categories: tuple[str, ...] = field(default_factory=tuple)
    evidence: str = ""

    @property
    def moved(self) -> bool:
        return bool(self.categories) and self.categories != ("none",)


_AUDITED_TYPES = ("speech", "action", "narration")


def build_delta_audit_messages(game: GameState) -> list[dict]:
    """Frame the latest narrating turn for audit against its prior context.

    A "turn" is a whole ``turn_number`` block (the Narrator's narration plus
    each character's speech and action), not a single record. The window
    carries earlier turns for grounding, but the model judges only the last
    block: did the story materially move on it?
    """
    audited = [r for r in game.history if r.content_type in _AUDITED_TYPES]

    def label(speaker: str) -> str:
        return speaker_label(speaker, game.characters, game.player.controlled_character_id)

    latest_turn = audited[-1].turn_number if audited else 0
    context = [r for r in audited if r.turn_number < latest_turn][-9:]
    under_audit = [r for r in audited if r.turn_number == latest_turn]
    audit_lines = [f"  {label(r.speaker)}: {r.content[:240]}" for r in under_audit] or [
        "  (no turn yet)"
    ]

    lines = [
        f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
        "PRIOR CONTEXT (oldest to newest, for grounding only):",
        *(f"  {label(r.speaker)}: {r.content[:160]}" for r in context),
        "",
        "TURN UNDER AUDIT (judge only this block):",
        *audit_lines,
    ]
    if game.story_summary:
        lines.insert(0, f"STORY SO FAR: {game.story_summary[:400]}")
    system = (
        "You audit whether a roleplay scene MATERIALLY moved on its most recent\n"
        "turn. A scene can be full of talk, motion, and vivid description and\n"
        "still stand still. Return, as a json object, only the material deltas\n"
        "the TURN UNDER AUDIT introduces that are GENUINELY NEW relative to the\n"
        "prior context.\n"
        "THE NOVELTY GATE (apply first, to every candidate delta):\n"
        "- If the turn re-narrates, rephrases, or reacts to something ALREADY\n"
        "  established in the prior context, that is NOT a new delta. An event\n"
        "  described a second time in different words is `none`. Characters\n"
        "  confirming they are unhurt, walking to a spot, or restating an\n"
        "  existing situation is `none`.\n"
        "- Only count what changes the story's trajectory from this turn onward.\n"
        "Categories (each must pass the novelty gate AND matter to the stakes):\n"
        "- decision_taken: a character commits to a NEW course of action.\n"
        "- information_revealed: a fact new to someone present becomes known AND\n"
        "  it changes a decision, stake, or relationship. Merely SEEING or\n"
        "  DESCRIBING the scene (smoke clearing, debris, a mark on the floor) is\n"
        "  NOT information_revealed.\n"
        "- position_or_access_changed: someone gains or loses real access to a\n"
        "  place, person, or object. Walking to an assigned spot is NOT this.\n"
        "- attempt_got_consequence: an action lands a real result, success or\n"
        "  failure, that a later turn must reckon with (not merely attempted).\n"
        "- relationship_changed: trust, alliance, or standing between parties\n"
        "  shifts.\n"
        "- threat_advanced: a danger or deadline FIRST appears or moves closer.\n"
        "  Re-describing a danger already present is `none`.\n"
        "- possibility_opened_or_closed: a new option appears or an existing one\n"
        "  is foreclosed.\n"
        "- none: the turn restated, reacted, hesitated, moved into position, or\n"
        "  described without changing anything above.\n"
        "Rules:\n"
        "- Quote the concrete words that prove each delta in `evidence`, and say\n"
        "  why it is NEW; if the verdict is `none`, leave `evidence` empty.\n"
        "- Return `none` alone when nothing material and new changed; never pair\n"
        "  it with another category.\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_delta_audit_schema() -> dict:
    return {
        "name": "roteiro_delta_audit",
        "schema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(DELTA_CATEGORIES)},
                },
                "evidence": {"type": "string"},
            },
            "required": ["categories", "evidence"],
            "additionalProperties": False,
        },
    }


def _normalize_categories(raw: object) -> tuple[str, ...]:
    """Keep known categories in taxonomy order; drop `none` if paired."""
    if not isinstance(raw, list):
        return ()
    seen = {str(c) for c in raw}
    kept = tuple(c for c in DELTA_CATEGORIES if c in seen)
    material = tuple(c for c in kept if c != "none")
    return material or (("none",) if "none" in seen else ())


async def audit_delta(
    client: httpx.AsyncClient,
    game: GameState,
    config: dict,
    turn_number: int,
) -> DeltaAudit:
    """Classify the material delta of the most recent narrating turn."""
    result = await chat_completion_json(
        client,
        build_delta_audit_messages(game),
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=256,
        timeout=resolve_llm_timeout(config),
        json_schema=build_delta_audit_schema(),
        session_id=game.session_id,
        turn_number=turn_number,
        agent="watcher:delta_audit",
        **llm_request_options(config),
    )
    return DeltaAudit(
        categories=_normalize_categories(result.get("categories")),
        evidence=str(result.get("evidence", "")).strip(),
    )


# --------------------------------------------------------------------------
# Piece 2: the recovery ladder (pure code, consumes the piece-1 signal).
# --------------------------------------------------------------------------

WATCHER_DEFAULTS = {
    # OFF by default: the watcher is a fallback layer. The A/B/C battery showed
    # the task-40 clock + causal seeds can carry a scene with the watcher never
    # firing; it exists for when they do not.
    "watcher_enabled": False,
    # Escalate only after this many consecutive immobile audited turns. One
    # quiet turn is a lull, not a stall.
    "watcher_quiet_threshold": 2,
    # After any intervention, suppress the ladder this many turns so the last
    # push has room to land (matches the causal contract's validated
    # refractory_turns=3).
    "watcher_refractory_turns": 3,
}

# The recovery ladder, gentlest first (design freeze, 2026-07-19). Disruption
# is the LAST resort — every rung above it reuses material already in play.
RUNG_NONE = "none"
RUNG_EXECUTE_TRANSITION = "execute_promised_transition"
RUNG_ADJUDICATE_ATTEMPT = "adjudicate_attempt"
RUNG_ALLOW_SILENCE = "allow_silence"
RUNG_REINCORPORATE_THREAD = "reincorporate_thread"
RUNG_CAUSAL_DISRUPTION = "causal_disruption"

RECOVERY_LADDER: tuple[str, ...] = (
    RUNG_EXECUTE_TRANSITION,
    RUNG_ADJUDICATE_ATTEMPT,
    RUNG_ALLOW_SILENCE,
    RUNG_REINCORPORATE_THREAD,
    RUNG_CAUSAL_DISRUPTION,
)


@dataclass(frozen=True)
class LadderContext:
    """Everything the ladder needs, made explicit so the decision is pure.

    The runner derives these from state at integration time: ``quiet_turns``
    accumulates from piece-1's ``moved is False`` verdicts; the availability
    flags come from the roteiro (a promised ``world_event``), the audit history
    (a dangling attempt), and the causal extractor (a citable open thread).
    """

    quiet_turns: int
    turns_since_intervention: int
    promised_transition_ready: bool = False
    unadjudicated_attempt: bool = False
    open_thread: bool = False
    # Whether the one-beat silence grace was already spent in THIS stall.
    silence_spent: bool = False


@dataclass(frozen=True)
class RecoveryStep:
    rung: str
    reason: str

    @property
    def intervenes(self) -> bool:
        """Whether this rung actually acts (allow_silence and none do not)."""
        return self.rung not in (RUNG_NONE, RUNG_ALLOW_SILENCE)


def select_recovery_step(ctx: LadderContext, config: dict) -> RecoveryStep:
    """Pick the recovery rung for the current immobility, deterministically.

    Two gates precede the climb: the scene must have been immobile past the
    quiet threshold, and any prior intervention must be out of its refractory
    window. Then the gentlest applicable rung wins, in frozen order, so a
    causal disruption only fires once every reuse of existing material — a
    promised transition, a dangling attempt, a tolerated beat of silence, an
    open thread to reincorporate — has been exhausted.
    """
    if not bool(config.get("watcher_enabled", WATCHER_DEFAULTS["watcher_enabled"])):
        return RecoveryStep(RUNG_NONE, "disabled")

    threshold = int(
        config.get("watcher_quiet_threshold", WATCHER_DEFAULTS["watcher_quiet_threshold"])
    )
    if ctx.quiet_turns < threshold:
        return RecoveryStep(RUNG_NONE, f"scene moving (quiet {ctx.quiet_turns} < {threshold})")

    refractory = int(
        config.get("watcher_refractory_turns", WATCHER_DEFAULTS["watcher_refractory_turns"])
    )
    if ctx.turns_since_intervention < refractory:
        return RecoveryStep(
            RUNG_NONE, f"refractory ({ctx.turns_since_intervention} < {refractory})"
        )

    if ctx.promised_transition_ready:
        return RecoveryStep(RUNG_EXECUTE_TRANSITION, "a promised act transition is ready")
    if ctx.unadjudicated_attempt:
        return RecoveryStep(RUNG_ADJUDICATE_ATTEMPT, "a recent attempt earned no consequence")
    if not ctx.silence_spent:
        return RecoveryStep(RUNG_ALLOW_SILENCE, "tolerate one beat of silence before disrupting")
    if ctx.open_thread:
        return RecoveryStep(RUNG_REINCORPORATE_THREAD, "an open thread can be reincorporated")
    return RecoveryStep(RUNG_CAUSAL_DISRUPTION, "no gentler recovery remains")
