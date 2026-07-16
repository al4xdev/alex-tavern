"""Perception: zone-aware witness computation and typed-event handling.

Task 29.2 increment 2. The Narrator proposes typed ``perception_events`` (what
just happened and who could perceive it); this module is the deterministic
authority that CLAMPS those proposals against the zone graph and presence — a
model cannot grant perception to someone the physics denies. Rendering for one
viewer then projects the event text through that viewer's identity ledger, so
unlearned names and internal IDs never reach a character prompt.
"""

from __future__ import annotations

from typing import Any

from src.agents.perspective import project_text_for_viewer
from src.models import Character, CharacterPerspective, Scene

EVENT_KINDS = (
    "observation",
    "audible_speech",
    "identity_claim",
    "physical_outcome",
    "scene_change",
)
MAX_EVENTS_PER_TURN = 6


def can_perceive(scene: Scene, witness_id: str, subject_id: str) -> bool:
    """Whether ``witness_id`` can perceive an event produced at ``subject_id``'s spot.

    Without a zone graph (or for unplaced participants) the scene is one shared
    space: everyone perceives everything, exactly the previous engine behavior.
    With zones, perception requires the same zone or a directed audibility edge
    from the witness's zone to the subject's zone.
    """
    if not scene.zones:
        return True
    witness_zone = scene.positions.get(witness_id)
    subject_zone = scene.positions.get(subject_id)
    if witness_zone is None or subject_zone is None:
        return True
    if witness_zone == subject_zone:
        return True
    return subject_zone in scene.zones.get(witness_zone, [])


def eligible_witnesses(scene: Scene, characters: dict[str, Character], subject_id: str) -> set[str]:
    """Present characters whose zone allows perceiving the subject (subject excluded)."""
    return {
        cid
        for cid in scene.present_characters
        if cid in characters and cid != subject_id and can_perceive(scene, cid, subject_id)
    }


def validate_perception_events(
    raw_events: Any,
    scene: Scene,
    characters: dict[str, Character],
) -> list[dict[str, Any]]:
    """Deterministic clamp over the Narrator's proposed events.

    Keeps only well-formed events; the witness list is intersected with the
    zone-eligible set — the model may narrow perception (someone distracted),
    never widen it beyond what the zone graph allows.
    """
    if not isinstance(raw_events, list):
        return []
    validated: list[dict[str, Any]] = []
    present = set(scene.present_characters)
    for item in raw_events:
        if not isinstance(item, dict):
            continue
        kind = item.get("event_kind")
        subject_id = item.get("subject_id")
        content = item.get("content")
        raw_witnesses = item.get("witness_ids")
        if kind not in EVENT_KINDS or not isinstance(content, str) or not content.strip():
            continue
        if not isinstance(subject_id, str) or subject_id not in (present | {"Narrator"}):
            continue
        if not isinstance(raw_witnesses, list):
            continue
        allowed = (
            eligible_witnesses(scene, characters, subject_id)
            if subject_id != "Narrator"
            else {cid for cid in present if cid in characters}
        )
        witnesses = [
            cid for cid in dict.fromkeys(raw_witnesses) if isinstance(cid, str) and cid in allowed
        ]
        validated.append(
            {
                "event_kind": kind,
                "subject_id": subject_id,
                "content": content.strip(),
                "witness_ids": witnesses,
            }
        )
        if len(validated) >= MAX_EVENTS_PER_TURN:
            break
    return validated


def render_events_for_viewer(
    events: list[dict[str, Any]],
    viewer_id: str,
    characters: dict[str, Character],
    perspective: CharacterPerspective | None,
) -> str:
    """Build one viewer's SCENE CONTEXT from the events they actually witness.

    Event text is projected through the viewer's identity ledger (unlearned
    canonical names become references; internal IDs never survive).
    """
    lines: list[str] = []
    for event in events:
        if viewer_id not in event["witness_ids"] and event["subject_id"] != viewer_id:
            continue
        lines.append(project_text_for_viewer(event["content"], characters, perspective))
    return "\n".join(lines)


def describe_zones_for_narrator(scene: Scene, characters: dict[str, Character]) -> list[str]:
    """CURRENT SCENE prompt lines describing the zone graph and who is where."""
    if not scene.zones:
        return []
    lines = ["Zones (audibility is one-way as listed; same zone always perceives):"]
    for zone, audible in scene.zones.items():
        occupants = [
            characters[cid].mind.name
            for cid, position in scene.positions.items()
            if position == zone and cid in characters
        ]
        hears = ", ".join(audible) if audible else "nothing outside itself"
        who = ", ".join(occupants) if occupants else "nobody"
        lines.append(f"  {zone}: hears {hears} | occupants: {who}")
    unplaced = [
        characters[cid].mind.name
        for cid in scene.present_characters
        if cid in characters and cid not in scene.positions
    ]
    if unplaced:
        lines.append(f"  unplaced (perceive everything): {', '.join(unplaced)}")
    return lines
