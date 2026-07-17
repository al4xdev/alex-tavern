"""Narrator Agent — orchestrates scenes, processes actions, decides who speaks."""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.confidentiality import REDACTION_MARKER, hidden_whisper_tokens, redact_tokens
from src.perception import describe_zones_for_narrator, validate_perception_events
from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.models import (
    Character,
    Scene,
    TurnRecord,
    speaker_label,
    trim_history_by_tokens,
)


MAX_SPEAKERS_PER_TURN = 3


def _build_system_prompt(character_ids: list[str], narrator_directives: str = "") -> str:
    speakers = ", ".join([*character_ids, "Narrator"])
    prompt = (
        "You are the Director of a roleplay world. You know EVERYTHING about it.\n"
        "You DECIDE what physically happens next and who reacts; a separate blind\n"
        "renderer will turn your confirmed events into prose. You write decisions,\n"
        "never narration.\n"
        "\n"
        "FIELDS:\n"
        f'- "next_speakers": ordered list (1 to 3) of who reacts next. Each entry is one of: {speakers}.\n'
        "  - List several characters, in speaking order, when the moment calls for an\n"
        "    exchange (a question and its answer, a reaction chain); each later speaker\n"
        "    will have heard the earlier ones before speaking.\n"
        "  - List a character only when they have a real, present reason to speak now.\n"
        '  - Use ["Narrator"] when you need to describe something before anyone speaks\n'
        "    (e.g., an environmental event), or when no reaction is needed yet.\n"
        '- "perception_events": the typed record of what happens THIS beat, resolving\n'
        "  the last HISTORY event (an attempted action succeeds, fails, or twists;\n"
        "  a speech lands; the environment moves). This is the ONLY substrate the\n"
        "  renderer and the characters receive, so cover everything that matters.\n"
        "  Each event:\n"
        '  {"event_kind": one of "observation" | "audible_speech" | "identity_claim" |\n'
        '  "physical_outcome" | "scene_change"; "subject_id": the acting character\'s\n'
        "  ID (or \"Narrator\" for environmental events); \"content\": ONE short sentence\n"
        "  describing the event exactly as a witness would perceive it (no inner\n"
        "  thoughts, no facts a witness could not sense); \"witness_ids\": the IDs of\n"
        "  every present character who could genuinely perceive it given the zones,\n"
        "  distance, and noise. Never include someone who could not perceive it.}\n"
        "  1 to 6 events; make the FIRST events cover what the next speakers need\n"
        "  to react to. An UPCOMING EVENT, if provided, must appear here for those\n"
        "  who witness it.\n"
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
        '- "zone_moves": null OR an object mapping character_id to the zone they\n'
        "  physically moved to THIS beat (only when the scene has zones and an\n"
        "  attempted movement succeeds). Movement takes effect next beat.\n"
        '- "zone_link_updates": null OR an object remapping a zone to the FULL list\n'
        "  of zones now audible from it, when a physical change connects or seals\n"
        "  spaces (a partition opens: each side starts hearing the other; a door\n"
        "  closes: remap back to []). Takes effect next beat.\n"
        '- "return_control": true ONLY when this beat ends on a decision, danger,\n'
        "  or direct question that the protagonist of the last input must answer\n"
        "  personally; false while the world can keep moving on its own.\n"
        "\n"
        "RULES:\n"
        "- Resolve the immediate consequence of the final HISTORY event before adding\n"
        "  atmosphere, introducing a new thread, or moving the scene forward.\n"
        "- Never assert a character's unspoken thoughts, intentions, or emotions as\n"
        "  objective fact. Describe observable evidence and concrete perceptions only.\n"
        "- Dialogue is an attributed claim, not automatically world truth. A character's\n"
        "  action is an attempt until narration confirms its outcome. Preserve uncertainty.\n"
        "- HISTORY entries marked [WHISPERED, perceived only by: ...] were perceived\n"
        "  exclusively by the listed characters. Everyone else does not know that\n"
        "  content: never let them react to it, reference it, or overhear it in your\n"
        "  narration, and never put whispered content in a perception_event whose\n"
        "  witness_ids include anyone outside the listed audience.\n"
        "- Beware of denials that reveal. When telling an outsider that they did not\n"
        "  perceive a whisper, never quote, spell out, or paraphrase the whispered\n"
        "  content itself: no names, codes, passwords, numbers, or facts from it.\n"
        '  Wrong: "You did not hear the password VIOLET-9 they whispered." Right:\n'
        '  "You noticed a hushed exchange you could not make out."\n'
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
    extra_properties: dict[str, Any] | None = None,
    extra_required: list[str] | None = None,
) -> dict:
    """Builds the structural JSON schema for the Narrator's response.

    Used with ``response_format: {"type": "json_schema", ...}`` — LLM output
    is grammar-constrained and does not rely on textual prompts like
    "no markdown, no code fences".

    ``extra_properties``/``extra_required`` let a plugin extend the schema with its
    own optional output key (the ``narrator.schema`` hook) without a provider- or
    plugin-specific branch here — the property's own JSON Schema fragment (e.g. its
    ``description``) carries whatever the model needs to understand it.
    """
    all_speakers = [*character_ids, "Narrator"]
    if forced_speaker in all_speakers:
        speakers = [forced_speaker]
    else:
        # exclude_speaker is a routing POLICY, not a schema constraint: a
        # narrowed enum makes the provider-side validator reject responses the
        # lenient normalization was designed to absorb (measured: 3 straight
        # schema failures on a stalled skip turn). The full enum guides the
        # model; normalization drops the excluded entry deterministically.
        del exclude_speaker
        speakers = all_speakers
    return {
        "name": "narrator_turn",
        "schema": {
            "type": "object",
            "properties": {
                "next_speakers": {
                    "type": "array",
                    "items": {"type": "string", "enum": speakers},
                    "minItems": 1,
                    "maxItems": MAX_SPEAKERS_PER_TURN,
                },
                "perception_events": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 6,
                    "items": {
                        "type": "object",
                        "properties": {
                            "event_kind": {
                                "type": "string",
                                "enum": [
                                    "observation",
                                    "audible_speech",
                                    "identity_claim",
                                    "physical_outcome",
                                    "scene_change",
                                ],
                            },
                            "subject_id": {"type": "string"},
                            "content": {"type": "string"},
                            "witness_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["event_kind", "subject_id", "content", "witness_ids"],
                        "additionalProperties": False,
                    },
                },
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
                "zone_moves": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": "string"},
                },
                "zone_link_updates": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": "array", "items": {"type": "string"}},
                },
                "return_control": {"type": "boolean"},
                **(extra_properties or {}),
            },
            "required": [
                "next_speakers",
                "perception_events",
                "scene_update",
                "mood_updates",
                "zone_moves",
                "zone_link_updates",
                *(extra_required or []),
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
    extra_context: list[str] | None = None,
    exclude_speaker: str | None = None,
) -> str:
    """Builds the user prompt with scene, characters, and history.

    No separate input block: the last action/speech (from anyone,
    including the controlled character) is already at the end of HISTORY.

    ``extra_context`` holds read-only lines contributed by plugins (the
    ``narrator.context`` hook) — always rendered, independent of provider.
    """
    lines: list[str] = []
    present_ids = [cid for cid in characters if cid in scene.present_characters]
    absent_ids = [cid for cid in characters if cid not in present_ids]

    # Rarely changing character identity comes first so provider prefix caches can
    # retain it even when the scene, mood, or routing changes.
    lines.append("CHARACTERS PRESENT:")
    for cid in present_ids:
        ch = characters[cid]
        lines.append(f"  ID={cid} | NAME={ch.mind.name}")
        lines.append(f"    Personality: {ch.mind.personality}")
        lines.append(f"    Appearance: {ch.body.physical_description}")
        lines.append(f"    Outfit: {ch.body.outfit}")
    lines.append("")

    # Absent characters keep only a minimal, deterministic identity — full profiles
    # (personality, appearance, knowledge) would leak detail the Narrator has no
    # scene reason to know while they are elsewhere.
    if absent_ids:
        lines.append("CHARACTERS ELSEWHERE (not in the current scene):")
        for cid in absent_ids:
            lines.append(f"  ID={cid} | NAME={characters[cid].mind.name}")
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
            audience_marker = ""
            if rec.audience is not None:
                hearers = ", ".join(
                    characters[cid].mind.name if cid in characters else cid for cid in rec.audience
                )
                audience_marker = f" [WHISPERED, perceived only by: {hearers}]"
            lines.append(
                f"  Turn {rec.turn_number} | TYPE={rec.content_type}{audience_marker} | "
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
    for zone_line in describe_zones_for_narrator(scene, characters):
        lines.append(f"  {zone_line}")
    lines.append("")

    lines.append("CURRENT MOODS:")
    for cid in present_ids:
        lines.append(f"  ID={cid} | Mood: {characters[cid].mind.current_mood}")
    lines.append("")

    if narrator_hint.strip():
        lines.append("UPCOMING EVENT (incorporate this into your narration):")
        lines.append(f"  {narrator_hint.strip()}")
        lines.append("")

    if extra_context:
        lines.append("PLUGIN CONTEXT:")
        for line in extra_context:
            lines.append(f"  {line}")
        lines.append("")

    if forced_speaker is None and exclude_speaker is not None:
        lines.append("ROUTING CONSTRAINT:")
        lines.append(
            f"  Do not include {exclude_speaker} in next_speakers this turn; "
            "they just spoke or passed."
        )
        lines.append("")
    if forced_speaker is not None:
        lines.append("ROUTING CONSTRAINT:")
        lines.append(f'  next_speakers is fixed as ["{forced_speaker}"].')
        if forced_speaker != "Narrator":
            lines.append(
                "  perception_events must include what "
                f"{forced_speaker} needs to react to right now."
            )
        lines.append("")

    return "\n".join(lines)


# Kept as the historical import site; the shared implementation lives in
# src.confidentiality so the Character output guard reuses the same primitives.
_REDACTION_MARKER = REDACTION_MARKER


def redact_whisper_leaks(
    context: str,
    history: list[TurnRecord],
    speaker_id: str,
    characters: dict[str, Character],
    scene: Scene,
) -> str:
    """Strips whispered-only content from a context handed to a whisper outsider.

    Deterministic safety net behind the system-prompt rule: the Narrator sees the
    full history (whispers included) and occasionally leaks a secret while trying
    to obey the rule ("you did not hear the password X" names X). Secrets are
    derived from history (see ``src.confidentiality``); for characters inside the
    whisper's audience nothing changes.
    """
    if not context:
        return context
    secret = hidden_whisper_tokens(history, speaker_id, characters, scene)
    return redact_tokens(context, secret)


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
    extra_context: list[str] | None = None,
    exclude_speaker: str | None = None,
) -> list[dict]:
    """Assembles the Narrator messages (system + user) — pure, without calling the LLM.

    Reused by both ``narrate`` and the offline prompt preview.
    """
    present_ids = [cid for cid in characters if cid in scene.present_characters]
    return [
        {
            "role": "system",
            "content": _build_system_prompt(present_ids, narrator_directives),
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
                extra_context=extra_context,
                exclude_speaker=exclude_speaker,
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
    extra_context: list[str] | None = None,
    extra_schema_properties: dict[str, Any] | None = None,
    extra_schema_required: list[str] | None = None,
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

    ``extra_context``/``extra_schema_properties``/``extra_schema_required`` are the
    ``narrator.context``/``narrator.schema`` hook results, collected by the caller
    across every registered plugin. Any resulting extra key in the returned dict is
    left untouched here — validating and applying it is the owning plugin's job via
    the ``narrator.result`` hook.

    Returns:
        Dict with keys: next_speakers, perception_events,
        scene_update, mood_updates, plus any plugin-contributed keys.

    Raises:
        ValueError: If the returned JSON is missing required fields.
    """
    max_tokens_narrator = config.get("max_tokens_narrator", 2048)
    present_ids = [cid for cid in characters if cid in scene.present_characters]
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
        extra_context=extra_context,
        exclude_speaker=exclude_speaker,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_narrator,
        timeout=resolve_llm_timeout(config),
        json_schema=build_narrator_json_schema(
            present_ids,
            forced_speaker=forced_speaker,
            exclude_speaker=exclude_speaker,
            extra_properties=extra_schema_properties,
            extra_required=extra_schema_required,
        ),
        session_id=session_id,
        turn_number=turn_number,
        agent="director",
        **llm_request_options(config),
    )

    # Validate required fields
    required = ["next_speakers", "perception_events"]
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(
            f"Resposta do Narrador sem campos obrigatórios: {missing}. "
            f"Recebido: {json.dumps(result, ensure_ascii=False)[:300]}"
        )

    # Normalize next_speakers — only present characters (plus Narrator) are valid;
    # an absent character can never be routed to, whether hallucinated or forced.
    # "Narrator" means "no one reacts", so nothing meaningfully speaks after it:
    # the queue is truncated there, deduplicated in order, and capped.
    valid_speakers = set(present_ids) | {"Narrator"}
    if forced_speaker in valid_speakers:
        result["next_speakers"] = [forced_speaker]
    else:
        raw_queue = result.get("next_speakers")
        queue: list[str] = []
        for entry in raw_queue if isinstance(raw_queue, list) else []:
            if entry == "Narrator":
                break
            if entry in valid_speakers and entry != exclude_speaker and entry not in queue:
                queue.append(entry)
        result["next_speakers"] = queue[:MAX_SPEAKERS_PER_TURN] or ["Narrator"]

    # scene_update and mood_updates can be None
    result.setdefault("scene_update", None)
    result.setdefault("mood_updates", None)

    result["perception_events"] = validate_perception_events(
        result.get("perception_events"), scene, characters
    )
    raw_moves = result.get("zone_moves")
    moves: dict[str, str] = {}
    if isinstance(raw_moves, dict) and scene.zones:
        for cid, zone in raw_moves.items():
            if (
                isinstance(zone, str)
                and cid in characters
                and cid in scene.present_characters
                and zone in scene.zones
            ):
                moves[cid] = zone
    result["zone_moves"] = moves
    raw_links = result.get("zone_link_updates")
    links: dict[str, list[str]] = {}
    if isinstance(raw_links, dict) and scene.zones:
        for zone, audible in raw_links.items():
            if zone in scene.zones and isinstance(audible, list):
                links[zone] = [
                    other
                    for other in dict.fromkeys(audible)
                    if isinstance(other, str) and other in scene.zones and other != zone
                ]
    result["zone_link_updates"] = links
    result["return_control"] = bool(result.get("return_control", False))
    for event in result["perception_events"]:
        event["content"] = normalize_generated_text(event["content"])


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
