"""Immutable plugin cache, ZIP installation, activation pointers, and uv environment."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import threading
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from src.paths import PLUGIN_CACHE_DIR, PLUGIN_ENV_DIR, PLUGIN_HUB_DIR, PLUGIN_STARTED_DIR
from src.plugins.journal import emit
from src.plugins.manifest import ManifestError, PluginManifest, load_manifest
from src.plugins.sdk import _atomic_json

_lock = threading.RLock()
_JSON_READ_ERRORS = (json.JSONDecodeError, OSError)


class PluginInstallError(ValueError):
    pass


_MANIFEST_ERRORS = (ManifestError, PluginInstallError)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise PluginInstallError(f"Unsafe ZIP member: {member.filename}")
        mode = member.external_attr >> 16
        if mode & 0o170000 == 0o120000:
            raise PluginInstallError(f"Symbolic links are not allowed: {member.filename}")
    return members


def _package_root(extracted: Path) -> Path:
    if (extracted / "plugin.toml").is_file():
        return extracted
    children = [path for path in extracted.iterdir() if path.name != "__MACOSX"]
    if len(children) == 1 and children[0].is_dir() and (children[0] / "plugin.toml").is_file():
        return children[0]
    raise PluginInstallError("ZIP must contain plugin.toml at its root or one top-level folder")


def validate_package(package_dir: Path) -> PluginManifest:
    manifest = load_manifest(package_dir)
    for entrypoint in (manifest.entrypoints.backend, manifest.entrypoints.frontend):
        if entrypoint and not (package_dir / entrypoint).is_file():
            raise PluginInstallError(f"Missing entrypoint: {entrypoint}")
    return manifest


def install_zip(zip_path: Path) -> dict[str, Any]:
    """Validate and cache an immutable package under id/version/archive hash."""
    if not zip_path.is_file():
        raise PluginInstallError(f"ZIP not found: {zip_path}")
    archive_hash = _sha256(zip_path)
    with _lock, tempfile.TemporaryDirectory(prefix="alex-tavern-plugin-") as temporary:
        extracted = Path(temporary) / "package"
        extracted.mkdir()
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extracted, _safe_members(archive))
            package = _package_root(extracted)
            manifest = validate_package(package)
        except (zipfile.BadZipFile, ManifestError, OSError) as error:
            raise PluginInstallError(str(error)) from error
        destination = PLUGIN_CACHE_DIR / manifest.plugin_id / manifest.version / archive_hash
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            staging = destination.parent / f".{archive_hash}.installing"
            if staging.exists():
                shutil.rmtree(staging)
            shutil.copytree(package, staging)
            staging.replace(destination)
        emit("installed", manifest.plugin_id, version=manifest.version, sha256=archive_hash)
        return {
            "manifest": manifest.public_dict(),
            "sha256": archive_hash,
            "path": str(destination),
        }


def curated_catalog() -> dict[str, Any]:
    path = PLUGIN_HUB_DIR / "catalog.json"
    if not path.exists():
        return {"schema_version": 1, "plugins": [], "experiences": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise PluginInstallError("Curated catalog is not version 1")
    if not isinstance(value.get("plugins"), list) or not isinstance(value.get("experiences"), list):
        raise PluginInstallError("Curated catalog arrays are invalid")
    return value


def install_curated(plugin_id: str, version: str | None = None) -> dict[str, Any]:
    catalog = curated_catalog()
    matches = [
        item
        for item in catalog["plugins"]
        if isinstance(item, dict)
        and item.get("id") == plugin_id
        and (version is None or item.get("version") == version)
    ]
    if not matches:
        raise PluginInstallError(f"Plugin {plugin_id} is not in the synced curated catalog")
    selected = matches[-1]
    artifact = (PLUGIN_HUB_DIR / str(selected.get("artifact", ""))).resolve()
    if PLUGIN_HUB_DIR.resolve() not in artifact.parents or not artifact.is_file():
        raise PluginInstallError("Curated artifact path is invalid")
    expected_hash = selected.get("sha256")
    actual_hash = _sha256(artifact)
    if expected_hash != actual_hash:
        raise PluginInstallError(
            f"Curated artifact hash mismatch: expected {expected_hash}, received {actual_hash}"
        )
    return install_zip(artifact)


def installed_plugins() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not PLUGIN_CACHE_DIR.exists():
        return result
    for manifest_path in PLUGIN_CACHE_DIR.glob("*/*/*/plugin.toml"):
        package = manifest_path.parent
        try:
            manifest = validate_package(package)
        except _MANIFEST_ERRORS:
            continue
        result.append(
            {
                "manifest": manifest.public_dict(),
                "sha256": package.name,
                "path": str(package),
                "active": activation_path(manifest.plugin_id).exists(),
            }
        )
    return sorted(
        result,
        key=lambda item: (item["manifest"]["plugin_id"], item["manifest"]["version"]),
    )


def activation_path(plugin_id: str) -> Path:
    return PLUGIN_STARTED_DIR / f"{plugin_id}.json"


def activate(
    plugin_id: str,
    version: str | None = None,
    sha256: str | None = None,
    order: int = 0,
) -> dict[str, Any]:
    with _lock:
        matches = [
            item
            for item in installed_plugins()
            if item["manifest"]["plugin_id"] == plugin_id
            and (version is None or item["manifest"]["version"] == version)
            and (sha256 is None or item["sha256"] == sha256)
        ]
        if not matches:
            raise PluginInstallError(f"No installed package matches {plugin_id}")
        selected = sorted(
            matches,
            key=lambda item: tuple(
                int(part) for part in item["manifest"]["version"].split("-")[0].split(".")
            ),
        )[-1]
        PLUGIN_STARTED_DIR.mkdir(parents=True, exist_ok=True)
        pointer = {
            "plugin_id": plugin_id,
            "version": selected["manifest"]["version"],
            "sha256": selected["sha256"],
            "path": selected["path"],
            "order": order,
        }
        _atomic_json(activation_path(plugin_id), pointer)
        emit("activated", plugin_id, version=pointer["version"], sha256=pointer["sha256"])
        return pointer


def deactivate(plugin_id: str) -> bool:
    with _lock:
        path = activation_path(plugin_id)
        if not path.exists():
            return False
        path.unlink()
        emit("deactivated", plugin_id)
        return True


def active_pointers() -> list[dict[str, Any]]:
    if not PLUGIN_STARTED_DIR.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(PLUGIN_STARTED_DIR.glob("*.json")):
        try:
            pointer = json.loads(path.read_text(encoding="utf-8"))
        except _JSON_READ_ERRORS:
            continue
        if isinstance(pointer, dict):
            result.append(pointer)
    return sorted(result, key=lambda pointer: (int(pointer.get("order", 0)), pointer["plugin_id"]))


def rebuild_environment(pointers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build one import target for the exact active plugin set using uv."""
    selected = pointers if pointers is not None else active_pointers()
    requirements: list[str] = []
    for pointer in selected:
        manifest = load_manifest(Path(pointer["path"]))
        requirements.extend(manifest.python_dependencies)
    fingerprint = hashlib.sha256("\n".join(sorted(requirements)).encode()).hexdigest()
    current = PLUGIN_ENV_DIR / "fingerprint"
    if current.exists() and current.read_text(encoding="utf-8") == fingerprint:
        return {"changed": False, "fingerprint": fingerprint, "requirements": requirements}
    PLUGIN_ENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="plugin-env-", dir=PLUGIN_ENV_DIR.parent))
    try:
        if requirements:
            subprocess.run(
                ["uv", "pip", "install", "--target", str(temporary), *requirements],
                check=True,
            )
        (temporary / "fingerprint").write_text(fingerprint, encoding="utf-8")
        old = PLUGIN_ENV_DIR.with_name(f".{PLUGIN_ENV_DIR.name}.old")
        if old.exists():
            shutil.rmtree(old)
        if PLUGIN_ENV_DIR.exists():
            PLUGIN_ENV_DIR.replace(old)
        temporary.replace(PLUGIN_ENV_DIR)
        if old.exists():
            shutil.rmtree(old)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"changed": True, "fingerprint": fingerprint, "requirements": requirements}
