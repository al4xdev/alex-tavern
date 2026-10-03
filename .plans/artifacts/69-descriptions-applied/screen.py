"""Curl the applied production descriptions against frozen prior requests."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-plan-label-current-builder/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-field-descriptions/manifest.json"
spec = importlib.util.spec_from_file_location("applied_screen_shared", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR,
        Path(baseline.__file__),
        ROOT / "src/roteiro.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def without_descriptions(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: without_descriptions(v) for k, v in value.items() if k != "description"}
    if isinstance(value, list):
        return [without_descriptions(v) for v in value]
    return value


async def prepare() -> None:
    if shared.MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cfg = baseline.config()
    prior = json.loads(PRIOR.read_text())
    assert all(cfg[k] == v for k, v in prior["provider"].items())
    cases = []
    for old in prior["cases"]:
        if old["arm"] != "control":
            continue
        fixture = copy.deepcopy(old["fixture"])
        fixture["id"] = fixture["id"].removesuffix("-control")
        early, late = baseline.game_for(fixture, False), baseline.game_for(fixture, True)
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        game = early if first.action else late
        assert decision.action is not None
        scope = "act" if decision.action == "replan_act" else "beat"
        new = await baseline.captured_request(game, decision.reason, scope, cfg)
        assert new["messages"][1:] == old["request"]["messages"][1:]
        assert {k: v for k, v in new.items() if k != "messages"} == {
            k: v for k, v in old["request"].items() if k != "messages"
        }
        schema = baseline.build_next_beat_schema(scope)["schema"]
        assert without_descriptions(schema) == old["schema"]
        for arm, request, selected_schema in (
            ("prior", old["request"], old["schema"]),
            ("descriptive", new, schema),
        ):
            f = copy.deepcopy(fixture)
            f["id"] += "-" + arm
            cases.append(
                {
                    "fixture": f,
                    "arm": arm,
                    "request": request,
                    "schema": selected_schema,
                    "decision": asdict(decision),
                    "canonical_scene": asdict(game.scene),
                }
            )
    baseline.write(
        shared.MANIFEST, {"hashes": hashes(), "cases": cases, "provider": prior["provider"]}
    )
    print("Frozen exact production descriptions and prior comparator; 24 fresh curls")


if __name__ == "__main__":
    shared.HERE = HERE
    shared.MANIFEST = HERE / "manifest.json"
    shared.hashes = hashes
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else shared.run())
