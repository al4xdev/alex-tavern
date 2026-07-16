"""Task 31: unified structured-output retry policy at the client layer.

Every structured agent call shares the same budget (``chat_completion_json``
default), transient failures are retried with backoff, definitive client errors
fail fast, and the character semantic-correction loop never multiplies the
format-retry budget.
"""

from __future__ import annotations

import json

import httpx
import pytest

from src.agents import character as character_mod
from src.llm.client import chat_completion_json
from src.models import Character, CharacterBody, CharacterMind

CHARACTERS = {
    "C1": Character(
        mind=CharacterMind(
            name="Thorn", personality="Direto.", knowledge=[], current_mood="neutro"
        ),
        body=CharacterBody(name="Thorn", physical_description="Alto.", outfit="Capa."),
    ),
    "C2": Character(
        mind=CharacterMind(
            name="Vela", personality="Calma.", knowledge=[], current_mood="neutra"
        ),
        body=CharacterBody(name="Vela", physical_description="Baixa.", outfit="Túnica."),
    ),
}

VALID_CONTENT = json.dumps(
    {"speech": "Oi.", "thought": "Ele parece tranquilo.", "action_intent": None}
)
PHYSICAL_ACTION_CONTENT = json.dumps(
    {"speech": None, "thought": "Arrumo um tufo de cabelo atrás da orelha.", "action_intent": None}
)


def _response(status: int, content: str, request: httpx.Request) -> httpx.Response:
    if status != 200:
        return httpx.Response(status, text=content, request=request)
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
        request=request,
    )


def _sequenced_post(plan: list[tuple[int, str]]):
    """Return (post, calls) where post plays the plan and repeats its last step."""
    calls: list[int] = []

    async def post(url, json=None, **kwargs):  # noqa: ANN001, ANN202, A002, ARG001
        step = plan[min(len(calls), len(plan) - 1)]
        calls.append(step[0])
        return _response(step[0], step[1], httpx.Request("POST", url))

    return post, calls


async def _act(client: httpx.AsyncClient) -> dict:
    return await character_mod.act(
        client=client,
        character=CHARACTERS["C2"],
        context="Thorn cumprimenta.",
        history=[],
        characters=CHARACTERS,
        controlled_id="C1",
        character_id="C2",
        config={},
    )


@pytest.fixture
def no_backoff(monkeypatch) -> None:  # noqa: ANN001
    async def instant(delay: float) -> None:
        assert delay > 0

    monkeypatch.setattr("src.llm.client.asyncio.sleep", instant)


class TestUnifiedRetryPolicy:
    @pytest.mark.asyncio
    async def test_character_call_survives_one_malformed_response(
        self, monkeypatch, no_backoff
    ) -> None:  # noqa: ANN001
        post, calls = _sequenced_post([(200, "not-json"), (200, VALID_CONTENT)])
        async with httpx.AsyncClient(base_url="http://localhost:8888") as client:
            monkeypatch.setattr(client, "post", post)
            output = await _act(client)
        assert output == {"speech": "Oi.", "thought": "Ele parece tranquilo.", "action_intent": None}
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_definitive_client_error_fails_fast(
        self, monkeypatch, no_backoff
    ) -> None:  # noqa: ANN001
        post, calls = _sequenced_post([(400, "bad request")])
        async with httpx.AsyncClient(base_url="http://localhost:8888") as client:
            monkeypatch.setattr(client, "post", post)
            with pytest.raises(ValueError, match="após 1 tentativas"):
                await chat_completion_json(client, [{"role": "user", "content": "JSON."}])
        assert len(calls) == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("transient_status", [408, 429, 503])
    async def test_transient_http_errors_keep_their_retry_budget(
        self, monkeypatch, no_backoff, transient_status: int
    ) -> None:  # noqa: ANN001
        post, calls = _sequenced_post([(transient_status, "busy"), (200, '{"ok": true}')])
        async with httpx.AsyncClient(base_url="http://localhost:8888") as client:
            monkeypatch.setattr(client, "post", post)
            result = await chat_completion_json(client, [{"role": "user", "content": "JSON."}])
        assert result == {"ok": True}
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_persistent_malformed_output_exhausts_client_budget_only(
        self, monkeypatch, no_backoff
    ) -> None:  # noqa: ANN001
        """Format failures burn the client budget (3 calls), never 2x3 via act()."""
        post, calls = _sequenced_post([(200, "not-json")])
        async with httpx.AsyncClient(base_url="http://localhost:8888") as client:
            monkeypatch.setattr(client, "post", post)
            with pytest.raises(ValueError, match="após 3 tentativas"):
                await _act(client)
        assert len(calls) == 3

    @pytest.mark.asyncio
    async def test_correction_loop_does_not_multiply_format_retries(
        self, monkeypatch, no_backoff
    ) -> None:  # noqa: ANN001
        """Semantic corrections are act()-level: 2 attempts, 1 provider call each."""
        post, calls = _sequenced_post([(200, PHYSICAL_ACTION_CONTENT)])
        async with httpx.AsyncClient(base_url="http://localhost:8888") as client:
            monkeypatch.setattr(client, "post", post)
            with pytest.raises(ValueError):
                await _act(client)
        assert len(calls) == 2
