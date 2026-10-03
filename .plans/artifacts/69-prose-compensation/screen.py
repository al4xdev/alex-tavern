"""Actual public prose from two retained Director outputs; no new Director draw."""

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
PRIOR = HERE.parent / "69-runner-director-live"
spec = importlib.util.spec_from_file_location("director_probe", PRIOR / "screen.py")
assert spec is not None and spec.loader is not None
prior: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

from src.models import dict_to_game_state, game_state_to_dict  # noqa: E402
from src.prompt_contract import operator_ontology_hits  # noqa: E402
from src.runner import Runner  # noqa: E402
from src.store.locks import session_lock  # noqa: E402
from src.store.sessions import load_game, save_game  # noqa: E402

CONFIG = {**prior.CONFIG, "narrator_min_words": 150}


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR / "screen.py",
        PRIOR / "manifest.json",
        PRIOR / "runs/submission2-2.result.json",
        PRIOR / "runs/submission2-3.result.json",
        HERE.parent / "69-runner-authority/candidate.py",
        ROOT / "src/runner.py",
        ROOT / "src/agents/prose.py",
        ROOT / "src/perception.py",
        ROOT / "src/models.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/schema.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "src/store/sessions.py",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def render(client: httpx.AsyncClient, game: Any, case: dict, cfg: dict) -> str:
    raw = copy.deepcopy(case["director"])
    authority = prior.candidate.AuthorityRunner(client, cfg, prior.clean_review)
    authority._apply_canon(game, raw, 2)
    runner = Runner(client, cfg)
    assert runner._narration_clusters(game, raw["perception_events"]) == [None]
    return await runner._render_and_prepare(game, raw, [], 2, multi_beat=False)


async def prepare() -> None:
    assert not MANIFEST.exists(), "Preserve executed manifest"
    parent = json.loads((PRIOR / "manifest.json").read_text())
    assert parent["hashes"] == prior.hashes(), "Retained Director source drift"
    start = parent["cases"][1]["game"]
    cases = []
    for index, source_repeat in enumerate((3, 2), 1):
        source = json.loads((PRIOR / f"runs/submission2-{source_repeat}.result.json").read_text())
        assert source["schema_pass"] and source["mechanical_pass"] and source["expectation_pass"]
        case = {
            "id": f"submission{index}",
            "game": start,
            "source_draw": f"submission2-{source_repeat}",
            "director": source["output"],
        }
        game = dict_to_game_state(start)
        captured = []

        def capture(request: httpx.Request, captured: list = captured) -> httpx.Response:
            captured.append(json.loads(request.content))
            # Force the existing echo guard to capture its exact static retry.
            text = (
                start["history"][0]["content"]
                if len(captured) == 1
                else ("Bento afasta a folha azul. Téo alcança a passagem iluminada.")
            )
            return httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps({"narration": text})}}]}
            )

        async with session_lock(game.session_id):
            save_game(game)
            reloaded = load_game(game.session_id)
            assert reloaded is not None
            async with httpx.AsyncClient(transport=httpx.MockTransport(capture)) as client:
                await render(client, reloaded, case, CONFIG)
            persisted = load_game(game.session_id)
            assert persisted is not None and game_state_to_dict(persisted) == start
        assert len(captured) == 2, "Actual echo-correction request not captured"
        assert captured[1]["messages"][:-1] == captured[0]["messages"]
        assert captured[1]["messages"][-1]["role"] == "user"
        for request in captured:
            text = json.dumps(request["messages"], ensure_ascii=False)
            assert not operator_ontology_hits(text)
            assert "private-blue" not in text and "private-green" not in text
            assert '"physical_goals"' not in text and "Give stage time" not in text
        case["requests"] = captured
        cases.append(case)
    prior.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen two actual public renderer requests plus static echo corrections")


async def run() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    provider = json.loads((ROOT / ".data/config.json").read_text())["providers"]["deepseek"]
    prior.DeepSeekAdapter().validate_api_base(provider["api_base"])
    cfg = {**CONFIG, "api_base": provider["api_base"], "api_key": provider["api_key"]}
    semaphore = asyncio.Semaphore(4)

    async def logical(case: dict, repeat: int) -> None:
        async with semaphore:
            stem = f"{case['id']}-{repeat}"
            game = dict_to_game_state(case["game"])
            game.session_id = str(uuid4())
            attempts = 0
            variants = []

            async def network(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                body = json.loads(request.content)
                assert body in case["requests"], "Renderer request drift"
                variant = case["requests"].index(body)
                variants.append(variant)
                name = f"{stem}-attempt{attempts}"
                path = runs / f"{name}.request.json"
                prior.write(path, body)
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
                prior.write(
                    runs / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError("curl failed; retained transport", request=request)
                return httpx.Response(int(status), content=raw, request=request)

            result = {
                "case": case["id"],
                "repeat": repeat,
                "session_id": game.session_id,
                "terminal_success": False,
            }
            async with session_lock(game.session_id):
                save_game(game)
                reloaded = load_game(game.session_id)
                assert reloaded is not None
                async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                    try:
                        text = await render(client, reloaded, case, cfg)
                        result.update(
                            terminal_success=True, narration=text, word_count=len(text.split())
                        )
                    except Exception as error:
                        result["error"] = f"{type(error).__name__}: {error}"
                prior.write(runs / f"{stem}.draft.json", game_state_to_dict(reloaded))
                persisted = load_game(game.session_id)
                assert persisted is not None
                assert game_state_to_dict(persisted) == game_state_to_dict(game)
            result.update(attempts=attempts, request_variants=variants)
            prior.write(runs / f"{stem}.result.json", result)
            print(
                stem,
                "terminal",
                result["terminal_success"],
                "attempts",
                attempts,
                "echo_correction",
                1 in variants,
                flush=True,
            )

    await asyncio.gather(
        *(logical(case, repeat) for case in manifest["cases"] for repeat in range(1, 5))
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
