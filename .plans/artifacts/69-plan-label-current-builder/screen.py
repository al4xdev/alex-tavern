"""Fresh label-only curl comparison using the current production builder."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py"
spec = importlib.util.spec_from_file_location("label_baseline", BASE)
assert spec is not None and spec.loader is not None
baseline: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
MANIFEST = HERE / "manifest.json"


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        ROOT / "src/roteiro.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/prompting.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve existing manifest")
    cfg = baseline.config()
    cases = []
    for fixture in baseline.fixtures():
        if fixture["id"] not in {"portal_attempt", "portal_closed", "portal_left"}:
            continue
        early, late = baseline.game_for(fixture, False), baseline.game_for(fixture, True)
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        game = early if first.action else late
        assert decision.action is not None
        scope = "act" if decision.action == "replan_act" else "beat"
        control = await baseline.captured_request(game, decision.reason, scope, cfg)
        candidate = copy.deepcopy(control)
        changes = 0
        for msg in candidate["messages"]:
            changes += msg["content"].count("CURRENT BEAT (")
            msg["content"] = msg["content"].replace("CURRENT BEAT (", "PREVIOUS BEAT PLAN (")
        assert changes == 1
        for arm, request in (("control", control), ("previous_label", candidate)):
            f = copy.deepcopy(fixture)
            f["id"] += "-" + arm
            cases.append(
                {
                    "fixture": f,
                    "arm": arm,
                    "request": request,
                    "decision": asdict(decision),
                    "canonical_scene": asdict(game.scene),
                    "schema": baseline.build_next_beat_schema(scope)["schema"],
                }
            )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "provider": {k: cfg[k] for k in ("model", "api_base", "language")},
        },
    )
    print("Frozen six cells; only the previous-plan label differs")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    jobs = [(case, rep) for case in manifest["cases"] for rep in range(1, 5)]
    random.Random(691003).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], rep: int) -> None:
        async with semaphore:
            await baseline.call_one(case, rep, cfg)

    await asyncio.gather(*(limited(case, rep) for case, rep in jobs))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    grade = []
    for case in manifest["cases"]:
        valid = [r for r in rows if r["case"] == case["fixture"]["id"] and r["valid"]]
        ids = {r.get("response_id") for r in valid}
        grade.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "complete": len(valid) == 4 and len(ids) == 4 and None not in ids,
                "flag_failures": [
                    r["repeat"]
                    for r in valid
                    if r["output"]["act_completed"] != case["fixture"]["required_act_completed"]
                ],
            }
        )
    baseline.write(HERE / "grade.json", grade)
    print(json.dumps(grade))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
