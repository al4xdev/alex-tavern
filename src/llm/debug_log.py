"""Concurrency-safe append-only session debug log."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from typing import Any
from weakref import WeakValueDictionary

from src.llm.tokens import estimate_prompt_tokens
from src.store.sessions import session_debug_path

_locks: WeakValueDictionary[str, threading.Lock] = WeakValueDictionary()
_locks_guard = threading.Lock()


def _get_lock(session_id: str) -> threading.Lock:
    with _locks_guard:
        lock = _locks.get(session_id)
        if lock is None:
            lock = threading.Lock()
            _locks[session_id] = lock
        return lock


def _append(session_id: str, entry: dict[str, Any]) -> None:
    if not session_id:
        return
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with _get_lock(session_id):
        path = session_debug_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def read_entries(session_id: str, limit: int) -> list[dict[str, Any]]:
    """Read a bounded, complete snapshot while excluding any in-progress append."""
    if limit <= 0:
        return []
    with _get_lock(session_id):
        path = session_debug_path(session_id)
        if not path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                entries.append(value)
        return entries


def log_turn_input(
    session_id: str,
    turn_number: int,
    speech: str,
    thought: str,
    action: str,
    requested_force_speaker: str | None,
    narrator_hint: str = "",
    skip: bool = False,
) -> None:
    """Append the exact API turn payload before any LLM call for that turn."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "turn_input",
            "input": {
                "speech": speech,
                "thought": thought,
                "action": action,
                "force_speaker": requested_force_speaker,
                "narrator_hint": narrator_hint,
                "skip": skip,
            },
        },
    )


def log_effective_turn_input(
    session_id: str,
    turn_number: int,
    value: dict[str, Any],
    effective_force_speaker: str | None,
    transformed_fields: list[str],
) -> None:
    """Append the post-plugin input that becomes authoritative history."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "turn_input_effective",
            "input": value,
            "effective_force_speaker": effective_force_speaker,
            "transformed_fields": transformed_fields,
        },
    )


def log_command_input(
    session_id: str,
    turn_number: int,
    *,
    operation_id: str,
    command: str,
    plugin_id: str,
    plugin_version: str,
    input_metadata: dict[str, Any],
) -> None:
    """Record a utility command without ever persisting uploaded Base64 data."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "command_input",
            "operation_id": operation_id,
            "command": command,
            "plugin_id": plugin_id,
            "plugin_version": plugin_version,
            "input": input_metadata,
        },
    )


