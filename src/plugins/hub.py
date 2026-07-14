"""Automatic, validated synchronization with the curated plugin hub."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
import time
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

from src.paths import EXPERIENCES_DIR, PLUGIN_HUB_DIR, PLUGINS_DIR
from src.plugins.experiences import parse_experience, save_experience
from src.plugins.store import PluginInstallError, curated_catalog, inspect_zip

DEFAULT_REPOSITORY = "https://github.com/al4xdev/alex-tavern-plugins.git"
DEFAULT_BRANCH = "master"
DEFAULT_MAX_AGE_SECONDS = 300.0
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_BYTES = 200 * 1024 * 1024

_GITHUB_HTTPS = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")
_GITHUB_SSH = re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$")
_sync_lock = threading.RLock()


class HubSyncError(RuntimeError):
    """The remote hub could not produce a valid local snapshot."""


def repository_archive_url(repository: str, branch: str = DEFAULT_BRANCH) -> str:
    """Resolve a supported GitHub repository URL to its branch archive."""
    if repository.endswith(".zip"):
        return repository
    match = _GITHUB_HTTPS.fullmatch(repository) or _GITHUB_SSH.fullmatch(repository)
    if match is None:
        raise HubSyncError("Curated hub must be a GitHub repository URL or ZIP archive URL")
    owner, name = match.groups()
    return f"https://github.com/{owner}/{name}/archive/refs/heads/{branch}.zip"


@contextmanager
def _locked_hub() -> Iterator[None]:
    """Serialize threads and independent CLI/server processes touching the hub."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = PLUGINS_DIR / ".hub-sync.lock"
    with _sync_lock, lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _download_archive(url: str, destination: Path) -> None:
    size = 0
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=30.0) as response:
            response.raise_for_status()
            with destination.open("wb") as handle:
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_ARCHIVE_BYTES:
                        raise HubSyncError("Curated hub archive exceeds 100 MiB")
                    handle.write(chunk)
    except httpx.HTTPError as error:
        raise HubSyncError(f"Cannot download curated hub: {error}") from error


def _safe_archive_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    extracted_size = 0
    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise HubSyncError(f"Unsafe curated hub archive member: {member.filename}")
        mode = member.external_attr >> 16
        if mode & 0o170000 == 0o120000:
            raise HubSyncError(f"Curated hub symbolic links are not allowed: {member.filename}")
        extracted_size += member.file_size
        if extracted_size > MAX_EXTRACTED_BYTES:
            raise HubSyncError("Curated hub expands beyond 200 MiB")
    return members


def _snapshot_root(extracted: Path) -> Path:
    if (extracted / "catalog.json").is_file():
        return extracted
    roots = [path for path in extracted.iterdir() if path.is_dir()]
    if len(roots) == 1 and (roots[0] / "catalog.json").is_file():
        return roots[0]
    raise HubSyncError("Curated hub archive must contain one catalog.json at its root")


