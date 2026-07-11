"""Agente Personagem — age in-character, responde com fala ou pensamento."""

from __future__ import annotations

import httpx

from src.llm.client import chat_completion
from src.models import Character, TurnRecord


def _build_system_prompt(character: Character) -> str:
    return (
        f"You are {character.mind.name}. Stay in character at all times.\n"
        f"Personality: {character.mind.personality_full}\n"
        f"Knowledge: {', '.join(character.mind.knowledge)}\n"
        f"Current mood: {character.mind.current_mood}\n"
        "\n"
        "RULES:\n"
        "- You are a character in a roleplay scene. You CANNOT narrate actions or\n"
        "  describe the environment. Only your own character can speak or think.\n"
        "- Speak in first person.\n"
        "- Use **text** for internal thoughts.\n"
        "- Only use information from the provided context. Do not invent facts.\n"
        "- Keep responses to 1-3 sentences.\n"
        "- You may address other characters directly.\n"
    )


def _format_history_for_character(history: list[TurnRecord], char_name: str) -> str:
    """Formata o histórico como texto linear para o personagem.

    O personagem vê todas as falas/narrações do histórico (o Narrador já
    filtrou o que é relevante via context_for_character).
    """
    if not history:
        return "(none)"
    lines: list[str] = []
    for rec in history[-5:]:
        lines.append(f"Turn {rec.turn_number} — {rec.speaker}: {rec.content[:300]}")
    return "\n".join(lines)


async def act(
    client: httpx.AsyncClient,
    character: Character,
    context: str,
    history: list[TurnRecord],
    config: dict,
) -> tuple[str, list[dict]]:
    """Constrói prompt do Personagem, chama LLM, retorna fala/pensamento + messages.

    Args:
        client: httpx.AsyncClient compartilhado.
        character: O personagem (só Mind é usada no prompt).
        context: ``context_for_character`` vindo do Narrador.
        history: Histórico completo da sessão (usado para construir parte
                 do contexto de eventos recentes).
        config: Config do servidor (temperatura, max_tokens).

    Returns:
        Tupla ``(content, messages)``: a fala/pensamento (string pura, sem JSON)
        e os messages enviados ao LLM (para o modo debug).
    """
    messages = [
        {"role": "system", "content": _build_system_prompt(character)},
        {
            "role": "user",
            "content": (
                "SCENE CONTEXT (what you perceive right now):\n"
                f"{context}\n"
                "\n"
                "RECENT EVENTS:\n"
                f"{_format_history_for_character(history, character.mind.name)}\n"
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
        max_tokens=config.get("max_tokens_character", 1024),
    )

    return content.strip(), messages
