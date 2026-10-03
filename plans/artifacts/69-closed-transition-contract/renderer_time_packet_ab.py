"""Frozen direct-curl renderer packet experiment; does not alter runtime."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transaction
import closure_admission_pilot as base

sys.path.insert(0, str(base.ROOT))

HERE = Path(__file__).resolve().parent
PREREG = HERE / "RENDERER-TIME-PACKET-PREREGISTRATION.md"
SOURCE = HERE / "authoritative-transaction-v2-runs"
MANIFEST = HERE / "renderer-time-packet-manifest.json"
RUNS = HERE / "renderer-time-packet-runs"
CASES = ["closed_blocked", "open_cross", "reopen_cross", "seal_maintenance"]
ROSTER = re.compile(
    r"IN THIS VIEW \(the only people whose PRESENT actions you may narrate; "
    r"others may be remembered as past events, never shown acting now\):\n"
    r"  [^\n]+\n\n"
)
STILLNESS = (
    "  hesitation to answer, or non-response — and never present someone's\n"
    "  stillness or not-moving as an event. Omit anyone the events give\n"
    "  nothing new to do.\n"
)
FLOOR = "- Narrate at least 150 words; a beat deserves full paragraphs.\n"


def source_files() -> list[Path]:
    return [
        item
        for case in CASES
        for item in [
            SOURCE / f"{case}-1.result.json",
            SOURCE / f"{case}-1.prose.request.json",
        ]
    ]


def b_request(a: dict[str, Any], case: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(a)
    system = body["messages"][0]["content"]
    user = body["messages"][1]["content"]
    if system.count(STILLNESS) != 1 or system.count(FLOOR) != 1:
        raise ValueError("Unexpected production system text")
    system = system.replace(
        STILLNESS,
        "  hesitation to answer, or non-response. Omit anyone the confirmed\n"
        "  events give nothing new to do; a confirmed continuing physical\n"
        "  condition may be observed without inventing a new action.\n",
    ).replace(FLOOR, "- Use only the space the confirmed material supports.\n")
    roster = ROSTER.search(user)
    if roster is None:
        raise ValueError("Expected one final-state roster")
    replacement = "IN THIS VIEW: narrate only confirmed events witnessed in the salon. "
    if derived["liora_side"] == "tunnel":
        replacement += (
            "Liora's crossing is witnessed during this beat, although she is absent "
            "from the salon afterward. Do not narrate any new action by her in the "
            "tunnel or outside this view after that crossing. "
        )
    replacement += "Do not invent actions for anyone.\n"
    occupants = ["Link", "Garran Holt", "Mirella Valecourt"]
    if derived["liora_side"] == "salon":
        occupants.append("Liora Celestria")
    replacement += "  Current salon occupants: " + ", ".join(occupants) + "\n\n"
    user = user[: roster.start()] + replacement + user[roster.end() :]
    if derived["liora_side"] == "tunnel":
        anchor = "  Mirella Valecourt: pessoa na cena | wearing: roupas comuns\n"
        if user.count(anchor) != 1:
            raise ValueError("Unexpected cast")
        user = user.replace(
            anchor,
            anchor + "  Liora Celestria: pessoa na cena | wearing: roupas comuns\n",
        )
        user = user.replace(
            "CAST (visible appearance only):",
            "CAST (current occupants and a witnessed event actor; appearance only):",
        )
    aperture = {"open": "aberto", "closed": "fechado"}
    seal = {"present": "presente", "absent": "ausente"}
    before = (
        "VISIBLE PHYSICAL TIMELINE (the confirmed events below occur between these states; "
        "the AFTER position does not erase a witnessed crossing):\n"
        f"  BEFORE: portão azul {aperture[case['initial_aperture']]}; selo de gelo "
        f"{seal[case['initial_ice_seal']]}; Liora Celestria no "
        f"{'salão' if case['initial_positions']['Liora Celestria'] == 'salon' else 'túnel'}.\n"
        f"  AFTER: portão azul {aperture[derived['aperture']]}; selo de gelo "
        f"{seal[derived['ice_seal']]}; Liora Celestria no "
        f"{'salão' if derived['liora_side'] == 'salon' else 'túnel'}.\n\n"
    )
    anchor = "CONFIRMED EVENTS OF THIS BEAT (narrate exactly these):\n"
    if user.count(anchor) != 1:
        raise ValueError("Unexpected transcript anchor")
    user = user.replace(anchor, before + anchor)
    body["messages"][0]["content"] = system
    body["messages"][1]["content"] = user
    return body


def frozen() -> dict[str, Any]:
    source_hashes = {path.name: base.digest(path) for path in source_files()}
    requests: dict[str, dict[str, Any]] = {}
    for case in transaction.cases():
        name = case["id"]
        result = json.loads((SOURCE / f"{name}-1.result.json").read_text(encoding="utf-8"))
        a = json.loads((SOURCE / f"{name}-1.prose.request.json").read_text(encoding="utf-8"))
        if result["derived"]["operations"] != case["expected_operations"]:
            raise ValueError("Frozen Director operations changed")
        requests[name] = {"A": a, "B": b_request(a, case, result["derived"])}
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "cases": base.digest(transaction.CASES),
            "source": source_hashes,
        },
        "repeats": 4,
        "requests": requests,
        "request_hashes": {
            f"{case}-{arm}-{repeat}": hashlib.sha256(
                json.dumps(requests[case][arm], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            for case in CASES
            for arm in ("A", "B")
            for repeat in range(1, 5)
        },
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Existing manifest or run")
    base.write_json(MANIFEST, frozen())
    print("Frozen 8 request bodies, each repeated four times")


async def one(label: str, request_body: dict[str, Any], cfg: dict[str, Any]) -> None:
    result: dict[str, Any] = {"label": label, "valid": False}
    try:
        meta, output = await transaction.curl_json(label, "prose", request_body, cfg)
        result.update(meta=meta, output=output)
        from src.agents.prose import build_prose_schema
        from src.llm.schema import validate_json_schema

        validate_json_schema(output, build_prose_schema()["schema"])
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve runs")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest != frozen():
        raise RuntimeError("Frozen request or source changed")
    cfg = base.config()
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek config incomplete")
    RUNS.mkdir()
    transaction.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(case: str, arm: str, repeat: int) -> None:
        async with semaphore:
            await one(f"{case}-{arm}-{repeat}", manifest["requests"][case][arm], cfg)

    await asyncio.gather(
        *(
            limited(case, arm, repeat)
            for case in CASES
            for arm in ("A", "B")
            for repeat in range(1, 5)
        )
    )
    print("Completed 32 fresh prose calls")


def grade() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    output = {
        "calls": len(rows),
        "valid_by_arm": {
            arm: sum(bool(row.get("valid")) for row in rows if f"-{arm}-" in row["label"])
            for arm in ("A", "B")
        },
        "b_technical_gate": len(rows) == 32
        and all(row.get("valid") for row in rows if "-B-" in row["label"]),
        "errors": [
            {"label": row["label"], "error": row.get("error")}
            for row in rows
            if not row.get("valid")
        ],
    }
    base.write_json(RUNS / "grade.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade"))
    action = parser.parse_args().command
    if action == "run":
        asyncio.run(run())
    else:
        cast(Any, globals()[action])()
