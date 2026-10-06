"""Conversation transforms preserve canon, visibility and retry semantics."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import httpx
import pytest

from src.engine_io import (
    EngineBoundaryError,
    EngineInput,
    OutputProjection,
    PresentationUnavailableError,
)
from src.models import game_state_to_dict
from src.plugins.contracts import Hook
from src.plugins.runtime import PluginRuntime
from src.runner import Runner
from src.store.sessions import delete_session, fork_session, load_game, save_game
from tests.factories import make_cast, make_record, make_scene
from tests.test_plugins import _stub_turn_pipeline


@pytest.fixture
async def runner():
    async with httpx.AsyncClient() as client:
        active = Runner(client, {}, PluginRuntime())
        _stub_turn_pipeline(active)
        yield active


async def session(runner: Runner) -> str:
    cast = make_cast("Rui", "Marta", "Lia")
    return await runner.start_session(
        {
            "characters": cast,
            "controlled_character_id": "C1",
            "scene": make_scene(characters=cast),
        }
    )


def test_projection_only_exposes_explicit_texts_and_preserves_wire_shape() -> None:
    payload = {
        "suggestions": [{"speech": "Hello", "thought": "Secret", "action": "", "id": "C7"}],
        "revision": 42,
    }
    projection = OutputProjection("suggestions", "C1", payload)
    assert list(projection.output.texts.values()) == ["Hello", "Secret", ""]
    translated = replace(
        projection.output,
        texts={
            "suggestions/0/speech": "Olá",
            "suggestions/0/thought": "Segredo",
            "suggestions/0/action": "",
        },
    )
    result = projection.render(translated)
    assert result["revision"] == 42
    assert result["suggestions"][0]["id"] == "C7"
    assert payload["suggestions"][0]["speech"] == "Hello"
    with pytest.raises(ValueError, match="keys"):
        projection.render(replace(translated, texts={"unknown": "oops"}))


@pytest.mark.parametrize(
    "field,value", [("audience", ["C3"]), ("skip", True), ("force_speaker", "C2")]
)
async def test_input_cannot_rewrite_structural_fields(
    runner: Runner, field: str, value: object
) -> None:
    sid = await session(runner)

    def invalid(turn, context):
        setattr(turn, field, value)

    runner.plugins.hooks.register("dev.test.invalid", Hook.ENGINE_INPUT, "filter", invalid)
    with pytest.raises(EngineBoundaryError) as failure:
        await runner.player_turn(sid, speech="Olá", audience=["C2"])
    assert failure.value.phase == "input"
    assert load_game(sid).history == []
    assert runner.plugins.disabled_for_boot == {}
    await delete_session(sid)


async def test_input_failure_retains_filter_and_does_not_advance(
    runner: Runner, monkeypatch
) -> None:
    sid = await session(runner)
    calls = 0

    def transform(turn, context):
        nonlocal calls
        calls += 1
        if calls == 1:
            turn.speech = "discarded"
            raise RuntimeError("provider unavailable")
        turn.speech = "Hello"
        turn.event = "The door opens"

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_INPUT, "filter", transform)

    async def rewrite(*args, **kwargs):
        from src.models import Roteiro

        return Roteiro(premise="test")

    monkeypatch.setattr("src.runner.rewrite_future_from_event", rewrite)
    with pytest.raises(EngineBoundaryError):
        await runner.player_turn(sid, speech="Olá", event="A porta abre")
    assert load_game(sid).revision == 0
    result = await runner.player_turn(sid, speech="Olá", event="A porta abre")
    assert result["effective_input"]["speech"] == "Hello"
    assert result["transformed_fields"] == ["speech"]
    assert load_game(sid).history[0].content == "Hello"
    await delete_session(sid)


async def test_output_retry_survives_runner_restart_without_replaying_turn(runner: Runner) -> None:
    sid = await session(runner)
    calls = 0

    def transform(output, context):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("translator offline")
        output.texts.update({key: "Olá" if text else text for key, text in output.texts.items()})

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_OUTPUT, "filter", transform)
    with pytest.raises(EngineBoundaryError) as failure:
        await runner.player_turn(sid, speech="Hello")
    assert failure.value.committed is True
    game = load_game(sid)
    assert game.revision == 1
    restarted = Runner(runner.client, {}, runner.plugins)

    async def forbidden(*args, **kwargs):
        raise AssertionError("Presentation retry must not generate a turn")

    restarted._call_narrator = forbidden
    result = await restarted.retry_presentation(sid, "turn", failure.value.operation_id)
    assert result["effective_input"]["speech"] == "Olá"
    assert game_state_to_dict(load_game(sid)) == game_state_to_dict(game)
    await runner.undo_turn(sid)
    with pytest.raises(PresentationUnavailableError):
        await restarted.retry_presentation(sid, "turn", failure.value.operation_id)
    await delete_session(sid)


async def test_history_and_state_share_projection_without_exposing_hidden_audience(
    runner: Runner,
) -> None:
    sid = await session(runner)
    game = load_game(sid)
    game.history = [
        make_record(1, "C2", "Visible", scene=game.scene),
        make_record(1, "C2", "Hidden whisper", scene=game.scene, audience=["C3"]),
        make_record(1, "Narrator", "Hidden room", "narration", scene=game.scene, audience=["C3"]),
        make_record(1, "Player", "Own whisper", scene=game.scene, audience=["C2"]),
    ]
    save_game(game)
    observed = []

    def transform(output, context):
        observed.extend(output.texts.values())
        output.texts.update({key: f"PT:{value}" for key, value in output.texts.items()})

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_OUTPUT, "filter", transform)
    history = await runner.get_presented_history(sid)
    state = await runner.get_presented_state(sid)
    assert [item["content"] for item in history] == ["PT:Visible", "PT:Own whisper"]
    assert [item["content"] for item in state["history"]] == ["PT:Visible", "PT:Own whisper"]
    assert "Hidden whisper" not in observed and "Hidden room" not in observed
    assert load_game(sid).history[0].content == "Visible"
    fork = await fork_session(sid)
    fork_history = await runner.get_presented_history(fork)
    assert fork_history == history
    await delete_session(fork)
    await delete_session(sid)


@pytest.mark.parametrize("operation", ["suggestions", "opening-suggestions"])
async def test_suggestions_retry_does_not_regenerate(
    runner: Runner, monkeypatch, operation: str
) -> None:
    sid = await session(runner)
    generated = 0

    async def generate(**kwargs):
        nonlocal generated
        generated += 1
        return (
            [{"speech": "Hello", "thought": "", "action": ""}]
            if operation == "suggestions"
            else ["The door opens", "Rain falls", "A bell rings"]
        )

    target = "suggest_moves" if operation == "suggestions" else "narrator_suggest_openings"
    monkeypatch.setattr(f"src.runner.{target}", generate)
    failed = False

    def translate(output, context):
        nonlocal failed
        if not failed:
            failed = True
            raise RuntimeError("temporary failure")
        output.texts.update(
            {key: f"PT:{text}" if text else text for key, text in output.texts.items()}
        )

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_OUTPUT, "filter", translate)
    with pytest.raises(EngineBoundaryError) as failure:
        if operation == "suggestions":
            await runner.suggest_actions(sid)
        else:
            await runner.suggest_openings(sid)
    result = await runner.retry_presentation(sid, operation, failure.value.operation_id)
    assert result["suggestions"]
    assert generated == 1
    assert load_game(sid).revision == 0
    await delete_session(sid)


async def test_concurrent_output_reads_use_one_session_transaction(runner: Runner) -> None:
    sid = await session(runner)
    active = 0

    async def transform(output, context):
        nonlocal active
        active += 1
        assert active == 1
        await asyncio.sleep(0)
        active -= 1

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_OUTPUT, "filter", transform)
    await asyncio.gather(runner.get_presented_state(sid), runner.get_presented_history(sid))
    await delete_session(sid)


@pytest.mark.parametrize("bad", [True, 7, None, ""])
def test_input_text_validation_rejects_erasure_or_wrong_type(bad: object) -> None:
    original = EngineInput("Hello", "", "", None, "", False, None)
    candidate = replace(original, speech=bad)
    with pytest.raises((TypeError, ValueError)):
        original.validate_transform(candidate)


async def test_http_failure_contract_and_read_only_recovery(runner: Runner, monkeypatch) -> None:
    from src import main
    from tests.conftest import sec_headers

    sid = await session(runner)
    runtime = main.RuntimeState({}, {}, runner.client, runner, runner.plugins)
    monkeypatch.setattr(main.app.state, "runtime", runtime, raising=False)
    fail = True

    def translate(output, context):
        if fail:
            raise RuntimeError("secret provider detail must not enter HTTP")
        output.texts.update({key: "Olá" if text else text for key, text in output.texts.items()})

    runner.plugins.hooks.register("dev.test.translate", Hook.ENGINE_OUTPUT, "filter", translate)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app),
        base_url="http://test",
        headers=sec_headers(),
    ) as http:
        response = await http.post(f"/session/{sid}/turn", json={"speech": "Hello"})
        assert response.status_code == 503
        error = response.json()
        assert error["phase"] == "output" and error["committed"] is True
        assert "secret provider" not in response.text
        fail = False
        retry = await http.get(
            f"/session/{sid}/presentation/turn",
            params={"operation_id": error["operation_id"]},
        )
        assert retry.status_code == 200
        assert retry.json()["effective_input"]["speech"] == "Olá"
        assert load_game(sid).revision == 1
        history = await http.get(f"/session/{sid}/history")
        state = await http.get(f"/session/{sid}/state")
        assert history.json()[0]["content"] == "Olá"
        assert state.json()["history"][0]["content"] == "Olá"
        assert load_game(sid).history[0].content == "Hello"
    await delete_session(sid)


async def test_output_validation_failure_retains_the_required_filter(runner: Runner) -> None:
    sid = await session(runner)

    def invalid(output, context):
        output.texts["unrequested"] = "invented"

    runner.plugins.hooks.register("dev.test.invalid", Hook.ENGINE_OUTPUT, "filter", invalid)
    with pytest.raises(EngineBoundaryError) as failure:
        await runner.player_turn(sid, thought="Secret")
    assert failure.value.committed is True
    with pytest.raises(EngineBoundaryError):
        await runner.retry_presentation(sid, "turn", failure.value.operation_id)
    assert runner.plugins.disabled_for_boot == {}
    assert load_game(sid).revision == 1
    await delete_session(sid)
