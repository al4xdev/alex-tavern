"""`scene_update` is the Director output with no per-viewer projection.

Everything else it returns gets filtered on the way to a reader: perception
events are rendered per witness and whispers stripped there, prose is generated
from a redacted view. A physical fact is different — it goes verbatim into the
prose prompt and, worse, `confidentiality.known_tokens` counts every token in it
as legitimately public FOR EVERY VIEWER, subtracting it from both the whisper and
the thought secret sets. Facts are never pruned, so one laundered token silences
the guard permanently.

The Director is omniscient (Task 41): it reads every whisper and every private
thought, and it writes free-form strings into that dict on almost every turn (37
of 38 in the measured session, including character-scoped values like
`bruma_status: "Bruma esta escondida no antigo canil"`). So the channel was one
model slip away from a permanent, global secrecy hole.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.agents import narrator as narrator_mod
from src.agents.narrator import narrate
from src.confidentiality import hidden_whisper_tokens, scene_fact_secret_tokens
from src.runner import _evict_oldest_facts, _fact_key_admissible
from tests.factories import director_beat, make_cast, make_game, make_record

SECRET = "Vharkhalos"


def _game_with_whisper():
    """C2 whispers a rare name to C3; C1 is present and did NOT hear it."""
    cast = make_cast("Link", "Maelis", "Riven")
    game = make_game(characters=cast, controlled="C1")
    game.history = [
        make_record(
            1,
            "C2",
            f"O nome verdadeiro do selo e {SECRET}, nao repita.",
            scene=game.scene,
            audience=["C2", "C3"],
            audience_origin="whisper",
        )
    ]
    return game


class TestTheLaunderingPath:
    def test_a_whispered_token_is_secret_before_it_becomes_a_fact(self) -> None:
        game = _game_with_whisper()
        secret = hidden_whisper_tokens(game.history, "C1", game.characters, game.scene)
        assert SECRET.casefold() in secret

    def test_writing_it_as_a_fact_would_make_it_public_to_everyone(self) -> None:
        """The hazard itself, stated as a test: this is why redaction is needed.

        Not a defect being fixed — it is the reason the fix has to happen
        upstream, in `narrate`, before the fact is ever applied.
        """
        game = _game_with_whisper()
        game.scene.physical_facts["seal_name"] = f"o selo responde a {SECRET}"
        secret = hidden_whisper_tokens(game.history, "C1", game.characters, game.scene)
        assert SECRET.casefold() not in secret, (
            "a fact launders the token into public knowledge — permanently"
        )

    def test_the_scene_fact_secret_set_covers_every_present_viewer(self) -> None:
        game = _game_with_whisper()
        secret = scene_fact_secret_tokens(game.history, game.characters, game.scene)
        assert SECRET.casefold() in secret, (
            "a whisper one present character missed must still be secret for facts"
        )


class TestNarrateRedactsFacts:
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

    @pytest.mark.asyncio
    async def test_a_whispered_secret_never_reaches_a_physical_fact(self, monkeypatch) -> None:  # noqa: ANN001
        game = _game_with_whisper()
        result = await self._narrate(
            monkeypatch,
            director_beat(scene_update={"seal_name": f"o selo responde a {SECRET}"}),
            game,
        )
        assert SECRET.casefold() not in str(result["scene_update"]).casefold()

    @pytest.mark.asyncio
    async def test_an_ordinary_fact_survives_untouched(self, monkeypatch) -> None:  # noqa: ANN001
        """The interlock: redaction must not eat the channel it protects."""
        game = _game_with_whisper()
        result = await self._narrate(
            monkeypatch, director_beat(scene_update={"main_doors": "trancadas"}), game
        )
        assert result["scene_update"]["main_doors"] == "trancadas"


class TestValuesAreCoercedNotRejected:
    """A bool used to discard the entire turn.

    The schema demanded string-or-null and the local validator threw away the
    whole decision — events, moods, zone moves — resampling with the same
    messages and no correction. Across the battery runs 5 of the 8 Director
    validation failures were exactly one boolean fact value.
    """

    @pytest.mark.asyncio
    async def test_a_boolean_fact_is_coerced_instead_of_losing_the_turn(
        self, monkeypatch
    ) -> None:  # noqa: ANN001
        cast = make_cast("Link", "Maelis")
        game = make_game(characters=cast, controlled="C1")
        calls: list[Any] = []

        async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003
            calls.append(kwargs)
            return director_beat(
                next_speakers=["C2"], scene_update={"gate_sealed": True, "lamps_lit": 3}
            )

        monkeypatch.setattr(narrator_mod, "call_agent", fake_call_agent)
        result = await narrate(
            client=httpx.AsyncClient(),
            scene=game.scene,
            characters=game.characters,
            player_controlled_id="C1",
            history=game.history,
            config={},
        )
        assert len(calls) == 1, "no resample: a scalar is coerced, not rejected"
        assert result["scene_update"] == {"gate_sealed": "true", "lamps_lit": "3"}
        assert result["next_speakers"] == ["C2"], "the rest of the decision survived"

    @pytest.mark.asyncio
    async def test_the_schema_accepts_any_scalar_fact(self, monkeypatch) -> None:  # noqa: ANN001
        from src.llm.schema import validate_json_schema

        schema = narrator_mod.build_narrator_json_schema(["C1", "C2"])["schema"]
        # Only the keys the Director's own contract declares — `director_beat`
        # carries `narration`, which belongs to the prose renderer.
        payload = {
            key: value
            for key, value in director_beat(
                next_speakers=["C2"],
                scene_update={"gate_sealed": True, "lamps_lit": 3},
                perception_events=[
                    {
                        "event_kind": "observation",
                        "subject_id": "Narrator",
                        "content": "O portao bate.",
                        "witness_ids": ["C1", "C2"],
                    }
                ],
            ).items()
            if key in schema["properties"]
        }
        validate_json_schema(payload, schema)  # must not raise


class TestFactKeyHygiene:
    def test_a_near_synonym_of_an_existing_key_is_refused(self) -> None:
        facts = {"crack_in_ceiling": "fina"}
        assert not _fact_key_admissible("ceiling_crack", facts)
        assert not _fact_key_admissible("crack_in_ceilings", facts)

    def test_updating_an_existing_key_is_always_allowed(self) -> None:
        """Rejecting an update would freeze the world, which is the opposite fix."""
        facts = {"crack_in_ceiling": "fina"}
        assert _fact_key_admissible("crack_in_ceiling", facts)

    def test_per_character_transient_state_is_refused(self) -> None:
        assert not _fact_key_admissible("maelis_action", {})
        assert not _fact_key_admissible("goblin_position", {})
        assert not _fact_key_admissible("shaman_stance", {})

    def test_an_unrelated_new_fact_is_admitted(self) -> None:
        assert _fact_key_admissible("main_doors", {"crack_in_ceiling": "fina"})

    def test_the_budget_evicts_least_recently_written_first(self) -> None:
        facts = {f"fact_{index}": "x" for index in range(50)}
        _evict_oldest_facts(facts)
        assert len(facts) == 40
        assert "fact_0" not in facts and "fact_49" in facts
