"""Frozen real-payload full-draft retry with an explicit aperture event delta."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base
import real_transaction_producer_screen as source
import t38_label_conditioned_retry as previous

from src.llm.schema import validate_json_schema

HERE = Path(__file__).resolve().parent
PREREG = HERE / "EVENT-DELTA-FEEDBACK-PREREGISTRATION.md"
MANIFEST = HERE / "event-delta-feedback-manifest.json"
RUNS = HERE / "event-delta-feedback-runs"
PACKETS = ("A", "B", "P")
P_FEEDBACK = (
    "The preceding Director draft is uncommitted. Regenerate a complete new "
    "JSON draft from the same scene. The physical outcome for the tracked "
    "main gates is: initial_aperture=ajar; next_aperture=open; "
    "aperture_delta=opening; attempt_outcome=not_applicable; actor_name=. "
    "Preserve all other supported scene events and keep every event, move, "
    "blocking statement and scene update consistent with that outcome."
)


def p_source() -> dict[str, Any]:
    directory, turn, _, _ = source.SOURCES["P"]
    rows = [json.loads(line) for line in (directory / "debug.jsonl").read_text().splitlines()]
    selected = [
        row
        for row in rows
        if row.get("turn_number") == turn
        and row.get("agent") == "director"
        and row.get("error") is None
    ]
    if len(selected) != 1 or selected[0]["attempt_number"] != 1:
        raise RuntimeError("Archived T8 Director source changed")
    return cast(dict[str, Any], selected[0])


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    older = json.loads(previous.MANIFEST.read_text(encoding="utf-8"))
    a = older["requests"]["B"]
    old_feedback = a["messages"][-1]["content"]
    marker = "next_aperture=closed;"
    if old_feedback.count(marker) != 1:
        raise RuntimeError("Old physical feedback changed")
    b_feedback = old_feedback.replace(marker, marker + " aperture_delta=none;", 1)
    b = {
        **a,
        "messages": [*a["messages"][:-1], {"role": "user", "content": b_feedback}],
    }
    if a["messages"][:-1] != b["messages"][:-1]:
        raise RuntimeError("T38 arms differ before final feedback")
    p_row = p_source()
    if p_row["model"] != cfg["model"] or a["model"] != cfg["model"]:
        raise RuntimeError("Current model differs from archived sources")
    if p_row["request"]["messages"][0] != a["messages"][0]:
        raise RuntimeError("T8 and T38 Director system contracts differ")
    present_ids = re.findall(
        r"(?m)^  ID=(C\d+) \| NAME=", p_row["request"]["messages"][1]["content"]
    )
    if len(present_ids) != 21 or len(set(present_ids)) != 21:
        raise RuntimeError("Expected 21 distinct T8 present character IDs")
    p_messages = [
        *p_row["request"]["messages"],
        {"role": "assistant", "content": p_row["response"]},
        {"role": "user", "content": P_FEEDBACK},
    ]
    p = {**a, "messages": p_messages}
    if p["response_format"] != p_row["request"]["response_format"]:
        raise RuntimeError("T8 and T38 JSON modes differ")
    if p["max_tokens"] != p_row["request"]["max_tokens"]:
        raise RuntimeError("T8 and T38 output limits differ")
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "old_manifest": base.digest(previous.MANIFEST),
            "t8_debug": base.digest(source.SOURCES["P"][0] / "debug.jsonl"),
        },
        "schema": older["schema"],
        "runs_per_packet": 4,
        "requests": {"A": a, "B": b, "P": p},
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen twelve complete-draft event-delta requests")


async def one(
    packet: str,
    repeat: int,
    request: dict[str, Any],
    cfg: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    label = f"event-delta-{packet}-{repeat}"
    result: dict[str, Any] = {"packet": packet, "repeat": repeat, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "director", request, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, schema)
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve existing calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen source, script, protocol or requests changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(packet: str, repeat: int) -> None:
        async with semaphore:
            await one(packet, repeat, manifest["requests"][packet], cfg, manifest["schema"])

    await asyncio.gather(*(limited(packet, repeat) for packet in PACKETS for repeat in range(1, 5)))
    print("Completed twelve frozen event-delta feedback curls")


def grade() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    outcome = {
        "calls": len(rows),
        "technical_gate": (
            len(rows) == 12
            and all(row.get("valid") for row in rows)
            and all(ids)
            and len(set(ids)) == len(ids)
        ),
        "by_packet": {
            packet: {
                "valid": sum(bool(row.get("valid")) for row in rows if row["packet"] == packet),
                "errors": [
                    {"repeat": row["repeat"], "error": row.get("error")}
                    for row in rows
                    if row["packet"] == packet and not row.get("valid")
                ],
            }
            for packet in PACKETS
        },
    }
    base.write_json(RUNS / "grade.json", outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    command = parser.parse_args().command
    if command == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[command])()
