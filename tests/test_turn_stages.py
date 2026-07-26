"""Two turn stages that used to be unreachable without running a whole turn.

``_resolve_beat_hint`` decides which of four producers gets the single blind
``narrator_hint`` channel; the precedence used to live in the physical order of
lines inside player_turn. ``_beat_settled`` decides when an autonomous burst
stops. Both are now callable on their own, so their rules are stated as tests
rather than inferred from a 245-statement method.
"""

from __future__ import annotations

import httpx
import pytest

from src.models import (
    GameState,
    Player,
    Scene,
)
from src.runner import CLOCK_SKIP_INVITE, BurstState, Runner, TurnInput
from tests.factories import make_character


def _game() -> GameState:
    return GameState(
        session_id="stage001",
        characters={"C1": make_character("Rui"), "C2": make_character("Marta")},
        player=Player(controlled_character_id="C1"),
        scene=Scene(
            location="Estalagem",
            time_of_day="Noite",
            present_characters=["C1", "C2", "Player"],
            physical_facts={},
        ),
    )


def _turn(**overrides: object) -> TurnInput:
    base = {
        "speech": "",
        "thought": "",
        "action": "",
        "force_speaker": None,
        "narrator_hint": "",
        "skip": True,
        "audience": None,
        "transformed_fields": [],
        "effective_force_speaker": None,
    }
    return TurnInput(**{**base, **overrides})  # type: ignore[arg-type]


@pytest.fixture
def runner() -> Runner:
    # Every producer is disabled by config, so each test enables exactly one.
    return Runner(httpx.AsyncClient(), {"auto_event_enabled": False})


class TestBeatHintPrecedence:
    async def test_a_hint_the_player_wrote_is_never_overridden(self, runner: Runner) -> None:
        hint, injected = await runner._resolve_beat_hint(_game(), 1, 0, _turn(), "A storm nears.")
        assert hint == "A storm nears."
        assert injected is False

    async def test_a_bare_skip_falls_back_to_the_time_compression_invite(
        self, runner: Runner
    ) -> None:
        hint, injected = await runner._resolve_beat_hint(_game(), 1, 0, _turn(), "")
        assert hint == CLOCK_SKIP_INVITE
        # The invite is a question for the Director, not an event the world caused.
        assert injected is False

    async def test_the_drive_seed_wins_over_the_invite(
        self, runner: Runner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import src.runner as runner_mod

        async def seed(*_args: object, **_kwargs: object) -> str:
            return "Um cavalo escapa do estábulo."

        monkeypatch.setattr(runner_mod, "generate_event_seed", seed)
        runner.config = {"auto_event_enabled": True, "auto_event_base_probability": 1.0}

        hint, injected = await runner._resolve_beat_hint(_game(), 1, 0, _turn(), "")

        assert hint == "Um cavalo escapa do estábulo."
        assert injected is True

    async def test_a_turn_with_content_gets_no_invite(self, runner: Runner) -> None:
        """The invite is the "player passed" signal; a written turn is not one."""
        hint, injected = await runner._resolve_beat_hint(
            _game(), 1, 0, _turn(skip=False, speech="Boa noite."), ""
        )
        assert hint == ""
        assert injected is False

    async def test_later_burst_beats_get_no_invite_either(self, runner: Runner) -> None:
        hint, _ = await runner._resolve_beat_hint(_game(), 2, 1, _turn(), "")
        assert hint == ""

    async def test_the_watcher_speaks_only_when_nothing_else_did(
        self, runner: Runner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def recovery(*_args: object, **_kwargs: object) -> str:
            return "A porta range."

        monkeypatch.setattr(runner, "_maybe_watcher_recovery", recovery)

        # A written turn leaves the channel free, so the watcher may use it...
        hint, injected = await runner._resolve_beat_hint(
            _game(), 1, 0, _turn(skip=False, speech="Boa noite."), ""
        )
        assert (hint, injected) == ("A porta range.", True)

        # ...but it never displaces what the player wrote.
        hint, injected = await runner._resolve_beat_hint(
            _game(), 1, 0, _turn(skip=False, speech="Boa noite."), "O sino toca."
        )
        assert (hint, injected) == ("O sino toca.", False)


class TestBurstStopConditions:
    def _settle(self, runner: Runner, burst: BurstState, **kwargs: object) -> bool:
        defaults: dict = {
            "queue": ["C2"],
            "narrator_raw": {"perception_events": [{"content": "algo"}], "return_control": False},
            "character_responses": [{"character_id": "C2"}],
            "controlled": "C1",
            "multi_beat": True,
        }
        merged = {**defaults, **kwargs}
        return runner._beat_settled(
            burst,
            merged["queue"],
            merged["narrator_raw"],
            merged["character_responses"],
            merged["controlled"],
            multi_beat=merged["multi_beat"],
        )

    def test_routing_the_protagonist_returns_control(self, runner: Runner) -> None:
        burst = BurstState()
        assert self._settle(runner, burst, queue=["C2", "C1"]) is True
        assert burst.stop_reason == "player_addressed"

    def test_the_director_can_hand_control_back(self, runner: Runner) -> None:
        burst = BurstState()
        settled = self._settle(
            runner,
            burst,
            narrator_raw={"perception_events": [{"content": "x"}], "return_control": True},
        )
        assert settled is True
        assert burst.stop_reason == "protagonist_decision"

    def test_a_beat_with_speech_keeps_the_burst_running(self, runner: Runner) -> None:
        burst = BurstState()
        assert self._settle(runner, burst) is False
        assert burst.narrator_only_streak == 0

    def test_a_silent_beat_with_no_events_settles_at_once(self, runner: Runner) -> None:
        burst = BurstState()
        settled = self._settle(
            runner,
            burst,
            narrator_raw={"perception_events": [], "return_control": False},
            character_responses=[],
        )
        assert settled is True
        assert burst.stop_reason == "beat_settled"

    def test_two_narrator_only_beats_in_a_row_settle(self, runner: Runner) -> None:
        burst = BurstState()
        assert self._settle(runner, burst, character_responses=[]) is False
        assert self._settle(runner, burst, character_responses=[]) is True
        assert burst.stop_reason == "beat_settled"

    def test_a_single_beat_turn_never_settles_on_an_empty_beat(self, runner: Runner) -> None:
        """Outside a burst the "no events" shortcut must not fire (max_beats == 1)."""
        burst = BurstState()
        settled = self._settle(
            runner,
            burst,
            narrator_raw={"perception_events": [], "return_control": False},
            character_responses=[],
            multi_beat=False,
        )
        assert settled is False
        assert burst.narrator_only_streak == 1
