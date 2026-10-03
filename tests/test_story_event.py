"""Manual events replace future direction once, under the existing turn lock."""

from __future__ import annotations

import copy
import json

import httpx
import pytest

from src import roteiro as roteiro_mod
from src import runner as runner_mod
from src.models import CharacterPerspective, RoteiroAct, game_state_to_dict
from src.roteiro import build_roteiro_messages, rewrite_future_from_event
from src.runner import Runner
from src.store.sessions import load_game, save_game, session_state_path
from tests.factories import director_beat, make_event_roteiro, make_game

EVENT = "Marta e afetada por magia negra agora; o efeito piora nos proximos cinco turnos."


def model_plan():
    return {
        "premise": "A magia negra afeta Marta e piora ao longo dos proximos cinco turnos.",
        "acts": [
            {
                "act_id": "corruption",
                "summary": "Efeito inicial e agravamento em cinco turnos",
                "exit_condition": "Quinto agravamento",
                "duration_ticks": 5,
                "world_event": "A maldicao atinge sua manifestacao final.",
            },
        ],
        "first_beat": {
            "beat_id": "first-effect",
            "intent": "Marta apresenta o primeiro sinal da maldicao agora.",
            "expected_actors": [],
            "expected_anchors": ["primeiro sinal da maldicao"],
            "exit_condition": "Primeiro sinal aparece",
            "budget_turns": 3,
        },
    }


def test_event_input_is_separate_from_confirmed_history_and_output_schema():
    game = make_game()
    messages = build_roteiro_messages(game, event=EVENT)
    assert json.loads(messages[-1]["content"].split("ADDITIONAL INPUT:\n", 1)[1]) == {
        "event": EVENT
    }
    assert "first manifestation must happen in the next turn" in messages[0]["content"]
    assert "has not happened yet" in messages[0]["content"]
    assert "event" not in roteiro_mod.build_roteiro_schema()["schema"]["properties"]
    assert game.history == []


@pytest.mark.asyncio
async def test_rewrite_preserves_completed_acts_but_replaces_current_and_future(monkeypatch):
    game = make_game()
    old = make_event_roteiro("Old future")
    completed = RoteiroAct(act_id="completed", summary="Already played", exit_condition="Done")
    old.acts.insert(0, completed)
    old.act_index = 1
    old.anchors_seen = ["old anchor"]
    game.roteiro = old
    game.narrative_tick = 17
    before = game_state_to_dict(game)
    calls = []

    async def fake_call(client, config, messages, **kwargs):
        calls.append(kwargs)
        assert EVENT in messages[-1]["content"]
        assert "Old future" in messages[-1]["content"]
        return model_plan()

    monkeypatch.setattr(roteiro_mod, "call_agent", fake_call)
    async with httpx.AsyncClient() as client:
        updated = await rewrite_future_from_event(client, game, EVENT, {}, 8)
    assert game_state_to_dict(game) == before  # generator returns a draft
    assert updated.acts[0] == completed
    assert [act.act_id for act in updated.acts] == ["completed", "corruption"]
    assert updated.act_index == 1
    assert updated.act_started_tick == 17
    assert updated.beat_started_turn == 8
    assert updated.anchors_seen == []
    assert updated.beat_actions_elapsed == 0
    assert updated.beat_replans_in_act == 0
    assert "event_rewrite" in updated.beat_log[-1]
    assert calls[0]["agent"] == "roteiro:event"
    assert calls[0]["session_id"] == game.session_id
    assert calls[0]["turn_number"] == 8


@pytest.mark.asyncio
async def test_empty_event_is_rejected_before_model_call():
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="must not be empty"):
            await rewrite_future_from_event(client, make_game(), "  ", {}, 1)


