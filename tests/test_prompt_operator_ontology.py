"""Task 57: no agent may learn that a human drives one of the characters.

`AGENTS.md` §3 promises a stronger thing than "the model knows but keeps quiet":
the operator's existence never becomes text. The agency lock is deterministic
and lives in the Runner, so a prompt that restates it is pure leakage — it
hands the model a protected identity in exchange for nothing.

These tests read the **final messages** of each shipped builder, not the
helpers that feed them, because the last refactor that only checked a helper is
exactly how `(controlled by the player)` survived ten days of green suites.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents import character, narrator, perspective, prose, summarizer
from src.models import Roteiro, RoteiroBeat
from src.prompt_contract import (
    leaks_operator_ontology,
    operator_ontology_hits,
)
from src.roteiro import (
    _story_context_lines,
    _validate_beat,
    build_next_beat_messages,
    build_roteiro_messages,
)
from tests.factories import make_cast, make_game, make_record, make_scene

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "src" / "scenarios"


def _game_with_history():
    cast = make_cast("Rui", "Marta", "Nuno")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled="C1")
    game.narrator_directives = "Tom sombrio. A magia e rara."
    game.story_summary = "Choveu a noite toda."
    game.history = [
        make_record(1, "Player", "Quem pilota?", scene=game.scene),
        make_record(1, "C2", "Eu piloto.", scene=game.scene),
    ]
    return game


def _director_messages(game, *, exclude_controlled: bool = True) -> list[str]:
    return [
        narrator._build_system_prompt(list(game.characters), game.narrator_directives),
        narrator._build_user_prompt(
            game.scene,
            game.characters,
            game.player.controlled_character_id,
            game.history,
            story_summary=game.story_summary,
            exclude_speaker=(
                game.player.controlled_character_id if exclude_controlled else None
            ),
        ),
    ]


def _all_family_messages(game) -> dict[str, str]:
    """Every prompt family the Runner can send, as the text actually posted."""
    controlled = game.player.controlled_character_id
    other = next(cid for cid in game.characters if cid != controlled)
    families: dict[str, str] = {}

    for index, text in enumerate(_director_messages(game)):
        families[f"director:{index}"] = text

    families["narrator_suggest"] = narrator._build_suggest_system_prompt(
        controlled, game.characters[controlled].mind.name, game.narrator_directives
    )
    for index, message in enumerate(
        narrator.build_opening_suggestions_messages(game.scene, game.narrator_directives)
    ):
        families[f"opening_suggest:{index}"] = message["content"]

    families["character"] = character._build_system_prompt(game.characters[other])
    families["historian"] = summarizer._build_system_prompt(game.narrator_directives)

    for index, message in enumerate(
        prose.build_prose_messages(game.scene, game.characters, controlled, game.history, [])
    ):
        families[f"prose:{index}"] = message["content"]

    families["perspective:init:system"] = perspective._INIT_SYSTEM
    families["perspective:update:system"] = perspective._UPDATE_SYSTEM
    _, roster = perspective._roster_lines(game.characters, other)
    families["perspective:init:roster"] = "\n".join(roster)

    families["roteiro:context"] = "\n".join(_story_context_lines(game))
    for index, message in enumerate(build_roteiro_messages(game)):
        families[f"roteiro:compile:{index}"] = message["content"]

    return families


def test_no_shipped_prompt_family_names_an_outside_operator() -> None:
    game = _game_with_history()
    leaking = {
        name: sorted(set(operator_ontology_hits(text)))
        for name, text in _all_family_messages(game).items()
        if leaks_operator_ontology(text)
    }
    assert leaking == {}, f"prompt families leaking operator ontology: {leaking}"


def test_replan_messages_stay_blind_too() -> None:
    game = _game_with_history()
    roteiro = Roteiro(
        premise="Alguem chega",
        acts=[],
        beat=RoteiroBeat(
            beat_id="b1",
            intent="Pressao sobe",
            expected_actors=["C2"],
            expected_anchors=["porta"],
            exit_condition="alguem sai",
            budget_turns=2,
        ),
    )
    for index, message in enumerate(build_next_beat_messages(game, roteiro, "advance", "beat")):
        assert not leaks_operator_ontology(message["content"]), (
            f"roteiro:replan message {index} leaks "
            f"{sorted(set(operator_ontology_hits(message['content'])))}"
        )


@pytest.mark.parametrize("controlled", ["C1", "C2", "C3"])
def test_perspective_roster_is_identical_whoever_is_controlled(controlled: str) -> None:
    """Switching the controlled character must not change one byte of the roster."""
    cast = make_cast("Rui", "Marta", "Nuno")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled=controlled)
    _, roster = perspective._roster_lines(game.characters, "C2")
    assert roster == [
        '  C1: canonical name "Rui" | visible appearance: d',
        '  C3: canonical name "Nuno" | visible appearance: d',
    ]
    assert not leaks_operator_ontology("\n".join(roster))


def test_roteiro_prompt_does_not_mark_the_controlled_character() -> None:
    game = _game_with_history()
    context = "\n".join(_story_context_lines(game))
    controlled_line = next(line for line in context.splitlines() if "ID=C1" in line)
    other_line = next(line for line in context.splitlines() if "ID=C2" in line)
    # Same shape for both: only the id, the name and the personality.
    assert controlled_line.replace("C1", "CX").replace("Rui", "NAME") == other_line.replace(
        "C2", "CX"
    ).replace("Marta", "NAME")


def test_validate_beat_still_removes_the_controlled_character() -> None:
    """The lock moved nowhere: it was always deterministic, in the Runner's code."""
    game = _game_with_history()
    beat = _validate_beat(
        {
            "beat_id": "b1",
            "intent": "Todos se movem",
            "expected_actors": ["C1", "C2", "C3"],
            "expected_anchors": ["porta"],
            "exit_condition": "alguem sai",
            "budget_turns": 2,
        },
        game,
        "fallback",
    )
    assert "C1" not in beat.expected_actors
    assert beat.expected_actors == ["C2", "C3"]


