"""English repetition of the frozen Portuguese split-contract fixture."""

from __future__ import annotations

import argparse
import asyncio
import contextvars
import copy
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "69-local-split"
DATA = Path(os.environ["ROLEPLAY_DATA_DIR"]).resolve()
assert DATA.is_relative_to(Path("/tmp")), "Use isolated /tmp data"
spec = importlib.util.spec_from_file_location("split_candidate", PRIOR / "chain.py")
assert spec and spec.loader
split: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split)
base = split.base

from src.models import dict_to_game_state, game_state_to_dict  # noqa: E402
from src.store.locks import session_lock  # noqa: E402
from src.store.sessions import load_game, save_game  # noqa: E402

TRANSLATIONS = {
    "portal azul": "blue portal",
    "portal verde": "green portal",
    "salão": "hall",
    "túnel": "tunnel",
    "pátio": "courtyard",
    "observatório": "observatory",
    "Noite": "Night",
    "lanterna": "lantern",
    "acesa": "lit",
    "azul aberto": "blue open",
    "Téo no túnel": "Téo in the tunnel",
    "saída": "exit",
    "Encontrar uma saída com cautela.": "Find a way out cautiously.",
    "Dar passagem a Téo pelo portal azul.": "Let Téo through the blue portal.",
    "A ventania fecha o portal azul.": "The gust closes the blue portal.",
    "A ventania fecha o portal azul. Téo permanece no salão.": (
        "The gust closes the blue portal. Téo remains in the hall."
    ),
}
CAUSES = {
    2: "Téo tries to push the blue portal to cross through, but the heavy bar does not budge. "
    "There is no new cause for opening or closing either portal.",
    3: "Bento removes the heavy bar and pulls the blue portal's leaf until it is completely open. "
    "His intervention is sufficient. Téo then tries to cross from the hall into the tunnel. "
    "There is no new cause for closing it and no change to the green portal.",
    4: "Neither portal changes and nobody changes zone this turn. Iara only watches "
    "the light of the lantern. There is no new gust of wind or new crossing attempt.",
    5: "A NEW strong gust pushes the blue portal's leaf and shuts it completely. "
    "Téo is already in the tunnel and stays there; nobody crosses this turn. "
    "The green portal does not change.",
}
ACTION = "I watch the light of my lantern."
CONFIG = {**base.CONFIG, "language": "en-US"}
EXPECTED = {
    2: ("closed", "hall"),
    3: ("open", "tunnel"),
    4: ("open", "tunnel"),
    5: ("closed", "tunnel"),
}
VIEW: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "english_prose_view", default=None
)


def translate(value: Any) -> Any:
    if isinstance(value, str):
        return TRANSLATIONS.get(value, value)
    if isinstance(value, list):
        return [translate(item) for item in value]
    if isinstance(value, dict):
        return {translate(key): translate(item) for key, item in value.items()}
    return value


# Only isolated imported contract labels change; schema shapes/validators do not.
base.CAUSES = CAUSES
base.candidate.STEPS_SCHEMA = translate(base.candidate.STEPS_SCHEMA)
split.CONTRACT = translate(split.CONTRACT)


