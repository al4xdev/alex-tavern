"""Wrapper async para llama.cpp (OpenAI-compatible) via httpx.

Endpoint: /v1/chat/completions em localhost:8888
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

_SESSIONS_DIR = Path(".data/sessions")


def _log_llm_call(
    session_id: str,
    turn_number: int,
    agent: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    response_format: dict | None,
    response: str | None,
    error: str | None,
) -> None:
    """Acrescenta um registro bruto e sequencial da chamada real ao LLM.

    Um arquivo por sessão (``.data/sessions/{session_id}.debug.jsonl``), uma
    linha JSON por chamada — pensado pra debug de baixo nível (o que foi
    REALMENTE enviado/recebido, incluindo retries), não pra UI estruturada.
    Sem ``session_id`` (ex.: chamadas fora de uma sessão), não grava nada.
    """
    if not session_id:
        return
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "turn_number": turn_number,
        "agent": agent,
        "model": model,
        "request": {
            "messages": messages,
            "max_tokens": max_tokens,
            "response_format": response_format,
        },
        "response": response,
        "error": error,
    }
    path = _SESSIONS_DIR / f"{session_id}.debug.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_undo(session_id: str, turn_number: int, removed_records: int) -> None:
    """Acrescenta ao mesmo log bruto um marcador de que um undo aconteceu.

    Não afeta nem reverte o log — é só um evento sequencial, para quem lê o
    ``.debug.jsonl`` depois saber, no meio das chamadas reais ao LLM, em que
    ponto um passo foi desfeito e quantos registros do histórico saíram.
    """
    if not session_id:
        return
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "turn_number": turn_number,
        "agent": "undo",
        "removed_records": removed_records,
    }
    path = _SESSIONS_DIR / f"{session_id}.debug.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_compact(
    session_id: str, cutoff_turn_number: int, evicted_records: int, kept_records: int
) -> None:
    """Acrescenta ao mesmo log bruto um marcador de que uma compactação aconteceu.

    Mesma ideia do ``log_undo``: não reescreve nem afeta o log, só marca a
    sequência real de eventos — pra quem lê o ``.debug.jsonl`` depois entender
    por que o histórico ficou menor num certo ponto.
    """
    if not session_id:
        return
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "agent": "compact",
        "cutoff_turn_number": cutoff_turn_number,
        "evicted_records": evicted_records,
        "kept_records": kept_records,
    }
    path = _SESSIONS_DIR / f"{session_id}.debug.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_restore_compaction(session_id: str, restored: bool, reason: str) -> None:
    """Acrescenta ao mesmo log bruto um marcador de tentativa de desfazer compactação.

    Loga tanto sucesso quanto recusa (a recusa é o caminho seguro — ver
    ``store.sessions.restore_last_backup``) — útil pra saber, ao debugar, se
    e por que uma restauração foi bloqueada.
    """
    if not session_id:
        return
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "agent": "restore_compaction",
        "restored": restored,
        "reason": reason,
    }
    path = _SESSIONS_DIR / f"{session_id}.debug.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def chat_completion(
    client: httpx.AsyncClient,
    messages: list[dict],
    *,
    model: str = "",
    language: str = "",
    response_format: dict | None = None,
    max_tokens: int = 1024,
    timeout: float = 60.0,
    session_id: str = "",
    turn_number: int = 0,
    agent: str = "",
) -> str:
    """Chama /v1/chat/completions e retorna ``content`` como string.

    Args:
        client: httpx.AsyncClient compartilhado.
        messages: Lista de mensagens no formato OpenAI.
        model: O nome do modelo.
        language: Idioma de resposta a ser injetado (opcional). Independente disso,
            toda chamada recebe a instrução de evitar travessão/en dash.
        response_format: ``{"type": "json_object"}`` ou ``None``.
        max_tokens: Máximo de tokens na resposta.
        timeout: Timeout em segundos.
        session_id: Se informado, grava esta chamada no log bruto da sessão
            (``.data/sessions/{session_id}.debug.jsonl``).
        turn_number: Número do turno/passo que disparou a chamada (log).
        agent: Quem disparou a chamada — "narrator", "narrator_suggest" ou
            "character:<nome>" (log).

    Returns:
        Conteúdo da mensagem de resposta (string).

    Raises:
        httpx.HTTPError: Se a chamada HTTP falhar.
        KeyError: Se a resposta não tiver o formato esperado.
    """
    extra_instructions: list[str] = []
    if language:
        extra_instructions.append(f"Always respond and write in {language}.")
    extra_instructions.append(
        "Do not use em dashes or en dashes (— –) anywhere in your writing; "
        "use commas, periods, or parentheses instead."
    )

    import copy
    messages = [copy.deepcopy(m) for m in messages]
    system_msg = None
    for msg in messages:
        if msg.get("role") == "system":
            system_msg = msg
            break

    instruction = "".join(f"\n- {line}" for line in extra_instructions)
    if system_msg:
        content = system_msg.get("content", "")
        if instruction not in content:
            system_msg["content"] = content.rstrip() + instruction
    else:
        messages.insert(0, {"role": "system", "content": instruction.strip()})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    try:
        r = await client.post(
            "/v1/chat/completions",
            json=payload,
            timeout=httpx.Timeout(timeout),
        )
        r.raise_for_status()
        content = cast(str, r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        _log_llm_call(
            session_id, turn_number, agent, model, messages, max_tokens, response_format,
            None, str(e),
        )
        raise
    _log_llm_call(
        session_id, turn_number, agent, model, messages, max_tokens, response_format,
        content, None,
    )
    return content


async def chat_completion_json(
    client: httpx.AsyncClient,
    messages: list[dict],
    *,
    model: str = "",
    language: str = "",
    max_tokens: int = 1024,
    json_schema: dict | None = None,
    retries: int = 2,
    timeout: float = 60.0,
    session_id: str = "",
    turn_number: int = 0,
    agent: str = "",
) -> dict:
    """Wrapper que força saída JSON e faz ``json.loads()``.

    Se ``json_schema`` for informado (``{"name": ..., "schema": {...}}``), usa
    ``response_format: {"type": "json_schema", "json_schema": ...}`` — a saída
    é restrita por gramática no servidor. Sem schema, cai para
    ``{"type": "json_object"}``.

    Faz retries com backoff exponencial se o JSON retornado for malformado,
    se o conteúdo for vazio, ou se o servidor retornar erro HTTP (5xx).

    Args:
        client: httpx.AsyncClient compartilhado.
        messages: Lista de mensagens no formato OpenAI.
        model: O nome do modelo.
        language: Idioma de resposta a ser injetado (opcional). Independente disso,
            toda chamada recebe a instrução de evitar travessão/en dash.
        max_tokens: Máximo de tokens na resposta.
        json_schema: Schema opcional para saída estruturada via grammar.
        retries: Número de retries se resposta inválida (backoff: 0.5s, 1s, ...).
        timeout: Timeout em segundos.
        session_id: Repassado ao log bruto (ver ``chat_completion``).
        turn_number: Repassado ao log bruto.
        agent: Repassado ao log bruto.

    Returns:
        JSON parseado como dict.

    Raises:
        ValueError: Se não conseguir obter JSON válido depois de N+1 tentativas.
    """
    response_format: dict[str, Any] = (
        {"type": "json_schema", "json_schema": json_schema}
        if json_schema is not None
        else {"type": "json_object"}
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            content = await chat_completion(
                client,
                messages,
                model=model,
                language=language,
                response_format=response_format,
                max_tokens=max_tokens,
                timeout=timeout,
                session_id=session_id,
                turn_number=turn_number,
                agent=agent,
            )
            if not content or not content.strip():
                raise json.JSONDecodeError("Empty response from LLM", content or "", 0)
            return cast(dict, json.loads(content))
        except (json.JSONDecodeError, KeyError, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))  # backoff: 0.5s, 1s
            continue

    raise ValueError(
        f"Falha ao obter JSON válido após {retries + 1} tentativas. "
        f"Último erro: {last_error}"
    )