def _inside(root: Path, relative: object, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise HubSyncError(f"{label} must be a non-empty relative path")
    root = root.resolve()
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise HubSyncError(f"Invalid {label}: {relative}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_snapshot(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise HubSyncError(f"Cannot read curated catalog: {error}") from error
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise HubSyncError("Curated catalog must use schema_version 1")
    plugins = catalog.get("plugins")
    experiences = catalog.get("experiences")
    if not isinstance(plugins, list) or not isinstance(experiences, list):
        raise HubSyncError("Curated catalog plugins and experiences must be arrays")

    seen_releases: set[tuple[str, str]] = set()
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            raise HubSyncError(f"plugins[{index}] must be an object")
        artifact = _inside(root, plugin.get("artifact"), f"plugins[{index}].artifact")
        expected_hash = plugin.get("sha256")
        if not isinstance(expected_hash, str) or _sha256(artifact) != expected_hash:
            raise HubSyncError(f"plugins[{index}] artifact SHA-256 does not match the catalog")
        plugin_id = plugin.get("id")
        version = plugin.get("version")
        if not isinstance(plugin_id, str) or not isinstance(version, str):
            raise HubSyncError(f"plugins[{index}] id and version must be strings")
        release = (plugin_id, version)
        if release in seen_releases:
            raise HubSyncError(f"Duplicate curated release: {plugin_id}@{version}")
        seen_releases.add(release)
        try:
            inspected = inspect_zip(artifact)
        except PluginInstallError as error:
            raise HubSyncError(f"plugins[{index}] artifact is invalid: {error}") from error
        manifest = inspected["manifest"]
        if manifest["plugin_id"] != plugin_id or manifest["version"] != version:
            raise HubSyncError(
                f"plugins[{index}] artifact manifest does not match {plugin_id}@{version}"
            )

    prepared_experiences: list[dict[str, Any]] = []
    for index, entry in enumerate(experiences):
        if not isinstance(entry, dict):
            raise HubSyncError(f"experiences[{index}] must be an object")
        manifest = _inside(root, entry.get("manifest"), f"experiences[{index}].manifest")
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            message = f"Cannot read Experience manifest {manifest.name}: {error}"
            raise HubSyncError(message) from error
        if not isinstance(value, dict):
            raise HubSyncError(f"Experience manifest {manifest.name} must contain an object")
        image = entry.get("image")
        image_path = _inside(root, image, f"experiences[{index}].image") if image else None
        if image_path is not None:
            value["image"] = f"/experiences/assets/{image_path.name}"
            value["_source_image"] = str(image_path)
        try:
            parse_experience({key: item for key, item in value.items() if key != "_source_image"})
        except ValueError as error:
            raise HubSyncError(f"Invalid Experience manifest {manifest.name}: {error}") from error
        prepared_experiences.append(value)
    return catalog, prepared_experiences


def _atomic_bytes(value: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(value)
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_copy(source: Path, destination: Path) -> None:
    _atomic_bytes(source.read_bytes(), destination)


def _experience_targets(prepared_experiences: list[dict[str, Any]]) -> list[Path]:
    targets: list[Path] = []
    for prepared in prepared_experiences:
        experience_id = prepared.get("id")
        if isinstance(experience_id, str):
            targets.append(EXPERIENCES_DIR / f"{experience_id}.json")
        source_image = prepared.get("_source_image")
        if isinstance(source_image, str):
            targets.append(EXPERIENCES_DIR / "assets" / Path(source_image).name)
    return targets


def _restore_files(backups: dict[Path, bytes | None]) -> None:
    for path, content in backups.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            _atomic_bytes(content, path)


def _publish_snapshot(root: Path, prepared_experiences: list[dict[str, Any]]) -> list[str]:
    staged = PLUGIN_HUB_DIR.with_name(f".{PLUGIN_HUB_DIR.name}.staged")
    previous = PLUGIN_HUB_DIR.with_name(f".{PLUGIN_HUB_DIR.name}.previous")
    failed = PLUGIN_HUB_DIR.with_name(f".{PLUGIN_HUB_DIR.name}.failed")
    for path in (staged, previous, failed):
        if path.exists():
            shutil.rmtree(path)
    shutil.copytree(root, staged)
    try:
        if PLUGIN_HUB_DIR.exists():
            PLUGIN_HUB_DIR.replace(previous)
        staged.replace(PLUGIN_HUB_DIR)
    except BaseException:
        if previous.exists() and not PLUGIN_HUB_DIR.exists():
            previous.replace(PLUGIN_HUB_DIR)
        raise

    targets = _experience_targets(prepared_experiences)
    backups = {path: path.read_bytes() if path.is_file() else None for path in targets}
    installed: list[str] = []
    try:
        for prepared in prepared_experiences:
            value = dict(prepared)
            source_image = value.pop("_source_image", None)
            if isinstance(source_image, str):
                destination = EXPERIENCES_DIR / "assets" / Path(source_image).name
                _atomic_copy(Path(source_image), destination)
            experience = save_experience(value)
            installed.append(experience.experience_id)
    except BaseException:
        try:
            _restore_files(backups)
        finally:
            PLUGIN_HUB_DIR.replace(failed)
            if previous.exists():
                previous.replace(PLUGIN_HUB_DIR)
            shutil.rmtree(failed)
        raise
    if previous.exists():
        shutil.rmtree(previous)
    os.utime(PLUGIN_HUB_DIR / "catalog.json")
    return installed


def _sync_hub_locked(repository: str, branch: str) -> dict[str, Any]:
    archive_url = repository_archive_url(repository, branch)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-hub-") as temporary_name:
        temporary = Path(temporary_name)
        archive_path = temporary / "hub.zip"
        extracted = temporary / "extracted"
        extracted.mkdir()
        _download_archive(archive_url, archive_path)
        try:
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(extracted, _safe_archive_members(archive))
        except (OSError, zipfile.BadZipFile) as error:
            raise HubSyncError(f"Cannot extract curated hub: {error}") from error
        root = _snapshot_root(extracted)
        catalog, prepared_experiences = _validated_snapshot(root)
        installed_experiences = _publish_snapshot(root, prepared_experiences)
    return {
        "repository": repository,
        "plugins": len(catalog["plugins"]),
        "experiences": installed_experiences,
        "status": "updated",
    }


def sync_hub(
    repository: str = DEFAULT_REPOSITORY,
    *,
    branch: str = DEFAULT_BRANCH,
) -> dict[str, Any]:
    """Force a fresh reviewed snapshot and atomically expose it to the runtime."""
    with _locked_hub():
        return _sync_hub_locked(repository, branch)


def _cached_summary(repository: str, status: str, error: str | None = None) -> dict[str, Any]:
    catalog = curated_catalog()
    result: dict[str, Any] = {
        "repository": repository,
        "plugins": len(catalog["plugins"]),
        "experiences": len(catalog["experiences"]),
        "status": status,
    }
    if error:
        result["error"] = error
    return result


def ensure_hub_synced(
    repository: str = DEFAULT_REPOSITORY,
    *,
    branch: str = DEFAULT_BRANCH,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    force: bool = False,
) -> dict[str, Any]:
    """Refresh an expired snapshot, falling back to the last valid cached copy."""
    with _locked_hub():
        catalog_path = PLUGIN_HUB_DIR / "catalog.json"
        if not force and catalog_path.is_file():
            age = max(0.0, time.time() - catalog_path.stat().st_mtime)
            if age < max_age_seconds:
                return _cached_summary(repository, "fresh")
        try:
            return _sync_hub_locked(repository, branch)
        except (HubSyncError, OSError, PluginInstallError, json.JSONDecodeError) as error:
            if catalog_path.is_file():
                return _cached_summary(repository, "stale", str(error))
            if isinstance(error, HubSyncError):
                raise
            raise HubSyncError(f"Cannot synchronize curated hub: {error}") from error
