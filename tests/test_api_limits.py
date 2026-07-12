"""HTTP contract tests for bounded session inspection endpoints."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from src import main


@pytest.mark.asyncio
async def test_inspection_endpoints_reject_limits_outside_public_contract() -> None:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/session/abc/history", "/session/abc/debug_log"):
            for limit in (0, 1001):
                response = await client.get(path, params={"limit": limit})
                assert response.status_code == 422


@pytest.mark.asyncio
async def test_inspection_endpoints_forward_maximum_allowed_limit(monkeypatch) -> None:  # noqa: ANN001
    observed: dict[str, int] = {}

    class StubRunner:
        async def get_history(self, session_id: str, limit: int):  # noqa: ANN201
            assert session_id == "abc"
            observed["history"] = limit
            return []

    def fake_read_entries(session_id: str, limit: int) -> list[dict]:
        assert session_id == "abc"
        observed["debug_log"] = limit
        return []

    monkeypatch.setattr(main, "_runtime", lambda: SimpleNamespace(runner=StubRunner()))
    monkeypatch.setattr(main, "read_entries", fake_read_entries)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        history = await client.get("/session/abc/history", params={"limit": 1000})
    debug_log = main.get_debug_log("abc", limit=1000)

    assert history.status_code == 200
    assert debug_log == []
    assert observed == {"history": 1000, "debug_log": 1000}
