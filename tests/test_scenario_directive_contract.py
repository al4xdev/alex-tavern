"""Task 57 follow-up: a scenario's own directives can leak what the core cannot.

`narrator_directives` reach the Director, the Historian, both suggestion paths
and the Architect. The core stopped naming the operator, but a scenario that
says "the player controls Link" tells all of them anyway.

The scenario belongs to whoever wrote it, so this is recorded and never
rewritten: silently editing somebody's narrative text is a worse failure than
the leak it would hide.
"""

from __future__ import annotations

import json

import httpx
import pytest

from src.llm.debug_log import read_entries
from src.runner import Runner
from src.store.sessions import load_game
from tests.factories import make_cast, make_scene


def _warnings(session_id: str) -> list[dict]:
    return [
        entry
        for entry in read_entries(session_id, 200)
        if entry.get("agent") == "scenario_contract"
    ]


@pytest.mark.asyncio
async def test_leaking_directives_are_recorded_and_left_untouched() -> None:
    directives = (
        "Fantasia escolar.\n\nAGENCIA DO JOGADOR\n"
        "O jogador controla Link (C1). Nenhum agente escolhe falas por Link."
    )
    cast = make_cast("Link")
    runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
    session_id = await runner.start_session(
        {
            "characters": cast,
            "scene": make_scene(characters=cast, location="Salao"),
            "narrator_directives": directives,
        }
    )

    found = _warnings(session_id)
    assert len(found) == 1
    assert found[0]["status"] == "operator_ontology"
    assert "O jogador" in found[0]["phrases"]

    game = load_game(session_id)
    assert game is not None
    assert game.narrator_directives == directives, "the author's text is never rewritten"


@pytest.mark.asyncio
async def test_clean_directives_produce_no_warning() -> None:
    cast = make_cast("Link")
    runner = Runner(httpx.AsyncClient(), {})  # type: ignore[arg-type]
    session_id = await runner.start_session(
        {
            "characters": cast,
            "scene": make_scene(characters=cast, location="Salao"),
            "narrator_directives": (
                "Fantasia escolar. Magia e regulada e o unico humano da corte e Link."
            ),
        }
    )
    assert _warnings(session_id) == []


def test_the_shipped_user_scenario_that_prompted_this_is_still_detected() -> None:
    """Regression fixture from the real .data scenario that surfaced the gap."""
    from src.prompt_contract import operator_ontology_hits

    directives = json.loads(
        json.dumps(
            {
                "narrator_directives": (
                    "AGENCIA DO JOGADOR\nO jogador controla Dax Vanguard (C1). "
                    "Deixe a situacao evoluir a partir das decisoes do personagem "
                    "controlado pelo humano (Dax Vanguard)."
                )
            }
        )
    )["narrator_directives"]
    hits = sorted(set(operator_ontology_hits(directives)))
    assert "O jogador" in hits
    assert "controlado pelo humano" in hits
