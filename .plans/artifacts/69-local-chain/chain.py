"""Actual local model calls through isolated AuthorityRunner transactions."""

from __future__ import annotations

import argparse
import asyncio
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
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA.is_relative_to(Path("/tmp")), "Use an isolated /tmp data directory"


def module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


fixture_module = module("director_fixture", HERE.parent / "69-runner-director-live/screen.py")
candidate = fixture_module.candidate

from src.models import dict_to_game_state, game_state_to_dict  # noqa: E402
from src.store.locks import session_lock  # noqa: E402
from src.store.sessions import load_game, save_game  # noqa: E402

CONFIG = {
    "provider": "llama_cpp",
    "api_base": "http://127.0.0.1:8080/v1",
    "model": "",
    "context_max": 32768,
    "max_tokens_narrator": 4096,
    "max_tokens_character": 1024,
    "narrator_min_words": 600,
    "character_max_sentences": 5,
    "llm_timeout_seconds": 240,
    "language": "pt-BR",
    "autonomous_burst_max_beats": 1,
    "automatic_compaction_enabled": False,
    "watcher_enabled": False,
}
CAUSES = {
    2: "Téo tenta empurrar o portal azul para atravessar, mas a barra pesada não cede. "
    "Não há causa nova de abertura ou fechamento de qualquer portal.",
    3: "Bento retira a barra pesada e puxa a folha do portal azul até abrir completamente. "
    "Sua intervenção é suficiente. Téo então tenta atravessar do salão para o túnel. "
    "Não há nova causa de fechamento nem mudança no portal verde.",
    4: "Nenhum portal muda e ninguém muda de zona neste turno. Iara apenas observa "
    "a luz da lanterna. Não há nova ventania nem nova tentativa de travessia.",
    5: "Uma NOVA rajada forte empurra a folha do portal azul e fecha-a completamente. "
    "Téo já está no túnel e fica lá; ninguém atravessa neste turno. O portal verde não muda.",
}
EXPECTED = {
    2: ("closed", "salão"),
    3: ("open", "túnel"),
    4: ("open", "túnel"),
    5: ("closed", "túnel"),
}


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hashes() -> dict[str, str]:
    files = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        HERE.parent / "69-runner-authority/candidate.py",
        HERE.parent / "69-runner-director-live/screen.py",
        ROOT / "tests/factories.py",
        *sorted((ROOT / "src").rglob("*.py")),
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


class LocalRunner(candidate.AuthorityRunner):
    async def _call_narrator(self, game: Any, turn_number: int, *args: Any, **kwargs: Any) -> dict:
        context = list(kwargs.pop("extra_context", None) or [])
        context.append(
            "SOURCE FOR THIS BEAT (supported causes, not yet committed): "
            + json.dumps({"new_causes": {"value": CAUSES[turn_number]}}, ensure_ascii=False)
        )
        return await super()._call_narrator(
            game, turn_number, *args, extra_context=context, **kwargs
        )


async def prepare() -> None:
    assert not (HERE / "manifest.json").exists(), "Preserve frozen inputs"
    case = fixture_module.fixture(0)
    game = dict_to_game_state(case["game"])
    game.history = [record for record in game.history if record.turn_number == 1]
    game.roteiro.beat_started_turn = 2
    attempts = game.plugin_state["authority_fixture"]["attempts_by_turn"]
    attempts["3"] = attempts["2"]
    props_process = await asyncio.create_subprocess_exec(
        "curl",
        "--silent",
        "--show-error",
        "http://127.0.0.1:8080/props",
        stdout=asyncio.subprocess.PIPE,
    )
    raw, _ = await props_process.communicate()
    assert props_process.returncode == 0
    props = json.loads(raw)
    settings = props["default_generation_settings"]
    assert settings["n_ctx"] == 32768
    assert "StyleTune-QK-Heretic.i1-IQ4_XS" in props["model_path"]
    write(
        HERE / "manifest.json",
        {
            "hashes": hashes(),
            "config": CONFIG,
            "start": game_state_to_dict(game),
            "causes": CAUSES,
            "expected": EXPECTED,
            "repeats": 3,
            "server": {
                "model_path": props["model_path"],
                "n_ctx": settings["n_ctx"],
                "total_slots": props["total_slots"],
                "sampling": {
                    key: settings.get("params", settings).get(key)
                    for key in ("seed", "temperature", "top_p", "top_k")
                },
            },
        },
    )
    print("Frozen three four-submission local chains, no provider calls")


