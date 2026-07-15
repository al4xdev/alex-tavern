from __future__ import annotations

import base64
import json
import shutil
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from starlette.requests import Request

from src.llm.debug_log import read_entries
from src.main import get_preset_avatar
from src.paths import PRESETS_DIR
from src.plugins.commands import CommandError, CommandRegistry
from src.plugins.runtime import PluginRuntime
from src.runner import Runner
from src.store.presets import (
    PresetConflictError,
    delete_preset,
    list_presets,
    load_avatar,
    load_preset,
    save_preset,
)
from src.store.sessions import delete_session, load_game


def _character(name: str = "Lyra") -> dict:
    return {
        "mind": {
            "name": name,
            "personality": "Lyra is cautious.",
            "knowledge": ["Lyra knows the road."],
            "current_mood": "alert",
        },
        "body": {
            "name": name,
            "physical_description": "Dark curls.",
            "outfit": "Green cloak.",
        },
    }


@pytest.fixture(autouse=True)
def clean_presets() -> None:
    if PRESETS_DIR.exists():
        shutil.rmtree(PRESETS_DIR)
    yield
    if PRESETS_DIR.exists():
        shutil.rmtree(PRESETS_DIR)


def _descriptor(name: str = "convert-character") -> dict:
    localized = {"en": "Text", "pt-BR": "Texto"}
    return {
        "name": name,
        "title": localized,
        "summary": localized,
        "icon": "✦",
        "aliases": {"en": ["character"], "pt-BR": ["personagem"]},
        "keywords": {"en": ["preset"], "pt-BR": ["converter"]},
        "inputs": [
            {
                "name": "preset-name",
                "type": "text",
                "required": True,
                "label": localized,
                "hint": localized,
            },
            {
                "name": "source-file",
                "type": "file",
                "required": False,
                "label": localized,
                "hint": localized,
                "accept": [".json"],
                "max_bytes": 64,
            },
        ],
        "result_kind": "core/character-preset-draft",
    }


def test_command_registry_rejects_collision_and_invalid_upload() -> None:
    registry = CommandRegistry()
    registry.register("one", "One", "1.0.0", _descriptor(), lambda value, context: {})
    with pytest.raises(ValueError, match="already reserved"):
        registry.register("two", "Two", "1.0.0", _descriptor(), lambda value, context: {})

    registration = registry.get("convert-character")
    assert registration is not None
    with pytest.raises(CommandError, match="could not be read"):
        registry._validated_payload(
            registration,
            {
                "values": {"preset-name": "lyra"},
                "files": {
                    "source-file": {
                        "name": "bad.json",
                        "media_type": "application/json",
                        "data_base64": "not-base64",
                    }
                },
            },
        )


def test_command_schema_v2_is_forward_only_namespaced_and_reserves_builtins() -> None:
    registry = CommandRegistry()
    legacy = {
        "name": "legacy",
        "summary": {"en": "Legacy", "pt-BR": "Legado"},
        "usage": "/legacy",
        "arguments": [],
        "fields": [],
        "result_kind": "legacy",
    }
    with pytest.raises(ValueError, match="schema v1 is unsupported"):
        registry.register("test.plugin", "Test", "1.0.0", legacy, lambda value, context: {})

    reserved = _descriptor("help")
    with pytest.raises(ValueError, match="reserved by Alex Tavern"):
        registry.register("test.plugin", "Test", "1.0.0", reserved, lambda value, context: {})

    wrong_namespace = _descriptor()
    wrong_namespace["result_kind"] = "another.plugin/result"
    with pytest.raises(ValueError, match="result_kind must use"):
        registry.register(
            "test.plugin", "Test", "1.0.0", wrong_namespace, lambda value, context: {}
        )


def test_command_aliases_share_the_global_namespace_and_payload_rejects_unknown_values() -> None:
    registry = CommandRegistry()
    registry.register("one", "One", "1.0.0", _descriptor(), lambda value, context: {})
    colliding = _descriptor("other-command")
    colliding["aliases"] = {"en": ["character"], "pt-BR": []}
    with pytest.raises(ValueError, match="/character"):
        registry.register("two", "Two", "1.0.0", colliding, lambda value, context: {})

    registration = registry.get("convert-character")
    assert registration is not None
    with pytest.raises(CommandError, match="unknown value"):
        registry._validated_payload(
            registration,
            {"values": {"preset-name": "lyra", "hidden": "no"}, "files": {}},
        )


