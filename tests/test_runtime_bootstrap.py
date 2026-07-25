"""Config v2 boot migration and mandatory default Experience tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src import runtime_bootstrap
from src.config import CONFIG_SCHEMA_VERSION, DEFAULT_CONFIG


def _record_boot_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, object]]:
    operations: list[tuple[str, object]] = []
    monkeypatch.setattr(
        runtime_bootstrap,
        "ensure_hub_synced",
        lambda **kwargs: operations.append(("sync", kwargs)),
    )
    monkeypatch.setattr(
        runtime_bootstrap,
        "activate_experience",
        lambda experience_id: operations.append(("activate", experience_id)),
    )
    monkeypatch.setattr(
        runtime_bootstrap,
        "rebuild_environment",
        lambda: operations.append(("rebuild", None)),
    )
    return operations


def test_fresh_boot_applies_default_experience_before_writing_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    operations = _record_boot_operations(monkeypatch)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == [
        ("sync", {"force": True}),
        ("activate", "before_the_war"),
        ("rebuild", None),
    ]
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION
    assert json.loads(path.read_text(encoding="utf-8")) == loaded


def test_v1_boot_applies_default_experience_and_preserves_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    legacy = deepcopy(DEFAULT_CONFIG)
    legacy.pop("schema_version")
    legacy["language"] = "English"
    path.write_text(json.dumps(legacy), encoding="utf-8")
    operations = _record_boot_operations(monkeypatch)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == [
        ("sync", {"force": True}),
        ("activate", "before_the_war"),
        ("rebuild", None),
    ]
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION
    assert loaded["language"] == "English"


def test_v2_boot_does_not_reapply_default_experience(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")
    operations = _record_boot_operations(monkeypatch)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == []
    assert loaded == DEFAULT_CONFIG


def test_failed_default_experience_keeps_config_at_v1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The server still boots, and the untouched v1 file makes it retry later."""
    path = tmp_path / "config.json"
    legacy = deepcopy(DEFAULT_CONFIG)
    legacy.pop("schema_version")
    legacy["language"] = "English"
    original = json.dumps(legacy)
    path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", lambda **kwargs: None)

    def fail_activation(experience_id: str) -> None:
        raise RuntimeError(f"cannot activate {experience_id}")

    monkeypatch.setattr(runtime_bootstrap, "activate_experience", fail_activation)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert loaded["language"] == "English"
    assert path.read_text(encoding="utf-8") == original


def test_offline_hub_failure_does_not_take_the_server_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A phone with no connectivity must still reach a usable config."""
    path = tmp_path / "config.json"

    def fail_sync(**kwargs: object) -> None:
        raise OSError("no route to host")

    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", fail_sync)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert loaded["active_provider"] == DEFAULT_CONFIG["active_provider"]
    # Nothing was committed, so the next boot takes the migration path again.
    assert not path.exists()


def test_retry_after_a_failed_boot_completes_the_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The v1 file left behind by a failed boot is migrated once the hub works."""
    path = tmp_path / "config.json"
    legacy = deepcopy(DEFAULT_CONFIG)
    legacy.pop("schema_version")
    path.write_text(json.dumps(legacy), encoding="utf-8")

    def fail_sync(**kwargs: object) -> None:
        raise OSError("no route to host")

    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", fail_sync)
    runtime_bootstrap.prepare_runtime_config(path)
    assert "schema_version" not in json.loads(path.read_text(encoding="utf-8"))

    operations = _record_boot_operations(monkeypatch)
    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == [
        ("sync", {"force": True}),
        ("activate", "before_the_war"),
        ("rebuild", None),
    ]
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == CONFIG_SCHEMA_VERSION
