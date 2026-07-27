"""Task 53: a manual event the human queued must reach perception_events.

The live session showed the whole transport working and the event vanishing
anyway: `turn_input` carried it, `turn_input_effective` preserved it, the
Director prompt contained the UPCOMING EVENT block at 99% of its length, and
none of the six returned events mentioned it. The prose, blind by design, never
had a chance.

The gap in the old tests was exactly this: they proved the hint reached the
prompt and stopped there. These prove what happens to a response that ignores
it.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.agents import narrator as narrator_mod
from src.agents.narrator import _hint_materialized, narrate
from tests.factories import director_beat, make_cast, make_game, make_record

HINT = "Um dragao aparece do nada"


def _events(*contents: str) -> list[dict[str, Any]]:
    return [
        {
            "event_kind": "observation",
            "subject_id": "Narrator",
            "content": content,
            "witness_ids": ["C1", "C2"],
        }
        for content in contents
    ]


class TestDetection:
    def test_the_observed_omission_is_detected(self) -> None:
        """The literal turn-7 shape: six events, none about the dragon."""
        result = director_beat(
            perception_events=_events(
                "Link interrompe a abertura do microportal ao ouvir a ordem.",
                "A figura encapuzada tosse novamente, liberando mais nevoa roxa.",
            )
        )
        assert not _hint_materialized(result, HINT)

    def test_a_literal_materialization_passes(self) -> None:
        result = director_beat(
            perception_events=_events("Um dragao enorme surge no centro do salao.")
        )
        assert _hint_materialized(result, HINT)

    def test_accents_do_not_decide_it(self) -> None:
        result = director_beat(perception_events=_events("Um DRAGÃO irrompe do teto."))
        assert _hint_materialized(result, "Um dragao aparece do nada")

    def test_a_pure_paraphrase_reads_as_a_miss_and_that_is_the_known_cost(self) -> None:
        """Measured at 1 run in 4. One wasted retry beats a silent disappearance."""
        result = director_beat(
            perception_events=_events("Uma criatura escamosa de asas retorcidas irrompe.")
        )
        assert not _hint_materialized(result, HINT)

    def test_no_hint_is_never_a_miss(self) -> None:
        assert _hint_materialized(director_beat(), "")
        assert _hint_materialized(director_beat(), "   ")

    def test_only_short_words_cannot_fabricate_a_match(self) -> None:
        """A hint with nothing distinctive must not trigger an endless retry."""
        assert _hint_materialized(director_beat(perception_events=_events("Nada.")), "e um so")


class TestGuardRetry:
    async def _narrate(self, monkeypatch, responses: list[dict]) -> tuple[dict, list[dict]]:
        calls: list[dict] = []

        async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003
            calls.append({"messages": messages, **kwargs})
            return responses[min(len(calls) - 1, len(responses) - 1)]

        monkeypatch.setattr(narrator_mod, "call_agent", fake_call_agent)
        cast = make_cast("Link", "Maelis")
        game = make_game(characters=cast, controlled="C1")
        game.history = [make_record(1, "C2", "Fiquem onde estao.", scene=game.scene)]
        result = await narrate(
            client=httpx.AsyncClient(),
            scene=game.scene,
            characters=game.characters,
            player_controlled_id="C1",
            history=game.history,
            config={},
            narrator_hint=HINT,
        )
        return result, calls

    @pytest.mark.asyncio
    async def test_an_ignored_hint_is_retried_once_with_a_correction(self, monkeypatch) -> None:  # noqa: ANN001
        omission = director_beat(
            next_speakers=["C2"], perception_events=_events("Maelis observa o portal.")
        )
        recovery = director_beat(
            next_speakers=["C2"], perception_events=_events("Um dragao surge no salao.")
        )
        result, calls = await self._narrate(monkeypatch, [omission, recovery])

        assert len(calls) == 2, "the omission must cost exactly one correction"
        assert "CORRECTION" in calls[1]["messages"][-1]["content"]
        assert calls[1]["guard_retry"] == "hint_omitted"
        assert "dragao" in result["perception_events"][0]["content"]

    @pytest.mark.asyncio
    async def test_a_materialized_hint_costs_no_second_call(self, monkeypatch) -> None:  # noqa: ANN001
        good = director_beat(
            next_speakers=["C2"], perception_events=_events("Um dragao surge no salao.")
        )
        _, calls = await self._narrate(monkeypatch, [good])
        assert len(calls) == 1
        assert calls[0].get("guard_retry", "") == ""

    @pytest.mark.asyncio
    async def test_the_retry_is_not_repeated_forever(self, monkeypatch) -> None:  # noqa: ANN001
        """A Director that keeps refusing gets one correction, then is accepted."""
        stubborn = director_beat(
            next_speakers=["C2"], perception_events=_events("Maelis observa o portal.")
        )
        result, calls = await self._narrate(monkeypatch, [stubborn])
        assert len(calls) == 2
        assert result["perception_events"], "a refused hint never costs the turn"


def test_the_mandatory_rule_ships_in_the_system_prompt() -> None:
    prompt = narrator_mod._build_system_prompt(["C1", "C2"])
    assert "UPCOMING EVENT IS MANDATORY" in prompt
    assert "no coherence concern overrides it" in prompt
