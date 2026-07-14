"""In-process loader and crash fallback coordinator."""

from __future__ import annotations

import importlib.util
import sys
import traceback
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from src.paths import PLUGIN_ENV_DIR
from src.plugins.commands import CommandRegistry
from src.plugins.hooks import HookRegistry
from src.plugins.journal import emit
from src.plugins.manifest import PluginManifest, load_manifest, satisfies_version
from src.plugins.sdk import PluginConfig, PluginContext
from src.plugins.store import active_pointers

_SETTINGS_FIELD_TYPES = {"boolean"}


def _validated_settings_fields(plugin_id: str, descriptor: Any) -> list[dict[str, Any]]:
    """Enforces the ``settings`` contribution shape declared in ``contracts.SETTINGS``.

    A malformed descriptor fails the plugin's boot explicitly instead of producing
    a broken or silently-skipped config form.
    """
    if not isinstance(descriptor, dict) or not isinstance(descriptor.get("fields"), list):
        raise ValueError(f"{plugin_id}: settings contribution must be an object with 'fields'")
    fields: list[dict[str, Any]] = []
    for field in descriptor["fields"]:
        if not isinstance(field, dict):
            raise ValueError(f"{plugin_id}: settings field must be an object")
        missing = [key for key in ("key", "type", "label", "default") if key not in field]
        if missing:
            raise ValueError(f"{plugin_id}: settings field missing {missing}")
        if field["type"] not in _SETTINGS_FIELD_TYPES:
            raise ValueError(f"{plugin_id}: unsupported settings field type '{field['type']}'")
        if not isinstance(field["label"], dict) or not field["label"].get("en"):
            raise ValueError(f"{plugin_id}: settings field label needs at least an 'en' locale")
        fields.append(field)
    return fields


@dataclass(slots=True)
class LoadedPlugin:
    manifest: PluginManifest
    package_dir: Path
    module: ModuleType | None


