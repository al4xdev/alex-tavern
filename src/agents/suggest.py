"""Move suggestions: three drafts written from inside one character's head.

This is deliberately NOT the Narrator. The feature predates the split into
Director / Prose / Character and was implemented as an omniscient Narrator call
reusing `_build_user_prompt`, which handed it every character sheet, every
private thought and the whole roteiro — 42k to 65k characters per call to
produce three short lines, and the model kept proposing the same tactic because
it was reasoning about the *world* instead of about one person's options.

The boundary here is the one the Character agent already trusts: what this
character perceives, via `_format_history_for_character` and `record_visible_to`.
Nothing is persisted and nothing is executed — a suggestion is an editable
draft, and the decision stays with whoever asked for it.
"""

from __future__ import annotations

import httpx

from src.agents.character import _format_history_for_character
from src.llm.client import call_agent, normalize_generated_text
from src.models import (
    Character,
    CharacterPerspective,
    Scene,
    TurnRecord,
)

# Three short speech/action pairs never need the Director's budget. Fixed rather
# than derived from config so one long-context provider cannot silently turn a
# helper into the most expensive call of the turn.
SUGGESTION_MAX_TOKENS = 1024
SUGGESTION_HISTORY_TOKENS = 1024

_SYSTEM = """\
You draft three possible next moves for ONE character in a roleplay scene, from
inside that character's head. You are not narrating and not deciding: each move
is an editable draft the character could choose right now.

Rules:
- Use ONLY what this character knows, perceives and can physically do from where
  they are. Never use information they were not told and never invent a fact
  about the world.
- The three moves must be MATERIALLY different — a different intention, target
  or register each time. Three phrasings of the same tactic is a failed answer.
- Cover different registers across the three: for example one that speaks, one
  that acts physically, one that does neither loudly (observe, withdraw, wait).
- The three moves must also engage three DIFFERENT targets: one directed at a
  specific person, one at the physical scene or an object, and one at nobody
  (the character alone: withdrawing, watching, thinking it over). Never open
  all three by addressing the same person.
- Keep each field short and concrete: one sentence, no stage directions, no
  narration of anyone else's reaction.
- "speech" is what the character says aloud, or an empty string. "action" is
  what they physically do, or an empty string. At least one of the two must be
  non-empty in every move.
"""


def build_suggestion_schema() -> dict:
    """Exactly three moves, each a speech/action pair."""
    return {
        "name": "character_move_suggestions",
        "schema": {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "speech": {"type": "string"},
                            "action": {"type": "string"},
                        },
                        "required": ["speech", "action"],
                        "additionalProperties": False,
                    },
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            "required": ["suggestions"],
            "additionalProperties": False,
        },
    }


def build_suggestion_messages(
    scene: Scene,
    characters: dict[str, Character],
    target_id: str,
    history: list[TurnRecord],
    narrator_directives: str = "",
    viewer_perspective: CharacterPerspective | None = None,
) -> list[dict[str, str]]:
    """The whole context: this character's own sheet, their scene, their history.

    Every other character's mind, notes and private thoughts are absent by
    construction — they are never read here, so no instruction has to protect
    them.
    """
    character = characters[target_id]
    lines = [
        f"YOU ARE: {character.mind.name}",
        f"PERSONALITY: {character.mind.personality}",
        f"CURRENT MOOD: {character.mind.current_mood}",
    ]
    if character.mind.knowledge:
        lines.append("WHAT YOU KNOW:")
        lines.extend(f"  - {fact}" for fact in character.mind.knowledge)
    lines.append(f"YOU ARE WEARING: {character.body.outfit}")
    lines.append("")
    lines.append(f"WHERE YOU ARE: {scene.location} | {scene.time_of_day}")
    if scene.physical_facts:
        lines.append("WHAT YOU CAN SEE AROUND YOU:")
        lines.extend(f"  - {key}: {value}" for key, value in scene.physical_facts.items())
    lines.append("")
    lines.append("WHAT YOU HAVE PERCEIVED (oldest to newest):")
    lines.append(
        _format_history_for_character(
            history,
            characters,
            target_id,
            target_id,
            context_max=None,
            max_tokens_character=SUGGESTION_HISTORY_TOKENS,
            viewer_perspective=viewer_perspective,
        )
    )
    if narrator_directives.strip():
        lines.append("")
        lines.append("WORLD RULES (tone and setting you live under):")
        lines.append(narrator_directives.strip())
    lines.append("")
    lines.append("Give three materially different moves you could make right now.")

    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": "\n".join(lines)},
    ]


async def suggest_moves(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    target_id: str,
    history: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
    viewer_perspective: CharacterPerspective | None = None,
) -> list[dict[str, str]]:
    """Three editable drafts for ``target_id``. Persists nothing, executes nothing."""
    result = await call_agent(
        client,
        config,
        build_suggestion_messages(
            scene, characters, target_id, history, narrator_directives, viewer_perspective
        ),
        agent="suggest_moves",
        json_schema=build_suggestion_schema(),
        max_tokens=SUGGESTION_MAX_TOKENS,
        session_id=session_id,
        turn_number=turn_number,
    )
    return [
        {
            "speech": normalize_generated_text(item.get("speech", "")).strip(),
            "action": normalize_generated_text(item.get("action", "")).strip(),
        }
        for item in result.get("suggestions", [])
    ]
