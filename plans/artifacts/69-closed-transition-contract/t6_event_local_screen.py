"""Frozen, direct-curl T6 event-local reader-unit candidate screen."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base

sys.path.insert(0, str(base.ROOT))

from src.agents.prose import PROSE_SYSTEM  # noqa: E402
from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE = base.ROOT / "plans/artifacts/repetition-battery/base-P3-r2/sessions/d5a2ccf0"
PREREG = HERE / "T6-EVENT-LOCAL-PREREGISTRATION.md"
MANIFEST = HERE / "t6-event-local-manifest.json"
RUNS = HERE / "t6-event-local-runs"
MARKER = "CONFIRMED EVENTS OF THIS BEAT (narrate exactly these):\n"
FLOOR = "- Narrate at least 150 words; a beat deserves full paragraphs.\n"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"unit": {"type": "string"}},
    "required": ["unit"],
    "additionalProperties": False,
}
TRANSIT_NOTE = (
    "TRAVESSIA CONFIRMADA E PRESENCIADA: o instrutor Garran Holt atravessa "
    "o vão estreito da origem para o corredor lateral parcialmente obstruído. "
    "Este grupo testemunha a travessia; depois que ele chega ao corredor, "
    "não narre nova ação dele nem condições do corredor que não constem do evento."
)


def source() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = [json.loads(line) for line in (SOURCE / "debug.jsonl").read_text().splitlines()]
    director = next(
        row for row in rows if row.get("turn_number") == 6 and row.get("agent") == "director"
    )
    prose = next(row for row in rows if row.get("turn_number") == 6 and row.get("agent") == "prose")
    accepted = json.loads(director["response"])
    events = [
        event for event in accepted["perception_events"] if event["event_kind"] != "audible_speech"
    ]
    state = json.loads((SOURCE / "state.json").read_text())
    narration = next(
        row
        for row in state["history"]
        if row.get("turn_number") == 6 and row.get("content_type") == "narration"
    )
    viewers = set(narration["audience"])
    if (
        len(events) != 3
        or not all(viewers & set(event["witness_ids"]) for event in events)
        or accepted["zone_moves"].get("C18")
        != "corredor lateral parcialmente obstruído, após o vão estreito"
        or events[0]["subject_id"] != "Narrator"
        or "Garran atravessa" not in events[0]["content"]
    ):
        raise RuntimeError("T6 source no longer matches the pre-registration")
    return prose, events


def request(event_index: int, cfg: dict[str, Any]) -> dict[str, Any]:
    prose, events = source()
    logged = prose["request"]
    if cfg["model"] != prose["model"] or logged["provider_options"]["thinking_enabled"]:
        raise RuntimeError("Provider settings differ from archived T6")
    if PROSE_SYSTEM.count(FLOOR) != 1:
        raise RuntimeError("Cannot remove exactly one whole-beat prose floor")
    system = PROSE_SYSTEM.replace(FLOOR, "") + (
        "- Produce only this event's reader-ready prose unit, 35 to 90 words. "
        "Do not narrate another event, a later action, a new physical outcome, "
        "or a fact inaccessible to the origin witnesses. Do not write a list.\n"
    )
    system += (
        "- Always respond and write in Brazilian Portuguese.\n"
        "- Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in "
        "your writing; use commas, periods, or parentheses instead."
    )
    old_user = logged["messages"][-1]["content"]
    if old_user.count(MARKER) != 1:
        raise RuntimeError("Archived prose event block is not unique")
    prefix = old_user.split(MARKER, 1)[0]
    user = prefix + "ONE CONFIRMED EVENT OF THIS BEAT (render only this):\n"
    user += f"  - ({events[event_index]['event_kind']}) {events[event_index]['content']}"
    if event_index == 0:
        user += "\n\n" + TRANSIT_NOTE
    adapter = DeepSeekAdapter()
    prepared = adapter.prepare_request(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        None,
        {"name": "event_unit", "schema": SCHEMA},
        thinking_enabled=False,
    )
    if not any(
        "Always respond and write in Brazilian Portuguese." in m["content"]
        for m in prepared.messages
    ):
        raise RuntimeError("Missing shared-client language instruction")
    return {
        "model": cfg["model"],
        "messages": prepared.messages,
        "max_tokens": 1000,
        "response_format": prepared.response_format,
        **prepared.extra_payload,
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    requests = {str(index): request(index, cfg) for index in range(3)}
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "source_debug": base.digest(SOURCE / "debug.jsonl"),
            "source_state": base.digest(SOURCE / "state.json"),
            "prose_builder": base.digest(base.ROOT / "src/agents/prose.py"),
            "adapter": base.digest(base.ROOT / "src/llm/adapters/deepseek.py"),
        },
        "repeats": 4,
        "requests": requests,
        "request_hashes": {
            f"{repeat}-{index}": hashlib.sha256(
                json.dumps(requests[str(index)], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            for repeat in range(1, 5)
            for index in range(3)
        },
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing T6 event-local manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen twelve event-local T6 dispatches")


async def one(repeat: int, index: int, body: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"T6-event-local-{repeat}-{index}"
    result: dict[str, Any] = {"label": label, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "unit", body, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, SCHEMA)
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve all calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text())
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek config incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    sem = asyncio.Semaphore(4)

    async def limited(repeat: int, index: int) -> None:
        async with sem:
            await one(repeat, index, manifest["requests"][str(index)], cfg)

    await asyncio.gather(*(limited(repeat, index) for repeat in range(1, 5) for index in range(3)))
    print("Completed twelve direct-curl event-unit calls")


def grade() -> None:
    rows = [json.loads(path.read_text()) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    valid = len(rows) == 12 and all(row.get("valid") for row in rows)
    assemblies = []
    for repeat in range(1, 5):
        units = [
            next((row for row in rows if row["label"] == f"T6-event-local-{repeat}-{index}"), None)
            for index in range(3)
        ]
        assemblies.append(
            {
                "repeat": repeat,
                "unit_labels": [unit["label"] if unit else None for unit in units],
                "narration": "\n\n".join(
                    unit["output"]["unit"].strip() for unit in units if unit and unit.get("valid")
                ),
                "complete": all(unit and unit.get("valid") for unit in units),
            }
        )
    outcome = {
        "calls": len(rows),
        "valid_calls": sum(bool(row.get("valid")) for row in rows),
        "technical_gate": valid and len(set(ids)) == 12 and all(ids),
        "errors": [
            {"label": row["label"], "error": row.get("error")}
            for row in rows
            if not row.get("valid")
        ],
        "assemblies": assemblies,
    }
    base.write_json(RUNS / "grade.json", outcome)
    print(json.dumps({k: v for k, v in outcome.items() if k != "assemblies"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
