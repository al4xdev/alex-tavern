"""Persistência de GameState em JSON com lock por sessão e escrita atômica."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from src.models import GameState, dict_to_game_state, game_state_to_dict

SESSIONS_DIR = Path(".data/sessions")
_session_locks: dict[str, asyncio.Lock] = {}

# Tech debt: _session_locks cresce indefinidamente (aceitável no MVP)


def _get_lock(session_id: str) -> asyncio.Lock:
    """Retorna (ou cria) o lock para esta sessão."""
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def generate_session_id() -> str:
    """UUID4 curto (8 primeiros caracteres hex)."""
    return uuid.uuid4().hex[:8]


def _ensure_sessions_dir() -> None:
    """Garante que o diretório de sessões existe."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def save_game(game: GameState) -> None:
    """Salva GameState em JSON com escrita atômica (temp + fsync + rename).

    DEVE ser chamado dentro de um ``async with _get_lock(session_id)``.

    Args:
        game: GameState a ser salvo.
    """
    _ensure_sessions_dir()
    data: dict[str, Any] = game_state_to_dict(game)
    path = _session_path(game.session_id)

    # Write-to-temp-then-rename atômico
    fd, tmp_path = tempfile.mkstemp(
        dir=str(SESSIONS_DIR),
        prefix=f"{game.session_id}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(fd)
        os.replace(tmp_path, path)
    except BaseException:
        # Limpa o temp se algo falhar
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_game(session_id: str) -> GameState | None:
    """Carrega GameState do JSON da sessão.

    DEVE ser chamado dentro de um ``async with _get_lock(session_id)``.

    Args:
        session_id: ID da sessão.

    Returns:
        GameState ou None se o arquivo não existir.
    """
    path = _session_path(session_id)
    if not path.exists():
        return None

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return dict_to_game_state(data)


def delete_session(session_id: str) -> None:
    """Remove o arquivo de sessão e o log bruto de chamadas LLM. Usado em testes."""
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
    debug_path = SESSIONS_DIR / f"{session_id}.debug.jsonl"
    if debug_path.exists():
        debug_path.unlink()
    _session_locks.pop(session_id, None)


def list_sessions() -> list[dict]:
    """Lista todas as sessões com resumo (personagens, cena, turnos, data).

    Returns:
        Lista de dicts ordenada por ``created_at`` decrescente.
        Cada dict: {session_id, characters: [{name}], scene_location,
                    turn_count, created_at}
    """
    _ensure_sessions_dir()
    summaries: list[dict] = []
    for fpath in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if fpath.suffix != ".json":
            continue
        try:
            data: dict[str, Any] = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue  # pula arquivos corrompidos

        chars = data.get("characters", {})
        char_names = [
            {"name": ch.get("mind", {}).get("name", "")}
            for ch in chars.values()
        ]
        scene = data.get("scene", {})
        history = data.get("history", [])

        summaries.append({
            "session_id": data.get("session_id", fpath.stem),
            "characters": char_names,
            "scene_location": scene.get("location", ""),
            "turn_count": len(history),
            "created_at": data.get("created_at", ""),
        })
    # Ordena por created_at decrescente (mais recentes primeiro)
    summaries.sort(key=lambda s: s["created_at"], reverse=True)
    return summaries


def fork_session(session_id: str) -> str | None:
    """Cria uma cópia da sessão com novo ID.

    Args:
        session_id: ID da sessão original.

    Returns:
        Novo session_id, ou None se a sessão original não existir.
    """
    game = load_game(session_id)
    if game is None:
        return None

    new_id = generate_session_id()
    game.session_id = new_id
    save_game(game)
    return new_id
