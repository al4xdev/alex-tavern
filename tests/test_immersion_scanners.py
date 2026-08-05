"""Seeded positives and negatives for the three immersion scanners.

Each scanner gates a wave-1 task at zero, so each one needs a case it MUST catch
and a case it must NOT flag — a scanner that only ever sees real archives cannot
tell "the defect is gone" from "the scanner broke".

The zone mirror gets its own cross-check against the shipped
``src.perception.can_perceive``, because the scanner reimplements that rule to
keep reading archived snapshots and a silent drift there would certify the exact
bug task 67 is about.
"""

from __future__ import annotations

import json

import pytest

from src.confidentiality import REDACTION_MARKER
from src.models import Scene
from src.perception import can_perceive as shipped_can_perceive
from src.perception import eligible_witnesses as shipped_eligible_witnesses
from tests.factories import make_character
from tools.acceptance.immersion_scanners import (
    can_perceive,
    eligible_witnesses,
    scan_director_speech,
    scan_empty_audience,
    scan_redaction,
)

HALL = "Salão"
SUBZONE = "Salão, junto aos escombros"
CORRIDOR = "corredor leste"


def _scene(positions: dict[str, str] | None = None, zones: dict | None = None) -> dict:
    return {
        "location": HALL,
        "time_of_day": "manhã",
        "present_characters": ["C1", "C2", "C3"],
        "physical_facts": {},
        "positions": positions or {},
        "zones": zones or {},
    }


def _record(
    turn: int,
    speaker: str,
    content: str,
    content_type: str = "speech",
    audience: list[str] | None = None,
    scene: dict | None = None,
) -> dict:
    return {
        "turn_number": turn,
        "speaker": speaker,
        "content": content,
        "content_type": content_type,
        "audience": audience,
        "audience_origin": "zone",
        "scene_snapshot": scene or _scene(),
    }


def _state(history: list[dict], **extra) -> dict:
    return {
        "session_id": "seed",
        "characters": {
            "C1": {"body": {"name": "Link"}, "mind": {}},
            "C2": {"body": {"name": "Bruna"}, "mind": {}},
            "C3": {"body": {"name": "Garran"}, "mind": {}},
        },
        "player": {"controlled_character_id": "C1"},
        "scene": _scene(),
        "history": history,
        **extra,
    }


def _director_record(turn: int, events: list[dict]) -> dict:
    return {
        "agent": "director",
        "turn_number": turn,
        "provider": "seed",
        "response": json.dumps({"perception_events": events}, ensure_ascii=False),
    }


def _character_record(turn: int, name: str) -> dict:
    return {"agent": f"character:{name}", "turn_number": turn, "provider": "seed", "response": "{}"}


# ---------------------------------------------------------------------------
# Scanner 1 — redaction
# ---------------------------------------------------------------------------


def test_redaction_marker_is_counted_per_channel():
    state = _state(
        [
            _record(1, "C2", f"As portas {REDACTION_MARKER} abertas."),
            _record(1, "Narrator", f"A sala segue {REDACTION_MARKER}.", content_type="narration"),
            _record(2, "C3", f"empurrar a {REDACTION_MARKER} para o lado", content_type="action"),
        ],
        character_perspectives={
            "C2": {
                "recent_memory": [f"T1 Bruna disse: as portas {REDACTION_MARKER} abertas"],
                "memory_summary": "",
                "people": {"C3": {"known_name": "Garran", "reference": "o instrutor"}},
            }
        },
    )

    result = scan_redaction(state)

    assert result["occurrences"] == 4
    assert result["persisted_speech_records"] == 2, "speech and action are both durable records"
    assert result["ledger_entries"] == 1
    assert result["ledger_viewers"] == 1
    assert set(result["by_channel"]) == {
        "speech",
        "narration",
        "action",
        "ledger_recent_memory",
    }


def test_a_clean_session_scores_zero():
    state = _state(
        [_record(1, "C2", "As portas estão abertas.")],
        character_perspectives={
            "C2": {
                "recent_memory": ["T1 Bruna disse: as portas estão abertas"],
                "memory_summary": "Nada de estranho até aqui.",
                "people": {"C3": {"known_name": "Garran", "reference": "o instrutor"}},
            }
        },
    )

    result = scan_redaction(state)

    assert result["occurrences"] == 0
    assert result["records_with_marker"] == 0
    assert result["by_channel"] == {}


# ---------------------------------------------------------------------------
# Scanner 2 — speech the Director wrote
# ---------------------------------------------------------------------------


def test_director_authored_speech_is_matched_back_to_its_event():
    line = "Bruna grita para o salão: 'A fonte está sob os escombros, recuem!'"
    state = _state(
        [
            _record(4, "C2", "Recuem, todos!"),
            _record(4, "C2", line),
        ]
    )
    records = [
        _character_record(4, "Bruna"),
        _director_record(
            4,
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C2",
                    "content": line,
                    "witness_ids": ["C1", "C3"],
                }
            ],
        ),
    ]

    result = scan_director_speech(state, records)

    assert result["director_authored"] == 1
    assert result["routed_same_turn"] == 1, "Bruna had an agent call of her own that turn"
    assert result["evidence"][0]["character_id"] == "C2"
    assert result["evidence"][0]["turn"] == 4


