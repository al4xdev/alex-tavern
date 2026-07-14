"""FastAPI server para o sistema de roleplay multi-agente."""

from __future__ import annotations

import asyncio
import json
import tempfile
import threading
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config import (
    ConfigValidationError,
    load_config,
    merge_config_update,
    public_config,
    resolve_active_config,
)
from src.llm.debug_log import read_entries
from src.paths import DATA_DIR
from src.plugins.runtime import PluginRuntime
from src.runner import Runner
from src.store.sessions import delete_session, fork_session, list_sessions

MAX_READ_LIMIT = 1000


@dataclass(slots=True)
class RuntimeState:
    """Application-scoped mutable runtime switched as one transaction."""

    stored_config: dict[str, Any]
    server_config: dict[str, Any]
    llm_client: httpx.AsyncClient
    runner: Runner
    plugins: PluginRuntime = field(default_factory=PluginRuntime)
    config_lock: threading.RLock = field(default_factory=threading.RLock)


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    plugins = PluginRuntime()
    plugins.boot()
    stored_config = load_config()
    server_config = resolve_active_config(stored_config)
    llm_client = httpx.AsyncClient()
    runtime = RuntimeState(
        stored_config=stored_config,
        server_config=server_config,
        llm_client=llm_client,
        runner=Runner(llm_client, server_config, plugins),
        plugins=plugins,
    )
    plugins.bind_host(runtime)
    app.state.runtime = runtime
    yield
    await llm_client.aclose()


app = FastAPI(lifespan=lifespan)


def _runtime() -> RuntimeState:
    """Return initialized application state or fail clearly outside lifespan."""
    runtime = getattr(app.state, "runtime", None)
    if not isinstance(runtime, RuntimeState):
        raise RuntimeError("Application runtime is not initialized")
    return runtime


# CORS — allow all in MVP (local frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────


class CharacterMindInput(BaseModel):
    name: str
    personality: str = ""
    knowledge: list[str] = Field(default_factory=list)
    current_mood: str = ""


class CharacterBodyInput(BaseModel):
    name: str
    physical_description: str = ""
    outfit: str = ""


class CharacterInput(BaseModel):
    mind: CharacterMindInput
    body: CharacterBodyInput


class SceneInput(BaseModel):
    location: str = ""
    time_of_day: str = ""
    present_characters: list[str] = Field(default_factory=list)
    physical_facts: dict[str, str] = Field(default_factory=dict)


class StartSessionRequest(BaseModel):
    controlled_character_id: str | None = None
    characters: dict[str, CharacterInput] | None = None
    scene: SceneInput | None = None
    narrator_directives: str | None = None
    scenario_name: str | None = None
    character_preset_ids: dict[str, str] = Field(default_factory=dict)


class StartSessionResponse(BaseModel):
    session_id: str
    state: dict


class PlayerTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speech: str = ""
    thought: str = ""
    action: str = ""
    force_speaker: str | None = None
    narrator_hint: str = ""
    skip: bool = False

    @model_validator(mode="after")
    def require_content(self) -> PlayerTurnRequest:
        if self.skip:
            if self.speech.strip() or self.thought.strip() or self.action.strip():
                raise ValueError("skip=True cannot be combined with speech, thought, or action")
            return self
        if not any(
            value.strip() for value in (self.speech, self.thought, self.action, self.narrator_hint)
        ):
            raise ValueError("A turn needs speech, thought, action, or narrator_hint")
        return self


class CommandFileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    media_type: str = "application/octet-stream"
    data_base64: str


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arguments: dict[str, str] = Field(default_factory=dict)
    fields: dict[str, str] = Field(default_factory=dict)
    files: dict[str, CommandFileInput] = Field(default_factory=dict)


class AvatarInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_type: Literal["image/webp"]
    data_base64: str


class PresetPutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    character: CharacterInput
    avatar: AvatarInput | None = None
    expected_revision: int | None = Field(default=None, ge=1)
    replace: bool = False


