"""Tests for the queued, repeatable live-playtest harness."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tools.playtest_harness import (
    PlaytestConfigurationError,
    ScenarioQueue,
    aggregate_runs,
    analyze_debug_records,
    assert_safe_output_dir,
    build_markdown_report,
    load_scenario,
    prepare_output_dir,
)


def _write_scenario(path: Path, events: list[dict] | None = None) -> Path:
    value = {
        "name": "test-scenario",
        "description": "A test scenario.",
        "narrator_directives": "",
        "events": events
        or [
            {
                "type": "turn",
                "speech": "Hello",
                "action": "",
                "force_speaker": "C2",
            }
        ],
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_scenario_load_round_trip_and_supported_operations(tmp_path: Path) -> None:
    path = _write_scenario(
        tmp_path / "scenario.json",
        [
            {"type": "turn", "speech": "Speak", "action": "Act", "force_speaker": None},
            {"type": "suggest"},
            {"type": "compact"},
            {"type": "restore_compaction"},
            {"type": "undo"},
        ],
    )

    scenario = load_scenario(path)

    assert scenario.name == "test-scenario"
    assert [event["type"] for event in scenario.events] == [
        "turn",
        "suggest",
        "compact",
        "restore_compaction",
        "undo",
    ]
    assert scenario.events[0]["force_speaker"] is None


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"name": "x", "description": "x", "events": []},
        {"name": "x", "description": "x", "events": [{"type": "unknown"}]},
        {
            "name": "x",
            "description": "x",
            "events": [{"type": "turn", "speech": "", "action": ""}],
        },
    ],
)
def test_scenario_validation_rejects_invalid_inputs(tmp_path: Path, value: dict) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(PlaytestConfigurationError):
        load_scenario(path)


def test_output_directory_is_fresh_and_isolated(tmp_path: Path) -> None:
    output = tmp_path / "run"

    prepared = prepare_output_dir(output)

    assert prepared == output
    with pytest.raises(PlaytestConfigurationError, match="already exists"):
        prepare_output_dir(output)


def test_output_directory_rejects_real_data_and_descendants() -> None:
    from tools.playtest_harness import REAL_DATA_DIR

    for path in (REAL_DATA_DIR, REAL_DATA_DIR / "playtests"):
        with pytest.raises(PlaytestConfigurationError, match="real data"):
            assert_safe_output_dir(path)


@pytest.mark.asyncio
async def test_scenario_queue_serializes_jobs() -> None:
    queue = ScenarioQueue(1)
    active = 0
    maximum_active = 0

    async def operation(label: str) -> dict:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        await asyncio.sleep(0.02)
        active -= 1
        return {"label": label}

    first, second = await asyncio.gather(
        queue.run(lambda: operation("first")),
        queue.run(lambda: operation("second")),
    )

    assert maximum_active == 1
    assert {first["label"], second["label"]} == {"first", "second"}
    assert max(first["queue"]["wait_ms"], second["queue"]["wait_ms"]) >= 10


def test_analysis_detects_observable_signals() -> None:
    narrator_response = json.dumps(
        {
            "narration": "You feel the air change.",
            "next_speaker": "C2",
            "context_for_character": "Context",
            "scene_update": {"physical_facts": '{"door": "open"}'},
            "mood_updates": {"C2": "calm"},
        }
    )
    records = [
        {
            "agent": "narrator",
            "turn_number": 1,
            "request": {"messages": [{"role": "user", "content": "SPEAKER=Thorn"}]},
            "response": narrator_response,
            "error": None,
            "duration_ms": 12.5,
            "attempt_number": 1,
            "prompt_chars": 100,
        },
        {
            "agent": "character:Lyra",
            "turn_number": 1,
            "request": {"messages": []},
            "response": '"Fine," I whisper, my eyes narrowing.',
            "error": None,
            "duration_ms": 5.0,
            "attempt_number": 2,
            "prompt_chars": 50,
        },
    ]
    event_results = [
        {
            "type": "turn",
            "before": {"moods": {"C2": "calm"}},
            "result": {"turn_number": 1},
        }
    ]

    analysis = analyze_debug_records(records, event_results)

    assert analysis["llm_calls"] == 2
    assert analysis["retry_attempts"] == 1
    assert analysis["nested_physical_facts_outputs"] == 1
    assert analysis["second_person_narrations"] == 1
    assert analysis["character_action_heuristic_hits"] == 1
    assert analysis["redundant_mood_updates"] == 1
    assert analysis["player_prompt_occurrences"] == 0


def test_aggregation_and_markdown_are_repeatable() -> None:
    runs = [
        {
            "scenario": "same",
            "repetition": 1,
            "session_id": "one",
            "queue": {"wait_ms": 0.0},
            "analysis": {"llm_calls": 2, "llm_errors": 0},
        },
        {
            "scenario": "same",
            "repetition": 2,
            "session_id": "two",
            "queue": {"wait_ms": 1.0},
            "analysis": {"llm_calls": 4, "llm_errors": 0},
        },
    ]
    aggregates = aggregate_runs(runs)
    manifest = {
        "started_at": "now",
        "model_label": "model",
        "llm_host": "local",
        "repeat": 2,
        "max_in_flight": 1,
        "data_dir": "/tmp/run",
        "runs": runs,
    }

    assert aggregates == [
        {
            "scenario": "same",
            "runs": 2,
            "metrics": {
                "llm_calls": {"min": 2.0, "mean": 3.0, "max": 4.0},
                "llm_errors": {"min": 0.0, "mean": 0.0, "max": 0.0},
            },
        }
    ]
    report = build_markdown_report(manifest)
    assert "same" in report
    assert "model" in report
