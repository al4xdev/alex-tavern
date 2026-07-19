"""Task 32: routing_check event, cost attribution, post-split analyzer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.playtest_harness import (
    PlaytestConfigurationError,
    analyze_debug_records,
    evaluate_routing_check,
    load_scenario,
    turn_usage,
)

BASE = {
    "name": "t",
    "description": "d",
    "narrator_directives": "",
    "events": [],
}


def _write(tmp_path: Path, events: list[dict]) -> Path:
    doc = dict(BASE)
    doc["events"] = events
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class TestRoutingCheckLoader:
    def test_valid_routing_check_normalizes(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            [
                {
                    "type": "routing_check",
                    "speech": "Bruxa, e as venezianas?",
                    "expected_speakers": ["C7"],
                }
            ],
        )
        event = load_scenario(path).events[0]
        assert event["force_speaker"] is None
        assert event["expected_speakers"] == ["C7"]
        assert event["required"] is True

    def test_force_speaker_is_rejected(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            [
                {
                    "type": "routing_check",
                    "speech": "x",
                    "force_speaker": "C7",
                    "expected_speakers": ["C7"],
                }
            ],
        )
        with pytest.raises(PlaytestConfigurationError, match="natural routing"):
            load_scenario(path)

    def test_expected_speakers_must_be_non_empty(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            [{"type": "routing_check", "speech": "x", "expected_speakers": []}],
        )
        with pytest.raises(PlaytestConfigurationError, match="expected_speakers"):
            load_scenario(path)


class TestRoutingEvaluation:
    def test_expected_speaker_responding_passes(self) -> None:
        routing = evaluate_routing_check(
            {"expected_speakers": ["C7", "C2"]},
            {
                "character_responses": [{"character_id": "C7", "speech": "Sim."}],
                "next_speakers": ["C7"],
            },
        )
        assert routing["passed"] is True
        assert routing["localization"] == "expected_speaker_responded"

    def test_routed_elsewhere_is_localized(self) -> None:
        routing = evaluate_routing_check(
            {"expected_speakers": ["C7"]},
            {
                "character_responses": [{"character_id": "C2", "speech": "Eu respondo."}],
                "next_speakers": ["C2"],
            },
        )
        assert routing["passed"] is False
        assert routing["localization"] == "routed_elsewhere"

    def test_no_character_call_is_localized(self) -> None:
        routing = evaluate_routing_check(
            {"expected_speakers": ["C7"]},
            {"character_responses": [], "next_speakers": ["Narrator"]},
        )
        assert routing["passed"] is False
        assert routing["localization"] == "no_character_call"


class TestCostAttribution:
    RECORDS = [
        {
            "turn_number": 3,
            "request": {"messages": []},
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
            "prompt_cache": {"hit_tokens": 80, "miss_tokens": 20},
        },
        {
            "turn_number": 3,
            "request": {"messages": []},
            "usage": None,
        },
        {
            "turn_number": 4,
            "request": {"messages": []},
            "usage": {"prompt_tokens": 999, "completion_tokens": 1},
        },
        {"turn_number": 3, "agent": "turn_input"},
    ]

    def test_turn_usage_sums_only_that_turns_calls(self) -> None:
        usage = turn_usage(self.RECORDS, 3)
        assert usage == {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "cache_hit_tokens": 80,
            "cache_miss_tokens": 20,
            "calls": 2,
        }

    def test_missing_usage_degrades_gracefully(self) -> None:
        assert (
            turn_usage([{"turn_number": 1, "request": {"messages": []}}], 1)["prompt_tokens"] == 0
        )


class TestPostSplitAnalyzer:
    def test_prose_and_director_agents_feed_the_metrics(self) -> None:
        records = [
            {
                "turn_number": 1,
                "agent": "director",
                "request": {"messages": []},
                "error": None,
                "response": json.dumps(
                    {"next_speakers": ["C2"], "scene_update": None, "mood_updates": None}
                ),
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
            {
                "turn_number": 1,
                "agent": "prose",
                "request": {"messages": []},
                "error": None,
                "response": json.dumps({"narration": "Você sente o vento no rosto."}),
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
        ]
        analysis = analyze_debug_records(records, [])
        assert analysis["narrator_outputs"] == 1
        assert analysis["second_person_narrations"] == 1
        assert analysis["total_prompt_tokens"] == 17
        assert analysis["total_completion_tokens"] == 8