class CharacterResponse(BaseModel):
    speech: str | None = None
    thought: str | None = None


class EffectiveTurnInput(BaseModel):
    speech: str
    thought: str
    action: str


class PlayerTurnResponse(BaseModel):
    narration: str | None = None
    character_response: CharacterResponse | None = None
    next_speaker: str | None = None
    scene_update: dict | None = None
    turn_number: int | None = None
    effective_input: EffectiveTurnInput | None = None
    transformed_fields: list[Literal["speech", "thought", "action"]] = Field(default_factory=list)
    automatic_compaction: dict[str, Any] | None = None
    error: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[dict] | None = None
    error: str | None = None


class CompactResponse(BaseModel):
    compacted: bool
    status: str | None = None
    trigger: str | None = None
    compaction_id: str | None = None
    reason: str | None = None
    evicted_records: int | None = None
    kept_records: int | None = None
    cutoff_turn_number: int | None = None
    estimated_context_tokens: int | None = None
    threshold_tokens: int | None = None
    context_max: int | None = None
    undo_depth: int | None = None
    error: str | None = None


class RestoreCompactionResponse(BaseModel):
    restored: bool
    undone: bool | None = None
    compaction_id: str | None = None
    reason: str | None = None
    history_length: int | None = None
    restored_records: int | None = None
    preserved_through_turn: int | None = None
    remaining_undo_depth: int | None = None
    plugin_conflicts: list[str] = Field(default_factory=list)
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest) -> dict:
    """Creates a new roleplay session."""
    active_runner = _runtime().runner
    from src.models import (
        Scene,
        dict_to_character,
        game_state_to_dict,
    )
    from src.store.scenarios import list_builtin_scenarios, load_builtin_scenario, load_scenario

    scenario_data: dict[str, Any] = {}
    if req.scenario_name:
        scenario_val = load_scenario(req.scenario_name)
        if scenario_val is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario '{req.scenario_name}' not found.",
            )
        scenario_data = scenario_val

    if not scenario_data and not req.characters and not req.scene:
        defaults = list_builtin_scenarios()
        if defaults:
            first_def = load_builtin_scenario(defaults[0])
            if first_def:
                scenario_data = first_def

    characters = {}
    if req.characters:
        for cid, ci in req.characters.items():
            characters[cid] = dict_to_character(ci.dict())
    elif "characters" in scenario_data:
        for cid, cdata in scenario_data["characters"].items():
            characters[cid] = dict_to_character(cdata)

    scene = None
    if req.scene is not None:
        scene = Scene(
            location=req.scene.location,
            time_of_day=req.scene.time_of_day,
            present_characters=[],  # recomputed by the runner
            physical_facts=dict(req.scene.physical_facts),
        )
    elif "scene" in scenario_data:
        sdata = scenario_data["scene"]
        scene = Scene(
            location=sdata["location"],
            time_of_day=sdata["time_of_day"],
            present_characters=list(sdata.get("present_characters", [])),
            physical_facts=dict(sdata.get("physical_facts", {})),
        )

    directives = ""
    if req.narrator_directives is not None:
        directives = req.narrator_directives
    elif "narrator_directives" in scenario_data:
        directives = scenario_data["narrator_directives"]

    controlled_id = ""
    if req.controlled_character_id:
        controlled_id = req.controlled_character_id
    elif "controlled_character_id" in scenario_data:
        controlled_id = scenario_data["controlled_character_id"]

    cfg: dict[str, Any] = {
        "controlled_character_id": controlled_id,
        "narrator_directives": directives,
        "character_preset_ids": (
            dict(req.character_preset_ids)
            if req.character_preset_ids
            else dict(scenario_data.get("character_preset_ids", {}))
        ),
    }
    if characters:
        cfg["characters"] = characters
    if scene:
        cfg["scene"] = scene

    try:
        session_id = active_runner.start_session(cfg)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    game = await active_runner.get_state(session_id)
    assert game is not None, "Newly-created session should exist"
    return {"session_id": session_id, "state": game_state_to_dict(game)}


