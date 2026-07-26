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

from copy import deepcopy
from typing import Any

from src.models import (
    Character,
    CharacterBody,
    CharacterMind,
    GameState,
    Player,
    Scene,
    TurnRecord,
    deepcopy_scene,
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


def make_record(
    turn: int,
    speaker: str,
    content: str,
    content_type: str = "speech",
    *,
    scene: Scene | None = None,
    **overrides: Any,
) -> TurnRecord:
    """One history entry. ``scene_snapshot`` is required by the model and is
    almost never what a test is about, so it defaults to a throwaway scene."""
    return TurnRecord(
        turn_number=turn,
        speaker=speaker,
        content=content,
        content_type=content_type,
        scene_snapshot=deepcopy_scene(scene if scene is not None else make_scene()),
        **overrides,
    )


# ── Director doubles ──────────────────────────────────────────────────────
#
# Nearly every runner test needed a fake Director, and each one hand-wrote the
# same five-key dict. That made the Director's response contract a thing you
# had to remember in eighteen files: adding a required field meant finding
# every literal, and a test that forgot one failed for the wrong reason.
#
# `director_beat` writes that contract once. What stays per-test is what the
# test is actually about - who speaks, what was perceived, what changed.

DIRECTOR_CONTRACT_DEFAULTS: dict[str, Any] = {
    "narration": "A cena segue.",
    "next_speakers": [],
    "perception_events": [],
    "scene_update": None,
    "mood_updates": None,
    "zone_moves": None,
    "zone_link_updates": None,
    "scene_blocking": {
        "character_zones": {},
        "action_location": "",
        "spatial_constraints": [],
        "destination_reachable_this_beat": True,
    },
    "time_skip_ticks": 0,
    "time_skip_summary": "",
    "return_control": False,
}


def director_beat(**overrides: Any) -> dict[str, Any]:
    """One Director response with every contract field present.

    ``director_beat(next_speakers=["C2"])`` is the whole contract with the one
    field this test cares about replaced.
    """
    unknown = set(overrides) - set(DIRECTOR_CONTRACT_DEFAULTS)
    if unknown:
        raise AssertionError(
            f"not part of the Director contract: {sorted(unknown)}. "
            "Add it to DIRECTOR_CONTRACT_DEFAULTS if the schema really grew."
        )
    # deepcopy, not a merge: the defaults hold lists and dicts, and a test that
    # appends to one would silently seed every later beat in the same run.
    return {**deepcopy(DIRECTOR_CONTRACT_DEFAULTS), **overrides}


class FakeDirector:
    """A Director that answers from a queue and records what it was asked.

    ``FakeDirector(director_beat(next_speakers=["C2"]), director_beat())`` answers
    those beats in order and then repeats the last one, which is what a burst
    test wants: program the interesting beats, let the rest settle.
    """

    def __init__(self, *beats: dict[str, Any]) -> None:
        self.beats = list(beats) or [director_beat()]
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self.beats) - 1)
        return self.beats[index]

    @property
    def call_count(self) -> int:
        return len(self.calls)
