"""Narrator Agent — orchestrates scenes, processes actions, decides who speaks."""

from __future__ import annotations

import json

import httpx

from src.llm.client import chat_completion_json
from src.models import Character, Scene, TurnRecord, speaker_label, trim_history_by_tokens


def _build_system_prompt(character_ids: list[str], narrator_directives: str = "") -> str:
    speakers = ", ".join([*character_ids, "Narrator"])
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        "You describe scenes, process what happens, and decide who speaks next.\n"
        "\n"
        "FIELDS:\n"
        '- "narration": describe what happens in the scene based on the last event in\n'
        "  HISTORY and the current state. Ground it in the senses: when a character\n"
        "  touches, looks, or moves, name the concrete physical detail they perceive\n"
        "  (the grain of the wood, the cold of steel, the weight of a door swinging) —\n"
        "  write it as if the reader is inhabiting that character's body. Favor vivid,\n"
        "  immersive prose over a quick summary; take as many sentences as the moment\n"
        "  deserves, don't rush the scene.\n"
        f'- "next_speaker": who should speak/act next. One of: {speakers}.\n'
        "  - Use a character id when that character should react.\n"
        '  - Use "Narrator" when you need to describe something before anyone speaks\n'
        "    (e.g., an environmental event), or when no reaction is needed yet.\n"
        '- "context_for_character": a string with filtered information for the next\n'
        "  speaker. Include only what THAT character would perceive. If next_speaker\n"
        "  is Narrator, use empty string.\n"
        '- "scene_update": object with physical changes to the scene (e.g.,\n'
        '  {"door": "open", "weather": "rain"}). Use null if nothing changed.\n'
        "  Set a key's value to null to remove that fact from the scene entirely\n"
        "  (e.g., an item that no longer exists).\n"
        '- "mood_updates": null OR an object mapping character_id to their new mood,\n'
        "  only for characters whose mood actually changed this turn (e.g.\n"
        '  {"C1": "furioso"}). Omit characters whose mood is unchanged.\n'
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_narrator_json_schema(character_ids: list[str]) -> dict:
    """Builds the structural JSON schema for the Narrator's response.

    Used with ``response_format: {"type": "json_schema", ...}`` — LLM output
    is grammar-constrained and does not rely on textual prompts like
    "no markdown, no code fences".
    """
    speakers = [*character_ids, "Narrator"]
    return {
        "name": "narrator_turn",
        "schema": {
            "type": "object",
            "properties": {
                "narration": {"type": "string"},
                "next_speaker": {"type": "string", "enum": speakers},
                "context_for_character": {"type": "string"},
                "scene_update": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": ["string", "null"]},
                },
                "mood_updates": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": [
                "narration",
                "next_speaker",
                "context_for_character",
                "scene_update",
                "mood_updates",
            ],
            "additionalProperties": False,
        },
    }


def _build_user_prompt(
    scene: Scene,
    characters: dict[str, Character],
    player_controlled_id: str,
    history: list[TurnRecord],
    context_max: int | None = None,
    max_tokens_narrator: int = 2048,
    story_summary: str = "",
) -> str:
    """Builds the user prompt with scene, characters, and history.

    No separate input block: the last action/speech (from anyone,
    including the controlled character) is already at the end of HISTORY.
    """
    lines: list[str] = []

    # Summary of already compacted turns (see runner.compact_session) — world
    # context, only the Narrator sees this.
    if story_summary.strip():
        lines.append("STORY SO FAR:")
        lines.append(f"  {story_summary.strip()}")
        lines.append("")

    # Current scene
    lines.append("CURRENT SCENE:")
    lines.append(f"  Location: {scene.location}")
    lines.append(f"  Time: {scene.time_of_day}")
    lines.append(f"  Physical facts: {json.dumps(scene.physical_facts, ensure_ascii=False)}")
    lines.append("")

    # Present characters
    lines.append("CHARACTERS PRESENT:")
    for cid in characters:
        ch = characters[cid]
        lines.append(f"  {cid} — {ch.mind.name}")
        lines.append(f"    Personality: {ch.mind.personality}")
        lines.append(f"    Appearance: {ch.body.physical_description}")
        lines.append(f"    Outfit: {ch.body.outfit}")
        lines.append(f"    Mood: {ch.mind.current_mood}")
    lines.append("")

    # History — complete window, or trimmed by token budget if context_max is provided
    lines.append("HISTORY:")
    hist = history
    if context_max is not None:
        hist = trim_history_by_tokens(history, context_max, max_tokens_narrator)
    if hist:
        for rec in hist:
            label = speaker_label(rec.speaker, characters, player_controlled_id)
            lines.append(f"  Turn {rec.turn_number} — {label}: {rec.content}")
    else:
        lines.append("  (none — first turn)")
    lines.append("")

    return "\n".join(lines)