def log_command_result(
    session_id: str,
    turn_number: int,
    *,
    operation_id: str,
    command: str,
    plugin_id: str,
    plugin_version: str,
    status: str,
    result_kind: str,
    error_type: str | None = None,
    error: str | None = None,
) -> None:
    """Record the command outcome while keeping the potentially large draft out of the log."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "command_result",
            "operation_id": operation_id,
            "command": command,
            "plugin_id": plugin_id,
            "plugin_version": plugin_version,
            "status": status,
            "result_kind": result_kind,
            "error_type": error_type,
            "error": error,
        },
    )


def log_llm_call(
    session_id: str,
    turn_number: int,
    agent: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    response_format: dict | None,
    response: str | None,
    error: BaseException | None,
    duration_ms: float,
    attempt_number: int,
    provider: str,
    api_base: str,
    thinking_enabled: bool,
    usage: dict[str, Any] | None,
    cache_hit_tokens: int | None,
    cache_miss_tokens: int | None,
) -> None:
    """Append one raw request/result attempt without secrets."""
    if not session_id:
        return
    prompt_chars = sum(len(str(message.get("content", ""))) for message in messages)
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": agent,
            "provider": provider,
            "model": model,
            "request": {
                "messages": messages,
                "max_tokens": max_tokens,
                "response_format": response_format,
                "provider_options": {
                    "api_base": api_base,
                    "thinking_enabled": thinking_enabled,
                },
            },
            "response": response,
            "usage": usage,
            "prompt_cache": (
                {
                    "hit_tokens": cache_hit_tokens,
                    "miss_tokens": cache_miss_tokens,
                }
                if cache_hit_tokens is not None or cache_miss_tokens is not None
                else None
            ),
            "error": (str(error) or repr(error)) if error is not None else None,
            "error_type": type(error).__name__ if error is not None else None,
            "error_repr": repr(error) if error is not None else None,
            "duration_ms": duration_ms,
            "attempt_number": attempt_number,
            "prompt_chars": prompt_chars,
            "prompt_estimated_tokens": estimate_prompt_tokens(messages),
        },
    )


def log_whisper_output_guard(
    session_id: str,
    turn_number: int,
    character_id: str,
    outcome: str,
    leaked_tokens: list[str],
    attempt_number: int,
) -> None:
    """Record the Character output guard acting on a whispered-secret leak.

    ``outcome`` is "retried" (a correction was sent and the model got another
    attempt) or "redacted" (last resort: secret tokens replaced in the recorded
    speech).
    """
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "whisper_output_guard",
            "character_id": character_id,
            "outcome": outcome,
            "leaked_tokens": leaked_tokens,
            "attempt_number": attempt_number,
        },
    )


def log_undo(session_id: str, turn_number: int, removed_records: int) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "undo",
            "removed_records": removed_records,
        },
    )


def log_compact(
    session_id: str,
    cutoff_turn_number: int,
    evicted_records: int,
    kept_records: int,
    *,
    checkpoint_id: str,
    trigger: str,
    estimated_context_tokens: int | None = None,
    threshold_tokens: int | None = None,
) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "agent": "compact",
            "status": "compacted",
            "trigger": trigger,
            "checkpoint_id": checkpoint_id,
            "cutoff_turn_number": cutoff_turn_number,
            "evicted_records": evicted_records,
            "kept_records": kept_records,
            "estimated_context_tokens": estimated_context_tokens,
            "threshold_tokens": threshold_tokens,
        },
    )


def log_drive_decision(
    session_id: str,
    turn_number: int,
    *,
    fired: bool,
    probability: float,
    quiet_turns: int,
    roll: float,
    event_seed: str = "",
) -> None:
    """One autonomous-event scheduler decision (Task 33), fired or not."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "drive_scheduler",
            "fired": fired,
            "probability": probability,
            "quiet_turns": quiet_turns,
            "roll": roll,
            "event_seed": event_seed,
        },
    )


def log_burst(
    session_id: str,
    turn_number: int,
    *,
    beat_count: int,
    stop_reason: str,
    first_turn: int,
) -> None:
    """One autonomous burst outcome (Task 37): how many beats and why it stopped."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "autonomous_burst",
            "beat_count": beat_count,
            "first_turn": first_turn,
            "stop_reason": stop_reason,
        },
    )


def log_compaction_status(
    session_id: str,
    turn_number: int,
    *,
    status: str,
    trigger: str,
    estimated_context_tokens: int | None,
    threshold_tokens: int | None,
    reason: str = "",
    error: BaseException | None = None,
) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": "compaction_status",
            "status": status,
            "trigger": trigger,
            "estimated_context_tokens": estimated_context_tokens,
            "threshold_tokens": threshold_tokens,
            "reason": reason,
            "error": None,
            "error_type": type(error).__name__ if error is not None else None,
            "error_repr": (
                f"<{type(error).__module__}.{type(error).__qualname__}>"
                if error is not None
                else None
            ),
        },
    )


def log_restore_compaction(session_id: str, restored: bool, reason: str) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "agent": "restore_compaction",
            "restored": restored,
            "reason": reason,
        },
    )


def log_presence_change(
    session_id: str, *, origin: str, changed_ids: list[str], revision: int, edit_id: str
) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "agent": "presence_change",
            "origin": origin,
            "changed_ids": changed_ids,
            "revision": revision,
            "edit_id": edit_id,
        },
    )


def log_presence_undo(session_id: str, restored: bool, reason: str) -> None:
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "agent": "presence_undo",
            "restored": restored,
            "reason": reason,
        },
    )
