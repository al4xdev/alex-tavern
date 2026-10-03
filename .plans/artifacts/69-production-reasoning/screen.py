"""Exercise the delivered builder, adapter and reasoning output budget."""

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

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-order-versus-reasoning/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
spec = importlib.util.spec_from_file_location("production_reasoning_shared", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline
MANIFEST = HERE / "manifest.json"


async def captured_request(game: Any, reason: str, cfg: dict[str, Any]) -> dict[str, Any]:
    captured: list[dict[str, Any]] = []

    def capture(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
        await chat_completion(
            client,
            baseline.build_next_beat_messages(game, game.roteiro, reason, "beat"),
            provider="deepseek",
            model=cfg["model"],
            language=cfg["language"],
            api_base=cfg["api_base"],
            api_key="",
            thinking_enabled=cfg["thinking_enabled"],
            max_tokens=1024,
            json_schema=baseline.build_next_beat_schema("beat"),
        )
    assert len(captured) == 1
    return captured[0]


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR,
        ROOT / "src/roteiro.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/adapters/base.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/llm/client.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cfg = baseline.config()
    assert cfg["thinking_enabled"] is True
    cases = []
    for old in json.loads(PRIOR.read_text())["cases"]:
        if old["arm"] != "descriptive":
            continue
        f = copy.deepcopy(old["fixture"])
        f["id"] = f["id"].removesuffix("-descriptive") + "-production"
        early, late = baseline.game_for(f, False), baseline.game_for(f, True)
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        decision = (
            first
            if first.action
            else baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        )
        assert decision.action is not None
        game = early if first.action else late
        request = await captured_request(game, decision.reason, cfg)
        assert request["thinking"] == {"type": "enabled"}
        assert request["reasoning_effort"] == "high"
        assert request["max_tokens"] == 8192
        assert "PREVIOUS BEAT PLAN" in request["messages"][1]["content"]
        cases.append({"fixture": f, "request": request, "schema": old["schema"]})
    assert len(cases) == 3
    baseline.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen delivered production requests: 12 curls")


async def run() -> None:
    m = json.loads(MANIFEST.read_text())
    assert m["hashes"] == hashes()
    cfg = {**baseline.config(), "llm_timeout_seconds": 180}
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    semaphore = asyncio.Semaphore(4)

    async def call(c: dict[str, Any], r: int) -> None:
        async with semaphore:
            await baseline.call_one(c, r, cfg)

    await asyncio.gather(*(call(c, r) for r in range(1, 5) for c in m["cases"]))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    grade = []
    for c in m["cases"]:
        valid = [r for r in rows if r["case"] == c["fixture"]["id"] and r["valid"]]
        ids = {r.get("response_id") for r in valid}
        explanations = []
        for r in valid:
            raw = json.loads((baseline.RUNS / f"{r['case']}-{r['repeat']}.raw.json").read_text())
            explanations.append(len(raw["choices"][0]["message"].get("reasoning_content") or ""))
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
                "reasoning_chars": explanations,
            }
        )
    baseline.write(HERE / "grade.json", grade)
    print(json.dumps(grade))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
