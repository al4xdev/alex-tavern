"""Narrator Agent — orchestrates scenes, processes actions, decides who speaks."""

from __future__ import annotations

import json

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
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
        "  (the grain of the wood, the cold of steel, the weight of a door swinging),\n"
        "  write it in third person, focusing on the characters themselves. Favor vivid,\n"
        "  immersive prose over a quick summary; take as many sentences as the moment\n"
        "  deserves, don't rush the scene.\n"
        f'- "next_speaker": who should speak/act next. One of: {speakers}.\n'
        "  - Use a character id when that character should react.\n"
        '  - Use "Narrator" when you need to describe something before anyone speaks\n'
        "    (e.g., an environmental event), or when no reaction is needed yet.\n"
        '- "context_for_character": a string with filtered information for the next\n'
        "  speaker. Include only what THAT character would perceive. If next_speaker\n"
        "  is Narrator, use empty string. If an UPCOMING EVENT was provided,\n"
        "  include it here when the next speaker would witness it.\n"
        '- "scene_update": object with changes to the current scene (e.g.,\n'
        '  {"location": "Old Watchtower", "door": "open"}). "location" and\n'
        '  "time_of_day" are reserved Scene fields. Every other key is a physical\n'
        "  fact for the current location. Reuse one stable snake_case key for the\n"
        "  same fact; never create simultaneous synonyms such as weather and\n"
        "  weather_outside. Use null if nothing changed.\n"
        "  Set a key's value to null to remove that fact from the scene entirely\n"
        "  (e.g., an item that no longer exists).\n"
        '- "mood_updates": null OR an object mapping character_id to their new mood,\n'
        "  only after a meaningful emotional transition. Mood is persistent state,\n"
        "  not a pose or momentary synonym. Omit unchanged characters.\n"
        "\n"
        "RULES:\n"
        "- Resolve the immediate consequence of the final HISTORY event before adding\n"
        "  atmosphere, introducing a new thread, or moving the scene forward.\n"
        "- Never assert a character's unspoken thoughts, intentions, or emotions as\n"
        "  objective fact. Describe observable evidence and concrete perceptions only.\n"
        "- Dialogue is an attributed claim, not automatically world truth. A character's\n"
        "  action is an attempt until narration confirms its outcome. Preserve uncertainty.\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting; always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_narrator_json_schema(
    character_ids: list[str],
    forced_speaker: str | None = None,
    exclude_speaker: str | None = None,
) -> dict:
    """Builds the structural JSON schema for the Narrator's response.

    Used with ``response_format: {"type": "json_schema", ...}`` — LLM output
    is grammar-constrained and does not rely on textual prompts like
    "no markdown, no code fences".
    """
    all_speakers = [*character_ids, "Narrator"]
    if forced_speaker in all_speakers:
        speakers = [forced_speaker]
    else:
        speakers = [s for s in all_speakers if s != exclude_speaker]
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
                    "properties": {
                        "location": {"type": "string"},
                        "time_of_day": {"type": "string"},
                    },
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
    forced_speaker: str | None = None,
    narrator_hint: str = "",
) -> str:
    """Builds the user prompt with scene, characters, and history.

    No separate input block: the last action/speech (from anyone,
    including the controlled character) is already at the end of HISTORY.
    """
    lines: list[str] = []

    # Rarely changing character identity comes first so provider prefix caches can
    # retain it even when the scene, mood, or routing changes.
    lines.append("CHARACTERS PRESENT:")
    for cid in characters:
        ch = characters[cid]
        lines.append(f"  ID={cid} | NAME={ch.mind.name}")
        lines.append(f"    Personality: {ch.mind.personality}")
        lines.append(f"    Appearance: {ch.body.physical_description}")
        lines.append(f"    Outfit: {ch.body.outfit}")
    lines.append("")

    # Summary of already compacted turns (see runner.compact_session) — world
    # context, only the Narrator sees this.
    if story_summary.strip():
        lines.append("STORY SO FAR:")
        lines.append(f"  {story_summary.strip()}")
        lines.append("")

    # History — complete window, or trimmed by token budget if context_max is provided
    lines.append("HISTORY:")
    # Thoughts are private and must never become Narrator knowledge.
    hist = [rec for rec in history if rec.content_type != "thought"]
    if context_max is not None:
        hist = trim_history_by_tokens(hist, context_max, max_tokens_narrator)
    if hist:
        for rec in hist:
            label = speaker_label(rec.speaker, characters, player_controlled_id)
            lines.append(
                f"  Turn {rec.turn_number} | TYPE={rec.content_type} | "
                f"SPEAKER={label}: {rec.content}"
            )
    else:
        lines.append("  (none, first turn)")
    lines.append("")

    # Frequently changing state follows append-only history, preserving the longest
    # useful prefix while keeping the current state closest to the generation point.
    lines.append("CURRENT SCENE:")
    lines.append(f"  Location: {scene.location}")
    lines.append(f"  Time: {scene.time_of_day}")
    lines.append(f"  Physical facts: {json.dumps(scene.physical_facts, ensure_ascii=False)}")
    lines.append("")

    lines.append("CURRENT MOODS:")
    for cid, character in characters.items():
        lines.append(f"  ID={cid} | Mood: {character.mind.current_mood}")
    lines.append("")

    if narrator_hint.strip():
        lines.append("UPCOMING EVENT (incorporate this into your narration):")
        lines.append(f"  {narrator_hint.strip()}")
        lines.append("")

    if forced_speaker is not None:
        lines.append("ROUTING CONSTRAINT:")
        lines.append(f"  next_speaker is fixed as {forced_speaker}.")
        if forced_speaker == "Narrator":
            lines.append("  context_for_character must be an empty string.")
        else:
            lines.append(
                "  context_for_character must contain only what "
                f"{forced_speaker} perceives right now."
            )
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
    forced_speaker: str | None = None,
    narrator_hint: str = "",
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
                forced_speaker=forced_speaker,
                narrator_hint=narrator_hint,
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
    forced_speaker: str | None = None,
    narrator_hint: str = "",
    exclude_speaker: str | None = None,
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
        forced_speaker=forced_speaker,
        narrator_hint=narrator_hint,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_narrator,
        timeout=resolve_llm_timeout(config),
        json_schema=build_narrator_json_schema(
            list(characters),
            forced_speaker=forced_speaker,
            exclude_speaker=exclude_speaker,
        ),
        session_id=session_id,
        turn_number=turn_number,
        agent="narrator",
        **llm_request_options(config),
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
    if forced_speaker in valid_speakers:
        result["next_speaker"] = forced_speaker
        if forced_speaker == "Narrator":
            result["context_for_character"] = ""
    elif result["next_speaker"] not in valid_speakers:
        # Fallback: normalize to Narrator (the Narrator does not know "Player")
        result["next_speaker"] = "Narrator"

    # scene_update and mood_updates can be None
    result.setdefault("scene_update", None)
    result.setdefault("mood_updates", None)

    for field in ("narration", "context_for_character"):
        if isinstance(result.get(field), str):
            result[field] = normalize_generated_text(result[field])
    for field in ("scene_update", "mood_updates"):
        values = result.get(field)
        if isinstance(values, dict):
            result[field] = {
                key: normalize_generated_text(value) if isinstance(value, str) else value
                for key, value in values.items()
            }

    return result


