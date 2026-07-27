"""Drive layer, piece 1 (Task 33): the autonomous event scheduler.

CODE decides WHEN the story receives a "picada de aleatoriedade"; a small
structured call decides only WHAT the event is. The hazard function is
deterministic per (session, turn): each completed narrating turn without an
injected event raises the firing probability; firing resets it. The scheduler
only ever produces a WORLD event hint for the blind Narrator — it never plays
a move for the human's character (agency invariant).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import httpx

from src.llm.client import call_agent
from src.models import GameState
from src.prompting import stalled_scene_context

AUTO_EVENT_DEFAULTS = {
    "auto_event_enabled": True,
    "auto_event_base_probability": 0.05,
    "auto_event_growth_per_quiet_turn": 0.12,
    "auto_event_max_probability": 0.85,
}


@dataclass(frozen=True)
class DriveDecision:
    fired: bool
    probability: float
    quiet_turns: int
    roll: float


def evaluate_event_hazard(game: GameState, config: dict) -> DriveDecision:
    """Deterministic hazard: p = min(base + growth * quiet_turns, cap).

    The roll is seeded by (session_id, next turn number), so replaying the same
    session state always reproduces the same schedule decision.
    """
    quiet = game.turns_since_injected_event
    base = float(config.get("auto_event_base_probability", 0.05))
    growth = float(config.get("auto_event_growth_per_quiet_turn", 0.12))
    cap = float(config.get("auto_event_max_probability", 0.85))
    probability = min(base + growth * quiet, cap)
    next_turn = (game.history[-1].turn_number + 1) if game.history else 1
    roll = random.Random(f"{game.session_id}:{next_turn}").random()
    enabled = bool(config.get("auto_event_enabled", True))
    return DriveDecision(
        fired=enabled and roll < probability,
        probability=round(probability, 4),
        quiet_turns=quiet,
        roll=round(roll, 4),
    )


def build_event_seed_messages(game: GameState) -> list[dict]:
    lines = stalled_scene_context(game)
    system = (
        "You inject narrative momentum into a stalled roleplay scene.\n"
        "First identify ONE open thread ALREADY present in the recent events or\n"
        "story so far: a tension, an unanswered question, an object in play, a\n"
        "pending action, or an approaching force. Quote its concrete evidence in\n"
        "`source_thread`.\n"
        "Then propose ONE short EXTERNAL event that GROWS CAUSALLY from that\n"
        "thread and pushes the story forward. State in `expected_delta` what\n"
        "materially changes.\n"
        "Rules:\n"
        "- The event MUST be traceable to `source_thread`: it escalates, answers,\n"
        "  or complicates something already in the scene. Never introduce an\n"
        "  element disconnected from it (no figure, object, sound, or force from\n"
        "  nowhere).\n"
        "- One or two sentences, in the language of the scene.\n"
        "- The event must be external to the characters' wills: never dictate\n"
        "  any character's action, dialogue, thought, or decision.\n"
        "- Stay consistent with the location and physical facts; never contradict\n"
        "  them and never resolve an open mystery outright.\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_event_seed_schema() -> dict:
    return {
        "name": "drive_event_seed",
        "schema": {
            "type": "object",
            "properties": {
                "source_thread": {"type": "string"},
                "event": {"type": "string"},
                "expected_delta": {"type": "string"},
            },
            "required": ["source_thread", "event", "expected_delta"],
            "additionalProperties": False,
        },
    }


async def generate_event_seed(
    client: httpx.AsyncClient,
    game: GameState,
    config: dict,
    turn_number: int,
) -> str:
    result = await call_agent(
        client,
        config,
        build_event_seed_messages(game),
        agent="drive:event_seed",
        json_schema=build_event_seed_schema(),
        max_tokens=256,
        session_id=game.session_id,
        turn_number=turn_number,
    )
    return str(result.get("event", "")).strip()
