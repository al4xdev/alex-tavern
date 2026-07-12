"""Character Agent — replies with private thought and/or public speech."""

from __future__ import annotations

import re
from typing import TypedDict

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.models import Character, TurnRecord, speaker_label, trim_history_by_tokens


class CharacterOutput(TypedDict):
    speech: str | None
    thought: str | None


_PHYSICAL_ACTION_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:eu\s+|i\s+)?(?:"
    r"arrum(?:o|ei)|inclin(?:o|ei)|erg(?:o|ui)|abaix(?:o|ei)|toc(?:o|uei)|"
    r"segur(?:o|ei)|agarr(?:o|ei)|pux(?:o|ei)|empurr(?:o|ei)|levant(?:o|ei)|"
    r"and(?:o|ei)|caminh(?:o|ei)|olh(?:o|ei)|encar(?:o|ei)|vir(?:o|ei)|"
    r"sorr(?:io|i)|pis[cq](?:o|uei)|tamboril(?:o|ei)|"
    r"adjust|tilt|raise|lower|touch|hold|grip|pull|push|stand|walk|look|"
    r"stare|turn|smile|blink|drum|tuck|nod|brush|sit"
    r")\b",
    re.IGNORECASE,
)


def build_character_json_schema() -> dict:
    """Return the provider-enforced shape for one Character response."""
    return {
        "name": "character_response",
        "schema": {
            "type": "object",
            "properties": {
                "speech": {"type": ["string", "null"]},
                "thought": {"type": ["string", "null"]},
            },
            "required": ["speech", "thought"],
            "additionalProperties": False,
        },
    }


def _normalize_output(result: dict) -> CharacterOutput:
    """Normalize nullable fields and reject empty or action-like thoughts."""
    speech_value = result.get("speech")
    thought_value = result.get("thought")
    speech = (
        normalize_generated_text(speech_value.strip())
        if isinstance(speech_value, str) and speech_value.strip()
        else None
    )
    thought = (
        normalize_generated_text(thought_value.strip())
        if isinstance(thought_value, str) and thought_value.strip()
        else None
    )
    if speech is None and thought is None:
        raise ValueError("Character response must contain speech, thought, or both")
    if any(text is not None and _PHYSICAL_ACTION_RE.search(text) for text in (speech, thought)):
        raise ValueError("Character response appears to describe a physical action")
    return {"speech": speech, "thought": thought}


def _build_system_prompt(character: Character) -> str:
    """Build the stable Character prefix; changing state belongs in the user suffix."""
    return (
        f"You are {character.mind.name}. Stay in character at all times.\n"
        f"Personality: {character.mind.personality}\n"
        f"Knowledge: {', '.join(character.mind.knowledge)}\n"
        "\n"
        "RULES:\n"
        "- You are a character in a roleplay scene, not the Narrator: never state\n"
        "  the environment or anyone's body/actions as flat, objective fact. You\n"
        "  may react to what you perceive in others, but only as your own\n"
        "  subjective read: what it seems like to you, not what is happening\n"
        '  ("he seems tense", never "he grips the hilt of his sword").\n'
        "- Never perform or describe a physical action, including your own body,\n"
        "  gestures, posture, facial expression, or movement. Physical action belongs\n"
        "  exclusively to the Narrator. A thought such as 'I tuck my hair behind my\n"
        "  ear' is forbidden; 'His voice sounds unusually soft to me' is valid.\n"
        "- Put audible first-person dialogue in speech. Put only your private internal\n"
        "  reaction, opinion, or feeling in thought. Do not use markdown wrappers.\n"
        "  Either field may be null, but they cannot both be null or empty.\n"
        "- Facts may come only from your Knowledge, What you remember, SCENE CONTEXT,\n"
        "  or RECENT EVENTS. If a detail is absent, omit it or clearly express doubt;\n"
        "  never invent a location, backstory, relationship, or prior event.\n"
        "- Never repeat a complete sentence from RECENT EVENTS. Silently proofread\n"
        "  grammar and remove accidental duplicated words before answering.\n"
        "- Keep responses to 1-3 sentences.\n"
        "- You may address other characters directly.\n"
    )


