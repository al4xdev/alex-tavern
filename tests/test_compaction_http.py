"""HTTP content negotiation and cancellation for explicit compaction."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest

from src.compaction import CompactionProgress


def _sec_headers() -> dict:
    from tests.conftest import sec_headers

    return sec_headers()


def _install_runtime(main_mod, monkeypatch):  # noqa: ANN001, ANN202
    llm_client = httpx.AsyncClient()
    runner = main_mod.Runner(llm_client, {})
    runtime = main_mod.RuntimeState({}, {}, llm_client, runner)
    monkeypatch.setattr(main_mod.app.state, "runtime", runtime, raising=False)
    return runtime


def _result() -> dict[str, Any]:
    return {
        "status": "compacted",
        "trigger": "manual",
        "compaction_id": "c000001",
        "compacted": True,
        "reason": None,
        "cutoff_turn_number": 3,
        "evicted_records": 2,
        "kept_records": 2,
        "estimated_context_tokens": None,
        "threshold_tokens": None,
        "context_max": 100,
        "undo_depth": 1,
    }


@pytest.mark.asyncio
async def test_compact_endpoint_preserves_json_and_streams_equivalent_sse(
    monkeypatch,  # noqa: ANN001
) -> None:
    from src import main as main_mod

    result = _result()
    calls: list[bool] = []

    async def get_state(_session_id):  # noqa: ANN001, ANN202
        return {}

    async def compact(_session_id, *, progress=None):  # noqa: ANN001, ANN202
        calls.append(progress is not None)
        if progress is not None:
            progress(CompactionProgress("c000001", 1, "checking", 0, 0))
            progress(
                CompactionProgress(
                    "c000001",
                    2,
                    "completed",
                    3,
                    3,
                    result=result,
                )
            )
        return result

    runtime = _install_runtime(main_mod, monkeypatch)
    runner = runtime.runner
    monkeypatch.setattr(runner, "get_state", get_state)
    monkeypatch.setattr(runner, "compact_session", compact)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main_mod.app),
        base_url="http://test",
        headers=_sec_headers(),
    ) as client:
        json_response = await client.post(
            "/session/streamtest/compact", headers={"Accept": "application/json"}
        )
        stream_response = await client.post(
            "/session/streamtest/compact", headers={"Accept": "text/event-stream"}
        )

    assert json_response.status_code == 200
    assert json_response.json()["compaction_id"] == result["compaction_id"]
    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"].startswith("text/event-stream")
    assert stream_response.headers["cache-control"] == "no-store"
    assert stream_response.headers["x-accel-buffering"] == "no"
    payloads = [
        json.loads(line.removeprefix("data: "))
        for line in stream_response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert [payload["stage"] for payload in payloads] == ["checking", "completed"]
    assert payloads[-1]["result"] == json_response.json()
    assert calls == [False, True]
    await runtime.llm_client.aclose()


@pytest.mark.asyncio
async def test_sse_failure_has_one_sanitized_terminal_event(monkeypatch) -> None:  # noqa: ANN001
    from src import main as main_mod

    async def get_state(_session_id):  # noqa: ANN001, ANN202
        return {}

    async def fail(_session_id, *, progress=None):  # noqa: ANN001, ANN202
        assert progress is not None
        progress(CompactionProgress("c000001", 1, "checking", 0, 0))
        progress(
            CompactionProgress(
                "c000001",
                2,
                "failed",
                0,
                3,
                error_type="RuntimeError",
            )
        )
        raise RuntimeError("private response must stay server-side")

    runtime = _install_runtime(main_mod, monkeypatch)
    runner = runtime.runner
    monkeypatch.setattr(runner, "get_state", get_state)
    monkeypatch.setattr(runner, "compact_session", fail)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main_mod.app),
        base_url="http://test",
        headers=_sec_headers(),
    ) as client:
        response = await client.post(
            "/session/streamtest/compact", headers={"Accept": "text/event-stream"}
        )

    assert response.status_code == 200
    assert response.text.count("event: failed") == 1
    assert "RuntimeError" in response.text
    assert "private response" not in response.text
    await runtime.llm_client.aclose()


@pytest.mark.asyncio
async def test_closing_sse_consumer_cancels_and_awaits_runner() -> None:
    from src.main import _compaction_event_stream

    cancelled = asyncio.Event()

    class WaitingRunner:
        async def compact_session(self, _session_id, *, progress=None):  # noqa: ANN001, ANN202
            assert progress is not None
            progress(CompactionProgress("c000001", 1, "checking", 0, 0))
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

    stream = _compaction_event_stream(WaitingRunner(), "streamtest")
    first = await anext(stream)
    assert "event: checking" in first
    await stream.aclose()
    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_unresolved_plugin_undo_conflict_returns_409(monkeypatch) -> None:  # noqa: ANN001
    from src import main as main_mod

    runtime = _install_runtime(main_mod, monkeypatch)

    async def conflict(_session_id):  # noqa: ANN001, ANN202
        return {
            "restored": False,
            "undone": False,
            "reason": "Plugin state changed after compaction; undo requires a resolver.",
            "plugin_conflicts": ["weather"],
            "remaining_undo_depth": 1,
        }

    monkeypatch.setattr(runtime.runner, "restore_last_compaction", conflict)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main_mod.app),
        base_url="http://test",
        headers=_sec_headers(),
    ) as client:
        response = await client.post("/session/conflict/restore_compaction")

    assert response.status_code == 409
    assert response.json()["plugin_conflicts"] == ["weather"]
    await runtime.llm_client.aclose()
