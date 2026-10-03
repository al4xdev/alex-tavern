"""One ambiguous case: original input, reordered input, original with high thinking."""

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
BASE = ROOT / ".plans/artifacts/69-plan-label-current-builder/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
spec = importlib.util.spec_from_file_location("order_shared", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline
MANIFEST = HERE / "manifest.json"


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR,
        Path(baseline.__file__),
        ROOT / "src/roteiro.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/llm/client.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    prior = json.loads(PRIOR.read_text())
    old = next(c for c in prior["cases"] if c["fixture"]["id"] == "portal_closed-descriptive")
    cfg = baseline.config()
    f = copy.deepcopy(old["fixture"])
    f["id"] = "portal_closed"
    early, late = baseline.game_for(f, False), baseline.game_for(f, True)
    first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
    decision = (
        first if first.action else baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
    )
    game = early if first.action else late
    assert decision.action is not None
    new = await baseline.captured_request(game, decision.reason, "beat", cfg)
    original = copy.deepcopy(old["request"])
    assert new["messages"][0] == original["messages"][0]
    assert baseline.build_next_beat_schema("beat")["schema"] == old["schema"]
    # All unchanged input lines survive; only their order and this label differ.
    assert sorted(
        line
        for line in new["messages"][1]["content"]
        .replace("PREVIOUS BEAT PLAN", "CURRENT BEAT")
        .splitlines()
        if line
    ) == sorted(line for line in original["messages"][1]["content"].splitlines() if line)
    cases = []
    for arm, request in (
        ("original", original),
        ("reordered", new),
        ("original_high", copy.deepcopy(original)),
    ):
        request["model"] = "deepseek-flash"
        request["max_tokens"] = 8192
        request["thinking"] = {"type": "enabled" if arm == "original_high" else "disabled"}
        if arm == "original_high":
            request["reasoning_effort"] = "high"
        fixture = copy.deepcopy(f)
        fixture["id"] += "-" + arm
        cases.append({"fixture": fixture, "arm": arm, "request": request, "schema": old["schema"]})
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "provider": {k: cfg[k] for k in ("api_base", "language")},
        },
    )
    print("Frozen three arms, four curls each; original/high messages identical")


async def run() -> None:
    m = json.loads(MANIFEST.read_text())
    assert m["hashes"] == hashes()
    cfg = {**baseline.config(), "llm_timeout_seconds": 180}
    assert all(cfg[k] == v for k, v in m["provider"].items())
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    jobs = [(c, rep) for c in m["cases"] for rep in range(1, 5)]
    random.Random(6920).shuffle(jobs)
    # Ensure both requested interventions are launched alongside the control.
    first = [
        (next(c for c in m["cases"] if c["arm"] == arm), 1)
        for arm in ("original_high", "reordered", "original")
    ]
    jobs = first + [(c, r) for c, r in jobs if r != 1]
    semaphore = asyncio.Semaphore(4)

    async def call(case: dict[str, Any], rep: int) -> None:
        async with semaphore:
            await baseline.call_one(case, rep, cfg)

    await asyncio.gather(*(call(c, rep) for c, rep in jobs))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    grade = []
    for c in m["cases"]:
        valid = [r for r in rows if r["case"] == c["fixture"]["id"] and r["valid"]]
        ids = {r.get("response_id") for r in valid}
        reasoning = []
        for r in valid:
            raw = json.loads((baseline.RUNS / f"{r['case']}-{r['repeat']}.raw.json").read_text())
            msg = raw["choices"][0]["message"]
            reasoning.append(
                {
                    "repeat": r["repeat"],
                    "reasoning_chars": len(msg.get("reasoning_content") or ""),
                    "finish_reason": raw["choices"][0].get("finish_reason"),
                    "usage": raw.get("usage"),
                }
            )
        grade.append(
            {
                "arm": c["arm"],
                "valid": len(valid),
                "complete": len(valid) == 4 and len(ids) == 4 and None not in ids,
                "flag_errors": [
                    r["repeat"] for r in valid if r["output"]["act_completed"] is not True
                ],
                "metadata": reasoning,
            }
        )
    baseline.write(HERE / "grade.json", grade)
    print(json.dumps(grade))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
