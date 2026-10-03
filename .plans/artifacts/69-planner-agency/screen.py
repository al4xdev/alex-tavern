"""Isolated compiler replay: field-local situation/choice descriptions."""

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
from src.roteiro import build_roteiro_messages, build_roteiro_schema

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-actor-references/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-actor-references/manifest.json"
spec = importlib.util.spec_from_file_location("planner_agency_shared", BASE)
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
        ROOT / "src/roteiro.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def schema_for(arm: str, ids: list[str]) -> dict[str, Any]:
    schema = build_roteiro_schema(ids)
    beat = schema["schema"]["properties"]["first_beat"]["properties"]
    if arm != "control":
        beat["intent"]["description"] = (
            "Physical world changes and pressures in 'first_beat', "
            "with characters' voluntary actions, speech and conclusions left open."
        )
    if arm == "world_plan":
        summary = schema["schema"]["properties"]["acts"]["items"]["properties"]["summary"]
        summary["description"] = (
            "World situation and objective for this act. "
            "Characters' voluntary actions, speech and conclusions remain undecided."
        )
        beat["expected_anchors"]["description"] = (
            "Two to four world elements introduced or changed by 'first_beat'. "
            "Use confirmed belongings when attributing a possession to a character."
        )
    return schema


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    old = next(c for c in json.loads(PRIOR.read_text())["cases"] if c["fixture"]["id"] == "compile")
    cfg = baseline.config()
    fixture = copy.deepcopy(old["fixture"])
    game = baseline.game_for(fixture, False)
    game.roteiro = None
    messages = build_roteiro_messages(game)
    cases = []
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    for arm in ("control", "intent_only", "world_plan"):
        captured.clear()
        schema = schema_for(arm, list(game.characters))
        async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
            await chat_completion(
                client,
                copy.deepcopy(messages),
                json_schema=schema,
                provider="deepseek",
                api_base=cfg["api_base"],
                model=cfg["model"],
                language=cfg["language"],
                thinking_enabled=cfg["thinking_enabled"],
                max_tokens=1536,
            )
        assert len(captured) == 1
        if arm == "control":
            assert captured[0] == old["request"]
        f = copy.deepcopy(fixture)
        f["id"] = arm
        cases.append({"fixture": f, "arm": arm, "request": captured[0], "schema": schema["schema"]})
    baseline.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen control, intent-only and combined-world descriptions: 12 fresh curls")


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
            c["arm"],
            "valid",
            len(valid),
            "distinct IDs",
            len({r.get("response_id") for r in valid}),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
