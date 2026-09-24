from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "plans/artifacts/77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl"
SEED = 690519
RUNS_PER_ARM = 4

CLOSED_STATE = {
    "east_messenger": {
        "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
        "family": "presence",
        "state": "present",
    },
    "messenger_garrilha_fragment": {
        "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
        "family": "object",
        "state": "available",
    },
    "marta_equipment_chest": {
        "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
        "family": "container",
        "state": "open",
    },
    "east_door": {
        "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
        "family": "passage",
        "state": "ajar",
    },
}

CLOSED_STATE_V2 = {
    **CLOSED_STATE,
    "south_arch_seal": {
        "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
        "family": "structure",
        "state": "cracked",
    },
}

FAMILIES = {
    "presence": {"present", "gone", "incapacitated", "dead"},
    "passage": {"closed", "ajar", "open", "blocked", "sealed", "broken"},
    "container": {"locked", "unlocked", "open", "empty", "broken"},
    "object": {"unavailable", "available", "used", "destroyed"},
    "structure": {"intact", "cracked", "collapsed", "cleared"},
}

FIELD_TEXT = (
    '- "physical_transitions": every durable physical change in this beat. '
    "Each item has a local transition_id, one stable entry_id, the current "
    "location, one family, the exact canonical from_state (null only for a "
    "genuinely new entry), and a different to_state. Reuse entry_ids from "
    "CLOSED PHYSICAL STATE. Do not invent a synonym for an existing entry. "
    "A physical_outcome or scene_change must reference at least one "
    "transition_id; an observation may reference none only when it perceives "
    "an existing state without changing it."
)

RULE_TEXT = (
    "- CLOSED PHYSICAL STATE IS BINDING. A settled state does not happen again. "
    "Never describe an existing entry entering the same state, even with "
    "different wording. A new state is allowed: cracked may become collapsed, "
    "an open door may become blocked, and consequences may continue. Every "
    "material state change must be declared in physical_transitions and linked "
    "from its perception_event. Do not hide a state change inside an observation."
)

FIELD_TEXT_V2 = (
    '- "physical_transitions": the ONLY way physical state changes. Select an '
    "entry_id from CLOSED PHYSICAL STATE, copy its exact family and current "
    "from_state, choose a different allowed to_state, identify the responsible "
    "subject_id and every genuine witness, and add only a short sensory_detail. "
    "Never write the physical action as a sentence. New physical entities cannot "
    "be created in this beat."
)

RULE_TEXT_V2 = (
    "- CLOSED PHYSICAL STATE IS BINDING. You cannot restage or rename an entry. "
    "All physical change lives in physical_transitions. An observation is passive: "
    "it may report light, sound, smell, weather, or an already-current condition, "
    "but it may not contain an actor changing an object, structure, passage, or "
    "person. The separate renderer will turn validated transitions into prose."
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_request() -> dict[str, Any]:
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        row = json.loads(raw)
        if (
            row.get("turn_number") == 5
            and row.get("agent") == "director"
            and row.get("error") is None
        ):
            request = copy.deepcopy(row["request"])
            cfg = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
                "deepseek"
            ]
            request.pop("provider_options", None)
            request["model"] = cfg["model"]
            request["thinking"] = {"type": "disabled"}
            return request
    raise RuntimeError("accepted fb62cc2f T5 Director request not found")


def split_schema(system: str) -> tuple[str, dict[str, Any]]:
    marker = (
        "Return only one JSON object that conforms exactly to this JSON Schema. "
        "Do not add markdown or keys outside the schema:\n"
    )
    before, raw = system.split(marker, 1)
    return before + marker, json.loads(raw)


