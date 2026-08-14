"""Post-wave-1 audit of one fresh cell.

Answers three questions that the archive cannot, because the archive was
produced by the engine wave 1 replaced:

  70/64  did removing the named exclusion change control return? The archive
         measured return_control=True on 5 of 482 Director turns (1%) and the
         controlled character routed 11 times (2.3%), both taken WHILE the
         prompt carried the exclusion. Task 64 is not to be designed against
         those numbers.

  63     does the redaction marker still reach a persisted record or the live
         ledger now that 65 removed the channel carrying 42 of its 43 cases?
         This is task 63's own falsifier: if it never reaches either, the task
         is a prose cosmetic and drops out of wave 1.

  65     does the shipped mandate hold up over a real session, and how often
         does mandate_ignored fire? That is the calibration instrument for
         _INTENT_CARRIED_RATIO, now at 0.34.

Reuses tools/acceptance/immersion_scanners.py for redaction and
director-speech rather than reimplementing either.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

from src.prompt_contract import named_exclusions  # noqa: E402
from tools.acceptance.immersion_scanners import scan  # noqa: E402

_MOOD_ID_RE = re.compile(r"^\s*ID=([A-Za-z0-9_]+)\s*\|", re.MULTILINE)


class _Mind:
    def __init__(self, name: str) -> None:
        self.name = name


class _Char:
    def __init__(self, name: str) -> None:
        self.mind = _Mind(name)


def routing_audit(session_dir: pathlib.Path) -> dict:
    state = json.loads((session_dir / "state.json").read_text(encoding="utf-8"))
    controlled = (state.get("player") or {}).get("controlled_character_id")
    cast = {
        cid: _Char((data.get("mind") or {}).get("name") or cid)
        for cid, data in (state.get("characters") or {}).items()
    }

    director_turns = 0
    return_control = 0
    pc_routed_raw = 0
    pc_routed_final = 0
    exclusions = 0
    prompts_with_block = 0

    for line in (session_dir / "debug.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("agent") != "director" or not isinstance(record.get("request"), dict):
            continue
        messages = record["request"].get("messages") or []
        if len(messages) < 2:
            continue
        user = str(messages[1].get("content", ""))
        director_turns += 1
        if named_exclusions(user, cast):
            exclusions += 1
        if "ROUTING CONSTRAINT" in user:
            prompts_with_block += 1
        if record.get("error") or not isinstance(record.get("response"), str):
            continue
        try:
            parsed = json.loads(record["response"])
        except json.JSONDecodeError:
            continue
        if parsed.get("return_control"):
            return_control += 1
        raw = parsed.get("next_speakers") or []
        if controlled in [str(x) for x in raw]:
            pc_routed_raw += 1

    for turn in state.get("history", []):
        if turn.get("speaker") == controlled and turn.get("content_type") in ("speech", "action"):
            pc_routed_final += 1

    return {
        "controlled": controlled,
        "director_turns": director_turns,
        "return_control_true": return_control,
        "pc_routed_raw": pc_routed_raw,
        "named_exclusions": exclusions,
        "routing_constraint_blocks": prompts_with_block,
        "pc_records_in_history": pc_routed_final,
    }


def drop_log(session_dir: pathlib.Path) -> tuple[dict, dict]:
    """Drop reasons, plus a case-C/case-A split of the mandate misses.

    This session ran BEFORE `routed_intent_missing` split off, so both misses
    are logged as `mandate_ignored`. They are separable after the fact: case C
    is "the subject already had a speech record that turn", which is exactly
    the condition the runner branched on. Only the case-C share bears on the
    case-C falsifier.
    """
    state = json.loads((session_dir / "state.json").read_text(encoding="utf-8"))
    spoke: set[tuple[int, str]] = {
        (int(turn.get("turn_number", 0)), str(turn.get("speaker")))
        for turn in state.get("history", [])
        if turn.get("content_type") == "speech"
    }

    reasons: dict[str, int] = {}
    split = {"case_C_already_speaking": 0, "case_A_routed": 0}
    for line in (session_dir / "debug.jsonl").read_text(encoding="utf-8").splitlines():
        if "audible_speech" not in line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not str(record.get("agent") or "").startswith("audible_speech"):
            continue
        reason = str(record.get("reason") or "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
        if reason == "mandate_ignored":
            key = (int(record.get("turn_number", 0)), str(record.get("subject_id")))
            split["case_C_already_speaking" if key in spoke else "case_A_routed"] += 1
    return reasons, split


def main() -> None:
    session_dir = pathlib.Path(sys.argv[1]).resolve()
    report = scan(session_dir.name, root=session_dir.parent)
    routing = routing_audit(session_dir)
    drops, split = drop_log(session_dir)

    print(f"session {session_dir.name}  turns={report.turns}")
    print()
    print("--- 70 / 64: routing and control return ---")
    for key, value in routing.items():
        print(f"  {key:<28} {value}")
    d = routing["director_turns"] or 1
    print(f"  return_control rate           {routing['return_control_true'] / d:.1%}")
    print(f"  PC routed rate (raw)          {routing['pc_routed_raw'] / d:.1%}")
    print()
    print("--- 63: redaction ---")
    for key, value in report.redaction.items():
        print(f"  {key:<28} {value}")
    print()
    print("--- 65: director-authored speech ---")
    for key, value in report.director_speech.items():
        print(f"  {key:<28} {value}")
    print()
    print("--- 65: audible_speech drop log ---")
    print(f"  {drops or 'no drop records found'}")
    total_events = report.director_speech.get("audible_speech_events") or 0
    ignored = drops.get("mandate_ignored", 0)
    print(f"  mandate_ignored split: {split}")
    if total_events:
        print(f"  mandate_ignored / audible_speech events = {ignored}/{total_events}")
        case_c = split["case_C_already_speaking"]
        print(f"  case-C misses (the falsifier's population) = {case_c}")
    print()
    print("--- empty audience (67) ---")
    for key, value in report.empty_audience.items():
        print(f"  {key:<28} {value}")


if __name__ == "__main__":
    main()
