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

import src.plugins.store as store_module
from src import main
from src.paths import EXPERIENCES_DIR, PLUGIN_HUB_DIR, PLUGINS_DIR
from src.plugins.experiences import activate_experience, save_experience
from src.plugins.hooks import HookOrderError, HookRegistry
from src.plugins.manifest import (
    ManifestError,
    compare_versions,
    load_manifest,
    satisfies_version,
)
from src.plugins.runtime import PluginRuntime
from src.plugins.sdk import PluginModel
from src.plugins.store import (
    PluginInstallError,
    activate,
    active_pointers,
    install_curated,
    install_zip,
    installed_plugins,
    plugin_inventory,
    switch_activation,
    uninstall,
    update_curated,
)
from src.runner import Runner
from src.store.sessions import delete_session, load_game, session_debug_path
from tools.plugin_author import pack_plugin, scaffold_plugin

EXAMPLES = Path(__file__).resolve().parents[1] / "plugins" / "examples"


def _sec_headers() -> dict:
    """Task 19 access token so ASGI POSTs pass the origin/token gate."""
    import src.main
    return {"X-Tavern-Token": src.main.ACCESS_TOKEN}


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


def _versioned_plugin(
    destination: Path,
    version: str,
    *,
    permissions: tuple[str, ...] = (),
    python_dependencies: tuple[str, ...] = (),
) -> Path:
    permission_values = ", ".join(json.dumps(item) for item in permissions)
    dependency_values = ", ".join(json.dumps(item) for item in python_dependencies)
    manifest = f'''schema_version = 1
id = "dev.test.release"
name = "Release Test"
version = "{version}"
description = "Release inventory fixture"
license = "MIT"
authors = ["Tests"]
permissions = [{permission_values}]

[entrypoints]
backend = "backend.py"

[python]
dependencies = [{dependency_values}]
'''
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr("plugin.toml", manifest)
        archive.writestr("backend.py", "def setup(api):\n    pass\n")
    return destination


def _curate(artifact: Path, version: str) -> str:
    artifacts = PLUGIN_HUB_DIR / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    target = artifacts / artifact.name
    shutil.copy2(artifact, target)
    sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
    (PLUGIN_HUB_DIR / "catalog.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": [
                    {
                        "id": "dev.test.release",
                        "version": version,
                        "artifact": f"artifacts/{target.name}",
                        "sha256": sha256,
                    }
                ],
                "experiences": [],
            }
        ),
        encoding="utf-8",
    )
    return sha256


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
    assert compare_versions("2.0.0-rc.1", "2.0.0") < 0
    assert compare_versions("2.0.0+build.2", "2.0.0+build.1") == 0


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


def test_plugin_restart_waits_for_explicit_endpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _pack(EXAMPLES / "turn_counter", tmp_path / "counter.zip")
    installed = install_zip(package)
    restart_requests: list[bool] = []
    monkeypatch.setattr(
        "src.supervisor.request_restart",
        lambda: restart_requests.append(True) or True,
    )
    monkeypatch.setattr(store_module, "rebuild_environment", lambda pointers=None: {"locked": []})
    activated = main.activate_plugin(
        "dev.alex-tavern.turn-counter",
        main.PluginActivationRequest(
            version=installed["manifest"]["version"], sha256=installed["sha256"]
        ),
    )
    deactivated = main.deactivate_plugin("dev.alex-tavern.turn-counter")

    assert activated["restart"] is True
    assert deactivated["restart"] is True
    assert restart_requests == []

    background_tasks = main.BackgroundTasks()
    restarted = main.restart_plugins(background_tasks)
    assert restarted == {"restart": True}
    assert len(background_tasks.tasks) == 1
    background_tasks.tasks[0].func()
    assert restart_requests == [True]


def test_zip_rejects_path_traversal(tmp_path: Path) -> None:
    malicious = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../outside", "no")
    with pytest.raises(PluginInstallError, match="Unsafe ZIP member"):
        install_zip(malicious)


@pytest.mark.asyncio
async def test_external_zip_can_be_inspected_without_installing(tmp_path: Path) -> None:
    package = _versioned_plugin(tmp_path / "external.zip", "1.0.0", permissions=("model.call",))
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=_sec_headers()) as client:
        response = await client.post(
            "/plugins/inspect-upload",
            headers={"Content-Type": "application/zip"},
            content=package.read_bytes(),
        )

    assert response.status_code == 200
    assert response.json()["manifest"]["permissions"] == ["model.call"]
    assert installed_plugins() == []


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


