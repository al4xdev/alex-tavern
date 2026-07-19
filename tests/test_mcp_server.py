"""Tests for the debug MCP HTTP adapter and tool registry."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.exceptions import ToolError

from tools.mcp_server import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DebugApiClient,
    _parse_args,
    create_mcp_server,
)


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
        await api.start_session(scenario_name="thorn-lyra", controlled_character_id="C1")
        await api.fork_session("abc")
        await api.submit_turn(
            "abc", speech="Hello", thought="Stay alert.", action="Wave", force_speaker="C2"
        )
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
        '{"scenario_name":"thorn-lyra","controlled_character_id":"C1"}'
    )
    turn_request = next(request for request in requests if request.url.path.endswith("/turn"))
    assert turn_request.read().decode() == (
        '{"speech":"Hello","thought":"Stay alert.","action":"Wave","force_speaker":"C2"}'
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
@pytest.mark.parametrize(
    ("response_kwargs", "expected_detail"),
    [
        (
            {
                "json": {
                    "detail": [
                        {
                            "type": "int_parsing",
                            "loc": ["query", "limit"],
                            "msg": "Input should be a valid integer",
                        }
                    ]
                }
            },
            '[{"loc": ["query", "limit"], "msg": "Input should be a valid integer", '
            '"type": "int_parsing"}]',
        ),
        ({"json": {"error": "backend failed"}}, '{"error": "backend failed"}'),
        ({"text": "plain backend failure"}, "plain backend failure"),
        ({"content": b""}, "Internal Server Error"),
    ],
)
async def test_adapter_formats_structured_and_text_http_errors(
    response_kwargs: dict[str, Any], expected_detail: str
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request=request, **response_kwargs)

    api = DebugApiClient(roleplay_transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ToolError, match=re.escape(expected_detail)):
            await api.list_sessions()
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
async def test_adapter_uses_configured_request_timeout() -> None:
    api = DebugApiClient(timeout=75.5)
    try:
        assert api._roleplay.timeout == httpx.Timeout(75.5)
        assert api._replay.timeout == httpx.Timeout(75.5)
    finally:
        await api.aclose()


def test_mcp_cli_configures_positive_request_timeout() -> None:
    assert _parse_args([]).request_timeout == DEFAULT_REQUEST_TIMEOUT_SECONDS
    assert _parse_args(["--request-timeout", "75.5"]).request_timeout == 75.5
    for invalid in ("0", "-1", "not-a-number"):
        with pytest.raises(SystemExit):
            _parse_args(["--request-timeout", invalid])


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
        with pytest.raises(ToolError, match="Unsupported"):
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
        "replay_extract_call",
        "replay_llm_call",
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


@pytest.mark.asyncio
async def test_destructive_mcp_tools_require_explicit_confirmation() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _json_response(request, {"ok": True})

    api = DebugApiClient(roleplay_transport=httpx.MockTransport(handler))
    server = create_mcp_server(api=api)
    try:
        for tool_name in (
            "mutate_undo_turn",
            "mutate_compact_session",
            "mutate_restore_compaction",
        ):
            with pytest.raises(ToolError, match="confirm=true"):
                await server.call_tool(tool_name, {"session_id": "abc"})
            for invalid_confirmation in ("true", "false", 1, 0):
                with pytest.raises(ToolError, match="valid boolean"):
                    await server.call_tool(
                        tool_name,
                        {"session_id": "abc", "confirm": invalid_confirmation},
                    )
            await server.call_tool(tool_name, {"session_id": "abc", "confirm": True})
    finally:
        await api.aclose()

    assert [request.url.path for request in requests] == [
        "/session/abc/undo",
        "/session/abc/compact",
        "/session/abc/restore_compaction",
    ]


@pytest.mark.asyncio
async def test_mcp_stdio_initializes_and_lists_tools() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["tools/mcp_server.py"],
        cwd=repository_root,
    )

    with Path(os.devnull).open("w", encoding="utf-8") as errlog:
        async with (
            stdio_client(parameters, errlog=errlog) as (read, write),
            ClientSession(read, write) as session,
        ):
            initialized = await session.initialize()
            tools = await session.list_tools()

    assert initialized.serverInfo.name == "Alex Tavern Debug"
    assert len(tools.tools) == 17
    assert {tool.name for tool in tools.tools} >= {
        "inspect_api_routes",
        "mutate_submit_turn",
        "mutate_compact_session",
    }


# ---------------------------------------------------------------------------
# Curl-replay tools (recorded call -> active provider)
# ---------------------------------------------------------------------------


def _write_debug_log(session_id: str, records: list[dict[str, Any]]) -> None:
    from src.store.sessions import session_debug_path

    path = session_debug_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _recorded(agent: str, turn: int, system: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "turn_number": turn,
        "model": "recorded-model",
        "provider": "deepseek",
        "ts": "2026-07-19T03:00:00Z",
        "request": {
            "max_tokens": 2048,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": "hello"},
            ],
            "response_format": {"type": "json_object"},
        },
        "response": {"ok": True},
    }


def _mock_api() -> DebugApiClient:
    return DebugApiClient(
        roleplay_transport=httpx.MockTransport(lambda request: _json_response(request, {})),
        replay_transport=httpx.MockTransport(lambda request: _json_response(request, {})),
    )


@pytest.mark.asyncio
async def test_replay_extract_selects_agent_turn_and_occurrence() -> None:
    _write_debug_log(
        "mcpjog1",
        [
            _recorded("narrator", 1, "first"),
            _recorded("narrator", 2, "second"),
            _recorded("prose", 2, "prose-sys"),
        ],
    )
    api = _mock_api()
    server = create_mcp_server(api=api)
    try:
        _, latest = await server.call_tool(
            "replay_extract_call", {"session_id": "mcpjog1", "agent": "narrator"}
        )
        assert latest["turn_number"] == 2
        assert latest["request"]["messages"][0]["content"] == "second"

        _, by_turn = await server.call_tool(
            "replay_extract_call",
            {"session_id": "mcpjog1", "agent": "narrator", "turn_number": 1},
        )
        assert by_turn["request"]["messages"][0]["content"] == "first"

        with pytest.raises(ToolError, match="agents in this session"):
            await server.call_tool(
                "replay_extract_call", {"session_id": "mcpjog1", "agent": "missing"}
            )
    finally:
        await api.aclose()


def test_apply_system_edits_keeps_schema_tail_last() -> None:
    from tools.mcp_server import _apply_system_edits

    messages = [
        {
            "role": "system",
            "content": "Rule one.\n\nReturn only one JSON object matching: {}",
        },
        {"role": "user", "content": "hi"},
    ]
    edited = _apply_system_edits(
        messages,
        append_to_system="New closing rule.",
        replace_old="Rule one.",
        replace_new="Rule 1.",
    )
    content = edited[0]["content"]
    assert content.startswith("Rule 1.\nNew closing rule.\n")
    assert content.endswith("Return only one JSON object matching: {}")
    # original untouched, replace_old must match exactly once
    assert messages[0]["content"].startswith("Rule one.")
    with pytest.raises(ToolError, match="exactly once"):
        _apply_system_edits(messages, replace_old="absent", replace_new="x")


@pytest.mark.asyncio
async def test_replay_llm_call_edits_prompt_and_fires_active_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_debug_log("mcpjog2", [_recorded("prose", 3, "Base.\n\nReturn only one JSON object x")])
    seen: list[dict[str, Any]] = []

    async def fake_chat_completion(client: Any, messages: list[dict], **kwargs: Any) -> str:
        seen.append({"messages": messages, "kwargs": kwargs})
        return '{"narration": "ok"}'

    monkeypatch.setattr("src.llm.client.chat_completion", fake_chat_completion)
    monkeypatch.setattr(
        "src.config.load_config",
        lambda *args, **kwargs: {
            "provider": "deepseek",
            "model": "active-model",
            "api_base": "https://api.deepseek.com",
            "api_key": "k",
        },
    )
    monkeypatch.setattr("src.config.resolve_active_config", lambda value: value)

    api = _mock_api()
    server = create_mcp_server(api=api)
    try:
        _, result = await server.call_tool(
            "replay_llm_call",
            {
                "session_id": "mcpjog2",
                "agent": "prose",
                "append_to_system": "Closing trigger.",
                "runs": 2,
            },
        )
    finally:
        await api.aclose()

    assert len(seen) == 2
    system = seen[0]["messages"][0]["content"]
    assert "Closing trigger." in system
    assert system.endswith("Return only one JSON object x")
    assert seen[0]["kwargs"]["model"] == "active-model"
    assert seen[0]["kwargs"]["agent"] == "mcp-replay:prose"
    assert result["active_model"] == "active-model"
    assert result["recorded_model"] == "recorded-model"
    assert [run["content"] for run in result["runs"]] == ['{"narration": "ok"}'] * 2

    with pytest.raises(ToolError, match="runs must be between"):
        await server.call_tool(
            "replay_llm_call", {"session_id": "mcpjog2", "agent": "prose", "runs": 99}
        )