def test_builtin_scenarios_carry_no_operator_ontology() -> None:
    leaking = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        directives = json.loads(path.read_text(encoding="utf-8")).get("narrator_directives", "")
        hits = sorted(set(operator_ontology_hits(directives)))
        if hits:
            leaking[path.name] = hits
    assert leaking == {}, f"built-in scenarios leaking operator ontology: {leaking}"


def test_the_rule_catches_the_four_shapes_that_actually_shipped() -> None:
    """Regression fixtures: the exact strings that were live before this task."""
    for shipped in (
        ' C2: canonical name "Marta" (controlled by the player) | visible appearance: d',
        "The player's own speech or action in the final HISTORY entry IS such an event",
        "Leaving next_speakers empty there is the world ignoring the player",
        "  ID=C1 | Rui (PROTAGONIST — never an expected actor): p",
        "reaja à agência humana",
        "as decisões do personagem controlado pelo humano (Dax Vanguard)",
        "AGÊNCIA DO JOGADOR",
    ):
        assert leaks_operator_ontology(shipped), f"rule missed a shipped leak: {shipped!r}"


def test_the_rule_leaves_diegetic_language_alone() -> None:
    """"human" is a species and "protagonist" is craft talk; neither is ontology."""
    for legitimate in (
        "Marta e a unica humana entre os elfos da corte.",
        "O bardo e um player de alaude notavel na regiao.",
        "Escreva situacoes, nunca decisoes: as escolhas de cada personagem sao sagradas.",
        "A patrulha imperial entra na cantina e varre o local com os olhos.",
        "Every character's choices are sacred: plan around them, not for them.",
        "expected_actors: character IDs who should get stage time during the beat.",
    ):
        assert not leaks_operator_ontology(legitimate), (
            f"rule false-positives on diegetic text: {legitimate!r} -> "
            f"{operator_ontology_hits(legitimate)}"
        )
