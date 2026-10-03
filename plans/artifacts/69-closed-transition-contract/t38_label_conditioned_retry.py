"""Frozen full-draft T38 retry with generic versus physical-label feedback."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, cast

import authoritative_transaction_screen as transport
import closure_admission_pilot as base
import t38_manual_retry as previous

HERE = Path(__file__).resolve().parent
PREREG = HERE / "T38-LABEL-CONDITIONED-RETRY-PREREGISTRATION.md"
MANIFEST = HERE / "t38-label-conditioned-retry-manifest.json"
RUNS = HERE / "t38-label-conditioned-retry-runs"
LABEL_REPORT = (
    "A separate physical-only decision for the tracked blue gate and Téo "
    "Ventobravo's last attempted crossing returned exactly: "
    "next_aperture=closed; attempt_outcome=blocked; actor_name=Téo Ventobravo. "
    "Treat this as the physical outcome of this beat and regenerate every field "
    "as a new draft. Preserve all other supported scene events and keep every "
    "event, move, blocking statement and scene update consistent with that "
    "outcome."
)


def frozen(cfg: dict[str, Any]) -> dict[str, Any]:
    schema, old = previous.schema_and_requests(cfg)
    a = old["A"]
    b = {
        **a,
        "messages": [
            *a["messages"][:-1],
            {"role": "user", "content": previous.COMMON + LABEL_REPORT},
        ],
    }
    if a["messages"][:-1] != b["messages"][:-1]:
        raise RuntimeError("Arms differ before the last feedback message")
    if a["messages"][-1]["content"] != previous.COMMON + previous.GENERIC:
        raise RuntimeError("Generic control differs from the archived contract")
    labels = json.loads(
        (HERE / "physics-only-draft-ab-runs" / "grade.json").read_text(encoding="utf-8")
    )
    if labels["by_packet"]["F-B"]["exact_expected"] != 4:
        raise RuntimeError("Physical-only F-B label source did not pass")
    return {
        "hashes": {
            "script": base.digest(Path(__file__)),
            "prereg": base.digest(PREREG),
            "source_debug": base.digest(previous.SOURCE),
            "old_script": base.digest(Path(previous.__file__)),
            "label_grade": base.digest(HERE / "physics-only-draft-ab-runs" / "grade.json"),
        },
        "runs_per_arm": 4,
        "schema": schema,
        "requests": {"A": a, "B": b},
    }


def prepare() -> None:
    if MANIFEST.exists() or RUNS.exists():
        raise RuntimeError("Preserve existing manifest and runs")
    base.write_json(MANIFEST, frozen(base.config()))
    print("Frozen eight complete-draft retry requests")


async def one(
    arm: str,
    repeat: int,
    request: dict[str, Any],
    cfg: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    label = f"label-retry-{arm}-{repeat}"
    result: dict[str, Any] = {"arm": arm, "repeat": repeat, "valid": False}
    try:
        meta, output = await transport.curl_json(label, "director", request, cfg)
        result.update(meta=meta, output=output)
        from src.llm.schema import validate_json_schema

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
        raise RuntimeError("Frozen source, protocol, script or requests changed")
    if not cfg.get("api_key") or not cfg.get("api_base"):
        raise RuntimeError("DeepSeek configuration incomplete")
    RUNS.mkdir()
    transport.RUNS = RUNS
    base.write_json(
        RUNS / "run.json", {"manifest_sha256": base.digest(MANIFEST), "started_unix": time.time()}
    )
    semaphore = asyncio.Semaphore(4)

    async def limited(arm: str, repeat: int) -> None:
        async with semaphore:
            await one(arm, repeat, manifest["requests"][arm], cfg, manifest["schema"])

    await asyncio.gather(*(limited(arm, repeat) for arm in ("A", "B") for repeat in range(1, 5)))
    print("Completed eight frozen direct curls")


def grade() -> None:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in RUNS.glob("*.result.json")]
    ids = [row.get("meta", {}).get("response_id") for row in rows]
    outcome = {
        "calls": len(rows),
        "technical_gate": (
            len(rows) == 8
            and all(row.get("valid") for row in rows)
            and all(ids)
            and len(set(ids)) == len(ids)
        ),
        "by_arm": {
            arm: {
                "valid": sum(bool(row.get("valid")) for row in rows if row["arm"] == arm),
                "errors": [
                    {"repeat": row["repeat"], "error": row.get("error")}
                    for row in rows
                    if row["arm"] == arm and not row.get("valid")
                ],
            }
            for arm in ("A", "B")
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