@pytest.mark.asyncio
async def test_command_is_locked_logged_and_does_not_mutate_narrative_state() -> None:
    plugins = PluginRuntime()

    async def handler(payload, context):  # noqa: ANN001, ANN202
        context["game"].revision = 999
        return {"character": _character(), "preset_name": payload["values"]["preset-name"]}

    plugins.commands.register("test.plugin", "Test Plugin", "1.0.0", _descriptor(), handler)
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, plugins)
        session_id = runner.start_session()
        before = load_game(session_id)
        assert before is not None
        result = await runner.execute_command(
            session_id,
            "convert-character",
            {"values": {"preset-name": "lyra"}, "files": {}},
        )
    after = load_game(session_id)
    assert after is not None
    assert result["result_kind"] == "core/character-preset-draft"
    assert after.revision == before.revision
    assert after.history == before.history
    entries = [
        entry for entry in read_entries(session_id, 20) if entry["agent"].startswith("command_")
    ]
    assert [entry["agent"] for entry in entries] == ["command_input", "command_result"]
    assert "data_base64" not in json.dumps(entries)
    assert await delete_session(session_id)


def test_preset_crud_revision_avatar_and_public_shape() -> None:
    vp8x = b"\0\0\0\0" + (255).to_bytes(3, "little") + (255).to_bytes(3, "little")
    avatar_bytes = (
        b"RIFF"
        + (4 + 8 + len(vp8x)).to_bytes(4, "little")
        + b"WEBP"
        + b"VP8X"
        + len(vp8x).to_bytes(4, "little")
        + vp8x
    )
    created = save_preset(
        "lyra-nightfall",
        character=_character(),
        avatar={"media_type": "image/webp", "data_base64": base64.b64encode(avatar_bytes).decode()},
        expected_revision=None,
        replace=False,
    )
    assert created["revision"] == 1
    assert "data_base64" not in json.dumps(created)
    assert list_presets()[0]["preset_name"] == "lyra-nightfall"
    assert load_avatar("lyra-nightfall")[0] == avatar_bytes  # type: ignore[index]
    response = get_preset_avatar(
        "lyra-nightfall", Request({"type": "http", "method": "GET", "headers": []})
    )
    assert response.body == avatar_bytes
    assert response.headers["etag"] == f'"{created["avatar"]["sha256"]}"'
    cached = get_preset_avatar(
        "lyra-nightfall",
        Request(
            {
                "type": "http",
                "method": "GET",
                "headers": [(b"if-none-match", response.headers["etag"].encode())],
            }
        ),
    )
    assert cached.status_code == 304

    with pytest.raises(PresetConflictError, match="Confirm replacement"):
        save_preset(
            "lyra-nightfall",
            character=_character(),
            avatar=None,
            expected_revision=None,
            replace=False,
        )
    updated = save_preset(
        "lyra-nightfall",
        character=_character("Lyra Vale"),
        avatar=None,
        expected_revision=1,
        replace=True,
    )
    assert updated["revision"] == 2
    assert updated["avatar"] is not None
    assert delete_preset("lyra-nightfall", expected_revision=2)
    assert load_preset("lyra-nightfall") is None


def test_concurrent_replacement_allows_only_one_revision_winner() -> None:
    save_preset("lyra", character=_character(), avatar=None, expected_revision=None, replace=False)

    def replace(name: str) -> str:
        try:
            save_preset(
                "lyra",
                character=_character(name),
                avatar=None,
                expected_revision=1,
                replace=True,
            )
            return "saved"
        except PresetConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(replace, ["Lyra One", "Lyra Two"]))
    assert sorted(outcomes) == ["conflict", "saved"]
    assert load_preset("lyra")["revision"] == 2  # type: ignore[index]
