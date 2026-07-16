"""Provider-neutral HTTP, output policy, parsing, and retry layer."""

from __future__ import annotations

import asyncio
import json
import time
from copy import deepcopy
from typing import Any, cast

import httpx

from src.llm.adapters import get_provider_adapter
from src.llm.debug_log import log_llm_call
from src.llm.schema import JSONSchemaValidationError, validate_json_schema

DEFAULT_LLM_TIMEOUT_SECONDS = 60.0


def resolve_llm_timeout(config: dict) -> float:
    """Return a positive configured timeout or the application default."""
    value = config.get("llm_timeout_seconds", DEFAULT_LLM_TIMEOUT_SECONDS)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return float(value)
    return DEFAULT_LLM_TIMEOUT_SECONDS


def normalize_generated_text(text: str) -> str:
    """Enforce the product's punctuation rule on generated, user-visible text."""
    return text.replace(" — ", ", ").replace("—", ", ").replace(" – ", "-").replace("–", "-")


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
    provider: str = "llama_cpp",
    api_base: str = "",
    api_key: str = "",
    thinking_enabled: bool = False,
    validation_schema: dict[str, Any] | None = None,
    json_schema: dict[str, Any] | None = None,
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
            (``.data/sessions/{session_id}/debug.jsonl``).
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

    messages = [deepcopy(m) for m in messages]
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
    adapter = get_provider_adapter(provider)
    prepared = adapter.prepare_request(
        messages,
        response_format,
        json_schema,
        thinking_enabled,
    )
    messages = prepared.messages
    response_format = prepared.response_format
    payload["messages"] = messages
    if response_format is None:
        payload.pop("response_format", None)
    else:
        payload["response_format"] = response_format
    payload.update(prepared.extra_payload)
    request_url = adapter.completion_url(api_base)
    headers = adapter.headers(api_key)

    started = time.perf_counter()
    content: str | None = None
    usage: dict[str, Any] | None = None
    cache_hit_tokens: int | None = None
    cache_miss_tokens: int | None = None
    try:
        r = await client.post(
            request_url,
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )
        r.raise_for_status()
        parsed_response = adapter.extract_response(r.json())
        content = parsed_response.content
        usage = parsed_response.usage
        cache_hit_tokens = parsed_response.cache_hit_tokens
        cache_miss_tokens = parsed_response.cache_miss_tokens
        if response_format is not None:
            if not content or not content.strip():
                raise json.JSONDecodeError("Empty response from LLM", content or "", 0)
            parsed = json.loads(content)
            if validation_schema is not None:
                validate_json_schema(parsed, validation_schema)
    except Exception as e:
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        log_llm_call(
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
            provider,
            api_base,
            thinking_enabled,
            usage,
            cache_hit_tokens,
            cache_miss_tokens,
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    log_llm_call(
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
        provider,
        api_base,
        thinking_enabled,
        usage,
        cache_hit_tokens,
        cache_miss_tokens,
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
    provider: str = "llama_cpp",
    api_base: str = "",
    api_key: str = "",
    thinking_enabled: bool = False,
) -> dict:
    """Wrapper that forces JSON output and performs ``json.loads()``.

    If ``json_schema`` is provided (``{"name": ..., "schema": {...}}``), it uses
    ``response_format: {"type": "json_schema", "json_schema": ...}`` — the output
    is grammar-constrained on the server. Without schema, it falls back to
    ``{"type": "json_object"}``.

    Performs retries with exponential backoff if the returned JSON is malformed,
    if the content is empty, or if the server returns a transient HTTP error.
    Definitive client errors (4xx except 408/429) fail fast: resending the same
    request cannot fix them, so no retry budget is spent on them.

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
    requested_format: dict[str, Any] = (
        {"type": "json_schema", "json_schema": json_schema}
        if json_schema is not None
        else {"type": "json_object"}
    )
    last_error: Exception | None = None
    attempts_made = 0
    for attempt in range(retries + 1):
        attempts_made = attempt + 1
        try:
            content = await chat_completion(
                client,
                messages,
                model=model,
                language=language,
                response_format=requested_format,
                max_tokens=max_tokens,
                timeout=timeout,
                session_id=session_id,
                turn_number=turn_number,
                agent=agent,
                attempt_number=attempt + 1,
                provider=provider,
                api_base=api_base,
                api_key=api_key,
                thinking_enabled=thinking_enabled,
                validation_schema=json_schema["schema"] if json_schema is not None else None,
                json_schema=json_schema,
            )
            return cast(dict, json.loads(content))
        except (
            json.JSONDecodeError,
            JSONSchemaValidationError,
            KeyError,
            httpx.HTTPStatusError,
            httpx.RequestError,
        ) as e:
            last_error = e
            if _is_unretryable(e):
                break
            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))  # backoff: 0.5s, 1s
            continue

    raise ValueError(
        f"Falha ao obter JSON válido após {attempts_made} tentativas. Último erro: {last_error}"
    )


def _is_unretryable(error: Exception) -> bool:
    """A definitive client error: resending the identical request cannot fix it.

    408 (request timeout) and 429 (rate limit) are transient by definition and
    keep their retry budget; every other 4xx means the request itself is wrong.
    """
    if not isinstance(error, httpx.HTTPStatusError):
        return False
    status = error.response.status_code
    return 400 <= status < 500 and status not in (408, 429)
