"""Persistent application and per-provider LLM configuration."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.llm.adapters import get_provider_adapter, provider_adapters, provider_names
from src.paths import CONFIG_PATH

PROVIDER_NAMES = provider_names()
_config_lock = threading.RLock()

DEFAULT_CONFIG: dict[str, Any] = {
    "active_provider": "llama_cpp",
    "language": "Portuguese",
    "compaction_keep_recent_turns": 200,
    "automatic_compaction_enabled": False,
    "automatic_compaction_threshold_percent": 80,
    "providers": {
        name: deepcopy(adapter.config_defaults) for name, adapter in provider_adapters().items()
    },
}


class ConfigValidationError(ValueError):
    """Raised when persisted or submitted provider configuration is invalid."""


def _positive_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigValidationError(f"{label} must be a positive number")
    return float(value)


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigValidationError(f"{label} must be a positive integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigValidationError(f"{label} must be a boolean")
    return value


def _unit_interval(value: object, label: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0:
        return float(value)
    raise ConfigValidationError(f"{label} must be a number between 0 and 1")


def _percentage(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise ConfigValidationError(f"{label} must be an integer from 1 to 100")
    return value


def _required_string(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ConfigValidationError(f"{label} must be a string")
    return value.strip()


def validate_config(value: dict[str, Any]) -> dict[str, Any]:
    """Validate and return one canonical forward-only configuration object."""
    current_provider_names = provider_names()
    active_provider = value.get("active_provider")
    if active_provider not in current_provider_names:
        raise ConfigValidationError(f"active_provider must be one of {current_provider_names}")
    providers = value.get("providers")
    if not isinstance(providers, dict):
        raise ConfigValidationError("providers must be an object")

    canonical: dict[str, Any] = {
        "active_provider": active_provider,
        "language": _required_string(value.get("language", ""), "language", allow_empty=True),
        "compaction_keep_recent_turns": _positive_integer(
            value.get("compaction_keep_recent_turns"), "compaction_keep_recent_turns"
        ),
        "automatic_compaction_enabled": _boolean(
            value.get("automatic_compaction_enabled"), "automatic_compaction_enabled"
        ),
        "automatic_compaction_threshold_percent": _percentage(
            value.get("automatic_compaction_threshold_percent"),
            "automatic_compaction_threshold_percent",
        ),
        "auto_event_enabled": _boolean(
            value.get("auto_event_enabled", True), "auto_event_enabled"
        ),
        "auto_event_base_probability": _unit_interval(
            value.get("auto_event_base_probability", 0.05), "auto_event_base_probability"
        ),
        "auto_event_growth_per_quiet_turn": _unit_interval(
            value.get("auto_event_growth_per_quiet_turn", 0.12),
            "auto_event_growth_per_quiet_turn",
        ),
        "auto_event_max_probability": _unit_interval(
            value.get("auto_event_max_probability", 0.85), "auto_event_max_probability"
        ),
        "autonomous_burst_max_beats": _positive_integer(
            value.get("autonomous_burst_max_beats", 1), "autonomous_burst_max_beats"
        ),
        "roteiro_enabled": _boolean(
            value.get("roteiro_enabled", False), "roteiro_enabled"
        ),
        "providers": {},
    }
    for name in current_provider_names:
        adapter = get_provider_adapter(name)
        raw = providers.get(name, adapter.config_defaults)
        if not isinstance(raw, dict):
            raise ConfigValidationError(f"providers.{name} must be an object")
        provider = {
            "api_base": _required_string(raw.get("api_base"), f"providers.{name}.api_base"),
            "model": _required_string(
                raw.get("model", ""),
                f"providers.{name}.model",
                allow_empty=not adapter.model_required,
            ),
            "context_max": _positive_integer(
                raw.get("context_max"), f"providers.{name}.context_max"
            ),
            "max_tokens_narrator": _positive_integer(
                raw.get("max_tokens_narrator"), f"providers.{name}.max_tokens_narrator"
            ),
            "max_tokens_character": _positive_integer(
                raw.get("max_tokens_character"), f"providers.{name}.max_tokens_character"
            ),
            "summarizer_max_tokens": _positive_integer(
                raw.get("summarizer_max_tokens"), f"providers.{name}.summarizer_max_tokens"
            ),
            "llm_timeout_seconds": _positive_number(
                raw.get("llm_timeout_seconds"), f"providers.{name}.llm_timeout_seconds"
            ),
        }
        for key, expected in adapter.forced_settings.items():
            if raw.get(key) != expected:
                raise ConfigValidationError(
                    f"providers.{name}.{key} must remain {expected!r} for this integration"
                )
            provider[key] = expected
        for key in adapter.secret_fields:
            secret = raw.get(key, "")
            if not isinstance(secret, str):
                raise ConfigValidationError(f"providers.{name}.{key} must be a string")
            provider[key] = secret.strip()
        canonical["providers"][name] = provider
    active_adapter = get_provider_adapter(active_provider)
    if active_adapter.requires_secret_when_active and not all(
        canonical["providers"][active_provider].get(key) for key in active_adapter.secret_fields
    ):
        raise ConfigValidationError(
            f"{active_provider} requires its secret fields before it can be activated"
        )
    return canonical


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
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
        if temporary.exists():
            temporary.unlink()
        raise


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the canonical config, creating defaults when it does not exist."""
    with _config_lock:
        if not path.exists():
            config = deepcopy(DEFAULT_CONFIG)
            _atomic_write_json(path, config)
            return config
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ConfigValidationError(f"Cannot read {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigValidationError(f"Configuration in {path} must be an object")
        return validate_config(raw)


def save_config(value: dict[str, Any], path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Validate and atomically persist a complete configuration."""
    with _config_lock:
        canonical = validate_config(value)
        _atomic_write_json(path, canonical)
        return canonical


def merge_config_update(value: dict[str, Any], path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Persist a UI update while preserving an omitted/blank DeepSeek API key."""
    with _config_lock:
        current = load_config(path)
        submitted = deepcopy(value)
        providers = submitted.get("providers")
        if isinstance(providers, dict):
            for name, adapter in provider_adapters().items():
                provider = providers.get(name)
                if not isinstance(provider, dict):
                    continue
                for key in adapter.secret_fields:
                    secret = provider.get(key)
                    if not isinstance(secret, str) or not secret.strip():
                        provider[key] = current["providers"][name][key]
        return save_config(submitted, path)


def resolve_active_config(value: dict[str, Any]) -> dict[str, Any]:
    """Flatten the selected provider for the existing agent/Runner interface."""
    canonical = validate_config(value)
    provider_name = canonical["active_provider"]
    provider = canonical["providers"][provider_name]
    return {
        **provider,
        "provider": provider_name,
        "language": canonical["language"],
        "compaction_keep_recent_turns": canonical["compaction_keep_recent_turns"],
        "automatic_compaction_enabled": canonical["automatic_compaction_enabled"],
        "automatic_compaction_threshold_percent": canonical[
            "automatic_compaction_threshold_percent"
        ],
        "auto_event_enabled": canonical["auto_event_enabled"],
        "auto_event_base_probability": canonical["auto_event_base_probability"],
        "auto_event_growth_per_quiet_turn": canonical["auto_event_growth_per_quiet_turn"],
        "auto_event_max_probability": canonical["auto_event_max_probability"],
        "autonomous_burst_max_beats": canonical["autonomous_burst_max_beats"],
        "roteiro_enabled": canonical["roteiro_enabled"],
    }


def llm_request_options(config: dict[str, Any]) -> dict[str, Any]:
    """Return the provider transport options shared by every agent call."""
    return {
        "provider": config.get("provider", "llama_cpp"),
        "api_base": config.get("api_base", ""),
        "api_key": config.get("api_key", ""),
        "thinking_enabled": config.get("thinking_enabled", False),
    }


def public_config(value: dict[str, Any]) -> dict[str, Any]:
    """Return UI-safe settings without ever returning the DeepSeek API key."""
    canonical = validate_config(value)
    safe = deepcopy(canonical)
    for name, adapter in provider_adapters().items():
        for key in adapter.secret_fields:
            secret = safe["providers"][name].pop(key)
            safe["providers"][name][f"{key}_configured"] = bool(secret)
    return safe
