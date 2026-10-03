"""One-call, three-unit direct-curl feasibility screen for archived T6."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base
import t6_event_local_screen as previous

sys.path.insert(0, str(base.ROOT))

from src.agents.prose import PROSE_SYSTEM  # noqa: E402
from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402

HERE = Path(__file__).resolve().parent
PREREG = HERE / "T6-JOINT-UNITS-PREREGISTRATION.md"
MANIFEST = HERE / "t6-joint-units-manifest.json"
RUNS = HERE / "t6-joint-units-runs"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "units": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 3,
            "maxItems": 3,
        }
    },
    "required": ["units"],
    "additionalProperties": False,
}


def request(cfg: dict[str, Any]) -> dict[str, Any]:
    prose, events = previous.source()
    logged = prose["request"]
    if cfg["model"] != prose["model"] or logged["provider_options"]["thinking_enabled"]:
        raise RuntimeError("Provider settings differ from archived T6")
    if PROSE_SYSTEM.count(previous.FLOOR) != 1:
        raise RuntimeError("Cannot remove exactly one whole-beat prose floor")
    system = PROSE_SYSTEM.replace(previous.FLOOR, "") + (
        "- See every event before writing. Return exactly three prose units in "
        "the same order, one for each numbered event. Keep each unit's factual "
        "claims within its own event and visible prior scene; use the whole beat "
        "to coordinate rhythm and avoid repeated images. Do not omit a source "
        "clause, narrate a later event early, or add a physical outcome. Each "
        "unit should be 35 to 90 words and read as literary Brazilian "
        "Portuguese prose, not a list. Each unit must make sense on its own "
        "if another unit is omitted for a different viewer: do not rely on "
        "an antecedent or sentence fragment in another unit.\n"
        "- Always respond and write in Brazilian Portuguese.\n"
        "- Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in "
        "your writing; use commas, periods, or parentheses instead."
    )
    old_user = logged["messages"][-1]["content"]
    if old_user.count(previous.MARKER) != 1:
        raise RuntimeError("Archived prose event block is not unique")
    prefix = old_user.split(previous.MARKER, 1)[0]
    lines = [
        f"  {index}. ({event['event_kind']}) {event['content']}"
        for index, event in enumerate(events, 1)
    ]
    user = (
        prefix
        + "THREE CONFIRMED EVENTS OF THIS BEAT (one output unit per event):\n"
        + "\n".join(lines)
        + "\n\n"
        + previous.TRANSIT_NOTE
    )
    prepared = DeepSeekAdapter().prepare_request(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        None,
        {"name": "joint_event_units", "schema": SCHEMA},
        thinking_enabled=False,
    )
    return {
        "model": cfg["model"],
        "messages": prepared.messages,
        "max_tokens": 2500,
        "response_format": prepared.response_format,
        **prepared.extra_payload,
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "source_debug": base.digest(previous.SOURCE / "debug.jsonl"),
            "source_state": base.digest(previous.SOURCE / "state.json"),
            "previous_script": base.digest(Path(previous.__file__)),
            "prose_builder": base.digest(base.ROOT / "src/agents/prose.py"),
            "adapter": base.digest(base.ROOT / "src/llm/adapters/deepseek.py"),
        },
        "repeats": 4,
        "schema": SCHEMA,
        "request": request(cfg),
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve any existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen four one-call T6 joint-unit requests")


async def one(repeat: int, body: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"T6-joint-units-{repeat}"
    result: dict[str, Any] = {"label": label, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "units", body, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, SCHEMA)
        if any(not unit.strip() for unit in output["units"]):
            raise ValueError("Empty unit")
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve all calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("Provider config incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    await asyncio.gather(*(one(repeat, manifest["request"], cfg) for repeat in range(1, 5)))
    print("Completed four direct-curl joint-unit calls")


def grade() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    rows.sort(key=lambda row: row["label"])
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    result = {
        "calls": len(rows),
        "valid_calls": sum(bool(row.get("valid")) for row in rows),
        "technical_gate": (
            len(rows) == 4
            and all(row.get("valid") for row in rows)
            and len(set(ids)) == 4
            and all(ids)
        ),
        "errors": [
            {"label": row["label"], "error": row.get("error")}
            for row in rows
            if not row.get("valid")
        ],
        "assemblies": [
            {
                "label": row["label"],
                "units": row["output"]["units"],
                "narration": "\n\n".join(unit.strip() for unit in row["output"]["units"]),
            }
            for row in rows
            if row.get("valid")
        ],
    }
    base.write_json(RUNS / "grade.json", result)
    print(
        json.dumps({key: value for key, value in result.items() if key != "assemblies"}, indent=2)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
