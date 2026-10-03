"""Read-only real-session comparison through curl, with isolated debug evidence."""

# ruff: noqa: E402 — isolate runtime paths before importing application modules
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "alex-tavern"
OUT = Path(__file__).parent / "private" / "v2"
OUT.mkdir(parents=True, exist_ok=True)
os.environ["ROLEPLAY_DATA_DIR"] = str(OUT / "data")

import httpx

from src.agents.suggest import suggest_moves
from src.config import load_config, resolve_active_config
from src.models import SESSION_SCHEMA_VERSION, dict_to_game_state


class CurlTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        body = await request.aread()
        with tempfile.NamedTemporaryFile(suffix=".json") as payload:
            payload.write(body)
            payload.flush()
            settings = "url = " + json.dumps(str(request.url)) + "\n"
            settings += "\n".join(
                "header = " + json.dumps(f"{key}: {value}")
                for key, value in request.headers.items()
                if key.lower() != "content-length"
            )
            process = await asyncio.create_subprocess_exec(
                "curl",
                "--silent",
                "--compressed",
                "--show-error",
                "--fail-with-body",
                "--max-time",
                "90",
                "--config",
                "-",
                "--data-binary",
                "@" + payload.name,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            response, error = await process.communicate(settings.encode())
            if process.returncode:
                raise RuntimeError(f"curl failed with status {process.returncode}")
            return httpx.Response(200, content=response, request=request)


async def main():
    config = resolve_active_config(load_config(SOURCE / ".data/config.json"))
    old = types.ModuleType("baseline_suggest")
    exec(
        subprocess.check_output(
            ["git", "show", "06abc87:src/agents/suggest.py"], cwd=ROOT, text=True
        ),
        old.__dict__,
    )
    selected = []
    for case in (0, 1):
        frozen = OUT.parent / f"case-{case}.json"
        raw = frozen.read_bytes()
        state = json.loads(raw)
        assert state["schema_version"] == SESSION_SCHEMA_VERSION
        selected.append((len(state["history"]), frozen, raw, state))
    records = []
    async with httpx.AsyncClient(transport=CurlTransport()) as client:
        for case, (_, path, raw, state) in enumerate(selected):
            game = dict_to_game_state(state)
            target = game.player.controlled_character_id
            (OUT / f"case-{case}.json").write_text(json.dumps(state, ensure_ascii=False, indent=2))
            for repetition in range(3):
                common = {
                    "client": client,
                    "scene": game.scene,
                    "characters": game.characters,
                    "target_id": target,
                    "history": game.history,
                    "config": config,
                    "narrator_directives": game.narrator_directives,
                    "turn_number": game.history[-1].turn_number,
                    "viewer_perspective": game.character_perspectives.get(target),
                }
                baseline, candidate = await asyncio.gather(
                    old.suggest_moves(**common, session_id=f"case-{case}-baseline-{repetition}"),
                    suggest_moves(
                        **common,
                        dispositions=game.dispositions,
                        session_id=f"case-{case}-candidate-{repetition}",
                    ),
                )
                records.append(
                    {
                        "case": case,
                        "repetition": repetition,
                        "baseline": baseline,
                        "candidate": candidate,
                    }
                )
                (OUT / "results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
                print(f"case {case}, repetition {repetition}: both completed", flush=True)
            assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(raw).digest()
    print("Source snapshots unchanged", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
