"""Async wrapper for llama.cpp (OpenAI-compatible) via httpx.

Endpoint: /v1/chat/completions on localhost:8888
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import UTC, datetime
from typing import Any, cast

import httpx

from src.paths import SESSIONS_DIR

DEFAULT_LLM_TIMEOUT_SECONDS = 60.0
_debug_log_locks: dict[str, threading.Lock] = {}
_debug_log_locks_guard = threading.Lock()


def resolve_llm_timeout(config: dict) -> float:
    """Return a positive configured timeout or the backward-compatible default."""
    value = config.get("llm_timeout_seconds", DEFAULT_LLM_TIMEOUT_SECONDS)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return float(value)
    return DEFAULT_LLM_TIMEOUT_SECONDS


def normalize_generated_text(text: str) -> str:
    """Enforce the product's punctuation rule on generated, user-visible text."""
    return text.replace(" — ", ", ").replace("—", ", ").replace(" – ", "-").replace("–", "-")


def _get_debug_log_lock(session_id: str) -> threading.Lock:
    """Return the process-local lock protecting one append-only debug log."""
    with _debug_log_locks_guard:
        return _debug_log_locks.setdefault(session_id, threading.Lock())


def _append_debug_entry(session_id: str, entry: dict[str, Any]) -> None:
    """Append one complete JSON line while holding the session's log lock."""
    if not session_id:
        return
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with _get_debug_log_lock(session_id):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONS_DIR / f"{session_id}.debug.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


def log_turn_input(
    session_id: str,
    turn_number: int,
    speech: str,
    action: str,
    requested_force_speaker: str | None,
    effective_force_speaker: str | None,
) -> None:
    """Append the exact API turn payload before any LLM call for that turn."""
    if not session_id:
        return
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "turn_number": turn_number,
        "agent": "turn_input",
        "input": {
            "speech": speech,
            "action": action,
            "force_speaker": requested_force_speaker,
        },
        "effective_force_speaker": effective_force_speaker,
    }
    _append_debug_entry(session_id, entry)


def _log_llm_call(
    session_id: str,
    turn_number: int,
    agent: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    response_format: dict | None,
    response: str | None,
    error: BaseException | None,
    duration_ms: float,
    attempt_number: int,
) -> None:
    """Appends a raw sequential record of the actual LLM call.

    One file per session (``.data/sessions/{session_id}.debug.jsonl``), one
    JSON line per call — intended for low-level debugging (what was
    REALLY sent/received, including retries), not for structured UI.
    Without ``session_id`` (e.g. calls outside a session), nothing is recorded.
    """
    if not session_id:
        return
    prompt_chars = sum(len(str(message.get("content", ""))) for message in messages)
    error_message = (str(error) or repr(error)) if error is not None else None
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
        "error": error_message,
        "error_type": type(error).__name__ if error is not None else None,
        "error_repr": repr(error) if error is not None else None,
        "duration_ms": duration_ms,
        "attempt_number": attempt_number,
        "prompt_chars": prompt_chars,
        "prompt_estimated_tokens": prompt_chars // 4,
    }
    _append_debug_entry(session_id, entry)


def log_undo(session_id: str, turn_number: int, removed_records: int) -> None:
    """Appends a marker to the raw log indicating that an undo occurred.

    Does not affect or revert the log — it is just a sequential event so anyone
    reading the ``.debug.jsonl`` afterwards knows, amidst the actual LLM calls,
    at what point a step was undone and how many history records were removed.
    """
    if not session_id:
        return
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "turn_number": turn_number,
        "agent": "undo",
        "removed_records": removed_records,
    }
    _append_debug_entry(session_id, entry)


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
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "agent": "compact",
        "cutoff_turn_number": cutoff_turn_number,
        "evicted_records": evicted_records,
        "kept_records": kept_records,
    }
    _append_debug_entry(session_id, entry)


def log_restore_compaction(session_id: str, restored: bool, reason: str) -> None:
    """Appends a marker of a compaction restore attempt to the raw log.

    Logs both success and refusal (refusal is the safe path — see
    ``store.sessions.restore_last_backup``) — useful to know when debugging
    if and why a restore was blocked.
    """
    if not session_id:
        return
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "agent": "restore_compaction",
        "restored": restored,
        "reason": reason,
    }
    _append_debug_entry(session_id, entry)


async def chat_completion(
    client: httpx.AsyncClient,
    messages: list[dict],
    *,
    model: str = "",
    language: str = "",
    response_format: dict | None = None,
    max_tokens: int = 1024,
    timeout: float = DEFAULT_LLM_TIMEOUT_SECONDS,
    session_id: str = "",
    turn_number: int = 0,
    agent: str = "",
    attempt_number: int = 1,
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
        "Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in your writing; "
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
        system_content = system_msg.get("content", "")
        if instruction not in system_content:
            system_msg["content"] = system_content.rstrip() + instruction
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

    started = time.perf_counter()
    content: str | None = None
    try:
        r = await client.post(
            "/v1/chat/completions",
            json=payload,
            timeout=httpx.Timeout(timeout),
        )
        r.raise_for_status()
        content = cast(str, r.json()["choices"][0]["message"]["content"])
        if response_format is not None:
            if not content or not content.strip():
                raise json.JSONDecodeError("Empty response from LLM", content or "", 0)
            json.loads(content)
    except Exception as e:
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        _log_llm_call(
            session_id,
            turn_number,
            agent,
            model,
            messages,
            max_tokens,
            response_format,
            content,
            e,
            duration_ms,
            attempt_number,
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
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
        duration_ms,
        attempt_number,
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
    timeout: float = DEFAULT_LLM_TIMEOUT_SECONDS,
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
                attempt_number=attempt + 1,
            )
            return cast(dict, json.loads(content))
        except (json.JSONDecodeError, KeyError, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))  # backoff: 0.5s, 1s
            continue

    raise ValueError(
        f"Falha ao obter JSON válido após {retries + 1} tentativas. Último erro: {last_error}"
    )
