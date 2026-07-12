"""Recreate a recorded Roleplay session through the real HTTP API and compare outputs."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


class ReplaySessionError(RuntimeError):
    """Raised when a recorded conversation cannot be reconstructed or replayed."""


@dataclass(frozen=True, slots=True)
class RecordedTurn:
    """One exact player turn plus the override needed to align recorded LLM calls."""

    turn_number: int
    speech: str
    action: str
    force_speaker: str | None


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object from disk with a useful error message."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplaySessionError(f"Cannot load JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReplaySessionError(f"Expected a JSON object in {path}")
    return value


def load_debug_records(path: Path) -> list[dict[str, Any]]:
    """Load an append-only debug JSONL file once."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReplaySessionError(f"Cannot read debug log {path}: {exc}") from exc

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReplaySessionError(
                f"Invalid JSON on line {line_number} of {path}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise ReplaySessionError(f"Expected an object on line {line_number} of {path}")
        records.append(value)
    return records


def successful_outputs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select stable output fields while ignoring timestamps, requests, errors, and markers."""
    outputs: list[dict[str, Any]] = []
    for record in records:
        if record.get("error") is not None:
            continue
        response = record.get("response")
        if not isinstance(response, str):
            continue
        outputs.append(
            {
                "turn_number": record.get("turn_number"),
                "agent": record.get("agent"),
                "response": response,
            }
        )
    return outputs


def build_recorded_turns_from_turn_inputs(
    records: list[dict[str, Any]],
) -> list[RecordedTurn]:
    """Recover exact turns from required ``turn_input`` markers."""
    markers = [record for record in records if record.get("agent") == "turn_input"]
    if not markers:
        raise ReplaySessionError("Debug log contains no turn_input markers")

    turns: list[RecordedTurn] = []
    seen_turns: set[int] = set()
    for marker in markers:
        turn_number = marker.get("turn_number")
        input_payload = marker.get("input")
        if not isinstance(turn_number, int) or not isinstance(input_payload, dict):
            raise ReplaySessionError("Malformed turn_input marker")
        if turn_number in seen_turns:
            raise ReplaySessionError(f"Duplicate turn_input marker for turn {turn_number}")
        speech = input_payload.get("speech")
        action = input_payload.get("action")
        force_speaker = input_payload.get("force_speaker")
        if (
            not isinstance(speech, str)
            or not isinstance(action, str)
            or (force_speaker is not None and not isinstance(force_speaker, str))
        ):
            raise ReplaySessionError(f"Malformed input payload for turn {turn_number}")
        turns.append(
            RecordedTurn(
                turn_number=turn_number,
                speech=speech,
                action=action,
                force_speaker=force_speaker,
            )
        )
        seen_turns.add(turn_number)
    return turns


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Remove only per-run identifiers before deterministic state comparison."""
    normalized = copy.deepcopy(state)
    normalized.pop("session_id", None)
    normalized.pop("created_at", None)
    return normalized


def first_difference(expected: object, actual: object, path: str = "$") -> str | None:
    """Return the first structural difference between two JSON-compatible values."""
    if type(expected) is not type(actual):
        return f"{path}: expected type {type(expected).__name__}, got {type(actual).__name__}"
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        if expected_keys != actual_keys:
            return (
                f"{path}: missing keys {sorted(expected_keys - actual_keys)}, "
                f"extra keys {sorted(actual_keys - expected_keys)}"
            )
        for key in expected:
            difference = first_difference(expected[key], actual[key], f"{path}.{key}")
            if difference is not None:
                return difference
        return None
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return f"{path}: expected {len(expected)} items, got {len(actual)}"
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=True)):
            difference = first_difference(expected_item, actual_item, f"{path}[{index}]")
            if difference is not None:
                return difference
        return None
    if expected != actual:
        return f"{path}: expected {expected!r}, got {actual!r}"
    return None


async def _request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> Any:
    response = await client.request(method, path, json=payload)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ReplaySessionError(
            f"{method} {path} returned {response.status_code}: {response.text}"
        ) from exc
    return response.json()


