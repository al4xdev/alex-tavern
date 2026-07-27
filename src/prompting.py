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

from src.models import GameState, TurnRecord

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


def recent_event_lines(game: GameState, *, limit: int = 12, max_chars: int = 160) -> list[str]:
    """The last events as ``"  Name: content"``, oldest first.

    Every speaker is rendered by NAME. There is no option to render them by id,
    and the ``resolve_names`` flag that used to select between the two is gone.

    Why it is gone rather than merely defaulted the other way. ``speaker_label``
    resolves the internal ``Player`` marker and nothing else, so labelling "by
    id" never labelled the whole cast by id — it labelled the human-controlled
    character by name and everyone else by id, in the same list:

        RECENT EVENTS (oldest to newest):
          Thorn: Who runs this inn?
          C2: Hm, that depends...

    The set of characters rendered by name was exactly
    ``{player.controlled_character_id}``. That is not a style difference; it is
    the protected identity written into the prompt as a formatting rule, and
    AGENTS.md section 3 keeps that fact in the Runner. A flag whose off position
    breaks an invariant is not a choice worth preserving.

    An A/B did run first (2026-07-27, n=80 per arm, real provider): the name arm
    also removed every raw id from the drive's output (5/80 -> 0/80, p = 0.03),
    while the grounding difference used to reject it was p = 0.43. Full account
    and the reasoning error it corrected: entry 18 of
    ``docs/cases/19-pre-1.0-measurement-log-2026-07-26.md``.
    """
    recent: list[TurnRecord] = [
        record for record in game.history[-limit:] if record.content_type in PROGRESS_RECORD_TYPES
    ]
    controlled = game.player.controlled_character_id

    def label(speaker: str) -> str:
        subject = controlled if speaker == "Player" else speaker
        character = game.characters.get(subject)
        return character.mind.name if character is not None else speaker

    return [f"  {label(record.speaker)}: {record.content[:max_chars]}" for record in recent]


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
