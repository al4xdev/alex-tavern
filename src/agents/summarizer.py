"""Agente Resumidor — condensa turnos antigos em story_summary/character_notes.

Roda "de fora" do fluxo de turno normal, disparado manualmente pela
compactação (ver ``runner.compact_session``). É cego igual o Narrador: nunca
sabe que existe um humano, só vê nomes de personagem (via ``speaker_label``).
"""

from __future__ import annotations

import httpx

from src.llm.client import chat_completion_json
from src.models import Character, TurnRecord, speaker_label


def _build_system_prompt(narrator_directives: str = "") -> str:
    prompt = (
        "You are a Historian distilling the story so far, so it keeps fitting a\n"
        "smaller model's limited context window. You read a chunk of older events\n"
        "that are about to be discarded from active memory, and fold anything that\n"
        "still matters into the running world summary and per-character notes.\n"
        "\n"
        "FIELDS:\n"
        '- "story_summary": the FULL rewritten world summary — merge the current\n'
        "  summary with anything new from these events that matters going forward:\n"
        "  key facts, open promises or threats, relationships that changed, items\n"
        "  or people that appeared or disappeared. Prioritize not losing\n"
        "  information over brevity, but stay dense, not verbose.\n"
        '- "character_notes": an object mapping character id to an updated note,\n'
        "  ONLY for characters whose note actually needs to change because of\n"
        "  these events. Omit any character whose existing note is still accurate\n"
        "  — do not repeat it.\n"
        "\n"
        "RULES:\n"
        "- These events are being discarded after this — if something matters\n"
        "  later, it must survive into story_summary or a character note.\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_summarizer_json_schema() -> dict:
    """Monta o JSON schema estrutural da resposta do Resumidor."""
    return {
        "name": "summarizer_output",
        "schema": {
            "type": "object",
            "properties": {
                "story_summary": {"type": "string"},
                "character_notes": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
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
        lines.append(f"  {cid} — {ch.mind.name}: {note}")
    lines.append("")

    lines.append("EVENTS TO SUMMARIZE (oldest to newest, being discarded after this):")
    for rec in evicted_turns:
        label = speaker_label(rec.speaker, characters, controlled_id)
        lines.append(f"  Turn {rec.turn_number} — {label}: {rec.content}")
    lines.append("")

    return "\n".join(lines)


def build_summarizer_messages(
    characters: dict[str, Character],
    controlled_id: str,
    story_summary: str,
    character_notes: dict[str, str],
    evicted_turns: list[TurnRecord],
    narrator_directives: str = "",
) -> list[dict]:
    """Monta os messages (system + user) do Resumidor — puro, sem chamar o LLM."""
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
    """Chama o Resumidor, devolve o resumo atualizado e as notas que mudaram.

    ``character_notes`` retornado contém SÓ as entradas que o LLM decidiu
    atualizar (personagens não mencionados nos eventos evictados são omitidos
    de propósito) — quem chama (``runner.compact_session``) faz o merge com
    o ``character_notes`` existente no ``GameState``.

    Returns:
        Tupla ``(story_summary, changed_character_notes)``.
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
        json_schema=build_summarizer_json_schema(),
        session_id=session_id,
        turn_number=turn_number,
        agent="summarizer",
    )

    new_summary = str(result.get("story_summary", story_summary))
    changed_notes = dict(result.get("character_notes") or {})
    return new_summary, changed_notes