@app.post("/session/{session_id}/turn", response_model=PlayerTurnResponse)
async def player_turn(session_id: str, body: PlayerTurnRequest) -> dict:
    """Processes a Player's turn."""
    result = await _runtime().runner.player_turn(
        session_id=session_id,
        speech=body.speech,
        thought=body.thought,
        action=body.action,
        force_speaker=body.force_speaker,
        narrator_hint=body.narrator_hint,
        skip=body.skip,
    )
    return result


@app.get("/commands")
def get_commands() -> dict[str, Any]:
    """Return the executable command catalog for slash autocomplete and forms."""
    return {"schema_version": 1, "commands": _runtime().plugins.commands.public_catalog()}


@app.post("/session/{session_id}/commands/{command_name}")
async def execute_command(
    session_id: str, command_name: str, body: CommandRequest
) -> dict[str, Any]:
    """Execute a non-narrative plugin command under the session lock."""
    from src.plugins.commands import CommandError

    try:
        return await _runtime().runner.execute_command(session_id, command_name, body.model_dump())
    except CommandError as error:
        status = 404 if error.code in {"command_not_found", "session_not_found"} else 422
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "message": str(error), "field": error.field},
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "command_failed",
                "message": str(error) or "The command could not be completed.",
            },
        ) from error


@app.post("/session/{session_id}/suggest", response_model=SuggestResponse)
async def suggest_actions(session_id: str) -> dict:
    """Possible move suggestions from the Narrator for the controlled character (manual trigger)."""
    result = await _runtime().runner.suggest_actions(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/session/{session_id}/compact", response_model=CompactResponse)
async def compact_session(session_id: str, request: Request):  # noqa: ANN201
    """Compacts the session: summarizes old turns, keeps only the most recent ones.

    Browser clients negotiate measured SSE progress; machine clients receive
    the equivalent final JSON result.
    """
    runner = _runtime().runner
    if "text/event-stream" in request.headers.get("accept", ""):
        if await runner.get_state(session_id) is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return StreamingResponse(
            _compaction_event_stream(runner, session_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )
    result = await runner.compact_session(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


async def _compaction_event_stream(runner: Runner, session_id: str):  # noqa: ANN201
    """Forward measured Runner progress as one cancellation-safe SSE response."""
    queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=64)

    def publish(event: Any) -> None:
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(event)

    operation = asyncio.create_task(runner.compact_session(session_id, progress=publish))
    saw_terminal = False
    try:
        while not saw_terminal:
            if operation.done() and queue.empty():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
            except TimeoutError:
                yield ": keepalive\n\n"
                continue
            payload = asdict(event)
            if event.result is not None:
                payload["result"] = CompactResponse.model_validate(event.result).model_dump()
            yield f"event: {event.stage}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            saw_terminal = event.stage in {"completed", "skipped", "failed"}
        try:
            result = await operation
        except Exception:
            if not saw_terminal:
                raise
        else:
            if not saw_terminal:
                if "error" in result:
                    stage = "failed"
                    normalized_result = None
                    error_type = "SessionUnavailable"
                else:
                    stage = "completed" if result.get("compacted") else "skipped"
                    normalized_result = CompactResponse.model_validate(result).model_dump()
                    error_type = None
                payload = {
                    "operation_id": "",
                    "sequence": 1,
                    "stage": stage,
                    "completed_units": 0,
                    "total_units": 0,
                    "result": normalized_result,
                    "error_type": error_type,
                }
                yield f"event: {stage}\ndata: {json.dumps(payload)}\n\n"
    finally:
        if not operation.done():
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)


@app.post("/session/{session_id}/restore_compaction", response_model=RestoreCompactionResponse)
async def restore_compaction(session_id: str):  # noqa: ANN201
    """Undo the latest compaction while preserving all later turns."""
    result = await _runtime().runner.restore_last_compaction(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    if result.get("plugin_conflicts"):
        return JSONResponse(status_code=409, content=result)
    return result


@app.get("/session/{session_id}/debug_log")
def get_debug_log(
    session_id: str,
    limit: Annotated[int, Query(ge=1, le=MAX_READ_LIMIT)] = 200,
) -> list[dict]:
    """Raw sequential log of turn inputs, LLM calls, and state-operation markers.

    Entries preserve their actual order. LLM calls include retries and structured
    diagnostics; ``turn_input`` records the exact API payload before the first call.
    Replaces the old debug logging embedded in the turn response.
    """
    return read_entries(session_id, limit)


@app.post("/session/{session_id}/undo")
async def undo_turn(session_id: str) -> dict:
    """Undoes the last turn of the session."""
    result = await _runtime().runner.undo_turn(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/session/{session_id}/state")
async def get_state(session_id: str) -> dict:
    """Returns the complete session state."""
    game = await _runtime().runner.get_state(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Session not found")
    from src.models import game_state_to_dict

    return game_state_to_dict(game)


@app.get("/session/{session_id}/history")
async def get_history(
    session_id: str,
    limit: Annotated[int, Query(ge=1, le=MAX_READ_LIMIT)] = 50,
) -> list[dict]:
    """Returns the turn history of the session."""
    records = await _runtime().runner.get_history(session_id, limit=limit)
    return [
        {
            "turn_number": r.turn_number,
            "speaker": r.speaker,
            "content": r.content,
            "content_type": r.content_type,
        }
        for r in records
    ]


@app.get("/scenario-defaults")
def get_builtin_scenarios(name: str | None = None) -> dict:
    """Returns the default scenario for the UI to pre-fill."""
    from src.store.scenarios import list_builtin_scenarios, load_builtin_scenario

    defaults = list_builtin_scenarios()
    target_name = name
    if not target_name:
        target_name = defaults[0] if defaults else ""

    if not target_name:
        raise HTTPException(status_code=404, detail="No default scenario available.")

    scenario_val = load_builtin_scenario(target_name)
    if not scenario_val:
        raise HTTPException(status_code=404, detail=f"Default scenario '{target_name}' not found.")

    return {
        "scenarios": defaults,
        "scenario": scenario_val,
    }


@app.get("/config")
def get_runtime_config() -> dict:
    """Return the complete browser-editable config with its API key redacted."""
    return public_config(_runtime().stored_config)


@app.put("/config")
def put_runtime_config(body: dict[str, Any]) -> dict:
    """Atomically persist config.json and switch subsequent LLM calls to it."""
    runtime = _runtime()
    with runtime.config_lock:
        try:
            stored = merge_config_update(body)
        except ConfigValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        resolved = resolve_active_config(stored)
        runtime.stored_config = stored
        runtime.server_config = resolved
        runtime.runner = Runner(runtime.llm_client, resolved, runtime.plugins)
        return public_config(stored)


# ── Native character presets ───────────────────────────────────────────────


@app.get("/presets")
def get_presets() -> dict[str, Any]:
    from src.store.presets import list_presets

    return {"schema_version": 1, "presets": list_presets()}


@app.get("/presets/{preset_name}")
def get_preset(preset_name: str) -> dict[str, Any]:
    from src.store.presets import PresetError, load_preset

    try:
        value = load_preset(preset_name)
    except PresetError as error:
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": str(error)}
        ) from error
    if value is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    return value


@app.put("/presets/{preset_name}")
def put_preset(preset_name: str, body: PresetPutRequest) -> dict[str, Any]:
    from src.store.presets import PresetConflictError, PresetError, save_preset

    try:
        return save_preset(
            preset_name,
            character=body.character.model_dump(),
            avatar=body.avatar.model_dump() if body.avatar else None,
            expected_revision=body.expected_revision,
            replace=body.replace,
        )
    except PresetConflictError as error:
        raise HTTPException(
            status_code=409, detail={"code": error.code, "message": str(error)}
        ) from error
    except PresetError as error:
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": str(error)}
        ) from error


@app.delete("/presets/{preset_name}")
def remove_preset(
    preset_name: str, expected_revision: Annotated[int, Query(ge=1)]
) -> dict[str, bool]:
    from src.store.presets import PresetConflictError, PresetError, delete_preset

    try:
        deleted = delete_preset(preset_name, expected_revision=expected_revision)
    except PresetConflictError as error:
        raise HTTPException(
            status_code=409, detail={"code": error.code, "message": str(error)}
        ) from error
    except PresetError as error:
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": str(error)}
        ) from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"deleted": True}


