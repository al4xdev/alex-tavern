from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = 4
LABELS = ["P", "Q", "R", "S"]
MAPPING = {"P": 1, "Q": 3, "R": 0, "S": 2}
REASONS = [
    "settled_transition_repeat",
    "causal_role_mismatch",
    "witness_impossibility",
    "simultaneous_actor_overload",
    "route_or_order_contradiction",
    "pacing_overload",
    "unsupported_object_use",
    "dangling_immediate_consequence",
    "no_material_progress",
]

SYSTEM = """You are an isolated fiction continuity judge. You do not write or
repair the story. Read the complete source state and four opaque structured
next-beat plans, then classify each plan independently.

A PASS must continue settled physical facts, preserve causal roles and orders,
use plausible witnesses, avoid assigning incompatible simultaneous actions to
one actor, respect the current pace, and materially advance the immediate beat.
A legal state transition can still be bad fiction. Veto a plan for any of these
closed reasons:
- settled_transition_repeat
- causal_role_mismatch
- witness_impossibility
- simultaneous_actor_overload
- route_or_order_contradiction
- pacing_overload
- unsupported_object_use
- dangling_immediate_consequence
- no_material_progress

Physical operation text is literal entry:current->target. Narrator as cause is
environmental or impersonal. Cue IDs have their registered meanings. Frame IDs
choose focus only and assert no position or action. next_speakers act only after
the planned beat.

Select the strongest PASS plan. Select NONE if every plan is vetoed. Return only
the schema object, with no prose and no preference for any label."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def selector_schema() -> dict[str, Any]:
    return {
        "name": "continuity_selection",
        "schema": {
            "type": "object",
            "properties": {
                "selected_plan": {"type": "string", "enum": [*LABELS, "NONE"]},
                "verdicts": {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "plan_id": {"type": "string", "enum": LABELS},
                            "verdict": {"type": "string", "enum": ["PASS", "VETO"]},
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string", "enum": REASONS},
                            },
                        },
                        "required": ["plan_id", "verdict", "reasons"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["selected_plan", "verdicts"],
            "additionalProperties": False,
        },
    }


def local_errors(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    verdicts = parsed.get("verdicts")
    if not isinstance(verdicts, list):
        return ["verdicts is not a list"]
    by_id = {
        item.get("plan_id"): item
        for item in verdicts
        if isinstance(item, dict) and item.get("plan_id") in LABELS
    }
    if set(by_id) != set(LABELS):
        errors.append("verdicts do not cover each plan exactly once")
    selected = parsed.get("selected_plan")
    if selected == "NONE":
        if any(item.get("verdict") == "PASS" for item in by_id.values()):
            errors.append("NONE selected while a plan passes")
    elif selected in by_id and by_id[selected].get("verdict") != "PASS":
        errors.append("selected plan is not marked PASS")
    for plan_id, item in by_id.items():
        reasons = item.get("reasons")
        verdict = item.get("verdict")
        if verdict == "PASS" and reasons:
            errors.append(f"passing plan {plan_id} has veto reasons")
        if verdict == "VETO" and not reasons:
            errors.append(f"vetoed plan {plan_id} has no reason")
    return errors


async def execute(run_name: str) -> None:
    out = HERE / run_name
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-v5-") as temporary_data:
        os.environ["ROLEPLAY_DATA_DIR"] = temporary_data
        sys.path.insert(0, str(ROOT))

        from src.llm.client import call_agent  # noqa: PLC0415

        source_messages = json.loads((HERE / "runs-v4/messages.json").read_text(encoding="utf-8"))
        source = source_messages[-1]["content"]
        candidates = {
            label: json.loads(
                (HERE / f"runs-v4/V4-{repeat}.result.json").read_text(encoding="utf-8")
            )["parsed"]
            for label, repeat in MAPPING.items()
        }
        meanings = (
            "CUE MEANINGS:\n"
            "east_courtyard_roar_nearer = external roar moves nearer\n"
            "east_courtyard_roar_fades = external roar fades\n"
            "east_courtyard_blood_scent_intensifies = courtyard blood scent grows\n"
            "south_arch_cold_intensifies = cold from cracked south seal grows\n"
            "south_arch_green_light_fades = green light at south seal fades\n"
            "equipment_rattles_from_roar = equipment rattles from external roar\n"
            "floor_vibration_intensifies = hall-floor vibration grows\n"
        )
        user = (
            source
            + "\n\n"
            + meanings
            + "\nOPAQUE CANDIDATE PLANS:\n"
            + json.dumps(candidates, ensure_ascii=False, indent=2)
        )
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ]
        schema = selector_schema()

        stored = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))
        config = {
            **stored["providers"]["deepseek"],
            "provider": "deepseek",
            "language": stored["language"],
        }
        write_json(
            out / "run.json",
            {
                "script_sha256": digest(Path(__file__)),
                "preregistration_sha256": digest(HERE / "PREREGISTRATION-V5.md"),
                "candidate_mapping": MAPPING,
                "reader_target": "S",
                "started_unix": time.time(),
            },
        )
        write_json(out / "messages.json", messages)
        write_json(out / "schema.json", schema)

        semaphore = asyncio.Semaphore(4)
        async with httpx.AsyncClient() as client:

            async def one(repeat: int) -> dict[str, Any]:
                async with semaphore:
                    session_id = f"v5-{repeat}"
                    result: dict[str, Any] = {"repeat": repeat}
                    try:
                        parsed = await call_agent(
                            client,
                            config,
                            copy.deepcopy(messages),
                            agent="continuity_judge",
                            json_schema=schema,
                            max_tokens=4096,
                            session_id=session_id,
                            turn_number=5,
                        )
                        result["client_valid"] = True
                        result["parsed"] = parsed
                        result["local_errors"] = local_errors(parsed)
                    except ValueError as exc:
                        result["client_valid"] = False
                        result["error"] = str(exc)

                    debug_path = Path(temporary_data) / "sessions" / session_id / "debug.jsonl"
                    if debug_path.exists():
                        archived = out / f"V5-{repeat}.debug.jsonl"
                        archived.write_bytes(debug_path.read_bytes())
                        result["attempts"] = len(
                            debug_path.read_text(encoding="utf-8").splitlines()
                        )
                    else:
                        result["attempts"] = 0
                    write_json(out / f"V5-{repeat}.result.json", result)
                    return result

            results = await asyncio.gather(*(one(repeat) for repeat in range(RUNS)))
        write_json(out / "summary.json", results)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: v5_selector.py RUN_NAME")
    asyncio.run(execute(sys.argv[1]))
