"""Replay recorded LLM outputs through a minimal OpenAI-compatible HTTP server."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException


class ReplayFixtureError(ValueError):
    """Raised when a replay fixture cannot be parsed safely."""


@dataclass(frozen=True, slots=True)
class ReplayEntry:
    """One successful LLM output extracted from a raw session debug log."""

    source_line: int
    agent: str
    turn_number: int | None
    response: str
    response_format_type: str | None


def _response_format_type(request: object) -> str | None:
    if not isinstance(request, dict):
        return None
    response_format = request.get("response_format")
    if not isinstance(response_format, dict):
        return None
    value = response_format.get("type")
    return value if isinstance(value, str) else None


def load_replay_entries(path: Path) -> list[ReplayEntry]:
    """Load successful response entries from a session ``.debug.jsonl`` file once."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReplayFixtureError(f"Cannot read replay fixture {path}: {exc}") from exc

    entries: list[ReplayEntry] = []
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ReplayFixtureError(
                f"Invalid JSON on line {line_number} of {path}: {exc.msg}"
            ) from exc
        if not isinstance(record, dict):
            raise ReplayFixtureError(f"Expected a JSON object on line {line_number} of {path}")

        response = record.get("response")
        if record.get("error") is not None:
            continue
        if response is None:
            continue
        if not isinstance(response, str):
            raise ReplayFixtureError(
                f"Expected response to be a string on line {line_number} of {path}"
            )

        turn_number = record.get("turn_number")
        if not isinstance(turn_number, int):
            turn_number = None
        agent = record.get("agent")
        entries.append(
            ReplayEntry(
                source_line=line_number,
                agent=agent if isinstance(agent, str) else "unknown",
                turn_number=turn_number,
                response=response,
                response_format_type=_response_format_type(record.get("request")),
            )
        )
    return entries


class ReplayTape:
    """Concurrency-safe cursor over immutable replay entries."""

    def __init__(self, entries: list[ReplayEntry], *, strict: bool = True) -> None:
        self._entries = tuple(entries)
        self._cursor = 0
        self._strict = strict
        self._lock = asyncio.Lock()

    async def consume(self, request: dict[str, Any]) -> ReplayEntry:
        """Return and advance past the next compatible entry."""
        incoming_type = _response_format_type(request)
        async with self._lock:
            if self._cursor >= len(self._entries):
                raise HTTPException(
                    status_code=409,
                    detail="Replay fixture exhausted. Reset or seek before requesting more.",
                )
            entry = self._entries[self._cursor]
            if self._strict and entry.response_format_type != incoming_type:
                expected = entry.response_format_type or "plain text"
                received = incoming_type or "plain text"
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Replay mismatch at position {self._cursor}: expected {expected} "
                        f"for {entry.agent} turn {entry.turn_number}, received {received}."
                    ),
                )
            self._cursor += 1
            return entry

    async def seek(self, position: int) -> dict[str, Any]:
        """Move the cursor to an absolute position, including the exhausted position."""
        async with self._lock:
            if position < 0 or position > len(self._entries):
                raise HTTPException(
                    status_code=422,
                    detail=f"Position must be between 0 and {len(self._entries)}.",
                )
            self._cursor = position
            return self._status_unlocked()

    async def reset(self) -> dict[str, Any]:
        """Move the cursor back to the first entry."""
        return await self.seek(0)

    async def status(self) -> dict[str, Any]:
        """Return cursor metadata without exposing recorded response content."""
        async with self._lock:
            return self._status_unlocked()

    def _status_unlocked(self) -> dict[str, Any]:
        total = len(self._entries)
        next_entry = self._entries[self._cursor] if self._cursor < total else None
        return {
            "total": total,
            "cursor": self._cursor,
            "remaining": total - self._cursor,
            "strict": self._strict,
            "next": (
                {
                    "agent": next_entry.agent,
                    "turn_number": next_entry.turn_number,
                    "source_line": next_entry.source_line,
                    "response_format_type": next_entry.response_format_type,
                }
                if next_entry is not None
                else None
            ),
        }


def create_app(tape: ReplayTape) -> FastAPI:
    """Build a replay server around one tape instance."""
    app = FastAPI(title="Alex Tavern LLM Replay", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "replay": await tape.status()}

    @app.get("/replay/status")
    async def replay_status() -> dict[str, Any]:
        return await tape.status()

    @app.post("/replay/reset")
    async def replay_reset() -> dict[str, Any]:
        return await tape.reset()

    @app.post("/replay/seek/{position}")
    async def replay_seek(position: int) -> dict[str, Any]:
        return await tape.seek(position)

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: dict[str, Any]) -> dict[str, Any]:
        entry = await tape.consume(payload)
        requested_model = payload.get("model")
        model = requested_model if isinstance(requested_model, str) else "replay"
        return {
            "id": f"replay-{entry.source_line}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": entry.response},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "replay": {
                "agent": entry.agent,
                "turn_number": entry.turn_number,
                "source_line": entry.source_line,
            },
        }

    return app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve successful responses from a session debug JSONL in order."
    )
    parser.add_argument("fixture", type=Path, help="Path to a .debug.jsonl replay fixture")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not compare plain-text versus structured-output request types.",
    )
    return parser.parse_args()


def main() -> None:
    """Load a fixture and run the local replay server."""
    args = _parse_args()
    entries = load_replay_entries(args.fixture)
    if not entries:
        raise SystemExit(f"No replayable responses found in {args.fixture}")
    tape = ReplayTape(entries, strict=not args.no_strict)
    uvicorn.run(create_app(tape), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