@app.get("/presets/{preset_name}/avatar")
def get_preset_avatar(preset_name: str, request: Request) -> Response:
    from src.store.presets import PresetError, load_avatar

    try:
        value = load_avatar(preset_name)
    except PresetError as error:
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": str(error)}
        ) from error
    if value is None:
        raise HTTPException(status_code=404, detail="Preset avatar not found")
    data, sha256 = value
    etag = f'"{sha256}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return Response(
        content=data,
        media_type="image/webp",
        headers={"ETag": etag, "Cache-Control": "private, max-age=31536000, immutable"},
    )


# ── Scenarios API ──────────────────────────────────────────────────────────


@app.get("/scenarios")
def get_scenarios() -> list[str]:
    """Lists the names of all user scenarios."""
    from src.store.scenarios import list_scenarios

    return list_scenarios()


@app.get("/scenarios/{name}")
def get_scenario(name: str) -> dict:
    """Returns the complete scenario configuration."""
    from src.store.scenarios import load_user_scenario

    scenario_val = load_user_scenario(name)
    if scenario_val is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found.")
    return scenario_val


@app.put("/scenarios/{name}")
def put_scenario(name: str, body: StartSessionRequest) -> dict:
    """Saves or updates a user scenario."""
    from src.store.scenarios import save_scenario

    save_scenario(name, body.dict(exclude_none=True))
    return {"saved": True}


