"""Shared filesystem paths for runtime data."""

from __future__ import annotations

import os
from pathlib import Path

DATA_DIR_ENV = "ROLEPLAY_DATA_DIR"
DATA_DIR = Path(os.environ.get(DATA_DIR_ENV, ".data")).expanduser()
CONFIG_PATH = DATA_DIR / "config.json"
SESSIONS_DIR = DATA_DIR / "sessions"
PRESETS_DIR = DATA_DIR / "presets"
DEFAULTS_DIR = DATA_DIR / "defaults"