def _build_user_prompt(context: str, history_text: str, current_mood: str, notes: str) -> str:
    """Put append-only history before the Character's changing state and context."""
    memory = notes.strip() or "(none yet)"
    return (
        "RECENT EVENTS:\n"
        f"{history_text}\n"
        "\n"
        "CURRENT PRIVATE STATE:\n"
        f"Current mood: {current_mood}\n"
        f"What you remember: {memory}\n"
        "\n"
        "SCENE CONTEXT (what you perceive right now):\n"
        f"{context}\n"
        "\n"
        "Return your audible speech and private thought in the requested fields."
    )


def _format_history_for_character(
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    context_max: int | None = None,
    max_tokens_character: int = 1024,
) -> str:
    """Formats the history as linear text for the character.

    The character sees public dialogue and only its own private thoughts. It never
    receives narration, actions, or another character's thoughts.
    """
    hist = [
        rec
        for rec in history
        if rec.content_type == "speech"
        or (rec.content_type == "thought" and rec.speaker == character_id)
    ]
    if context_max is not None:
        hist = trim_history_by_tokens(hist, context_max, max_tokens_character)
    if not hist:
        return "(none)"
    lines: list[str] = []
    for rec in hist:
        label = speaker_label(rec.speaker, characters, controlled_id)
        kind = "PRIVATE THOUGHT" if rec.content_type == "thought" else "SPEECH"
        lines.append(f"Turn {rec.turn_number} | TYPE={kind} | SPEAKER={label}: {rec.content}")
    return "\n".join(lines)


async def act(
    client: httpx.AsyncClient,
    character: Character,
    context: str,
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    character_id: str,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
    notes: str = "",
) -> CharacterOutput:
    """Build the Character prompt and return separate speech/thought fields.

    Args:
        client: Shared httpx.AsyncClient.
        character: The character (only Mind is used in the prompt).
        context: ``context_for_character`` from the Narrator.
        history: Full session history (used to build the recent events context).
        characters: All characters in the session — only used to translate
                    ``speaker_label`` in the history (never leaks other characters'
                    `body`/personality to the prompt).
        controlled_id: ID of the human-controlled character — only used to
                       translate the internal "Player" marker to the character's name.
        character_id: Canonical ID of the Character being called.
        config: Server config (max_tokens).
        session_id: Passed to the raw LLM call log (see ``src/llm/client.py``).
        turn_number: Passed to the raw call log.
        notes: This character's note (``game.character_notes[character_id]``,
               see ``runner.compact_session``) — never another character's.

    Returns:
        Nullable speech/thought fields, with at least one populated.
    """
    max_tokens_character = config.get("max_tokens_character", 1024)
    history_text = _format_history_for_character(
        history,
        characters,
        controlled_id,
        character_id,
        context_max=config.get("context_max"),
        max_tokens_character=max_tokens_character,
    )
    messages = [
        {"role": "system", "content": _build_system_prompt(character)},
        {
            "role": "user",
            "content": _build_user_prompt(
                context,
                history_text,
                character.mind.current_mood,
                notes,
            ),
        },
    ]

    last_error: ValueError | None = None
    for attempt in range(2):
        attempt_messages = messages
        if attempt:
            attempt_messages = [dict(message) for message in messages]
            attempt_messages[-1]["content"] += (
                "\nCORRECTION: Your previous response was invalid. Remove every physical "
                "action or gesture. Return only audible dialogue and/or genuinely internal "
                "thought.\n"
            )
        result = await chat_completion_json(
            client,
            attempt_messages,
            model=config.get("model", ""),
            language=config.get("language", ""),
            max_tokens=max_tokens_character,
            timeout=resolve_llm_timeout(config),
            json_schema=build_character_json_schema(),
            retries=0,
            session_id=session_id,
            turn_number=turn_number,
            agent=f"character:{character.mind.name}",
            **llm_request_options(config),
        )
        try:
            return _normalize_output(result)
        except ValueError as exc:
            last_error = exc
    raise ValueError(f"Invalid Character response after correction: {last_error}")
