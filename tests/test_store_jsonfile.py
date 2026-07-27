"""The shared atomic-write contract every persisted store now depends on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.store import jsonfile
from src.store.locks import append_lock, named_lock, session_lock


def test_write_json_creates_parents_and_ends_with_newline(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deeper" / "value.json"

    jsonfile.write_json(target, {"acentuação": "preservada", "n": 1})

    raw = target.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert "acentuação" in raw  # ensure_ascii=False
    assert json.loads(raw) == {"acentuação": "preservada", "n": 1}


def test_failed_write_keeps_the_previous_content_and_leaves_no_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "value.json"
    jsonfile.write_json(target, {"revision": 1})

    def explode(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("serialization failed")

    monkeypatch.setattr(jsonfile.json, "dumps", explode)
    with pytest.raises(RuntimeError):
        jsonfile.write_json(target, {"revision": 2})

    assert json.loads(target.read_text(encoding="utf-8")) == {"revision": 1}
    assert [path.name for path in tmp_path.iterdir()] == ["value.json"]


def test_interrupted_publication_leaves_no_temporary_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "value.json"

    def refuse_replace(self: Path, _target: object) -> None:
        raise OSError("cross-device link")

    monkeypatch.setattr(Path, "replace", refuse_replace)
    with pytest.raises(OSError):
        jsonfile.write_json(target, {"revision": 1})

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_read_json_returns_none_for_a_missing_file(tmp_path: Path) -> None:
    assert jsonfile.read_json(tmp_path / "absent.json") is None


def test_read_json_propagates_a_corrupt_file(tmp_path: Path) -> None:
    target = tmp_path / "broken.json"
    target.write_text("{not json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        jsonfile.read_json(target)


def test_locks_are_identical_per_key_and_distinct_across_keys() -> None:
    assert session_lock("abc") is session_lock("abc")
    assert session_lock("abc") is not session_lock("def")
    assert append_lock("abc") is append_lock("abc")
    # Same key, different domain: a debug-log append never blocks a turn.
    assert session_lock("abc") is not append_lock("abc")  # type: ignore[comparison-overlap]


def test_named_locks_are_namespaced() -> None:
    assert named_lock("preset", "hero") is named_lock("preset", "hero")
    assert named_lock("preset", "hero") is not named_lock("scenario", "hero")
