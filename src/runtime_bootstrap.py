"""One-time runtime migrations that must complete before plugins boot."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import CONFIG_SCHEMA_VERSION, config_schema_version, load_config
from src.paths import CONFIG_PATH
from src.plugins.experiences import activate_experience
from src.plugins.hub import ensure_hub_synced
from src.plugins.store import rebuild_environment

DEFAULT_EXPERIENCE_ID = "before_the_war"

logger = logging.getLogger(__name__)


def prepare_runtime_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Apply the mandatory default Experience before committing config v2.

    Missing config and the original unversioned/v1 config both take this path.
    If synchronization, installation, activation, or environment rebuilding
    fails, the config remains pre-v2 so the whole operation is retried on the
    next boot.

    The failure is logged rather than raised, because this runs first in the
    application lifespan: raising takes the whole server down. The default
    Experience needs the plugin hub, so on a phone with no connectivity it is
    unreachable through no fault of the install — the app has to come up
    anyway, with the pre-v2 config it already has.
    """
    found_version = config_schema_version(path)
    if found_version == CONFIG_SCHEMA_VERSION:
        return load_config(path)
    try:
        ensure_hub_synced(force=True)
        activate_experience(DEFAULT_EXPERIENCE_ID)
        rebuild_environment()
    except Exception:
        logger.warning(
            "Could not apply the default Experience %r; staying on config v%s "
            "and retrying on the next boot.",
            DEFAULT_EXPERIENCE_ID,
            found_version,
            exc_info=True,
        )
        return load_config(path, persist_migration=False)
    return load_config(path)