async def replay_and_compare(
    *,
    app_url: str,
    replay_url: str,
    preset: str,
    turns: list[RecordedTurn],
    source_records: list[dict[str, Any]],
    source_backup: dict[str, Any] | None = None,
    source_final: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Drive all recorded turns, compact, and compare both states and output sequences."""
    async with (
        httpx.AsyncClient(base_url=app_url, timeout=30.0) as app_client,
        httpx.AsyncClient(base_url=replay_url, timeout=10.0) as replay_client,
    ):
        await _request(replay_client, "POST", "/replay/reset")
        started = await _request(
            app_client,
            "POST",
            "/session/start",
            payload={"preset_name": preset, "controlled_character_id": "C1"},
        )
        if not isinstance(started, dict) or not isinstance(started.get("session_id"), str):
            raise ReplaySessionError("Session start response did not contain a session id")
        session_id = started["session_id"]

        for turn in turns:
            await _request(
                app_client,
                "POST",
                f"/session/{session_id}/turn",
                payload={
                    "speech": turn.speech,
                    "action": turn.action,
                    "force_speaker": turn.force_speaker,
                },
            )

        before_compaction = await _request(app_client, "GET", f"/session/{session_id}/state")
        if not isinstance(before_compaction, dict):
            raise ReplaySessionError("State endpoint did not return an object")
        before_difference = (
            first_difference(normalize_state(source_backup), normalize_state(before_compaction))
            if source_backup is not None
            else None
        )

        has_summarizer_output = any(
            output.get("agent") == "summarizer" for output in successful_outputs(source_records)
        )
        compact_result = (
            await _request(app_client, "POST", f"/session/{session_id}/compact")
            if has_summarizer_output
            else None
        )
        after_compaction = await _request(app_client, "GET", f"/session/{session_id}/state")
        new_records = await _request(app_client, "GET", f"/session/{session_id}/debug_log")
        replay_status = await _request(replay_client, "GET", "/replay/status")

    if not isinstance(after_compaction, dict) or not isinstance(new_records, list):
        raise ReplaySessionError("Final state or debug log has an unexpected response type")
    typed_new_records = [record for record in new_records if isinstance(record, dict)]
    after_difference = (
        first_difference(normalize_state(source_final), normalize_state(after_compaction))
        if source_final is not None
        else None
    )
    output_difference = first_difference(
        successful_outputs(source_records), successful_outputs(typed_new_records)
    )
    differences: dict[str, str | None] = {"outputs": output_difference}
    if source_backup is not None:
        differences["before_compaction"] = before_difference
    if source_final is not None:
        differences["after_compaction"] = after_difference
    return {
        "session_id": session_id,
        "turns_replayed": len(turns),
        "compact_result": compact_result,
        "replay_status": replay_status,
        "successful_outputs": len(successful_outputs(typed_new_records)),
        "matches": all(value is None for value in differences.values()),
        "differences": differences,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recreate a recorded Roleplay session through HTTP and compare artifacts."
    )
    parser.add_argument("source_log", type=Path, help="Original .debug.jsonl")
    parser.add_argument("--source-backup", type=Path, help="Optional pre-compaction session JSON")
    parser.add_argument("--source-final", type=Path, help="Optional expected final session JSON")
    parser.add_argument("--app-url", default="http://127.0.0.1:8889")
    parser.add_argument("--replay-url", default="http://127.0.0.1:8888")
    parser.add_argument("--preset", default="thorn-lyra")
    return parser.parse_args()


async def _async_main() -> int:
    args = _parse_args()
    source_records = load_debug_records(args.source_log)
    source_backup = load_json_object(args.source_backup) if args.source_backup else None
    turns = build_recorded_turns_from_turn_inputs(source_records)
    result = await replay_and_compare(
        app_url=args.app_url,
        replay_url=args.replay_url,
        preset=args.preset,
        turns=turns,
        source_records=source_records,
        source_backup=source_backup,
        source_final=load_json_object(args.source_final) if args.source_final else None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["matches"] else 1


def main() -> None:
    """Run the replay driver CLI."""
    raise SystemExit(asyncio.run(_async_main()))


if __name__ == "__main__":
    main()
