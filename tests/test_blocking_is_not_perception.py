"""Task 79, decision 1: blocking may reach the prose renderer and NOTHING else.

The owner approved the reader list with one condition, and it is the condition
that matters:

    "The forbidden row is the best thing in this document - it applies task 76's
     lesson before the mistake instead of after it. One addition: make it a test,
     not a comment. A rule that lives only in prose is a rule the next refactor
     deletes without noticing."

So this file is that rule, executable. If blocking can ever narrow an audience,
task 79 has rebuilt the defect it exists to remove: a position inside a room
would once again become an acoustic wall, which is the whole reason the field was
wanted in the first place.

The three perception entry points are `can_perceive`, `eligible_witnesses` and
`perception_clusters`. None of them may see this data, and `Scene` may not carry
it - the ship-now half persists nothing at all.
"""

from __future__ import annotations

import inspect
from dataclasses import fields

import httpx
import pytest

import src.agents.narrator as narrator_mod
import src.perception as perception
from src.agents.narrator import narrate
from src.agents.prose import build_prose_messages
from src.models import Scene
from tests.factories import director_beat, make_cast, make_game


class TestPerceptionCannotSeeBlocking:
    def test_the_scene_carries_no_blocking_field(self) -> None:
        """Nothing is persisted: no `Scene` field, and therefore no schema bump.

        This is also what keeps the 33 archived sessions openable - see
        `.plan/para-o-dono/79-blocking-shape.md`, decision 3, deferred.
        """
        assert {f.name for f in fields(Scene)} == {
            "location",
            "time_of_day",
            "present_characters",
            "physical_facts",
            "zones",
            "positions",
        }

    def test_no_perception_entry_point_accepts_blocking(self) -> None:
        for name in ("can_perceive", "eligible_witnesses", "perception_clusters"):
            signature = inspect.signature(getattr(perception, name))
            assert "blocking" not in signature.parameters, name

    def test_the_perception_module_never_mentions_blocking(self) -> None:
        """A refactor that threads it in would have to delete this test first."""
        source = inspect.getsource(perception)
        assert "blocking" not in source.lower()

    def test_the_prose_renderer_is_the_only_approved_reader(self) -> None:
        assert "blocking" in inspect.signature(build_prose_messages).parameters

    def test_the_director_prompt_is_not_a_reader_in_v1(self) -> None:
        """Approved as "yes" but deferred with the bump: it needs durable state."""
        assert "blocking" not in inspect.signature(narrate).parameters


class TestNarrateDerivesBlockingFromTheDirectorsOwnField:
    """`narrate()` keeps `character_zones`; it does not keep it raw.

    Driven through the real function rather than a mirror of it, because a mirror
    is a second implementation that can agree with a test and disagree with the
    engine. It is model-authored free text written without being asked to keep a
    secret, and it lands in the blind renderer's prompt, so it earns the same
    treatment event content gets: present characters only, normalized, redacted.
    """

    async def _narrate(self, monkeypatch, response: dict, game) -> dict:  # noqa: ANN001
        async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003
            return response

        monkeypatch.setattr(narrator_mod, "call_agent", fake_call_agent)
        return await narrate(
            client=httpx.AsyncClient(),
            scene=game.scene,
            characters=game.characters,
            player_controlled_id="C1",
            history=game.history,
            config={},
        )

    def _beat(self, zones: dict[str, str]) -> dict:
        return director_beat(
            scene_blocking={
                "character_zones": zones,
                "action_location": "",
                "spatial_constraints": [],
                "destination_reachable_this_beat": True,
            }
        )

    @pytest.mark.asyncio
    async def test_the_field_survives_instead_of_being_discarded(self, monkeypatch) -> None:  # noqa: ANN001
        """The whole of task 79's ship-now half, in one assertion."""
        cast = make_cast("Link", "Marta")
        game = make_game(characters=cast, controlled="C1")
        result = await self._narrate(
            monkeypatch, self._beat({"C1": "junto a porta", "C2": "atras da mesa"}), game
        )
        assert result["blocking"] == {"C1": "junto a porta", "C2": "atras da mesa"}

    @pytest.mark.asyncio
    async def test_the_scratch_field_itself_still_does_not_escape(self, monkeypatch) -> None:  # noqa: ANN001
        cast = make_cast("Link")
        game = make_game(characters=cast, controlled="C1")
        result = await self._narrate(monkeypatch, self._beat({"C1": "junto a porta"}), game)
        assert "scene_blocking" not in result

    @pytest.mark.asyncio
    async def test_absent_and_unknown_characters_are_dropped(self, monkeypatch) -> None:  # noqa: ANN001
        cast = make_cast("Link", "Marta")
        game = make_game(characters=cast, controlled="C1")
        game.scene.present_characters = ["C1"]
        result = await self._narrate(
            monkeypatch,
            self._beat({"C1": "junto a porta", "C2": "no corredor", "C9": "?"}),
            game,
        )
        assert result["blocking"] == {"C1": "junto a porta"}

    @pytest.mark.asyncio
    async def test_an_empty_position_is_dropped(self, monkeypatch) -> None:  # noqa: ANN001
        cast = make_cast("Link")
        game = make_game(characters=cast, controlled="C1")
        result = await self._narrate(monkeypatch, self._beat({"C1": "   "}), game)
        assert result["blocking"] == {}

    @pytest.mark.asyncio
    async def test_a_long_position_is_truncated(self, monkeypatch) -> None:  # noqa: ANN001
        cast = make_cast("Link")
        game = make_game(characters=cast, controlled="C1")
        result = await self._narrate(monkeypatch, self._beat({"C1": "x" * 500}), game)
        assert len(result["blocking"]["C1"]) == 160

    @pytest.mark.asyncio
    async def test_a_missing_scene_blocking_yields_no_blocking(self, monkeypatch) -> None:  # noqa: ANN001
        """Turns without it take exactly the pre-79 path."""
        cast = make_cast("Link")
        game = make_game(characters=cast, controlled="C1")
        beat = director_beat()
        beat.pop("scene_blocking")
        result = await self._narrate(monkeypatch, beat, game)
        assert result["blocking"] == {}
