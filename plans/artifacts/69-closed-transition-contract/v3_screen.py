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
SCHEMA_MARKER = (
    "Return only one JSON object that conforms exactly to this JSON Schema. "
    "Do not add markdown or keys outside the schema:\n"
)

EVENT_DESCRIPTION_V2 = (
    '  {"event_kind": one of "observation" | "audible_speech" | '
    '"identity_claim" |\n'
    '  "physical_outcome" | "scene_change"; "subject_id": the acting '
    "character's\n"
    '  ID (or "Narrator" for environmental events); "content": ONE short sentence\n'
    "  describing the event exactly as a witness would perceive it (no inner\n"
    '  thoughts, no facts a witness could not sense), and for "audible_speech"\n'
    "  the fact being made public, in reported form, never the spoken words;"
)
EVENT_DESCRIPTION_V3 = (
    '  {"event_kind": one of "observation" | "audible_speech" | '
    '"identity_claim";\n'
    '  "subject_id": the perceived character\'s ID (or "Narrator" for '
    "environmental\n"
    '  observations); "content": ONE short sentence describing the passive event\n'
    "  exactly as a witness would perceive it (no inner thoughts, no facts a witness\n"
    "  could not sense, and no change to catalogued durable state), and for\n"
    '  "audible_speech" the fact being made public, in reported form, never the\n'
    "  spoken words;"
)
SCENE_UPDATE_V2 = """- "scene_update": object with changes to the current scene (e.g.,
  {"location": "Old Watchtower", "door": "open"}). "location" and
  "time_of_day" are reserved Scene fields. Every other key is a physical
  fact for the current location. Reuse one stable snake_case key for the
  same fact; never create simultaneous synonyms such as weather and
  weather_outside. Use null if nothing changed.
  Set a key's value to null to remove that fact from the scene entirely
  (e.g., an item that no longer exists)."""
SCENE_UPDATE_V3 = """- "scene_update": MUST be null in this screen. Catalogued durable physical
  change belongs only in physical_transitions; do not restate it under an alias."""
TRANSITION_DESCRIPTION_V2 = (
    '- "physical_transitions": the ONLY way physical state changes. Select an '
    "entry_id from CLOSED PHYSICAL STATE, copy its exact family and current "
    "from_state, choose a different allowed to_state, identify the responsible "
    "subject_id and every genuine witness, and add only a short sensory_detail. "
    "Never write the physical action as a sentence. New physical entities cannot "
    "be created in this beat."
)
TRANSITION_DESCRIPTION_V3 = (
    '- "physical_transitions": the ONLY way a CATALOGUED durable state changes. '
    "Select one allowed atomic operation that already binds the entry, current "
    "state and different target state. Name its cause, every genuine witness and "
    "one short sensory detail. Never repeat or paraphrase that state change in an "
    "observation or scene_update. New durable entities cannot be created this beat."
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_v3_request() -> tuple[dict[str, Any], set[str]]:
    from replay_contract import (  # noqa: PLC0415
        CLOSED_STATE_V2,
        FAMILIES,
        candidate_request_v2,
        source_request,
        split_schema,
    )

    request = candidate_request_v2(source_request())
    prefix, schema = split_schema(request["messages"][0]["content"])
    prefix = prefix.replace(EVENT_DESCRIPTION_V2, EVENT_DESCRIPTION_V3)
    prefix = prefix.replace(SCENE_UPDATE_V2, SCENE_UPDATE_V3)
    prefix = prefix.replace(TRANSITION_DESCRIPTION_V2, TRANSITION_DESCRIPTION_V3)
    if "physical_outcome" in prefix or "scene_change" in prefix:
        raise RuntimeError("V3 event prose still names a schema-forbidden event kind")
    if SCENE_UPDATE_V3 not in prefix or TRANSITION_DESCRIPTION_V3 not in prefix:
        raise RuntimeError("V3 prompt replacement did not land")

    operations = {
        f"{entry_id}:{current['state']}->{target}"
        for entry_id, current in CLOSED_STATE_V2.items()
        for target in FAMILIES[current["family"]]
        if target != current["state"]
    }
    speakers = schema["properties"]["next_speakers"]["items"]["enum"]
    schema["properties"]["scene_update"] = {"type": "null"}
    schema["properties"]["physical_transitions"] = {
        "type": "array",
        "maxItems": len(CLOSED_STATE_V2),
        "items": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": sorted(operations)},
                "cause_id": {"type": "string", "enum": ["Narrator", *speakers]},
                "witness_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": speakers},
                },
                "sensory_detail": {"type": "string"},
            },
            "required": ["operation", "cause_id", "witness_ids", "sensory_detail"],
            "additionalProperties": False,
        },
    }
    request["messages"][0]["content"] = prefix + json.dumps(
        schema, ensure_ascii=False, separators=(",", ":")
    )
    return request, operations


