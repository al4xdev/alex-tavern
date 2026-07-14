"""Public SDK passed to trusted backend plugin entrypoints."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from src.paths import PLUGIN_CONFIG_DIR
from src.plugins.hooks import Handler, HookKind, HookRegistry
from src.plugins.journal import emit
from src.plugins.manifest import PluginManifest

_config_lock = threading.RLock()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class PluginConfig:
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.path = PLUGIN_CONFIG_DIR / f"{plugin_id}.json"

    def read(self) -> dict[str, Any]:
        emit("permission_access", self.plugin_id, permission="config.read")
        with _config_lock:
            if not self.path.exists():
                return {}
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"Plugin config for {self.plugin_id} must be an object")
            return value

    def write(self, value: dict[str, Any]) -> None:
        emit("permission_access", self.plugin_id, permission="config.write")
        with _config_lock:
            _atomic_json(self.path, value)


class PluginHttp:
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        emit("permission_access", self.plugin_id, permission="network", method=method, url=url)
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, **kwargs)


@dataclass(slots=True)
class UnsafeAccess:
    """Explicit escape hatch: trusted plugins may reach and replace arbitrary objects."""

    plugin_id: str
    runtime: Any

    def get(self, name: str) -> Any:
        emit("permission_access", self.plugin_id, permission="unsafe", object=name)
        return getattr(self.runtime, name)

    def set(self, name: str, value: Any) -> None:
        emit("permission_access", self.plugin_id, permission="unsafe", object=name, mutation=True)
        setattr(self.runtime, name, value)


class PluginContext:
    """Stable SDK surface used from a plugin's ``setup(context)`` function."""

    def __init__(
        self,
        manifest: PluginManifest,
        hooks: HookRegistry,
        runtime: Any,
        default_before: tuple[str, ...] = (),
    ) -> None:
        self.manifest = manifest
        self.plugin_id = manifest.plugin_id
        self.config = PluginConfig(self.plugin_id)
        self.http = PluginHttp(self.plugin_id)
        self.unsafe = UnsafeAccess(self.plugin_id, runtime)
        self._hooks = hooks
        self._default_before = default_before

    def register(
        self,
        hook: str,
        kind: HookKind,
        handler: Handler,
        *,
        priority: int | None = None,
        before: tuple[str, ...] | None = None,
        after: tuple[str, ...] | None = None,
    ) -> None:
        self._hooks.register(
            self.plugin_id,
            hook,
            kind,
            handler,
            priority=self.manifest.priority if priority is None else priority,
            before=(self.manifest.before + self._default_before) if before is None else before,
            after=self.manifest.after if after is None else after,
        )

    def action(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "action", handler, **order)

    def filter(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "filter", handler, **order)

    def wrapper(self, hook: str, handler: Callable[..., Any], **order: Any) -> None:
        self.register(hook, "wrapper", handler, **order)

    def contribute(self, slot: str, value: Any) -> None:
        self._hooks.contribute(self.plugin_id, slot, value)

    def event(self, name: str, **details: Any) -> None:
        emit(name, self.plugin_id, **details)
