"""Concurrency-safe append-only session debug log.

Every entry shares one envelope — ``ts``, ``session_id``, ``turn_number``,
``agent`` — and adds its own fields. The envelope is written in exactly one
place (``_emit``) so a new event cannot forget a field and the whole log stays
queryable by turn: this file is the raw material for ``tools/replay_session.py``,
``tools/analyze_memory_run.py`` and the frontend's debug drawer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.llm.tokens import estimate_prompt_tokens
from src.store.locks import append_lock
from src.store.sessions import session_debug_path


def _append(session_id: str, entry: dict[str, Any]) -> None:
    if not session_id:
        return
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with append_lock(session_id):
        path = session_debug_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def _emit(session_id: str, agent: str, turn_number: int = 0, **fields: Any) -> None:
    """Append one entry under the canonical envelope."""
    _append(
        session_id,
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "turn_number": turn_number,
            "agent": agent,
            **fields,
        },
    )


def read_entries(session_id: str, limit: int) -> list[dict[str, Any]]:
    """Read a bounded, complete snapshot while excluding any in-progress append."""
    if limit <= 0:
        return []
    with append_lock(session_id):
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
    _emit(
        session_id,
        "turn_input",
        turn_number,
        input={
            "speech": speech,
            "thought": thought,
            "action": action,
            "force_speaker": requested_force_speaker,
            "narrator_hint": narrator_hint,
            "skip": skip,
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
    _emit(
        session_id,
        "turn_input_effective",
        turn_number,
        input=value,
        effective_force_speaker=effective_force_speaker,
        transformed_fields=transformed_fields,
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
    _emit(
        session_id,
        "command_input",
        turn_number,
        operation_id=operation_id,
        command=command,
        plugin_id=plugin_id,
        plugin_version=plugin_version,
        input=input_metadata,
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
    _emit(
        session_id,
        "command_result",
        turn_number,
        operation_id=operation_id,
        command=command,
        plugin_id=plugin_id,
        plugin_version=plugin_version,
        status=status,
        result_kind=result_kind,
        error_type=error_type,
        error=error,
    )


@dataclass(frozen=True, slots=True)
class LlmCallRequest:
    """What was sent to the provider for one attempt (no credentials)."""

    agent: str
    model: str
    messages: list[dict]
    max_tokens: int
    response_format: dict | None
    provider: str
    api_base: str
    thinking_enabled: bool
    # A guard retry is a SECOND structured call the agent chose to make after
    # reading the first answer (repetition, whisper leak, malformed action) -
    # not a transport retry. Both carry attempt_number 1, so a tool counting
    # only that field reports "zero retries" for a turn that called the model
    # twice (task 54, finding 7).
    guard_retry: str = ""


@dataclass(frozen=True, slots=True)
class LlmCallOutcome:
    """What came back from that attempt, successful or not."""

    content: str | None
    error: BaseException | None
    duration_ms: float
    attempt_number: int
    usage: dict[str, Any] | None = None
    cache_hit_tokens: int | None = None
    cache_miss_tokens: int | None = None


def log_llm_call(
    session_id: str,
    turn_number: int,
    request: LlmCallRequest,
    outcome: LlmCallOutcome,
) -> None:
    """Append one raw request/result attempt without secrets.

    Request and outcome are objects rather than seventeen positional parameters:
    the two call sites in ``llm/client.py`` differ only in the outcome, and a
    swapped pair of positions was a bug no test could have caught.
    """
    if not session_id:
        return
    error = outcome.error
    _emit(
        session_id,
        request.agent,
        turn_number,
        provider=request.provider,
        model=request.model,
        request={
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "response_format": request.response_format,
            "provider_options": {
                "api_base": request.api_base,
                "thinking_enabled": request.thinking_enabled,
            },
        },
        response=outcome.content,
        guard_retry=request.guard_retry,
        usage=outcome.usage,
        prompt_cache=(
            {"hit_tokens": outcome.cache_hit_tokens, "miss_tokens": outcome.cache_miss_tokens}
            if outcome.cache_hit_tokens is not None or outcome.cache_miss_tokens is not None
            else None
        ),
        error=(str(error) or repr(error)) if error is not None else None,
        error_type=type(error).__name__ if error is not None else None,
        error_repr=repr(error) if error is not None else None,
        duration_ms=outcome.duration_ms,
        attempt_number=outcome.attempt_number,
        prompt_chars=sum(len(str(message.get("content", ""))) for message in request.messages),
        prompt_estimated_tokens=estimate_prompt_tokens(request.messages),
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
    _emit(
        session_id,
        "whisper_output_guard",
        turn_number,
        character_id=character_id,
        outcome=outcome,
        leaked_tokens=leaked_tokens,
        attempt_number=attempt_number,
    )


def log_audible_speech_drop(
    session_id: str,
    turn_number: int,
    subject_id: str,
    reason: str,
    detail: str = "",
) -> None:
    """Record a Director ``audible_speech`` event that did NOT become a record.

    Every refusal on this channel is a line the reader will never see, so none of
    them may be silent (task 65). ``reason`` is one of ``echo``,
    ``whisper_leak``, ``internal_id`` or ``foreign_language``; ``detail`` carries
    the evidence that decided it.
    """
    _emit(
        session_id,
        "audible_speech_drop",
        turn_number,
        subject_id=subject_id,
        reason=reason,
        detail=detail,
    )


def log_undo(session_id: str, turn_number: int, removed_records: int) -> None:
    _emit(session_id, "undo", turn_number, removed_records=removed_records)


def log_compact(
    session_id: str,
    cutoff_turn_number: int,
    evicted_records: int,
    kept_records: int,
    *,
    checkpoint_id: str,
    trigger: str,
    turn_number: int = 0,
    estimated_context_tokens: int | None = None,
    threshold_tokens: int | None = None,
) -> None:
    _emit(
        session_id,
        "compact",
        turn_number,
        status="compacted",
        trigger=trigger,
        checkpoint_id=checkpoint_id,
        cutoff_turn_number=cutoff_turn_number,
        evicted_records=evicted_records,
        kept_records=kept_records,
        estimated_context_tokens=estimated_context_tokens,
        threshold_tokens=threshold_tokens,
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
    _emit(
        session_id,
        "drive_scheduler",
        turn_number,
        fired=fired,
        probability=probability,
        quiet_turns=quiet_turns,
        roll=roll,
        event_seed=event_seed,
    )


def log_scenario_contract_warning(session_id: str, *, phrases: list[str]) -> None:
    """A scenario's own directives named the operator (AGENTS.md section 3).

    Written, never acted on: the directives belong to whoever wrote the
    scenario, and silently rewriting narrative text is a worse failure than the
    leak it would hide. See src/prompt_contract.py for the rule.
    """
    _emit(session_id, "scenario_contract", 0, status="operator_ontology", phrases=phrases)


def log_time_skip(
    session_id: str,
    turn_number: int,
    *,
    ticks: int,
    summary: str,
    narrative_tick_after: int,
) -> None:
    """One applied time compression (Task 40 v2): Director request, code clamp."""
    _emit(
        session_id,
        "time_skip",
        turn_number,
        ticks=ticks,
        summary=summary,
        narrative_tick_after=narrative_tick_after,
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
    _emit(
        session_id,
        "autonomous_burst",
        turn_number,
        beat_count=beat_count,
        first_turn=first_turn,
        stop_reason=stop_reason,
    )


def log_unanswered_player(session_id: str, turn_number: int, *, present_characters: int) -> None:
    """The player spoke or acted and the Director routed nobody to answer.

    Measured, not assumed: 2026-07-21 review found turns where a message to a
    full room produced ``next_speakers: []`` and read as the world ignoring the
    player. This line makes the rate countable in any future session.
    """
    _emit(session_id, "unanswered_player", turn_number, present_characters=present_characters)


def log_roteiro_decision(
    session_id: str,
    turn_number: int,
    *,
    action: str,
    reason: str,
    beat_id: str,
    anchors_missing: list[str],
    actors_missing: list[str],
) -> None:
    """One deterministic roteiro replan decision (Task 38) and its evidence."""
    _emit(
        session_id,
        "roteiro_replan",
        turn_number,
        action=action,
        reason=reason,
        beat_id=beat_id,
        anchors_missing=anchors_missing,
        actors_missing=actors_missing,
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
    """Record why an automatic compaction did or did not happen.

    The error MESSAGE is deliberately never written here, unlike ``log_llm_call``:
    a summarizer failure carries the private world summary it was building, and
    this entry is read back by tools and by the frontend debug drawer. Only the
    exception's type and a sanitized qualified name are safe to keep, which is
    enough to tell provider flake from a bug (locked by
    ``tests/test_compaction.py``).
    """
    _emit(
        session_id,
        "compaction_status",
        turn_number,
        status=status,
        trigger=trigger,
        estimated_context_tokens=estimated_context_tokens,
        threshold_tokens=threshold_tokens,
        reason=reason,
        error=None,
        error_type=type(error).__name__ if error is not None else None,
        error_repr=(
            f"<{type(error).__module__}.{type(error).__qualname__}>" if error is not None else None
        ),
    )


def log_restore_compaction(
    session_id: str, restored: bool, reason: str, turn_number: int = 0
) -> None:
    _emit(session_id, "restore_compaction", turn_number, restored=restored, reason=reason)


def log_presence_change(
    session_id: str,
    *,
    origin: str,
    changed_ids: list[str],
    revision: int,
    edit_id: str,
    turn_number: int = 0,
) -> None:
    _emit(
        session_id,
        "presence_change",
        turn_number,
        origin=origin,
        changed_ids=changed_ids,
        revision=revision,
        edit_id=edit_id,
    )


def log_presence_undo(
    session_id: str, restored: bool, reason: str, turn_number: int = 0
) -> None:
    _emit(session_id, "presence_undo", turn_number, restored=restored, reason=reason)


def log_session_setup_change(
    session_id: str, *, revision: int, fields: list[str], turn_number: int = 0
) -> None:
    """Record an explicit out-of-band edit to the materialized session snapshot."""
    _emit(
        session_id,
        "session_setup_change",
        turn_number,
        revision=revision,
        fields=fields,
    )
