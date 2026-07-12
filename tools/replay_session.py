"""Recreate a recorded Roleplay session through the real HTTP API and compare outputs."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import re
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
    force_speaker: str


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


def build_recorded_turns(
    source_state: dict[str, Any], records: list[dict[str, Any]]
) -> list[RecordedTurn]:
    """Recover exact player inputs and derive overrides that reproduce the LLM call sequence."""
    characters = source_state.get("characters")
    if not isinstance(characters, dict):
        raise ReplaySessionError("Source state has no character map")
    character_ids_by_name: dict[str, str] = {}
    for character_id, character in characters.items():
        if not isinstance(character_id, str) or not isinstance(character, dict):
            continue
        mind = character.get("mind")
        name = mind.get("name") if isinstance(mind, dict) else None
        if isinstance(name, str):
            character_ids_by_name[name] = character_id

    history = source_state.get("history")
    if not isinstance(history, list):
        raise ReplaySessionError("Source state has no history list")

    player_by_turn: dict[int, dict[str, str]] = {}
    for item in history:
        if not isinstance(item, dict) or item.get("speaker") != "Player":
            continue
        turn_number = item.get("turn_number")
        content_type = item.get("content_type")
        content = item.get("content")
        if (
            isinstance(turn_number, int)
            and content_type in {"speech", "action"}
            and isinstance(content, str)
        ):
            player_by_turn.setdefault(turn_number, {})[content_type] = content

    successful_by_turn: dict[int, list[str]] = {}
    for output in successful_outputs(records):
        turn_number = output.get("turn_number")
        agent = output.get("agent")
        if isinstance(turn_number, int) and isinstance(agent, str):
            successful_by_turn.setdefault(turn_number, []).append(agent)

    turns: list[RecordedTurn] = []
    for turn_number in sorted(player_by_turn):
        agents = successful_by_turn.get(turn_number, [])
        if agents.count("narrator") != 1:
            raise ReplaySessionError(
                f"Turn {turn_number} needs exactly one successful narrator output, got {agents}"
            )
        character_agents = [agent for agent in agents if agent.startswith("character:")]
        if len(character_agents) > 1:
            raise ReplaySessionError(
                f"Turn {turn_number} has more than one character output: {character_agents}"
            )
        if character_agents:
            character_name = character_agents[0].removeprefix("character:")
            force_speaker = character_ids_by_name.get(character_name, "")
            if not force_speaker:
                raise ReplaySessionError(
                    f"Cannot map recorded character {character_name!r} to a character id"
                )
        else:
            force_speaker = "Narrator"

        player = player_by_turn[turn_number]
        turns.append(
            RecordedTurn(
                turn_number=turn_number,
                speech=player.get("speech", ""),
                action=player.get("action", ""),
                force_speaker=force_speaker,
            )
        )
    return turns


def build_recorded_turns_from_narrator_history(
    records: list[dict[str, Any]],
    *,
    controlled_name: str,
    character_ids_by_name: dict[str, str],
) -> list[RecordedTurn]:
    """Recover two-field player turns from the latest full Narrator HISTORY in a raw log."""
    narrator_records = [
        record
        for record in records
        if record.get("agent") == "narrator"
        and isinstance(record.get("response"), str)
        and isinstance(record.get("turn_number"), int)
    ]
    if not narrator_records:
        raise ReplaySessionError("Debug log contains no successful Narrator request")
    latest = max(narrator_records, key=lambda record: int(record["turn_number"]))
    request = latest.get("request")
    messages = request.get("messages") if isinstance(request, dict) else None
    if not isinstance(messages, list):
        raise ReplaySessionError("Latest Narrator record has no request messages")
    user_content = next(
        (
            message.get("content")
            for message in reversed(messages)
            if isinstance(message, dict)
            and message.get("role") == "user"
            and isinstance(message.get("content"), str)
        ),
        None,
    )
    if not isinstance(user_content, str) or "HISTORY:\n" not in user_content:
        raise ReplaySessionError("Latest Narrator request has no parseable HISTORY section")

    history_text = user_content.split("HISTORY:\n", maxsplit=1)[1]
    pattern = re.compile(r"^  Turn (\d+) — ([^:]+): (.*)$")
    player_content: dict[int, list[str]] = {}
    for line in history_text.splitlines():
        match = pattern.match(line)
        if match is None or match.group(2) != controlled_name:
            continue
        turn_number = int(match.group(1))
        player_content.setdefault(turn_number, []).append(match.group(3))

    if not player_content:
        raise ReplaySessionError(
            f"No history records found for controlled character {controlled_name!r}"
        )
    synthetic_history: list[dict[str, Any]] = []
    for turn_number, contents in sorted(player_content.items()):
        if len(contents) != 2:
            raise ReplaySessionError(
                f"Turn {turn_number} has {len(contents)} controlled-character records; "
                "raw prompt recovery requires exactly speech plus action"
            )
        synthetic_history.extend(
            [
                {
                    "turn_number": turn_number,
                    "speaker": "Player",
                    "content_type": "speech",
                    "content": contents[0],
                },
                {
                    "turn_number": turn_number,
                    "speaker": "Player",
                    "content_type": "action",
                    "content": contents[1],
                },
            ]
        )

    characters = {
        character_id: {"mind": {"name": character_name}}
        for character_name, character_id in character_ids_by_name.items()
    }
    characters.setdefault("C1", {"mind": {"name": controlled_name}})
    return build_recorded_turns(
        {"characters": characters, "history": synthetic_history}, records
    )


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

        before_compaction = await _request(
            app_client, "GET", f"/session/{session_id}/state"
        )
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
        after_compaction = await _request(
            app_client, "GET", f"/session/{session_id}/state"
        )
        new_records = await _request(
            app_client, "GET", f"/session/{session_id}/debug_log"
        )
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
    parser.add_argument("--controlled-name", default="Thorn")
    parser.add_argument(
        "--character-map",
        action="append",
        default=["Lyra=C2"],
        metavar="NAME=ID",
        help="Map a recorded Character name to its preset id; may be repeated.",
    )
    return parser.parse_args()


def _parse_character_map(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        name, separator, character_id = value.partition("=")
        if not separator or not name or not character_id:
            raise ReplaySessionError(f"Invalid character map {value!r}; expected NAME=ID")
        result[name] = character_id
    return result


async def _async_main() -> int:
    args = _parse_args()
    source_records = load_debug_records(args.source_log)
    source_backup = load_json_object(args.source_backup) if args.source_backup else None
    turns = (
        build_recorded_turns(source_backup, source_records)
        if source_backup is not None
        else build_recorded_turns_from_narrator_history(
            source_records,
            controlled_name=args.controlled_name,
            character_ids_by_name=_parse_character_map(args.character_map),
        )
    )
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
