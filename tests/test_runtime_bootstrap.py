"""First-boot Experience installation and its retry contract."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src import runtime_bootstrap
from src.config import CONFIG_SCHEMA_VERSION, DEFAULT_CONFIG

APPLIED = [
    ("sync", {"force": True}),
    ("activate", "before_the_war"),
    ("rebuild", None),
]


@pytest.fixture(autouse=True)
def _isolated_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the boot marker inside the test's own directory."""
    marker = tmp_path / "plugins" / "bootstrap.json"
    monkeypatch.setattr(runtime_bootstrap, "bootstrap_marker_path", lambda: marker)


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


def test_fresh_boot_applies_the_default_experience_and_writes_the_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    operations = _record_boot_operations(monkeypatch)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == APPLIED
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION
    assert json.loads(path.read_text(encoding="utf-8")) == loaded
    marker = json.loads(runtime_bootstrap.bootstrap_marker_path().read_text(encoding="utf-8"))
    assert marker["experience_id"] == "before_the_war"


def test_second_boot_does_not_reapply_the_default_experience(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    _record_boot_operations(monkeypatch)
    runtime_bootstrap.prepare_runtime_config(path)

    operations = _record_boot_operations(monkeypatch)
    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert operations == []
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION


def test_existing_settings_survive_the_first_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A config written before the Experience landed is never rewritten."""
    path = tmp_path / "config.json"
    existing = deepcopy(DEFAULT_CONFIG)
    existing["language"] = "English"
    path.write_text(json.dumps(existing), encoding="utf-8")
    _record_boot_operations(monkeypatch)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert loaded["language"] == "English"


def test_a_failed_activation_still_boots_and_retries_later(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", lambda **kwargs: None)

    def fail_activation(experience_id: str) -> None:
        raise RuntimeError(f"cannot activate {experience_id}")

    monkeypatch.setattr(runtime_bootstrap, "activate_experience", fail_activation)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    # The server came up with a usable config...
    assert loaded["schema_version"] == CONFIG_SCHEMA_VERSION
    # ...and nothing claims the Experience was installed.
    assert not runtime_bootstrap.bootstrap_marker_path().exists()


def test_offline_hub_does_not_take_the_server_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A phone with no connectivity must still reach a usable config."""
    path = tmp_path / "config.json"

    def fail_sync(**kwargs: object) -> None:
        raise OSError("no route to host")

    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", fail_sync)

    loaded = runtime_bootstrap.prepare_runtime_config(path)

    assert loaded["active_provider"] == DEFAULT_CONFIG["active_provider"]
    assert not runtime_bootstrap.bootstrap_marker_path().exists()


def test_retry_after_a_failed_boot_completes_the_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Experience lands on the first boot where the hub answers."""
    path = tmp_path / "config.json"

    def fail_sync(**kwargs: object) -> None:
        raise OSError("no route to host")

    monkeypatch.setattr(runtime_bootstrap, "ensure_hub_synced", fail_sync)
    runtime_bootstrap.prepare_runtime_config(path)

    operations = _record_boot_operations(monkeypatch)
    runtime_bootstrap.prepare_runtime_config(path)

    assert operations == APPLIED
    assert runtime_bootstrap.bootstrap_marker_path().exists()
