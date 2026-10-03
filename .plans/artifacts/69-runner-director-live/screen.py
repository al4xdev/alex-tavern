"""Fresh actual Director calls before admitting the full narrative pipeline."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA != ROOT / ".data" and ROOT / ".data" not in DATA.parents
spec = importlib.util.spec_from_file_location(
    "authority_candidate", HERE.parent / "69-runner-authority/candidate.py"
)
assert spec is not None and spec.loader is not None
candidate: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

from src.durable_state import (  # noqa: E402
    PhysicalTransition,
    apply_physical_transition,
    bootstrap_physical_entities,
)
from src.llm.adapters.deepseek import DeepSeekAdapter  # noqa: E402
from src.models import Roteiro, RoteiroBeat, dict_to_game_state, game_state_to_dict  # noqa: E402
from src.prompt_contract import operator_ontology_hits  # noqa: E402
from src.store.locks import session_lock  # noqa: E402
from src.store.sessions import load_game, save_game  # noqa: E402
from tests.factories import (  # noqa: E402
    director_beat,
    make_cast,
    make_game,
    make_record,
    make_scene,
)

CONFIG = {
    "provider": "deepseek",
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-v4-flash",
    "thinking_enabled": True,
    "max_tokens_narrator": 16384,
    "llm_timeout_seconds": 180,
    "language": "pt-BR",
}


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        HERE.parent / "69-runner-authority/candidate.py",
        ROOT / "src/runner.py",
        ROOT / "src/roteiro.py",
        ROOT / "src/models.py",
        ROOT / "src/durable_state.py",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/schema.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/store/sessions.py",
        ROOT / "tests/factories.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def clean_review(stage: str, payload: dict) -> bool:
    return True


def fixture(number: int) -> dict[str, Any]:
    cast = make_cast("Iara", "Bento", "Téo")
    scene = make_scene(
        characters=cast,
        present=[*cast, "Player"],
        location="observatório",
        zones={"salão": ["túnel", "pátio"], "túnel": ["salão"], "pátio": ["salão"]},
        positions=dict.fromkeys(cast, "salão"),
        physical_facts={"portal azul": "open", "portal verde": "closed", "lanterna": "acesa"},
    )
    game = make_game(session_id=str(uuid4()), characters=cast, scene=scene)
    game.durable_state = bootstrap_physical_entities(
        [
            {
                "entity_id": "private-blue",
                "key": "portal azul",
                "kind": "passage",
                "scene_key": "observatório",
                "dimensions": {"aperture": "open"},
            },
            {
                "entity_id": "private-green",
                "key": "portal verde",
                "kind": "passage",
                "scene_key": "observatório",
                "dimensions": {"aperture": "closed"},
            },
        ],
        character_ids=set(cast),
    )
    apply_physical_transition(
        game.durable_state,
        PhysicalTransition(
            "wind-close",
            "private-blue",
            "portal azul",
            "aperture",
            "open",
            "closed",
            1,
            "wind-turn-1",
        ),
        expected_turn_number=1,
    )
    old_close = {
        "kind": "aperture_change",
        "target": "portal azul",
        "actor": "",
        "from_state": "open",
        "to_state": "closed",
        "result": "",
        "cause": "A ventania fecha o portal azul.",
    }
    game.scene.physical_facts["portal azul"] = "closed"
    game.narrative_tick = 1
    game.revision = 1
    game.history = [
        make_record(
            1,
            "Narrator",
            "A ventania fecha o portal azul. Téo permanece no salão.",
            "narration",
            scene=game.scene,
        ),
        make_record(
            2,
            "Player",
            "Aproximo minha lanterna da barra do portal azul para observá-la.",
            "action",
            scene=game.scene,
        ),
    ]
    game.roteiro = Roteiro(
        premise="Encontrar uma saída com cautela.",
        beat=RoteiroBeat(
            "saída",
            "Dar passagem a Téo pelo portal azul.",
            expected_actors=["C2"],
            expected_anchors=["azul aberto", "Téo no túnel", "lanterna"],
        ),
    )
    game.plugin_state = {
        "accepted_physical_steps": [{"turn_number": 1, "steps": [old_close]}],
        "authority_fixture": {
            "routes": {
                "portal azul": {"origin": "salão", "destination": "túnel"},
                "portal verde": {"origin": "salão", "destination": "pátio"},
            },
            "attempts_by_turn": {
                "2": [
                    {
                        "actor": "Téo",
                        "target": "portal azul",
                        "origin": "salão",
                        "destination": "túnel",
                    }
                ]
            },
            "goals": [
                {
                    "anchor": "azul aberto",
                    "kind": "aperture",
                    "target": "portal azul",
                    "state": "open",
                },
                {
                    "anchor": "Téo no túnel",
                    "kind": "crossing",
                    "actor": "Téo",
                    "target": "portal azul",
                    "destination": "túnel",
                },
            ],
        },
    }
    source = {
        "new_causes": {
            "description": "New causes to resolve THIS beat, not yet committed; "
            "old wind is history.",
            "value": (
                "Téo empurra a folha do portal azul, mas a barra pesada não cede. "
                "Não há nova ventania nem causa de fechamento ou abertura de qualquer portal."
                if number == 0
                else "Bento retira a barra do portal azul e puxa a folha azul "
                "até abrir completamente a passagem. Sua intervenção é suficiente. "
                "Não há nova ventania nem outra causa "
                "de mudança de abertura de qualquer portal."
            ),
        },
        "ancillary_speech_intent": {
            "description": "Supported present speech intent; report it without writing dialogue.",
            "value": "Bento pede cautela junto à folha do portal azul.",
        },
    }
    return {
        "id": f"submission{number + 1}",
        "game": game_state_to_dict(game),
        "source": source,
        "expected": {
            "blue": "closed" if number == 0 else "open",
            "teo": "salão" if number == 0 else "túnel",
        },
    }


async def call(runner: Any, game: Any, case: dict) -> dict:
    return await runner._call_narrator(
        game,
        2,
        extra_context=[
            "SOURCE FOR THIS BEAT (supported causes/intents, not yet committed): "
            + json.dumps(case["source"], ensure_ascii=False)
        ],
    )


async def prepare() -> None:
    assert not MANIFEST.exists(), "Preserve existing manifest"
    cases = []
    for number in range(2):
        case = fixture(number)
        game = dict_to_game_state(case["game"])
        captured = []

        def capture(request: httpx.Request, captured: list = captured) -> httpx.Response:
            captured.append(json.loads(request.content))
            response = director_beat(
                next_speakers=[],
                perception_events=[
                    {
                        "event_kind": "observation",
                        "subject_id": "C1",
                        "content": "Iara ergue a lanterna.",
                        "witness_ids": ["C2", "C3"],
                    }
                ],
            )
            response.pop("narration")
            response["physical_steps"] = []
            return httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps(response)}}]}
            )

        async with session_lock(game.session_id):
            save_game(game)
            reloaded = load_game(game.session_id)
            assert reloaded is not None
            assert game_state_to_dict(reloaded) == case["game"]
            async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
                await call(candidate.AuthorityRunner(client, CONFIG, clean_review), reloaded, case)
        assert len(captured) == 1
        case["request"] = captured[0]
        text = json.dumps(captured[0]["messages"], ensure_ascii=False)
        assert "private-blue" not in text and "private-green" not in text
        assert not operator_ontology_hits(text)
        cases.append(case)
    write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen two actual Director requests and starts; eight fresh logical draws")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    provider = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    semaphore = asyncio.Semaphore(4)

    async def logical(case: dict, repeat: int) -> None:
        async with semaphore:
            stem = f"{case['id']}-{repeat}"
            game = dict_to_game_state(case["game"])
            game.session_id = str(uuid4())
            attempts = 0

            async def network(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                name = f"{stem}-attempt{attempts}"
                body = json.loads(request.content)
                assert body == case["request"], "Production request drift"
                path = runs / f"{name}.request.json"
                write(path, body)
                config = (
                    "\n".join(
                        [
                            "silent",
                            "show-error",
                            "request = POST",
                            "max-time = 180",
                            "url = " + json.dumps(str(request.url)),
                            "header = " + json.dumps("Content-Type: application/json"),
                            "header = "
                            + json.dumps("Authorization: " + request.headers["Authorization"]),
                            "data-binary = " + json.dumps("@" + str(path)),
                            'write-out = "\\n%{http_code}"',
                        ]
                    )
                    + "\n"
                )
                process = await asyncio.create_subprocess_exec(
                    "curl",
                    "--config",
                    "-",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate(config.encode())
                raw, _, status = stdout.rpartition(b"\n")
                (runs / f"{name}.raw.json").write_bytes(raw)
                write(
                    runs / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError("curl failed; see retained transport", request=request)
                return httpx.Response(int(status), content=raw, request=request)

            result = {
                "case": case["id"],
                "repeat": repeat,
                "session_id": game.session_id,
                "schema_pass": False,
                "mechanical_pass": False,
                "expectation_pass": False,
            }
            async with session_lock(game.session_id):
                save_game(game)
                game = load_game(game.session_id)
                assert game is not None
                write(runs / f"{stem}.start.json", game_state_to_dict(game))
                async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                    runner = candidate.AuthorityRunner(client, cfg, clean_review)
                    try:
                        output = await call(runner, game, case)
                        result.update(output=output, schema_pass=True)
                    except Exception as error:
                        result["client_error"] = f"{type(error).__name__}: {error}"
                    if result["schema_pass"]:
                        draft = copy.deepcopy(game)
                        try:
                            scene_up = runner._apply_canon(draft, output, 2)
                            draft.roteiro.anchors_seen.extend(
                                runner._collect_beat_evidence(draft, output, [], scene_up)
                            )
                            result["mechanical_pass"] = True
                            projected = candidate.project(draft, 2)
                            expected = case["expected"]
                            assert projected["apertures"] == {
                                "portal azul": expected["blue"],
                                "portal verde": "closed",
                            }
                            assert projected["positions"] == {
                                "Iara": "salão",
                                "Bento": "salão",
                                "Téo": expected["teo"],
                            }
                            hits = set(draft.roteiro.anchors_seen) & {"azul aberto", "Téo no túnel"}
                            assert hits == (
                                set()
                                if expected["blue"] == "closed"
                                else {"azul aberto", "Téo no túnel"}
                            )
                            progress = runner._evaluate_roteiro(draft, 3).progress
                            assert progress is not None
                            assert (
                                set(progress.anchors_hit) & {"azul aberto", "Téo no túnel"} == hits
                            )
                            result["expectation_pass"] = True
                        except Exception as error:
                            result["validation_error"] = f"{type(error).__name__}: {error}"
                        write(runs / f"{stem}.draft.json", game_state_to_dict(draft))
                persisted = load_game(game.session_id)
                assert persisted is not None
                assert game_state_to_dict(persisted) == game_state_to_dict(game)
            result["attempts"] = attempts
            write(runs / f"{stem}.result.json", result)
            print(
                stem,
                "schema",
                result["schema_pass"],
                "mechanical",
                result["mechanical_pass"],
                "expected",
                result["expectation_pass"],
                "attempts",
                attempts,
                flush=True,
            )

    await asyncio.gather(
        *(logical(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
