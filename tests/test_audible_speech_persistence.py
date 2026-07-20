"""WT-09 root cause: Director `audible_speech` events don't persist to history.

The counter-canon oracle's WT-09 fails at the epilogue: a witness cannot recall
that "the Dama do Norte is Glinda" because that reveal was staged by the
Director as an ``audible_speech`` perception event, and those events — unlike
character speech, player input, and narration — are never written to
``game.history``. They are rendered to that turn's REPLYING characters, fed to
the prose renderer, and counted for roteiro coverage, then discarded. A witness
who did not happen to reply that turn never perceives the spoken fact, and no
one can recall it later, because memory reads history.

This test pins the gap in current code. It is xfail: when audible_speech events
are persisted as speech records (the fix), it xpasses.
"""

from __future__ import annotations

import httpx
import pytest

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    Scene,
    deepcopy_scene,
)
from src.store.sessions import delete_session


async def _fake_prose() -> str:
    return "Alguem leu um documento em voz alta."


def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Dorothy")}
SCENE = Scene(
    location="Salao do Prisma",
    time_of_day="Manha",
    present_characters=["C1", "C2", "Player"],
    physical_facts={},
)

REVEAL = "Le em voz alta: 'a Dama do Norte e Glinda, que planeja a conquista das cinco cidades.'"


@pytest.mark.xfail(
    reason="WT-09: Director audible_speech events are not persisted to history, "
    "so a non-replying witness can never recall the spoken fact.",
    strict=True,
)
@pytest.mark.asyncio
async def test_audible_speech_event_reaches_history(monkeypatch) -> None:  # noqa: ANN001
    from src.runner import Runner

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        # The reveal is spoken to the whole room, but NOBODY is queued to reply
        # this turn (next_speakers is the Narrator). C2 is a witness.
        return {
            "narration": "A sala escuta.",
            "next_speakers": ["Narrator"],
            "perception_events": [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C1",
                    "content": REVEAL,
                    "witness_ids": ["C2"],
                }
            ],
            "scene_update": None,
            "mood_updates": None,
        }

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {"auto_event_enabled": False})
        sid = runner.start_session(
            {
                "characters": dict(CHARACTERS),
                "scene": deepcopy_scene(SCENE),
                "controlled_character_id": "C1",
            }
        )
        monkeypatch.setattr(runner, "_call_narrator", fake_narrator)
        monkeypatch.setattr(
            runner, "_render_narration", lambda game, events, turn_number: _fake_prose()
        )
        try:
            await runner.player_turn(sid, speech="Leio a cifra decifrada em voz alta.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert game is not None
    # The spoken reveal must survive in the record so memory and future turns
    # can recall it. Today it does not: only the player's own input, the blind
    # narration, and character replies are recorded.
    assert any("Glinda" in record.content for record in game.history)
