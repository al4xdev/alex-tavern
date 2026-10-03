"""Bounded planner/controller traces; world confirmations remain scripted."""

from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import asdict
from pathlib import Path

import httpx

import beat_only_baseline as baseline
from portal_exit_ab import BOUNDARY, NEW_STATUS, OLD_STATUS
from src.models import TurnRecord, deepcopy_scene
from src.roteiro import collect_beat_evidence, evaluate_roteiro, replan_roteiro

HERE = Path(__file__).resolve().parent
OUT = HERE / "bounded-portal"


def variant(request: dict) -> dict:
    request = copy.deepcopy(request)
    user = request["messages"][1]["content"].replace(OLD_STATUS, NEW_STATUS)
    start = user.index("RECENT EVENTS (oldest to newest):")
    end = user.index("\n\nPREMISE:", start)
    request["messages"][1]["content"] = (
        user[:start] + user[end:].lstrip("\n") + "\n\n" + user[start:end]
    )
    request["messages"][0]["content"] += BOUNDARY
    return request


async def trace(number: int, cfg: dict) -> dict:
    fixture = next(row for row in baseline.fixtures() if row["id"] == "portal_attempt")
    game = baseline.game_for(fixture, False)
    observations = []
    calls = 0

    async def plan(next_turn: int) -> bool:
        nonlocal calls
        assert game.roteiro is not None
        decision = evaluate_roteiro(game.roteiro, game.history, "C1", next_turn)
        obs = {
            "next_turn": next_turn,
            "decision": asdict(decision),
            "act_index_before": game.roteiro.act_index,
            "physical_facts": dict(game.scene.physical_facts),
        }
        observations.append(obs)
        if not decision.action:
            obs["act_index_after"] = game.roteiro.act_index
            return True
        calls += 1
        scope = "act" if decision.action == "replan_act" else "beat"
        request = variant(await baseline.captured_request(game, decision.reason, scope, cfg))
        label = f"trace{number}-turn{next_turn}"
        case = {
            "fixture": {"id": label},
            "request": request,
            "schema": baseline.build_next_beat_schema(scope)["schema"],
        }
        await baseline.call_one(case, 1, cfg)
        result_path = OUT / f"{label}-1.result.json"
        result = json.loads(result_path.read_text())
        obs["result"] = result_path.name
        if not result["valid"]:
            obs["technical_failure"] = True
            return False

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
            game.roteiro = await replan_roteiro(
                client,
                game,
                decision,
                {**cfg, "provider": "deepseek"},
                next_turn,
            )
        obs["act_index_after"] = game.roteiro.act_index
        obs["applied_beat"] = asdict(game.roteiro.beat)
        return True

    valid = await plan(3)
    assert game.roteiro is not None
    premature = game.roteiro.act_index != 0
    if valid and not premature:
        steps = (
            (
                3,
                "Narrator",
                "narration",
                "As runas se estabilizaram e apagaram; o portal se fechou completamente. "
                "Iara e Bento continuam no salão com o mapa.",
            ),
            (4, "Player", "speech", "Posso examinar o arco antes de irmos à torre?"),
            (5, "C2", "speech", "A passagem terminou; o mapa continua aqui conosco."),
        )
        for turn, speaker, kind, text in steps:
            game.history.append(TurnRecord(turn, speaker, text, kind, deepcopy_scene(game.scene)))
            game.roteiro.beat_actions_elapsed += 1
            if turn == 3:
                game.scene.physical_facts.update({"portal": "fechado", "runas": "apagadas"})
            game.roteiro.anchors_seen.extend(
                collect_beat_evidence(
                    game.roteiro,
                    [text],
                    scene_update_keys=("portal", "runas") if turn == 3 else (),
                )
            )
            valid = await plan(turn + 1)
            if not valid or game.roteiro.act_index != 0:
                break
    result = {
        "trace": number,
        "technical_complete": valid,
        "premature_advance": premature,
        "old_act_advanced_at_bound": valid and not premature and game.roteiro.act_index == 1,
        "calls": calls,
        "observations": observations,
    }
    baseline.write(OUT / f"trace{number}.json", result)
    return result


async def main() -> None:
    if OUT.exists():
        raise RuntimeError("Preserve traces")
    original = json.loads(baseline.MANIFEST.read_text())
    assert original["hashes"] == baseline.source_hashes()
    cfg = baseline.config()
    assert all(cfg[key] == original[key] for key in ("model", "language", "api_base"))
    OUT.mkdir()
    baseline.RUNS = OUT
    baseline.write(
        OUT / "manifest.json",
        {
            "hashes": baseline.source_hashes(),
            "script_sha256": baseline.digest(Path(__file__)),
            "protocol_sha256": baseline.digest(HERE / "BOUNDED-PORTAL-PREREGISTRATION.md"),
            "variant_sha256": baseline.digest(HERE / "portal_exit_ab.py"),
        },
    )
    rows = await asyncio.gather(*(trace(n, cfg) for n in range(1, 5)))
    summary = [{key: value for key, value in row.items() if key != "observations"} for row in rows]
    baseline.write(OUT / "grade.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
