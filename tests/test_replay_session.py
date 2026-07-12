"""Tests for reconstructing and comparing recorded Roleplay sessions."""

from __future__ import annotations

import pytest

from tools.replay_session import (
    ReplaySessionError,
    build_recorded_turns,
    build_recorded_turns_from_narrator_history,
    first_difference,
    normalize_state,
    successful_outputs,
)


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


def test_build_recorded_turns_uses_character_calls_to_align_force_speaker() -> None:
    records = [
        {"turn_number": 1, "agent": "narrator", "response": "{}"},
        {"turn_number": 1, "agent": "character:Lyra", "response": "Hello"},
        {"turn_number": 2, "agent": "narrator", "response": "{}"},
    ]

    turns = build_recorded_turns(_source_state(), records)

    assert [(turn.speech, turn.action, turn.force_speaker) for turn in turns] == [
        ("Speak", "Act", "C2"),
        ("", "Wait", "Narrator"),
    ]


def test_build_recorded_turns_rejects_unknown_character() -> None:
    records = [
        {"turn_number": 1, "agent": "narrator", "response": "{}"},
        {"turn_number": 1, "agent": "character:Ghost", "response": "Boo"},
    ]

    with pytest.raises(ReplaySessionError, match="Ghost"):
        build_recorded_turns(_source_state(), records)


def test_build_recorded_turns_recovers_inputs_from_latest_narrator_history() -> None:
    history = """CURRENT SCENE:
  Location: Tavern

HISTORY:
  Turn 1 — Thorn: Speak exactly
  Turn 1 — Thorn: Act exactly
  Turn 1 — Narrator: Something happens
  Turn 1 — C2: Hello
  Turn 2 — Thorn: Continue
  Turn 2 — Thorn: Move
"""
    records = [
        {
            "turn_number": 1,
            "agent": "narrator",
            "request": {"messages": [{"role": "user", "content": "HISTORY:\nold"}]},
            "response": "{}",
        },
        {"turn_number": 1, "agent": "character:Lyra", "response": "Hello"},
        {
            "turn_number": 2,
            "agent": "narrator",
            "request": {"messages": [{"role": "user", "content": history}]},
            "response": "{}",
        },
    ]

    turns = build_recorded_turns_from_narrator_history(
        records,
        controlled_name="Thorn",
        character_ids_by_name={"Lyra": "C2"},
    )

    assert [(turn.speech, turn.action, turn.force_speaker) for turn in turns] == [
        ("Speak exactly", "Act exactly", "C2"),
        ("Continue", "Move", "Narrator"),
    ]


def test_prompt_recovery_rejects_turn_without_both_input_fields() -> None:
    records = [
        {
            "turn_number": 1,
            "agent": "narrator",
            "request": {
                "messages": [{"role": "user", "content": "HISTORY:\n  Turn 1 — Thorn: Only"}]
            },
            "response": "{}",
        }
    ]

    with pytest.raises(ReplaySessionError, match="exactly speech plus action"):
        build_recorded_turns_from_narrator_history(
            records,
            controlled_name="Thorn",
            character_ids_by_name={"Lyra": "C2"},
        )


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
