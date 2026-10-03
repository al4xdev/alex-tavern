"""Boundary tests for the frozen, non-runtime feasibility artifact."""

from pathlib import Path

import pytest

import semantic_program_feasibility as pilot


def test_archived_character_speech_is_first_authored_record() -> None:
    t8_speakers, t8_words = pilot.source_packet("T8")
    assert t8_speakers == ["C17", "C18", "C2"]
    assert t8_words["C17"].startswith("Garran, segure a entrada")
    assert not t8_words["C17"].startswith("A Diretora Maelis grita")

    t23_speakers, t23_words = pilot.source_packet("T23")
    assert t23_speakers == ["C8", "C7", "C17"]
    assert t23_words["C8"].startswith("Noa, espelho bom")


def test_source_hash_mismatch_fails_before_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "plans/artifacts/probe"
    source.mkdir(parents=True)
    (source / "debug.jsonl").write_text("{}\n")
    (source / "state.json").write_text("{}\n")
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setitem(pilot.SOURCES, "probe", ("probe", 0, "0" * 64, "0" * 64))

    with pytest.raises(ValueError, match="source hash mismatch"):
        pilot.source_packet("probe")


def test_unregistered_event_cannot_be_rendered() -> None:
    with pytest.raises(ValueError, match="unregistered operation"):
        pilot.render(pilot.Event("unregistered", "noa"))