@app.delete("/scenarios/{name}")
def delete_scenario_endpoint(name: str) -> dict:
    """Removes a user scenario."""
    from src.store.scenarios import delete_scenario

    success = delete_scenario(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found.")
    return {"deleted": True}


@app.get("/sessions")
def get_sessions() -> list[dict]:
    """Lists all sessions with a summary."""
    return list_sessions()


@app.post("/session/{session_id}/fork")
async def fork_session_endpoint(session_id: str) -> dict:
    """Creates a copy of the session with a new ID."""
    new_id = await fork_session(session_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": new_id}


@app.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str) -> dict:
    """Removes a session."""
    if not await delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


# ── Plugin platform ─────────────────────────────────────────────────────


class PluginInstallRequest(BaseModel):
    zip_path: str


class PluginActivationRequest(BaseModel):
    version: str | None = None
    sha256: str | None = None


class PluginUpdateRequest(BaseModel):
    version: str
    sha256: str


@app.get("/plugins")
def get_plugins() -> dict[str, Any]:
    from src.plugins.store import plugin_inventory

    return {"plugins": plugin_inventory(), **_runtime().plugins.public_status()}


@app.get("/plugins/events")
def get_plugin_events(
    limit: Annotated[int, Query(ge=1, le=MAX_READ_LIMIT)] = 200,
) -> list[dict[str, Any]]:
    from src.plugins.journal import read

    return read(limit)


@app.post("/plugins/{plugin_id}/observe")
def observe_frontend_plugin(plugin_id: str, body: dict[str, Any]) -> dict[str, bool]:
    from src.plugins.journal import emit

    permission = body.pop("permission", "frontend.unknown")
    emit("permission_access", plugin_id, permission=permission, **body)
    return {"recorded": True}


@app.get("/plugins/{plugin_id}/config")
def get_plugin_config(plugin_id: str) -> dict[str, Any]:
    from src.plugins.sdk import PluginConfig

    return PluginConfig(plugin_id).read()


@app.put("/plugins/{plugin_id}/config")
def put_plugin_config(plugin_id: str, body: dict[str, Any]) -> dict[str, bool]:
    from src.plugins.sdk import PluginConfig

    PluginConfig(plugin_id).write(body)
    return {"saved": True}


@app.post("/plugins/install")
def install_plugin(body: PluginInstallRequest) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, install_zip

    try:
        return install_zip(Path(body.zip_path).expanduser().resolve())
    except PluginInstallError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/install-upload")
async def upload_plugin(request: Request) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, install_zip

    with tempfile.TemporaryDirectory(prefix="alex-tavern-upload-") as temporary:
        path = Path(temporary) / "plugin.zip"
        size = 0
        with path.open("wb") as handle:
            async for chunk in request.stream():
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=422, detail="Plugin ZIP exceeds 100 MiB")
                handle.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="Plugin ZIP is empty")
        try:
            return install_zip(path)
        except PluginInstallError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/inspect-upload")
