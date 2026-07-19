"""Task 33b experimental watcher — validated probes as a reusable module.

Both prompts are EXACTLY the variants validated by the 2026-07-19 curl
exploration (see .plan/tasks/33b-continuous-roteiro-watcher.md): the material
delta audit flagged the semantically immobile turns of a stalled real session
with empty delta lists, and the causal intervention contract produced 3/3
interventions grown from existing threads. Nothing here touches the runner:
the harness (tools/acceptance/watcher_abc.py) drives it from outside.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import GameState, TurnRecord, speaker_label

REPO = Path(__file__).resolve().parents[1]

DELTA_KINDS = [
    "decision_taken",
    "information_revealed",
    "position_or_access_changed",
    "attempt_got_consequence",
    "relationship_changed",
    "threat_advanced",
    "possibility_opened_or_closed",
    "none",
]

AUDIT_SYSTEM = (
    "You audit ONE roleplay turn for MATERIAL PROGRESS.\n"
    "A turn only counts as progress if it produced at least one verifiable delta:\n"
    "a decision was taken; previously unknown information became known; position,\n"
    "possession or access changed; an attempt received its consequence; a\n"
    "relationship or commitment changed; a threat advanced; a possibility was\n"
    "opened or closed. New scenery, restated feelings, paraphrased wishes and\n"
    "louder versions of an existing stimulus are NOT progress.\n"
    "Given the PRIOR CONTEXT and the TURN, return the deltas the TURN itself\n"
    "produced (empty list = no material progress) plus a one-line justification."
)

INTERVENTION_SYSTEM = (
    "You are the dramaturg auditing a STALLED roleplay scene (recent turns show\n"
    "reaction without material progress). Produce ONE intervention under a\n"
    "strict CAUSAL CONTRACT: it must transform something ALREADY IN PLAY, never\n"
    "open an unrelated thread.\n"
    "Steps: list the OPEN THREADS the transcript establishes (unresolved\n"
    "questions, objects, promises, dangers). Then design the intervention:\n"
    "- source_thread: which existing thread it grows from (quote its evidence);\n"
    "- target_state: what the scene should be ABOUT after it;\n"
    "- event_now: ONE concrete perceivable event happening immediately;\n"
    "- expected_delta: the verifiable change it forces;\n"
    "- closes_or_advances: which thread it closes or advances;\n"
    "- refractory_turns: how many turns the scene should digest it (2-4).\n"
    "Language of the transcript."
)


def build_delta_audit_schema() -> dict:
    return {
        "name": "delta_audit",
        "schema": {
            "type": "object",
            "properties": {
                "deltas": {"type": "array", "items": {"type": "string", "enum": DELTA_KINDS}},
                "justification": {"type": "string"},
            },
            "required": ["deltas", "justification"],
            "additionalProperties": False,
        },
    }


def build_intervention_schema() -> dict:
    intervention = {
        "type": "object",
        "properties": {
            "source_thread": {"type": "string"},
            "target_state": {"type": "string"},
            "event_now": {"type": "string"},
            "expected_delta": {"type": "string"},
            "closes_or_advances": {"type": "string"},
            "refractory_turns": {"type": "integer"},
        },
        "required": [
            "source_thread",
            "target_state",
            "event_now",
            "expected_delta",
            "closes_or_advances",
            "refractory_turns",
        ],
        "additionalProperties": False,
    }
    return {
        "name": "causal_intervention",
        "schema": {
            "type": "object",
            "properties": {
                "open_threads": {"type": "array", "items": {"type": "string"}},
                "intervention": intervention,
            },
            "required": ["open_threads", "intervention"],
            "additionalProperties": False,
        },
    }


def format_records(game: GameState, records: list[TurnRecord], clip: int = 220) -> str:
    """Viewer-neutral transcript lines (thoughts excluded by the caller)."""
    return "\n".join(
        f"T{r.turn_number} "
        f"{speaker_label(r.speaker, game.characters, game.player.controlled_character_id)}"
        f" [{r.content_type}]: {r.content[:clip]}"
        for r in records
    )


def audit_window(game: GameState, turn: int, context_records: int = 8) -> tuple[str, str]:
    """(prior context text, turn text) for auditing one committed turn."""
    visible = [r for r in game.history if r.content_type != "thought"]
    ctx = [r for r in visible if r.turn_number < turn][-context_records:]
    turn_records = [r for r in visible if r.turn_number == turn]
    return format_records(game, ctx), format_records(game, turn_records)


async def audit_turn(
    client: httpx.AsyncClient, config: dict, game: GameState, turn: int
) -> dict[str, Any]:
    """One material-delta audit call for one committed turn."""
    ctx_text, turn_text = audit_window(game, turn)
    return await chat_completion_json(
        client,
        [
            {"role": "system", "content": AUDIT_SYSTEM},
            {
                "role": "user",
                "content": f"PRIOR CONTEXT:\n{ctx_text}\n\nTURN UNDER AUDIT:\n{turn_text}",
            },
        ],
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=400,
        timeout=resolve_llm_timeout(config),
        json_schema=build_delta_audit_schema(),
        session_id=game.session_id,
        turn_number=turn,
        agent="watcher:delta",
        **llm_request_options(config),
    )


async def causal_intervention(
    client: httpx.AsyncClient, config: dict, game: GameState
) -> dict[str, Any]:
    """One causal-intervention call over the live transcript."""
    visible = [r for r in game.history if r.content_type != "thought"]
    transcript = format_records(game, visible)
    return await chat_completion_json(
        client,
        [
            {"role": "system", "content": INTERVENTION_SYSTEM},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}"},
        ],
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=1200,
        timeout=resolve_llm_timeout(config),
        json_schema=build_intervention_schema(),
        session_id=game.session_id,
        turn_number=game.history[-1].turn_number if game.history else 0,
        agent="watcher:intervention",
        **llm_request_options(config),
    )


@dataclass
class StallLadder:
    """Deterministic trigger: N consecutive no-delta turns arm an intervention.

    The LLM never decides WHEN — it only answers the two questions (was there
    a delta? what causal intervention?). Mirrors the clock doctrine.
    """

    threshold: int = 2
    refractory_turns: int = 3
    quiet: int = 0
    cooldown: int = 0
    fired: list[int] = field(default_factory=list)

    def observe(self, turn: int, deltas: list[str]) -> bool:
        """Record one audited turn; return True when an intervention is due."""
        material = [d for d in deltas if d != "none"]
        if material:
            self.quiet = 0
        else:
            self.quiet += 1
        if self.cooldown > 0:
            self.cooldown -= 1
            return False
        if self.quiet >= self.threshold:
            self.quiet = 0
            self.cooldown = self.refractory_turns
            self.fired.append(turn)
            return True
        return False
