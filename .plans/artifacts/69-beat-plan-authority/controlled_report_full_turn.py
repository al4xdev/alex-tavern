"""Full isolated Runner turn consuming an exact normalized real Director draft."""

from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4


async def main() -> None:
    isolated = Path(tempfile.mkdtemp(prefix="tavern-controlled-full-turn-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(isolated)

    import httpx

    import src.runner as runner_module
    from src.models import CharacterPerspective
    from src.paths import DATA_DIR
    from src.runner import Runner
    from src.store.sessions import save_game

    assert DATA_DIR.resolve() == isolated.resolve()
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "full_turn_cognition", here / "director_cognition.py"
    )
    assert spec is not None and spec.loader is not None
    cognition: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cognition)
    case = next(c for c in cognition.definitions() if c["id"] == "observable_clue")
    game = cognition.game_for(case)
    game.session_id = str(uuid4())
    before = len(game.history)
    save_game(game)
    mapping = json.loads((here / "director-cognition-reader-mapping.json").read_text())
    label = mapping["observable_clue-A"]
    raw = json.loads((here / "director-cognition" / f"{label}.normalized.json").read_text())
    contexts: list[dict[str, Any]] = []

    async def fake_initialize(*args: Any, **kwargs: Any) -> CharacterPerspective:
        return CharacterPerspective(
            initialized_turn=kwargs.get("turn_number", 0),
            processed_through_turn=kwargs.get("turn_number", 0),
        )

    async def replay_director(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return copy.deepcopy(raw)

    async def character_reply(
        state: Any, character_id: str, context: str, turn_number: int, **kwargs: Any
    ) -> dict[str, str]:
        assert character_id != state.player.controlled_character_id
        contexts.append({"character": character_id, "context": context})
        return {"speech": "Vejo marcas junto ao encaixe.", "thought": "Preciso examinar a pista."}

    async def fake_prose(*args: Any, **kwargs: Any) -> str:
        return "A pedra solta expõe marcas na parede sul."

    runner_module.initialize_perspective = fake_initialize
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbid_network)) as client:
        runner: Any = Runner(client, {"language": "Portuguese", "auto_event_enabled": False})
        runner._call_narrator = replay_director
        runner._call_character = character_reply
        runner._render_narration = fake_prose
        await runner.player_turn(
            game.session_id,
            speech="Continuo segurando o mapa. Não vou entregá-lo nem colocá-lo no chão.",
        )
        loaded = await runner.get_state(game.session_id)
    assert loaded is not None
    result = {
        "method": (
            "Full Runner player_turn replay; Director real frozen output, "
            "Character/prose/perspective stubs"
        ),
        "isolated_data_root": str(isolated),
        "source": label,
        "new_records": [
            {"speaker": r.speaker, "type": r.content_type, "content": r.content}
            for r in loaded.history[before:]
        ],
        "character_contexts": contexts,
    }
    output = here / "controlled-report-full-turn.json"
    assert not output.exists(), "Preserve previous replay"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


def forbid_network(request: Any) -> Any:
    raise AssertionError(f"Unexpected network call: {request.method}")


if __name__ == "__main__":
    asyncio.run(main())
