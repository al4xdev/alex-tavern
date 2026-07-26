"""Prompt context blocks shared by the Director-side small calls.

The drive scheduler, the watcher and the roteiro planner all describe "where we
are and what just happened" to a model. They had written that description three
times, byte for byte in two of them, and the third had reimplemented the
``Player`` marker translation by hand — the agency lock (AGENTS.md section 3)
stated twice, only one of them canonical.

What is NOT here, deliberately: the per-role history formatters of the Narrator,
Character, prose renderer, summarizer and perspective agents. Each filters by a
different visibility boundary, and that boundary is the product; merging them
would trade the clarity of five explicit rules for one parameterized one.
"""

from __future__ import annotations

from src.models import GameState, TurnRecord, speaker_label

# What counts as something happening: private thoughts are not scene progress.
PROGRESS_RECORD_TYPES = ("speech", "action", "narration")

RECENT_EVENTS_HEADER = "RECENT EVENTS (oldest to newest):"


def scene_header(game: GameState) -> list[str]:
    """Where the scene is and what is physically true about it."""
    return [
        f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
        f"PHYSICAL FACTS: {game.scene.physical_facts}",
    ]


def story_so_far(game: GameState, *, max_chars: int = 600) -> list[str]:
    """The compacted world summary, or nothing when there is none yet."""
    if not game.story_summary:
        return []
    return [f"STORY SO FAR: {game.story_summary[:max_chars]}"]


def recent_event_lines(
    game: GameState, *, limit: int = 12, max_chars: int = 160, resolve_names: bool = False
) -> list[str]:
    """The last events as ``"  Speaker: content"``, oldest first.

    The internal ``"Player"`` marker never reaches a prompt either way: that
    rule (AGENTS.md section 3) is implemented here and nowhere else.

    ``resolve_names`` is a REAL difference between the current callers, not a
    style choice, so it is explicit instead of accidental. The drive scheduler
    and the watcher label other characters by ID ("C2"); the roteiro planner
    labels them by name ("Marta"). Both prompts were validated as they are, and
    the curl-first rule (AGENTS.md section 6) says a prompt does not change
    without measured evidence — so unifying them is a prompt experiment, not a
    refactor.
    """
    recent: list[TurnRecord] = [
        record for record in game.history[-limit:] if record.content_type in PROGRESS_RECORD_TYPES
    ]
    controlled = game.player.controlled_character_id

    def label(speaker: str) -> str:
        canonical = controlled if speaker == "Player" else speaker
        if resolve_names and canonical in game.characters:
            return game.characters[canonical].mind.name
        return speaker_label(speaker, game.characters, controlled)

    return [
        f"  {label(record.speaker)}: {record.content[:max_chars]}" for record in recent
    ]


def stalled_scene_context(game: GameState) -> list[str]:
    """The shared context of the two "the story stopped moving" calls.

    Used by the drive scheduler (Task 33) and the watcher's causal intervention
    (Task 33b): both ask a model for ONE external event grown from a thread
    already in play, so both need exactly this view and nothing more.
    """
    return [
        *story_so_far(game),
        *scene_header(game),
        RECENT_EVENTS_HEADER,
        *recent_event_lines(game),
    ]
