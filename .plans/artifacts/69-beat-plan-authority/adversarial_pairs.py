"""Controlled paired fixtures derived from post-gate content criticism."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "adversarial-manifest.json"
OUT = HERE / "adversarial-runs"


def module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


pressure = module("paired_pressure", HERE / "pressure_screen.py")
baseline = pressure.baseline
frozen = module("paired_frozen_roteiro", HERE / "production_roteiro_frozen.py")
baseline.build_next_beat_messages = frozen.build_next_beat_messages
baseline.build_next_beat_schema = frozen.build_next_beat_schema


def fixtures() -> list[dict[str, Any]]:
    originals = {case["id"]: case for case in baseline.fixtures()}
    cases = []
    for name, event in (
        (
            "stable",
            "O salão está estável; piso e paredes estão intactos. Não houve dano pelo fechamento.",
        ),
        (
            "earthquake",
            "Após o fechamento, um terremoto externo rachou o piso e tornou o salão instável.",
        ),
    ):
        case = copy.deepcopy(originals["portal_closed"])
        case["id"] = name
        case["accepted"].extend(["O fechamento não danificou a estrutura do salão.", event])
        case["facts"].update(
            {
                "dano_por_fechamento": "nenhum",
                "estrutura": "intacta e estável"
                if name == "stable"
                else "rachada pelo terremoto externo",
            }
        )
        case["directives"] = (
            "O fechamento não causou danos estruturais. "
            "Eventos posteriores podem ter causas próprias."
        )
        cases.append(case)
    for name, event in (
        (
            "held",
            "Após a tentativa, Iara ainda segura firme o mapa. "
            "Ela não o largou nem o colocou no chão.",
        ),
        (
            "floor",
            "Após a tentativa, Iara colocou voluntariamente o mapa no chão. Ele continua no piso.",
        ),
    ):
        case = copy.deepcopy(originals["portal_attempt"])
        case["id"] = name
        case["accepted"].append(event)
        case["facts"]["mapa"] = (
            "seguro nas mãos de Iara" if name == "held" else "no chão, colocado por Iara"
        )
        cases.append(case)
    return cases


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "ADVERSARIAL-PREREGISTRATION.md",
        HERE / "pressure_screen.py",
        HERE / "production_roteiro_frozen.py",
        HERE / "production-manifest.json",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/prompting.py",
        ROOT / "src/models.py",
    ]
    return {str(path.relative_to(ROOT)): baseline.digest(path) for path in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve previous manifest")
    source = json.loads((HERE / "production-manifest.json").read_text())
    assert (
        baseline.digest(HERE / "production_roteiro_frozen.py") == source["hashes"]["src/roteiro.py"]
    )
    cfg = baseline.config()
    cases = []
    for fixture in fixtures():
        early, late = baseline.game_for(fixture, False), baseline.game_for(fixture, True)
        for game in (early, late):
            game.narrator_directives += " " + fixture.get("directives", "")
        first = frozen.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = frozen.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        game = early if first.action else late
        assert decision.action is not None
        scope = "act" if decision.action == "replan_act" else "beat"
        request = await baseline.captured_request(game, decision.reason, scope, cfg)
        system = request["messages"][0]["content"]
        assert system.count(pressure.OLD) == 1
        request["messages"][0]["content"] = system.replace(pressure.OLD, pressure.NEW)
        wire = "\n".join(message["content"] for message in request["messages"])
        assert all(event in wire for event in fixture["accepted"])
        cases.append(
            {
                "fixture": fixture,
                "request": request,
                "canonical_scene": asdict(game.scene),
                "decision": asdict(decision),
                "schema": frozen.build_next_beat_schema(scope)["schema"],
            }
        )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "provider": {k: cfg[k] for k in ("model", "language", "api_base")},
            "cases": cases,
        },
    )
    print("Frozen four paired fixtures; current runtime unchanged")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if OUT.exists():
        raise RuntimeError("Preserve previous responses")
    assert manifest["hashes"] == hashes()
    cfg = baseline.config()
    assert all(cfg[k] == value for k, value in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    random.Random(6913).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    rows = [json.loads(path.read_text()) for path in OUT.glob("*.result.json")]
    grade = []
    for case in manifest["cases"]:
        valid = [row for row in rows if row["case"] == case["fixture"]["id"] and row["valid"]]
        ids = {row["response_id"] for row in valid if row.get("response_id")}
        grade.append(
            {
                "case": case["fixture"]["id"],
                "valid": len(valid),
                "technical_complete": len(valid) >= 3 and len(ids) == len(valid),
                "act_gate_failures": [
                    row["repeat"]
                    for row in valid
                    if row["output"]["act_completed"] != case["fixture"]["required_act_completed"]
                ],
            }
        )
    baseline.write(OUT / "grade.json", grade)
    print(json.dumps(grade))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    if parser.parse_args().command == "prepare":
        asyncio.run(prepare())
    else:
        asyncio.run(run())