async def inspect_uploaded_plugin(request: Request) -> dict[str, Any]:
    """Validate an external ZIP and expose its review contract without installing it."""
    from src.plugins.store import PluginInstallError, inspect_zip

    with tempfile.TemporaryDirectory(prefix="alex-tavern-inspect-") as temporary:
        path = Path(temporary) / "plugin.zip"
        size = 0
        with path.open("wb") as handle:
            async for chunk in request.stream():
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=422, detail="Plugin ZIP exceeds 100 MiB")
                handle.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="Plugin ZIP is empty")
        try:
            return inspect_zip(path)
        except PluginInstallError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/plugins/catalog")
def get_plugin_catalog(refresh: bool = False) -> dict[str, Any]:
    from src.plugins.hub import HubSyncError, ensure_hub_synced
    from src.plugins.store import PluginInstallError, curated_catalog

    try:
        ensure_hub_synced(force=refresh)
        return curated_catalog()
    except HubSyncError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (PluginInstallError, json.JSONDecodeError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/catalog/{plugin_id}/install")
def install_curated_plugin(plugin_id: str, version: str | None = None) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, install_curated

    try:
        return install_curated(plugin_id, version)
    except PluginInstallError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/catalog/{plugin_id}/update")
def update_curated_plugin(
    plugin_id: str,
    body: PluginUpdateRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, update_curated
    from src.supervisor import request_restart

    try:
        result = update_curated(plugin_id, body.version, body.sha256)
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    background_tasks.add_task(request_restart)
    return result


@app.post("/plugins/{plugin_id}/activate")
def activate_plugin(
    plugin_id: str,
    body: PluginActivationRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, switch_activation
    from src.supervisor import request_restart

    try:
        result = switch_activation(plugin_id, body.version, body.sha256)
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    background_tasks.add_task(request_restart)
    return {**result, "restart": True}


@app.post("/plugins/{plugin_id}/deactivate")
def deactivate_plugin(plugin_id: str, background_tasks: BackgroundTasks) -> dict[str, Any]:
    from src.plugins.store import deactivate, rebuild_environment
    from src.supervisor import request_restart

    changed = deactivate(plugin_id)
    environment = rebuild_environment()
    if changed:
        background_tasks.add_task(request_restart)
    return {"deactivated": changed, "environment": environment, "restart": changed}


@app.delete("/plugins/{plugin_id}/installations/{version}/{sha256}")
def uninstall_plugin(
    plugin_id: str,
    version: str,
    sha256: str,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    from src.plugins.store import PluginInstallError, rebuild_environment, uninstall
    from src.supervisor import request_restart

    try:
        result = uninstall(plugin_id, version, sha256)
        environment = rebuild_environment() if result["deactivated"] else None
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if result["deactivated"]:
        background_tasks.add_task(request_restart)
    return {
        "uninstalled": result,
        "environment": environment,
        "restart": result["deactivated"],
    }


@app.get("/plugins/assets/{plugin_id}/{relative_path:path}")
def plugin_asset(plugin_id: str, relative_path: str) -> FileResponse:
    path = _runtime().plugins.asset(plugin_id, relative_path)
    if path is None:
        raise HTTPException(status_code=404, detail="Plugin asset not found")
    return FileResponse(path)


@app.get("/experiences")
def get_experiences() -> list[dict[str, Any]]:
    from src.plugins.experiences import list_experiences

    return list_experiences()


@app.get("/experiences/assets/{relative_path:path}")
def experience_asset(relative_path: str) -> FileResponse:
    from src.paths import EXPERIENCES_DIR

    root = (EXPERIENCES_DIR / "assets").resolve()
    path = (root / relative_path).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Experience asset not found")
    return FileResponse(path)


@app.put("/experiences/{experience_id}")
def put_experience(experience_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from src.plugins.experiences import ExperienceError, save_experience

    if body.get("id") != experience_id:
        raise HTTPException(status_code=422, detail="Path and Experience id must match")
    try:
        experience = save_experience(body)
    except ExperienceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return experience.public_dict()


@app.post("/experiences/{experience_id}/activate")
def activate_experience_endpoint(
    experience_id: str, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    from src.plugins.experiences import ExperienceError, activate_experience
    from src.plugins.store import rebuild_environment
    from src.supervisor import request_restart

    try:
        result = activate_experience(experience_id)
        result["environment"] = rebuild_environment()
    except (ExperienceError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    background_tasks.add_task(request_restart)
    return result


def get_git_commit() -> str:
    """Reads the current git commit hash directly from the .git folder."""
    repo_root = Path(__file__).resolve().parent.parent
    git_dir = repo_root / ".git"
    version_file = repo_root / "version.txt"

    if not git_dir.exists() or not git_dir.is_dir():
        if version_file.exists():
            try:
                return version_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        return "unknown"

    head_file = git_dir / "HEAD"
    if not head_file.exists():
        return "unknown"

    try:
        head_content = head_file.read_text(encoding="utf-8").strip()
        if head_content.startswith("ref:"):
            ref_path = head_content[4:].strip()
            ref_file = git_dir / ref_path
            if ref_file.exists():
                return ref_file.read_text(encoding="utf-8").strip()

            # Fallback to packed-refs if ref file doesn't exist
            packed_refs_file = git_dir / "packed-refs"
            if packed_refs_file.exists():
                with open(packed_refs_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split(None, 1)
                        if len(parts) == 2 and parts[1] == ref_path:
                            return parts[0]
            return "unknown"
        else:
            return head_content
    except Exception:
        return "unknown"


@app.get("/version")
def get_version() -> dict:
    """Returns the current backend git commit hash."""
    return {"commit": get_git_commit()}


@app.get("/health")
def health() -> dict:
    """Simple health check."""
    return {"status": "ok"}


@app.get("/bootstrap_log")
def get_bootstrap_log() -> HTMLResponse:
    """Returns the Android bootstrap log for diagnostics."""
    log_path = DATA_DIR.parent / "bootstrap.log"
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        html_content = f"<html><body><h3>Bootstrap Log</h3><pre>{content}</pre></body></html>"
        return HTMLResponse(content=html_content, status_code=200)
    return HTMLResponse(content="<html><body><h3>Log not found</h3></body></html>", status_code=404)


# ── Static Files (frontend) ──────────────────────────────────────────────
# Mounted after API routes to avoid conflicts
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