def test_inventory_groups_versions_and_describes_reviewed_update(tmp_path: Path) -> None:
    first = install_zip(_versioned_plugin(tmp_path / "release-1.zip", "1.0.0"))
    activate("dev.test.release", "1.0.0", first["sha256"])
    candidate_zip = _versioned_plugin(
        tmp_path / "release-2.zip", "2.0.0", permissions=("model.call",)
    )
    candidate_hash = _curate(candidate_zip, "2.0.0")

    inventory = plugin_inventory()

    assert len(inventory) == 1
    plugin = inventory[0]
    assert plugin["plugin_id"] == "dev.test.release"
    assert plugin["state"] == "update_available"
    assert plugin["active"]["manifest"]["version"] == "1.0.0"
    assert [item["manifest"]["version"] for item in plugin["cached_versions"]] == ["1.0.0"]
    assert plugin["curated"]["sha256"] == candidate_hash
    assert plugin["curated"]["diff"]["permissions"]["added"] == ["model.call"]


def test_same_version_with_different_hash_is_release_conflict(tmp_path: Path) -> None:
    installed = install_zip(_versioned_plugin(tmp_path / "local.zip", "1.0.0"))
    activate("dev.test.release", "1.0.0", installed["sha256"])
    remote = _versioned_plugin(tmp_path / "remote.zip", "1.0.0", permissions=("config.read",))
    remote_hash = _curate(remote, "1.0.0")

    assert plugin_inventory()[0]["state"] == "release_conflict"
    with pytest.raises(PluginInstallError, match="conflicts"):
        update_curated("dev.test.release", "1.0.0", remote_hash)


def test_failed_environment_build_keeps_previous_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = install_zip(_versioned_plugin(tmp_path / "release-1.zip", "1.0.0"))
    second = install_zip(_versioned_plugin(tmp_path / "release-2.zip", "2.0.0"))
    activate("dev.test.release", "1.0.0", first["sha256"])

    def fail(pointers=None):  # noqa: ANN001, ANN202, ARG001
        raise RuntimeError("dependency installation failed")

    monkeypatch.setattr(store_module, "rebuild_environment", fail)
    with pytest.raises(RuntimeError, match="dependency installation failed"):
        switch_activation("dev.test.release", "2.0.0", second["sha256"])

    assert active_pointers()[0]["sha256"] == first["sha256"]


def test_exact_curated_update_retains_old_version_for_rollback(tmp_path: Path) -> None:
    first = install_zip(_versioned_plugin(tmp_path / "release-1.zip", "1.0.0"))
    activate("dev.test.release", "1.0.0", first["sha256"])
    candidate = _versioned_plugin(tmp_path / "release-2.zip", "2.0.0")
    candidate_hash = _curate(candidate, "2.0.0")

    result = update_curated("dev.test.release", "2.0.0", candidate_hash)

    assert result["activated"]["version"] == "2.0.0"
    assert {item["manifest"]["version"] for item in installed_plugins()} == {"1.0.0", "2.0.0"}


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


def _stub_turn_pipeline(runner) -> None:  # noqa: ANN001
    """Thought-only turns now run the full Director pipeline (omniscience);
    plugin tests only exercise hooks, so the LLM boundary is stubbed out."""

    async def fake_narrator(game, turn_number, forced_speaker=None, narrator_hint="", **kwargs):  # noqa: ANN001, ANN003, ANN202, ARG001
        return {
            "next_speakers": ["Narrator"],
            "perception_events": [],
            "scene_update": None,
            "mood_updates": None,
            "return_control": False,
        }

    async def fake_prose(game, events, turn_number):  # noqa: ANN001, ANN202
        return ""

    runner._call_narrator = fake_narrator
    runner._render_narration = fake_prose


@pytest.mark.asyncio
async def test_runner_discards_crashed_precommit_plugin_draft() -> None:
    runtime = PluginRuntime()

    def crash(game, context):  # noqa: ANN001, ANN202, ARG001
        game.plugin_state["broken"] = {"dirty": True}
        raise RuntimeError("precommit failure")

    runtime.hooks.register("broken", "turn.before_commit", "filter", crash)
    async with httpx.AsyncClient() as client:
        runner = Runner(client, {}, runtime)
        _stub_turn_pipeline(runner)
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
        _stub_turn_pipeline(runner)
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