def build_narrator_messages(
    scene: Scene,
    characters: dict[str, Character],
    player_controlled_id: str,
    history: list[TurnRecord],
    narrator_directives: str = "",
    context_max: int | None = None,
    max_tokens_narrator: int = 2048,
    story_summary: str = "",
) -> list[dict]:
    """Assembles the Narrator messages (system + user) — pure, without calling the LLM.

    Reused by both ``narrate`` and the offline prompt preview.
    """
    return [
        {
            "role": "system",
            "content": _build_system_prompt(list(characters), narrator_directives),
        },
        {
            "role": "user",
            "content": _build_user_prompt(
                scene=scene,
                characters=characters,
                player_controlled_id=player_controlled_id,
                history=history,
                context_max=context_max,
                max_tokens_narrator=max_tokens_narrator,
                story_summary=story_summary,
            ),
        },
    ]


async def narrate(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    player_controlled_id: str,
    history: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
    story_summary: str = "",
) -> dict:
    """Builds the Narrator prompt, calls the LLM, and returns a validated dict.

    The Narrator is blind: they do not know a human exists. They react to the last
    entry of HISTORY, whoever it belongs to. ``player_controlled_id`` is only used
    to translate the internal ``"Player"`` marker to the character's name when
    assembling the history — it never appears as text in the prompt.

    ``story_summary`` is the summary of already compacted turns (see
    ``runner.compact_session``) — world context, only the Narrator receives it.

    ``session_id``/``turn_number`` only exist for the raw LLM call log
    (see ``src/llm/client.py``) — they do not affect the prompt.

    Returns:
        Dict with keys: narration, next_speaker, context_for_character,
        scene_update, mood_updates.

    Raises:
        ValueError: If the returned JSON is missing required fields.
    """
    max_tokens_narrator = config.get("max_tokens_narrator", 2048)
    messages = build_narrator_messages(
        scene=scene,
        characters=characters,
        player_controlled_id=player_controlled_id,
        history=history,
        narrator_directives=narrator_directives,
        context_max=config.get("context_max"),
        max_tokens_narrator=max_tokens_narrator,
        story_summary=story_summary,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_narrator,
        json_schema=build_narrator_json_schema(list(characters)),
        session_id=session_id,
        turn_number=turn_number,
        agent="narrator",
    )

    # Validate required fields
    required = ["narration", "next_speaker", "context_for_character"]
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(
            f"Resposta do Narrador sem campos obrigatórios: {missing}. "
            f"Recebido: {json.dumps(result, ensure_ascii=False)[:300]}"
        )

    # Validate next_speaker — valid speakers derived dynamically from IDs
    valid_speakers = set(characters) | {"Narrator"}
    if result["next_speaker"] not in valid_speakers:
        # Fallback: normalize to Narrator (the Narrator does not know "Player")
        result["next_speaker"] = "Narrator"

    # scene_update and mood_updates can be None
    result.setdefault("scene_update", None)
    result.setdefault("mood_updates", None)

    return result


def _build_suggest_system_prompt(target_id: str, narrator_directives: str = "") -> str:
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        f"Suggest 3 plausible next moves for {target_id}, given their personality, mood,\n"
        "knowledge and the current scene/history. Each suggestion is a distinct, in-\n"
        "character option — vary tone/approach across the 3.\n"
        "\n"
        'Return an object with a "suggestions" array of exactly 3 items, each with\n'
        '"speech" (what they say, or empty string) and "action" (what they physically\n'
        "do, or empty string).\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_suggest_json_schema() -> dict:
    """JSON schema of the suggestion response (manual trigger, Task 6)."""
    suggestion_schema = {
        "type": "object",
        "properties": {
            "speech": {"type": "string"},
            "action": {"type": "string"},
        },
        "required": ["speech", "action"],
        "additionalProperties": False,
    }
    return {
        "name": "narrator_suggestions",
        "schema": {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": suggestion_schema,
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            "required": ["suggestions"],
            "additionalProperties": False,
        },
    }


async def suggest(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    target_id: str,
    history: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
) -> list[dict]:
    """Asks the (blind) Narrator for a list of possible moves for ``target_id``.

    Used by the "suggest to me" trigger: the Narrator does not know ``target_id``
    is the human-controlled character — the question is generic ("suggest
    moves for this character"), exactly as it would be for any other character. It
    does not persist anything; the caller decides what to do with the suggestions.

    Returns:
        List of ``{"speech", "action"}``.
    """
    max_tokens_narrator = config.get("max_tokens_narrator", 2048)
    messages = [
        {
            "role": "system",
            "content": _build_suggest_system_prompt(target_id, narrator_directives),
        },
        {
            "role": "user",
            "content": _build_user_prompt(
                scene=scene,
                characters=characters,
                player_controlled_id=target_id,
                history=history,
                context_max=config.get("context_max"),
                max_tokens_narrator=max_tokens_narrator,
            ),
        },
    ]

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_narrator,
        json_schema=build_suggest_json_schema(),
        session_id=session_id,
        turn_number=turn_number,
        agent="narrator_suggest",
    )

    suggestions: list[dict] = result.get("suggestions", [])
    return suggestions
