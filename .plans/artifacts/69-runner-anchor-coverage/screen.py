"""Two Runner submissions: new beat coverage versus established world elements."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
OLD = "Not in play yet — introduce as concrete perception events:"
NEW = "Beat elements awaiting coverage:"
task_data = os.environ.get("ROLEPLAY_DATA_DIR")
if not task_data:
    raise RuntimeError("Set an isolated ROLEPLAY_DATA_DIR before importing storage")
task_root = Path(task_data).resolve()
if task_root == (ROOT / ".data").resolve() or (ROOT / ".data").resolve() in task_root.parents:
    raise RuntimeError("Refuse real data root")

import httpx  # noqa: E402

from src.models import (  # noqa: E402
    Roteiro,
    RoteiroAct,
    RoteiroBeat,
    TurnRecord,
    game_state_to_dict,
)
from src.runner import Runner  # noqa: E402
from src.store.sessions import load_game, save_game, session_debug_path  # noqa: E402
from tests.factories import director_beat, make_cast, make_game, make_scene  # noqa: E402

BASE = ROOT / ".plans/artifacts/69-actor-references/screen.py"
spec = importlib.util.spec_from_file_location("coverage_boundary_shared", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        ROOT / "src/roteiro.py",
        ROOT / "src/runner.py",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cast = make_cast("Iara", "Bento")
    scene = make_scene(
        characters=cast,
        location="Salão dos portais",
        time_of_day="tarde",
        physical_facts={"portal_azul": "fechado", "portal_verde": "fechado e intacto"},
        positions={"C1": "Salão dos portais", "C2": "Salão dos portais"},
    )
    game = make_game(
        session_id=str(uuid4()),
        characters=cast,
        scene=scene,
        narrator_directives="Fantasia de aventura. Texto em português brasileiro.",
        history=[
            TurnRecord(
                1,
                "Narrator",
                "O portal azul foi fechado. O portal verde permanece fechado e intacto no salão.",
                "narration",
                copy.deepcopy(scene),
            )
        ],
        roteiro=Roteiro(
            premise="Os portais e a tempestade ameaçam o salão.",
            acts=[
                RoteiroAct("a1", "Conter a abertura azul.", "O portal azul está fechado."),
                RoteiroAct(
                    "a2", "A tempestade ameaça o telhado.", "A tempestade causou dano ao telhado."
                ),
            ],
            beat=RoteiroBeat(
                "old-blue",
                "A abertura azul ameaça o salão.",
                [],
                ["portal azul"],
                "O azul fecha.",
                6,
            ),
            beat_started_turn=1,
            anchors_seen=["portal azul"],
        ),
    )
    save_game(game)
    snapshots = [game_state_to_dict(load_game(game.session_id))]
    requests: list[dict[str, Any]] = []
    planner_calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal planner_calls
        body = json.loads(request.content)
        schema = json.loads(
            body["messages"][0]["content"].split(
                "Do not add markdown or keys outside the schema:\n", 1
            )[1]
        )
        if "act_completed" in schema["properties"]:
            planner_calls += 1
            output = {
                "act_completed": planner_calls == 1,
                "beat": {
                    "beat_id": f"storm-{planner_calls}",
                    "intent": "Uma rajada pressiona a viga do telhado "
                    "ao lado do portal verde fechado.",
                    "expected_actors": [],
                    "expected_anchors": ["viga", "portal verde"],
                    "exit_condition": "A viga quebra ou a água invade o salão.",
                    "budget_turns": 6,
                },
            }
        elif "perception_events" in schema["properties"]:
            requests.append(body)
            output = director_beat(
                next_speakers=["Narrator"],
                perception_events=[
                    {
                        "event_kind": "physical_outcome",
                        "subject_id": "Narrator",
                        "content": "Uma rajada atravessa o salão; a viga range. "
                        "O portal verde permanece fechado.",
                        "witness_ids": ["C1", "C2"],
                    }
                ],
                return_control=True,
            )
            output = {k: v for k, v in output.items() if k in schema["properties"]}
        else:
            raise RuntimeError("Unexpected model call in controlled capture")
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(output)}}]})

    config = {
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "language": "pt-BR",
        "thinking_enabled": True,
        "roteiro_enabled": True,
        "auto_event_enabled": False,
        "watcher_enabled": False,
        "disposition_enabled": False,
        "context_max": 32768,
    }
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        runner = Runner(client, config)

        async def render(*args: Any, **kwargs: Any) -> str:
            return "Uma rajada atravessa o salão e a viga range; o portal verde permanece fechado."

        runner._render_narration = render  # type: ignore[method-assign]
        for _ in range(2):
            await runner.player_turn(
                game.session_id, action="Aguardo sem tocar nos portais.", force_speaker="Narrator"
            )
            persisted = load_game(game.session_id)
            assert persisted is not None and persisted.roteiro is not None
            assert persisted.scene.physical_facts["portal_verde"] == "fechado e intacto"
            assert persisted.roteiro.anchors_seen == ["viga", "portal verde"]
            snapshots.append(game_state_to_dict(persisted))
    assert planner_calls == 2 and len(requests) == 2
    cases = []
    for index, request in enumerate(requests, 1):
        source = request["messages"][1]["content"]
        assert source.count(OLD) == 1 and "portal verde" in source
        schema = json.loads(
            request["messages"][0]["content"].split(
                "Do not add markdown or keys outside the schema:\n", 1
            )[1]
        )
        for arm in ("control", "coverage"):
            body = copy.deepcopy(request)
            if arm == "coverage":
                body["messages"][1]["content"] = source.replace(OLD, NEW)
            cases.append(
                {
                    "fixture": {"id": f"submission{index}-{arm}"},
                    "arm": arm,
                    "request": body,
                    "schema": schema,
                }
            )
    baseline.write(
        MANIFEST,
        {
            "hashes": hashes(),
            "cases": cases,
            "snapshots": snapshots,
            "data_root": str(task_root),
            "session_id": game.session_id,
            "debug_log": str(session_debug_path(game.session_id)),
        },
    )
    print("Captured two persisted Runner submissions; froze four requests for sixteen curls")


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
        valid = [r for r in rows if r["case"] == case["fixture"]["id"] and r["valid"]]
        print(
            case["fixture"]["id"],
            "valid",
            len(valid),
            "distinct",
            len({r.get("response_id") for r in valid}),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
