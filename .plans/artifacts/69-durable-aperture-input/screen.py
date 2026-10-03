"""Current durable aperture as an isolated next-beat input variant."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from src.durable_state import (
    PhysicalTransition,
    apply_physical_transition,
    bootstrap_physical_entities,
)
from src.llm.client import chat_completion
from src.models import RoteiroAct, TurnRecord, dict_to_game_state, game_state_to_dict
from src.roteiro import build_next_beat_messages, build_next_beat_schema, evaluate_roteiro

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-actor-references/screen.py"
spec = importlib.util.spec_from_file_location("aperture_shared", BASE)
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
        ROOT / "src/roteiro.py",
        ROOT / "src/models.py",
        ROOT / "src/durable_state.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


def fixture(case_id: str) -> dict[str, Any]:
    return {
        "id": case_id,
        "before": "Salão dos portais",
        "now": "Salão dos portais",
        "premise": "A instabilidade do portal azul ameaça o salão dos portais.",
        "act": "Conter a abertura atual do portal azul.",
        "act_exit": "O portal azul está fechado.",
        "next_act": "Uma tempestade ameaça o telhado do salão.",
        "intent": "O portal azul aberto se alarga e pressiona as runas azuis.",
        "anchors": ["portal azul", "runas azuis"],
        "question": "Vamos aguardar aqui.",
        "accepted": [],
        "facts": {},
        "required_act_completed": case_id in {"closed_wait", "other_portal"},
    }


def state_for(f: dict[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
    game = baseline.game_for(f, False)
    game.durable_state = bootstrap_physical_entities(
        [
            {
                "entity_id": "physical-blue",
                "key": "portal azul",
                "kind": "passage",
                "scene_key": game.scene.location,
                "dimensions": {"aperture": "open"},
            },
            {
                "entity_id": "physical-green",
                "key": "portal verde",
                "kind": "passage",
                "scene_key": game.scene.location,
                "dimensions": {"aperture": "closed"},
            },
        ],
        character_ids=set(game.characters),
    )
    game.history.append(
        TurnRecord(
            1,
            "Narrator",
            "O portal azul está aberto; suas runas azuis estão acesas. "
            "O portal verde está fechado.",
            "narration",
            copy.deepcopy(game.scene),
        )
    )
    game.history.append(
        TurnRecord(
            1,
            "Narrator",
            "O mapa permanece enrolado sobre a mesa. Iara e Bento estão no salão.",
            "narration",
            copy.deepcopy(game.scene),
        )
    )
    snapshots = [game_state_to_dict(game)]

    def record(text: str, turn: int, *, speaker: str = "Narrator", kind: str = "narration") -> None:
        game.history.append(TurnRecord(turn, speaker, text, kind, copy.deepcopy(game.scene)))

    def change(entity: str, key: str, before: str, after: str, turn: int) -> None:
        apply_physical_transition(
            game.durable_state,
            PhysicalTransition(
                f"transition-{entity}-{turn}",
                entity,
                key,
                "aperture",
                before,
                after,
                turn,
                f"update-{turn}",
            ),
            expected_turn_number=turn,
        )

    if f["id"] == "failed_attempt":
        record(
            "A tentativa de fechamento falhou. O portal azul continua aberto; "
            "as runas azuis seguem acesas.",
            2,
        )
    else:
        change("physical-blue", "portal azul", "open", "closed", 2)
        record("O portal azul se fechou completamente; suas runas azuis apagaram.", 2)
    game = dict_to_game_state(game_state_to_dict(game))
    snapshots.append(game_state_to_dict(game))
    if f["id"] == "reopened":
        change("physical-blue", "portal azul", "closed", "open", 3)
        record(
            "O portal azul se abriu novamente por uma nova descarga; suas runas azuis reacenderam.",
            3,
        )
        record(
            "O portal azul voltou a abrir e as runas azuis estão acesas.",
            3,
            speaker="C2",
            kind="speech",
        )
        assert game.roteiro is not None and game.roteiro.beat is not None
        game.roteiro.acts.insert(
            0,
            RoteiroAct(
                "a0", "O primeiro fechamento do portal azul.", "O primeiro fechamento ocorreu."
            ),
        )
        game.roteiro.act_index = 1
        game.roteiro.beat_started_turn = 3
        game.roteiro.beat.beat_id = "reopened-blue-b1"
    elif f["id"] == "other_portal":
        change("physical-green", "portal verde", "closed", "open", 3)
        record(
            "Um portal verde distinto se abriu. O portal azul permanece fechado, "
            "sem passagem; suas runas azuis estão apagadas.",
            3,
        )
    else:
        record(
            "Iara e Bento aguardam no salão sem tocar nos portais. "
            "Nada abriu ou fechou durante essa espera.",
            3,
        )
    game = dict_to_game_state(game_state_to_dict(game))
    snapshots.append(game_state_to_dict(game))
    assert all(len(r.content) <= 160 for r in game.history)
    return game, snapshots


def projection(game: Any) -> str:
    public = [
        {"name": entity.key, "aperture": entity.dimensions["aperture"].state}
        for entity in game.durable_state.physical_entities.values()
        if entity.scene_key == game.scene.location and "aperture" in entity.dimensions
    ]
    return (
        "\n\nCURRENT CONFIRMED PHYSICAL STATE (not future plans):\n"
        "'name' identifies a world object; 'aperture' is its current openness: "
        "'closed' means no open passage, 'open' means an open passage.\n"
        + json.dumps(public, ensure_ascii=False)
    )


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cfg = baseline.config()
    cases = []
    for case_id in ("failed_attempt", "closed_wait", "reopened", "other_portal"):
        f = fixture(case_id)
        game, snapshots = state_for(f)
        decision = evaluate_roteiro(game.roteiro, game.history, "C1", 4)
        assert decision.reason == "coverage_complete"
        messages = build_next_beat_messages(game, game.roteiro, decision.reason, "beat")
        schema = build_next_beat_schema("beat", list(game.characters))
        for arm in ("control", "aperture"):
            selected = copy.deepcopy(messages)
            if arm == "aperture":
                selected[1]["content"] += projection(game)
            captured: list[dict[str, Any]] = []

            def capture(
                request: httpx.Request, bucket: list[dict[str, Any]] = captured
            ) -> httpx.Response:
                bucket.append(json.loads(request.content))
                return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

            async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
                await chat_completion(
                    client,
                    selected,
                    json_schema=schema,
                    provider="deepseek",
                    api_base=cfg["api_base"],
                    model=cfg["model"],
                    language=cfg["language"],
                    thinking_enabled=cfg["thinking_enabled"],
                    max_tokens=1024,
                )
            assert len(captured) == 1
            assert captured[0]["max_tokens"] == 8192
            label = {**f, "id": case_id + "-" + arm}
            cases.append(
                {
                    "fixture": label,
                    "arm": arm,
                    "request": captured[0],
                    "schema": schema["schema"],
                    "snapshots": snapshots,
                    "decision": asdict(decision),
                }
            )
    baseline.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen four state timelines, eight requests: 32 fresh curls")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes()
    baseline.RUNS = HERE / "runs"
    baseline.RUNS.mkdir()
    cfg = {**baseline.config(), "llm_timeout_seconds": 180}
    semaphore = asyncio.Semaphore(4)

    async def call(case: dict[str, Any], repeat: int) -> None:
        async with semaphore:
            await baseline.call_one(case, repeat, cfg)

    await asyncio.gather(*(call(c, r) for r in range(1, 5) for c in manifest["cases"]))
    rows = [json.loads(p.read_text()) for p in baseline.RUNS.glob("*.result.json")]
    for case in manifest["cases"]:
        matching = [r for r in rows if r["case"] == case["fixture"]["id"]]
        print(
            case["fixture"]["id"],
            "valid",
            sum(r["valid"] for r in matching),
            "flags",
            [r["output"]["act_completed"] for r in matching if r["valid"]],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
