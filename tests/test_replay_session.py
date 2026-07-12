"""Tests for reconstructing and comparing recorded Roleplay sessions."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.replay_session import (
    ReplaySessionError,
    build_recorded_turns_from_turn_inputs,
    first_difference,
    inspect_turn_state,
    load_debug_records,
    normalize_state,
    successful_outputs,
)

CURRENT_FIXTURE = Path(__file__).parent / "fixtures" / "current_replay.debug.jsonl"


def _source_state() -> dict:
    return {
        "session_id": "old",
        "created_at": "yesterday",
        "characters": {
            "C1": {"mind": {"name": "Thorn"}},
            "C2": {"mind": {"name": "Lyra"}},
        },
        "history": [
            {
                "turn_number": 1,
                "speaker": "Player",
                "content_type": "speech",
                "content": "Speak",
            },
            {
                "turn_number": 1,
                "speaker": "Player",
                "content_type": "action",
                "content": "Act",
            },
            {
                "turn_number": 2,
                "speaker": "Player",
                "content_type": "action",
                "content": "Wait",
            },
        ],
    }


def test_turn_input_markers_recover_exact_payload_without_state() -> None:
    records = [
        {
            "turn_number": 1,
            "agent": "turn_input",
            "input": {"speech": "Speak", "action": "", "force_speaker": None},
            "effective_force_speaker": None,
        },
        {"turn_number": 1, "agent": "narrator", "response": "{}"},
        {
            "turn_number": 2,
            "agent": "turn_input",
            "input": {"speech": "", "action": "Move", "force_speaker": "C2"},
            "effective_force_speaker": "C2",
        },
    ]

    turns = build_recorded_turns_from_turn_inputs(records)

    assert [(turn.speech, turn.action, turn.force_speaker) for turn in turns] == [
        ("Speak", "", None),
        ("", "Move", "C2"),
    ]


def test_current_fixture_is_machine_readable_and_replayable() -> None:
    records = load_debug_records(CURRENT_FIXTURE)
    turns = build_recorded_turns_from_turn_inputs(records)

    assert len(turns) == 9
    assert [turn.turn_number for turn in turns] == list(range(1, 10))
    assert all(turn.force_speaker == "Narrator" for turn in turns)
    assert len(successful_outputs(records)) == 10
    assert successful_outputs(records)[-1]["agent"] == "summarizer"


def test_turn_input_markers_are_required() -> None:
    with pytest.raises(ReplaySessionError, match="no turn_input"):
        build_recorded_turns_from_turn_inputs(
            [{"turn_number": 1, "agent": "narrator", "response": "{}"}]
        )


def test_turn_input_markers_reject_duplicate_turns() -> None:
    marker = {
        "turn_number": 1,
        "agent": "turn_input",
        "input": {"speech": "Speak", "action": "Act", "force_speaker": None},
    }

    with pytest.raises(ReplaySessionError, match="Duplicate"):
        build_recorded_turns_from_turn_inputs([marker, marker])


def test_successful_outputs_ignores_errors_markers_and_volatile_fields() -> None:
    records = [
        {
            "ts": "one",
            "turn_number": 1,
            "agent": "narrator",
            "request": {"messages": []},
            "response": "{}",
        },
        {"ts": "two", "turn_number": 1, "agent": "narrator", "error": "timeout"},
        {
            "ts": "invalid-json",
            "turn_number": 1,
            "agent": "narrator",
            "response": "not-json",
            "error": "JSONDecodeError",
        },
        {"ts": "three", "agent": "compact", "kept_records": 2},
    ]

    assert successful_outputs(records) == [
        {"turn_number": 1, "agent": "narrator", "response": "{}"}
    ]


def test_normalize_state_removes_only_run_identity() -> None:
    state = _source_state()

    normalized = normalize_state(state)

    assert "session_id" not in normalized
    assert "created_at" not in normalized
    assert normalized["characters"] == state["characters"]
    assert state["session_id"] == "old"


def test_first_difference_reports_nested_path() -> None:
    expected = {"history": [{"content": "same"}, {"content": "expected"}]}
    actual = {"history": [{"content": "same"}, {"content": "actual"}]}

    difference = first_difference(expected, actual)

    assert difference is not None
    assert "$.history[1].content" in difference
    assert "expected" in difference


def test_first_difference_returns_none_for_equal_values() -> None:
    value = {"a": [1, {"b": True}]}

    assert first_difference(value, value) is None


def test_inspect_turn_state_reports_per_turn_evidence() -> None:
    state = {
        "history": [
            {"turn_number": 1, "content": "first"},
            {"turn_number": 2, "content": "second"},
        ],
        "scene": {"location": "Watchtower"},
    }

    assert inspect_turn_state(state, 2) == {
        "turn_number": 2,
        "history_records": 2,
        "latest_persisted_turn": 2,
        "location": "Watchtower",
    }


@pytest.mark.parametrize(
    ("state", "message"),
    [
        ([], "not a JSON object"),
        ({}, "no history array"),
        ({"history": [{"turn_number": 1}]}, "State drift"),
    ],
)
def test_inspect_turn_state_rejects_drift(state: object, message: str) -> None:
    with pytest.raises(ReplaySessionError, match=message):
        inspect_turn_state(state, 2)
