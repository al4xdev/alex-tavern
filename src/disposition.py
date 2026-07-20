"""Character disposition substrate (Task 43): the scalar is the code's.

Today a character is a static sheet; nothing about them drifts as the story runs.
This module governs disposition that MOVES — trust that erodes, warmth that turns,
composure that shatters and slowly returns — as code-owned scalars.

THE ONE DISCIPLINE (docs/cases/15). The scalar (0..1) belongs to the CODE:
deterministic, persisted, testable with zero model spend; it buys the measurable
half (seed at preset, drift over the arc, thresholds, before/after). The model
never sees the number — it reads only the projected qualitative BAND
(``project_band``), and it never emits a number — it emits a directional delta
that the code integrates. Break that wall (show the model the number, or ask the
code to judge tone) and the design collapses back into the failure mode the
watcher work already documented (No. 13).

THE RAZOR (anti-complexity). An axis earns its place only if a blind reader,
given only the character's speech or action, can name which pole they are on. If
it does not change observable behavior, it is decoration. Phase 2 makes that a
curl acceptance test; this module only owns the arithmetic.

Phase 1 is pure code: the data model, seeding from the preset set-point,
deterministic drift/gravity, lazy dyadic materialization, and the scalar->band
projection. No model call lives here.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import Disposition, DispositionState, GameState, speaker_label

# --- Axis registry -----------------------------------------------------------
# Trust generalizes the "faith"/credence idea (how much I act as if what I
# perceived about you is true — what lets a character be fooled). Warmth is
# affection<->hostility. Both are DYADIC (I trust her, not him). Composure is
# calm<->rattled and GLOBAL (I am rattled at everyone right now); it disciplines
# one governed slice of the free-text ``current_mood`` that already exists.
AXIS_TRUST = "trust"
AXIS_WARMTH = "warmth"
AXIS_COMPOSURE = "composure"

GLOBAL_AXES: tuple[str, ...] = (AXIS_COMPOSURE,)
DYADIC_AXES: tuple[str, ...] = (AXIS_TRUST, AXIS_WARMTH)
ALL_AXES: tuple[str, ...] = DYADIC_AXES + GLOBAL_AXES

# A personality has a set-point (baseline); a neutral character sits mid-scale.
DEFAULT_BASELINE = 0.5
# Fraction of the gap to baseline closed per calm tick (a shock knocks value off,
# gravity eases it back). 0 = value never returns; 1 = snaps back instantly.
DEFAULT_GRAVITY = 0.25

# Five bands per axis, low pole -> high pole, split at these edges on [0, 1].
# Portuguese labels: the band seeds prose tone in a PT-BR game.
_BAND_EDGES: tuple[float, ...] = (0.15, 0.35, 0.65, 0.85)

AXIS_BANDS: dict[str, tuple[str, ...]] = {
    AXIS_TRUST: ("desconfiado", "cauteloso", "neutro", "confiante", "devotado"),
    AXIS_WARMTH: ("hostil", "frio", "neutro", "caloroso", "afetuoso"),
    AXIS_COMPOSURE: ("em frangalhos", "abalado", "firme", "calmo", "imperturbável"),
}


# --- Scalars (code-owned) ----------------------------------------------------
def clamp(x: float) -> float:
    """Confine a scalar to the unit interval."""
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _grav(gravity: float | None) -> float:
    return DEFAULT_GRAVITY if gravity is None else clamp(gravity)


def project_band(axis: str, value: float) -> str:
    """Map a code-owned scalar to the qualitative band a model may read."""
    labels = AXIS_BANDS[axis]
    idx = sum(1 for edge in _BAND_EDGES if value >= edge)
    return labels[idx]


# --- Seeding & lazy materialization ------------------------------------------
def seed_character(
    state: DispositionState,
    cid: str,
    *,
    baselines: dict[str, float] | None = None,
    gravity: float | None = None,
) -> None:
    """Seed a character's GLOBAL axes from the preset set-point (idempotent).

    ``baselines`` optionally overrides per-axis set-points (a preset-declared
    temperament plugs in here); absent axes default to neutral. Dyadic axes are
    NOT seeded here — they materialize lazily on the first recorded divergence.
    """
    baselines = baselines or {}
    axes = state.per_character.setdefault(cid, {})
    for axis in GLOBAL_AXES:
        if axis in axes:
            continue
        base = clamp(float(baselines.get(axis, DEFAULT_BASELINE)))
        axes[axis] = Disposition(baseline=base, value=base, gravity=_grav(gravity))


def ensure_dyad(
    state: DispositionState,
    observer: str,
    target: str,
    *,
    baselines: dict[str, float] | None = None,
    gravity: float | None = None,
) -> dict[str, Disposition]:
    """Lazily materialize the DYADIC axes observer->target (idempotent).

    Neutral baseline unless overridden. An entry exists only after this is called
    (on the first recorded divergence), so idle pairs cost nothing.
    """
    baselines = baselines or {}
    axes = state.per_dyad.setdefault(observer, {}).setdefault(target, {})
    for axis in DYADIC_AXES:
        if axis in axes:
            continue
        base = clamp(float(baselines.get(axis, DEFAULT_BASELINE)))
        axes[axis] = Disposition(baseline=base, value=base, gravity=_grav(gravity))
    return axes


# --- Drift & integration (still pure code) -----------------------------------
def _relax(disp: Disposition) -> None:
    disp.value = clamp(disp.value + disp.gravity * (disp.baseline - disp.value))


def apply_gravity(state: DispositionState) -> None:
    """One relaxation step: every live axis eases toward its baseline set-point."""
    for axes in state.per_character.values():
        for disp in axes.values():
            _relax(disp)
    for targets in state.per_dyad.values():
        for axes in targets.values():
            for disp in axes.values():
                _relax(disp)


def nudge(disp: Disposition, amount: float) -> None:
    """Integrate a signed delta into a scalar, clamped. Phase 3 supplies ``amount``
    from a directional qualitative delta the model emits; the model never sees the
    scalar it moved."""
    disp.value = clamp(disp.value + amount)


# --- Projection for prompts (Phase 2 consumes) -------------------------------
def character_bands(state: DispositionState, cid: str) -> dict[str, str]:
    """Global-axis bands for a character, ready to inject into its agent prompt."""
    return {
        axis: project_band(axis, disp.value)
        for axis, disp in state.per_character.get(cid, {}).items()
    }


def dyad_bands(state: DispositionState, observer: str, target: str) -> dict[str, str]:
    """Dyadic-axis bands for how ``observer`` currently stands toward ``target``.

    Empty when the pair has never diverged (lazy: absent means neutral-by-default).
    """
    axes = state.per_dyad.get(observer, {}).get(target, {})
    return {axis: project_band(axis, disp.value) for axis, disp in axes.items()}


# ============================================================================
# Phase 3: the feedback loop. The model emits a directional QUALITATIVE delta;
# the code integrates it into the scalar. The model never sees the number.
#
# Scope (owner decision 2026-07-20): trust + warmth only. Composure is PARKED —
# the Phase 2 curl gate showed it does not separate at the single-utterance level
# (it reads as a scene-level/prosodic stance), so nothing appraises it yet.
# ============================================================================

# Only the dyadic axes are appraised (composure parked).
APPRAISAL_AXES: tuple[str, ...] = DYADIC_AXES

# A qualitative delta maps to a bounded scalar nudge. Kept small so a single turn
# nudges rather than snaps: it takes a couple of strong turns to flip a band, and
# gravity (calm turns) can undo a one-off. Tunable in the Phase 3 curl battery.
INTENSITY_MAGNITUDE: dict[str, float] = {"slight": 0.10, "strong": 0.22}
DISPOSITION_FEEDBACK_DEFAULT = False  # OFF by default (extra call/turn), like the watcher


@dataclass(frozen=True)
class RelationshipDelta:
    """One directional shift the appraisal auditor found on the latest turn.

    ``observer`` now stands differently toward ``target`` on ``axis`` (trust or
    warmth), in ``direction`` (up/down) with ``intensity`` (slight/strong). The
    scalar move is code-owned (``signed_amount``); the model only names the shift.
    """

    observer: str
    target: str
    axis: str
    direction: str
    intensity: str
    evidence: str = ""

    @property
    def valid(self) -> bool:
        return (
            self.observer != self.target
            and self.axis in APPRAISAL_AXES
            and self.direction in ("up", "down")
            and self.intensity in INTENSITY_MAGNITUDE
        )

    @property
    def signed_amount(self) -> float:
        magnitude = INTENSITY_MAGNITUDE.get(self.intensity, 0.0)
        return magnitude if self.direction == "up" else -magnitude


_APPRAISED_TYPES = {"speech", "action", "narration"}


def build_appraisal_messages(game: GameState) -> list[dict]:
    """Frame the latest turn for a blind, Director-side relationship appraisal.

    Like the watcher's delta auditor, it judges only the latest ``turn_number``
    block against recent context, and it never sees the roteiro or any scalar. It
    reports, per affected ordered pair, how that character's trust or warmth toward
    another MATERIALLY moved this turn. Most turns move nothing.
    """
    audited = [r for r in game.history if r.content_type in _APPRAISED_TYPES]

    def label(speaker: str) -> str:
        return speaker_label(speaker, game.characters, game.player.controlled_character_id)

    latest_turn = audited[-1].turn_number if audited else 0
    context = [r for r in audited if r.turn_number < latest_turn][-6:]
    under = [r for r in audited if r.turn_number == latest_turn]
    under_lines = [f"  {label(r.speaker)}: {r.content[:240]}" for r in under] or ["  (no turn yet)"]

    roster = ", ".join(
        f"{cid}={game.characters[cid].mind.name}"
        for cid in game.scene.present_characters
        if cid in game.characters
    )
    lines = [
        f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
        f"ROSTER (id=name; use the ids in your answer): {roster}",
        "PRIOR CONTEXT (oldest to newest, for grounding only):",
        *(f"  {label(r.speaker)}: {r.content[:160]}" for r in context),
        "",
        "TURN UNDER APPRAISAL (judge only this block):",
        *under_lines,
    ]
    system = (
        "You audit whether anyone's FEELING toward another person shifted on the\n"
        "most recent turn of a roleplay scene. Return, as a json object, a list of\n"
        "directional shifts — one per ordered pair (observer -> target) whose\n"
        "trust or warmth MATERIALLY moved on the TURN UNDER APPRAISAL.\n"
        "Two axes only:\n"
        "- trust: how much the observer relies on / believes the target (moves when\n"
        "  the target keeps or breaks a word, helps, betrays, deceives, protects).\n"
        "- warmth: how warmly the observer feels toward the target (moves when the\n"
        "  target is kind, generous, cruel, insulting, hostile).\n"
        "For each shift give: observer (id), target (id), axis (trust|warmth),\n"
        "direction (up|down), intensity (slight|strong), and evidence (the concrete\n"
        "words that prove it).\n"
        "ATTRIBUTION (get the direction of the pair right):\n"
        "- When one character ACTS toward another, the shift is in the RECIPIENT's\n"
        "  feeling toward the ACTOR. The one betrayed, helped, insulted, or\n"
        "  protected is the OBSERVER whose trust/warmth moves; the actor is the\n"
        "  TARGET. E.g. if B betrays A, it is A->B trust that drops (A no longer\n"
        "  trusts B), not B->A.\n"
        "DISCIPLINE:\n"
        "- Most turns shift nothing: return an empty list. A plain question, a\n"
        "  greeting, moving about, or re-describing the scene shifts NOTHING.\n"
        "- Only a genuine act toward someone counts, and only for who would feel it.\n"
        "- Use ONLY roster ids for observer/target; never invent a pair not present.\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_appraisal_schema() -> dict:
    return {
        "name": "relationship_appraisal",
        "schema": {
            "type": "object",
            "properties": {
                "shifts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "observer": {"type": "string"},
                            "target": {"type": "string"},
                            "axis": {"type": "string", "enum": list(APPRAISAL_AXES)},
                            "direction": {"type": "string", "enum": ["up", "down"]},
                            "intensity": {"type": "string", "enum": ["slight", "strong"]},
                            "evidence": {"type": "string"},
                        },
                        "required": [
                            "observer",
                            "target",
                            "axis",
                            "direction",
                            "intensity",
                            "evidence",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["shifts"],
            "additionalProperties": False,
        },
    }


def parse_relationship_deltas(raw: object, present: set[str]) -> list[RelationshipDelta]:
    """Turn the auditor's JSON into validated deltas scoped to present characters."""
    if not isinstance(raw, list):
        return []
    deltas: list[RelationshipDelta] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        delta = RelationshipDelta(
            observer=str(item.get("observer", "")),
            target=str(item.get("target", "")),
            axis=str(item.get("axis", "")),
            direction=str(item.get("direction", "")),
            intensity=str(item.get("intensity", "")),
            evidence=str(item.get("evidence", "")).strip(),
        )
        if delta.valid and delta.observer in present and delta.target in present:
            deltas.append(delta)
    return deltas