def candidate_request(original: dict[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(original)
    system = request["messages"][0]["content"]
    prefix, schema = split_schema(system)
    prefix = prefix.replace(
        '- "scene_update": object with changes',
        FIELD_TEXT + '\n- "scene_update": object with changes',
    )
    prefix = prefix.replace("RULES:\n", "RULES:\n" + RULE_TEXT + "\n")

    event = schema["properties"]["perception_events"]["items"]
    event["properties"]["transition_ids"] = {
        "type": "array",
        "items": {"type": "string"},
    }
    event["required"].append("transition_ids")
    transition = {
        "type": "object",
        "properties": {
            "transition_id": {"type": "string"},
            "entry_id": {"type": "string"},
            "location": {"type": "string"},
            "family": {"type": "string", "enum": list(FAMILIES)},
            "from_state": {"type": ["string", "null"]},
            "to_state": {"type": "string"},
        },
        "required": [
            "transition_id",
            "entry_id",
            "location",
            "family",
            "from_state",
            "to_state",
        ],
        "additionalProperties": False,
    }
    schema["properties"]["physical_transitions"] = {
        "type": "array",
        "maxItems": 6,
        "items": transition,
    }
    schema["required"].append("physical_transitions")
    request["messages"][0]["content"] = prefix + json.dumps(
        schema, ensure_ascii=False, separators=(",", ":")
    )

    user = request["messages"][1]["content"]
    state_line = "  Closed physical state (binding): " + json.dumps(
        CLOSED_STATE, ensure_ascii=False, separators=(",", ":")
    )
    physical_line = next(line for line in user.splitlines() if line.startswith("  Physical facts:"))
    user = user.replace(physical_line, physical_line + "\n" + state_line)
    stale = next(line for line in user.splitlines() if "Not in play yet" in line)
    user = user.replace(stale + "\n", "")
    request["messages"][1]["content"] = user
    return request


def candidate_request_v2(original: dict[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(original)
    system = request["messages"][0]["content"]
    prefix, schema = split_schema(system)
    prefix = prefix.replace(
        '- "scene_update": object with changes',
        FIELD_TEXT_V2 + '\n- "scene_update": object with changes',
    )
    prefix = prefix.replace("RULES:\n", "RULES:\n" + RULE_TEXT_V2 + "\n")

    event_kind = schema["properties"]["perception_events"]["items"]["properties"]["event_kind"]
    event_kind["enum"] = ["observation", "audible_speech", "identity_claim"]
    all_states = sorted(set().union(*FAMILIES.values()))
    transition = {
        "type": "object",
        "properties": {
            "entry_id": {"type": "string", "enum": list(CLOSED_STATE_V2)},
            "family": {"type": "string", "enum": list(FAMILIES)},
            "from_state": {"type": "string", "enum": all_states},
            "to_state": {"type": "string", "enum": all_states},
            "subject_id": {"type": "string"},
            "witness_ids": {"type": "array", "items": {"type": "string"}},
            "sensory_detail": {"type": "string"},
        },
        "required": [
            "entry_id",
            "family",
            "from_state",
            "to_state",
            "subject_id",
            "witness_ids",
            "sensory_detail",
        ],
        "additionalProperties": False,
    }
    schema["properties"]["physical_transitions"] = {
        "type": "array",
        "maxItems": 6,
        "items": transition,
    }
    schema["required"].append("physical_transitions")
    request["messages"][0]["content"] = prefix + json.dumps(
        schema, ensure_ascii=False, separators=(",", ":")
    )

    user = request["messages"][1]["content"]
    state_line = "  Closed physical state (binding catalogue): " + json.dumps(
        CLOSED_STATE_V2, ensure_ascii=False, separators=(",", ":")
    )
    physical_line = next(line for line in user.splitlines() if line.startswith("  Physical facts:"))
    user = user.replace(physical_line, physical_line + "\n" + state_line)
    stale = next(line for line in user.splitlines() if "Not in play yet" in line)
    user = user.replace(stale + "\n", "")
    request["messages"][1]["content"] = user
    return request


def transition_errors(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    transitions = parsed.get("physical_transitions")
    if not isinstance(transitions, list):
        return ["physical_transitions is not a list"]
    by_id: dict[str, dict[str, Any]] = {}
    for item in transitions:
        if not isinstance(item, dict):
            errors.append("non-object transition")
            continue
        tid = str(item.get("transition_id", ""))
        if not tid or tid in by_id:
            errors.append(f"duplicate or empty transition_id: {tid!r}")
            continue
        by_id[tid] = item
        entry_id = str(item.get("entry_id", ""))
        family = str(item.get("family", ""))
        before = item.get("from_state")
        after = item.get("to_state")
        current = CLOSED_STATE.get(entry_id)
        if family not in FAMILIES or after not in FAMILIES.get(family, set()):
            errors.append(f"invalid family/state for {entry_id}: {family}/{after}")
        if current is None:
            if before is not None:
                errors.append(f"new {entry_id} has non-null from_state {before!r}")
        else:
            if family != current["family"]:
                errors.append(f"family changed for {entry_id}")
            if before != current["state"]:
                errors.append(
                    f"stale from_state for {entry_id}: {before!r}, canonical {current['state']!r}"
                )
        if before == after:
            errors.append(f"null transition for {entry_id}: {before!r} -> {after!r}")

    referenced: set[str] = set()
    for event in parsed.get("perception_events", []):
        tids = event.get("transition_ids") if isinstance(event, dict) else None
        if not isinstance(tids, list):
            errors.append("event transition_ids is not a list")
            continue
        referenced.update(str(item) for item in tids)
        if event.get("event_kind") in {"physical_outcome", "scene_change"} and not tids:
            errors.append(f"{event.get('event_kind')} has no transition_ids")
    unknown = referenced - set(by_id)
    unused = set(by_id) - referenced
    if unknown:
        errors.append("unknown transition_ids: " + ", ".join(sorted(unknown)))
    if unused:
        errors.append("unreferenced transitions: " + ", ".join(sorted(unused)))
    return errors


def transition_errors_v2(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    transitions = parsed.get("physical_transitions")
    if not isinstance(transitions, list):
        return ["physical_transitions is not a list"]
    seen: set[str] = set()
    for item in transitions:
        if not isinstance(item, dict):
            errors.append("non-object transition")
            continue
        entry_id = str(item.get("entry_id", ""))
        if entry_id in seen:
            errors.append(f"entry transitioned twice: {entry_id}")
            continue
        seen.add(entry_id)
        current = CLOSED_STATE_V2.get(entry_id)
        if current is None:
            errors.append(f"unknown entry_id: {entry_id}")
            continue
        family = str(item.get("family", ""))
        before = item.get("from_state")
        after = item.get("to_state")
        if family != current["family"]:
            errors.append(f"family changed for {entry_id}")
        if before != current["state"]:
            errors.append(
                f"stale from_state for {entry_id}: {before!r}, canonical {current['state']!r}"
            )
        if after not in FAMILIES[family]:
            errors.append(f"invalid target for {entry_id}: {family}/{after}")
        if before == after:
            errors.append(f"null transition for {entry_id}: {before!r} -> {after!r}")
    return errors


def correction(errors: list[str]) -> dict[str, str]:
    state = json.dumps(CLOSED_STATE, ensure_ascii=False, separators=(",", ":"))
    return {
        "role": "user",
        "content": (
            "CORRECTION: the physical transition contract rejected your response. "
            "Return one complete replacement JSON object. Canonical CLOSED PHYSICAL STATE is "
            + state
            + ". Fix these conflicts: "
            + "; ".join(errors)
            + ". Do not repeat a settled event and do not omit transition_ids "
            "from a physical_outcome or scene_change."
        ),
    }


async def execute(run_name: str, variant: str) -> None:
    sys.path.insert(0, str(ROOT))
    from src.llm.schema import validate_json_schema

    prereg = HERE / ("PREREGISTRATION-V2.md" if variant == "v2" else "PREREGISTRATION.md")
    original = source_request()
    requests = (
        {"V2": candidate_request_v2(original)}
        if variant == "v2"
        else {"A": original, "B": candidate_request(original)}
    )
    out = HERE / run_name
    out.mkdir(parents=True, exist_ok=False)
    write_json(
        out / "run.json",
        {
            "seed": SEED,
            "source_sha256": digest(SOURCE.read_bytes()),
            "script_sha256": digest(Path(__file__).read_bytes()),
            "preregistration_sha256": digest(prereg.read_bytes()),
            "started_unix": time.time(),
        },
    )
    cfg = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
        "deepseek"
    ]
    jobs = [(arm, repeat) for arm in requests for repeat in range(RUNS_PER_ARM)]
    random.Random(SEED).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def one(arm: str, repeat: int) -> None:
        async with semaphore:
            request = copy.deepcopy(requests[arm])
            result: dict[str, Any] = {"arm": arm, "repeat": repeat, "attempts": []}
            for attempt in range(2 if arm == "B" else 1):
                label = f"{arm}-{repeat}-attempt-{attempt}"
                reqpath = out / f"{label}.request.json"
                respath = out / f"{label}.response.json"
                write_json(reqpath, request)
                started = time.monotonic()
                proc = await asyncio.create_subprocess_exec(
                    "curl",
                    "-q",
                    "--config",
                    "-",
                    "--silent",
                    "--show-error",
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    "180",
                    "--request",
                    "POST",
                    cfg["api_base"].rstrip("/") + "/chat/completions",
                    "--header",
                    "Content-Type: application/json",
                    "--data-binary",
                    "@" + str(reqpath),
                    "--output",
                    str(respath),
                    "--write-out",
                    "%{http_code}",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                auth = "header = " + json.dumps("Authorization: Bearer " + cfg["api_key"])
                stdout, stderr = await proc.communicate((auth + "\n").encode())
                attempt_result: dict[str, Any] = {
                    "http_status": stdout.decode().strip(),
                    "curl_exit": proc.returncode,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "curl_error": stderr.decode().replace(cfg["api_key"], "[REDACTED]"),
                }
                try:
                    envelope = json.loads(respath.read_text(encoding="utf-8"))
                    parsed = json.loads(envelope["choices"][0]["message"]["content"])
                    _, schema = split_schema(request["messages"][0]["content"])
                    validate_json_schema(parsed, schema)
                    attempt_result["schema_valid"] = True
                    attempt_result["parsed"] = parsed
                    if arm == "B":
                        errors = transition_errors(parsed)
                    elif arm == "V2":
                        errors = transition_errors_v2(parsed)
                    else:
                        errors = []
                    attempt_result["transition_errors"] = errors
                except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                    errors = [f"{type(exc).__name__}: {exc}"]
                    attempt_result["schema_valid"] = False
                    attempt_result["transition_errors"] = errors
                result["attempts"].append(attempt_result)
                if arm != "B" or not errors:
                    break
                if attempt == 0:
                    request["messages"].append(correction(errors))
            write_json(out / f"{arm}-{repeat}.result.json", result)
            print(f"finished {arm}-{repeat}", flush=True)

    await asyncio.gather(*(one(*job) for job in jobs))
    result_files = sorted(out.glob("*.result.json"))
    summary = [json.loads(path.read_text(encoding="utf-8")) for path in result_files]
    write_json(out / "summary.json", summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("--variant", choices=("v1", "v2"), default="v1")
    args = parser.parse_args()
    asyncio.run(execute(args.run_name, args.variant))
