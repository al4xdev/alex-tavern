"""Reproduce the post-task-70 control-return counts from recorded sessions.

Only committed turns (``turn_number <= state.revision``) enter the denominator.
For a retried Director call, the last schema-parseable response is the accepted
candidate for this audit. The script reports valid responses beyond the committed
revision separately; they are evidence in the append-only log, not completed turns.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BATTERY_ROOT = REPOSITORY_ROOT / "plans/artifacts/repetition-battery"
SESSION_IDS = (
    "34390b86",
    "d0cc98e5",
    "00997daa",
    "b11b38dc",
    "55d03896",
    "21f7c4e1",
    "c76037ff",
    "09aabf25",
    "54bcdace",
)


@dataclass(frozen=True)
class SessionAudit:
    session_id: str
    revision: int
    valid_committed_director_turns: int
    return_control_turns: list[int]
    controlled_character_routed_turns: list[int]
    either_path_turns: list[int]
    valid_uncommitted_director_turns: list[int]


def _session_dir(session_id: str) -> Path:
    matches = sorted(BATTERY_ROOT.glob(f"*/sessions/{session_id}"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one directory for {session_id}, found {matches}")
    return matches[0]


def _parse_response(record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("error") is not None:
        return None
    response = record.get("response")
    if not isinstance(response, str):
        return None
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def audit_session(session_id: str) -> SessionAudit:
    session_dir = _session_dir(session_id)
    state = json.loads((session_dir / "state.json").read_text(encoding="utf-8"))
    revision = int(state["revision"])
    controlled_id = str(state["player"]["controlled_character_id"])

    valid_by_turn: dict[int, dict[str, Any]] = {}
    with (session_dir / "debug.jsonl").open(encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            if record.get("agent") != "director":
                continue
            parsed = _parse_response(record)
            if parsed is not None:
                valid_by_turn[int(record["turn_number"])] = parsed

    committed = {turn: value for turn, value in valid_by_turn.items() if turn <= revision}
    missing = sorted(set(range(1, revision + 1)) - committed.keys())
    if missing:
        raise RuntimeError(f"{session_id} lacks valid Director responses for turns {missing}")

    returned = sorted(
        turn for turn, value in committed.items() if value.get("return_control") is True
    )
    routed = sorted(
        turn
        for turn, value in committed.items()
        if controlled_id in [str(item) for item in value.get("next_speakers") or []]
    )
    return SessionAudit(
        session_id=session_id,
        revision=revision,
        valid_committed_director_turns=len(committed),
        return_control_turns=returned,
        controlled_character_routed_turns=routed,
        either_path_turns=sorted(set(returned) | set(routed)),
        valid_uncommitted_director_turns=sorted(turn for turn in valid_by_turn if turn > revision),
    )


def main() -> None:
    sessions = [audit_session(session_id) for session_id in SESSION_IDS]
    totals = {
        "sessions": len(sessions),
        "committed_director_turns": sum(item.valid_committed_director_turns for item in sessions),
        "return_control_turns": sum(len(item.return_control_turns) for item in sessions),
        "controlled_character_routed_turns": sum(
            len(item.controlled_character_routed_turns) for item in sessions
        ),
        "either_path_turns": sum(len(item.either_path_turns) for item in sessions),
        "sessions_without_either_path": sum(not item.either_path_turns for item in sessions),
    }
    print(json.dumps({"sessions": [asdict(item) for item in sessions], "totals": totals}, indent=2))


if __name__ == "__main__":
    main()