def local_errors(parsed: dict[str, Any], operations: set[str]) -> list[str]:
    transitions = parsed.get("physical_transitions")
    if not isinstance(transitions, list):
        return ["physical_transitions is not a list"]
    errors: list[str] = []
    seen: set[str] = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            errors.append("non-object transition")
            continue
        operation = transition.get("operation")
        if operation not in operations:
            errors.append(f"unknown operation: {operation!r}")
            continue
        entry_id = str(operation).split(":", 1)[0]
        if entry_id in seen:
            errors.append(f"entry transitioned twice: {entry_id}")
        seen.add(entry_id)
    return errors


async def execute(run_name: str) -> None:
    out = HERE / run_name
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-v3-") as temporary_data:
        os.environ["ROLEPLAY_DATA_DIR"] = temporary_data
        sys.path.insert(0, str(HERE))
        sys.path.insert(0, str(ROOT))

        request, operations = build_v3_request()
        from replay_contract import SOURCE, split_schema  # noqa: PLC0415

        from src.llm.client import call_agent  # noqa: PLC0415

        messages = copy.deepcopy(request["messages"])
        before_schema, schema = split_schema(messages[0]["content"])
        messages[0]["content"] = before_schema.removesuffix(SCHEMA_MARKER).rstrip()
        json_schema = {"name": "narrator_turn", "schema": schema}

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
                "preregistration_sha256": digest(HERE / "PREREGISTRATION-V3.md"),
                "request_sha256": hashlib.sha256(
                    json.dumps(request, ensure_ascii=False, sort_keys=True).encode()
                ).hexdigest(),
                "started_unix": time.time(),
            },
        )
        write_json(out / "request.json", request)

        semaphore = asyncio.Semaphore(4)
        async with httpx.AsyncClient() as client:

            async def one(repeat: int) -> dict[str, Any]:
                async with semaphore:
                    session_id = f"v3-{repeat}"
                    result: dict[str, Any] = {"repeat": repeat}
                    try:
                        parsed = await call_agent(
                            client,
                            config,
                            copy.deepcopy(messages),
                            agent="director",
                            json_schema=json_schema,
                            max_tokens=int(config["max_tokens_narrator"]),
                            session_id=session_id,
                            turn_number=5,
                        )
                        result["client_valid"] = True
                        result["parsed"] = parsed
                        result["transition_errors"] = local_errors(parsed, operations)
                    except ValueError as exc:
                        result["client_valid"] = False
                        result["error"] = str(exc)

                    debug_path = Path(temporary_data) / "sessions" / session_id / "debug.jsonl"
                    if debug_path.exists():
                        archived = out / f"V3-{repeat}.debug.jsonl"
                        archived.write_bytes(debug_path.read_bytes())
                        result["attempts"] = len(
                            debug_path.read_text(encoding="utf-8").splitlines()
                        )
                    else:
                        result["attempts"] = 0
                    write_json(out / f"V3-{repeat}.result.json", result)
                    return result

            results = await asyncio.gather(*(one(repeat) for repeat in range(RUNS)))
        write_json(out / "summary.json", results)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: v3_screen.py RUN_NAME")
    asyncio.run(execute(sys.argv[1]))
