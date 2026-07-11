"""Agente Narrador — orquestra cena, processa ações, decide quem fala."""

from __future__ import annotations

import json

import httpx

from src.llm.client import chat_completion_json
from src.models import Character, Scene, TurnRecord, speaker_label, trim_history_by_tokens


def _build_system_prompt(
    character_ids: list[str], narrator_directives: str = ""
) -> str:
    speakers = ", ".join([*character_ids, "Narrator"])
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        "You describe scenes, process what happens, and decide who speaks next.\n"
        "\n"
        "FIELDS:\n"
        '- "narration": describe what happens in the scene based on the last event in\n'
        "  HISTORY and the current state. Be vivid but concise (2-4 sentences).\n"
        f'- "next_speaker": who should speak/act next. One of: {speakers}.\n'
        "  - Use a character id when that character should react.\n"
        '  - Use "Narrator" when you need to describe something before anyone speaks\n'
        "    (e.g., an environmental event), or when no reaction is needed yet.\n"
        '- "context_for_character": a string with filtered information for the next\n'
        "  speaker. Include only what THAT character would perceive. If next_speaker\n"
        "  is Narrator, use empty string.\n"
        '- "scene_update": object with physical changes to the scene (e.g.,\n'
        '  {"door": "open", "weather": "rain"}). Use null if nothing changed.\n'
        "  Set a key's value to null to remove that fact from the scene entirely\n"
        "  (e.g., an item that no longer exists).\n"
        '- "mood_updates": null OR an object mapping character_id to their new mood,\n'
        "  only for characters whose mood actually changed this turn (e.g.\n"
        '  {"C1": "furioso"}). Omit characters whose mood is unchanged.\n'
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_narrator_json_schema(character_ids: list[str]) -> dict:
    """Monta o JSON schema estrutural da resposta do Narrador.

    Usado com ``response_format: {"type": "json_schema", ...}`` — a saída do
    LLM é restrita por gramática, não depende de instrução textual tipo
    "no markdown, no code fences".
    """
    speakers = [*character_ids, "Narrator"]
    return {
        "name": "narrator_turn",
        "schema": {
            "type": "object",
            "properties": {
                "narration": {"type": "string"},
                "next_speaker": {"type": "string", "enum": speakers},
                "context_for_character": {"type": "string"},
                "scene_update": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": ["string", "null"]},
                },
                "mood_updates": {
                    "type": ["object", "null"],
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": [
                "narration",
                "next_speaker",
                "context_for_character",
                "scene_update",
                "mood_updates",
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
) -> str:
    """Constrói o user prompt com cena, personagens e histórico.

    Sem bloco de input separado: a última jogada (de quem quer que seja,
    incluindo o personagem controlado) já está no fim do HISTORY.
    """
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
        lines.append(f"    Personality: {ch.mind.personality}")
        lines.append(f"    Appearance: {ch.body.physical_description}")
        lines.append(f"    Outfit: {ch.body.outfit}")
        lines.append(f"    Mood: {ch.mind.current_mood}")
    lines.append("")

    # Histórico — janela completa, ou trimada por orçamento de tokens se context_max informado
    lines.append("HISTORY:")
    hist = history
    if context_max is not None:
        hist = trim_history_by_tokens(history, context_max, max_tokens_narrator)
    if hist:
        for rec in hist:
            label = speaker_label(rec.speaker, characters, player_controlled_id)
            lines.append(f"  Turn {rec.turn_number} — {label}: {rec.content}")
    else:
        lines.append("  (none — first turn)")
    lines.append("")

    return "\n".join(lines)


def build_narrator_messages(
    scene: Scene,
    characters: dict[str, Character],
    player_controlled_id: str,
    history: list[TurnRecord],
    narrator_directives: str = "",
    context_max: int | None = None,
    max_tokens_narrator: int = 2048,
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
                player_controlled_id=player_controlled_id,
                history=history,
                context_max=context_max,
                max_tokens_narrator=max_tokens_narrator,
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
) -> tuple[dict, list[dict]]:
    """Constrói prompt do Narrador, chama LLM, devolve dict validado + messages.

    O Narrador é cego: não sabe que existe um humano. Ele reage à última
    entrada do HISTORY, seja de quem for. ``player_controlled_id`` só é usado
    para traduzir o marcador interno ``"Player"`` no nome do personagem ao
    montar o histórico — nunca aparece como texto no prompt.

    Returns:
        Tupla ``(result, messages)``:
        - ``result``: dict com chaves narration, next_speaker,
          context_for_character, scene_update, mood_updates.
        - ``messages``: os messages enviados ao LLM (para o modo debug).

    Raises:
        ValueError: Se o JSON retornado não tiver os campos obrigatórios.
    """
    max_tokens_narrator = config.get("max_tokens_narrator", 2048)
    messages = build_narrator_messages(
        scene=scene,
        characters=characters,
        player_controlled_id=player_controlled_id,
        history=history,
        narrator_directives=narrator_directives,
        context_max=config.get("context_max"),
        max_tokens_narrator=max_tokens_narrator,
    )

    result = await chat_completion_json(
        client,
        messages,
        model=config.get("model", ""),
        language=config.get("language", ""),
        max_tokens=max_tokens_narrator,
        json_schema=build_narrator_json_schema(list(characters)),
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
    valid_speakers = set(characters) | {"Narrator"}
    if result["next_speaker"] not in valid_speakers:
        # Fallback: normaliza para Narrator (o Narrador não conhece "Player")
        result["next_speaker"] = "Narrator"

    # scene_update e mood_updates podem ser None
    result.setdefault("scene_update", None)
    result.setdefault("mood_updates", None)

    return result, messages


def _build_suggest_system_prompt(target_id: str, narrator_directives: str = "") -> str:
    prompt = (
        "You are the Narrator of a roleplay game. You know EVERYTHING about the world.\n"
        f"Suggest 3 plausible next moves for {target_id}, given their personality, mood,\n"
        "knowledge and the current scene/history. Each suggestion is a distinct, in-\n"
        "character option — vary tone/approach across the 3.\n"
        "\n"
        'Return an object with a "suggestions" array of exactly 3 items, each with\n'
        '"speech" (what they say, or empty string) and "action" (what they physically\n'
        'do, or empty string).\n'
    )
    if narrator_directives.strip():
        prompt += (
            "\nWORLD DIRECTIVES (tone, rules, setting — always respect these):\n"
            f"{narrator_directives.strip()}\n"
        )
    return prompt


def build_suggest_json_schema() -> dict:
    """JSON schema da resposta de sugestão de jogadas (gatilho manual, Task 6)."""
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
) -> tuple[list[dict], list[dict]]:
    """Pede ao Narrador (cego) uma lista de jogadas possíveis para ``target_id``.

    Usado pelo gatilho "sugira pra mim": o Narrador não sabe que ``target_id``
    é o personagem controlado pelo humano — a pergunta é genérica ("sugira
    jogadas para este personagem"), igual seria para qualquer outro. Não
    persiste nada; quem chama decide o que fazer com as sugestões.

    Returns:
        Tupla ``(suggestions, messages)``: lista de ``{"speech", "action"}``
        e os messages enviados ao LLM (para o modo debug).
    """
    max_tokens_narrator = config.get("max_tokens_narrator", 2048)
    messages = [
        {
            "role": "system",
            "content": _build_suggest_system_prompt(target_id, narrator_directives),
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
        json_schema=build_suggest_json_schema(),
    )

    suggestions = result.get("suggestions", [])
    return suggestions, messages
