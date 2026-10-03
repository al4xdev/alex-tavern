"""Capture and test the actual candidate production planning builder."""

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
BASE = ROOT / "plans/artifacts/69-beat-only-baseline"
OUT = HERE / "production-runs"
MANIFEST = HERE / "production-manifest.json"
spec = importlib.util.spec_from_file_location("beat_baseline", BASE / "beat_only_baseline.py")
assert spec is not None and spec.loader is not None
baseline: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def fixtures() -> list[dict[str, Any]]:
    cases = baseline.fixtures()
    stable = copy.deepcopy(next(case for case in cases if case["id"] == "portal_closed"))
    stable["id"] = "closed_stable_hall"
    stable["directives"] = (
        "O salão se estabilizou após o selamento. Fechar o portal não danificou "
        "a estrutura, e ela não desmorona por causa desse fechamento."
    )
    distinct = copy.deepcopy(next(case for case in cases if case["id"] == "portal_left"))
    distinct["id"] = "different_runes"
    distinct["accepted"].append(
        "Um raio atingiu uma laje no cânion e acendeu inscrições diferentes; "
        "as runas do portal antigo continuam apagadas."
    )
    distinct["facts"]["inscricoes_do_canion"] = "acesas após um raio; distintas do portal"
    return [*cases, stable, distinct]


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PRODUCTION-PREREGISTRATION.md",
        ROOT / "src/roteiro.py",
        ROOT / "src/prompting.py",
        ROOT / "src/models.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        BASE / "beat_only_baseline.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cfg = baseline.config()
    cases = []
    for fixture in fixtures():
        early, late = baseline.game_for(fixture, False), baseline.game_for(fixture, True)
        for game in (early, late):
            if "directives" in fixture:
                game.narrator_directives += " " + fixture["directives"]
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        game = early if first.action else late
        scope = "act" if decision.action == "replan_act" else "beat"
        assert decision.action is not None
        request = await baseline.captured_request(game, decision.reason, scope, cfg)
        wire = "\n".join(msg["content"] for msg in request["messages"])
        assert all(event in wire for event in fixture["accepted"])
        cases.append(
            {
                "fixture": fixture,
                "request": request,
                "canonical_scene": asdict(game.scene),
                "decision": asdict(decision),
                "schema": baseline.build_next_beat_schema(scope)["schema"],
            }
        )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "provider": {k: cfg[k] for k in ("model", "language", "api_base")},
        },
    )
    print(f"Captured {len(cases)} actual production requests")


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
    random.Random(6910).shuffle(jobs)
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
                    if "required_act_completed" in case["fixture"]
                    and r["output"]["act_completed"] != case["fixture"]["required_act_completed"]
                ],
            }
        )
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
