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
from src.plugins.hooks import HookRegistry
from src.plugins.journal import emit
from src.plugins.manifest import PluginManifest, load_manifest, satisfies_version
from src.plugins.sdk import PluginContext
from src.plugins.store import active_pointers


@dataclass(slots=True)
class LoadedPlugin:
    manifest: PluginManifest
    package_dir: Path
    module: ModuleType | None


class PluginRuntime:
    """Trusted plugin runtime. Isolation is crash containment, not a security boundary."""

    def __init__(self) -> None:
        self.hooks = HookRegistry(self._hook_failed)
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
            self.loaded[manifest.plugin_id] = LoadedPlugin(manifest, package, module)
            emit(
                "loaded",
                manifest.plugin_id,
                version=manifest.version,
                permissions=list(manifest.permissions),
            )
        except BaseException as error:
            self.disable_for_boot(manifest.plugin_id, f"load: {error}")

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
                for slot in ("providers", "routes", "settings", "commands", "panels")
            },
        }

    def asset(self, plugin_id: str, relative_path: str) -> Path | None:
        loaded = self.loaded.get(plugin_id)
        if loaded is None:
            return None
        target = (loaded.package_dir / relative_path).resolve()
        if loaded.package_dir not in target.parents or not target.is_file():
            return None
        return target