class PluginRuntime:
    """Trusted plugin runtime. Isolation is crash containment, not a security boundary."""

    def __init__(self) -> None:
        self.hooks = HookRegistry(self._hook_failed)
        self.commands = CommandRegistry()
        self.loaded: dict[str, LoadedPlugin] = {}
        self.disabled_for_boot: dict[str, str] = {}
        self.host: Any = None

    def bind_host(self, host: Any) -> None:
        self.host = host

    def _hook_failed(self, plugin_id: str, hook: str, error: BaseException) -> None:
        self.disable_for_boot(plugin_id, f"{hook}: {error}")

    def disable_for_boot(self, plugin_id: str, reason: str) -> None:
        if plugin_id in self.disabled_for_boot:
            return
        self.disabled_for_boot[plugin_id] = reason
        self.hooks.remove_plugin(plugin_id)
        self.commands.remove_plugin(plugin_id)
        emit("crashed", plugin_id, reason=reason, traceback=traceback.format_exc())

    def boot(self) -> None:
        if PLUGIN_ENV_DIR.exists():
            environment = str(PLUGIN_ENV_DIR.resolve())
            if environment not in sys.path:
                sys.path.insert(0, environment)
        pointers = active_pointers()
        active_order = [str(pointer["plugin_id"]) for pointer in pointers]
        manifests: dict[str, tuple[PluginManifest, Path]] = {}
        for pointer in pointers:
            try:
                package = Path(pointer["path"]).resolve(strict=True)
                manifest = load_manifest(package)
                manifests[manifest.plugin_id] = (manifest, package)
            except BaseException as error:
                plugin_id = str(pointer.get("plugin_id", "unknown"))
                self.disable_for_boot(plugin_id, f"manifest: {error}")

        pending = set(manifests)
        while pending:
            progressed = False
            for plugin_id in sorted(pending):
                manifest, package = manifests[plugin_id]
                required = {item.plugin_id for item in manifest.dependencies if not item.optional}
                missing = required - manifests.keys()
                if missing:
                    self.disable_for_boot(
                        plugin_id, f"missing dependencies: {', '.join(sorted(missing))}"
                    )
                    pending.remove(plugin_id)
                    progressed = True
                    break
                incompatible = [
                    dependency.plugin_id
                    for dependency in manifest.dependencies
                    if not dependency.optional
                    and dependency.plugin_id in manifests
                    and not satisfies_version(
                        manifests[dependency.plugin_id][0].version, dependency.version
                    )
                ]
                if incompatible:
                    self.disable_for_boot(
                        plugin_id,
                        f"incompatible dependencies: {', '.join(sorted(incompatible))}",
                    )
                    pending.remove(plugin_id)
                    progressed = True
                    break
                if required & pending:
                    continue
                position = active_order.index(plugin_id)
                self._load(manifest, package, tuple(active_order[position + 1 :]))
                pending.remove(plugin_id)
                progressed = True
                break
            if not progressed:
                for plugin_id in sorted(pending):
                    self.disable_for_boot(plugin_id, "dependency cycle")
                break

    def _load(
        self, manifest: PluginManifest, package: Path, default_before: tuple[str, ...] = ()
    ) -> None:
        if manifest.plugin_id in self.disabled_for_boot:
            return
        module: ModuleType | None = None
        try:
            if manifest.entrypoints.backend:
                path = package / manifest.entrypoints.backend
                module_name = (
                    f"alex_tavern_plugin_{manifest.plugin_id.replace('.', '_').replace('-', '_')}"
                )
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    path,
                    submodule_search_locations=[str(package)],
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load backend entrypoint {path}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                setup = getattr(module, "setup", None)
                if not callable(setup):
                    raise TypeError("Backend entrypoint must export setup(context)")
                setup(PluginContext(manifest, self.hooks, self, default_before))
                self._materialize_settings_defaults(manifest.plugin_id)
            self.loaded[manifest.plugin_id] = LoadedPlugin(manifest, package, module)
            emit(
                "loaded",
                manifest.plugin_id,
                version=manifest.version,
                permissions=list(manifest.permissions),
            )
        except BaseException as error:
            self.disable_for_boot(manifest.plugin_id, f"load: {error}")

    def _materialize_settings_defaults(self, plugin_id: str) -> None:
        """Writes each declared field's default into config the first time it's missing.

        Runs once per boot, right after ``setup(context)`` registers the plugin's
        "settings" contribution — the generic config-UI contract (no per-plugin
        branch anywhere in core or the frontend).
        """
        descriptors = [
            item["value"]
            for item in self.hooks.contributions("settings")
            if item["plugin_id"] == plugin_id
        ]
        if not descriptors:
            return
        config = PluginConfig(plugin_id)
        current = config.read()
        changed = False
        for descriptor in descriptors:
            for field in _validated_settings_fields(plugin_id, descriptor):
                key = field["key"]
                if key not in current:
                    current[key] = field["default"]
                    changed = True
        if changed:
            config.write(current)

    def public_status(self) -> dict[str, Any]:
        return {
            "loaded": [
                {
                    **plugin.manifest.public_dict(),
                    "frontend_url": (
                        f"/plugins/assets/{plugin.manifest.plugin_id}/{plugin.manifest.entrypoints.frontend}"
                        if plugin.manifest.entrypoints.frontend
                        else None
                    ),
                }
                for plugin in self.loaded.values()
            ],
            "disabled_for_boot": deepcopy(self.disabled_for_boot),
            "contributions": {
                slot: self.hooks.contributions(slot)
                for slot in ("providers", "routes", "settings", "panels")
            },
            "commands": self.commands.public_catalog(),
        }

    def asset(self, plugin_id: str, relative_path: str) -> Path | None:
        loaded = self.loaded.get(plugin_id)
        if loaded is None:
            return None
        target = (loaded.package_dir / relative_path).resolve()
        if loaded.package_dir not in target.parents or not target.is_file():
            return None
        return target
