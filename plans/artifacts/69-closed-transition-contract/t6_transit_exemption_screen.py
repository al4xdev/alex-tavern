"""Frozen direct-curl T6 transit prompt/guard bundle screen."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transaction
import closure_admission_pilot as base

sys.path.insert(0, str(base.ROOT))

from src.agents.prose import _strip_offstage_actors, build_prose_schema  # noqa: E402
from src.llm.schema import validate_json_schema  # noqa: E402
from src.models import Scene, dict_to_character  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE = base.ROOT / "plans/artifacts/repetition-battery/base-P3-r2/sessions/d5a2ccf0"
PREREG = HERE / "T6-TRANSIT-EXEMPTION-PREREGISTRATION.md"
MANIFEST = HERE / "t6-transit-exemption-manifest.json"
RUNS = HERE / "t6-transit-exemption-runs"
TRANSIT_NOTE = (
    "\n\nTEMPO DESTE BEAT: a travessia de Garran Holt é um evento confirmado "
    "presenciado por este grupo, embora ele esteja fora do grupo depois. "
    "Narre apenas a travessia confirmada do vão estreito para o corredor; "
    "não invente ação dele depois que alcançar o outro lado. A lista IN THIS "
    "VIEW descreve quem permanece aqui depois deste beat."
)


def source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = [json.loads(line) for line in (SOURCE / "debug.jsonl").read_text().splitlines()]
    director = next(
        row for row in rows if row.get("turn_number") == 6 and row.get("agent") == "director"
    )
    prose = next(row for row in rows if row.get("turn_number") == 6 and row.get("agent") == "prose")
    state = json.loads((SOURCE / "state.json").read_text())
    accepted = json.loads(director["response"])
    event = accepted["perception_events"][0]
    if (
        accepted["zone_moves"].get("C18")
        != "corredor lateral parcialmente obstruído, após o vão estreito"
        or event["subject_id"] != "Narrator"
        or "Garran atravessa" not in event["content"]
    ):
        raise RuntimeError("T6 source selection changed")
    record = next(
        row
        for row in state["history"]
        if row.get("turn_number") == 6 and row.get("content_type") == "narration"
    )
    return prose, state, record


def requests(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    prose, _, _ = source()
    logged = prose["request"]
    if cfg["model"] != prose["model"]:
        raise RuntimeError("Current model differs from archived T6 model")
    if logged["provider_options"]["thinking_enabled"] is not False:
        raise RuntimeError("Unexpected thinking setting")
    a = {
        "model": cfg["model"],
        "messages": logged["messages"],
        "max_tokens": logged["max_tokens"],
        "response_format": logged["response_format"],
        "thinking": {"type": "disabled"},
    }
    if "Always respond and write in Brazilian Portuguese." not in a["messages"][0]["content"]:
        raise RuntimeError("Archived shared-client language instruction missing")
    b = copy.deepcopy(a)
    b["messages"][-1]["content"] += TRANSIT_NOTE
    return {"A": a, "B": b}


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    bodies = requests(cfg)
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "debug": base.digest(SOURCE / "debug.jsonl"),
            "state": base.digest(SOURCE / "state.json"),
        },
        "repeats": 4,
        "requests": bodies,
        "request_hashes": {
            f"{arm}-{repeat}": hashlib.sha256(
                json.dumps(bodies[arm], ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            for arm in ("A", "B")
            for repeat in range(1, 5)
        },
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen eight T6 prose dispatches")


def filter_output(narration: str, arm: str) -> tuple[str, bool]:
    _, state, record = source()
    scene = Scene(**record["scene_snapshot"])
    chars = {cid: dict_to_character(value) for cid, value in state["characters"].items()}
    viewers = set(record["audience"])
    if arm == "B":
        chars.pop("C18")
    directly_filtered = _strip_offstage_actors(
        narration, scene, chars, state["player"]["controlled_character_id"], viewers
    )
    return directly_filtered or narration, bool(directly_filtered)


async def one(arm: str, repeat: int, request_body: dict[str, Any], cfg: dict[str, Any]) -> None:
    label = f"T6-{arm}-{repeat}"
    result: dict[str, Any] = {"label": label, "valid": False}
    try:
        meta, output = await transaction.curl_json(label, "prose", request_body, cfg)
        result.update(meta=meta, output=output)
        validate_json_schema(output, build_prose_schema()["schema"])
        result["filtered"], result["direct_filter_nonempty"] = filter_output(
            output["narration"], arm
        )
        result["valid"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    base.write_json(RUNS / f"{label}.result.json", result)


async def run() -> None:
    if not MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Prepare once and preserve calls")
    cfg = base.config()
    manifest = json.loads(MANIFEST.read_text())
    if manifest != frozen(cfg):
        raise RuntimeError("Frozen inputs changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek config incomplete")
    RUNS.mkdir()
    transaction.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    sem = asyncio.Semaphore(4)

    async def limited(arm: str, repeat: int) -> None:
        async with sem:
            await one(arm, repeat, manifest["requests"][arm], cfg)

    await asyncio.gather(*(limited(arm, repeat) for arm in ("A", "B") for repeat in range(1, 5)))
    print("Completed eight direct-curl T6 prose calls")


def grade() -> None:
    rows = [json.loads(path.read_text()) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    valid = len(rows) == 8 and all(row.get("valid") for row in rows)
    outcome = {
        "calls": len(rows),
        "valid_by_arm": {
            arm: sum(bool(row.get("valid")) for row in rows if f"-{arm}-" in row["label"])
            for arm in ("A", "B")
        },
        "technical_gate": valid and len(set(ids)) == 8 and all(ids),
        "errors": [
            {"label": row["label"], "error": row.get("error")}
            for row in rows
            if not row.get("valid")
        ],
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
