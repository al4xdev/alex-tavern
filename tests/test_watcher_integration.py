"""Task 33b: the watcher wired into the runner turn loop (behind watcher_enabled).

Proves the end-to-end control flow with the two LLM calls mocked: immobile
turns accumulate the quiet counter, the ladder tolerates one beat of silence,
then fires a causal disruption into the blind narrator_hint channel, and the
refractory window suppresses an immediate re-fire.

The turns here are player-speech turns (not bare skips) because the watcher is
the fallback for a FREE hint channel: on a bare skip, task-40's
time-compression invite owns the channel and the watcher yields to it
(pre-empting that invite on stalled skips is a documented follow-up).
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
from src.watcher import CausalIntervention, DeltaAudit


async def _fake_prose() -> str:
    return "Narracao de teste."


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

DISRUPTION = "Do arco selado, um raspar metálico anuncia algo que força a porta."


@pytest.mark.asyncio
async def test_stall_accumulates_then_ladder_disrupts_then_refractory(monkeypatch) -> None:  # noqa: ANN001
    import src.runner as runner_mod
    from src.runner import Runner

    hints: list[str] = []

    async def fake_audit(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        return DeltaAudit(categories=("none",))  # every turn stands still

    async def fake_intervention(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        return CausalIntervention(
            source_thread="o arco selado range",
            target_state="a delegacao encara a intrusao",
            event_now=DISRUPTION,
            expected_delta="uma forca externa entra em cena",
            refractory_turns=3,
        )

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        hints.append(narrator_hint)
        return {
            "narration": "Segue.",
            "next_speakers": ["Narrator"],
            "perception_events": [],
            "scene_update": None,
            "mood_updates": None,
        }

    monkeypatch.setattr(runner_mod, "audit_delta", fake_audit)
    monkeypatch.setattr(runner_mod, "generate_causal_intervention", fake_intervention)

    config = {
        "watcher_enabled": True,
        "watcher_quiet_threshold": 2,
        "watcher_refractory_turns": 3,
        "auto_event_enabled": False,  # keep the drive scheduler out of the way
    }
    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)
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
            for _ in range(5):
                await runner.player_turn(sid, speech="Sigo observando.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    # T1/T2 below threshold, T3 spends the silence grace -> no hint; T4 fires the
    # causal disruption; T5 is suppressed (quiet reset + refractory).
    assert hints[0] == "" and hints[1] == "" and hints[2] == ""
    assert hints[3] == DISRUPTION
    assert hints[4] == ""
    assert game is not None
    assert game.watcher_last_intervention_tick == 3  # fired on T4 (tick 3 before increment)
    # T4 reset quiet to 0; T4 and T5 each then audited `none` -> back up to 2.
    assert game.watcher_quiet_turns == 2


@pytest.mark.asyncio
async def test_disabled_watcher_never_audits_or_intervenes(monkeypatch) -> None:  # noqa: ANN001
    import src.runner as runner_mod
    from src.runner import Runner

    calls = {"audit": 0, "intervene": 0}

    async def fake_audit(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        calls["audit"] += 1
        return DeltaAudit(categories=("none",))

    async def fake_intervention(client, game, config, turn_number):  # noqa: ANN001, ANN202, ARG001
        calls["intervene"] += 1
        return CausalIntervention("t", "s", "e", "d", 3)

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return {
            "narration": "Segue.",
            "next_speakers": ["Narrator"],
            "perception_events": [],
            "scene_update": None,
            "mood_updates": None,
        }

    monkeypatch.setattr(runner_mod, "audit_delta", fake_audit)
    monkeypatch.setattr(runner_mod, "generate_causal_intervention", fake_intervention)

    async with httpx.AsyncClient() as client:
        runner = Runner(client, {"auto_event_enabled": False})  # watcher_enabled absent -> OFF
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
            for _ in range(4):
                await runner.player_turn(sid, speech="Sigo observando.")
            game = await runner.get_state(sid)
        finally:
            await delete_session(sid)

    assert calls == {"audit": 0, "intervene": 0}
    assert game is not None and game.watcher_quiet_turns == 0
