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
from src.plugins.manifest import (
    ManifestError,
    PluginManifest,
    SemanticVersion,
    compare_versions,
    load_manifest,
)
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


def inspect_zip(zip_path: Path) -> dict[str, Any]:
    """Read the authoritative manifest from a ZIP without installing it."""
    if not zip_path.is_file():
        raise PluginInstallError(f"ZIP not found: {zip_path}")
    archive_hash = _sha256(zip_path)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-plugin-inspect-") as temporary:
        extracted = Path(temporary) / "package"
        extracted.mkdir()
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extracted, _safe_members(archive))
            manifest = validate_package(_package_root(extracted))
        except (zipfile.BadZipFile, ManifestError, OSError) as error:
            raise PluginInstallError(str(error)) from error
    return {"manifest": manifest.public_dict(), "sha256": archive_hash}


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
    inspected = inspect_zip(artifact)
    manifest = inspected["manifest"]
    if manifest["plugin_id"] != plugin_id or manifest["version"] != selected.get("version"):
        raise PluginInstallError("Curated artifact manifest does not match its catalog release")
    return install_zip(artifact)


def installed_plugins() -> list[dict[str, Any]]:
    with _lock:
        result: list[dict[str, Any]] = []
        if not PLUGIN_CACHE_DIR.exists():
            return result
        pointers = {pointer.get("plugin_id"): pointer for pointer in active_pointers()}
        for manifest_path in PLUGIN_CACHE_DIR.glob("*/*/*/plugin.toml"):
            package = manifest_path.parent
            try:
                manifest = validate_package(package)
            except _MANIFEST_ERRORS:
                continue
            pointer = pointers.get(manifest.plugin_id)
            active = bool(
                pointer
                and pointer.get("version") == manifest.version
                and pointer.get("sha256") == package.name
            )
            result.append(
                {
                    "manifest": manifest.public_dict(),
                    "sha256": package.name,
                    "path": str(package),
                    "active": active,
                }
            )
        return sorted(
            result,
            key=lambda item: (
                item["manifest"]["plugin_id"],
                SemanticVersion.parse(item["manifest"]["version"]),
                item["sha256"],
            ),
        )


