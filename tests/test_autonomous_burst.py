"""Task 37: bounded autonomous burst on skip turns."""

from __future__ import annotations

import httpx
import pytest

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    CharacterPerspective,
    Scene,
    deepcopy_scene,
)
from src.store.sessions import delete_session


async def _fake_prose() -> str:
    return "Narracao de teste."


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta"), "C3": _char("Bento")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)
BURST_CONFIG = {"autonomous_burst_max_beats": 4, "auto_event_enabled": False}


def _beat(queue, return_control=False, events=None):  # noqa: ANN001, ANN202
    return {
        "next_speakers": list(queue),
        "perception_events": list(events or []),
        "scene_update": None,
        "mood_updates": None,
        "return_control": return_control,
    }


def _event(text):  # noqa: ANN001, ANN202
    return {
        "event_kind": "observation",
        "subject_id": "Narrator",
        "content": text,
        "witness_ids": ["C2", "C3"],
    }


async def _run(monkeypatch, config, director_beats, skip=True, force=None):  # noqa: ANN001, ANN202
    import src.runner as runner_mod
    from src.runner import Runner

    async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return CharacterPerspective(
            initialized_turn=kwargs.get("turn_number", 0),
            processed_through_turn=kwargs.get("turn_number", 0),
        )

    monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

    beats_iter = iter(director_beats)

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return next(beats_iter)

    async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return {"speech": f"Beat de {character_id}.", "thought": None, "action_intent": None}

    async with httpx.AsyncClient() as client:
        runner = Runner(client, dict(config))
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(runner, "_call_character", fake_character)
        monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: _fake_prose())
        try:
            result = await runner.player_turn(sid, skip=skip, force_speaker=force)
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)
    return result, game