def _build_suggest_system_prompt(
    target_id: str, character_name: str, narrator_directives: str = ""
) -> str:
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        f"Suggest 3 plausible next moves for {character_name} (ID: {target_id}), and ONLY\n"
        f"for {character_name} — do NOT suggest moves for any other character. Base each\n"
        "suggestion on their personality, mood, knowledge and the current scene/history.\n"
        "Each suggestion is a distinct, in-character option; vary tone/approach across the 3.\n"
        "\n"
        'Return an object with a "suggestions" array of exactly 3 items, each with\n'
        '"speech" (what they say, or empty string) and "action" (what they physically\n'
        "do, or empty string).\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting; always respect these):\n"
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
    character_name = characters[target_id].mind.name if target_id in characters else target_id
    messages = [
        {
            "role": "system",
            "content": _build_suggest_system_prompt(target_id, character_name, narrator_directives),
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
        timeout=resolve_llm_timeout(config),
        json_schema=build_suggest_json_schema(),
        session_id=session_id,
        turn_number=turn_number,
        agent="narrator_suggest",
        **llm_request_options(config),
    )

    suggestions: list[dict] = result.get("suggestions", [])
    return [
        {
            key: normalize_generated_text(value) if isinstance(value, str) else value
            for key, value in suggestion.items()
        }
        for suggestion in suggestions
    ]
