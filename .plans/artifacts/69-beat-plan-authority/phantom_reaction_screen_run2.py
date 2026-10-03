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
MANIFEST = HERE / "phantom-reaction-run2-manifest.json"
OUT = HERE / "phantom-reaction-run2-result.json"


async def main(command: str) -> None:
    isolated = Path(tempfile.mkdtemp(prefix="tavern-owned-disclosure-screen-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(isolated)

    import httpx
    from owned_disclosure_boundary import ReadAuthorization, prepare_disclosure

    import src.runner as runner_module
    from src.agents.prose import build_prose_messages
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
    cases = ["holding"]
    paths = [
        Path(__file__),
        HERE / "owned_disclosure_boundary.py",
        HERE / "PHANTOM-REACTION-RUN2-PREREGISTRATION.md",
        HERE / "director_cognition.py",
        HERE / "director_refusal.py",
        ROOT / "src/runner.py",
        ROOT / "src/models.py",
        ROOT / "src/agents/prose.py",
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
        print("Frozen one adversarial program-boundary case; no provider calls")
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
        sources = {"cifra": content, "outro_documento": "O outro documento fala de uma ponte."}
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
        draft["next_speakers"] = ["C2"]
        draft["perception_events"].append(
            {
                "event_kind": "audible_speech",
                "subject_id": "C2",
                "content": "Bento responde à pergunta de Iara sobre onde encaixar o mapa.",
                "witness_ids": ["C1", "C3"],
            }
        )
        rendered: list[dict[str, Any]] = []
        contexts: list[dict[str, Any]] = []

        async def replay_director(
            state: Any,
            step: int,
            *unused: Any,
            _draft: dict[str, Any] = draft,
            _authorization: ReadAuthorization | None = authorization,
            _source: str = operation_source,
            _listeners: tuple[str, ...] = listeners,
            _sources: dict[str, str] = sources,
            **kwargs: Any,
        ) -> dict[str, Any]:
            return prepare_disclosure(
                state, _draft, step, _authorization, _source, _listeners, _sources
            )

        async def character_reply(
            state: Any,
            character_id: str,
            context: str,
            step: int,
            *unused: Any,
            _contexts: list[dict[str, Any]] = contexts,
            **kwargs: Any,
        ) -> dict[str, str]:
            assert character_id != state.player.controlled_character_id
            _contexts.append(
                {
                    "character": character_id,
                    "context": context,
                    "speech_intents": kwargs.get("speech_intents"),
                }
            )
            return {"speech": "Vejo marcas junto ao encaixe.", "thought": "Examino a pista."}

        async def fake_prose(
            state: Any,
            events: list[dict[str, Any]],
            step: int,
            viewers: set[str] | None = None,
            blocking: dict[str, str] | None = None,
            *,
            _rendered: list[dict[str, Any]] = rendered,
            **kwargs: Any,
        ) -> str:
            messages = build_prose_messages(
                state.scene,
                state.characters,
                state.player.controlled_character_id,
                state.history,
                events,
                viewers=viewers,
                blocking=blocking,
            )
            _rendered.append(
                {"messages": messages, "viewers": sorted(viewers) if viewers else None}
            )
            return "\n".join(
                line for line in messages[1]["content"].splitlines() if line.startswith("  - (")
            )

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
            assert all(
                content not in str(entry["messages"])
                for entry in rendered
                if entry["viewers"] and "C3" in entry["viewers"]
            )
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
    gate = not any(
        "Bento responde à pergunta de Iara" in str([row["character_contexts"], row["records"]])
        for row in rows
    )
    print(json.dumps({"no_phantom_question_context": gate, "isolated_data_root": str(isolated)}))
    assert gate, "NPC context still responds to the removed human question"


def forbid_network(request: Any) -> Any:
    raise AssertionError(f"Unexpected network call: {request.method}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    command = parser.parse_args().command
    try:
        asyncio.run(main(command))
    except Exception as exc:
        if command == "run":
            (HERE / "phantom-reaction-run2-failure.json").write_text(
                json.dumps({"type": type(exc).__name__, "error": str(exc)}) + "\n"
            )
        raise
