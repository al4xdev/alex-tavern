"""Provider adapter registry, extensible during trusted plugin boot."""

from __future__ import annotations

import threading

from src.llm.adapters.base import ProviderAdapter
from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.adapters.llama_cpp import LlamaCppAdapter

_ADAPTERS: dict[str, ProviderAdapter] = {
    LlamaCppAdapter.name: LlamaCppAdapter(),
    DeepSeekAdapter.name: DeepSeekAdapter(),
}
_LOCK = threading.RLock()


def provider_names() -> tuple[str, ...]:
    """Return registered provider identifiers for config/API validation."""
    with _LOCK:
        return tuple(_ADAPTERS)


def provider_adapters() -> dict[str, ProviderAdapter]:
    """Return a shallow registry copy for generic config discovery."""
    with _LOCK:
        return dict(_ADAPTERS)


def get_provider_adapter(name: str) -> ProviderAdapter:
    """Resolve a configured provider or fail before any network request."""
    with _LOCK:
        try:
            return _ADAPTERS[name]
        except KeyError as exc:
            raise ValueError(f"Unknown LLM provider: {name}") from exc


def register_provider_adapter(adapter: ProviderAdapter) -> None:
    """Register or deliberately replace a provider from a trusted plugin."""
    if not isinstance(adapter.name, str) or not adapter.name:
        raise ValueError("Provider adapter name must be a non-empty string")
    with _LOCK:
        _ADAPTERS[adapter.name] = adapter