def _manifest_diff(current: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    current_permissions = set(current.get("permissions", []))
    candidate_permissions = set(candidate.get("permissions", []))
    current_dependencies = {
        item["plugin_id"]: {"version": item["version"], "optional": item["optional"]}
        for item in current.get("dependencies", [])
    }
    candidate_dependencies = {
        item["plugin_id"]: {"version": item["version"], "optional": item["optional"]}
        for item in candidate.get("dependencies", [])
    }
    changed_dependencies = [
        {
            "plugin_id": plugin_id,
            "from": current_dependencies[plugin_id],
            "to": candidate_dependencies[plugin_id],
        }
        for plugin_id in sorted(current_dependencies.keys() & candidate_dependencies.keys())
        if current_dependencies[plugin_id] != candidate_dependencies[plugin_id]
    ]
    return {
        "permissions": {
            "added": sorted(candidate_permissions - current_permissions),
            "removed": sorted(current_permissions - candidate_permissions),
        },
        "dependencies": {
            "added": [
                {"plugin_id": plugin_id, **candidate_dependencies[plugin_id]}
                for plugin_id in sorted(candidate_dependencies.keys() - current_dependencies.keys())
            ],
            "removed": [
                {"plugin_id": plugin_id, **current_dependencies[plugin_id]}
                for plugin_id in sorted(current_dependencies.keys() - candidate_dependencies.keys())
            ],
            "changed": changed_dependencies,
        },
        "entrypoints": {
            "from": current.get("entrypoints", {}),
            "to": candidate.get("entrypoints", {}),
            "changed": current.get("entrypoints", {}) != candidate.get("entrypoints", {}),
        },
        "python_dependencies": {
            "from": current.get("python_dependencies", []),
            "to": candidate.get("python_dependencies", []),
            "changed": current.get("python_dependencies", [])
            != candidate.get("python_dependencies", []),
        },
    }


def _catalog_releases() -> dict[str, list[dict[str, Any]]]:
    releases: dict[str, list[dict[str, Any]]] = {}
    for entry in curated_catalog()["plugins"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        artifact = (PLUGIN_HUB_DIR / str(entry.get("artifact", ""))).resolve()
        if PLUGIN_HUB_DIR.resolve() not in artifact.parents:
            raise PluginInstallError("Curated artifact path is invalid")
        inspected = inspect_zip(artifact)
        manifest = inspected["manifest"]
        if (
            manifest["plugin_id"] != entry["id"]
            or manifest["version"] != entry.get("version")
            or inspected["sha256"] != entry.get("sha256")
        ):
            raise PluginInstallError("Curated artifact manifest does not match its catalog release")
        releases.setdefault(entry["id"], []).append(
            {"manifest": manifest, "sha256": inspected["sha256"]}
        )
    return releases


def plugin_inventory() -> list[dict[str, Any]]:
    """Group immutable installations and the newest curated release by logical plugin id."""
    with _lock:
        cached_by_id: dict[str, list[dict[str, Any]]] = {}
        for installation in installed_plugins():
            cached_by_id.setdefault(installation["manifest"]["plugin_id"], []).append(installation)
        curated_by_id = _catalog_releases()
        result: list[dict[str, Any]] = []
        for plugin_id in sorted(cached_by_id.keys() | curated_by_id.keys()):
            cached = sorted(
                cached_by_id.get(plugin_id, []),
                key=lambda item: (
                    SemanticVersion.parse(item["manifest"]["version"]),
                    item["sha256"],
                ),
                reverse=True,
            )
            active = next((item for item in cached if item["active"]), None)
            reference = active or (cached[0] if cached else None)
            releases = curated_by_id.get(plugin_id, [])
            candidate = max(
                releases,
                key=lambda item: (
                    SemanticVersion.parse(item["manifest"]["version"]),
                    item["sha256"],
                ),
                default=None,
            )
            state = "not_installed"
            curated: dict[str, Any] | None = None
            if candidate is not None:
                exact_cached = any(
                    item["manifest"]["version"] == candidate["manifest"]["version"]
                    and item["sha256"] == candidate["sha256"]
                    for item in cached
                )
                if reference is not None:
                    relation = compare_versions(
                        candidate["manifest"]["version"], reference["manifest"]["version"]
                    )
                    if relation == 0 and candidate["sha256"] != reference["sha256"]:
                        state = "release_conflict"
                    elif relation > 0:
                        state = "update_available"
                    elif relation < 0:
                        state = "catalog_older"
                    elif active and exact_cached and active["sha256"] == candidate["sha256"]:
                        state = "current"
                    else:
                        state = "candidate_available"
                curated = {
                    **candidate,
                    "cached": exact_cached,
                    "diff": _manifest_diff(reference["manifest"], candidate["manifest"])
                    if reference
                    else None,
                }
            elif reference is not None:
                state = "current"
            identity = reference or candidate
            if identity is None:  # pragma: no cover - union keys guarantee one release
                continue
            result.append(
                {
                    "plugin_id": plugin_id,
                    "name": identity["manifest"]["name"],
                    "state": state,
                    "active": active,
                    "cached_versions": cached,
                    "curated": curated,
                }
            )
        return result


def activation_path(plugin_id: str) -> Path:
    return PLUGIN_STARTED_DIR / f"{plugin_id}.json"


def _select_installation(
    plugin_id: str,
    version: str | None = None,
    sha256: str | None = None,
) -> dict[str, Any]:
    matches = [
        item
        for item in installed_plugins()
        if item["manifest"]["plugin_id"] == plugin_id
        and (version is None or item["manifest"]["version"] == version)
        and (sha256 is None or item["sha256"] == sha256)
    ]
    if not matches:
        raise PluginInstallError(f"No installed package matches {plugin_id}")
    return max(
        matches,
        key=lambda item: (SemanticVersion.parse(item["manifest"]["version"]), item["sha256"]),
    )


def activate(
    plugin_id: str,
    version: str | None = None,
    sha256: str | None = None,
    order: int = 0,
) -> dict[str, Any]:
    """Write an activation pointer; callers changing runtime should use switch_activation."""
    with _lock:
        selected = _select_installation(plugin_id, version, sha256)
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


def switch_activation(
    plugin_id: str,
    version: str | None = None,
    sha256: str | None = None,
) -> dict[str, Any]:
    """Prepare the exact environment before atomically switching one active pointer."""
    with _lock:
        selected = _select_installation(plugin_id, version, sha256)
        previous = active_pointers()
        previous_pointer = next(
            (item for item in previous if item.get("plugin_id") == plugin_id), None
        )
        order = int(previous_pointer.get("order", 0)) if previous_pointer else 0
        pointer = {
            "plugin_id": plugin_id,
            "version": selected["manifest"]["version"],
            "sha256": selected["sha256"],
            "path": selected["path"],
            "order": order,
        }
        proposed = [item for item in previous if item.get("plugin_id") != plugin_id]
        proposed.append(pointer)
        proposed.sort(key=lambda item: (int(item.get("order", 0)), item["plugin_id"]))
        environment = rebuild_environment(proposed)
        try:
            PLUGIN_STARTED_DIR.mkdir(parents=True, exist_ok=True)
            _atomic_json(activation_path(plugin_id), pointer)
        except BaseException:
            rebuild_environment(previous)
            raise
        emit("activated", plugin_id, version=pointer["version"], sha256=pointer["sha256"])
        return {"activated": pointer, "environment": environment}


def update_curated(
    plugin_id: str,
    version: str,
    sha256: str,
) -> dict[str, Any]:
    """Install one exact reviewed release, then activate it transactionally."""
    with _lock:
        catalog_match = next(
            (
                item
                for item in curated_catalog()["plugins"]
                if item.get("id") == plugin_id
                and item.get("version") == version
                and item.get("sha256") == sha256
            ),
            None,
        )
        if catalog_match is None:
            raise PluginInstallError("Requested curated release is no longer in the synced catalog")
        plugin_cache = [
            item for item in installed_plugins() if item["manifest"]["plugin_id"] == plugin_id
        ]
        if not plugin_cache:
            raise PluginInstallError("Curated update requires an installed plugin")
        reference = next((item for item in plugin_cache if item["active"]), None) or max(
            plugin_cache,
            key=lambda item: SemanticVersion.parse(item["manifest"]["version"]),
        )
        relation = compare_versions(version, reference["manifest"]["version"])
        if relation < 0:
            raise PluginInstallError("Curated update cannot downgrade the active release")
        if relation == 0 and reference["sha256"] != sha256:
            raise PluginInstallError("Curated release conflicts with the installed version hash")
        cached = next(
            (
                item
                for item in plugin_cache
                if item["manifest"]["version"] == version and item["sha256"] == sha256
            ),
            None,
        )
        installed = cached or install_curated(plugin_id, version)
        if installed["sha256"] != sha256:
            raise PluginInstallError("Installed artifact does not match requested curated release")
        switched = switch_activation(plugin_id, version, sha256)
        return {"installed": None if cached else installed, **switched, "restart": True}


def deactivate(plugin_id: str) -> bool:
    with _lock:
        path = activation_path(plugin_id)
        if not path.exists():
            return False
        path.unlink()
        emit("deactivated", plugin_id)
        return True


def uninstall(plugin_id: str, version: str, sha256: str) -> dict[str, Any]:
    """Remove one immutable cache entry and its matching active pointer, if any."""
    with _lock:
        root = PLUGIN_CACHE_DIR.resolve()
        destination = (PLUGIN_CACHE_DIR / plugin_id / version / sha256).resolve()
        if root not in destination.parents or not destination.is_dir():
            raise PluginInstallError(f"Installed package not found: {plugin_id}@{version}#{sha256}")
        try:
            manifest = validate_package(destination)
        except _MANIFEST_ERRORS as error:
            raise PluginInstallError(f"Installed package is invalid: {error}") from error
        selection_matches = (
            manifest.plugin_id == plugin_id
            and manifest.version == version
            and destination.name == sha256
        )
        if not selection_matches:
            raise PluginInstallError("Installed package selection does not match its manifest")

        pointer = next(
            (item for item in active_pointers() if item.get("plugin_id") == plugin_id),
            None,
        )
        deactivated = bool(
            pointer and pointer.get("version") == version and pointer.get("sha256") == sha256
        )
        if deactivated:
            activation_path(plugin_id).unlink(missing_ok=True)
        shutil.rmtree(destination)
        for parent in (destination.parent, destination.parent.parent):
            try:
                parent.rmdir()
            except OSError:
                break
        emit("uninstalled", plugin_id, version=version, sha256=sha256, deactivated=deactivated)
        return {
            "plugin_id": plugin_id,
            "version": version,
            "sha256": sha256,
            "deactivated": deactivated,
        }


def active_pointers() -> list[dict[str, Any]]:
    with _lock:
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
        return sorted(
            result,
            key=lambda pointer: (int(pointer.get("order", 0)), pointer["plugin_id"]),
        )


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
