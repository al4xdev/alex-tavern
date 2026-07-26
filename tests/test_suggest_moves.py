"""Task 55: a suggestion is one character's draft, not the Narrator's view.

The old implementation asked an omniscient Narrator and handed it
`_build_user_prompt` — every sheet, every private thought, the roteiro. These
tests pin the boundary that replaced it, and the two properties that make a
suggestion safe: it knows only what the character perceives, and asking for one
changes nothing.
"""

from __future__ import annotations

import httpx
import pytest

from src.agents.suggest import (
    SUGGESTION_MAX_TOKENS,
    build_suggestion_messages,
    build_suggestion_schema,
    suggest_moves,
)
from src.prompt_contract import leaks_operator_ontology
from tests.factories import make_cast, make_character, make_game, make_record, make_scene


def _game():
    cast = {
        "C1": make_character(
            "Link",
            personality="Curioso e cauteloso.",
            knowledge=["A nevoa vem do arco leste."],
            current_mood="tenso",
        ),
        "C2": make_character(
            "Maelis",
            personality="Diretora severa.",
            knowledge=["O SEGREDO DE MAELIS: ela abriu a ferida."],
            current_mood="fria",
        ),
        "C3": make_character("Garran", personality="Instrutor pratico."),
    }
    game = make_game(
        characters=cast,
        scene=make_scene(characters=cast, location="Salao do Prisma", time_of_day="tarde"),
        controlled="C1",
    )
    game.scene.physical_facts = {"arco leste": "instavel"}
    game.narrator_directives = "Fantasia escolar. Magia e regulada."
    game.history = [
        make_record(1, "C1", "Alguem viu a nevoa?", scene=game.scene),
        make_record(1, "C1", "Preciso chegar perto do arco.", "thought", scene=game.scene),
        make_record(2, "C2", "Fiquem onde estao.", scene=game.scene),
        make_record(2, "C2", "ELES NAO PODEM SABER QUE FUI EU.", "thought", scene=game.scene),
        make_record(3, "C3", "O arco leste range.", scene=game.scene),
    ]
    return game


def _request_text(game) -> str:
    messages = build_suggestion_messages(
        game.scene,
        game.characters,
        game.player.controlled_character_id,
        game.history,
        game.narrator_directives,
    )
    return "\n".join(message["content"] for message in messages)


def test_no_other_characters_private_thought_reaches_the_request() -> None:
    text = _request_text(_game())
    assert "ELES NAO PODEM SABER QUE FUI EU." not in text
    assert "Preciso chegar perto do arco." in text, "the character keeps their own thoughts"


def test_no_other_characters_sheet_reaches_the_request() -> None:
    text = _request_text(_game())
    assert "O SEGREDO DE MAELIS" not in text
    assert "Diretora severa." not in text
    assert "Instrutor pratico." not in text
    assert "Curioso e cauteloso." in text, "the character keeps their own sheet"


def test_request_carries_the_scene_and_the_characters_own_knowledge() -> None:
    text = _request_text(_game())
    assert "Salao do Prisma" in text
    assert "arco leste: instavel" in text
    assert "A nevoa vem do arco leste." in text
    assert "Fantasia escolar. Magia e regulada." in text


def test_request_never_names_an_operator() -> None:
    """The Runner owns agency; a suggestion must not hint that a human exists."""
    assert not leaks_operator_ontology(_request_text(_game()))


def test_schema_demands_exactly_three_speech_action_pairs() -> None:
    schema = build_suggestion_schema()["schema"]
    suggestions = schema["properties"]["suggestions"]
    assert suggestions["minItems"] == 3
    assert suggestions["maxItems"] == 3
    assert set(suggestions["items"]["properties"]) == {"speech", "action"}
    assert suggestions["items"]["additionalProperties"] is False


@pytest.mark.asyncio
async def test_budget_is_fixed_and_small_regardless_of_provider_context() -> None:
    """A helper must not become the most expensive call because a provider is big."""
    captured: dict = {}

    async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003
        captured.update(kwargs)
        captured["messages"] = messages
        return {"suggestions": [{"speech": "a", "action": ""} for _ in range(3)]}

    from src.agents import suggest as suggest_mod

    original = suggest_mod.call_agent
    suggest_mod.call_agent = fake_call_agent
    try:
        game = _game()
        await suggest_moves(
            httpx.AsyncClient(),
            game.scene,
            game.characters,
            "C1",
            game.history,
            {"context_max": 1_000_000, "max_tokens_narrator": 24576},
            game.narrator_directives,
            session_id="s",
        )
    finally:
        suggest_mod.call_agent = original

    assert captured["max_tokens"] == SUGGESTION_MAX_TOKENS == 1024
    assert captured["agent"] == "suggest_moves"


@pytest.mark.asyncio
async def test_asking_for_suggestions_persists_and_executes_nothing() -> None:
    """Agency test: the drafts come back and the world is untouched."""
    from src.models import game_state_to_dict

    game = _game()
    before = game_state_to_dict(game)

    async def fake_call_agent(client, config, messages, **kwargs):  # noqa: ANN001, ANN003
        return {
            "suggestions": [
                {"speech": "Pergunto a Garran.", "action": ""},
                {"speech": "", "action": "Ando ate o arco."},
                {"speech": "", "action": "Fico parado e observo."},
            ]
        }

    from src.agents import suggest as suggest_mod

    original = suggest_mod.call_agent
    suggest_mod.call_agent = fake_call_agent
    try:
        moves = await suggest_moves(
            httpx.AsyncClient(), game.scene, game.characters, "C1", game.history, {}
        )
    finally:
        suggest_mod.call_agent = original

    assert len(moves) == 3
    assert moves[1]["action"] == "Ando ate o arco."
    assert game_state_to_dict(game) == before


def test_whispered_records_outside_the_audience_stay_out() -> None:
    cast = make_cast("Link", "Maelis", "Garran")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled="C1")
    game.history = [
        make_record(
            1, "C2", "SEGREDO SUSSURRADO PARA GARRAN", scene=game.scene, audience=["C3"]
        ),
        make_record(1, "C2", "Bom dia a todos.", scene=game.scene),
    ]
    text = _request_text(game)
    assert "SEGREDO SUSSURRADO PARA GARRAN" not in text
    assert "Bom dia a todos." in text
