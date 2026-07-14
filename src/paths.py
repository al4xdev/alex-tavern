"""Shared filesystem paths for runtime data."""

from __future__ import annotations

import os
from pathlib import Path

DATA_DIR_ENV = "ROLEPLAY_DATA_DIR"
DATA_DIR = Path(os.environ.get(DATA_DIR_ENV, ".data")).expanduser()
CONFIG_PATH = DATA_DIR / "config.json"
SESSIONS_DIR = DATA_DIR / "sessions"
SCENARIOS_DIR = DATA_DIR / "scenarios"
PRESETS_DIR = DATA_DIR / "presets"
BUILTIN_SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
PLUGINS_DIR = DATA_DIR / "plugins"
PLUGIN_CACHE_DIR = PLUGINS_DIR / "cached"
PLUGIN_STARTED_DIR = PLUGINS_DIR / "started"
PLUGIN_CONFIG_DIR = PLUGINS_DIR / "config"
PLUGIN_ENV_DIR = PLUGINS_DIR / "environment"
PLUGIN_RUNTIME_PATH = PLUGINS_DIR / "runtime.json"
PLUGIN_EVENTS_PATH = PLUGINS_DIR / "events.jsonl"
PLUGIN_HUB_DIR = PLUGINS_DIR / "hub"
EXPERIENCES_DIR = DATA_DIR / "experiences"
