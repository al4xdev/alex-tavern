"""Trace one real controlled-character brief through Runner and isolated storage."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4


async def main() -> None:
    # Set storage before importing any application modules; never use real data.
    isolated = Path(tempfile.mkdtemp(prefix="tavern-controlled-report-trace-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(isolated)

    import httpx

    from src.paths import DATA_DIR
    from src.runner import Runner
    from src.store.sessions import load_game, save_game

    assert DATA_DIR.resolve() == isolated.resolve()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    assert DATA_DIR.resolve() != (root / ".data").resolve()
    spec = importlib.util.spec_from_file_location("trace_cognition", here / "director_cognition.py")
    assert spec is not None and spec.loader is not None
    cognition: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cognition)
    case = next(c for c in cognition.definitions() if c["id"] == "observable_clue")
    game = cognition.game_for(case)
    game.session_id = str(uuid4())
    mapping = json.loads((here / "director-cognition-reader-mapping.json").read_text())
    label = mapping["observable_clue-A"]
    raw = json.loads((here / "director-cognition" / f"{label}.normalized.json").read_text())
    before = len(game.history)

    async with httpx.AsyncClient(transport=httpx.MockTransport(forbid_network)) as client:
        runner = Runner(client, {"language": "Portuguese", "auto_event_enabled": False})
        intents = runner._admissible_speech_intents(game, raw, 4)
        controlled = [
            i for i in intents if i[0]["subject_id"] == game.player.controlled_character_id
        ]
        assert len(controlled) == 1
        await runner._resolve_speech_intents(game, controlled, set(), [], 4)
    save_game(game)
    loaded = load_game(game.session_id)
    assert loaded is not None
    after = [
        {"speaker": r.speaker, "type": r.content_type, "content": r.content, "audience": r.audience}
        for r in loaded.history[before:]
    ]
    result = {
        "method": (
            "One normalized real Director brief; partial Runner resolver and save/load, "
            "not a full turn"
        ),
        "source": label,
        "isolated_data_root": str(isolated),
        "supplied_human_speech": (
            "Continuo segurando o mapa. Não vou entregá-lo nem colocá-lo no chão."
        ),
        "human_action_at_last_turn": [
            r.content
            for r in game.history
            if r.turn_number == 3 and r.content_type == "action" and r.speaker == "Player"
        ],
        "persisted_new_records": after,
    }
    (here / "controlled-report-trace.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False))


def forbid_network(request: Any) -> Any:
    raise AssertionError(f"Unexpected network call: {request.method}")


if __name__ == "__main__":
    asyncio.run(main())
