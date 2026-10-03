"""Fresh fixed replication, preserving the incomplete prior screen."""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path

import beat_only_baseline as baseline

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "portal-events-last-ab/manifest.json"
OUT = HERE / "portal-replication"


async def main() -> None:
    if OUT.exists():
        raise RuntimeError("Preserve replication")
    original = json.loads(baseline.MANIFEST.read_text())
    assert original["hashes"] == baseline.source_hashes()
    cfg = baseline.config()
    assert all(cfg[key] == original[key] for key in ("model", "language", "api_base"))
    cases = [
        row
        for row in json.loads(SOURCE.read_text())["cases"]
        if row["fixture"]["id"].endswith("-events_last")
    ]
    assert len(cases) == 3
    OUT.mkdir()
    baseline.RUNS = OUT
    baseline.write(
        OUT / "manifest.json",
        {
            "source_manifest_sha256": baseline.digest(SOURCE),
            "script_sha256": baseline.digest(Path(__file__)),
            "protocol_sha256": baseline.digest(HERE / "PORTAL-REPLICATION-PREREGISTRATION.md"),
            "cases": cases,
        },
    )
    jobs = [(case, repeat) for case in cases for repeat in range(1, 5)]
    random.Random(6904).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict, repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    rows = [json.loads(p.read_text()) for p in OUT.glob("*.result.json")]
    summary = []
    for case in cases:
        valid = [row for row in rows if row["case"] == case["fixture"]["id"] and row["valid"]]
        ids = {row.get("response_id") for row in valid if row.get("response_id")}
        failures = [
            row["repeat"]
            for row in valid
            if row["output"]["act_completed"] != case["fixture"]["required_act_completed"]
        ]
        summary.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "technical_complete": len(valid) >= 3 and len(ids) == len(valid),
                "act_gate_failures": failures,
            }
        )
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
