"""Change only the mandatory escalation paragraph in frozen wire requests."""

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
SOURCE = HERE / "production-manifest.json"
MANIFEST = HERE / "pressure-manifest.json"
OUT = HERE / "pressure-runs"
spec = importlib.util.spec_from_file_location("beat_baseline", BASE / "beat_only_baseline.py")
assert spec is not None and spec.loader is not None
baseline: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
OLD = (
    "- ESCALATE. Every beat must raise the stakes with a NEW external pressure\n"
    "  that physically enters or changes the scene (an arrival, a threat, a\n"
    "  discovery, a thing breaking, a deadline closing). The world does not\n"
    "  wait for anyone; danger and events advance on their own. Tension\n"
    "  must rise from act to act, never plateau in talk.\n"
)
NEW = (
    "- Follow the confirmed situation and its consequences. Keep applicable\n"
    "  unfinished business moving; an already settled result may lead to a\n"
    "  transition or a new objective without another threat. New external\n"
    "  pressure is allowed when it fits the world, but is not mandatory in\n"
    "  every beat and never overrides established facts or world directives.\n"
)


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PRESSURE-PREREGISTRATION.md",
        SOURCE,
        BASE / "beat_only_baseline.py",
        HERE / "production_roteiro_frozen.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    source = json.loads(SOURCE.read_text())
    assert (
        baseline.digest(HERE / "production_roteiro_frozen.py") == source["hashes"]["src/roteiro.py"]
    )
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in source["provider"].items())
    cases = []
    for row in source["cases"]:
        if row["fixture"]["id"] not in ("closed_stable_hall", "portal_attempt"):
            continue
        for arm in ("control", "optional_pressure"):
            case = copy.deepcopy(row)
            case["fixture"]["id"] += "-" + arm
            if arm == "optional_pressure":
                system = case["request"]["messages"][0]["content"]
                assert system.count(OLD) == 1
                case["request"]["messages"][0]["content"] = system.replace(OLD, NEW)
            cases.append(case)
    assert len(cases) == 4
    baseline.write(MANIFEST, {"hashes": hashes(), "provider": source["provider"], "cases": cases})
    print("Frozen four cells, four calls each")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if OUT.exists():
        raise RuntimeError("Preserve responses")
    assert manifest["hashes"] == hashes()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    random.Random(6912).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    rows = [json.loads(p.read_text()) for p in OUT.glob("*.result.json")]
    summary = []
    for case in manifest["cases"]:
        valid = [r for r in rows if r["case"] == case["fixture"]["id"] and r["valid"]]
        ids = {r["response_id"] for r in valid if r.get("response_id")}
        summary.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "technical_complete": len(valid) >= 3 and len(ids) == len(valid),
                "act_gate_failures": [
                    r["repeat"]
                    for r in valid
                    if r["output"]["act_completed"] != case["fixture"]["required_act_completed"]
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
