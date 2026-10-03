"""Check that the 2×2 curl screen changes only its registered factors."""

import json

import t38_program_style_cross as screen


def _split_request(case: str, references: dict[str, str]) -> tuple[str, dict]:
    request = screen.request(case, references, {"model": "test-model"})
    user = request["messages"][1]["content"]
    reference, program_text = user.split("\n\nPROGRAMA AUTORITATIVO DESTE BEAT:\n")
    return reference, json.loads(program_text)


def test_crossed_factors_are_isolated_and_physically_distinct() -> None:
    references = {"38": "STYLE CLOSURE", "39": "STYLE STILLNESS"}
    s38_ref, s38_packet = _split_request("S38", references)
    s39_ref, s39_packet = _split_request("S39", references)
    l38_ref, l38_packet = _split_request("L38", references)
    l39_ref, l39_packet = _split_request("L39", references)

    assert s38_packet == s39_packet
    assert l38_packet == l39_packet
    assert s38_ref == l38_ref
    assert s39_ref == l39_ref
    assert s38_ref != s39_ref
    assert s38_packet["program"]["final"]["teo_zone"] == "hall"
    assert l38_packet["program"]["final"]["teo_zone"] == "tunnel"
    assert [event["op"] for event in l38_packet["program"]["ordered_events"]] == [
        "cross",
        "close_gate",
    ]


def test_archived_references_are_pinned_and_distinct() -> None:
    references = screen.source_references()
    assert "As folhas do portão colidem" in references["38"]
    assert "O último baque" in references["39"]
    assert references["38"] != references["39"]