def test_redaction_does_not_hide_a_director_authored_line():
    """The persisted text is the REDACTED event text, so matching must survive it."""
    spoken = "Garran grita: 'Sustentem o ritmo, eu seguro a retaguarda com a bengala!'"
    persisted = spoken.replace("bengala", REDACTION_MARKER)
    state = _state([_record(7, "C3", persisted)])
    records = [
        _director_record(
            7,
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C3",
                    "content": spoken,
                    "witness_ids": ["C1"],
                }
            ],
        )
    ]

    result = scan_director_speech(state, records)

    assert result["director_authored"] == 1
    assert result["carrying_redaction"] == 1


def test_a_characters_own_line_is_not_attributed_to_the_director():
    """A Director event about the same character, with different words, is not a match."""
    state = _state([_record(4, "C2", "Recuem, todos! A fonte está sob os escombros.")])
    records = [
        _character_record(4, "Bruna"),
        _director_record(
            4,
            [
                {
                    "event_kind": "observation",
                    "subject_id": "C2",
                    "content": "Bruna se afasta dos escombros com o braço erguido.",
                    "witness_ids": ["C1", "C3"],
                }
            ],
        ),
    ]

    result = scan_director_speech(state, records)

    assert result["director_authored"] == 0
    assert result["speech_records_excluding_player"] == 1


# ---------------------------------------------------------------------------
# Scanner 3 — an audience of nobody
# ---------------------------------------------------------------------------


def test_a_shout_cut_off_by_the_zone_graph_is_flagged():
    """C2 is minted into a sub-zone with no inbound edge; the hall cannot hear it."""
    scene = _scene(
        positions={"C1": HALL, "C2": SUBZONE, "C3": HALL},
        zones={HALL: [CORRIDOR], SUBZONE: [HALL], CORRIDOR: [HALL]},
    )
    state = _state(
        [
            _record(
                23, "C2", "Bruna grita que a fonte está sob os escombros!", audience=[], scene=scene
            )
        ]
    )
    records = [
        _director_record(
            23,
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C2",
                    "content": "Bruna grita que a fonte está sob os escombros!",
                    "witness_ids": ["C1", "C3"],
                }
            ],
        )
    ]

    result = scan_empty_audience(state, records)

    assert result["with_others_present"] == 1
    assert result["graph_isolated"] == 1
    assert result["evidence"][0]["proposed_witnesses"] == 2, "the Director listed two, not none"
    assert result["max_witnesses_clamped"] == 2


def test_speaking_alone_in_a_zone_nobody_shares_is_not_a_defect():
    """Legitimately empty: C2 is the only character present."""
    scene = _scene(positions={"C2": CORRIDOR}, zones={HALL: [], CORRIDOR: []})
    scene["present_characters"] = ["C2"]
    state = _state([_record(9, "C2", "Bruna murmura para si mesma.", audience=[], scene=scene)])

    result = scan_empty_audience(state, [])

    assert result["empty_audience_records"] == 1
    assert result["isolated"] == 1
    assert result["with_others_present"] == 0


def test_a_default_audience_is_not_an_empty_one():
    """``audience: null`` means everyone who can perceive it — never a hit."""
    state = _state([_record(9, "C2", "Bruna fala para a sala.", audience=None)])

    assert scan_empty_audience(state, [])["empty_audience_records"] == 0


def test_witnesses_narrowed_to_none_is_reported_apart_from_the_graph_bug():
    """The Director lists only the speaker as witness of their own shout."""
    scene = _scene(positions={"C1": HALL, "C2": HALL, "C3": HALL}, zones={HALL: []})
    line = "Marta grita do arsenal: 'Alguém venha aqui!'"
    state = _state([_record(18, "C2", line, audience=[], scene=scene)])
    records = [
        _director_record(
            18,
            [
                {
                    "event_kind": "audible_speech",
                    "subject_id": "C2",
                    "content": line,
                    "witness_ids": ["C2"],
                }
            ],
        )
    ]

    result = scan_empty_audience(state, records)

    assert result["narrowed_to_none"] == 1
    assert result["graph_isolated"] == 0


# ---------------------------------------------------------------------------
# The zone mirror must not drift from the shipped rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "positions,zones",
    [
        ({}, {}),
        ({"C1": HALL, "C2": HALL, "C3": HALL}, {HALL: []}),
        ({"C1": HALL, "C2": SUBZONE, "C3": HALL}, {HALL: [CORRIDOR], SUBZONE: [HALL]}),
        ({"C1": HALL, "C2": SUBZONE, "C3": HALL}, {HALL: [SUBZONE], SUBZONE: [HALL]}),
        ({"C1": CORRIDOR, "C2": HALL}, {HALL: [CORRIDOR], CORRIDOR: [HALL]}),
        ({"C1": CORRIDOR}, {HALL: [CORRIDOR], CORRIDOR: [HALL]}),  # C2 unplaced
    ],
)
def test_the_zone_mirror_agrees_with_the_shipped_rule(positions, zones):
    raw = _scene(positions=positions, zones=zones)
    scene = Scene(**raw)
    characters = {cid: make_character(cid) for cid in ("C1", "C2", "C3")}

    for subject in characters:
        assert eligible_witnesses(raw, characters, subject) == shipped_eligible_witnesses(
            scene, characters, subject
        )
        for witness in characters:
            assert can_perceive(raw, witness, subject) == shipped_can_perceive(
                scene, witness, subject
            )
