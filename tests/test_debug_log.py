"""The debug log's shared envelope: every entry is queryable by turn."""

from __future__ import annotations

import pytest

from src.llm import debug_log
from src.llm.debug_log import LlmCallOutcome, LlmCallRequest, read_entries

SESSION = "envelope1"

ENVELOPE_KEYS = {"ts", "session_id", "turn_number", "agent"}


def _emit_one_of_each() -> None:
    debug_log.log_turn_input(SESSION, 3, "oi", "", "", None)
    debug_log.log_effective_turn_input(SESSION, 3, {"speech": "oi"}, None, [])
    debug_log.log_undo(SESSION, 3, 2)
    debug_log.log_compact(
        SESSION, 2, 4, 6, checkpoint_id="c000001", trigger="manual", turn_number=3
    )
    debug_log.log_drive_decision(
        SESSION, 3, fired=False, probability=0.1, quiet_turns=1, roll=0.9
    )
    debug_log.log_time_skip(SESSION, 3, ticks=2, summary="a noite avanca", narrative_tick_after=9)
    debug_log.log_burst(SESSION, 3, beat_count=2, stop_reason="beat_settled", first_turn=2)
    debug_log.log_unanswered_player(SESSION, 3, present_characters=2)
    debug_log.log_roteiro_decision(
        SESSION, 3, action="replan_beat", reason="stall", beat_id="b1",
        anchors_missing=[], actors_missing=[],
    )
    debug_log.log_whisper_output_guard(SESSION, 3, "C1", "retried", ["X-9"], 1)
    debug_log.log_compaction_status(
        SESSION, 3, status="not_needed", trigger="automatic",
        estimated_context_tokens=10, threshold_tokens=99,
    )
    debug_log.log_restore_compaction(SESSION, True, "", 3)
    debug_log.log_presence_change(
        SESSION, origin="human", changed_ids=["C2"], revision=4, edit_id="e1", turn_number=3
    )
    debug_log.log_presence_undo(SESSION, True, "", 3)
    debug_log.log_command_input(
        SESSION, 3, operation_id="op1", command="dice", plugin_id="p", plugin_version="1.0.0",
        input_metadata={},
    )
    debug_log.log_command_result(
        SESSION, 3, operation_id="op1", command="dice", plugin_id="p", plugin_version="1.0.0",
        status="ok", result_kind="core/text",
    )


def test_every_entry_carries_the_full_envelope() -> None:
    _emit_one_of_each()
    entries = read_entries(SESSION, 100)

    assert len(entries) == 16
    for entry in entries:
        assert set(entry) >= ENVELOPE_KEYS, entry.get("agent")
        # turn_number used to be absent from compaction and presence entries,
        # which made those events impossible to correlate with a turn.
        assert entry["turn_number"] == 3, entry["agent"]
        assert entry["session_id"] == SESSION


def test_llm_call_records_request_and_outcome_without_credentials() -> None:
    request = LlmCallRequest(
        agent="director",
        model="deepseek-chat",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=512,
        response_format={"type": "json_object"},
        provider="deepseek",
        api_base="https://api.deepseek.com/v1",
        thinking_enabled=False,
    )
    debug_log.log_llm_call(
        "llmcall1",
        7,
        request,
        LlmCallOutcome(content='{"ok": true}', error=None, duration_ms=12.5, attempt_number=1),
    )

    entry = read_entries("llmcall1", 1)[0]
    assert entry["agent"] == "director"
    assert entry["turn_number"] == 7
    assert entry["request"]["provider_options"] == {
        "api_base": "https://api.deepseek.com/v1",
        "thinking_enabled": False,
    }
    assert entry["prompt_chars"] == len("hello")
    assert entry["error"] is None
    assert "api_key" not in str(entry)


@pytest.mark.parametrize("session_id", ["", None])
def test_a_sessionless_call_is_never_written(session_id: object) -> None:
    debug_log.log_undo(session_id or "", 1, 1)  # must not raise or create a file
