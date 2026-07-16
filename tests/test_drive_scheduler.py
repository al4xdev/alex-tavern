"""Task 33: autonomous event scheduler (hazard function + runner injection)."""

from __future__ import annotations

import httpx
import pytest

from src.store.sessions import delete_session

from src.config import ConfigValidationError, _unit_interval
from src.drive import build_event_seed_messages, evaluate_event_hazard
from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    deepcopy_scene,
)


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta")}
SCENE = Scene(
    location="Estalagem",
    time_of_day="Noite",
    present_characters=["C1", "C2", "Player"],
    physical_facts={},
)


def _game(session_id: str = "drivetest", quiet: int = 0) -> GameState:
    game = GameState(
        session_id=session_id,
        characters=dict(CHARACTERS),
        player=Player(controlled_character_id="C1"),
        scene=deepcopy_scene(SCENE),
    )
    game.turns_since_injected_event = quiet
    return game


class TestHazardFunction:
    def test_probability_escalates_with_quiet_turns_and_caps(self) -> None:
        config = {
            "auto_event_base_probability": 0.05,
            "auto_event_growth_per_quiet_turn": 0.12,
            "auto_event_max_probability": 0.85,
        }
        probabilities = [
            evaluate_event_hazard(_game(quiet=q), config).probability for q in (0, 2, 5, 50)
        ]
        assert probabilities[0] == 0.05
        assert probabilities[1] == pytest.approx(0.29)
        assert probabilities[2] == pytest.approx(0.65)
        assert probabilities[3] == 0.85  # hard cap

    def test_decision_is_deterministic_per_session_and_turn(self) -> None:
        config = {}
        first = evaluate_event_hazard(_game("abc", quiet=3), config)
        second = evaluate_event_hazard(_game("abc", quiet=3), config)
        assert first == second
        other_session = evaluate_event_hazard(_game("xyz", quiet=3), config)
        assert other_session.roll != first.roll

    def test_disabled_scheduler_never_fires(self) -> None:
        config = {
            "auto_event_enabled": False,
            "auto_event_base_probability": 1.0,
            "auto_event_max_probability": 1.0,
        }
        decision = evaluate_event_hazard(_game(quiet=50), config)
        assert decision.fired is False
        assert decision.probability == 1.0

    def test_unit_interval_validator_rejects_out_of_range(self) -> None:
        assert _unit_interval(0.3, "x") == 0.3
        with pytest.raises(ConfigValidationError):
            _unit_interval(1.5, "x")
        with pytest.raises(ConfigValidationError):
            _unit_interval(True, "x")


class TestSeedPromptShape:
    def test_seed_prompt_carries_scene_and_recent_events_only(self) -> None:
        game = _game()
        game.history.append(
            TurnRecord(
                turn_number=1,
                speaker="C2",
                content="A porta range com o vento.",
                content_type="speech",
                scene_snapshot=deepcopy_scene(SCENE),
            )
        )
        joined = "\n".join(m["content"] for m in build_event_seed_messages(game))
        assert "Estalagem" in joined
        assert "A porta range" in joined
        assert "never dictate" in joined.lower()


class TestRunnerInjection:
    @pytest.mark.asyncio
    async def test_skip_turn_fires_and_injects_seed_as_hint(self, monkeypatch) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.drive import DriveDecision
        from src.runner import Runner

        captured: dict[str, object] = {}

        def fake_hazard(game, config):  # noqa: ANN001, ANN202, ARG001
            return DriveDecision(fired=True, probability=0.5, quiet_turns=3, roll=0.1)

        async def fake_seed(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
            return "Um mensageiro encharcado abre a porta da estalagem."

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            captured["hint"] = narrator_hint
            return {
                "narration": "A porta se abre.",
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        monkeypatch.setattr(runner_mod, "evaluate_event_hazard", fake_hazard)
        monkeypatch.setattr(runner_mod, "generate_event_seed", fake_seed)

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            try:
                await runner.player_turn(sid, skip=True)
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)

        assert captured["hint"] == "Um mensageiro encharcado abre a porta da estalagem."
        assert game is not None and game.turns_since_injected_event == 0

    @pytest.mark.asyncio
    async def test_quiet_turns_accumulate_and_manual_hint_is_never_overridden(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        import src.runner as runner_mod
        from src.runner import Runner

        hazard_calls: list[int] = []

        def fake_hazard(game, config):  # noqa: ANN001, ANN202, ARG001
            hazard_calls.append(game.turns_since_injected_event)
            from src.drive import DriveDecision

            return DriveDecision(fired=False, probability=0.1, quiet_turns=0, roll=0.9)

        async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            return {
                "narration": "Segue.",
                "next_speakers": ["Narrator"],
                "perception_events": [],
                "scene_update": None,
                "mood_updates": None,
            }

        monkeypatch.setattr(runner_mod, "evaluate_event_hazard", fake_hazard)

        async with httpx.AsyncClient() as client:
            runner = Runner(client, {})
            sid = runner.start_session(
                {
                    "characters": dict(CHARACTERS),
                    "scene": deepcopy_scene(SCENE),
                    "controlled_character_id": "C1",
                }
            )
            monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
            try:
                await runner.player_turn(sid, speech="Oi.")
                await runner.player_turn(
                    sid, skip=True, narrator_hint="Evento manual do jogador."
                )
                await runner.player_turn(sid, skip=True)
                game = await runner.get_state(sid)
            finally:
                await delete_session(sid)

        # Scheduler consulted only on the bare skip turn; manual hints untouched.
        assert hazard_calls == [2]
        assert game is not None and game.turns_since_injected_event == 3
