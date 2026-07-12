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
SUPPORTED_EVENTS = {"turn", "suggest", "compact", "restore_compaction", "undo"}
SECOND_PERSON_RE = re.compile(r"\b(?:you|your|yours|yourself)\b", re.IGNORECASE)
CHARACTER_ACTION_RE = re.compile(
    r"\b(?:I (?:say|whisper|mutter|stammer|blink|stumble|lean|peer|stare|glance|"
    r"grip|pull|raise|hold|step|turn)|my (?:eyes|hands?|fingers?|grip|heart|body|feet))\b",
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
            action = event.get("action", "")
            force_speaker = event.get("force_speaker")
            if not isinstance(speech, str) or not isinstance(action, str):
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} speech/action must be strings"
                )
            if not speech and not action:
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} needs speech or action"
                )
            if force_speaker is not None and not isinstance(force_speaker, str):
                raise PlaytestConfigurationError(
                    f"{path}: turn event {index} force_speaker must be a string or null"
                )
            event = {
                "type": "turn",
                "speech": speech,
                "action": action,
                "force_speaker": force_speaker,
            }
        events.append(event)

    return Scenario(
        name=name,
        description=description,
        narrator_directives=narrator_directives,
        events=tuple(events),
        source_path=str(path),
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
    if event_type == "turn":
        return await runner.player_turn(
            session_id,
            speech=event["speech"],
            action=event["action"],
            force_speaker=event["force_speaker"],
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
    joined_raw = "\n".join(raw_texts)
    return {
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
    session_id = runner.start_session(
        {"narrator_directives": scenario.narrator_directives}
        if scenario.narrator_directives
        else None
    )
    event_results: list[dict[str, Any]] = []
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
        event_results.append(
            {
                "index": index,
                "type": event["type"],
                "input": event,
                "before": before,
                "after": await _snapshot(runner, session_id),
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                "result": result,
            }
        )

    debug_path = sessions_dir / f"{session_id}.debug.jsonl"
    records = _load_debug_records(debug_path) if debug_path.exists() else []
    return {
        "scenario": scenario.name,
        "description": scenario.description,
        "source_path": scenario.source_path,
        "repetition": repetition,
        "session_id": session_id,
        "events": event_results,
        "final_state": await _snapshot(runner, session_id),
        "analysis": analyze_debug_records(records, event_results),
    }


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
        "Character-action hits | Second-person narration | Nested physical_facts |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in manifest["runs"]:
        if "error" in run:
            lines.append(
                f"| {run['scenario']} | {run['repetition']} | ERROR | "
                f"{run.get('queue', {}).get('wait_ms', 0)} | - | - | - | - | - | - |"
            )
            continue
        analysis = run["analysis"]
        lines.append(
            f"| {run['scenario']} | {run['repetition']} | `{run['session_id']}` | "
            f"{run['queue']['wait_ms']} | {analysis.get('llm_calls', '-')} | "
            f"{analysis.get('llm_errors', '-')} | {analysis.get('max_prompt_chars', '-')} | "
            f"{analysis.get('character_action_heuristic_hits', '-')} | "
            f"{analysis.get('second_person_narrations', '-')} | "
            f"{analysis.get('nested_physical_facts_outputs', '-')} |"
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
