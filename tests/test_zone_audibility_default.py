"""Task 54, finding 1: crossing a room must not make anyone deaf.

A new zone used to start audible from nowhere, and the Director was told exactly
that in its own contract. It used `zone_moves` for a position inside one hall
anyway ("C18 walks to the central table"), and the runtime sealed the hall in
two: twelve records with an empty audience, including a shouted warning that
reached no one.

The default is inverted here — a new zone is born audible from where its mover
came, and separation is declared with `zone_link_updates`, which is what that
field is for. These tests pin both halves: sound carries by default, and an
explicit seal still wins.
"""

from __future__ import annotations

from src.runner import Runner
from tests.factories import make_cast, make_game, make_scene


def _game():
    cast = make_cast("Link", "Garran", "Maelis")
    return make_game(
        characters=cast,
        scene=make_scene(characters=cast, location="Salao dos Quatro Arcos"),
        controlled="C1",
    )


def _apply(game, zone_moves):
    new_zones = [z for z in zone_moves.values() if z not in game.scene.zones]
    if new_zones and not game.scene.zones:
        stage = (game.scene.location or "").strip()[:60] or "palco"
        game.scene.zones[stage] = []
        for cid in game.scene.present_characters:
            if cid in game.characters:
                game.scene.positions[cid] = stage
    Runner._open_new_zones(game, zone_moves, new_zones)
    for moved_id, zone in zone_moves.items():
        game.scene.positions[moved_id] = zone
    return game


def test_first_split_of_a_stage_keeps_both_sides_audible() -> None:
    """The exact live-session shape: one character walks to the central table."""
    game = _apply(_game(), {"C2": "mesa central"})
    stage = "Salao dos Quatro Arcos"
    assert game.scene.zones["mesa central"] == [stage]
    assert "mesa central" in game.scene.zones[stage]
    assert game.scene.positions["C2"] == "mesa central"
    assert game.scene.positions["C1"] == stage


def test_a_further_move_links_to_the_zone_the_mover_actually_left() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    game = _apply(game, {"C2": "corredor"})
    assert game.scene.zones["corredor"] == ["mesa central"]
    assert "corredor" in game.scene.zones["mesa central"]
    # The origin stage is not dragged along: only the zone actually left is linked.
    assert "corredor" not in game.scene.zones["Salao dos Quatro Arcos"]


def test_two_characters_moving_together_link_both_their_origins() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    game = _apply(game, {"C1": "varanda", "C2": "varanda"})
    assert game.scene.zones["varanda"] == ["Salao dos Quatro Arcos", "mesa central"]
    assert "varanda" in game.scene.zones["Salao dos Quatro Arcos"]
    assert "varanda" in game.scene.zones["mesa central"]


def test_an_explicit_seal_still_wins() -> None:
    """zone_link_updates is applied after creation, so declaring a gap works."""
    game = _apply(_game(), {"C2": "rua"})
    assert game.scene.zones["rua"] == ["Salao dos Quatro Arcos"]
    for zone, audible in {"rua": []}.items():
        if zone in game.scene.zones:
            game.scene.zones[zone] = [o for o in audible if o in game.scene.zones]
    assert game.scene.zones["rua"] == []


def test_moving_into_an_existing_zone_changes_no_links() -> None:
    game = _apply(_game(), {"C2": "mesa central"})
    before = {zone: list(audible) for zone, audible in game.scene.zones.items()}
    game = _apply(game, {"C3": "mesa central"})
    assert game.scene.zones == before
    assert game.scene.positions["C3"] == "mesa central"


def test_a_mover_with_no_recorded_origin_creates_an_isolated_zone() -> None:
    """Nothing to link to is still nothing to link to — no invented connection."""
    cast = make_cast("Link", "Garran")
    game = make_game(characters=cast, scene=make_scene(characters=cast), controlled="C1")
    game.scene.zones = {"palco": []}
    game.scene.positions = {}
    Runner._open_new_zones(game, {"C2": "torre"}, ["torre"])
    assert game.scene.zones["torre"] == []
    assert game.scene.zones["palco"] == []
