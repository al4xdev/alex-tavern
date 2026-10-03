"""Exact real drafts replayed through isolated production Runner consumers."""

from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "speech-basis-full-turn-result.json"
MANIFEST = HERE / "speech-basis-full-turn-manifest.json"


async def main(command: str) -> None:
    isolated = Path(tempfile.mkdtemp(prefix="tavern-speech-basis-full-turn-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(isolated)
    import httpx

    import src.runner as runner_module
    from src.agents.narrator import narrate
    from src.agents.prose import build_prose_messages
    from src.models import CharacterPerspective
    from src.paths import DATA_DIR
    from src.runner import Runner
    from src.store.sessions import save_game

    assert DATA_DIR.resolve() == isolated.resolve()
    spec = importlib.util.spec_from_file_location("basis_screen", HERE / "speech_basis_screen.py")
    assert spec and spec.loader
    screen: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)
    paths = [
        Path(__file__),
        HERE / "SPEECH-BASIS-FULL-TURN-PREREGISTRATION.md",
        HERE / "speech_basis_screen.py",
        ROOT / "src/runner.py",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/agents/prose.py",
        ROOT / "src/models.py",
        ROOT / "src/store/sessions.py",
    ]
    sources = [("holding", "holding_control-1"), ("npc", "npc_basis-2")]
    paths.extend(HERE / "speech-basis-runs" / (label + ".result.json") for _, label in sources)
    hashes = {str(p.relative_to(ROOT)): screen.baseline.digest(p) for p in paths}
    if command == "prepare":
        assert not MANIFEST.exists()
        screen.baseline.write(MANIFEST, {"hashes": hashes, "sources": sources})
        print("Frozen two exact real drafts; network forbidden")
        return
    assert json.loads(MANIFEST.read_text())["hashes"] == hashes and not OUT.exists()

    async def fake_initialize(*args: Any, **kwargs: Any) -> CharacterPerspective:
        return CharacterPerspective(
            initialized_turn=kwargs.get("turn_number", 0),
            processed_through_turn=kwargs.get("turn_number", 0),
        )

    runner_module.initialize_perspective = fake_initialize
    rows = []
    for case, label in sources:
        game = screen.game_for(case)
        game.session_id = str(uuid4())
        save_game(game)
        before = len(game.history)
        original = json.loads((HERE / "speech-basis-runs" / (label + ".result.json")).read_text())[
            "output"
        ]
        events = copy.deepcopy(original["perception_events"])
        captured: list[dict[str, Any]] = []

        def normalization_transport(
            request: httpx.Request, source: dict[str, Any] = original
        ) -> httpx.Response:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps(source)}}]}
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(normalization_transport)
        ) as client:
            normalized = await narrate(
                client,
                game.scene,
                game.characters,
                "C1",
                game.history,
                {
                    "provider": "deepseek",
                    "model": "deepseek-chat",
                    "api_key": "",
                    "api_base": "https://api.deepseek.com",
                    "language": "Portuguese",
                },
                session_id=game.session_id,
                turn_number=4,
            )

        async def replay_director(
            *args: Any, _raw: dict[str, Any] = normalized, **kwargs: Any
        ) -> dict[str, Any]:
            return copy.deepcopy(_raw)

        async def character_reply(
            state: Any,
            actor: str,
            context: str,
            step: int,
            _captured: list[dict[str, Any]] = captured,
            **kwargs: Any,
        ) -> dict[str, str]:
            _captured.append(
                {
                    "consumer": "character",
                    "actor": actor,
                    "context": context,
                    "speech_intents": kwargs.get("speech_intents"),
                }
            )
            return {"speech": "Ainda não vou explicar as marcas.", "thought": "Prefiro aguardar."}

        async def renderer(
            state: Any,
            projected: list[dict[str, Any]],
            step: int,
            viewers: set[str] | None = None,
            _captured: list[dict[str, Any]] = captured,
            **kwargs: Any,
        ) -> str:
            messages = build_prose_messages(
                state.scene,
                state.characters,
                "C1",
                state.history,
                projected,
                viewers=viewers,
                **kwargs,
            )
            _captured.append({"consumer": "prose", "messages": messages})
            return "\n".join(
                line for line in messages[1]["content"].splitlines() if line.startswith("  - (")
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(forbid_network)) as client:
            runner: Any = Runner(client, {"language": "Portuguese", "auto_event_enabled": False})
            runner._call_narrator = replay_director
            runner._call_character = character_reply
            runner._render_narration = renderer
            await runner.player_turn(game.session_id, skip=True)
            loaded = await runner.get_state(game.session_id)
        assert loaded is not None
        records = [asdict(r) for r in loaded.history[before:]]
        target = next(
            e["content"] for e in events if e["subject_id"] == ("C1" if case == "holding" else "C2")
        )
        rows.append(
            {
                "case": case,
                "source": label,
                "normalized": normalized,
                "consumers": captured,
                "new_records": records,
                "target": target,
                "target_persisted": any(target in r["content"] for r in records),
            }
        )
    screen.baseline.write(OUT, {"isolated_data_root": str(isolated), "cases": rows})
    print(
        json.dumps(
            {
                "counterexamples": [
                    {"case": r["case"], "target_persisted": r["target_persisted"]} for r in rows
                ]
            }
        )
    )


def forbid_network(request: Any) -> Any:
    raise AssertionError(f"Unexpected network call: {request.method}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(main(parser.parse_args().command))
