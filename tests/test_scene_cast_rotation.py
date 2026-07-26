"""Task 54 finding 5: the metric that survived validation, and its guard.

Three candidates were built and checked against the real sessions on disk
before one was kept:

1. rolling lexical novelty - REJECTED. It scored a session that visibly
   advances (a glass shatters, stormtroopers walk in) at 0.504, tied with the
   audited stagnant one at 0.499, because both keep a consistent atmosphere
   vocabulary and atmosphere dominates the word count.
2. scene-fact churn - REJECTED, and backwards: the advancing session changed
   its persisted facts LESS often (0.30 of turns) than the stagnant one (0.44).
3. cast rotation - kept. Stagnant 0.133, advancing 0.293, in the right order,
   with the mechanism the audit itself describes: the same people restaging the
   same moment.

It is reported, never gated. Task 26 asks for event-level evidence before any
material-delta gate; this is the evidence being collected.
"""

from __future__ import annotations

import json

from tools.playtest_harness import _cast_rotation


def _director(speakers: list[str]) -> dict:
    return {"agent": "director", "response": json.dumps({"next_speakers": speakers})}


def test_the_same_two_actors_every_beat_score_zero() -> None:
    calls = [_director(["C2", "C3"]) for _ in range(5)]
    assert _cast_rotation(calls) == 0.0


def test_a_fully_rotating_cast_scores_one() -> None:
    calls = [_director(["C2"]), _director(["C3"]), _director(["C4"])]
    assert _cast_rotation(calls) == 1.0


def test_a_partial_rotation_lands_between() -> None:
    calls = [_director(["C2", "C3"]), _director(["C3", "C4"])]
    # C4 is new; C3 is not. Half of this beat's cast is fresh.
    assert _cast_rotation(calls) == 0.5


def test_a_solo_scene_reports_nothing_instead_of_a_perfect_zero() -> None:
    """A one-actor scene scores 0 for a reason unrelated to stagnation."""
    calls = [_director(["C2"]) for _ in range(6)]
    assert _cast_rotation(calls) is None


def test_narrator_only_beats_do_not_count_as_a_cast() -> None:
    calls = [_director(["Narrator"]), _director(["C2"]), _director(["C3"])]
    assert _cast_rotation(calls) == 1.0


def test_too_little_evidence_reports_nothing() -> None:
    assert _cast_rotation([]) is None
    assert _cast_rotation([_director(["C2", "C3"])]) is None


def test_unparsable_and_foreign_records_are_skipped_not_counted() -> None:
    calls = [
        {"agent": "prose", "response": json.dumps({"next_speakers": ["C9"]})},
        _director(["C2"]),
        {"agent": "director", "response": "not json"},
        _director(["C3"]),
    ]
    assert _cast_rotation(calls) == 1.0


def test_a_dict_response_works_as_well_as_a_json_string() -> None:
    calls = [
        {"agent": "director", "response": {"next_speakers": ["C2"]}},
        {"agent": "director", "response": {"next_speakers": ["C3"]}},
    ]
    assert _cast_rotation(calls) == 1.0
