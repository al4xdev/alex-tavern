"""A burst beat that produces nothing must not commit as a turn.

Found by the task 45 HTTP smoke, not by any unit test. The chain is real and
was reproduced from a live session (`ce70b997`, turn 4):

1. a burst beat's Director returns a single perception event;
2. that event repeats one from an earlier beat, so the burst's own
   anti-repetition filter (task 37) empties the list;
3. with no events left, a multi-beat step deliberately narrates NOTHING;
4. the queue is the controlled character, so the speaker loop stops
   immediately and nobody replies;
5. the beat commits anyway - burning a turn number, a clock tick and a
   revision, with zero history records.

The cost is not cosmetic. `_next_turn_number` reads the LAST RECORD's number,
so the consumed number is handed out again, and two different beats end up
sharing one turn number - which undo then pops together, breaking the contract
this feature is built on: "each beat commits as its OWN turn (undo pops one
beat)".
"""

from __future__ import annotations

import httpx
import pytest

from src.runner import Runner
from src.store.sessions import delete_session, load_game
from tests.factories import director_beat, make_cast, make_scene


def _events(*contents: str) -> list[dict]:
    return [
        {
            "event_kind": "observation",
            "subject_id": "Narrator",
            "content": content,
            "witness_ids": ["C1", "C2"],
        }
        for content in contents
    ]


class TestEmptyBeat:
    async def _burst(self, monkeypatch, beats: list[dict]) -> tuple[object, str]:
        """Run one skip turn whose Director answers `beats` in order."""
        from src import runner as runner_mod

        calls = {"n": 0}

        async def fake_narrate(**kwargs):  # noqa: ANN003, ANN202
            index = min(calls["n"], len(beats) - 1)
            calls["n"] += 1
            return beats[index]

        async def fake_prose(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return "A cena respira."

        async def fake_character(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return {"speech": "Digo algo.", "thought": None, "action_intent": None}

        async def fake_init(client, viewer_id, characters, cfg, **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
            from src.models import CharacterPerspective

            turn_number = kwargs.get("turn_number", 0)
            return CharacterPerspective(
                initialized_turn=turn_number, processed_through_turn=turn_number
            )

        monkeypatch.setattr(runner_mod, "initialize_perspective", fake_init)
        monkeypatch.setattr(runner_mod, "narrate", fake_narrate)
        monkeypatch.setattr(runner_mod, "render_narration", fake_prose)
        monkeypatch.setattr(runner_mod, "character_act", fake_character)

        client = httpx.AsyncClient()
        # auto_event_enabled defaults to True and fires an LLM call on a probability
        # roll, which made an earlier version of this file pass alone and fail in
        # the full suite. The burst is what is under test, not the dice.
        runner = Runner(client, {"autonomous_burst_max_beats": 3, "auto_event_enabled": False})
        cast = make_cast("Thorn", "Lyra")
        sid = await runner.start_session(
            {
                "characters": cast,
                "scene": make_scene(characters=cast),
                "controlled_character_id": "C1",
            }
        )
        result = await runner.player_turn(sid, skip=True)
        return (runner, sid, result, client)

    @pytest.mark.asyncio
    async def test_a_beat_with_nothing_to_show_is_not_committed(self, monkeypatch) -> None:  # noqa: ANN001
        """Beat 2 repeats beat 1's event and routes to the protagonist."""
        repeated = "A porta range com o vento."
        beats = [
            director_beat(next_speakers=["C2"], perception_events=_events(repeated)),
            # Same text: the burst filter empties it. Queue is the controlled
            # character, so nobody speaks either.
            director_beat(next_speakers=["C1"], perception_events=_events(repeated)),
        ]
        runner, sid, result, client = await self._burst(monkeypatch, beats)
        try:
            game = load_game(sid)
            assert game is not None
            turns_with_records = {record.turn_number for record in game.history}
            reported = {beat["turn_number"] for beat in result["beats"]}

            assert reported <= turns_with_records, (
                f"beats {sorted(reported - turns_with_records)} were reported to the "
                "caller but left no record in history"
            )
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_an_uncommitted_beat_does_not_burn_a_turn_number(self, monkeypatch) -> None:  # noqa: ANN001
        """The next turn must not reuse a number an empty beat consumed."""
        repeated = "A porta range com o vento."
        beats = [
            director_beat(next_speakers=["C2"], perception_events=_events(repeated)),
            director_beat(next_speakers=["C1"], perception_events=_events(repeated)),
        ]
        runner, sid, result, client = await self._burst(monkeypatch, beats)
        try:
            game = load_game(sid)
            assert game is not None
            last_recorded = max(record.turn_number for record in game.history)
            highest_reported = max(beat["turn_number"] for beat in result["beats"])
            assert highest_reported == last_recorded, (
                f"the burst reported turn {highest_reported} but history stops at "
                f"{last_recorded}; the next turn would reuse that number"
            )
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_the_clock_only_advances_for_beats_that_happened(self, monkeypatch) -> None:  # noqa: ANN001
        repeated = "A porta range com o vento."
        beats = [
            director_beat(next_speakers=["C2"], perception_events=_events(repeated)),
            director_beat(next_speakers=["C1"], perception_events=_events(repeated)),
        ]
        runner, sid, result, client = await self._burst(monkeypatch, beats)
        try:
            game = load_game(sid)
            assert game is not None
            assert game.narrative_tick == len(result["beats"]), (
                f"clock at {game.narrative_tick} for {len(result['beats'])} reported beats"
            )
        finally:
            await delete_session(sid)
            await client.aclose()

    @pytest.mark.asyncio
    async def test_a_beat_that_narrates_is_still_committed(self, monkeypatch) -> None:  # noqa: ANN001
        """The guard must not swallow a beat that genuinely produced something."""
        beats = [
            director_beat(next_speakers=["C2"], perception_events=_events("Alguem entra.")),
            director_beat(next_speakers=["C2"], perception_events=_events("A luz apaga.")),
        ]
        runner, sid, result, client = await self._burst(monkeypatch, beats)
        try:
            game = load_game(sid)
            assert game is not None
            assert len(result["beats"]) >= 2, "two distinct beats must both commit"
            turns_with_records = {record.turn_number for record in game.history}
            assert {beat["turn_number"] for beat in result["beats"]} <= turns_with_records
        finally:
            await delete_session(sid)
            await client.aclose()