async def configure_runner(monkeypatch, game, *, planner_enabled=False):
    calls = []

    async def fake_call(client, config, messages, **kwargs):
        calls.append(kwargs["agent"])
        if kwargs["agent"] == "roteiro:replan":
            beat = model_plan()["first_beat"]
            beat["beat_id"] = "next-effect"
            beat["intent"] = "A maldicao piora no segundo turno."
            return {"act_completed": False, "beat": beat}
        return model_plan()

    async def fake_init(client, viewer_id, characters, config, **kwargs):
        return CharacterPerspective(initialized_turn=0, processed_through_turn=0)

    monkeypatch.setattr(roteiro_mod, "call_agent", fake_call)
    monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
    client = httpx.AsyncClient()
    runner = Runner(client, {"roteiro_enabled": planner_enabled, "auto_event_enabled": False})

    async def director(current, turn_number, forced_speaker=None, narrator_hint="", **kwargs):
        calls.append("director")
        assert narrator_hint == ""
        assert current.roteiro.beat.beat_id in {"first-effect", "next-effect"}
        return director_beat(
            next_speakers=["Narrator"], scene_update={"corruption": f"stage-{turn_number}"}
        )

    async def prose(*args, **kwargs):
        return "O primeiro sinal da maldicao aparece."

    monkeypatch.setattr(runner, "_call_narrator", director)
    monkeypatch.setattr(runner, "_render_narration", prose)
    save_game(game)
    return runner, calls


@pytest.mark.asyncio
@pytest.mark.parametrize("planner_enabled", [False, True])
async def test_event_wins_over_old_deadline_is_consumed_once_and_undo_restores(
    monkeypatch, planner_enabled
):
    game = make_game()
    game.roteiro = make_event_roteiro("Old future")
    game.roteiro.acts[0].duration_ticks = 1
    game.roteiro.acts[0].world_event = "OLD DEADLINE MUST NOT FIRE"
    game.narrative_tick = 9
    old = copy.deepcopy(game.roteiro)
    runner, calls = await configure_runner(monkeypatch, game, planner_enabled=planner_enabled)
    try:
        await runner.player_turn(game.session_id, event=EVENT, force_speaker="Narrator")
        assert calls == ["roteiro:event", "director"]
        current = load_game(game.session_id)
        assert current.roteiro.premise == model_plan()["premise"]
        assert current.scene.physical_facts["corruption"] == "stage-1"
        assert current.history[0].roteiro_snapshot["premise"] == old.premise
        assert all(record.content != EVENT for record in current.history)

        await runner.player_turn(game.session_id, speech="O que mudou?", force_speaker="Narrator")
        assert calls == ["roteiro:event", "director", "roteiro:replan", "director"]
        assert calls.count("roteiro:event") == 1
        await runner.undo_turn(game.session_id)
        await runner.undo_turn(game.session_id)
        restored = load_game(game.session_id)
        assert restored.roteiro == old
        assert "corruption" not in restored.scene.physical_facts
    finally:
        await runner.client.aclose()


@pytest.mark.asyncio
async def test_planner_failure_leaves_persisted_state_unchanged(monkeypatch):
    game = make_game()
    save_game(game)
    before = session_state_path(game.session_id).read_bytes()

    async def fail(*args, **kwargs):
        raise RuntimeError("planner unavailable")

    monkeypatch.setattr(roteiro_mod, "call_agent", fail)
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {})
        with pytest.raises(RuntimeError, match="planner unavailable"):
            await runner.player_turn(game.session_id, event=EVENT)
    assert session_state_path(game.session_id).read_bytes() == before


@pytest.mark.asyncio
async def test_http_accepts_event_and_rejects_old_input(monkeypatch):
    from types import SimpleNamespace

    from src import main
    from tests.conftest import sec_headers

    game = make_game()
    runner, calls = await configure_runner(monkeypatch, game)
    monkeypatch.setattr(main, "_runtime", lambda: SimpleNamespace(runner=runner))
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app),
            base_url="http://localhost",
            headers=sec_headers(),
        ) as client:
            old = await client.post(
                f"/session/{game.session_id}/turn", json={"narrator_hint": EVENT}
            )
            assert old.status_code == 422
            assert calls == []
            response = await client.post(
                f"/session/{game.session_id}/turn",
                json={"event": EVENT, "force_speaker": "Narrator"},
            )
            assert response.status_code == 200
            assert calls == ["roteiro:event", "director"]
    finally:
        await runner.client.aclose()
