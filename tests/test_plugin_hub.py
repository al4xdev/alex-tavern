"""Automatic curated-hub synchronization and offline fallback."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import HTTPException

import src.plugins.experiences as experiences_module
import src.plugins.hub as hub
import src.plugins.store as store
from src import main


def _patch_data_paths(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    plugins = root / "plugins"
    experiences = root / "experiences"
    plugin_hub = plugins / "hub"
    monkeypatch.setattr(hub, "PLUGINS_DIR", plugins)
    monkeypatch.setattr(hub, "PLUGIN_HUB_DIR", plugin_hub)
    monkeypatch.setattr(hub, "EXPERIENCES_DIR", experiences)
    monkeypatch.setattr(store, "PLUGIN_HUB_DIR", plugin_hub)
    monkeypatch.setattr(experiences_module, "EXPERIENCES_DIR", experiences)


def _build_hub_archive(root: Path, *, valid_hash: bool = True) -> Path:
    source = root / "source" / "alex-tavern-plugins-master"
    artifact = source / "artifacts" / "sample.zip"
    artifact.parent.mkdir(parents=True)
    with zipfile.ZipFile(artifact, "w") as package:
        package.writestr("plugin.toml", 'schema_version = 1\nid = "dev.test.sample"\n')
    artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()

    experience = {
        "schema_version": 1,
        "id": "sample-experience",
        "name": "Sample Experience",
        "description": "A synchronized test Experience.",
        "image": "assets/sample.gif",
        "plugins": [],
    }
    manifest = source / "experiences" / "sample.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(experience), encoding="utf-8")
    image = source / "assets" / "sample.gif"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"GIF89a-test")

    catalog = {
        "schema_version": 1,
        "plugins": [
            {
                "id": "dev.test.sample",
                "name": "Sample",
                "version": "1.0.0",
                "description": "Test plugin",
                "license": "MIT",
                "artifact": "artifacts/sample.zip",
                "sha256": artifact_hash if valid_hash else "0" * 64,
            }
        ],
        "experiences": [{"manifest": "experiences/sample.json", "image": "assets/sample.gif"}],
    }
    (source / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")

    archive_path = root / ("valid.zip" if valid_hash else "invalid.zip")
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source.parent))
    return archive_path


def _use_archive(monkeypatch: pytest.MonkeyPatch, archive: Path) -> None:
    def copy_archive(url: str, destination: Path) -> None:  # noqa: ARG001
        shutil.copy2(archive, destination)

    monkeypatch.setattr(hub, "_download_archive", copy_archive)


def test_sync_round_trip_is_idempotent_and_materializes_experience(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_data_paths(monkeypatch, tmp_path / "data")
    archive = _build_hub_archive(tmp_path)
    _use_archive(monkeypatch, archive)

    first = hub.sync_hub("https://example.test/hub.zip")
    second = hub.sync_hub("https://example.test/hub.zip")

    assert first["plugins"] == second["plugins"] == 1
    assert store.curated_catalog()["plugins"][0]["id"] == "dev.test.sample"
    assert experiences_module.list_experiences() == [
        {
            "id": "sample-experience",
            "name": "Sample Experience",
            "description": "A synchronized test Experience.",
            "image": "/experiences/assets/sample.gif",
            "plugins": [],
        }
    ]
    assert (hub.EXPERIENCES_DIR / "assets" / "sample.gif").read_bytes() == b"GIF89a-test"


def test_invalid_update_keeps_previous_valid_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_data_paths(monkeypatch, tmp_path / "data")
    valid = _build_hub_archive(tmp_path / "first")
    invalid = _build_hub_archive(tmp_path / "second", valid_hash=False)
    _use_archive(monkeypatch, valid)
    hub.sync_hub("https://example.test/hub.zip")
    previous = store.curated_catalog()

    _use_archive(monkeypatch, invalid)
    with pytest.raises(hub.HubSyncError, match="SHA-256"):
        hub.sync_hub("https://example.test/hub.zip")

    assert store.curated_catalog() == previous


def test_refresh_uses_stale_cache_when_remote_is_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_data_paths(monkeypatch, tmp_path / "data")
    archive = _build_hub_archive(tmp_path)
    _use_archive(monkeypatch, archive)
    hub.sync_hub("https://example.test/hub.zip")

    def offline(url: str, destination: Path) -> None:  # noqa: ARG001
        raise hub.HubSyncError("offline")

    monkeypatch.setattr(hub, "_download_archive", offline)
    result = hub.ensure_hub_synced("https://example.test/hub.zip", force=True)

    assert result["status"] == "stale"
    assert result["plugins"] == 1
    assert result["error"] == "offline"


def test_first_sync_reports_offline_instead_of_claiming_empty_catalog(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_data_paths(monkeypatch, tmp_path / "data")

    def offline(url: str, destination: Path) -> None:  # noqa: ARG001
        raise hub.HubSyncError("offline")

    monkeypatch.setattr(hub, "_download_archive", offline)
    with pytest.raises(hub.HubSyncError, match="offline"):
        hub.ensure_hub_synced("https://example.test/hub.zip", force=True)


def test_concurrent_syncs_are_serialized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_data_paths(monkeypatch, tmp_path / "data")
    archive = _build_hub_archive(tmp_path)
    _use_archive(monkeypatch, archive)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: hub.sync_hub("https://example.test/hub.zip"), range(2)))

    assert [result["plugins"] for result in results] == [1, 1]
    assert store.curated_catalog()["plugins"][0]["id"] == "dev.test.sample"


def test_catalog_endpoint_synchronizes_before_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[bool] = []
    catalog = {"schema_version": 1, "plugins": [{"id": "synced"}], "experiences": []}

    monkeypatch.setattr(hub, "ensure_hub_synced", lambda *, force=False: calls.append(force))
    monkeypatch.setattr(store, "curated_catalog", lambda: catalog)

    assert main.get_plugin_catalog(refresh=True) == catalog
    assert calls == [True]


def test_catalog_endpoint_reports_first_sync_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*, force: bool = False) -> None:  # noqa: ARG001
        raise hub.HubSyncError("offline")

    monkeypatch.setattr(hub, "ensure_hub_synced", fail)
    with pytest.raises(HTTPException) as captured:
        main.get_plugin_catalog()

    assert captured.value.status_code == 503
    assert captured.value.detail == "offline"
