"""Real Director requests against three disputed target conditions."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from src.agents.narrator import build_narrator_json_schema, build_narrator_messages, narrate
from src.llm.client import chat_completion
from src.models import RoteiroBeat, TurnRecord, deepcopy_scene
from src.roteiro import describe_roteiro_for_director

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "plans/artifacts/69-beat-only-baseline"
OUT = HERE / "director-refusal"
MANIFEST = HERE / "director-refusal-manifest.json"
spec = importlib.util.spec_from_file_location("beat_baseline", BASE / "beat_only_baseline.py")
assert spec is not None and spec.loader is not None
baseline: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def definitions() -> list[dict[str, str]]:
    return [
        {
            "id": "staircase_target",
            "intent": (
                "O piso cede e revela uma escada para o subsolo; a escadaria externa "
                "fica bloqueada por escombros. O mapa aponta para baixo. "
                "Iara e Bento precisam decidir como seguir para a torre."
            ),
            "exit": "Iara e Bento descem com o mapa, ou recuam enquanto o salão desmorona.",
        },
        {
            "id": "outside_target",
            "intent": (
                "O teto começa a soltar pedras e uma parede racha, pressionando "
                "Iara e Bento a sair e escolher uma rota para a torre."
            ),
            "exit": "O salão está parcialmente destruído e ambos estão do lado de fora com o mapa.",
        },
        {
            "id": "escort_target",
            "intent": (
                "Uma escolta da torre arromba a porta dupla, exige o mapa em voz alta "
                "e ocupa a saída sul. Iara e Bento precisam decidir como responder."
            ),
            "exit": "A escolta está no salão e exige o mapa, com a saída sul ocupada.",
        },
    ]


def game_for(case: dict[str, Any]) -> Any:
    fixture = next(row for row in baseline.fixtures() if row["id"] == "portal_closed")
    game = baseline.game_for(fixture, False)
    game.scene.physical_facts["runas"] = "apagadas"
    game.scene.zones = {fixture["now"]: []}
    assert game.roteiro is not None
    game.roteiro.act_index = 1
    game.roteiro.beat = RoteiroBeat(
        case["id"],
        case["intent"],
        ["C2"],
        [],
        case["exit"],
        4,
    )
    game.history.extend(
        [
            TurnRecord(
                3,
                "Player",
                "Eu fico aqui com o mapa para examinar o arco apagado. "
                "Não vou descer a escada nem sair agora.",
                "speech",
                deepcopy_scene(game.scene),
            ),
            TurnRecord(
                3,
                "C2",
                "Também fico no salão. Não levarei o mapa à escolta "
                "nem seguirei uma rota de saída agora.",
                "speech",
                deepcopy_scene(game.scene),
            ),
        ]
    )
    return game


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "DIRECTOR-REFUSAL-PREREGISTRATION.md",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/roteiro.py",
        ROOT / "src/models.py",
        ROOT / "src/prompting.py",
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
    for definition in definitions():
        game = game_for(definition)
        schema = build_narrator_json_schema(list(game.characters))
        messages = build_narrator_messages(
            game.scene,
            game.characters,
            "C1",
            game.history,
            narrator_directives=game.narrator_directives,
            roteiro_lines=describe_roteiro_for_director(game.roteiro, game.characters),
        )
        captured: list[dict[str, Any]] = []

        def capture(
            request: httpx.Request, sink: list[dict[str, Any]] = captured
        ) -> httpx.Response:
            sink.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
            await chat_completion(
                client,
                messages,
                provider="deepseek",
                model=cfg["model"],
                language=cfg["language"],
                api_base=cfg["api_base"],
                api_key="",
                json_schema=schema,
                max_tokens=2048,
            )
        assert len(captured) == 1
        cases.append(
            {
                "fixture": definition,
                "canonical_scene": asdict(game.scene),
                "schema": schema["schema"],
                "request": captured[0],
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
    print("Frozen three Director cases, four calls each")


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
    random.Random(6908).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)
            label = f"{case['fixture']['id']}-{repeat}"
            result = json.loads((OUT / f"{label}.result.json").read_text())
            if not result["valid"]:
                return
            game = game_for(case["fixture"])

            def replay(request: httpx.Request) -> httpx.Response:
                return httpx.Response(
                    200,
                    json={
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(result["output"]),
                                }
                            }
                        ]
                    },
                )

            async with httpx.AsyncClient(transport=httpx.MockTransport(replay)) as client:
                normalized = await narrate(
                    client,
                    game.scene,
                    game.characters,
                    "C1",
                    game.history,
                    {**cfg, "provider": "deepseek", "max_tokens_narrator": 2048},
                    narrator_directives=game.narrator_directives,
                    roteiro_lines=describe_roteiro_for_director(game.roteiro, game.characters),
                )
            baseline.write(OUT / f"{label}.normalized.json", normalized)

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
            }
        )
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
