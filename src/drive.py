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

from src.config import llm_request_options
from src.llm.client import chat_completion_json, resolve_llm_timeout
from src.models import GameState, speaker_label

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
    recent = [
        record
        for record in game.history[-12:]
        if record.content_type in ("speech", "action", "narration")
    ]
    lines = [
        f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
        f"PHYSICAL FACTS: {game.scene.physical_facts}",
        "RECENT EVENTS (oldest to newest):",
        *(
            f"  {speaker_label(r.speaker, game.characters, game.player.controlled_character_id)}:"
            f" {r.content[:160]}"
            for r in recent
        ),
    ]
    if game.story_summary:
        lines.insert(0, f"STORY SO FAR: {game.story_summary[:600]}")
    system = (
        "You inject narrative momentum into a stalled roleplay scene.\n"
        "Propose ONE short unexpected but scene-consistent EXTERNAL event that\n"
        "pushes the story forward: an arrival, an interruption, a discovery, a\n"
        "sound, an object changing state, a complication.\n"
        "Rules:\n"
        "- One or two sentences, in the language of the scene.\n"
        "- The event must be external to the characters' wills: never dictate\n"
        "  any character's action, dialogue, thought, or decision.\n"
        "- Stay consistent with the location, physical facts, and recent events;\n"
        "  never contradict them and never resolve an open mystery.\n"
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
            "properties": {"event": {"type": "string"}},
            "required": ["event"],
            "additionalProperties": False,
        },
    }


async def generate_event_seed(
    client: httpx.AsyncClient,
    game: GameState,
    config: dict,
    turn_number: int,
) -> str:
    result = await chat_completion_json(
        client,
        build_event_seed_messages(game),
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=256,
        timeout=resolve_llm_timeout(config),
        json_schema=build_event_seed_schema(),
        session_id=game.session_id,
        turn_number=turn_number,
        agent="drive:event_seed",
        **llm_request_options(config),
    )
    return str(result.get("event", "")).strip()
