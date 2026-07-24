"""One-time runtime migrations that must complete before plugins boot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import CONFIG_SCHEMA_VERSION, config_schema_version, load_config
from src.paths import CONFIG_PATH
from src.plugins.experiences import activate_experience
from src.plugins.hub import ensure_hub_synced
from src.plugins.store import rebuild_environment

DEFAULT_EXPERIENCE_ID = "before_the_war"


def prepare_runtime_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Apply the mandatory default Experience before committing config v2.

    Missing config and the original unversioned/v1 config both take this path.
    If synchronization, installation, activation, or environment rebuilding
    fails, the config remains pre-v2 so the whole operation is retried on the
    next boot.
    """
    found_version = config_schema_version(path)
    if found_version != CONFIG_SCHEMA_VERSION:
        ensure_hub_synced(force=True)
        activate_experience(DEFAULT_EXPERIENCE_ID)
        rebuild_environment()
    return load_config(path)
