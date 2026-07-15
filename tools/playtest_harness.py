"""Run repeatable queued playtest suites against a live OpenAI-compatible LLM."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REAL_DATA_DIR = (REPOSITORY_ROOT / ".data").resolve()
DEFAULT_SCENARIO_DIR = Path(__file__).resolve().parent / "playtests"
SUPPORTED_EVENTS = {"turn", "suggest", "compact", "restore_compaction", "undo", "recall_check"}
RECALL_PATTERN_FIELDS = (
    "prompt_patterns",
    "prompt_forbidden_patterns",
    "reply_patterns",
    "reply_forbidden_patterns",
)
SECOND_PERSON_RE = re.compile(r"\b(?:you|your|yours|yourself)\b", re.IGNORECASE)
CHARACTER_ACTION_RE = re.compile(
    r"\b(?:(?:I |eu )?(?:blink|stumble|lean|peer|stare|glance|grip|pull|raise|"
    r"hold|step|turn|arrumo|inclino|ergo|abaixo|toco|seguro|agarro|puxo|empurro|"
    r"levanto|ando|caminho|olho|encaro|viro|sorrio|pisco|tamborilo)|"
    r"(?:my |meus? |minhas? )(?:eyes|hands?|fingers?|grip|heart|body|feet|"
    r"olhos?|mãos?|dedos?|corpo|pés?))\b",
    re.IGNORECASE,
)


class PlaytestConfigurationError(ValueError):
    """Raised when a scenario or CLI setting cannot be executed safely."""


@dataclass(frozen=True, slots=True)
class Scenario:
    """One ordered conversation/operation sequence."""

    name: str
    description: str
    narrator_directives: str
    events: tuple[dict[str, Any], ...]
    source_path: str
    session_config: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class QueueTiming:
    """Timing for one job waiting for and holding a global harness slot."""

    queued_at: str
    wait_ms: float
    duration_ms: float


class ScenarioQueue:
    """Bound concurrent scenarios so HTTP timeouts do not become the implicit queue."""

    def __init__(self, max_in_flight: int) -> None:
        if max_in_flight < 1:
            raise PlaytestConfigurationError("max_in_flight must be at least 1")
        self._semaphore = asyncio.Semaphore(max_in_flight)

    async def run(self, operation: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
        queued_at = datetime.now(UTC).isoformat()
        queued = time.perf_counter()
        async with self._semaphore:
            started = time.perf_counter()
            result = await operation()
            finished = time.perf_counter()
        result["queue"] = asdict(
            QueueTiming(
                queued_at=queued_at,
                wait_ms=round((started - queued) * 1000, 3),
                duration_ms=round((finished - started) * 1000, 3),
            )
        )
        return result


def _require_string(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise PlaytestConfigurationError(f"{label} must be a string")
    return value


def _validated_audience(raw_event: dict[str, Any], label: str) -> list[str] | None:
    audience = raw_event.get("audience")
    if audience is None:
        return None
    if (
        not isinstance(audience, list)
        or not audience
        or not all(isinstance(cid, str) and cid for cid in audience)
    ):
        raise PlaytestConfigurationError(
            f"{label} audience must be a non-empty array of character IDs"
        )
    return list(audience)


def load_scenario(path: Path) -> Scenario:
    """Load and validate one scenario JSON file."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlaytestConfigurationError(f"Cannot load scenario {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlaytestConfigurationError(f"Scenario {path} must contain one JSON object")

    name = _require_string(value.get("name"), f"{path}: name")
    description = _require_string(value.get("description", ""), f"{path}: description")
    narrator_directives = _require_string(
        value.get("narrator_directives", ""),
        f"{path}: narrator_directives",
        allow_empty=True,
    )
    raw_session_config = value.get("session_config")
    if raw_session_config is not None and not isinstance(raw_session_config, dict):
        raise PlaytestConfigurationError(f"{path}: session_config must be an object")
    raw_events = value.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise PlaytestConfigurationError(f"{path}: events must be a non-empty array")

    events: list[dict[str, Any]] = []
    for index, raw_event in enumerate(raw_events, start=1):
        if not isinstance(raw_event, dict):
            raise PlaytestConfigurationError(f"{path}: event {index} must be an object")
        event_type = raw_event.get("type")
        if event_type not in SUPPORTED_EVENTS:
            raise PlaytestConfigurationError(
                f"{path}: event {index} has unsupported type {event_type!r}"
            )
        event = dict(raw_event)
        if event_type == "turn":
            speech = event.get("speech", "")
            thought = event.get("thought", "")
            action = event.get("action", "")
            force_speaker = event.get("force_speaker")
            if not all(isinstance(value, str) for value in (speech, thought, action)):
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} speech/thought/action must be strings"
                )
            if not speech and not thought and not action:
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} needs speech, thought, or action"
                )
            if force_speaker is not None and not isinstance(force_speaker, str):
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} force_speaker must be a string or null"
                )
            event = {
                "type": "turn",
                "speech": speech,
                "thought": thought,
                "action": action,
                "force_speaker": force_speaker,
                "audience": _validated_audience(raw_event, f"{path}: turn event {index}"),
            }
        elif event_type == "recall_check":
            speech = _require_string(event.get("speech"), f"{path}: recall_check {index} speech")
            force_speaker = _require_string(
                event.get("force_speaker"), f"{path}: recall_check {index} force_speaker"
            )
            patterns: dict[str, list[str]] = {}
            for field_name in RECALL_PATTERN_FIELDS:
                raw_patterns = event.get(field_name, [])
                if not isinstance(raw_patterns, list) or not all(
                    isinstance(pattern, str) and pattern for pattern in raw_patterns
                ):
                    raise PlaytestConfigurationError(
                        f"{path}: recall_check {index} {field_name} must be an array of "
                        "non-empty strings"
                    )
                for pattern in raw_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        raise PlaytestConfigurationError(
                            f"{path}: recall_check {index} has invalid regex {pattern!r}: {exc}"
                        ) from exc
                patterns[field_name] = list(raw_patterns)
            if not any(patterns.values()):
                raise PlaytestConfigurationError(
                    f"{path}: recall_check {index} needs at least one pattern"
                )
            required = event.get("required", True)
            if not isinstance(required, bool):
                raise PlaytestConfigurationError(
                    f"{path}: recall_check {index} required must be a boolean"
                )
            event = {
                "type": "recall_check",
                "speech": speech,
                "thought": "",
                "action": "",
                "force_speaker": force_speaker,
                "required": required,
                "audience": _validated_audience(raw_event, f"{path}: recall_check {index}"),
                **patterns,
            }
        events.append(event)

    return Scenario(
        name=name,
        description=description,
        narrator_directives=narrator_directives,
        events=tuple(events),
        source_path=str(path),
        session_config=raw_session_config,
    )


