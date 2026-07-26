"""Task 54 finding 3: a character may know an absent person, never address one.

The live session had Maelis asking "Geralt, do you have information you have not
shared?" — to someone who is not in the cast at all. Geralt has no ID and no
position; he exists in three characters' knowledge sheets as Asword's father,
a canonical figure of that world.

So the invariant is narrower than "do not mention him": knowing him is correct
characterization. What the prompt has to supply is the fact the code owns and
the text only implies — who is actually standing here.
"""

from __future__ import annotations

from src.agents.character import _build_present_roster
from src.models import CharacterPerspective, PersonView
from tests.factories import make_cast, make_scene


def test_the_roster_lists_everyone_present_except_the_viewer() -> None:
    cast = make_cast("Link", "Maelis", "Garran")
    roster = _build_present_roster(make_scene(characters=cast), cast, "C2", "C1")
    assert "Link" in roster
    assert "Garran" in roster
    assert "Maelis" not in roster, "a character is not company for itself"


def test_the_roster_says_the_list_is_closed() -> None:
    """Without this line the list is decoration; with it, it is a boundary."""
    cast = make_cast("Link", "Maelis")
    roster = _build_present_roster(make_scene(characters=cast), cast, "C2", "C1")
    assert "That list is complete" in roster
    # The distinction the measurement was about: about them, never to them.
    assert "ABOUT them" in roster
    assert "cannot speak TO them" in roster


def test_someone_absent_from_the_scene_is_absent_from_the_roster() -> None:
    cast = make_cast("Link", "Maelis", "Garran")
    scene = make_scene(characters=cast, present=["C1", "C2", "Player"])
    roster = _build_present_roster(scene, cast, "C2", "C1")
    assert "Link" in roster
    assert "Garran" not in roster


def test_names_travel_through_the_viewers_ledger() -> None:
    """A stranger stays a stranger: the roster must not leak canonical names."""
    cast = make_cast("Link", "Maelis", "Garran")
    perspective = CharacterPerspective(
        people={"C3": PersonView(known_name=None, reference="uma mulher de capuz", source_turn=1)},
        initialized_turn=1,
        processed_through_turn=1,
    )
    roster = _build_present_roster(
        make_scene(characters=cast), cast, "C2", "C1", viewer_perspective=perspective
    )
    assert "uma mulher de capuz" in roster
    assert "Garran" not in roster


def test_an_empty_scene_says_so_instead_of_listing_nothing() -> None:
    cast = make_cast("Link")
    scene = make_scene(characters=cast, present=["C1", "Player"])
    assert "alone in this place" in _build_present_roster(scene, cast, "C1", "C1")


def test_no_scene_produces_no_block_at_all() -> None:
    cast = make_cast("Link", "Maelis")
    assert _build_present_roster(None, cast, "C2", "C1") == ""


def test_the_roster_reaches_the_prompt() -> None:
    from src.agents.character import _build_user_prompt

    prompt = _build_user_prompt(
        "contexto", "eventos", "calmo", present_roster="WHO IS HERE WITH YOU: Link."
    )
    assert "WHO IS HERE WITH YOU: Link." in prompt
    assert prompt.index("WHO IS HERE") < prompt.index("CURRENT PRIVATE STATE")
