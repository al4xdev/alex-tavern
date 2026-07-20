"""WT-09 fix: Director `audible_speech` events persist to history.

The counter-canon oracle's WT-09 failed at the epilogue: a witness could not
recall that "the Dama do Norte is Glinda" because that reveal was staged by the
Director as an ``audible_speech`` perception event, and those events — unlike
character speech, player input, and narration — were never written to
``game.history``. They were rendered to that turn's REPLYING characters, fed to
the prose renderer, and counted for roteiro coverage, then discarded. A witness
who did not happen to reply that turn never perceived the spoken fact, and no
one could recall it later, because memory reads history.

The runner now records each audible_speech event as a spoken record (scoped to
its witnesses, zone origin). This test guards that a non-replying witness's
history retains the spoken fact.
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


CHARACTERS = {"C1": _char("Alice"), "C2": _char("Dorothy"), "C3": _char("Holmes")}
SCENE = Scene(
    location="Salao do Prisma",
    time_of_day="Manha",
    present_characters=["C1", "C2", "C3", "Player"],
    physical_facts={},
)

REVEAL = "Le em voz alta: 'a Dama do Norte e Glinda, que planeja a conquista das cinco cidades.'"


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
                    "witness_ids": ["C2", "C3"],  # every present character hears it -> public
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
    # can recall it. C2 witnessed it though it did not reply this turn.
    reveal = [r for r in game.history if "Glinda" in r.content]
    assert reveal, "the audible reveal must be persisted to history"
    from src.models import record_visible_to

    assert record_visible_to(reveal[0], "C2")  # the witness can recall it


@pytest.mark.asyncio
async def test_whisper_narration_audible_speech_is_not_persisted(monkeypatch) -> None:  # noqa: ANN001
    """Leak-safety: when the Director re-narrates a WHISPER with a broad scope
    carrying the secret inside, that audible_speech is NOT persisted — it would
    hand the secret to a listener outside the whisper. A shared record cannot be
    redacted per viewer, so the whole event is skipped.
    """
    from src.runner import Runner

    secret = "XILVAROK9"  # a distinctive payload token only C2 is told

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        # The Director broadly re-narrates the whisper, secret and all, to C2+C3.
        return {
            "narration": "Alice murmura algo.",
            "next_speakers": ["Narrator"],
            "perception_events": [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C1",
                    "content": f"Alice murmura, audivel aos proximos: 'o codigo e {secret}'.",
                    "witness_ids": ["C2", "C3"],  # C3 is NOT a confidant of the whisper
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
            # Turn 1: the player whispers the secret to C2 only (a whisper record).
            await runner.player_turn(
                sid, speech=f"So entre nos: o codigo e {secret}.", audience=["C2"]
            )
            # Turn 2: the Director broadly re-narrates it -> must be skipped.
            await runner.player_turn(sid, speech="Prossigo.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert game is not None
    # The whisper record itself keeps the secret (scoped to C2); the Director's
    # broad re-narration must NOT have created a zone-origin record with it.
    zone_leaks = [r for r in game.history if r.audience_origin == "zone" and secret in r.content]
    assert not zone_leaks