def assert_safe_output_dir(output_dir: Path) -> None:
    """Keep harness runs away from the repository's real persistent data."""
    resolved = output_dir.resolve()
    if resolved == REAL_DATA_DIR or REAL_DATA_DIR in resolved.parents:
        raise PlaytestConfigurationError(f"Refusing to use real data directory: {resolved}")


def prepare_output_dir(output_dir: Path | None) -> Path:
    """Create a fresh isolated runtime directory; built-ins remain source assets."""
    if output_dir is None:
        run_dir = Path(tempfile.mkdtemp(prefix="roleplay-playtest-suite-"))
    else:
        run_dir = output_dir.expanduser().resolve()
        assert_safe_output_dir(run_dir)
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise PlaytestConfigurationError(f"Output directory already exists: {run_dir}") from exc
    assert_safe_output_dir(run_dir)
    return run_dir


def build_session_config(scenario: Scenario) -> dict[str, Any] | None:
    """Convert the scenario's raw session_config into Runner.start_session input."""
    session_config: dict[str, Any] = {}
    if scenario.narrator_directives:
        session_config["narrator_directives"] = scenario.narrator_directives
    raw = scenario.session_config or {}
    if "characters" in raw:
        from src.models import dict_to_character

        characters = raw["characters"]
        if not isinstance(characters, dict) or not characters:
            raise PlaytestConfigurationError(
                f"{scenario.source_path}: session_config.characters must be a non-empty object"
            )
        session_config["characters"] = {
            character_id: dict_to_character(data) for character_id, data in characters.items()
        }
    if "scene" in raw:
        from src.models import Scene

        scene_data = raw["scene"]
        if not isinstance(scene_data, dict):
            raise PlaytestConfigurationError(
                f"{scenario.source_path}: session_config.scene must be an object"
            )
        session_config["scene"] = Scene(
            location=scene_data["location"],
            time_of_day=scene_data["time_of_day"],
            present_characters=list(scene_data.get("present_characters", [])),
            physical_facts=dict(scene_data.get("physical_facts", {})),
        )
    if "controlled_character_id" in raw:
        session_config["controlled_character_id"] = raw["controlled_character_id"]
    return session_config or None