class EnglishRunner(split.SplitRunner):
    async def _render_narration(
        self,
        game: Any,
        events: list[dict],
        turn_number: int,
        viewers: set[str] | None = None,
        **kwargs: Any,
    ) -> str:
        token = VIEW.set(
            {
                "viewers": sorted(viewers) if viewers is not None else None,
                "staging_viewers": sorted(kwargs["staging_viewers"])
                if kwargs.get("staging_viewers") is not None
                else None,
            }
        )
        try:
            return await super()._render_narration(
                game, events, turn_number, viewers=viewers, **kwargs
            )
        finally:
            VIEW.reset(token)


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        PRIOR / "manifest.json",
        PRIOR / "RESULT.md",
        PRIOR / "chain.py",
        HERE.parent / "69-local-chain/chain.py",
        HERE.parent / "69-runner-authority/candidate.py",
        HERE.parent / "69-runner-director-live/screen.py",
        ROOT / "tests/factories.py",
        *sorted((ROOT / "src").rglob("*.py")),
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def prepare() -> None:
    assert not (HERE / "manifest.json").exists(), "Preserve frozen manifest"
    prior = json.loads((PRIOR / "manifest.json").read_text())
    start = translate(copy.deepcopy(prior["start"]))
    assert translate(start) == start
    assert start["scene"]["zones"] == {
        "hall": ["tunnel", "courtyard"],
        "tunnel": ["hall"],
        "courtyard": ["hall"],
    }
    assert start["scene"]["positions"] == dict.fromkeys(("C1", "C2", "C3"), "hall")
    assert start["characters"] == prior["start"]["characters"]
    assert start["history"][0]["content"] == TRANSLATIONS[prior["start"]["history"][0]["content"]]
    # Frozen exact map must cover every changed free-form initial fixture string.
    remaining = [term for term in TRANSLATIONS if term in json.dumps(start, ensure_ascii=False)]
    assert not remaining, remaining
    process = await asyncio.create_subprocess_exec(
        "curl",
        "--silent",
        "--show-error",
        "http://127.0.0.1:8080/props",
        stdout=asyncio.subprocess.PIPE,
    )
    raw, _ = await process.communicate()
    assert process.returncode == 0
    props = json.loads(raw)
    settings = props["default_generation_settings"]
    server = {
        "model_path": props["model_path"],
        "n_ctx": settings["n_ctx"],
        "total_slots": props["total_slots"],
        "sampling": {
            k: settings.get("params", settings).get(k)
            for k in ("seed", "temperature", "top_p", "top_k")
        },
    }
    assert server == prior["server"], "Server identity/context/sampling changed since PT baseline"
    ps = await asyncio.create_subprocess_exec("ps", "-eo", "args", stdout=asyncio.subprocess.PIPE)
    args, _ = await ps.communicate()
    assert any(
        "llama-server " in line and "--reasoning off" in line and props["model_path"] in line
        for line in args.decode().splitlines()
    )
    write(
        HERE / "manifest.json",
        {
            "hashes": hashes(),
            "config": CONFIG,
            "start": start,
            "translations": TRANSLATIONS,
            "causes": CAUSES,
            "action": ACTION,
            "expected": EXPECTED,
            "server": server,
            "reasoning": "off",
            "repeats": 3,
            "contract": split.CONTRACT,
        },
    )
    print("Frozen three English four-submission chains; server matches Portuguese baseline")


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
                return True  # Same explicit observation mock as Portuguese.

            async def network(request: httpx.Request) -> httpx.Response:
                nonlocal attempts
                attempts += 1
                name = f"t{current}-call{attempts}"
                path = directory / f"{name}.request.json"
                body = json.loads(request.content)
                write(path, body)
                write(directory / f"{name}.scope.json", VIEW.get())
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

            summary: dict[str, Any] = {"session_id": sid, "turns": [], "complete": False}
            async with httpx.AsyncClient(transport=httpx.MockTransport(network)) as client:
                runner = EnglishRunner(client, CONFIG, review)
                for current in range(2, 6):
                    before = await runner.get_state(sid)
                    before_dict = game_state_to_dict(before)
                    write(directory / f"t{current}.start.json", before_dict)
                    result: dict[str, Any] = {"turn": current, "committed": False}
                    start_time = time.monotonic()
                    try:
                        output = await runner.player_turn(sid, action=ACTION, force_speaker="C2")
                        result["committed"] = True
                        write(directory / f"t{current}.output.json", output)
                    except Exception as error:
                        result["error"] = f"{type(error).__name__}: {error}"
                    result["wall_seconds"] = round(time.monotonic() - start_time, 3)
                    persisted = await runner.get_state(sid)
                    state = game_state_to_dict(persisted)
                    write(directory / f"t{current}.persisted.json", state)
                    projection = base.candidate.project(persisted, current)
                    result["projection"] = projection
                    if result["committed"]:
                        blue, teo = EXPECTED[current]
                        result["state_pass"] = projection["apertures"] == {
                            "blue portal": blue,
                            "green portal": "closed",
                        } and projection["positions"] == {
                            "Iara": "hall",
                            "Bento": "hall",
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
                        f"chain{repeat} turn{current}: committed={result['committed']} "
                        f"state={result.get('state_pass')} error={result.get('error')}",
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
