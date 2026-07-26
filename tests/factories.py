"""Builders for the domain objects almost every test needs.

Fifteen test modules had written the same five-line ``_char`` helper, so adding
a field to Character meant fifteen edits — the friction that makes a schema
change feel expensive and pushes people toward "purely additive" fields the
loader then has to read defensively (see AGENTS.md section 2).

What is NOT here: each module's own SCENE and cast. A test that happens in the
"Salao do Prisma" with three specific characters is describing its own
situation, and collapsing those into one shared fixture would hide what each
test is actually about.
"""

from __future__ import annotations

from typing import Any

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
)

# The historical placeholder values, kept verbatim so every migrated test keeps
# asserting against exactly what it asserted against before.
DEFAULT_PERSONALITY = "p"
DEFAULT_MOOD = "m"
DEFAULT_DESCRIPTION = "d"
DEFAULT_OUTFIT = "o"


def make_character(
    name: str,
    *,
    personality: str = DEFAULT_PERSONALITY,
    knowledge: list[str] | None = None,
    current_mood: str = DEFAULT_MOOD,
    physical_description: str = DEFAULT_DESCRIPTION,
    outfit: str = DEFAULT_OUTFIT,
) -> Character:
    """One character with placeholder sheets; override only what the test is about."""
    return Character(
        mind=CharacterMind(
            name=name,
            personality=personality,
            knowledge=list(knowledge or []),
            current_mood=current_mood,
        ),
        body=CharacterBody(
            name=name,
            physical_description=physical_description,
            outfit=outfit,
        ),
    )


def make_cast(*names: str) -> dict[str, Character]:
    """``make_cast("Rui", "Marta")`` -> ``{"C1": ..., "C2": ...}``."""
    return {f"C{index}": make_character(name) for index, name in enumerate(names, start=1)}


def make_scene(
    *,
    characters: dict[str, Character] | None = None,
    present: list[str] | None = None,
    location: str = "Estalagem",
    time_of_day: str = "Noite",
    **overrides: Any,
) -> Scene:
    """A scene where everyone is present unless the test says otherwise."""
    if present is None:
        present = [*(characters or {}), "Player"]
    return Scene(
        location=location,
        time_of_day=time_of_day,
        present_characters=list(present),
        physical_facts=overrides.pop("physical_facts", {}),
        **overrides,
    )


def make_game(
    *,
    session_id: str = "testsess",
    characters: dict[str, Character] | None = None,
    scene: Scene | None = None,
    controlled: str = "C1",
    **overrides: Any,
) -> GameState:
    """A committed-looking GameState for tests that need one without a Runner."""
    cast = characters if characters is not None else make_cast("Rui", "Marta")
    return GameState(
        session_id=session_id,
        characters=cast,
        player=Player(controlled_character_id=controlled),
        scene=scene if scene is not None else make_scene(characters=cast),
        **overrides,
    )