def evaluate_recall_check(
    event: dict[str, Any], turn_number: int, debug_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Match the recall patterns against what the character actually saw and answered.

    Prompt-level matches localize a loss before the provider (state/selection/prompt);
    reply-level matches localize it at the provider/model. A turn without any character
    call never passes — a routing failure must not read as successful recall.
    """
    character_records = [
        record
        for record in debug_records
        if record.get("turn_number") == turn_number
        and str(record.get("agent", "")).startswith("character:")
        and isinstance(record.get("request"), dict)
    ]
    prompt_text = "\n".join(
        str(message.get("content", ""))
        for record in character_records
        for message in record["request"].get("messages", [])
        if isinstance(message, dict)
    )
    reply_parts: list[str] = []
    for record in character_records:
        response = record.get("response")
        if not isinstance(response, str):
            continue
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            reply_parts.append(response)
            continue
        if isinstance(parsed, dict):
            reply_parts.extend(
                value
                for value in (parsed.get("speech"), parsed.get("thought"))
                if isinstance(value, str)
            )
        else:
            reply_parts.append(response)
    reply_text = "\n".join(reply_parts)

    prompt_matches = {
        pattern: bool(re.search(pattern, prompt_text))
        for pattern in event.get("prompt_patterns", [])
    }
    prompt_forbidden_hits = {
        pattern: bool(re.search(pattern, prompt_text))
        for pattern in event.get("prompt_forbidden_patterns", [])
    }
    reply_matches = {
        pattern: bool(re.search(pattern, reply_text)) for pattern in event.get("reply_patterns", [])
    }
    reply_forbidden_hits = {
        pattern: bool(re.search(pattern, reply_text))
        for pattern in event.get("reply_forbidden_patterns", [])
    }
    prompt_passed = all(prompt_matches.values()) and not any(prompt_forbidden_hits.values())
    reply_passed = all(reply_matches.values()) and not any(reply_forbidden_hits.values())
    return {
        "character_calls": len(character_records),
        "prompt_matches": prompt_matches,
        "prompt_forbidden_hits": prompt_forbidden_hits,
        "reply_matches": reply_matches,
        "reply_forbidden_hits": reply_forbidden_hits,
        "prompt_passed": prompt_passed,
        "reply_passed": reply_passed,
        "passed": bool(character_records) and prompt_passed and reply_passed,
    }


def whisper_leak_records(game: Any) -> list[dict[str, Any]]:
    """Character speech/action records that expose whispered-secret tokens.

    Deterministic invariant behind the Character output guard: after the guard,
    no character-produced record whose audience does not cover a whispered secret
    may contain that secret's rare tokens. Player-typed records are exempt — the
    player may spend their own secret aloud on purpose.
    """
    from src.confidentiality import secret_tokens_exposed_to, tokens

    leaks: list[dict[str, Any]] = []
    for index, record in enumerate(game.history):
        if record.speaker not in game.characters:
            continue
        if record.content_type not in ("speech", "action"):
            continue
        snapshot = record.scene_snapshot
        if record.audience is not None:
            exposed = set(record.audience)
        else:
            exposed = {cid for cid in snapshot.present_characters if cid in game.characters}
        exposed -= {record.speaker}
        if not exposed:
            continue
        secret = secret_tokens_exposed_to(
            game.history[:index],
            record.speaker,
            exposed,
            game.characters,
            snapshot,
            controlled_id=game.player.controlled_character_id,
        )
        leaked = secret & tokens(record.content)
        if leaked:
            leaks.append(
                {
                    "turn_number": record.turn_number,
                    "speaker": record.speaker,
                    "content_type": record.content_type,
                    "leaked_tokens": sorted(leaked),
                }
            )
    return leaks


def session_invariants(game: Any) -> list[str]:
    """Prove no compaction, presence edit, or mid-session participant change happened."""
    violations: list[str] = []
    if game.compaction_stack:
        violations.append("compaction_stack is not empty: a compaction happened")
    if game.story_summary:
        violations.append("story_summary is not empty: a compaction happened")
    if game.presence_edit_stack:
        violations.append("presence_edit_stack is not empty: an out-of-band presence edit happened")
    snapshot_presences = {
        tuple(record.scene_snapshot.present_characters) for record in game.history
    }
    if len(snapshot_presences) > 1:
        violations.append(
            f"present_characters changed during the session: {sorted(snapshot_presences)}"
        )
    if snapshot_presences and snapshot_presences != {tuple(game.scene.present_characters)}:
        violations.append("final present_characters differs from the history snapshots")
    return violations


async def _snapshot(runner: Any, session_id: str) -> dict[str, Any]:
    game = await runner.get_state(session_id)
    if game is None:
        raise RuntimeError(f"Session disappeared during playtest: {session_id}")
    return {
        "location": game.scene.location,
        "time_of_day": game.scene.time_of_day,
        "physical_facts": dict(game.scene.physical_facts),
        "moods": {cid: character.mind.current_mood for cid, character in game.characters.items()},
        "history_records": len(game.history),
        "history_turns": sorted({record.turn_number for record in game.history}),
        "story_summary": game.story_summary,
        "character_notes": dict(game.character_notes),
    }


async def _run_event(runner: Any, session_id: str, event: dict[str, Any]) -> Any:
    event_type = event["type"]
    if event_type in ("turn", "recall_check"):
        return await runner.player_turn(
            session_id,
            speech=event["speech"],
            thought=event["thought"],
            action=event["action"],
            force_speaker=event["force_speaker"],
            audience=event.get("audience"),
        )
    if event_type == "suggest":
        return await runner.suggest_actions(session_id)
    if event_type == "compact":
        return await runner.compact_session(session_id)
    if event_type == "restore_compaction":
        return await runner.restore_last_compaction(session_id)
    if event_type == "undo":
        return await runner.undo_turn(session_id)
    raise AssertionError(f"Unhandled event type: {event_type}")


def _load_debug_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"Expected object on line {line_number} of {path}")
        records.append(value)
    return records


def _exact_sentence_duplicates(texts: list[str]) -> int:
    seen: set[str] = set()
    duplicates = 0
    for text in texts:
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
            normalized = re.sub(r"\s+", " ", sentence.strip().lower())
            if len(normalized) < 20:
                continue
            if normalized in seen:
                duplicates += 1
            else:
                seen.add(normalized)
    return duplicates


def analyze_debug_records(
    records: list[dict[str, Any]], event_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Calculate deterministic signals without asking another model to judge prose."""
    calls = [record for record in records if isinstance(record.get("request"), dict)]
    prompts = "\n".join(
        str(message.get("content", ""))
        for record in calls
        for message in record["request"].get("messages", [])
        if isinstance(message, dict)
    )
    successful = [
        record
        for record in calls
        if record.get("error") is None and isinstance(record.get("response"), str)
    ]
    narrator_outputs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    character_texts: list[str] = []
    raw_texts: list[str] = []
    for record in successful:
        response = str(record["response"])
        raw_texts.append(response)
        if record.get("agent") == "narrator":
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                narrator_outputs.append((record, parsed))
        elif str(record.get("agent", "")).startswith("character:"):
            character_texts.append(response)

    before_moods: dict[int, dict[str, str]] = {}
    for event_result in event_results:
        if event_result.get("type") != "turn":
            continue
        result = event_result.get("result")
        before = event_result.get("before")
        if isinstance(result, dict) and isinstance(result.get("turn_number"), int):
            moods = before.get("moods") if isinstance(before, dict) else None
            if isinstance(moods, dict):
                before_moods[result["turn_number"]] = {
                    key: value
                    for key, value in moods.items()
                    if isinstance(key, str) and isinstance(value, str)
                }

    redundant_mood_updates = 0
    nested_physical_facts = 0
    second_person_narrations = 0
    narration_texts: list[str] = []
    for record, output in narrator_outputs:
        narration = output.get("narration")
        if isinstance(narration, str):
            narration_texts.append(narration)
            second_person_narrations += bool(SECOND_PERSON_RE.search(narration))
        scene_update = output.get("scene_update")
        if isinstance(scene_update, dict) and "physical_facts" in scene_update:
            nested_physical_facts += 1
        mood_updates = output.get("mood_updates")
        turn_number = record.get("turn_number")
        previous = before_moods.get(turn_number, {}) if isinstance(turn_number, int) else {}
        if isinstance(mood_updates, dict):
            redundant_mood_updates += sum(
                previous.get(character_id) == mood
                for character_id, mood in mood_updates.items()
                if isinstance(character_id, str) and isinstance(mood, str)
            )

    durations = [
        float(record["duration_ms"])
        for record in calls
        if isinstance(record.get("duration_ms"), (int, float))
    ]
    prompt_sizes = [
        int(record["prompt_chars"])
        for record in calls
        if isinstance(record.get("prompt_chars"), int)
    ]
    recall_results = [
        event_result["recall"]
        for event_result in event_results
        if isinstance(event_result.get("recall"), dict)
    ]
    guard_events = [record for record in records if record.get("agent") == "whisper_output_guard"]
    joined_raw = "\n".join(raw_texts)
    return {
        "whisper_guard_retries": sum(event.get("outcome") == "retried" for event in guard_events),
        "whisper_guard_redactions": sum(
            event.get("outcome") == "redacted" for event in guard_events
        ),
        "recall_checks": len(recall_results),
        "recall_failures": sum(not recall["passed"] for recall in recall_results),
        "recall_prompt_failures": sum(not recall["prompt_passed"] for recall in recall_results),
        "recall_reply_failures": sum(not recall["reply_passed"] for recall in recall_results),
        "llm_calls": len(calls),
        "llm_errors": sum(record.get("error") is not None for record in calls),
        "retry_attempts": sum(
            isinstance(record.get("attempt_number"), int) and record["attempt_number"] > 1
            for record in calls
        ),
        "max_prompt_chars": max(prompt_sizes, default=0),
        "max_duration_ms": round(max(durations, default=0.0), 3),
        "mean_duration_ms": round(statistics.mean(durations), 3) if durations else 0.0,
        "player_prompt_occurrences": prompts.count("Player"),
        "nested_physical_facts_outputs": nested_physical_facts,
        "second_person_narrations": second_person_narrations,
        "narrator_outputs": len(narrator_outputs),
        "character_outputs": len(character_texts),
        "character_action_heuristic_hits": sum(
            bool(CHARACTER_ACTION_RE.search(text)) for text in character_texts
        ),
        "redundant_mood_updates": redundant_mood_updates,
        "exact_narration_sentence_duplicates": _exact_sentence_duplicates(narration_texts),
        "exact_character_sentence_duplicates": _exact_sentence_duplicates(character_texts),
        "raw_em_dash_count": joined_raw.count("—"),
        "raw_en_dash_count": joined_raw.count("–"),
    }


async def run_scenario(
    runner: Any,
    scenario: Scenario,
    repetition: int,
    sessions_dir: Path,
) -> dict[str, Any]:
    """Execute one scenario sequentially inside its own real session."""
    session_id = runner.start_session(build_session_config(scenario))
    debug_path = sessions_dir / session_id / "debug.jsonl"
    event_results: list[dict[str, Any]] = []
    recall_failures: list[str] = []
    for index, event in enumerate(scenario.events, start=1):
        before = await _snapshot(runner, session_id)
        started = time.perf_counter()
        try:
            result = await _run_event(runner, session_id, event)
        except Exception as exc:
            event_results.append(
                {
                    "index": index,
                    "type": event["type"],
                    "input": event,
                    "before": before,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            raise
        event_result = {
            "index": index,
            "type": event["type"],
            "input": event,
            "before": before,
            "after": await _snapshot(runner, session_id),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "result": result,
        }
        if event["type"] == "recall_check":
            turn_number = result.get("turn_number") if isinstance(result, dict) else None
            if not isinstance(turn_number, int):
                raise RuntimeError("Recall check result is missing an integer turn_number")
            records = _load_debug_records(debug_path) if debug_path.exists() else []
            recall = evaluate_recall_check(event, turn_number, records)
            event_result["recall"] = recall
            if event["required"] and not recall["passed"]:
                recall_failures.append(f"event {index}: {event['speech'][:60]!r}")
        event_results.append(event_result)

    records = _load_debug_records(debug_path) if debug_path.exists() else []
    run_result = {
        "scenario": scenario.name,
        "description": scenario.description,
        "source_path": scenario.source_path,
        "repetition": repetition,
        "session_id": session_id,
        "events": event_results,
        "final_state": await _snapshot(runner, session_id),
        "analysis": analyze_debug_records(records, event_results),
    }
    has_recall_checks = any(event["type"] == "recall_check" for event in scenario.events)
    if has_recall_checks:
        game = await runner.get_state(session_id)
        if game is None:
            raise RuntimeError(f"Session disappeared during playtest: {session_id}")
        violations = session_invariants(game)
        run_result["invariant_violations"] = violations
        leaks = whisper_leak_records(game)
        run_result["whisper_leak_records"] = leaks
        failures: list[str] = []
        if recall_failures:
            failures.append(f"required recall checks failed: {'; '.join(recall_failures)}")
        if violations:
            failures.append(f"session invariants violated: {'; '.join(violations)}")
        if leaks:
            summary = "; ".join(
                f"turn {leak['turn_number']} {leak['speaker']}: {leak['leaked_tokens']}"
                for leak in leaks
            )
            failures.append(f"whispered secrets leaked into records: {summary}")
        if failures:
            # Keep the completed result (events, recall matrices, analysis) in the
            # manifest while still failing the run and the process exit code.
            run_result["error"] = f"RecallCheckFailed: {' | '.join(failures)}"
    return run_result


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate numeric analysis fields per scenario without hiding individual runs."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        if "analysis" in run:
            grouped.setdefault(str(run["scenario"]), []).append(run["analysis"])
    aggregates: list[dict[str, Any]] = []
    for scenario, analyses in sorted(grouped.items()):
        numeric_keys = sorted(
            set.intersection(
                *(
                    {key for key, value in analysis.items() if isinstance(value, (int, float))}
                    for analysis in analyses
                )
            )
        )
        metrics = {
            key: {
                "min": min(float(analysis[key]) for analysis in analyses),
                "mean": round(statistics.mean(float(analysis[key]) for analysis in analyses), 3),
                "max": max(float(analysis[key]) for analysis in analyses),
            }
            for key in numeric_keys
        }
        aggregates.append({"scenario": scenario, "runs": len(analyses), "metrics": metrics})
    return aggregates


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def build_markdown_report(manifest: dict[str, Any]) -> str:
    """Render a compact human-readable comparison next to the full JSON artifact."""
    lines = [
        "# Automated playtest suite",
        "",
        f"- Started: `{manifest['started_at']}`",
        f"- Model label: `{manifest['model_label']}`",
        f"- Provider: `{manifest.get('provider', 'llama_cpp')}`",
        f"- LLM host: `{manifest['llm_host']}`",
        f"- Repetitions: `{manifest['repeat']}`",
        f"- Maximum scenarios in flight: `{manifest['max_in_flight']}`",
        f"- Data directory: `{manifest['data_dir']}`",
        "",
        "## Runs",
        "",
        "| Scenario | Repeat | Session | Queue wait ms | Calls | Errors | Max prompt | "
        "Character-action hits | Second-person narration | Nested physical_facts | "
        "Recall fails |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in manifest["runs"]:
        if "analysis" not in run:
            lines.append(
                f"| {run['scenario']} | {run['repetition']} | ERROR | "
                f"{run.get('queue', {}).get('wait_ms', 0)} | - | - | - | - | - | - | - |"
            )
            continue
        analysis = run["analysis"]
        session_cell = f"`{run['session_id']}`" + (" (FAILED)" if "error" in run else "")
        lines.append(
            f"| {run['scenario']} | {run['repetition']} | {session_cell} | "
            f"{run['queue']['wait_ms']} | {analysis.get('llm_calls', '-')} | "
            f"{analysis.get('llm_errors', '-')} | {analysis.get('max_prompt_chars', '-')} | "
            f"{analysis.get('character_action_heuristic_hits', '-')} | "
            f"{analysis.get('second_person_narrations', '-')} | "
            f"{analysis.get('nested_physical_facts_outputs', '-')} | "
            f"{analysis.get('recall_failures', '-')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundaries",
            "",
            "- Queue timing measures harness scheduling, while call duration comes from the raw "
            "LLM log.",
            "- Character-action and second-person counts are deterministic regex signals, not "
            "semantic judgments.",
            "- A model comparison is meaningful only when scenario files, server settings, and "
            "repeat count are identical.",
            "- Schema/state anomalies are system findings even if their frequency varies by model.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run queued, repeatable Roleplay playtest scenarios against a live LLM."
    )
    parser.add_argument("scenarios", nargs="*", type=Path)
    parser.add_argument("--llm-host", default="http://127.0.0.1:8888")
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Use one canonical server config (including its selected provider and API key).",
    )
    parser.add_argument("--provider", choices=("llama_cpp", "deepseek"))
    parser.add_argument("--model-label", default="unspecified")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--max-in-flight", type=int, default=1)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--language", default="English")
    parser.add_argument("--context-max", type=int, default=65536)
    parser.add_argument("--llm-timeout", type=float, default=60.0)
    return parser.parse_args(argv)


async def _async_main(args: argparse.Namespace) -> int:
    if args.repeat < 1:
        raise PlaytestConfigurationError("repeat must be at least 1")
    scenario_paths = args.scenarios or sorted(DEFAULT_SCENARIO_DIR.glob("*.json"))
    if not scenario_paths:
        raise PlaytestConfigurationError("No scenario files were provided or discovered")
    scenarios = [load_scenario(path) for path in scenario_paths]
    run_dir = prepare_output_dir(args.output_dir)
    os.environ["ROLEPLAY_DATA_DIR"] = str(run_dir)
    sys.path.insert(0, str(REPOSITORY_ROOT))

    from src.config import load_config, resolve_active_config
    from src.runner import Runner

    if args.config_file is not None:
        stored_config = load_config(args.config_file.expanduser().resolve())
        if args.provider is not None:
            stored_config = deepcopy(stored_config)
            stored_config["active_provider"] = args.provider
        config = resolve_active_config(stored_config)
    else:
        provider = args.provider or "llama_cpp"
        if provider != "llama_cpp":
            raise PlaytestConfigurationError("DeepSeek playtests require --config-file for the key")
        api_base = args.llm_host.rstrip("/")
        if not api_base.endswith("/v1"):
            api_base += "/v1"
        config = {
            "provider": "llama_cpp",
            "api_base": api_base,
            "model": "",
        }
    config.update(
        {
            "language": args.language,
            "context_max": args.context_max,
            "max_tokens_narrator": 1024,
            "max_tokens_character": 512,
            "summarizer_max_tokens": 1536,
            "compaction_keep_recent_turns": 8,
            "llm_timeout_seconds": args.llm_timeout,
        }
    )
    started_at = datetime.now(UTC).isoformat()
    queue = ScenarioQueue(args.max_in_flight)
    jobs = [
        (scenario, repetition) for repetition in range(1, args.repeat + 1) for scenario in scenarios
    ]

    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)

        async def execute(scenario: Scenario, repetition: int) -> dict[str, Any]:
            try:
                return await queue.run(
                    lambda: run_scenario(runner, scenario, repetition, run_dir / "sessions")
                )
            except Exception as exc:
                return {
                    "scenario": scenario.name,
                    "repetition": repetition,
                    "error": f"{type(exc).__name__}: {exc}",
                }

        runs = await asyncio.gather(
            *(execute(scenario, repetition) for scenario, repetition in jobs)
        )

    manifest = {
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "model_label": args.model_label,
        "llm_host": config["api_base"],
        "provider": config["provider"],
        "repeat": args.repeat,
        "max_in_flight": args.max_in_flight,
        "data_dir": str(run_dir),
        "scenario_files": [str(path) for path in scenario_paths],
        "runs": runs,
        "aggregates": aggregate_runs(runs),
    }
    results_path = run_dir / "playtest-results.json"
    report_path = run_dir / "playtest-report.md"
    _atomic_write_text(results_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    _atomic_write_text(report_path, build_markdown_report(manifest))
    print(
        json.dumps(
            {
                "data_dir": str(run_dir),
                "results": str(results_path),
                "report": str(report_path),
                "runs": len(runs),
                "failed_runs": sum("error" in run for run in runs),
            },
            indent=2,
        )
    )
    return 1 if any("error" in run for run in runs) else 0


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint."""
    args = _parse_args(argv)
    raise SystemExit(asyncio.run(_async_main(args)))


if __name__ == "__main__":
    main()
