"""Isolated temporal-boundary A/B on the frozen portal requests."""

from __future__ import annotations

import asyncio
import copy
import json
import random
from pathlib import Path

import beat_only_baseline as baseline

HERE = Path(__file__).resolve().parent
OUT = HERE / "portal-events-last-ab"
OLD_STATUS = "The current beat COMPLETED (its actors and anchors all landed)."
NEW_STATUS = (
    "The current beat has covered its expected actors and anchors. "
    "Plan the next beat from the observed situation; coverage alone does not "
    "establish that the beat or act exit condition happened."
)
BOUNDARY = (
    "\nTemporal boundary: act_completed describes the current act's exit "
    "condition in events ALREADY CONFIRMED in the story context, before "
    "the next beat. An attempted action is not its successful result. "
    "Events planned in the next beat cannot complete the current act "
    "retroactively. A confirmed physical result remains established: "
    "do not treat a closed passage as still open or repeat its closure; "
    "any reopening must be a distinct new event with a cause.\n"
)


async def main() -> None:
    if OUT.exists():
        raise RuntimeError("Preserve existing A/B")
    manifest = json.loads(baseline.MANIFEST.read_text())
    assert manifest["hashes"] == baseline.source_hashes()
    cases = []
    for row in manifest["cases"]:
        if not row["fixture"]["id"].startswith("portal_"):
            continue
        for arm in ("boundary", "events_last"):
            case = copy.deepcopy(row)
            case["fixture"]["id"] += "-" + arm
            if arm in ("boundary", "events_last"):
                user = case["request"]["messages"][1]["content"]
                assert user.count(OLD_STATUS) == 1
                case["request"]["messages"][1]["content"] = user.replace(OLD_STATUS, NEW_STATUS)
                case["request"]["messages"][0]["content"] += BOUNDARY
                if arm == "events_last":
                    text = case["request"]["messages"][1]["content"]
                    start = text.index("RECENT EVENTS (oldest to newest):")
                    end = text.index("\n\nPREMISE:", start)
                    events = text[start:end]
                    case["request"]["messages"][1]["content"] = (
                        text[:start] + text[end:].lstrip("\n") + "\n\n" + events
                    )
            cases.append(case)
    OUT.mkdir()
    baseline.RUNS = OUT
    baseline.write(
        OUT / "manifest.json",
        {
            "baseline_manifest_sha256": baseline.digest(baseline.MANIFEST),
            "script_sha256": baseline.digest(Path(__file__)),
            "protocol_sha256": baseline.digest(HERE / "PORTAL-EVENTS-LAST-PREREGISTRATION.md"),
            "cases": cases,
        },
    )
    cfg = baseline.config()
    jobs = [(case, repeat) for case in cases for repeat in range(1, 5)]
    random.Random(6903).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict, repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    results = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.result.json"))]
    summary = []
    for case in cases:
        rows = [row for row in results if row["case"] == case["fixture"]["id"]]
        valid = [row for row in rows if row["valid"]]
        summary.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "act_gate_failures": [
                    row["repeat"]
                    for row in valid
                    if row["output"]["act_completed"] != case["fixture"]["required_act_completed"]
                ],
            }
        )
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
