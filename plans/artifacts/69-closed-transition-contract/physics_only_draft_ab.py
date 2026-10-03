"""Frozen direct-curl physical-only T38 draft-presence A/B."""

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
import real_transaction_producer_screen as prior

sys.path.insert(0, str(base.ROOT))

from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402

HERE = Path(__file__).resolve().parent
PREREG = HERE / "PHYSICS-ONLY-DRAFT-AB-PREREGISTRATION.md"
MANIFEST = HERE / "physics-only-draft-ab-manifest.json"
RUNS = HERE / "physics-only-draft-ab-runs"
PACKETS = ("F-A", "F-B", "P")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "next_aperture": {"type": "string", "enum": ["closed", "ajar", "open"]},
        "attempt_outcome": {
            "type": "string",
            "enum": ["blocked", "crossed", "not_applicable"],
        },
        "actor_name": {"type": "string", "enum": ["", "Téo Ventobravo"]},
    },
    "required": ["next_aperture", "attempt_outcome", "actor_name"],
    "additionalProperties": False,
}
SYSTEM = (
    "You decide only the physical outcome for the ONE tracked gate and, if "
    "present, the ONE tracked character's attempted crossing. Return exactly "
    "the JSON object. There is no prose, commentary, quote, event list or "
    "support field. Base the outcome on COMMITTED START and the current "
    "Director context. A proposed draft, when present, is not committed and "
    "may contradict it. A character's declared action is an attempt until "
    "the physical scene confirms its success. A gate already closed cannot "
    "close again; change its aperture only when a newly caused physical "
    "event in the supplied context or proposal establishes that change. "
    "A character already in the destination does not cross there again. "
    "If a tracked actor attempted a crossing, return their canonical public "
    "name and blocked or crossed; otherwise use not_applicable and empty "
    "actor_name. Never use an internal character ID in the answer.\n"
    "Always respond and write in Brazilian Portuguese.\n"
    "Do not use Unicode em dash (U+2014) or en dash (U+2013) anywhere in "
    "your writing; use commas, periods, or parentheses instead."
)


def packet(label: str) -> dict[str, Any]:
    source_case = "P" if label == "P" else "F"
    src = prior.source(source_case)
    value: dict[str, Any] = {
        "director_user_context": src["director_user_context"],
        "committed_start": {
            "tracked_gate_public_label": src["target"],
            "tracked_gate_aperture": src["initial_aperture"],
            "tracked_character_positions": src["initial_positions"],
            "tracked_last_action": (
                "Téo Ventobravo tenta avançar pela fresta do portão azul"
                if source_case == "F"
                else None
            ),
        },
    }
    if label in ("F-B", "P"):
        value["uncommitted_proposed_draft"] = src["accepted_draft"]
    return value


def request(label: str, cfg: dict[str, Any]) -> dict[str, Any]:
    source_case = "P" if label == "P" else "F"
    if prior.source(source_case)["model"] != cfg["model"]:
        raise RuntimeError("Current model differs from archived source")
    prepared = DeepSeekAdapter().prepare_request(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(packet(label), ensure_ascii=False)},
        ],
        None,
        {"name": "physical_only_draft_ab", "schema": SCHEMA},
        thinking_enabled=False,
    )
    return {
        "model": cfg["model"],
        "messages": prepared.messages,
        "max_tokens": 300,
        "response_format": prepared.response_format,
        **prepared.extra_payload,
    }


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    bodies = {label: request(label, cfg) for label in PACKETS}
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "prior_script": base.digest(Path(prior.__file__)),
            "F_debug": base.digest(prior.SOURCES["F"][0] / "debug.jsonl"),
            "F_state": base.digest(prior.SOURCES["F"][0] / "state.json"),
            "P_debug": base.digest(prior.SOURCES["P"][0] / "debug.jsonl"),
            "P_state": base.digest(prior.SOURCES["P"][0] / "state.json"),
            "adapter": base.digest(base.ROOT / "src/llm/adapters/deepseek.py"),
        },
        "schema": SCHEMA,
        "repeats": 4,
        "requests": bodies,
        "request_hashes": {
            f"{label}-{repeat}": hashlib.sha256(
                json.dumps(bodies[label], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            for label in PACKETS
            for repeat in range(1, 5)
        },
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve the existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen twelve physical-only A/B dispatches")


async def one(label: str, repeat: int, body: dict[str, Any], cfg: dict[str, Any]) -> None:
    call_label = f"physics-only-{label}-{repeat}"
    result: dict[str, Any] = {"label": call_label, "packet": label, "valid": False}
    try:
        meta, output = await transport.curl_json(call_label, "physical", body, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, SCHEMA)
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{call_label}.result.json", result)


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

    async def limited(label: str, repeat: int) -> None:
        async with sem:
            await one(label, repeat, manifest["requests"][label], cfg)

    await asyncio.gather(*(limited(label, repeat) for label in PACKETS for repeat in range(1, 5)))
    print("Completed twelve physical-only direct curls")


def grade() -> None:
    rows = [json.loads(path.read_text()) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    expected = {
        "F-A": {
            "next_aperture": "closed",
            "attempt_outcome": "blocked",
            "actor_name": "Téo Ventobravo",
        },
        "F-B": {
            "next_aperture": "closed",
            "attempt_outcome": "blocked",
            "actor_name": "Téo Ventobravo",
        },
        "P": {"next_aperture": "open", "attempt_outcome": "not_applicable", "actor_name": ""},
    }
    outcome = {
        "calls": len(rows),
        "technical_gate": (
            len(rows) == 12
            and all(row.get("valid") for row in rows)
            and len(ids) == len(set(ids))
            and all(ids)
        ),
        "by_packet": {
            label: {
                "valid": sum(bool(row.get("valid")) for row in rows if row["packet"] == label),
                "exact_expected": sum(
                    row.get("output") == expected[label]
                    for row in rows
                    if row["packet"] == label and row.get("valid")
                ),
                "outputs": [
                    {"label": row["label"], "output": row.get("output"), "error": row.get("error")}
                    for row in rows
                    if row["packet"] == label
                ],
            }
            for label in PACKETS
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
