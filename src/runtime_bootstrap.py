"""First-boot work that must complete before the application serves traffic."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import load_config
from src.paths import CONFIG_PATH, PLUGINS_DIR
from src.plugins.experiences import activate_experience
from src.plugins.hub import ensure_hub_synced
from src.plugins.store import rebuild_environment
from src.store.jsonfile import read_json, write_json

DEFAULT_EXPERIENCE_ID = "before_the_war"

logger = logging.getLogger(__name__)


def bootstrap_marker_path() -> Path:
    """Where the completed first-boot record lives."""
    return PLUGINS_DIR / "bootstrap.json"


def prepare_runtime_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Apply the mandatory default Experience once, then load the config.

    The marker file — not the configuration — records that the default
    Experience was installed, so the two concerns stay independent: the user's
    provider settings persist from the very first boot even when the plugin hub
    is unreachable, and the Experience is retried on the next boot until it
    succeeds.

    Failure is logged rather than raised, because this runs first in the
    application lifespan: raising takes the whole server down. The default
    Experience needs the plugin hub, so on a phone with no connectivity it is
    unreachable through no fault of the install — the app has to come up anyway.
    """
    marker = bootstrap_marker_path()
    if read_json(marker) is None:
        try:
            ensure_hub_synced(force=True)
            activate_experience(DEFAULT_EXPERIENCE_ID)
            rebuild_environment()
        except Exception:
            logger.warning(
                "Could not apply the default Experience %r; retrying on the next boot.",
                DEFAULT_EXPERIENCE_ID,
                exc_info=True,
            )
        else:
            write_json(
                marker,
                {
                    "experience_id": DEFAULT_EXPERIENCE_ID,
                    "applied_at": datetime.now(UTC).isoformat(),
                },
            )
    return load_config(path)
