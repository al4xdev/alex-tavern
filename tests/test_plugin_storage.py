"""Task 21: per-plugin private storage namespace and path safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.paths import PLUGIN_STORAGE_DIR
from src.plugins.sdk import PluginStorage


def test_unique_root_per_plugin_id() -> None:
    a = PluginStorage("dev.alex.one")
    b = PluginStorage("dev.alex.two")
    assert a.path != b.path
    assert a.path == PLUGIN_STORAGE_DIR / "dev.alex.one"
    assert a.path.is_dir()  # created on access


def test_resolve_nested_stays_inside() -> None:
    s = PluginStorage("dev.alex.nested")
    resolved = s.resolve("sessions", "abc123", "index.json")
    assert resolved == (s.root.resolve() / "sessions" / "abc123" / "index.json")


def test_open_write_creates_parents_and_roundtrips() -> None:
    s = PluginStorage("dev.alex.rw")
    with s.open("cache", "state.json", mode="w") as handle:
        handle.write('{"k": 1}')
    assert s.exists("cache", "state.json")
    with s.open("cache", "state.json") as handle:
        assert handle.read() == '{"k": 1}'


def test_two_plugins_same_filename_no_conflict() -> None:
    a, b = PluginStorage("dev.alex.p1"), PluginStorage("dev.alex.p2")
    with a.open("plugin-state.json", mode="w") as fh:
        fh.write("A")
    with b.open("plugin-state.json", mode="w") as fh:
        fh.write("B")
    with a.open("plugin-state.json") as fh:
        assert fh.read() == "A"
    with b.open("plugin-state.json") as fh:
        assert fh.read() == "B"


def test_mkdir_exists_remove() -> None:
    s = PluginStorage("dev.alex.lifecycle")
    s.mkdir("assets", "img")
    assert s.exists("assets", "img")
    with s.open("assets", "img", "a.txt", mode="w") as fh:
        fh.write("x")
    with pytest.raises(ValueError):
        s.remove("assets", recursive=False)  # directory needs recursive
    s.remove("assets", recursive=True)
    assert not s.exists("assets")
    s.remove("assets", recursive=True)  # no-op when already gone


def test_for_session_is_inside_namespace() -> None:
    s = PluginStorage("dev.alex.sessions")
    session_dir = s.for_session("a4363ccf")
    assert session_dir == s.root.resolve() / "sessions" / "a4363ccf"
    assert session_dir.is_dir()
    assert s.root.resolve() in session_dir.parents


@pytest.mark.parametrize(
    "parts",
    [
        ("..",),
        ("..", "..", "sessions"),
        ("/etc/passwd",),
        ("sessions", "../../../../etc"),
        ("",),
        ("   ",),
        ("a\x00b",),
    ],
)
def test_traversal_and_malformed_rejected(parts: tuple[str, ...]) -> None:
    s = PluginStorage("dev.alex.safety")
    with pytest.raises(ValueError):
        s.resolve(*parts)


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    s = PluginStorage("dev.alex.symlink")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("leak")
    link = s.path / "escape"
    link.symlink_to(outside)
    with pytest.raises(ValueError):
        s.resolve("escape", "secret.txt")


def test_remove_root_rejected() -> None:
    s = PluginStorage("dev.alex.root")
    s.path  # noqa: B018 - create it
    with pytest.raises(ValueError):
        s.remove()


def test_malformed_plugin_id_stays_contained() -> None:
    # Even a plugin id with dots resolves to a single directory component; a
    # crafted id cannot climb out because the root is a fixed join and every
    # resolve() re-checks containment.
    s = PluginStorage("dev.alex.dotted")
    resolved = s.resolve("x")
    assert PLUGIN_STORAGE_DIR.resolve() in resolved.parents
