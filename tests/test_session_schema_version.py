"""Versionamento de schema da sessão — política forward-only sem migração."""

from __future__ import annotations

import json

import httpx
import pytest

from src.models import SESSION_SCHEMA_VERSION
from src.store.sessions import (
    IncompatibleSessionError,
    generate_session_id,
    list_sessions,
    load_game,
    save_game,
    session_dir,
    session_state_path,
)
from tests.test_memory_retention import THREE_CHARACTERS, _make_game, _record


def _seed(session_id: str) -> None:
    save_game(_make_game(session_id, [_record(1, "Player", "olá")]))


def _cleanup(session_id: str) -> None:
    import shutil

    directory = session_dir(session_id)
    if directory.exists():
        shutil.rmtree(directory)


def test_saved_sessions_carry_current_schema_version() -> None:
    sid = generate_session_id()
    try:
        _seed(sid)
        data = json.loads(session_state_path(sid).read_text(encoding="utf-8"))
        assert data["schema_version"] == SESSION_SCHEMA_VERSION
        game = load_game(sid)
        assert game is not None and game.schema_version == SESSION_SCHEMA_VERSION
    finally:
        _cleanup(sid)


def test_outdated_session_is_refused_at_load() -> None:
    sid = generate_session_id()
    try:
        _seed(sid)
        path = session_state_path(sid)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["schema_version"] = SESSION_SCHEMA_VERSION - 1
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(IncompatibleSessionError) as excinfo:
            load_game(sid)
        assert excinfo.value.session_id == sid
        assert excinfo.value.found_version == SESSION_SCHEMA_VERSION - 1
    finally:
        _cleanup(sid)


def test_session_without_version_field_counts_as_v1_and_is_refused() -> None:
    sid = generate_session_id()
    try:
        _seed(sid)
        path = session_state_path(sid)
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["schema_version"]
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(IncompatibleSessionError) as excinfo:
            load_game(sid)
        assert excinfo.value.found_version == 1
    finally:
        _cleanup(sid)


def test_listing_flags_incompatible_sessions_but_keeps_them_visible() -> None:
    ok_sid = generate_session_id()
    old_sid = generate_session_id()
    try:
        _seed(ok_sid)
        _seed(old_sid)
        path = session_state_path(old_sid)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["schema_version"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")

        by_id = {entry["session_id"]: entry for entry in list_sessions()}
        assert by_id[ok_sid]["compatible"] is True
        assert by_id[ok_sid]["schema_version"] == SESSION_SCHEMA_VERSION
        assert by_id[old_sid]["compatible"] is False
        assert by_id[old_sid]["schema_version"] == 1
        # Campos best-effort continuam presentes para o card do frontend.
        assert by_id[old_sid]["characters"]
        assert by_id[old_sid]["turn_count"] == 1
    finally:
        _cleanup(ok_sid)
        _cleanup(old_sid)


@pytest.mark.asyncio
async def test_runner_surfaces_incompatibility_instead_of_opening() -> None:
    from src.runner import Runner

    sid = generate_session_id()
    try:
        _seed(sid)
        path = session_state_path(sid)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["schema_version"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")

        runner = Runner(httpx.AsyncClient(base_url="http://localhost:8888"), {})
        with pytest.raises(IncompatibleSessionError):
            await runner.player_turn(sid, speech="olá", force_speaker="C2")
    finally:
        _cleanup(sid)


def test_three_characters_fixture_reuse_is_intentional() -> None:
    assert set(THREE_CHARACTERS) == {"C1", "C2", "C3"}
