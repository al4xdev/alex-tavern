"""Wrapper async para llama.cpp (OpenAI-compatible) via httpx.

Endpoint: /v1/chat/completions em localhost:8888
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import httpx

LLAMA_HOST = "http://localhost:8888"
CHAT_ENDPOINT = "/v1/chat/completions"
DEFAULT_TIMEOUT = 60.0


async def chat_completion(
    client: httpx.AsyncClient,
    messages: list[dict],
    *,
    response_format: dict | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Chama /v1/chat/completions e retorna ``content`` como string.

    Args:
        client: httpx.AsyncClient compartilhado (base_url aponta para LLAMA_HOST).
        messages: Lista de mensagens no formato OpenAI.
        response_format: ``{"type": "json_object"}`` ou ``None``.
        max_tokens: Máximo de tokens na resposta.
        temperature: Temperatura do modelo.
        timeout: Timeout em segundos.

    Returns:
        Conteúdo da mensagem de resposta (string).

    Raises:
        httpx.HTTPError: Se a chamada HTTP falhar.
        KeyError: Se a resposta não tiver o formato esperado.
    """
    payload: dict[str, Any] = {
        "model": "",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    r = await client.post(
        CHAT_ENDPOINT,
        json=payload,
        timeout=httpx.Timeout(timeout),
    )
    r.raise_for_status()
    return cast(str, r.json()["choices"][0]["message"]["content"])


async def chat_completion_json(
    client: httpx.AsyncClient,
    messages: list[dict],
    *,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    retries: int = 2,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Wrapper que força ``response_format`` json_object e faz ``json.loads()``.

    Faz retries com backoff exponencial se o JSON retornado for malformado.

    Args:
        client: httpx.AsyncClient compartilhado.
        messages: Lista de mensagens no formato OpenAI.
        max_tokens: Máximo de tokens na resposta.
        temperature: Temperatura (default 0 para JSON determinístico).
        retries: Número de retries se JSON malformado (backoff: 0.5s, 1s, ...).
        timeout: Timeout em segundos.

    Returns:
        JSON parseado como dict.

    Raises:
        ValueError: Se não conseguir parsear JSON depois de N retries.
    """
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            content = await chat_completion(
                client,
                messages,
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
            )
            return cast(dict, json.loads(content))
        except (json.JSONDecodeError, KeyError) as e:
            last_error = e
            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))  # backoff: 0.5s, 1s
            continue

    raise ValueError(
        f"Falha ao obter JSON válido após {retries + 1} tentativas. "
        f"Último erro: {last_error}"
    )
