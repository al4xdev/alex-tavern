"""Tests for the deterministic OpenAI-compatible LLM replay server."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from tools.replay_llm import ReplayFixtureError, ReplayTape, create_app, load_replay_entries


def _record(
    response: str | None,
    *,
    agent: str = "narrator",
    turn_number: int = 1,
    response_format_type: str | None = "json_schema",
) -> str:
    request: dict = {"messages": []}
    if response_format_type is not None:
        request["response_format"] = {"type": response_format_type}
    return json.dumps(
        {
            "agent": agent,
            "turn_number": turn_number,
            "request": request,
            "response": response,
            "error": None if response is not None else "timeout",
        }
    )


def _write_fixture(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_load_replay_entries_filters_errors_and_markers(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [
            _record('{"narration":"one"}'),
            _record(None),
            json.dumps({"agent": "compact", "cutoff_turn_number": 2}),
            _record("Lyra speaks", agent="character:Lyra", response_format_type=None),
        ],
    )

    entries = load_replay_entries(path)

    assert [entry.response for entry in entries] == [
        '{"narration":"one"}',
        "Lyra speaks",
    ]
    assert [entry.source_line for entry in entries] == [1, 4]
    assert entries[0].response_format_type == "json_schema"
    assert entries[1].response_format_type is None


def test_load_replay_entries_rejects_malformed_json(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path / "broken.debug.jsonl", ["{not-json}"])

    with pytest.raises(ReplayFixtureError, match="line 1"):
        load_replay_entries(path)


async def test_replay_serves_entries_in_order_and_then_exhausts(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [
            _record('{"narration":"one"}'),
            _record("Lyra speaks", agent="character:Lyra", response_format_type=None),
        ],
    )
    app = create_app(ReplayTape(load_replay_entries(path)))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://replay") as client:
        narrator = await client.post(
            "/v1/chat/completions",
            json={"model": "test", "response_format": {"type": "json_schema"}},
        )
        character = await client.post("/v1/chat/completions", json={"model": "test"})
        exhausted = await client.post("/v1/chat/completions", json={"model": "test"})

    assert narrator.status_code == 200
    assert narrator.json()["choices"][0]["message"]["content"] == '{"narration":"one"}'
    assert narrator.json()["replay"] == {
        "agent": "narrator",
        "turn_number": 1,
        "source_line": 1,
    }
    assert character.json()["choices"][0]["message"]["content"] == "Lyra speaks"
    assert exhausted.status_code == 409
    assert "exhausted" in exhausted.json()["detail"]


async def test_mismatch_does_not_advance_and_reset_rewinds(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [_record('{"narration":"one"}')],
    )
    app = create_app(ReplayTape(load_replay_entries(path)))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://replay") as client:
        mismatch = await client.post("/v1/chat/completions", json={})
        status_after_mismatch = await client.get("/replay/status")
        success = await client.post(
            "/v1/chat/completions",
            json={"response_format": {"type": "json_schema"}},
        )
        reset = await client.post("/replay/reset")

    assert mismatch.status_code == 409
    assert "mismatch" in mismatch.json()["detail"]
    assert status_after_mismatch.json()["cursor"] == 0
    assert success.status_code == 200
    assert reset.json()["cursor"] == 0
    assert reset.json()["remaining"] == 1


async def test_seek_validates_bounds(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [_record("one", response_format_type=None)],
    )
    app = create_app(ReplayTape(load_replay_entries(path)))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://replay") as client:
        exhausted_position = await client.post("/replay/seek/1")
        invalid_position = await client.post("/replay/seek/2")

    assert exhausted_position.status_code == 200
    assert exhausted_position.json()["remaining"] == 0
    assert invalid_position.status_code == 422


async def test_concurrent_requests_consume_distinct_entries(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [
            _record("one", response_format_type=None),
            _record("two", turn_number=2, response_format_type=None),
        ],
    )
    app = create_app(ReplayTape(load_replay_entries(path)))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://replay") as client:
        first, second = await asyncio.gather(
            client.post("/v1/chat/completions", json={}),
            client.post("/v1/chat/completions", json={}),
        )
        status = await client.get("/replay/status")

    contents = {
        first.json()["choices"][0]["message"]["content"],
        second.json()["choices"][0]["message"]["content"],
    }
    assert contents == {"one", "two"}
    assert status.json()["cursor"] == 2


async def test_empty_fixture_is_healthy_but_exhausted(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path / "session.debug.jsonl",
        [json.dumps({"agent": "compact", "kept_records": 2})],
    )
    app = create_app(ReplayTape(load_replay_entries(path)))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://replay") as client:
        health = await client.get("/health")
        completion = await client.post("/v1/chat/completions", json={})

    assert health.json()["status"] == "ok"
    assert health.json()["replay"]["total"] == 0
    assert completion.status_code == 409
