"""Final roster-constrained compiler and next-beat provider boundary."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import httpx

from src.llm.client import chat_completion
from src.roteiro import (
    build_next_beat_messages,
    build_next_beat_schema,
    build_roteiro_messages,
    build_roteiro_schema,
)

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-production-reasoning/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
spec = importlib.util.spec_from_file_location("actor_reference_shared", BASE)
assert spec is not None and spec.loader is not None
production: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(production)
baseline = production.baseline
MANIFEST = HERE / "manifest.json"


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR,
        ROOT / "src/roteiro.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    prior = json.loads(PRIOR.read_text())
    cfg = baseline.config()
    cases = []
    captured: list[dict[str, Any]] = []
    for operation, fid in (
        ("compile", "portal_closed-descriptive"),
        ("replan", "portal_attempt-descriptive"),
    ):
        f = copy.deepcopy(next(c["fixture"] for c in prior["cases"] if c["fixture"]["id"] == fid))
        f["id"] = operation
        game = baseline.game_for(f, False)
        ids = list(game.characters)
        if operation == "compile":
            game.roteiro = None
            messages = build_roteiro_messages(game)
            schema = build_roteiro_schema(ids)
            requested_tokens = 1536
        else:
            messages = build_next_beat_messages(game, game.roteiro, "coverage_complete", "beat")
            schema = build_next_beat_schema("beat", ids)
            requested_tokens = 1024
        captured.clear()

        def capture(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
            await chat_completion(
                client,
                messages,
                json_schema=schema,
                provider="deepseek",
                api_base=cfg["api_base"],
                model=cfg["model"],
                language=cfg["language"],
                thinking_enabled=cfg["thinking_enabled"],
                max_tokens=requested_tokens,
            )
        assert len(captured) == 1
        assert captured[0]["max_tokens"] == 8192
        cases.append({"fixture": f, "request": captured[0], "schema": schema["schema"]})
    baseline.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen roster-bound compiler and next-beat: eight fresh curls")


async def run() -> None:
    m = json.loads(MANIFEST.read_text())
    assert m["hashes"] == hashes()
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    cfg = {**baseline.config(), "llm_timeout_seconds": 180}
    semaphore = asyncio.Semaphore(4)

    async def call(c: dict[str, Any], r: int) -> None:
        async with semaphore:
            await baseline.call_one(c, r, cfg)

    await asyncio.gather(*(call(c, r) for r in range(1, 5) for c in m["cases"]))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    for c in m["cases"]:
        valid = [r for r in rows if r["case"] == c["fixture"]["id"] and r["valid"]]
        print(
            c["fixture"]["id"],
            "valid",
            len(valid),
            "distinct_ids",
            len({r.get("response_id") for r in valid}),
        )
        for r in valid:
            key = "first_beat" if r["case"] == "compile" else "beat"
            print(r["repeat"], r["output"][key]["expected_actors"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