async def run() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert manifest["hashes"] == hashes(), "Frozen source drift"
    runs = HERE / "runs"
    runs.mkdir()
    semaphore = asyncio.Semaphore(2)

    async def chain(repeat: int) -> None:
        async with semaphore:
            directory = runs / f"chain{repeat}"
            directory.mkdir()
            game = dict_to_game_state(manifest["start"])
            game.session_id = str(uuid4())
            sid = game.session_id
            async with session_lock(sid):
                save_game(game)
            current = 2
            attempts = 0
            reviews = []

            async def review(stage: str, payload: dict) -> bool:
                reviews.append({"turn": current, "stage": stage, "payload": payload})
                return True  # Explicit observation double, NOT semantic admission.

            async def network(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                name = f"t{current}-call{attempts}"
                path = directory / f"{name}.request.json"
                write(path, json.loads(request.content))
                process = await asyncio.create_subprocess_exec(
                    "curl",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "240",
                    "--request",
                    "POST",
                    "--header",
                    "Content-Type: application/json",
                    "--data-binary",
                    "@" + str(path),
                    "--write-out",
                    "\n%{http_code}",
                    str(request.url),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()
                raw, _, status = stdout.rpartition(b"\n")
                (directory / f"{name}.raw.json").write_bytes(raw)
                write(
                    directory / f"{name}.transport.json",
                    {
                        "exit_code": process.returncode,
                        "http_status": status.decode(),
                        "stderr": stderr.decode(),
                    },
                )
                if process.returncode or not status.isdigit() or int(status) == 0:
                    raise httpx.RequestError("curl failed; retained transport", request=request)
                return httpx.Response(int(status), content=raw, request=request)

            summary = {"session_id": sid, "turns": [], "complete": False}
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                runner = LocalRunner(client, CONFIG, review)
                for current in range(2, 6):
                    before = await runner.get_state(sid)
                    before_dict = game_state_to_dict(before)
                    write(directory / f"t{current}.start.json", before_dict)
                    result: dict[str, Any] = {"turn": current, "committed": False}
                    try:
                        output = await runner.player_turn(
                            sid, action="Observo a luz da minha lanterna.", force_speaker="C2"
                        )
                        write(directory / f"t{current}.output.json", output)
                        result["committed"] = True
                    except Exception as error:
                        result["error"] = f"{type(error).__name__}: {error}"
                    persisted = await runner.get_state(sid)
                    state = game_state_to_dict(persisted)
                    write(directory / f"t{current}.persisted.json", state)
                    projection = candidate.project(persisted, current)
                    result["projection"] = projection
                    if result["committed"]:
                        blue, teo = EXPECTED[current]
                        result["state_pass"] = projection["apertures"] == {
                            "portal azul": blue,
                            "portal verde": "closed",
                        } and projection["positions"] == {
                            "Iara": "salão",
                            "Bento": "salão",
                            "Téo": teo,
                        }
                        async with session_lock(sid):
                            reloaded = load_game(sid)
                            result["reload_pass"] = game_state_to_dict(reloaded) == state
                    else:
                        result["rollback_pass"] = state == before_dict
                    summary["turns"].append(result)
                    write(directory / "reviews.json", reviews)
                    write(directory / "result.json", summary)
                    print(
                        f"chain{repeat} turn{current}: {json.dumps(result, ensure_ascii=False)}",
                        flush=True,
                    )
                    if not result["committed"] or not result["state_pass"]:
                        break
            summary["complete"] = len(summary["turns"]) == 4 and all(
                r["committed"] and r["state_pass"] and r["reload_pass"] for r in summary["turns"]
            )
            summary["calls"] = attempts
            write(directory / "result.json", summary)
            (directory / "debug.jsonl").write_bytes(
                (DATA / "sessions" / sid / "debug.jsonl").read_bytes()
            )

    await asyncio.gather(*(chain(repeat) for repeat in range(1, 4)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
