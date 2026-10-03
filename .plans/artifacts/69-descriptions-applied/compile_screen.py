"""Boundary smoke test of the described initial roteiro compiler."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any

import httpx

from src.roteiro import build_roteiro_schema, generate_roteiro

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("applied_helper", HERE / "screen.py")
assert spec is not None and spec.loader is not None
helper: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
baseline = helper.baseline
MANIFEST = HERE / "compile-manifest.json"


def hashes() -> dict[str, str]:
    paths = [Path(__file__), HERE / "COMPILE-PREREGISTRATION.md", ROOT / "src/roteiro.py"]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve compile manifest")
    cfg = {**baseline.config(), "provider": "deepseek"}
    fixture = next(f for f in baseline.fixtures() if f["id"] == "portal_closed")
    game = baseline.game_for(fixture, False)
    game.roteiro = None
    captured = []
    dummy = {
        "premise": "Levar o mapa à torre.",
        "acts": [
            {
                "act_id": "a1",
                "summary": "Seguir à torre.",
                "exit_condition": "Mapa na torre.",
                "duration_ticks": 3,
                "world_event": "Um sino toca.",
            }
        ],
        "first_beat": {
            "beat_id": "b1",
            "intent": "Um sino toca.",
            "expected_actors": ["C2"],
            "expected_anchors": ["sino"],
            "exit_condition": "O sino para.",
            "budget_turns": 3,
        },
    }

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(dummy)}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        await generate_roteiro(client, game, cfg, 1)
    assert len(captured) == 1
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "case": {
                "fixture": {**fixture, "id": "compile_closed"},
                "request": captured[0],
                "schema": build_roteiro_schema()["schema"],
            },
        },
    )
    print("Frozen actual generate_roteiro payload; four curl boundary calls")


async def run() -> None:
    m = json.loads(MANIFEST.read_text())
    assert m["hashes"] == hashes()
    baseline.RUNS = HERE / "compile-runs"
    baseline.RUNS.mkdir()
    await asyncio.gather(
        *(baseline.call_one(m["case"], rep, baseline.config()) for rep in range(1, 5))
    )
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    print(json.dumps({"calls": len(rows), "valid": sum(r["valid"] for r in rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
