"""Plugin contract, package lifecycle, ordering, and crash-containment tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import tomllib
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from src.paths import EXPERIENCES_DIR, PLUGIN_HUB_DIR, PLUGINS_DIR
from src.plugins.experiences import activate_experience, save_experience
from src.plugins.hooks import HookOrderError, HookRegistry
from src.plugins.manifest import ManifestError, load_manifest, satisfies_version
from src.plugins.runtime import PluginRuntime
from src.plugins.sdk import PluginModel
from src.plugins.store import (
    PluginInstallError,
    activate,
    active_pointers,
    install_curated,
    install_zip,
    installed_plugins,
    uninstall,
)
from src.runner import Runner
from src.store.sessions import delete_session, load_game, session_debug_path
from tools.plugin_author import pack_plugin, scaffold_plugin

EXAMPLES = Path(__file__).resolve().parents[1] / "plugins" / "examples"


@pytest.fixture(autouse=True)
def isolated_plugin_data() -> None:
    for directory in (PLUGINS_DIR, EXPERIENCES_DIR):
        if directory.exists():
            shutil.rmtree(directory)
    yield
    for directory in (PLUGINS_DIR, EXPERIENCES_DIR):
        if directory.exists():
            shutil.rmtree(directory)


def _pack(source: Path, destination: Path) -> Path:
    with zipfile.ZipFile(destination, "w") as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source))
    return destination


def test_reference_manifest_is_strict_and_current() -> None:
    manifest = load_manifest(EXAMPLES / "openrouter_provider")
    assert manifest.plugin_id == "dev.alex-tavern.openrouter"
    assert manifest.entrypoints.frontend == "frontend.js"
    invalid = tomllib.loads(
        (EXAMPLES / "openrouter_provider" / "plugin.toml").read_text(encoding="utf-8")
    )
    invalid["schema_version"] = 99
    with pytest.raises(ManifestError, match="schema_version"):
        from src.plugins.manifest import parse_manifest

        parse_manifest(invalid)


@pytest.mark.asyncio
async def test_hook_order_and_failed_filter_draft_rollback() -> None:
    failures: list[str] = []

    async def failed(plugin_id: str, hook: str, error: BaseException) -> None:
        failures.append(f"{plugin_id}:{hook}:{error}")

    hooks = HookRegistry(failed)
    hooks.register("later", "demo", "filter", lambda value, _: [*value, "later"], after=("first",))
    hooks.register("first", "demo", "filter", lambda value, _: [*value, "first"])

    def crash(value, context):  # noqa: ANN001, ANN202, ARG001
        value.append("dirty")
        raise RuntimeError("boom")

    hooks.register("broken", "demo", "filter", crash, priority=100)
    assert await hooks.filter("demo", [], {}) == ["first", "later"]
    assert failures == ["broken:demo:boom"]


def test_hook_cycle_is_rejected_at_registration() -> None:
    hooks = HookRegistry()
    hooks.register("one", "cycle", "action", lambda _: None, after=("two",))
    with pytest.raises(HookOrderError, match="cycle"):
        hooks.register("two", "cycle", "action", lambda _: None, after=("one",))


def test_dependency_version_constraints_are_semantic() -> None:
    assert satisfies_version("1.8.2", ">=1.2.0,<2.0.0")
    assert satisfies_version("1.8.2", "^1.4.0")
    assert not satisfies_version("2.0.0", "^1.4.0")
    assert satisfies_version("1.8.9", "~1.8.0")
    assert not satisfies_version("1.9.0", "~1.8.0")


def test_zip_install_activation_and_backend_boot(tmp_path: Path) -> None:
    package = _pack(EXAMPLES / "turn_counter", tmp_path / "counter.zip")
    installed = install_zip(package)
    assert installed["manifest"]["plugin_id"] == "dev.alex-tavern.turn-counter"
    assert len(installed_plugins()) == 1
    pointer = activate("dev.alex-tavern.turn-counter")
    assert pointer["sha256"] == installed["sha256"]
    assert active_pointers() == [pointer]

    runtime = PluginRuntime()
    runtime.boot()
    assert "dev.alex-tavern.turn-counter" in runtime.loaded
    assert runtime.disabled_for_boot == {}


def test_zip_rejects_path_traversal(tmp_path: Path) -> None:
    malicious = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../outside", "no")
    with pytest.raises(PluginInstallError, match="Unsafe ZIP member"):
        install_zip(malicious)


def test_curated_install_requires_the_catalog_hash() -> None:
    artifacts = PLUGIN_HUB_DIR / "artifacts"
    artifacts.mkdir(parents=True)
    artifact = _pack(EXAMPLES / "openrouter_provider", artifacts / "openrouter.zip")
    sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (PLUGIN_HUB_DIR / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": [
                    {
                        "id": "dev.alex-tavern.openrouter",
                        "version": "1.0.0",
                        "artifact": "artifacts/openrouter.zip",
                        "sha256": sha256,
                    }
                ],
                "experiences": [],
            }
        ),
        encoding="utf-8",
    )
    installed = install_curated("dev.alex-tavern.openrouter", "1.0.0")
    assert installed["sha256"] == sha256


def test_experience_switches_the_physical_active_set(tmp_path: Path) -> None:
    for folder in ("turn_counter", "crash_test"):
        install_zip(_pack(EXAMPLES / folder, tmp_path / f"{folder}.zip"))
    activate("dev.alex-tavern.crash-test")
    experience = {
        "schema_version": 1,
        "id": "clean-writing",
        "name": "Clean writing",
        "description": "Grammar filter only",
        "image": "preview.gif",
        "plugins": [
            {
                "id": "dev.alex-tavern.turn-counter",
                "version": "1.0.0",
                "config": {"label": "clean"},
            }
        ],
    }
    save_experience(experience)
    result = activate_experience("clean-writing")
    assert result["restart"] is True
    assert [item["plugin_id"] for item in active_pointers()] == ["dev.alex-tavern.turn-counter"]
    config_path = PLUGINS_DIR / "config" / "dev.alex-tavern.turn-counter.json"
    assert json.loads(config_path.read_text(encoding="utf-8"))["label"] == "clean"


def test_experience_installs_missing_curated_dependency(tmp_path: Path) -> None:
    artifacts = PLUGIN_HUB_DIR / "artifacts"
    artifacts.mkdir(parents=True)
    artifact = _pack(EXAMPLES / "turn_counter", artifacts / "counter.zip")
    sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (PLUGIN_HUB_DIR / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": [
                    {
                        "id": "dev.alex-tavern.turn-counter",
                        "version": "1.0.0",
                        "artifact": "artifacts/counter.zip",
                        "sha256": sha256,
                    }
                ],
                "experiences": [],
            }
        ),
        encoding="utf-8",
    )
    save_experience(
        {
            "schema_version": 1,
            "id": "auto-install",
            "name": "Auto install",
            "description": "Installs its dependency.",
            "image": "",
            "plugins": [
                {
                    "id": "dev.alex-tavern.turn-counter",
                    "version": "1.0.0",
                    "config": {},
                }
            ],
        }
    )

    result = activate_experience("auto-install")

    assert [item["manifest"]["plugin_id"] for item in result["installed"]] == [
        "dev.alex-tavern.turn-counter"
    ]
    assert [pointer["plugin_id"] for pointer in active_pointers()] == [
        "dev.alex-tavern.turn-counter"
    ]


def test_uninstall_removes_cache_and_matching_activation(tmp_path: Path) -> None:
    installed = install_zip(_pack(EXAMPLES / "turn_counter", tmp_path / "counter.zip"))
    activate("dev.alex-tavern.turn-counter")

    result = uninstall(
        "dev.alex-tavern.turn-counter",
        installed["manifest"]["version"],
        installed["sha256"],
    )

    assert result["deactivated"] is True
    assert installed_plugins() == []
    assert active_pointers() == []
    with pytest.raises(PluginInstallError, match="not found"):
        uninstall(
            "dev.alex-tavern.turn-counter",
            installed["manifest"]["version"],
            installed["sha256"],
        )


def test_concurrent_uninstall_leaves_one_clean_result(tmp_path: Path) -> None:
    installed = install_zip(_pack(EXAMPLES / "turn_counter", tmp_path / "counter.zip"))
    selection = (
        "dev.alex-tavern.turn-counter",
        installed["manifest"]["version"],
        installed["sha256"],
    )

    def remove() -> str:
        try:
            uninstall(*selection)
            return "removed"
        except PluginInstallError:
            return "missing"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(lambda _: remove(), range(2)))

    assert outcomes == ["missing", "removed"]
    assert installed_plugins() == []


@pytest.mark.asyncio
async def test_runner_discards_crashed_precommit_plugin_draft() -> None:
    runtime = PluginRuntime()

    def crash(game, context):  # noqa: ANN001, ANN202, ARG001
        game.plugin_state["broken"] = {"dirty": True}
        raise RuntimeError("precommit failure")

    runtime.hooks.register("broken", "turn.before_commit", "filter", crash)
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)
        session_id = runner.start_session()
        result = await runner.player_turn(session_id, thought="secret")
    assert result["turn_number"] == 1
    game = load_game(session_id)
    assert game is not None
    assert "broken" not in game.plugin_state
    assert runtime.disabled_for_boot["broken"].startswith("turn.before_commit")


def test_agent_authoring_scaffold_and_pack_are_reproducible(tmp_path: Path) -> None:
    package = tmp_path / "authored"
    scaffolded = scaffold_plugin(
        package,
        "dev.example.authored",
        "Authored Example",
        backend=True,
        frontend=True,
    )
    assert scaffolded["valid"] is True
    first = pack_plugin(package, tmp_path / "first.zip")
    second = pack_plugin(package, tmp_path / "second.zip")
    assert first["sha256"] == second["sha256"]


@pytest.mark.asyncio
async def test_plugin_model_call_json_uses_shared_provider_and_logs_metadata() -> None:
    observed: dict[str, object] = {}

    def respond(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["authorization"] = request.headers.get("Authorization")
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"text":"corrigido"}'}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4},
            },
        )

    config = {
        "provider": "deepseek",
        "api_base": "https://provider.invalid",
        "api_key": "private-key",
        "model": "model-name",
        "language": "Portuguese",
        "thinking_enabled": False,
        "llm_timeout_seconds": 3,
    }
    session_id = "pluginmodel"
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        runner = Runner(client, config)
        result = await PluginModel("dev.test.structured").call_json(
            {
                "runner": runner,
                "game": SimpleNamespace(session_id=session_id),
                "turn_number": 7,
            },
            messages=[{"role": "user", "content": "corrija"}],
            json_schema={
                "name": "plugin_result",
                "schema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
            },
            max_tokens=64,
            use_configured_language=False,
        )

    assert result == {"text": "corrigido"}
    assert observed["url"] == "https://provider.invalid/chat/completions"
    assert observed["authorization"] == "Bearer private-key"
    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["response_format"] == {"type": "json_object"}
    entries = json.loads(session_debug_path(session_id).read_text(encoding="utf-8"))
    assert entries["agent"] == "plugin:dev.test.structured"
    assert entries["turn_number"] == 7
    assert "private-key" not in json.dumps(entries)
    await delete_session(session_id)


@pytest.mark.asyncio
async def test_turn_input_filter_records_raw_and_effective_values() -> None:
    runtime = PluginRuntime()

    async def correct(value, context):  # noqa: ANN001, ANN202
        assert context["turn_number"] == 1
        value["thought"] = "Eu estou aqui."
        return value

    runtime.hooks.register("dev.test.correct", "turn.input", "filter", correct)
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)
        session_id = runner.start_session()
        result = await runner.player_turn(session_id, thought="eu esta aqui")

    assert result["effective_input"]["thought"] == "Eu estou aqui."
    assert result["transformed_fields"] == ["thought"]
    game = load_game(session_id)
    assert game is not None
    assert game.history[-1].content == "Eu estou aqui."
    assert game.history[-1].input_transformed is True
    records = [
        json.loads(line)
        for line in session_debug_path(session_id).read_text(encoding="utf-8").splitlines()
    ]
    assert [record["agent"] for record in records] == [
        "turn_input",
        "turn_input_effective",
    ]
    assert records[0]["input"]["thought"] == "eu esta aqui"
    assert records[1]["input"]["thought"] == "Eu estou aqui."
    await delete_session(session_id)
