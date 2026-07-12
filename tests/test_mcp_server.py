"""Tests for the debug MCP HTTP adapter and tool registry."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from tools.mcp_server import DebugApiClient, create_mcp_server


def _json_response(request: httpx.Request, payload: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload, request=request)


@pytest.mark.asyncio
async def test_adapter_maps_supported_operations_to_http() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path == "/openapi.json":
            return _json_response(
                request,
                {
                    "paths": {
                        "/sessions": {"get": {"summary": "List", "operationId": "get_sessions"}},
                        "/session/{session_id}": {
                            "delete": {"summary": "Delete", "operationId": "delete_session"}
                        },
                    }
                },
            )
        if path == "/sessions":
            return _json_response(request, [{"session_id": "abc"}])
        if path.endswith("/history") or path.endswith("/debug_log"):
            return _json_response(request, [{"path": path}])
        if path.endswith("/state"):
            return _json_response(request, {"session_id": "abc"})
        if path == "/replay/status":
            return _json_response(request, {"cursor": 1})
        return _json_response(request, {"path": path})

    transport = httpx.MockTransport(handler)
    api = DebugApiClient(roleplay_transport=transport, replay_transport=transport)
    try:
        routes = await api.enumerate_routes()
        assert routes == [
            {
                "method": "DELETE",
                "path": "/session/{session_id}",
                "summary": "Delete",
                "operation_id": "delete_session",
            },
            {
                "method": "GET",
                "path": "/sessions",
                "summary": "List",
                "operation_id": "get_sessions",
            },
        ]
        assert await api.list_sessions() == [{"session_id": "abc"}]
        assert await api.session_state("abc") == {"session_id": "abc"}
        await api.session_history("abc", 25)
        await api.debug_log("abc", 75)
        await api.start_session(preset_name="thorn-lyra", controlled_character_id="C1")
        await api.fork_session("abc")
        await api.submit_turn("abc", speech="Hello", action="Wave", force_speaker="C2")
        for operation in ("suggest", "undo", "compact", "restore_compaction"):
            await api.mutate_session("abc", operation)
        assert await api.replay_status() == {"cursor": 1}
        await api.reset_replay()
        await api.seek_replay(3)
    finally:
        await api.aclose()

    history_request = next(request for request in requests if request.url.path.endswith("/history"))
    debug_request = next(request for request in requests if request.url.path.endswith("/debug_log"))
    assert history_request.url.params["limit"] == "25"
    assert debug_request.url.params["limit"] == "75"

    start_request = next(request for request in requests if request.url.path == "/session/start")
    assert start_request.method == "POST"
    assert start_request.read().decode() == (
        '{"preset_name":"thorn-lyra","controlled_character_id":"C1"}'
    )
    turn_request = next(request for request in requests if request.url.path.endswith("/turn"))
    assert turn_request.read().decode() == (
        '{"speech":"Hello","action":"Wave","force_speaker":"C2"}'
    )
    assert any(request.url.path == "/replay/reset" for request in requests)
    assert any(request.url.path == "/replay/seek/3" for request in requests)


@pytest.mark.asyncio
async def test_adapter_reports_http_errors_with_detail() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(request, {"detail": "Session not found"}, status=404)

    api = DebugApiClient(roleplay_transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ToolError, match="HTTP 404.*Session not found"):
            await api.session_state("missing")
    finally:
        await api.aclose()


@pytest.mark.asyncio
async def test_adapter_reports_unavailable_service() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    api = DebugApiClient(replay_transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ToolError, match="Replay is unavailable.*connection refused"):
            await api.replay_status()
    finally:
        await api.aclose()


@pytest.mark.asyncio
async def test_adapter_reports_timeout_and_invalid_json() -> None:
    async def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    timeout_api = DebugApiClient(roleplay_transport=httpx.MockTransport(timeout_handler))
    try:
        with pytest.raises(ToolError, match="Roleplay request timed out"):
            await timeout_api.list_sessions()
    finally:
        await timeout_api.aclose()

    async def invalid_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json", request=request)

    invalid_api = DebugApiClient(roleplay_transport=httpx.MockTransport(invalid_handler))
    try:
        with pytest.raises(ToolError, match="invalid JSON"):
            await invalid_api.list_sessions()
    finally:
        await invalid_api.aclose()


@pytest.mark.asyncio
async def test_adapter_validates_limits_and_replay_position_before_http() -> None:
    api = DebugApiClient()
    try:
        for limit in (0, 1001):
            with pytest.raises(ToolError, match="limit must be between"):
                await api.session_history("abc", limit)
            with pytest.raises(ToolError, match="limit must be between"):
                await api.debug_log("abc", limit)
        with pytest.raises(ToolError, match="zero or greater"):
            await api.seek_replay(-1)
        with pytest.raises(ValueError, match="Unsupported"):
            await api.mutate_session("abc", "delete")
    finally:
        await api.aclose()


@pytest.mark.asyncio
async def test_mcp_registry_separates_tools_and_omits_delete_and_retry() -> None:
    api = DebugApiClient(
        roleplay_transport=httpx.MockTransport(lambda request: _json_response(request, {})),
        replay_transport=httpx.MockTransport(lambda request: _json_response(request, {})),
    )
    server = create_mcp_server(api=api)
    try:
        tools = await server.list_tools()
    finally:
        await api.aclose()

    by_name = {tool.name: tool for tool in tools}
    assert set(by_name) == {
        "inspect_api_routes",
        "inspect_sessions",
        "inspect_session_state",
        "inspect_session_history",
        "inspect_debug_log",
        "inspect_replay_status",
        "mutate_start_session",
        "mutate_fork_session",
        "mutate_submit_turn",
        "mutate_request_suggestions",
        "mutate_undo_turn",
        "mutate_compact_session",
        "mutate_restore_compaction",
        "mutate_reset_replay",
        "mutate_seek_replay",
    }
    assert not any("delete" in name or "retry" in name for name in by_name)
    assert all(
        tool.annotations is not None and tool.annotations.readOnlyHint
        for name, tool in by_name.items()
        if name.startswith("inspect_")
    )
    assert all(
        tool.annotations is not None and not tool.annotations.readOnlyHint
        for name, tool in by_name.items()
        if name.startswith("mutate_")
    )
    for name in ("mutate_undo_turn", "mutate_compact_session", "mutate_restore_compaction"):
        assert by_name[name].annotations is not None
        assert by_name[name].annotations.destructiveHint is True
