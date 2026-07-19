"""Summarizer Agent — condenses old turns into the world story_summary.

Per-character private memory is the perspective ledger's job (Task 39): the
old per-character note fan-out is gone.

Runs "outside" the normal turn flow, triggered manually by
compaction (see ``runner.compact_session``). It is blind like the Narrator: it never
knows a human exists, only sees character names (via ``speaker_label``).
"""

from __future__ import annotations

from collections.abc import Callable

import httpx

from src.config import llm_request_options
from src.llm.client import chat_completion_json, normalize_generated_text, resolve_llm_timeout
from src.models import Character, TurnRecord, speaker_label


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


def build_summarizer_json_schema() -> dict:
    """Build the public world-summary schema."""
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



def _build_user_prompt(
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    evicted_turns: list[TurnRecord],
) -> str:
    lines: list[str] = []

    lines.append("CURRENT STORY SUMMARY:")
    lines.append(f"  {story_summary or '(none yet)'}")
    lines.append("")

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



def build_summarizer_messages(
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
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
                evicted_turns=evicted_turns,
            ),
        },
    ]


async def summarize(
    client: httpx.AsyncClient,
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    evicted_turns: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
    session_id: str = "",
    turn_number: int = 0,
    on_model_completed: Callable[[str], None] | None = None,
) -> str:
    """Compact evicted public history into the world story summary.

    One model unit. Per-character private memory lives in the perspective
    ledger (continuous capture + semantic revision); compaction no longer
    fans out per-character calls.
    """
    max_tokens = config.get("summarizer_max_tokens", 1024)
    messages = build_summarizer_messages(
        characters=characters,
        controlled_id=controlled_id,
        story_summary=story_summary,
        evicted_turns=evicted_turns,
        narrator_directives=narrator_directives,
    )
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
        **llm_request_options(config),
    )
    new_summary = normalize_generated_text(str(result.get("story_summary", story_summary)))
    if on_model_completed is not None:
        on_model_completed(agent)
    return new_summary
