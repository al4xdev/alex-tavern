"""Controlled real-provider screen of confirmed versus proposed speech basis."""

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

import httpx

from src.agents.narrator import build_narrator_json_schema, build_narrator_messages
from src.llm.client import chat_completion
from src.models import TurnRecord, deepcopy_scene

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / "speech-basis-manifest.json"
OUT = HERE / "speech-basis-runs"
PROTOCOL = HERE / "SPEECH-BASIS-PREREGISTRATION.md"
spec = importlib.util.spec_from_file_location("basis_cognition", HERE / "director_cognition.py")
assert spec and spec.loader
cognition: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cognition)
baseline = cognition.baseline
RULE = """- SPEECH BASIS: an audible_speech brief proposes the character's next speech;
  it is not evidence that the words have already been spoken. Other proposed
  speech and physical events must not depend on an utterance absent from HISTORY.
  Preserve ordinary independent speech proposals. An explicitly attempted reading
  aloud may disclose the established source contents, but does not authorize
  adding a question, opinion, warning or instruction to that reading.
"""


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        PROTOCOL,
        HERE / "director_cognition.py",
        HERE / "director_refusal.py",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def game_for(case: str) -> Any:
    game = cognition.game_for(
        next(c for c in cognition.definitions() if c["id"] == "observable_clue")
    )
    game.roteiro = None
    game.narrator_directives = (
        "O portal permanece aberto após uma tentativa de fechamento que falhou. "
        "As runas oscilam, mas não existe urgência nem instabilidade adicional. "
        "Iara mantém o mapa firmemente nas mãos. Bento vê marcas perto do encaixe."
    )
    game.scene.physical_facts["cifra_decifrada"] = (
        "Texto já decifrado e legível: a Dama do Norte é Glinda, "
        "que planeja conquistar as cinco cidades."
    )
    if case == "reading":
        game.history.append(
            TurnRecord(
                4,
                "Player",
                "Leio a cifra já decifrada em voz alta para Bento.",
                "action",
                deepcopy_scene(game.scene),
            )
        )
    elif case == "npc":
        game.history.append(
            TurnRecord(
                4,
                "C2",
                "Vejo um encaixe na parede; vou explicar o que vejo.",
                "speech",
                deepcopy_scene(game.scene),
            )
        )
    return game


async def prepare() -> None:
    assert not MANIFEST.exists()
    cfg = baseline.config()
    cases = []
    for name in ("holding", "reading", "npc"):
        game = game_for(name)
        schema = build_narrator_json_schema(list(game.characters))
        original = build_narrator_messages(
            game.scene,
            game.characters,
            "C1",
            game.history,
            narrator_directives=game.narrator_directives,
        )
        for arm in ("control", "basis"):
            messages = copy.deepcopy(original)
            if arm == "basis":
                system = messages[0]["content"]
                start = system.index("- DIALOGUE OWNERSHIP:")
                end = system.index("- HISTORY entries", start)
                messages[0]["content"] = system[:start] + RULE + system[end:]
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
                    "fixture": {"id": f"{name}_{arm}"},
                    "case": name,
                    "arm": arm,
                    "canonical_scene": asdict(game.scene),
                    "history": [asdict(r) for r in game.history],
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
    print("Frozen 24 independent curls: three matched cases, two arms, four repeats")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes() and not OUT.exists()
    cfg = baseline.config()
    assert all(cfg[k] == v for k, v in manifest["provider"].items())
    OUT.mkdir()
    baseline.RUNS = OUT
    jobs = [(case, repeat) for case in manifest["cases"] for repeat in range(1, 5)]
    random.Random(6919).shuffle(jobs)
    semaphore = asyncio.Semaphore(4)

    async def limited(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(limited(case, repeat) for case, repeat in jobs))
    rows = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.result.json"))]
    baseline.write(
        HERE / "speech-basis-gate.json",
        {
            "completed": len(rows),
            "valid": sum(bool(row["valid"]) for row in rows),
            "all_valid": len(rows) == 24 and all(row["valid"] for row in rows),
        },
    )
    print(json.dumps({"completed": len(rows), "valid": sum(bool(row["valid"]) for row in rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
