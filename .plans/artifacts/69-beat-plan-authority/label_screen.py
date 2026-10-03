"""Single-payload labeling screen; no production changes."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "plans/artifacts/69-beat-only-baseline"
SOURCE = BASE / "portal-events-last-ab/manifest.json"
OUT = HERE / "runs"
MANIFEST = HERE / "manifest.json"
spec = importlib.util.spec_from_file_location("beat_baseline", BASE / "beat_only_baseline.py")
assert spec is not None and spec.loader is not None
baseline: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    frozen = json.loads(baseline.MANIFEST.read_text())
    assert frozen["hashes"] == baseline.source_hashes()
    source = next(
        row
        for row in json.loads(SOURCE.read_text())["cases"]
        if row["fixture"]["id"] == "portal_closed-events_last"
    )
    cases = []
    for arm in ("control", "plan_label"):
        case = copy.deepcopy(source)
        case["fixture"]["id"] = "portal_closed-" + arm
        if arm == "plan_label":
            text = case["request"]["messages"][1]["content"]
            assert text.count("CURRENT BEAT (") == 1
            case["request"]["messages"][1]["content"] = text.replace(
                "CURRENT BEAT (",
                "PREVIOUS BEAT PLAN (guidance, not current world facts) (",
            )
        cases.append(case)
    cfg = baseline.config()
    baseline.write(
        MANIFEST,
        {
            "source_sha256": baseline.digest(SOURCE),
            "script_sha256": baseline.digest(Path(__file__)),
            "protocol_sha256": baseline.digest(HERE / "PREREGISTRATION.md"),
            "baseline_hashes": baseline.source_hashes(),
            "provider": {key: cfg[key] for key in ("model", "language", "api_base")},
            "cases": cases,
        },
    )
    print("Frozen 2 arms, 4 calls each")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if OUT.exists():
        raise RuntimeError("Preserve existing responses")
    assert manifest["script_sha256"] == baseline.digest(Path(__file__))
    assert manifest["protocol_sha256"] == baseline.digest(HERE / "PREREGISTRATION.md")
    assert manifest["source_sha256"] == baseline.digest(SOURCE)
    assert manifest["baseline_hashes"] == baseline.source_hashes()
    cfg = baseline.config()
    assert all(cfg[key] == value for key, value in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    random.Random(6906).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    rows = [json.loads(p.read_text()) for p in OUT.glob("*.result.json")]
    summary = []
    for case in manifest["cases"]:
        valid = [row for row in rows if row["case"] == case["fixture"]["id"] and row["valid"]]
        ids = {row["response_id"] for row in valid if row.get("response_id")}
        summary.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "technical_complete": len(valid) >= 3 and len(ids) == len(valid),
                "act_gate_failures": [
                    row["repeat"] for row in valid if not row["output"]["act_completed"]
                ],
            }
        )
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    if parser.parse_args().command == "prepare":
        prepare()
    else:
        asyncio.run(run())
