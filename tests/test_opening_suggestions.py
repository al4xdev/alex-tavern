"""Task 48: scenario-only, ephemeral openings composed with native hint + skip."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from src.agents.narrator import (
    build_opening_suggestions_messages,
    build_opening_suggestions_schema,
)
from src.llm.schema import JSONSchemaValidationError, validate_json_schema
from src.models import Scene, game_state_to_dict
from src.store.sessions import _get_lock, delete_session

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "static"

SCENE = Scene(
    location="Taverna da Ponte",
    time_of_day="noite chuvosa",
    present_characters=["C1", "C2", "Player"],
    physical_facts={"door": "closed", "fire": "low"},
)
OPENINGS = [
    "Uma batida ecoa na porta; quem percebe tem motivo para comentar sobre o som...",
    "A lareira apaga de repente; quem percebe tem motivo para comentar sobre a escuridão...",
    "Um envelope surge no balcão; quem percebe tem motivo para comentar sobre a carta...",
]
RAW_OPENINGS = [
    {
        "event": "Uma batida ecoa na porta",
        "conversation_hook": "quem percebe tem motivo para comentar sobre o som",
    },
    {
        "event": "A lareira apaga de repente",
        "conversation_hook": "quem percebe tem motivo para comentar sobre a escuridão",
    },
    {
        "event": "Um envelope surge no balcão",
        "conversation_hook": "quem percebe tem motivo para comentar sobre a carta",
    },
]


class TestOpeningContract:
    def test_schema_requires_exactly_three_bounded_ellipses(self) -> None:
        schema = build_opening_suggestions_schema()["schema"]
        fields = schema["properties"]["suggestions"]["items"]["properties"]
        assert fields["event"]["maxLength"] == 140
        assert fields["conversation_hook"]["maxLength"] == 120
        assert "6-to-12-word clause" in fields["conversation_hook"]["description"]
        validate_json_schema({"suggestions": RAW_OPENINGS}, schema)
        with pytest.raises(JSONSchemaValidationError):
            validate_json_schema({"suggestions": RAW_OPENINGS[:2]}, schema)
        with pytest.raises(JSONSchemaValidationError, match="required"):
            validate_json_schema(
                {"suggestions": [*RAW_OPENINGS[:2], {"event": "Sem gancho de conversa"}]},
                schema,
            )

    def test_prompt_contains_scenario_but_no_character_surface(self) -> None:
        messages = build_opening_suggestions_messages(SCENE, "Mantenha o tom de mistério.")
        system = messages[0]["content"]
        user = messages[1]["content"]

        assert "Taverna da Ponte" in user and '"door": "closed"' in user
        assert "Mantenha o tom de mistério" in user
        assert "present_characters" not in user
        assert all(token not in user for token in ("C1", "C2", "Player"))
        assert "Never name or describe a character" in system
        assert "quiet observer may simply watch" in system
        assert user.rfind("FINAL OUTPUT CONTRACT") > user.rfind("world_directives")
        assert "Do not require everyone" in user

    @pytest.mark.asyncio
    async def test_call_uses_opening_debug_identity_and_small_budget(self, monkeypatch) -> None:  # noqa: ANN001
        from src.agents import narrator as narrator_mod

        captured: dict = {}

        async def fake_json(client, messages, **kwargs):  # noqa: ANN001, ANN202, ARG001
            captured.update({"messages": messages, **kwargs})
            return {"suggestions": RAW_OPENINGS}

        monkeypatch.setattr(narrator_mod, "chat_completion_json", fake_json)
        async with httpx.AsyncClient() as client:
            result = await narrator_mod.suggest_openings(
                client,
                SCENE,
                {"max_tokens_narrator": 24_000},
                "Mistério.",
                "opening-session",
            )

        assert result == OPENINGS
        assert captured["agent"] == "opening_suggest"
        assert captured["session_id"] == "opening-session"
        assert captured["turn_number"] == 0
        assert captured["max_tokens"] == 512


class TestOpeningRunnerAndRoute:
    @pytest.mark.asyncio
    async def test_empty_session_generation_is_locked_and_does_not_mutate_state(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        calls: list[dict] = []

        async def fake_openings(**kwargs):  # noqa: ANN003, ANN202
            calls.append(kwargs)
            return OPENINGS

        monkeypatch.setattr(runner_mod, "narrator_suggest_openings", fake_openings)
        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session()
            try:
                before = await runner.get_state(sid)
                assert before is not None
                before_dict = game_state_to_dict(before)

                lock = _get_lock(sid)
                await lock.acquire()
                task = asyncio.create_task(runner.suggest_openings(sid))
                await asyncio.sleep(0)
                assert not task.done()
                lock.release()
                result = await task

                after = await runner.get_state(sid)
            finally:
                await delete_session(sid)

        assert result == {"suggestions": OPENINGS}
        assert after is not None and game_state_to_dict(after) == before_dict
        assert set(calls[0]) == {
            "client",
            "scene",
            "config",
            "narrator_directives",
            "session_id",
        }

    @pytest.mark.asyncio
    async def test_started_or_missing_session_never_calls_model(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner
        from src.store.sessions import load_game, save_game

        async def forbidden(**kwargs):  # noqa: ANN003, ANN202, ARG001
            raise AssertionError("model must not be called")

        monkeypatch.setattr(runner_mod, "narrator_suggest_openings", forbidden)
        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session()
            try:
                game = load_game(sid)
                assert game is not None
                runner._append_history(game, "Narrator", "A cena começou.", "narration", 1)
                save_game(game)
                started = await runner.suggest_openings(sid)
                missing = await runner.suggest_openings("does-not-exist")
            finally:
                await delete_session(sid)

        assert started["code"] == "conversation_started"
        assert missing["code"] == "session_not_found"

    @pytest.mark.asyncio
    async def test_http_handler_maps_not_found_conflict_and_success(self, monkeypatch) -> None:  # noqa: ANN001
        from src import main as main_mod

        class FakeRunner:
            result: dict = {"suggestions": OPENINGS}

            async def suggest_openings(self, session_id):  # noqa: ANN001, ANN202
                return self.result

        fake_runner = FakeRunner()
        monkeypatch.setattr(main_mod, "_runtime", lambda: SimpleNamespace(runner=fake_runner))

        assert await main_mod.suggest_openings("sid") == {"suggestions": OPENINGS}
        fake_runner.result = {"error": "gone", "code": "session_not_found"}
        with pytest.raises(HTTPException) as missing:
            await main_mod.suggest_openings("sid")
        assert missing.value.status_code == 404
        fake_runner.result = {"error": "started", "code": "conversation_started"}
        with pytest.raises(HTTPException) as conflict:
            await main_mod.suggest_openings("sid")
        assert conflict.value.status_code == 409


class TestOpeningFrontend:
    def test_empty_state_carousel_composes_existing_hint_and_skip(self) -> None:
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        source = (STATIC / "app.js").read_text(encoding="utf-8")
        api = (STATIC / "api.js").read_text(encoding="utf-8")
        styles = (STATIC / "style.css").read_text(encoding="utf-8")

        for element_id in (
            "opening-generate-btn",
            "opening-carousel",
            "opening-prev-btn",
            "opening-next-btn",
            "opening-dots",
            "opening-start-btn",
            "opening-regenerate-btn",
        ):
            assert f'id="{element_id}"' in html
        assert "/opening-suggestions" in api
        assert "state.narratorHint = opening;\n    await skipTurn();" in source
        assert "openingSuggestions" in source and "resetOpeningSuggestions()" in source
        opening_state = source[source.index("let openingSuggestions") : source.index("/* ── Toast")]
        assert "localStorage" not in opening_state
        assert "pointerdown" in source and "ArrowLeft" in source and "ArrowRight" in source
        assert ".opening-card.from-right" in styles and ".opening-dot.active" in styles
        assert "touch-action: pan-y" in styles

    def test_service_worker_cache_moves_with_the_new_shell(self) -> None:
        sw = (STATIC / "sw.js").read_text(encoding="utf-8")
        assert "rpt-shell-v19" in sw