class TestBurst:
    @pytest.mark.asyncio
    async def test_budget_exhausted_runs_all_beats_with_own_turns(self, monkeypatch) -> None:  # noqa: ANN001
        result, game = await _run(
            monkeypatch, BURST_CONFIG, [_beat(["C2"]), _beat(["C3"]), _beat(["C2"]), _beat(["C3"])]
        )
        assert result["burst_stop_reason"] == "budget_exhausted"
        assert [b["turn_number"] for b in result["beats"]] == [1, 2, 3, 4]
        assert game is not None and game.history[-1].turn_number == 4

    @pytest.mark.asyncio
    async def test_protagonist_excluded_for_first_two_beats(self, monkeypatch) -> None:  # noqa: ANN001
        """Task 45 hybrid routing: the controlled character stays out of
        next_speakers for the first two beats of a burst, then becomes eligible."""
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(initialized_turn=0, processed_through_turn=0)

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        recorded: list[object] = []

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            recorded.append(kwargs.get("exclude_controlled"))
            return _beat(["C2"])  # C2 replies every beat so the burst runs to budget

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": f"Beat de {character_id}.", "thought": None, "action_intent": None}

        async with httpx.AsyncClient() as client:
            runner = Runner(client, dict(BURST_CONFIG))  # max_beats=4
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: _fake_prose())
            try:
                await runner.player_turn(sid, skip=True)
            finally:
                await delete_session(sid)

        assert recorded == [True, True, False, False]

    @pytest.mark.asyncio
    async def test_stops_when_player_is_addressed(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(
            monkeypatch, BURST_CONFIG, [_beat(["C2"]), _beat(["C3", "C1"]), _beat(["C2"])]
        )
        assert result["burst_stop_reason"] == "player_addressed"
        assert len(result["beats"]) == 2

    @pytest.mark.asyncio
    async def test_stops_on_return_control_flag(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(
            monkeypatch,
            BURST_CONFIG,
            [_beat(["C2"]), _beat(["C3"], return_control=True), _beat(["C2"])],
        )
        assert result["burst_stop_reason"] == "protagonist_decision"
        assert len(result["beats"]) == 2

    @pytest.mark.asyncio
    async def test_two_narrator_only_beats_settle_the_scene(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(
            monkeypatch,
            BURST_CONFIG,
            [
                _beat(["C2"], events=[_event("Um som vem do estabulo.")]),
                _beat(["Narrator"], events=[_event("A porta do estabulo range.")]),
                _beat(["Narrator"], events=[_event("Um cavalo se agita la fora.")]),
                _beat(["C2"]),
            ],
        )
        assert result["burst_stop_reason"] == "beat_settled"
        assert len(result["beats"]) == 3

    @pytest.mark.asyncio
    async def test_empty_beat_settles_immediately(self, monkeypatch) -> None:  # noqa: ANN001
        """A narrator-only beat with zero novel events ends the burst at once."""
        result, game = await _run(
            monkeypatch,
            BURST_CONFIG,
            [_beat(["C2"], events=[_event("Barulho.")]), _beat(["Narrator"]), _beat(["C2"])],
        )
        assert result["burst_stop_reason"] == "beat_settled"
        assert len(result["beats"]) == 2
        # The empty beat writes NO narration record: nothing happened, so the
        # prose renderer is never invited to re-describe the standing tableau.
        assert game is not None
        narration_turns = [r.turn_number for r in game.history if r.content_type == "narration"]
        assert narration_turns == [1]
        assert result["beats"][1]["narration"] == ""

    @pytest.mark.asyncio
    async def test_duplicate_events_are_dropped_across_beats(self, monkeypatch) -> None:  # noqa: ANN001
        """The same stimulus paraphrased is resolved once, not re-narrated."""
        result, _ = await _run(
            monkeypatch,
            BURST_CONFIG,
            [
                _beat(["C2"], events=[_event("Um baque surdo vem do estabulo.")]),
                _beat(["Narrator"], events=[_event("Um baque surdo vem do estabulo!")]),
                _beat(["C2"]),
            ],
        )
        # Beat 2's duplicated event is dropped -> empty narrator-only beat -> settled.
        assert result["burst_stop_reason"] == "beat_settled"
        assert len(result["beats"]) == 2

    @pytest.mark.asyncio
    async def test_default_config_keeps_single_beat_contract(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(monkeypatch, {"auto_event_enabled": False}, [_beat(["C2"])])
        assert result["burst_stop_reason"] is None
        assert len(result["beats"]) == 1
        assert result["character_responses"][0]["speech"] == "Beat de C2."

    @pytest.mark.asyncio
    async def test_force_speaker_disables_the_burst(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(monkeypatch, BURST_CONFIG, [_beat(["C2"])], skip=True, force="C2")
        assert result["burst_stop_reason"] is None
        assert len(result["beats"]) == 1

    @pytest.mark.asyncio
    async def test_undo_pops_exactly_one_beat(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, controlled_id, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
        beats = iter([_beat(["C2"]), _beat(["C3"])])

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return next(beats)

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": "Ok.", "thought": None, "action_intent": None}

        async with httpx.AsyncClient() as client:
            runner = Runner(client, dict(BURST_CONFIG, autonomous_burst_max_beats=2))
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: _fake_prose())
            try:
                result = await runner.player_turn(sid, skip=True)
                assert len(result["beats"]) == 2
                await runner.undo_turn(sid)
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)
        assert game is not None and game.history[-1].turn_number == 1


class TestBurstConfigValidation:
    """Task 45: canonical default 6 and a safe upper bound for the burst size."""

    def test_default_is_six(self) -> None:
        from src.config import DEFAULT_CONFIG, validate_config

        canonical = validate_config(DEFAULT_CONFIG)
        assert canonical["autonomous_burst_max_beats"] == 6

    def test_accepts_a_valid_custom_value(self) -> None:
        from src.config import DEFAULT_CONFIG, validate_config

        canonical = validate_config({**DEFAULT_CONFIG, "autonomous_burst_max_beats": 3})
        assert canonical["autonomous_burst_max_beats"] == 3

    def test_rejects_out_of_range_and_wrong_types(self) -> None:
        from src.config import (
            DEFAULT_CONFIG,
            MAX_BURST_BEATS,
            ConfigValidationError,
            validate_config,
        )

        for bad in (0, -1, MAX_BURST_BEATS + 1, True, 2.5, "6"):
            with pytest.raises(ConfigValidationError):
                validate_config({**DEFAULT_CONFIG, "autonomous_burst_max_beats": bad})
