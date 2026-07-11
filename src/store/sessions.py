"""Persistência de GameState em JSON com lock por sessão e escrita atômica."""

from __future__ import annotations

import asyncio
import json
import os
import re
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
    fd, tmp_name = tempfile.mkstemp(
        dir=str(SESSIONS_DIR),
        prefix=f"{game.session_id}_",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(fd)
        tmp_path.replace(path)
    except BaseException:
        # Limpa o temp se algo falhar
        if tmp_path.exists():
            tmp_path.unlink()
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


def backup_session(session_id: str) -> str:
    """Copia o {session_id}.json atual para {session_id}.kb_N.json (N incremental).

    Feito ANTES de qualquer edição destrutiva (ex.: compactação) para permitir
    recuperação manual. Cópia de bytes crus, sem reserializar — o backup é
    bit-a-bit idêntico ao arquivo original no momento da chamada.

    Returns:
        Path (string) do arquivo de backup criado.

    Raises:
        FileNotFoundError: se a sessão não existir.
    """
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Sessão {session_id} não encontrada para backup.")

    _ensure_sessions_dir()
    pattern = re.compile(rf"^{re.escape(session_id)}\.kb_(\d+)\.json$")
    indices = [int(m.group(1)) for f in SESSIONS_DIR.iterdir() if (m := pattern.match(f.name))]
    next_index = max(indices, default=-1) + 1
    backup_path = SESSIONS_DIR / f"{session_id}.kb_{next_index}.json"
    backup_path.write_bytes(path.read_bytes())
    return str(backup_path)


def find_latest_backup(session_id: str) -> Path | None:
    """Acha o backup de compactação mais recente ({session_id}.kb_N.json de maior N).

    Returns:
        Path do backup, ou None se não houver nenhum.
    """
    _ensure_sessions_dir()
    pattern = re.compile(rf"^{re.escape(session_id)}\.kb_(\d+)\.json$")
    candidates = [
        (int(m.group(1)), f) for f in SESSIONS_DIR.iterdir() if (m := pattern.match(f.name))
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[-1][1]


def restore_last_backup(session_id: str) -> dict:
    """Desfaz a última compactação, restaurando o backup mais recente — SE seguro.

    ⚠️ Operação arriscada por natureza: só restaura se NENHUM turno novo foi
    jogado desde aquela compactação (o maior ``turn_number`` da sessão ativa
    não pode ser maior que o maior ``turn_number`` do próprio backup) — senão,
    restaurar descartaria essas jogadas novas de verdade (elas não existem no
    backup, que é anterior a elas). Nesse caso a operação se RECUSA, sem tocar
    em nada — nunca tenta "mesclar" os dois históricos.

    DEVE ser chamado dentro de um ``async with _get_lock(session_id)``.
    Trabalha em cima dos dicts JSON crus (sem round-trip por dataclass), pra
    minimizar a chance de um bug de (de)serialização mascarar a checagem.

    Returns:
        ``{"error": "..."}`` se a sessão não existe (mesmo formato de
        ``undo_turn``/``compact_session``, pro endpoint devolver 404).
        ``{"restored": False, "reason": "..."}`` se não há backup, ou não é
        seguro restaurar (nada é alterado nesse caso).
        ``{"restored": True, "history_length": N}`` se restaurou — o backup
        consumido é apagado; uma nova chamada, se houver outro backup mais
        antigo, restaura esse (mesmo espírito do undo: uma chamada por vez).
    """
    path = _session_path(session_id)
    if not path.exists():
        return {"error": f"Sessão {session_id} não encontrada."}

    backup_path = find_latest_backup(session_id)
    if backup_path is None:
        return {"restored": False, "reason": "Nenhum backup de compactação encontrado."}

    try:
        backup_data: dict[str, Any] = json.loads(backup_path.read_text(encoding="utf-8"))
        live_data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return {"restored": False, "reason": f"Backup ou sessão corrompidos: {e}"}

    backup_max_turn = max((h["turn_number"] for h in backup_data.get("history", [])), default=0)
    live_max_turn = max((h["turn_number"] for h in live_data.get("history", [])), default=0)
    if live_max_turn > backup_max_turn:
        return {
            "restored": False,
            "reason": (
                f"Há turnos mais recentes (até {live_max_turn}) do que o backup "
                f"(até {backup_max_turn}) — restaurar perderia essas jogadas. "
                "Nada foi alterado."
            ),
        }

    path.write_bytes(backup_path.read_bytes())
    backup_path.unlink()
    return {"restored": True, "history_length": len(backup_data.get("history", []))}


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
        char_names = [{"name": ch.get("mind", {}).get("name", "")} for ch in chars.values()]
        scene = data.get("scene", {})
        history = data.get("history", [])

        summaries.append(
            {
                "session_id": data.get("session_id", fpath.stem),
                "characters": char_names,
                "scene_location": scene.get("location", ""),
                "turn_count": len(history),
                "created_at": data.get("created_at", ""),
            }
        )
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
