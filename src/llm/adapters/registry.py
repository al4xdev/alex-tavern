"""Immutable registry for server-side provider adapters."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from src.llm.adapters.base import ProviderAdapter
from src.llm.adapters.deepseek import DeepSeekAdapter
from src.llm.adapters.llama_cpp import LlamaCppAdapter

_ADAPTERS: Mapping[str, ProviderAdapter] = MappingProxyType(
    {
        LlamaCppAdapter.name: LlamaCppAdapter(),
        DeepSeekAdapter.name: DeepSeekAdapter(),
    }
)


def provider_names() -> tuple[str, ...]:
    """Return registered provider identifiers for config/API validation."""
    return tuple(_ADAPTERS)


def provider_adapters() -> dict[str, ProviderAdapter]:
    """Return a shallow registry copy for generic config discovery."""
    return dict(_ADAPTERS)


def get_provider_adapter(name: str) -> ProviderAdapter:
    """Resolve a configured provider or fail before any network request."""
    try:
        return _ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown LLM provider: {name}") from exc
