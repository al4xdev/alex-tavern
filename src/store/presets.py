"""Persistência de presets de usuário em JSON com lock por nome e escrita atômica."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

PRESETS_DIR = Path(".data/presets")
DEFAULTS_DIR = Path(".data/defaults")
_preset_locks: dict[str, asyncio.Lock] = {}


def _get_lock(name: str) -> asyncio.Lock:
    """Retorna (ou cria) o lock para este preset."""
    if name not in _preset_locks:
        _preset_locks[name] = asyncio.Lock()
    return _preset_locks[name]


def _ensure_dirs() -> None:
    """Garante que os diretórios de presets e defaults existem."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULTS_DIR.mkdir(parents=True, exist_ok=True)


def _preset_path(name: str) -> Path:
    return PRESETS_DIR / f"{name}.json"


def save_preset(name: str, config: dict) -> None:
    """Salva preset em JSON com escrita atômica."""
    _ensure_dirs()
    path = _preset_path(name)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(PRESETS_DIR),
        prefix=f"{name}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(fd)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_preset(name: str) -> dict | None:
    """Carrega preset de usuário ou do diretório de defaults como fallback."""
    path = _preset_path(name)
    if not path.exists():
        path = DEFAULTS_DIR / f"{name}.json"
        if not path.exists():
            return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def delete_preset(name: str) -> bool:
    """Remove o preset de usuário do filesystem."""
    path = _preset_path(name)
    if path.exists():
        path.unlink()
        _preset_locks.pop(name, None)
        return True
    return False


def list_presets() -> list[str]:
    """Lista todos os nomes de presets de usuário salvos."""
    _ensure_dirs()
    names: list[str] = []
    for f in PRESETS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)


def list_defaults() -> list[str]:
    """Lista todos os nomes de presets padrões/embutidos."""
    _ensure_dirs()
    names: list[str] = []
    for f in DEFAULTS_DIR.iterdir():
        if f.suffix == ".json":
            names.append(f.stem)
    return sorted(names)
