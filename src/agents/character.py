"""Agente Personagem — age in-character, responde com fala ou pensamento."""

from __future__ import annotations

import httpx

from src.llm.client import chat_completion
from src.models import Character, TurnRecord, speaker_label, trim_history_by_tokens


def _build_system_prompt(character: Character) -> str:
    return (
        f"You are {character.mind.name}. Stay in character at all times.\n"
        f"Personality: {character.mind.personality}\n"
        f"Knowledge: {', '.join(character.mind.knowledge)}\n"
        f"Current mood: {character.mind.current_mood}\n"
        "\n"
        "RULES:\n"
        "- You are a character in a roleplay scene. You CANNOT narrate, describe\n"
        "  the environment, or describe anyone's physical actions or body\n"
        "  language — including your own or someone else's. That is the\n"
        "  Narrator's job, never yours.\n"
        "- Speak in first person, as dialogue.\n"
        "- Use **text** for internal thoughts — always wrap them, no exceptions.\n"
        "  A thought is your own reaction, opinion, or feeling; it is never a\n"
        "  description of what someone else is doing or how they look.\n"
        "- Only use information from the provided context. Do not invent facts.\n"
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
    """Formata o histórico como texto linear para o personagem.

    O personagem só vê falas anteriores — nunca narrações nem ações (isso
    quebraria o modelo de papéis: só o Narrador narra/descreve/age). Ele reage
    à mensagem atual do Narrador (``context_for_character``), trimado por
    orçamento de tokens se ``context_max`` informado.
    """
    hist = [rec for rec in history if rec.content_type == "speech"]
    if context_max is not None:
        hist = trim_history_by_tokens(hist, context_max, max_tokens_character)
    if not hist:
        return "(none)"
    lines: list[str] = []
    for rec in hist:
        label = speaker_label(rec.speaker, characters, controlled_id)
        lines.append(f"Turn {rec.turn_number} — {label}: {rec.content}")
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
) -> str:
    """Constrói prompt do Personagem, chama LLM, retorna fala/pensamento.

    Args:
        client: httpx.AsyncClient compartilhado.
        character: O personagem (só Mind é usada no prompt).
        context: ``context_for_character`` vindo do Narrador.
        history: Histórico completo da sessão (usado para construir parte
                 do contexto de eventos recentes).
        characters: Todos os personagens da sessão — só usado para traduzir
                    ``speaker_label`` no histórico (nunca vaza `body`/personalidade
                    de outros para o prompt).
        controlled_id: ID do personagem controlado pelo humano — usado só para
                       traduzir o marcador interno "Player" no nome do personagem.
        config: Config do servidor (temperatura, max_tokens).
        session_id: Repassado ao log bruto de chamadas LLM (ver ``src/llm/client.py``).
        turn_number: Repassado ao log bruto.

    Returns:
        A fala/pensamento (string pura, sem JSON).
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
        {"role": "system", "content": _build_system_prompt(character)},
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
        session_id=session_id,
        turn_number=turn_number,
        agent=f"character:{character.mind.name}",
    )

    return content.strip()
