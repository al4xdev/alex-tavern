"""Task 37: bounded autonomous burst on skip turns."""

from __future__ import annotations

import httpx
import pytest

from src.models import (
    CharacterPerspective,
    Scene,
    deepcopy_scene,
)
from src.store.sessions import delete_session
from tests.factories import director_beat, make_cast


async def _fake_prose() -> str:
    return "Narracao de teste."



CHARACTERS = make_cast("Rui", "Marta", "Bento")
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)
BURST_CONFIG = {"autonomous_burst_max_beats": 4, "auto_event_enabled": False}


def _beat(queue, return_control=False, events=None):  # noqa: ANN001, ANN202
    return director_beat(
               next_speakers=list(queue),
               perception_events=list(events or []),
               return_control=return_control,
           )


def _event(text):  # noqa: ANN001, ANN202
    return {
        "event_kind": "observation",
        "subject_id": "Narrator",
        "content": text,
        "witness_ids": ["C2", "C3"],
    }


async def _run(monkeypatch, config, director_beats, skip=True, force=None, speech=""):  # noqa: ANN001, ANN202
    import src.runner as runner_mod
    from src.runner import Runner

    async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
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
        sid = await runner.start_session(
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
            result = await runner.player_turn(sid, speech=speech, skip=skip, force_speaker=force)
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

        async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
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
            sid = await runner.start_session(
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
        """A narrator-only beat with zero novel events ends the burst at once.

        It used to be reported as a beat AND committed as a turn, which burned a
        turn number `_next_turn_number` then handed out again (found by the task
        45 HTTP smoke). A beat that leaves no trace is now dropped entirely: the
        burst still ends here, and it says so precisely.
        """
        result, game = await _run(
            monkeypatch,
            BURST_CONFIG,
            [_beat(["C2"], events=[_event("Barulho.")]), _beat(["Narrator"]), _beat(["C2"])],
        )
        assert result["burst_stop_reason"] == "beat_produced_nothing"
        assert len(result["beats"]) == 1
        # The empty beat writes NO narration record: nothing happened, so the
        # prose renderer is never invited to re-describe the standing tableau.
        assert game is not None
        narration_turns = [r.turn_number for r in game.history if r.content_type == "narration"]
        assert narration_turns == [1]
        # And it consumed no turn number: every reported beat has records.
        recorded = {r.turn_number for r in game.history}
        assert {b["turn_number"] for b in result["beats"]} <= recorded

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
        # Beat 2's duplicated event is dropped -> the beat leaves no trace at all
        # -> it is not committed, and the burst ends there.
        assert result["burst_stop_reason"] == "beat_produced_nothing"
        assert len(result["beats"]) == 1

    @pytest.mark.asyncio
    async def test_default_config_keeps_single_beat_contract(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(monkeypatch, {"auto_event_enabled": False}, [_beat(["C2"])])
        assert result["burst_stop_reason"] is None
        assert len(result["beats"]) == 1
        assert result["character_responses"][0]["speech"] == "Beat de C2."

    @pytest.mark.asyncio
    async def test_normal_player_turn_never_bursts(self, monkeypatch) -> None:  # noqa: ANN001
        """A turn the player actually wrote is ONE beat, whatever the budget says.

        The burst is a skip-only contract: only passing hands the world several
        beats. Reported symptom (2026-07-21): "it seems to fire even when I do
        not press continue" — this pins the contract so the answer stops being
        a reading of `runner.py`.
        """
        result, game = await _run(
            monkeypatch,
            BURST_CONFIG,
            [_beat(["C2"]), _beat(["C3"]), _beat(["C2"]), _beat(["C3"])],
            skip=False,
            speech="Oi pessoal.",
        )
        assert result["burst_stop_reason"] is None
        assert len(result["beats"]) == 1
        assert game is not None and game.history[-1].turn_number == 1

    @pytest.mark.asyncio
    async def test_force_speaker_disables_the_burst(self, monkeypatch) -> None:  # noqa: ANN001
        result, _ = await _run(monkeypatch, BURST_CONFIG, [_beat(["C2"])], skip=True, force="C2")
        assert result["burst_stop_reason"] is None
        assert len(result["beats"]) == 1

    @pytest.mark.asyncio
    async def test_undo_pops_exactly_one_beat(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
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
            sid = await runner.start_session(
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


class TestACrashLeavesOnlyCompleteBeats:
    """Task 45: "an error ends the sequence without repeating a persisted beat".

    The runner's own comment states the contract - "each beat commits as its OWN
    turn (undo pops one beat; a crash leaves only complete beats)" - and the
    burst loop has no `except`, so it rests entirely on `_commit_beat` calling
    `save_game` before the next beat starts. That was asserted and never tested.

    What it costs if it is wrong: the client retries the skip after the error,
    `_next_turn_number` reads a history that never reached disk, and the beats
    the player already read are generated a second time under the same turn
    numbers - the burst replays itself.
    """

    @pytest.mark.asyncio
    async def test_beats_before_the_error_survive_and_are_not_replayed(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner
        from src.store.sessions import load_game

        async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return CharacterPerspective(
                initialized_turn=kwargs.get("turn_number", 0),
                processed_through_turn=kwargs.get("turn_number", 0),
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)

        calls = {"n": 0}

        async def exploding_narrator(  # noqa: ANN202
            game,  # noqa: ANN001, ARG001
            turn_number,  # noqa: ANN001, ARG001
            forced_speaker=None,  # noqa: ANN001, ARG001
            narrator_hint="",  # noqa: ANN001, ARG001
            **kwargs,  # noqa: ANN003, ARG001
        ):
            calls["n"] += 1
            if calls["n"] == 3:
                raise RuntimeError("provider died mid-burst")
            return _beat(["C2"], events=[_event(f"Algo acontece ({calls['n']}).")])

        async def fake_character(game, character_id, context, turn_number, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {"speech": f"Beat de {character_id}.", "thought": None, "action_intent": None}

        async with httpx.AsyncClient() as client:
            runner = Runner(client, dict(BURST_CONFIG))
            sid = await runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", exploding_narrator)
            monkeypatch.setattr(runner, "_call_character", fake_character)
            monkeypatch.setattr(runner, "_render_narration", lambda g, e, t: _fake_prose())
            try:
                with pytest.raises(RuntimeError, match="provider died mid-burst"):
                    await runner.player_turn(sid, skip=True)

                # On disk, not in memory: the caller's GameState is gone with the
                # exception, and the retry will read the file.
                crashed = load_game(sid)
                assert crashed is not None
                survived = sorted({record.turn_number for record in crashed.history})
                assert survived == [1, 2], (
                    f"two beats completed before the error; history has {survived}"
                )
                texts_before = [record.content for record in crashed.history]

                # The client retries the same skip. The third Director call is
                # the one that raised, so this run starts from the fourth.
                retried = await runner.player_turn(sid, skip=True)
                numbers = [beat["turn_number"] for beat in retried["beats"]]
                assert min(numbers) == 3, (
                    f"the retry restarted at turn {min(numbers)}, replaying a beat "
                    "the player already read"
                )

                after = load_game(sid)
                assert after is not None
                assert [r.content for r in after.history][: len(texts_before)] == texts_before, (
                    "the retry rewrote the beats that had already been committed"
                )
                all_numbers = [record.turn_number for record in after.history]
                assert all_numbers == sorted(all_numbers)
            finally:
                await delete_session(sid)
