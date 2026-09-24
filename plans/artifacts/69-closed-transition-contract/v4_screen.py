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

OPERATIONS = {
    "east_messenger:present->incapacitated",
    "east_messenger:present->dead",
    "east_messenger:present->gone",
    "messenger_garrilha_fragment:available->used",
    "messenger_garrilha_fragment:available->destroyed",
    "messenger_garrilha_fragment:available->unavailable",
    "marta_equipment_chest:open->empty",
    "marta_equipment_chest:open->broken",
    "marta_equipment_chest:open->closed",
    "east_door:ajar->open",
    "east_door:ajar->blocked",
    "east_door:ajar->sealed",
    "east_door:ajar->broken",
    "east_door:ajar->closed",
    "south_arch_seal:cracked->collapsed",
    "south_arch_seal:cracked->cleared",
}

CUES = {
    "east_courtyard_roar_nearer",
    "east_courtyard_roar_fades",
    "east_courtyard_blood_scent_intensifies",
    "south_arch_cold_intensifies",
    "south_arch_green_light_fades",
    "equipment_rattles_from_roar",
    "floor_vibration_intensifies",
}

FRAMES = {
    "east_threshold_threat",
    "south_arch_failure",
    "equipment_triage",
    "command_platform_response",
    "split_east_and_south",
}

SYSTEM = """You are the Director's decision planner for a roleplay world.
Read the supplied history and current state, then return only the structured
decision requested by the JSON Schema. You choose what changes and who may
react. You do not write narration, dialogue, descriptions, summaries, moods,
positions, zone names, or any other prose.

CLOSED PHYSICAL STATE is binding. A settled transition cannot happen again.
Only a physical_transitions operation changes durable state. Every operation
already binds one known entry, its exact current state, and a different allowed
target state. Select only a causally coherent new consequence. Do not select
two operations for the same entry.

cue_events are new non-agentive sensory developments. Their IDs have these
fixed meanings:
- east_courtyard_roar_nearer: the external roar moves nearer;
- east_courtyard_roar_fades: the external roar fades;
- east_courtyard_blood_scent_intensifies: blood scent from the courtyard grows;
- south_arch_cold_intensifies: cold from the cracked south seal grows;
- south_arch_green_light_fades: green light at the south seal fades;
- equipment_rattles_from_roar: equipment rattles from the external roar;
- floor_vibration_intensifies: vibration through the hall floor grows.
Choose each cue at most once. A cue is a new change, never a recap.

blocking_frame_id chooses attention only: east threshold threat, south arch
failure, equipment triage, command platform response, or a split between east
and south. It asserts no character position or action.

next_speakers routes future character calls. It does not author what anyone
says. Select zero to three present IDs with an immediate reason to react, in
conversation order. Use return_control only when the beat ends on a decision,
danger, or direct question for one person. Preserve private thought boundaries
and never infer that any character is externally controlled.

Resolve the immediate pressure at the end of HISTORY and materially advance the
emergency. Do not buy compliance through a static tableau."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def schema_for(speakers: list[str]) -> dict[str, Any]:
    witnesses = {"type": "array", "items": {"type": "string", "enum": speakers}}
    return {
        "name": "director_decision_atoms",
        "schema": {
            "type": "object",
            "properties": {
                "next_speakers": {
                    "type": "array",
                    "items": {"type": "string", "enum": speakers},
                    "maxItems": 3,
                },
                "physical_transitions": {
                    "type": "array",
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": sorted(OPERATIONS)},
                            "cause_id": {
                                "type": "string",
                                "enum": ["Narrator", *speakers],
                            },
                            "witness_ids": witnesses,
                        },
                        "required": ["operation", "cause_id", "witness_ids"],
                        "additionalProperties": False,
                    },
                },
                "cue_events": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "cue_id": {"type": "string", "enum": sorted(CUES)},
                            "witness_ids": witnesses,
                        },
                        "required": ["cue_id", "witness_ids"],
                        "additionalProperties": False,
                    },
                },
                "blocking_frame_id": {"type": "string", "enum": sorted(FRAMES)},
                "return_control": {"type": "boolean"},
            },
            "required": [
                "next_speakers",
                "physical_transitions",
                "cue_events",
                "blocking_frame_id",
                "return_control",
            ],
            "additionalProperties": False,
        },
    }


def local_errors(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_entries: set[str] = set()
    for transition in parsed.get("physical_transitions", []):
        operation = transition.get("operation") if isinstance(transition, dict) else None
        if operation not in OPERATIONS:
            errors.append(f"unknown operation: {operation!r}")
            continue
        entry_id = str(operation).split(":", 1)[0]
        if entry_id in seen_entries:
            errors.append(f"entry transitioned twice: {entry_id}")
        seen_entries.add(entry_id)
    cue_ids = [
        cue.get("cue_id") if isinstance(cue, dict) else None for cue in parsed.get("cue_events", [])
    ]
    if len(cue_ids) != len(set(cue_ids)):
        errors.append("cue selected twice")
    if any(cue not in CUES for cue in cue_ids):
        errors.append("unknown cue")
    return errors


async def execute(run_name: str) -> None:
    out = HERE / run_name
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-v4-") as temporary_data:
        os.environ["ROLEPLAY_DATA_DIR"] = temporary_data
        sys.path.insert(0, str(HERE))
        sys.path.insert(0, str(ROOT))

        from replay_contract import SOURCE, candidate_request_v2, source_request  # noqa: PLC0415

        from src.llm.client import call_agent  # noqa: PLC0415

        v2_request = candidate_request_v2(source_request())
        user_messages = copy.deepcopy(v2_request["messages"][1:])
        speakers = v2_request["messages"][0]["content"].split(
            '"next_speakers":{"type":"array","items":{"type":"string","enum":[', 1
        )
        if len(speakers) != 2:
            raise RuntimeError("could not locate present speaker enum")
        speaker_json = speakers[1].split("]", 1)[0]
        present_ids = json.loads("[" + speaker_json + "]")
        json_schema = schema_for(present_ids)
        messages = [{"role": "system", "content": SYSTEM}, *user_messages]

        stored = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))
        config = {
            **stored["providers"]["deepseek"],
            "provider": "deepseek",
            "language": stored["language"],
        }
        write_json(
            out / "run.json",
            {
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "script_sha256": digest(Path(__file__)),
                "preregistration_sha256": digest(HERE / "PREREGISTRATION-V4.md"),
                "started_unix": time.time(),
            },
        )
        write_json(out / "messages.json", messages)
        write_json(out / "schema.json", json_schema)

        semaphore = asyncio.Semaphore(4)
        async with httpx.AsyncClient() as client:

            async def one(repeat: int) -> dict[str, Any]:
                async with semaphore:
                    session_id = f"v4-{repeat}"
                    result: dict[str, Any] = {"repeat": repeat}
                    try:
                        parsed = await call_agent(
                            client,
                            config,
                            copy.deepcopy(messages),
                            agent="director",
                            json_schema=json_schema,
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
                        archived = out / f"V4-{repeat}.debug.jsonl"
                        archived.write_bytes(debug_path.read_bytes())
                        result["attempts"] = len(
                            debug_path.read_text(encoding="utf-8").splitlines()
                        )
                    else:
                        result["attempts"] = 0
                    write_json(out / f"V4-{repeat}.result.json", result)
                    return result

            results = await asyncio.gather(*(one(repeat) for repeat in range(RUNS)))
        write_json(out / "summary.json", results)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: v4_screen.py RUN_NAME")
    asyncio.run(execute(sys.argv[1]))
