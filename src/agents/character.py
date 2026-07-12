"""Character Agent — acts in-character, replies with speech or thought."""

from __future__ import annotations

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion, normalize_generated_text, resolve_llm_timeout
from src.models import Character, TurnRecord, speaker_label, trim_history_by_tokens


def _build_system_prompt(character: Character, notes: str = "") -> str:
    memory_line = f"What you remember: {notes.strip()}\n" if notes.strip() else ""
    return (
        f"You are {character.mind.name}. Stay in character at all times.\n"
        f"Personality: {character.mind.personality}\n"
        f"Knowledge: {', '.join(character.mind.knowledge)}\n"
        f"Current mood: {character.mind.current_mood}\n"
        f"{memory_line}"
        "\n"
        "RULES:\n"
        "- You are a character in a roleplay scene, not the Narrator: never state\n"
        "  the environment or anyone's body/actions as flat, objective fact. You\n"
        "  may react to what you perceive in others, but only as your own\n"
        "  subjective read: what it seems like to you, not what is happening\n"
        '  ("he seems tense", never "he grips the hilt of his sword").\n'
        "- Speak in first person, as dialogue.\n"
        "- Use **text** for internal thoughts; always wrap them, no exceptions.\n"
        "  A thought is your own reaction, opinion, or feeling about yourself\n"
        "  or someone else, filtered through your own perspective.\n"
        "- Facts may come only from your Knowledge, What you remember, SCENE CONTEXT,\n"
        "  or RECENT EVENTS. If a detail is absent, omit it or clearly express doubt;\n"
        "  never invent a location, backstory, relationship, or prior event.\n"
        "- Never repeat a complete sentence from RECENT EVENTS. Silently proofread\n"
        "  grammar and remove accidental duplicated words before answering.\n"
        "- Keep responses to 1-3 sentences.\n"
        "- You may address other characters directly.\n"
    )


def _format_history_for_character(
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    context_max: int | None = None,
    max_tokens_character: int = 1024,
) -> str:
    """Formats the history as linear text for the character.

    The character only sees previous dialogue — never narration nor actions (that
    would break the role model: only the Narrator narrates/describes/acts). They react
    to the current Narrator message (``context_for_character``), trimmed by
    token budget if ``context_max`` is provided.
    """
    hist = [rec for rec in history if rec.content_type == "speech"]
    if context_max is not None:
        hist = trim_history_by_tokens(hist, context_max, max_tokens_character)
    if not hist:
        return "(none)"
    lines: list[str] = []
    for rec in hist:
        label = speaker_label(rec.speaker, characters, controlled_id)
        lines.append(f"Turn {rec.turn_number} | SPEAKER={label}: {rec.content}")
    return "\n".join(lines)


async def act(
    client: httpx.AsyncClient,
    character: Character,
    context: str,
    history: list[TurnRecord],
    characters: dict[str, Character],
    controlled_id: str,
    config: dict,
    session_id: str = "",
    turn_number: int = 0,
    notes: str = "",
) -> str:
    """Builds the Character prompt, calls the LLM, and returns speech/thought.

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
        config: Server config (max_tokens).
        session_id: Passed to the raw LLM call log (see ``src/llm/client.py``).
        turn_number: Passed to the raw call log.
        notes: This character's note (``game.character_notes[character_id]``,
               see ``runner.compact_session``) — never another character's.

    Returns:
        The speech/thought (raw string, without JSON).
    """
    max_tokens_character = config.get("max_tokens_character", 1024)
    history_text = _format_history_for_character(
        history,
        characters,
        controlled_id,
        context_max=config.get("context_max"),
        max_tokens_character=max_tokens_character,
    )
    messages = [
        {"role": "system", "content": _build_system_prompt(character, notes)},
        {
            "role": "user",
            "content": (
                "SCENE CONTEXT (what you perceive right now):\n"
                f"{context}\n"
                "\n"
                "RECENT EVENTS:\n"
                f"{history_text}\n"
                "\n"
                "What do you say or think?"
            ),
        },
    ]

    content = await chat_completion(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_character,
        timeout=resolve_llm_timeout(config),
        session_id=session_id,
        turn_number=turn_number,
        agent=f"character:{character.mind.name}",
        **llm_request_options(config),
    )

    return normalize_generated_text(content.strip())
