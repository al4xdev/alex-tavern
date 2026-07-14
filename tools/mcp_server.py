"""Debug-only MCP server for the Roleplay and replay HTTP APIs."""

from __future__ import annotations

import argparse
import json
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import StrictBool

DEFAULT_ROLEPLAY_URL = "http://127.0.0.1:8889"
DEFAULT_REPLAY_URL = "http://127.0.0.1:8888"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 420.0
MAX_READ_LIMIT = 1000

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
MUTATING = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)
DESTRUCTIVE_MUTATION = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)
CURSOR_MUTATION = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


class DebugApiClient:
    """Shared HTTP adapter used by MCP tools."""

    def __init__(
        self,
        roleplay_url: str = DEFAULT_ROLEPLAY_URL,
        replay_url: str = DEFAULT_REPLAY_URL,
        *,
        timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        roleplay_transport: httpx.AsyncBaseTransport | None = None,
        replay_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._roleplay = httpx.AsyncClient(
            base_url=roleplay_url,
            timeout=timeout,
            transport=roleplay_transport,
        )
        self._replay = httpx.AsyncClient(
            base_url=replay_url,
            timeout=timeout,
            transport=replay_transport,
        )

    async def aclose(self) -> None:
        """Close both shared HTTP clients."""
        await self._roleplay.aclose()
        await self._replay.aclose()

    async def _request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        client = self._roleplay if service == "Roleplay" else self._replay
        try:
            response = await client.request(method, path, json=payload, params=params)
        except httpx.TimeoutException as exc:
            raise ToolError(f"{service} request timed out: {method} {path}") from exc
        except httpx.RequestError as exc:
            raise ToolError(f"{service} is unavailable: {exc}") from exc

        if response.is_error:
            try:
                body = response.json()
            except ValueError:
                detail = response.text or response.reason_phrase
            else:
                detail = body.get("detail", body) if isinstance(body, dict) else body
                if not isinstance(detail, str):
                    detail = json.dumps(detail, ensure_ascii=False, sort_keys=True)
            raise ToolError(
                f"{service} returned HTTP {response.status_code} for {method} {path}: {detail}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ToolError(f"{service} returned invalid JSON for {method} {path}") from exc

    async def enumerate_routes(self) -> list[dict[str, str]]:
        """Return the Roleplay OpenAPI operations in stable path/method order."""
        document = await self._request("Roleplay", "GET", "/openapi.json")
        if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):
            raise ToolError("Roleplay OpenAPI document has no paths object")
        routes: list[dict[str, str]] = []
        for path, operations in document["paths"].items():
            if not isinstance(path, str) or not isinstance(operations, dict):
                continue
            for method, operation in operations.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                operation = operation if isinstance(operation, dict) else {}
                routes.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "summary": str(operation.get("summary", "")),
                        "operation_id": str(operation.get("operationId", "")),
                    }
                )
        return sorted(routes, key=lambda route: (route["path"], route["method"]))

    async def list_sessions(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], await self._request("Roleplay", "GET", "/sessions"))

    async def session_state(self, session_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self._request("Roleplay", "GET", f"/session/{session_id}/state"),
        )

    async def session_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        _validate_limit(limit)
        return cast(
            list[dict[str, Any]],
            await self._request(
                "Roleplay",
                "GET",
                f"/session/{session_id}/history",
                params={"limit": limit},
            ),
        )

    async def debug_log(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        _validate_limit(limit)
        return cast(
            list[dict[str, Any]],
            await self._request(
                "Roleplay",
                "GET",
                f"/session/{session_id}/debug_log",
                params={"limit": limit},
            ),
        )

    async def start_session(
        self,
        *,
        scenario_name: str | None = None,
        controlled_character_id: str | None = None,
        characters: dict[str, Any] | None = None,
        scene: dict[str, Any] | None = None,
        narrator_directives: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            key: value
            for key, value in {
                "scenario_name": scenario_name,
                "controlled_character_id": controlled_character_id,
                "characters": characters,
                "scene": scene,
                "narrator_directives": narrator_directives,
            }.items()
            if value is not None
        }
        return cast(
            dict[str, Any],
            await self._request("Roleplay", "POST", "/session/start", payload=payload),
        )

    async def fork_session(self, session_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self._request("Roleplay", "POST", f"/session/{session_id}/fork"),
        )

    async def submit_turn(
        self,
        session_id: str,
        *,
        speech: str = "",
        thought: str = "",
        action: str = "",
        force_speaker: str | None = None,
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self._request(
                "Roleplay",
                "POST",
                f"/session/{session_id}/turn",
                payload={
                    "speech": speech,
                    "thought": thought,
                    "action": action,
                    "force_speaker": force_speaker,
                },
            ),
        )

    async def mutate_session(self, session_id: str, operation: str) -> dict[str, Any]:
        if operation not in {"suggest", "undo", "compact", "restore_compaction"}:
            raise ToolError(f"Unsupported session operation: {operation}")
        return cast(
            dict[str, Any],
            await self._request("Roleplay", "POST", f"/session/{session_id}/{operation}"),
        )

    async def replay_status(self) -> dict[str, Any]:
        return cast(dict[str, Any], await self._request("Replay", "GET", "/replay/status"))

    async def reset_replay(self) -> dict[str, Any]:
        return cast(dict[str, Any], await self._request("Replay", "POST", "/replay/reset"))

    async def seek_replay(self, position: int) -> dict[str, Any]:
        if position < 0:
            raise ToolError("Replay position must be zero or greater")
        return cast(
            dict[str, Any],
            await self._request("Replay", "POST", f"/replay/seek/{position}"),
        )


def _validate_limit(limit: int) -> None:
    if not 1 <= limit <= MAX_READ_LIMIT:
        raise ToolError(f"limit must be between 1 and {MAX_READ_LIMIT}")


def _require_destructive_confirmation(operation: str, confirm: bool) -> None:
    """Require an explicit boolean confirmation for state-destructive tools."""
    if confirm is not True:
        raise ToolError(
            f"{operation} can change or discard session state; call again with confirm=true"
        )


def create_mcp_server(
    roleplay_url: str = DEFAULT_ROLEPLAY_URL,
    replay_url: str = DEFAULT_REPLAY_URL,
    *,
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    api: DebugApiClient | None = None,
) -> FastMCP:
    """Build the stdio MCP server and register its debug tools."""
    debug_api = api or DebugApiClient(roleplay_url, replay_url, timeout=request_timeout)

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {"debug_api": debug_api}
        finally:
            await debug_api.aclose()

    server = FastMCP(
        "Alex Tavern Debug",
        instructions=(
            "Local debugging tools for the Roleplay HTTP API and deterministic replay server. "
            "Debug logs may contain private prompts and model responses."
        ),
        lifespan=lifespan,
    )

    @server.tool(annotations=READ_ONLY)
    async def inspect_api_routes() -> list[dict[str, str]]:
        """Enumerate Roleplay HTTP routes from its live OpenAPI document."""
        return await debug_api.enumerate_routes()

    @server.tool(annotations=READ_ONLY)
    async def inspect_sessions() -> list[dict[str, Any]]:
        """List persisted Roleplay sessions and their summary metadata."""
        return await debug_api.list_sessions()

    @server.tool(annotations=READ_ONLY)
    async def inspect_session_state(session_id: str) -> dict[str, Any]:
        """Read the complete live state of one Roleplay session."""
        return await debug_api.session_state(session_id)

    @server.tool(annotations=READ_ONLY)
    async def inspect_session_history(session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Read recent history records from a Roleplay session."""
        return await debug_api.session_history(session_id, limit)

    @server.tool(annotations=READ_ONLY)
    async def inspect_debug_log(session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        """Read raw LLM debug records, which may include private prompts and responses."""
        return await debug_api.debug_log(session_id, limit)

    @server.tool(annotations=READ_ONLY)
    async def inspect_replay_status() -> dict[str, Any]:
        """Read the deterministic replay cursor and next-entry metadata."""
        return await debug_api.replay_status()

    @server.tool(annotations=MUTATING)
    async def mutate_start_session(
        scenario_name: str | None = None,
        controlled_character_id: str | None = None,
        characters: dict[str, Any] | None = None,
        scene: dict[str, Any] | None = None,
        narrator_directives: str | None = None,
    ) -> dict[str, Any]:
        """Create a session from a scenario or explicit character and scene data."""
        return await debug_api.start_session(
            scenario_name=scenario_name,
            controlled_character_id=controlled_character_id,
            characters=characters,
            scene=scene,
            narrator_directives=narrator_directives,
        )

    @server.tool(annotations=MUTATING)
    async def mutate_fork_session(session_id: str) -> dict[str, Any]:
        """Create a non-destructive copy of an existing session."""
        return await debug_api.fork_session(session_id)

    @server.tool(annotations=MUTATING)
    async def mutate_submit_turn(
        session_id: str,
        speech: str = "",
        thought: str = "",
        action: str = "",
        force_speaker: str | None = None,
    ) -> dict[str, Any]:
        """Submit player input and optionally force the responding speaker."""
        return await debug_api.submit_turn(
            session_id,
            speech=speech,
            thought=thought,
            action=action,
            force_speaker=force_speaker,
        )

    @server.tool(annotations=MUTATING)
    async def mutate_request_suggestions(session_id: str) -> dict[str, Any]:
        """Ask the live Roleplay backend for possible player moves."""
        return await debug_api.mutate_session(session_id, "suggest")

    @server.tool(annotations=DESTRUCTIVE_MUTATION)
    async def mutate_undo_turn(session_id: str, confirm: StrictBool = False) -> dict[str, Any]:
        """Remove the most recent Roleplay turn where the HTTP API supports it."""
        _require_destructive_confirmation("undo", confirm)
        return await debug_api.mutate_session(session_id, "undo")

    @server.tool(annotations=DESTRUCTIVE_MUTATION)
    async def mutate_compact_session(
        session_id: str, confirm: StrictBool = False
    ) -> dict[str, Any]:
        """Summarize older history and retain a recoverable compaction backup."""
        _require_destructive_confirmation("compaction", confirm)
        return await debug_api.mutate_session(session_id, "compact")

    @server.tool(annotations=DESTRUCTIVE_MUTATION)
    async def mutate_restore_compaction(
        session_id: str, confirm: StrictBool = False
    ) -> dict[str, Any]:
        """Restore the latest compaction backup when the backend safety check permits it."""
        _require_destructive_confirmation("compaction restore", confirm)
        return await debug_api.mutate_session(session_id, "restore_compaction")

    @server.tool(annotations=CURSOR_MUTATION)
    async def mutate_reset_replay() -> dict[str, Any]:
        """Reset the replay cursor to its first recorded output."""
        return await debug_api.reset_replay()

    @server.tool(annotations=CURSOR_MUTATION)
    async def mutate_seek_replay(position: int) -> dict[str, Any]:
        """Move the replay cursor to an absolute zero-based position."""
        return await debug_api.seek_replay(position)

    return server


def _positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("request timeout must be a number") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("request timeout must be greater than zero")
    return timeout


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Roleplay debug MCP over stdio.")
    parser.add_argument("--roleplay-url", default=DEFAULT_ROLEPLAY_URL)
    parser.add_argument("--replay-url", default=DEFAULT_REPLAY_URL)
    parser.add_argument(
        "--request-timeout",
        type=_positive_timeout,
        default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        help="HTTP request timeout in seconds (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Run the debug MCP server over stdio."""
    args = _parse_args()
    create_mcp_server(
        args.roleplay_url,
        args.replay_url,
        request_timeout=args.request_timeout,
    ).run(transport="stdio")


if __name__ == "__main__":
    main()
