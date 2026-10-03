"""Full Runner lab screen for explicit author-owned disclosure operations."""

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
MANIFEST = HERE / "owned-disclosure-manifest.json"
OUT = HERE / "owned-disclosure-result.json"


async def main(command: str) -> None:
    isolated = Path(tempfile.mkdtemp(prefix="tavern-owned-disclosure-screen-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(isolated)

    import httpx
    from owned_disclosure_boundary import ReadAuthorization, prepare_disclosure

    import src.runner as runner_module
    from src.models import CharacterPerspective
    from src.paths import DATA_DIR
    from src.runner import Runner
    from src.store.sessions import save_game
    from tests.factories import make_character

    assert DATA_DIR.resolve() == isolated.resolve()
    spec = importlib.util.spec_from_file_location(
        "owned_lab_cognition", HERE / "director_cognition.py"
    )
    assert spec is not None and spec.loader is not None
    cognition: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cognition)
    baseline = cognition.baseline
    cases = ["holding", "reading", "reading_plus_question", "wrong_source", "stale", "wide", "npc"]
    paths = [
        Path(__file__),
        HERE / "owned_disclosure_boundary.py",
        HERE / "OWNED-DISCLOSURE-PREREGISTRATION.md",
        HERE / "director_cognition.py",
        HERE / "director_refusal.py",
        ROOT / "src/runner.py",
        ROOT / "src/models.py",
        ROOT / "src/perception.py",
        ROOT / "src/store/sessions.py",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
    ]
    mapping = json.loads((HERE / "director-cognition-reader-mapping.json").read_text())
    source = HERE / "director-cognition" / (mapping["observable_clue-A"] + ".normalized.json")
    paths.append(source)
    hashes = {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}
    if command == "prepare":
        assert not MANIFEST.exists(), "Preserve previous manifest"
        baseline.write(MANIFEST, {"hashes": hashes, "cases": cases})
        print("Frozen seven program-boundary cases; no provider calls")
        return
    assert json.loads(MANIFEST.read_text())["hashes"] == hashes
    assert not OUT.exists(), "Preserve previous result"
    original = json.loads(source.read_text())

    async def fake_initialize(*args: Any, **kwargs: Any) -> CharacterPerspective:
        return CharacterPerspective(
            initialized_turn=kwargs.get("turn_number", 0),
            processed_through_turn=kwargs.get("turn_number", 0),
        )

    runner_module.initialize_perspective = fake_initialize
    rows = []
    for case_id in cases:
        definition = next(c for c in cognition.definitions() if c["id"] == "observable_clue")
        game = cognition.game_for(definition)
        game.session_id = str(uuid4())
        game.roteiro = None
        game.characters["C3"] = make_character("Clara")
        game.scene.present_characters.append("C3")
        game.scene.positions["C3"] = game.scene.location
        content = "A Dama do Norte é Glinda, que planeja a conquista das cinco cidades."
        game.scene.physical_facts["cifra"] = content
        game.scene.physical_facts["outro_documento"] = "O outro documento fala de uma ponte."
        before = len(game.history)
        save_game(game)
        draft = copy.deepcopy(original)
        draft["next_speakers"] = []
        # The real negative draft's controlled speech is kept; unrelated NPC
        # briefs are reserved for the dedicated permitted-NPC control.
        draft["perception_events"] = [
            event
            for event in draft["perception_events"]
            if event["event_kind"] != "audible_speech" or event["subject_id"] == "C1"
        ]
        authorization = None
        operation_source = "cifra"
        listeners: tuple[str, ...] = ("C2",)
        action = ""
        if case_id not in ("holding", "npc"):
            action = "Leio a cifra decifrada em voz alta para Bento."
            authorization = ReadAuthorization(game.session_id, "C1", 4, "cifra", ("C2",))
            if case_id == "wrong_source":
                operation_source = "outro_documento"
            elif case_id == "stale":
                authorization = ReadAuthorization(game.session_id, "C1", 3, "cifra", ("C2",))
            elif case_id == "wide":
                listeners = ("C2", "C3")
            if case_id == "reading":
                draft["perception_events"] = [
                    e for e in draft["perception_events"] if e["event_kind"] != "audible_speech"
                ]
        if case_id == "npc":
            draft["perception_events"].append(
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C2",
                    "content": "Bento anuncia que consegue ver marcas junto ao encaixe.",
                    "witness_ids": ["C1", "C3"],
                }
            )
        rendered: list[dict[str, Any]] = []
        contexts: list[dict[str, Any]] = []

        async def replay_director(
            state: Any,
            step: int,
            _draft: dict[str, Any] = draft,
            _authorization: ReadAuthorization | None = authorization,
            _source: str = operation_source,
            _listeners: tuple[str, ...] = listeners,
            **kwargs: Any,
        ) -> dict[str, Any]:
            return prepare_disclosure(state, _draft, step, _authorization, _source, _listeners)

        async def character_reply(
            state: Any,
            character_id: str,
            context: str,
            step: int,
            _contexts: list[dict[str, Any]] = contexts,
            **kwargs: Any,
        ) -> dict[str, str]:
            assert character_id != state.player.controlled_character_id
            _contexts.append({"character": character_id, "context": context})
            return {"speech": "Vejo marcas junto ao encaixe.", "thought": "Examino a pista."}

        async def fake_prose(
            state: Any,
            events: list[dict[str, Any]],
            step: int,
            _rendered: list[dict[str, Any]] = rendered,
            **kwargs: Any,
        ) -> str:
            _rendered.append({"events": copy.deepcopy(events), "viewers": kwargs.get("viewers")})
            return "\n".join(e["content"] for e in events if e["event_kind"] != "audible_speech")

        error = None
        async with httpx.AsyncClient(transport=httpx.MockTransport(forbid_network)) as client:
            runner: Any = Runner(client, {"language": "Portuguese", "auto_event_enabled": False})
            runner._call_narrator = replay_director
            runner._call_character = character_reply
            runner._render_narration = fake_prose
            try:
                await runner.player_turn(
                    game.session_id,
                    speech="Continuo segurando o mapa." if not action else "",
                    action=action,
                )
            except ValueError as exc:
                error = str(exc)
            loaded = await runner.get_state(game.session_id)
        assert loaded is not None
        records = [asdict(record) for record in loaded.history[before:]]
        leaked_question = any("pergunta se as marcas" in record["content"] for record in records)
        assert not leaked_question
        assert not any("pergunta se as marcas" in str(value) for value in [rendered, contexts])
        if case_id in ("wrong_source", "stale", "wide"):
            assert error and not records and not rendered and not contexts
        elif case_id in ("reading", "reading_plus_question"):
            assert error is None
            disclosed = [record for record in loaded.history[before:] if content in record.content]
            assert disclosed
            assert all(
                record.audience is not None and "C3" not in record.audience for record in disclosed
            )
            assert any(record.audience and "C2" in record.audience for record in disclosed)
        elif case_id == "npc":
            assert error is None and any(
                record["speaker"] == "C2" and record["content_type"] == "speech"
                for record in records
            )
        else:
            assert error is None
        rows.append(
            {
                "case": case_id,
                "error": error,
                "records": records,
                "renderer_inputs": rendered,
                "character_contexts": contexts,
            }
        )
    baseline.write(OUT, {"isolated_data_root": str(isolated), "cases": rows})
    print(json.dumps({"passed": cases, "isolated_data_root": str(isolated)}))


def forbid_network(request: Any) -> Any:
    raise AssertionError(f"Unexpected network call: {request.method}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(main(parser.parse_args().command))
