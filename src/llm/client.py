"""Async wrapper for llama.cpp (OpenAI-compatible) via httpx.

Endpoint: /v1/chat/completions on localhost:8888
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
    """Appends a raw sequential record of the actual LLM call.

    One file per session (``.data/sessions/{session_id}.debug.jsonl``), one
    JSON line per call — intended for low-level debugging (what was
    REALLY sent/received, including retries), not for structured UI.
    Without ``session_id`` (e.g. calls outside a session), nothing is recorded.
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
    """Appends a marker to the raw log indicating that an undo occurred.

    Does not affect or revert the log — it is just a sequential event so anyone
    reading the ``.debug.jsonl`` afterwards knows, amidst the actual LLM calls,
    at what point a step was undone and how many history records were removed.
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
    """Appends a marker to the raw log indicating that compaction occurred.

    Same idea as ``log_undo``: does not rewrite or affect the log, only marks the
    actual sequence of events — so anyone reading the ``.debug.jsonl`` afterwards
    understands why the history got smaller at a certain point.
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
    """Appends a marker of a compaction restore attempt to the raw log.

    Logs both success and refusal (refusal is the safe path — see
    ``store.sessions.restore_last_backup``) — useful to know when debugging
    if and why a restore was blocked.
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
    """Calls /v1/chat/completions and returns ``content`` as string.

    Args:
        client: Shared httpx.AsyncClient.
        messages: List of messages in OpenAI format.
        model: Model name.
        language: Response language to inject (optional). Regardless,
            every call receives the instruction to avoid em/en dashes.
        response_format: ``{"type": "json_object"}`` or ``None``.
        max_tokens: Maximum tokens in the response.
        timeout: Timeout in seconds.
        session_id: If provided, records this call in the raw session log
            (``.data/sessions/{session_id}.debug.jsonl``).
        turn_number: Number of the turn/step that triggered the call (log).
        agent: Who triggered the call — "narrator", "narrator_suggest" or
            "character:<name>" (log).

    Returns:
        Content of the response message (string).

    Raises:
        httpx.HTTPError: If the HTTP call fails.
        KeyError: If the response is not in the expected format.
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
            session_id,
            turn_number,
            agent,
            model,
            messages,
            max_tokens,
            response_format,
            None,
            str(e),
        )
        raise
    _log_llm_call(
        session_id,
        turn_number,
        agent,
        model,
        messages,
        max_tokens,
        response_format,
        content,
        None,
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
    """Wrapper that forces JSON output and performs ``json.loads()``.

    If ``json_schema`` is provided (``{"name": ..., "schema": {...}}``), it uses
    ``response_format: {"type": "json_schema", "json_schema": ...}`` — the output
    is grammar-constrained on the server. Without schema, it falls back to
    ``{"type": "json_object"}``.

    Performs retries with exponential backoff if the returned JSON is malformed,
    if the content is empty, or if the server returns an HTTP error (5xx).

    Args:
        client: Shared httpx.AsyncClient.
        messages: List of messages in OpenAI format.
        model: Model name.
        language: Response language to inject (optional). Regardless,
            every call receives the instruction to avoid em/en dashes.
        max_tokens: Maximum tokens in the response.
        json_schema: Optional schema for structured output via grammar.
        retries: Number of retries if invalid response (backoff: 0.5s, 1s, ...).
        timeout: Timeout in seconds.
        session_id: Passed to the raw log (see ``chat_completion``).
        turn_number: Passed to the raw log.
        agent: Passed to the raw log.

    Returns:
        Parsed JSON as a dict.

    Raises:
        ValueError: If a valid JSON cannot be obtained after N+1 attempts.
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
        f"Falha ao obter JSON válido após {retries + 1} tentativas. Último erro: {last_error}"
    )
