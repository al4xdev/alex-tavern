"""Agente Narrador — orquestra cena, processa ações, decide quem fala."""

from __future__ import annotations

import json

import httpx

from src.llm.client import chat_completion_json
from src.models import Character, Scene, TurnRecord


def _build_system_prompt(
    character_ids: list[str], narrator_directives: str = ""
) -> str:
    speakers = ", ".join([*character_ids, "Player", "Narrator"])
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        "You describe scenes, process player actions, and decide who speaks next.\n"
        "\n"
        "RULES:\n"
        "- Return ONLY valid JSON, no markdown, no code fences.\n"
        '- "narration": describe what happens in the scene based on the player\'s action\n'
        "  and the current state. Be vivid but concise (2-4 sentences).\n"
        f'- "next_speaker": who should speak/act next. One of: {speakers}.\n'
        '  - Use "Player" when the player needs to make a choice or respond.\n'
        '  - Use "Narrator" when you need to describe something before anyone speaks\n'
        "    (e.g., an environmental event).\n"
        "  - If the Player only performed an action without speaking, prefer\n"
        '    "Player" or "Narrator" as next_speaker — don\'t force a character\n'
        "    to respond to silence unless it makes narrative sense.\n"
        '- "context_for_character": a string with filtered information for the next\n'
        "  speaker. Include only what THAT character would perceive. If next_speaker\n"
        "  is Narrator, use empty string.\n"
        '- "scene_update": object with physical changes to the scene (e.g.,\n'
        '  {"door": "open", "weather": "rain"}). Use null if nothing changed.\n'
        '- "player_options": null OR an array of {index, label, description} when\n'
        "  the player needs to choose an action. Index starts at 0. Max 5 options.\n"
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def _build_user_prompt(
    scene: Scene,
    characters: dict[str, Character],
    player_speech: str,
    player_action: str,
    player_controlled_id: str,
    history: list[TurnRecord],
) -> str:
    """Constrói o user prompt com cena, personagens, input do Player e histórico."""
    lines: list[str] = []

    # Cena atual
    lines.append("CURRENT SCENE:")
    lines.append(f"  Location: {scene.location}")
    lines.append(f"  Time: {scene.time_of_day}")
    lines.append(f"  Physical facts: {json.dumps(scene.physical_facts, ensure_ascii=False)}")
    lines.append("")

    # Personagens presentes
    lines.append("CHARACTERS PRESENT:")
    for cid in characters:
        ch = characters[cid]
        lines.append(f"  {cid} — {ch.mind.name}")
        lines.append(f"    Personality: {ch.mind.personality_summary}")
        lines.append(f"    Appearance: {ch.body.physical_description}")
        lines.append(f"    Outfit: {ch.body.outfit}")
        lines.append(f"    Mood: {ch.mind.current_mood}")
    lines.append(f"  Player controls: {player_controlled_id} (o Player age como este personagem)")
    lines.append("")

    # Input do Player
    lines.append("PLAYER INPUT:")
    lines.append(f"  Speech: {player_speech or '(nothing said)'}")
    lines.append(f"  Action: {player_action or '(no action)'}")
    lines.append("")

    # Histórico recente (últimos 5 turnos)
    lines.append("RECENT HISTORY (last 5 turns):")
    if history:
        recent = history[-5:]
        for rec in recent:
            lines.append(
                f"  Turn {rec.turn_number} — {rec.speaker}: {rec.content[:200]}"
            )
    else:
        lines.append("  (none — first turn)")
    lines.append("")

    return "\n".join(lines)


def build_narrator_messages(
    scene: Scene,
    characters: dict[str, Character],
    player_speech: str,
    player_action: str,
    player_controlled_id: str,
    history: list[TurnRecord],
    narrator_directives: str = "",
) -> list[dict]:
    """Monta os messages (system + user) do Narrador — puro, sem chamar o LLM.

    Reusado tanto por ``narrate`` quanto pelo preview de prompt offline.
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
                player_speech=player_speech,
                player_action=player_action,
                player_controlled_id=player_controlled_id,
                history=history,
            ),
        },
    ]


async def narrate(
    client: httpx.AsyncClient,
    scene: Scene,
    characters: dict[str, Character],
    player_speech: str,
    player_action: str,
    player_controlled_id: str,
    history: list[TurnRecord],
    config: dict,
    narrator_directives: str = "",
) -> tuple[dict, list[dict]]:
    """Constrói prompt do Narrador, chama LLM, devolve dict validado + messages.

    Returns:
        Tupla ``(result, messages)``:
        - ``result``: dict com chaves narration, next_speaker,
          context_for_character, scene_update, player_options (opcional).
        - ``messages``: os messages enviados ao LLM (para o modo debug).

    Raises:
        ValueError: Se o JSON retornado não tiver os campos obrigatórios.
    """
    messages = build_narrator_messages(
        scene=scene,
        characters=characters,
        player_speech=player_speech,
        player_action=player_action,
        player_controlled_id=player_controlled_id,
        history=history,
        narrator_directives=narrator_directives,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=config.get("max_tokens_narrator", 2048),
    )

    # Valida campos obrigatórios
    required = ["narration", "next_speaker", "context_for_character"]
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(
            f"Resposta do Narrador sem campos obrigatórios: {missing}. "
            f"Recebido: {json.dumps(result, ensure_ascii=False)[:300]}"
        )

    # Valida next_speaker — speakers válidos derivados dinamicamente dos IDs
    valid_speakers = set(characters) | {"Player", "Narrator"}
    if result["next_speaker"] not in valid_speakers:
        # Fallback: normaliza para Player
        result["next_speaker"] = "Player"

    # scene_update e player_options podem ser None
    result.setdefault("scene_update", None)
    result.setdefault("player_options", None)

    return result, messages


def format_history_for_prompt(history: list[TurnRecord], limit: int = 5) -> str:
    """Formata histórico como texto linear (opção A do plano)."""
    if not history:
        return "(none)"
    lines: list[str] = []
    for rec in history[-limit:]:
        lines.append(f"Turn {rec.turn_number} — {rec.speaker}: {rec.content[:200]}")
    return "\n".join(lines)
