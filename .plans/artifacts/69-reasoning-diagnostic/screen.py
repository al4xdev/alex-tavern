"""Frozen ambiguous inputs: paired disabled/high reasoning diagnostic."""

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
BASE = ROOT / ".plans/artifacts/69-order-versus-reasoning/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
spec = importlib.util.spec_from_file_location("reasoning_shared", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline
MANIFEST = HERE / "manifest.json"


def hashes() -> dict[str, str]:
    paths = [Path(__file__), HERE / "PREREGISTRATION.md", BASE, PRIOR]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    prior = json.loads(PRIOR.read_text())
    cases = []
    for old in prior["cases"]:
        if old["fixture"]["id"] not in (
            "portal_attempt-descriptive",
            "portal_left-descriptive",
        ):
            continue
        for arm in ("disabled", "high"):
            request = copy.deepcopy(old["request"])
            request["model"] = "deepseek-flash"
            request["max_tokens"] = 8192
            request["thinking"] = {"type": "enabled" if arm == "high" else "disabled"}
            if arm == "high":
                request["reasoning_effort"] = "high"
            f = copy.deepcopy(old["fixture"])
            f["id"] = f["id"].removesuffix("-descriptive") + "-" + arm
            cases.append({"fixture": f, "arm": arm, "request": request, "schema": old["schema"]})
    assert len(cases) == 4
    for disabled, high in zip(cases[::2], cases[1::2], strict=True):
        assert disabled["request"]["messages"] == high["request"]["messages"]
    cfg = baseline.config()
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "provider": {k: cfg[k] for k in ("api_base", "language")},
        },
    )
    print("Frozen two fixtures, paired disabled/high, four repetitions: 16 curls")


async def run() -> None:
    m = json.loads(MANIFEST.read_text())
    assert m["hashes"] == hashes()
    cfg = {**baseline.config(), "llm_timeout_seconds": 180}
    assert all(cfg[k] == v for k, v in m["provider"].items())
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    jobs = [(c, r) for c in m["cases"] for r in range(1, 5)]
    random.Random(6921).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def call(c: dict[str, Any], r: int) -> None:
        async with semaphore:
            await baseline.call_one(c, r, cfg)

    await asyncio.gather(*(call(c, r) for c, r in jobs))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    grade = []
    for c in m["cases"]:
        valid = [r for r in rows if r["case"] == c["fixture"]["id"] and r["valid"]]
        ids = {r.get("response_id") for r in valid}
        reasoning = []
        for r in valid:
            raw = json.loads((baseline.RUNS / f"{r['case']}-{r['repeat']}.raw.json").read_text())
            reasoning.append(
                {
                    "repeat": r["repeat"],
                    "reasoning_chars": len(
                        raw["choices"][0]["message"].get("reasoning_content") or ""
                    ),
                    "finish_reason": raw["choices"][0].get("finish_reason"),
                }
            )
        grade.append(
            {
                "case": c["fixture"]["id"],
                "valid": len(valid),
                "complete": len(valid) == 4 and len(ids) == 4 and None not in ids,
                "flag_errors": [
                    r["repeat"]
                    for r in valid
                    if r["output"]["act_completed"] != c["fixture"]["required_act_completed"]
                ],
                "metadata": reasoning,
            }
        )
    baseline.write(HERE / "grade.json", grade)
    print(json.dumps(grade))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    if parser.parse_args().command == "prepare":
        prepare()
    else:
        asyncio.run(run())
