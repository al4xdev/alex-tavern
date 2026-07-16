"""Summarizer Agent — condenses old turns into story_summary/character_notes.

Runs "outside" the normal turn flow, triggered manually by
compaction (see ``runner.compact_session``). It is blind like the Narrator: it never
knows a human exists, only sees character names (via ``speaker_label``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.models import Character, TurnRecord, record_visible_to, speaker_label


def _build_system_prompt(narrator_directives: str = "") -> str:
    prompt = (
        "You are a Historian distilling the story so far, so it keeps fitting a\n"
        "smaller model's limited context window. You receive only public, observable\n"
        "events. Fold anything that still matters into the running world summary.\n"
        "\n"
        "FIELDS:\n"
        '- "story_summary": the FULL rewritten world summary; merge the current\n'
        "  summary with anything new from these events that matters going forward:\n"
        "  key facts, open promises or threats, relationships that changed, items\n"
        "  or people that appeared or disappeared. Prioritize not losing\n"
        "  information over brevity, but stay dense, not verbose.\n"
        "RULES:\n"
        "- These events are being discarded after this. If something matters\n"
        "  later in the public world, it must survive into story_summary.\n"
        "- TYPE=speech is an attributed claim, not automatically a canonical world fact.\n"
        "- TYPE=action is an attempt until a later TYPE=narration confirms its outcome.\n"
        "- Preserve uncertainty, unknown identities, unresolved threads, and attribution.\n"
        "  Never turn an unsupported claim or inference into an unqualified fact.\n"
        "- Never include private thoughts or inferred private mental state.\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting; always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_summarizer_json_schema(character_ids: list[str] | None = None) -> dict:
    """Build the public world-summary schema.

    ``character_ids`` remains accepted for source compatibility; private notes
    now use isolated calls and are never part of the public response.
    """
    del character_ids
    return {
        "name": "summarizer_output",
        "schema": {
            "type": "object",
            "properties": {
                "story_summary": {"type": "string"},
            },
            "required": ["story_summary"],
            "additionalProperties": False,
        },
    }


def build_private_memory_json_schema() -> dict:
    """Build the schema for one character's isolated compacted memory."""
    return {
        "name": "private_character_memory",
        "schema": {
            "type": "object",
            "properties": {"character_note": {"type": "string"}},
            "required": ["character_note"],
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

    # Kept in the signature for compatibility, but private notes must never
    # enter a prompt that can write the public story summary.
    del character_notes

    lines.append("EVENTS TO SUMMARIZE (oldest to newest, being discarded after this):")
    for rec in evicted_turns:
        if rec.content_type == "thought":
            continue
        label = speaker_label(rec.speaker, characters, controlled_id)
        lines.append(
            f"  Turn {rec.turn_number} | TYPE={rec.content_type} | SPEAKER={label}: {rec.content}"
        )
    lines.append("")

    return "\n".join(lines)


def _private_owner(record: TurnRecord, controlled_id: str) -> str:
    return controlled_id if record.speaker == "Player" else record.speaker


def relevant_character_ids(
    characters: dict[str, Character],
    controlled_id: str,
    evicted_turns: list[TurnRecord],
) -> list[str]:
    """Return deterministic private-memory work units for one compaction."""
    return sorted(
        character_id
        for character_id, character in characters.items()
        if any(
            _private_owner(record, controlled_id) == character_id
            or character.mind.name.casefold() in record.content.casefold()
            for record in evicted_turns
        )
    )


def build_private_memory_messages(
    character_id: str,
    character: Character,
    controlled_id: str,
    current_note: str,
    evicted_turns: list[TurnRecord],
    characters: dict[str, Character],
    narrator_directives: str = "",
) -> list[dict]:
    """Build a prompt containing public events plus only this character's thoughts."""
    rules = (
        f"You compact private memory for {character.mind.name} (ID={character_id}).\n"
        "Return the full rewritten private note for this character. Preserve public\n"
        "events they experienced and their own private thoughts. Never infer another\n"
        "character's thoughts, and never write a world summary.\n"
        "TYPE=speech is an attributed claim. TYPE=action is an attempt until confirmed\n"
        "by TYPE=narration. TYPE=thought is private and belongs only to this character.\n"
    )
    # World directives are narrator-side authority and may define secrets as
    # world truth (measured: the campaign bible carried the whispered
    # instrument into every private-historian prompt). A private note compresses
    # ONE character's lived experience; it never receives world directives.
    del narrator_directives
    lines = [f"CURRENT PRIVATE NOTE:\n  {current_note or '(none yet)'}", "", "EVENTS:"]
    for record in evicted_turns:
        if (
            record.content_type == "thought"
            and _private_owner(record, controlled_id) != character_id
        ):
            continue
        # Private memory honors the perception boundary (Task 35; the 29.3
        # comparison traced a five-stage confidentiality cascade to exactly
        # this missing filter):
        # - narration is reader-facing omniscient prose a character never
        #   perceives live, and it can retell whispers (measured at T21 of the
        #   post-29.2 run) — it never enters a private note;
        # - whispered/zone-scoped records outside this character's perception
        #   stay out; the record's own speaker keeps theirs ("Player" records
        #   belong to the controlled character).
        if record.content_type == "narration":
            continue
        if (
            record.content_type in ("speech", "action")
            and not record_visible_to(record, character_id)
            and _private_owner(record, controlled_id) != character_id
        ):
            continue
        label = speaker_label(record.speaker, characters, controlled_id)
        lines.append(
            f"  Turn {record.turn_number} | TYPE={record.content_type} | "
            f"SPEAKER={label}: {record.content}"
        )
    return [
        {"role": "system", "content": rules},
        {"role": "user", "content": "\n".join(lines)},
    ]


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
    on_model_completed: Callable[[str], None] | None = None,
) -> tuple[str, dict[str, str]]:
    """Compact public history and isolated per-character private memories."""
    max_tokens = config.get("summarizer_max_tokens", 1024)
    messages = build_summarizer_messages(
        characters=characters,
        controlled_id=controlled_id,
        story_summary=story_summary,
        character_notes=character_notes,
        evicted_turns=evicted_turns,
        narrator_directives=narrator_directives,
    )

    common_options = llm_request_options(config)
    relevant_ids = relevant_character_ids(characters, controlled_id, evicted_turns)

    async def compact_world() -> tuple[str, str, str]:
        agent = "summarizer:world"
        result = await chat_completion_json(
            client,
            messages,
            model=config.get("model", ""),
            language=config.get("language", ""),
            max_tokens=max_tokens,
            timeout=resolve_llm_timeout(config),
            json_schema=build_summarizer_json_schema(),
            session_id=session_id,
            turn_number=turn_number,
            agent=agent,
            **common_options,
        )
        summary = normalize_generated_text(str(result.get("story_summary", story_summary)))
        return "world", summary, agent

    async def compact_private(character_id: str) -> tuple[str, str, str]:
        character = characters[character_id]
        agent = f"summarizer:{character.mind.name}"
        private_result = await chat_completion_json(
            client,
            build_private_memory_messages(
                character_id,
                character,
                controlled_id,
                character_notes.get(character_id, ""),
                evicted_turns,
                characters,
                narrator_directives,
            ),
            model=config.get("model", ""),
            language=config.get("language", ""),
            max_tokens=max_tokens,
            timeout=resolve_llm_timeout(config),
            json_schema=build_private_memory_json_schema(),
            session_id=session_id,
            turn_number=turn_number,
            agent=agent,
            **common_options,
        )
        note = normalize_generated_text(str(private_result.get("character_note", "")))
        return f"private:{character_id}", note, agent

    new_summary = story_summary
    private_results: list[tuple[str, str]] = []
    tasks = [
        asyncio.create_task(compact_world()),
        *(asyncio.create_task(compact_private(cid)) for cid in relevant_ids),
    ]
    try:
        for completed in asyncio.as_completed(tasks):
            kind, value, agent = await completed
            if kind == "world":
                new_summary = value
            else:
                private_results.append((kind.removeprefix("private:"), value))
            if on_model_completed is not None:
                on_model_completed(agent)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    changed_notes = {character_id: note for character_id, note in sorted(private_results) if note}
    return new_summary, changed_notes