async def appraise_relationships(
    client: httpx.AsyncClient,
    game: GameState,
    config: dict,
    turn_number: int,
) -> list[RelationshipDelta]:
    """Blind, Director-side appraisal of relationship shifts on the latest turn."""
    result = await chat_completion_json(
        client,
        build_appraisal_messages(game),
        model=config.get("model", ""),
        language=config.get("language", ""),
        # OUTPUT cap only (input is bounded by context_max, not this). The JSON is
        # small — most turns emit 0-2 shifts — but a crowded turn with several
        # evidence quotes could run long; a truncated JSON forces a wasted retry,
        # and we bill only for tokens actually generated, so the headroom is free.
        max_tokens=1024,
        timeout=resolve_llm_timeout(config),
        json_schema=build_appraisal_schema(),
        session_id=game.session_id,
        turn_number=turn_number,
        agent="disposition:appraisal",
        **llm_request_options(config),
    )
    present = {cid for cid in game.scene.present_characters if cid in game.characters}
    return parse_relationship_deltas(result.get("shifts"), present)


def integrate_appraisal(state: DispositionState, deltas: list[RelationshipDelta]) -> None:
    """Fold directional deltas into the scalar substrate (pure code).

    Each shift lazily materializes its dyad and nudges the axis by the mapped
    magnitude, clamped. This is the ONLY place the model's qualitative verdict
    becomes a number.
    """
    for delta in deltas:
        if not delta.valid:
            continue
        axes = ensure_dyad(state, delta.observer, delta.target)
        nudge(axes[delta.axis], delta.signed_amount)
