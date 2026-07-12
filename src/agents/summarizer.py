"""Summarizer Agent — condenses old turns into story_summary/character_notes.

Runs "outside" the normal turn flow, triggered manually by
compaction (see ``runner.compact_session``). It is blind like the Narrator: it never
knows a human exists, only sees character names (via ``speaker_label``).
"""

from __future__ import annotations

import httpx

from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.models import Character, TurnRecord, speaker_label


def _build_system_prompt(narrator_directives: str = "") -> str:
    prompt = (
        "You are a Historian distilling the story so far, so it keeps fitting a\n"
        "smaller model's limited context window. You read a chunk of older events\n"
        "that are about to be discarded from active memory, and fold anything that\n"
        "still matters into the running world summary and per-character notes.\n"
        "\n"
        "FIELDS:\n"
        '- "story_summary": the FULL rewritten world summary; merge the current\n'
        "  summary with anything new from these events that matters going forward:\n"
        "  key facts, open promises or threats, relationships that changed, items\n"
        "  or people that appeared or disappeared. Prioritize not losing\n"
        "  information over brevity, but stay dense, not verbose.\n"
        '- "character_notes": an object mapping character id to an updated note,\n'
        "  ONLY for characters whose note actually needs to change because of\n"
        "  these events. Omit any character whose existing note is still accurate\n"
        "  and do not repeat it.\n"
        "\n"
        "RULES:\n"
        "- These events are being discarded after this. If something matters\n"
        "  later, it must survive into story_summary or a character note.\n"
        "- TYPE=speech is an attributed claim, not automatically a canonical world fact.\n"
        "- TYPE=action is an attempt until a later TYPE=narration confirms its outcome.\n"
        "- Preserve uncertainty, unknown identities, unresolved threads, and attribution.\n"
        "  Never turn an unsupported claim or inference into an unqualified fact.\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting; always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_summarizer_json_schema(character_ids: list[str]) -> dict:
    """Builds the structural JSON schema for the Summarizer's response."""
    return {
        "name": "summarizer_output",
        "schema": {
            "type": "object",
            "properties": {
                "story_summary": {"type": "string"},
                "character_notes": {
                    "type": "object",
                    "properties": {cid: {"type": "string"} for cid in character_ids},
                    "additionalProperties": False,
                },
            },
            "required": ["story_summary", "character_notes"],
            "additionalProperties": False,
        },
    }


def _build_user_prompt(
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    character_notes: dict[str, str],
    evicted_turns: list[TurnRecord],
) -> str:
    lines: list[str] = []

    lines.append("CURRENT STORY SUMMARY:")
    lines.append(f"  {story_summary or '(none yet)'}")
    lines.append("")

    lines.append("CURRENT CHARACTER NOTES:")
    for cid, ch in characters.items():
        note = character_notes.get(cid, "(none yet)")
        lines.append(f"  ID={cid} | NAME={ch.mind.name} | NOTE={note}")
    lines.append("")

    lines.append("EVENTS TO SUMMARIZE (oldest to newest, being discarded after this):")
    for rec in evicted_turns:
        label = speaker_label(rec.speaker, characters, controlled_id)
        lines.append(
            f"  Turn {rec.turn_number} | TYPE={rec.content_type} | SPEAKER={label}: {rec.content}"
        )
    lines.append("")

    return "\n".join(lines)


def _canonical_character_notes(
    raw_notes: object, characters: dict[str, Character]
) -> dict[str, str]:
    """Keep only string notes keyed by canonical IDs from this session."""
    if not isinstance(raw_notes, dict):
        return {}
    return {
        character_id: note
        for character_id, note in raw_notes.items()
        if character_id in characters and isinstance(note, str)
    }


def build_summarizer_messages(
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    character_notes: dict[str, str],
    evicted_turns: list[TurnRecord],
    narrator_directives: str = "",
) -> list[dict]:
    """Assembles the Summarizer messages (system + user) — pure, without calling the LLM."""
    return [
        {"role": "system", "content": _build_system_prompt(narrator_directives)},
        {
            "role": "user",
            "content": _build_user_prompt(
                characters=characters,
                controlled_id=controlled_id,
                story_summary=story_summary,
                character_notes=character_notes,
                evicted_turns=evicted_turns,
            ),
        },
    ]


async def summarize(
    client: httpx.AsyncClient,
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    character_notes: dict[str, str],
    evicted_turns: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
) -> tuple[str, dict[str, str]]:
    """Calls the Summarizer, returns the updated summary and the notes that changed.

    ``character_notes`` returned contains ONLY the entries the LLM decided
    to update (characters not mentioned in the evicted events are omitted
    purposely) — the caller (``runner.compact_session``) merges this with
    the existing ``character_notes`` in ``GameState``.

    Returns:
        Tuple of ``(story_summary, changed_character_notes)``.
    """
    max_tokens = config.get("summarizer_max_tokens", 1024)
    messages = build_summarizer_messages(
        characters=characters,
        controlled_id=controlled_id,
        story_summary=story_summary,
        character_notes=character_notes,
        evicted_turns=evicted_turns,
        narrator_directives=narrator_directives,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens,
        timeout=resolve_llm_timeout(config),
        json_schema=build_summarizer_json_schema(list(characters)),
        session_id=session_id,
        turn_number=turn_number,
        agent="summarizer",
    )

    new_summary = normalize_generated_text(str(result.get("story_summary", story_summary)))
    changed_notes = {
        character_id: normalize_generated_text(note)
        for character_id, note in _canonical_character_notes(
            result.get("character_notes"), characters
        ).items()
    }
    return new_summary, changed_notes
