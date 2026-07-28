"""FastAPI server for the multi-agent roleplay system."""

from __future__ import annotations

import asyncio
import json
import tempfile
import threading
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.build_info import build_commit, debug_mode
from src.config import (
    ConfigValidationError,
    merge_config_update,
    public_config,
    resolve_active_config,
)
from src.llm.debug_log import read_entries
from src.models import Scene, dict_to_character, game_state_to_dict
from src.paths import EXPERIENCES_DIR, STATIC_DIR
from src.plugins.commands import CommandError
from src.plugins.experiences import (
    ExperienceError,
    activate_experience,
    list_experiences,
    save_experience,
)
from src.plugins.hub import HubSyncError, ensure_hub_synced
from src.plugins.journal import emit, read
from src.plugins.runtime import PluginRuntime
from src.plugins.sdk import PluginConfig
from src.plugins.store import (
    PluginInstallError,
    curated_catalog,
    deactivate,
    inspect_zip,
    install_curated,
    install_zip,
    plugin_inventory,
    rebuild_environment,
    switch_activation,
    uninstall,
    update_curated,
)
from src.pydantic_compat import StrictModel, dump, validate
from src.runner import ConversationAlreadyStartedError, PresenceRevisionConflictError, Runner
from src.runtime_bootstrap import prepare_runtime_config
from src.security import (
    ACCESS_TOKEN_HEADER,
    generate_access_token,
    unsafe_request_allowed,
)
from src.store.presets import (
    PresetConflictError,
    PresetError,
    delete_preset,
    list_presets,
    load_avatar,
    load_preset,
    save_preset,
)
from src.store.scenarios import (
    delete_scenario,
    list_builtin_scenarios,
    list_scenarios,
    load_builtin_scenario,
    load_scenario,
    load_user_scenario,
    save_scenario,
)
from src.store.sessions import (
    IncompatibleSessionError,
    SessionNotFoundError,
    delete_session,
    fork_session,
    list_sessions,
)
from src.supervisor import request_restart

MAX_READ_LIMIT = 1000
# Bound enforced while an upload streams, so an oversized ZIP is never buffered.
MAX_PLUGIN_ZIP_BYTES = 100 * 1024 * 1024
# Seconds between SSE keepalive comments while a compaction runs.
COMPACTION_KEEPALIVE_SECONDS = 15


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
    stored_config = prepare_runtime_config()
    plugins = PluginRuntime()
    plugins.boot()
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


@app.exception_handler(IncompatibleSessionError)
async def incompatible_session_handler(
    request: Request, exc: IncompatibleSessionError
) -> JSONResponse:
    """Refuse any operation on a session persisted with an outdated schema.

    Deliberate no-migration policy (alpha): the session stays on disk, is listed
    with ``compatible: false``, and can never be opened by this build.
    """
    return JSONResponse(
        status_code=409,
        content={
            "error": "incompatible_session",
            "detail": str(exc),
            "session_id": exc.session_id,
            "found_version": exc.found_version,
            "current_version": exc.current_version,
        },
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError) -> JSONResponse:
    """Answer 404 for every operation on a session that does not exist."""
    return JSONResponse(
        status_code=404,
        content={"error": "session_not_found", "detail": str(exc), "session_id": exc.session_id},
    )


@app.exception_handler(ConversationAlreadyStartedError)
async def conversation_started_handler(
    request: Request, exc: ConversationAlreadyStartedError
) -> JSONResponse:
    """Opening-only operations are a conflict once the story has begun."""
    return JSONResponse(
        status_code=409,
        content={"code": "conversation_started", "message": str(exc)},
    )


@app.exception_handler(ValueError)
async def invalid_request_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Turn a domain rule violation into 422, the same status a schema error gets.

    Validation of MEANING lives in the domain (see ``PlayerTurnRequest``), so it
    reaches HTTP as an exception rather than a pydantic error. Subclasses that
    carry their own status handle it themselves and never reach here.
    """
    return JSONResponse(status_code=422, content={"error": "invalid_request", "detail": str(exc)})


def _runtime() -> RuntimeState:
    """Return initialized application state or fail clearly outside lifespan."""
    runtime = getattr(app.state, "runtime", None)
    if not isinstance(runtime, RuntimeState):
        raise RuntimeError("Application runtime is not initialized")
    return runtime


# Per-process access token (Task 19): never persisted, never logged. The served
# same-origin app fetches it from /bootstrap and returns it on every mutation; a
# cross-origin page cannot read it, so it cannot forge a state-changing request.
ACCESS_TOKEN = generate_access_token()

# Origins the browser may drive unsafe endpoints from: loopback on any port
# (desktop/Docker/dev). Native/WebView clients send no Origin or "null" and are
# handled by the security middleware. This replaces credentialed wildcard CORS.
_LOOPBACK_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    # NEVER allow the "null" origin here: a sandboxed attacker iframe also has
    # Origin "null", and allowing it to READ /bootstrap would hand it the access
    # token and defeat the whole boundary. Android/WebView clients that load the
    # document from file:// must either serve the app same-origin from this
    # server or use a WebView mode that is not subject to CORS; both paths keep
    # working because the unsafe gate itself admits a null/absent Origin WITH a
    # valid token. Same-origin browser use (localhost, LAN IP, Docker) never
    # needs CORS at all.
    allow_origin_regex=_LOOPBACK_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", ACCESS_TOKEN_HEADER],
)


@app.middleware("http")
async def enforce_origin_and_token(request: Request, call_next):  # noqa: ANN001, ANN201
    """Reject cross-origin/untokened state-changing requests (Task 19).

    Safe methods pass. Every unsafe method (session/config/scenario/plugin/
    Experience mutations alike) requires the access token AND a loopback/native
    Origin, so an arbitrary web page cannot reach these endpoints.
    """
    if not unsafe_request_allowed(
        request.method,
        request.headers.get("origin"),
        request.headers.get(ACCESS_TOKEN_HEADER),
        ACCESS_TOKEN,
        host=request.headers.get("host"),
    ):
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "detail": "invalid origin or access token"},
        )
    return await call_next(request)


@app.get("/bootstrap")
def bootstrap() -> dict:
    """Deliver the per-process access token to the served app.

    Browser pages can read this only same-origin or from a loopback origin (the
    CORS policy above allows nothing else — in particular never the "null"
    origin, which sandboxed attacker iframes share). Native clients and
    CORS-exempt WebViews read it directly; they are trusted local callers.
    """
    return {"access_token": ACCESS_TOKEN}


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
    zones: dict[str, list[str]] = Field(default_factory=dict)
    positions: dict[str, str] = Field(default_factory=dict)


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


class SessionSetupUpdateRequest(BaseModel):
    controlled_character_id: str
    characters: dict[str, CharacterInput]
    scene: SceneInput
    narrator_directives: str = ""
    character_preset_ids: dict[str, str] = Field(default_factory=dict)
    expected_revision: int = Field(ge=0)


class PlayerTurnRequest(StrictModel):
    """The SHAPE of a turn submission; its rules live in ``Runner.player_turn``.

    Keeping the two apart is deliberate: what makes a turn valid (skip excludes
    content, a whisper needs something audible, an audience must be present) is
    domain law that every caller must obey, not only the HTTP one.
    """

    speech: str = ""
    thought: str = ""
    action: str = ""
    force_speaker: str | None = None
    narrator_hint: str = ""
    skip: bool = False
    # Whisper: character IDs that perceive this turn's speech/action. None = public.
    audience: list[str] | None = None


class PresenceUpdateRequest(StrictModel):
    present_characters: list[str]
    expected_revision: int = Field(ge=0)


class CommandFileInput(StrictModel):
    name: str
    media_type: str = "application/octet-stream"
    data_base64: str


class CommandRequest(StrictModel):
    values: dict[str, str] = Field(default_factory=dict)
    files: dict[str, CommandFileInput] = Field(default_factory=dict)


class AvatarInput(StrictModel):
    media_type: Literal["image/webp"]
    data_base64: str


class PresetPutRequest(StrictModel):
    character: CharacterInput
    avatar: AvatarInput | None = None
    expected_revision: int | None = Field(default=None, ge=1)
    replace: bool = False


class EffectiveTurnInput(BaseModel):
    speech: str
    thought: str
    action: str


class CharacterTurnEntry(BaseModel):
    character_id: str
    speech: str | None = None
    thought: str | None = None
    action_intent: str | None = None


class BeatResult(BaseModel):
    narration: str | None = None
    character_responses: list[CharacterTurnEntry] = Field(default_factory=list)
    next_speakers: list[str] = Field(default_factory=list)
    scene_update: dict | None = None
    turn_number: int | None = None


class PlayerTurnResponse(BaseModel):
    narration: str | None = None
    character_responses: list[CharacterTurnEntry] = Field(default_factory=list)
    next_speakers: list[str] = Field(default_factory=list)
    beats: list[BeatResult] | None = None
    burst_stop_reason: str | None = None
    scene_update: dict | None = None
    turn_number: int | None = None
    effective_input: EffectiveTurnInput | None = None
    transformed_fields: list[Literal["speech", "thought", "action"]] = Field(default_factory=list)
    automatic_compaction: dict[str, Any] | None = None
    error: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[dict] | None = None
    error: str | None = None


class OpeningSuggestionsResponse(BaseModel):
    suggestions: list[str]


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
            characters[cid] = dict_to_character(dump(ci))
    elif scenario_data:
        refs = scenario_data.get("character_preset_ids")
        if not isinstance(refs, dict) or not refs:
            raise HTTPException(
                status_code=422,
                detail="Scenario must link at least one character preset.",
            )
        for cid, preset_name in refs.items():
            try:
                preset = load_preset(preset_name)
            except PresetError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            if preset is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Scenario character preset '{preset_name}' was not found.",
                )
            characters[cid] = dict_to_character(preset["character"])

    scene = None
    if req.scene is not None:
        scene = Scene(
            location=req.scene.location,
            time_of_day=req.scene.time_of_day,
            present_characters=list(req.scene.present_characters),
            physical_facts=dict(req.scene.physical_facts),
            zones={z: list(a) for z, a in req.scene.zones.items()},
            positions=dict(req.scene.positions),
        )
    elif "scene" in scenario_data:
        sdata = scenario_data["scene"]
        scene = Scene(
            location=sdata["location"],
            time_of_day=sdata["time_of_day"],
            present_characters=list(sdata.get("present_characters", [])),
            physical_facts=dict(sdata.get("physical_facts", {})),
            zones={z: list(a) for z, a in sdata.get("zones", {}).items()},
            positions=dict(sdata.get("positions", {})),
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
        "scenario_source_id": req.scenario_name or "",
    }
    if characters:
        cfg["characters"] = characters
    if scene:
        cfg["scene"] = scene

    try:
        session_id = await active_runner.start_session(cfg)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    game = await active_runner.get_state(session_id)
    if game is None:  # pragma: no cover - the session was just committed
        raise RuntimeError(f"Session {session_id} vanished right after creation")
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
        audience=body.audience,
    )
    return result


@app.get("/commands")
def get_commands() -> dict[str, Any]:
    """Return the executable command catalog for slash autocomplete and forms."""
    return {"schema_version": 2, "commands": _runtime().plugins.commands.public_catalog()}


@app.post("/session/{session_id}/commands/{command_name}")
async def execute_command(
    session_id: str, command_name: str, body: CommandRequest
) -> dict[str, Any]:
    """Execute a non-narrative plugin command under the session lock."""

    try:
        return await _runtime().runner.execute_command(session_id, command_name, dump(body))
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
    return await _runtime().runner.suggest_actions(session_id)


@app.post(
    "/session/{session_id}/opening-suggestions",
    response_model=OpeningSuggestionsResponse,
)
async def suggest_openings(session_id: str) -> dict:
    """Return three scenario-only opening hints for an empty session."""
    return await _runtime().runner.suggest_openings(session_id)


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
    return await runner.compact_session(session_id)


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
                event = await asyncio.wait_for(
                    queue.get(), timeout=COMPACTION_KEEPALIVE_SECONDS
                )
            except TimeoutError:
                yield ": keepalive\n\n"
                continue
            payload = asdict(event)
            if event.result is not None:
                payload["result"] = dump(validate(CompactResponse, event.result))
            yield f"event: {event.stage}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            saw_terminal = event.stage in {"completed", "skipped", "failed"}
        try:
            result = await operation
        except Exception:
            if not saw_terminal:
                raise
        else:
            if not saw_terminal:
                stage = "completed" if result.get("compacted") else "skipped"
                normalized_result = dump(validate(CompactResponse, result))
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
    return await _runtime().runner.undo_turn(session_id)


@app.post("/session/{session_id}/presence")
async def set_presence(session_id: str, body: PresenceUpdateRequest) -> dict:
    """Administrative presence edit — no turn, no LLM call, no history entry."""
    try:
        result = await _runtime().runner.set_presence(
            session_id, body.present_characters, body.expected_revision
        )
    except PresenceRevisionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return result


@app.post("/session/{session_id}/presence/undo")
async def undo_presence(session_id: str) -> dict:
    """Undo the newest out-of-band admin presence edit (strictly LIFO)."""
    return await _runtime().runner.undo_last_presence_edit(session_id)


@app.get("/session/{session_id}/state")
async def get_state(session_id: str) -> dict:
    """Returns the complete session state."""
    game = await _runtime().runner.get_state(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return game_state_to_dict(game)


@app.put("/session/{session_id}/setup")
async def update_session_setup(session_id: str, body: SessionSetupUpdateRequest) -> dict:
    """Edit the independent runtime snapshot without mutating its source records."""
    characters = {
        cid: dict_to_character(dump(character)) for cid, character in body.characters.items()
    }
    scene = Scene(
        location=body.scene.location,
        time_of_day=body.scene.time_of_day,
        present_characters=list(body.scene.present_characters),
        physical_facts=dict(body.scene.physical_facts),
        zones={zone: list(audible) for zone, audible in body.scene.zones.items()},
        positions=dict(body.scene.positions),
    )
    try:
        return await _runtime().runner.update_session_setup(
            session_id,
            characters=characters,
            scene=scene,
            narrator_directives=body.narrator_directives,
            character_preset_ids=dict(body.character_preset_ids),
            controlled_character_id=body.controlled_character_id,
            expected_revision=body.expected_revision,
        )
    except PresenceRevisionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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

    return {"schema_version": 1, "presets": list_presets()}


@app.get("/presets/{preset_name}")
def get_preset(preset_name: str) -> dict[str, Any]:

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

    try:
        return save_preset(
            preset_name,
            character=dump(body.character),
            avatar=dump(body.avatar) if body.avatar else None,
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

    return list_scenarios()


@app.get("/scenarios/{name}")
def get_scenario(name: str) -> dict:
    """Returns the complete scenario configuration."""

    scenario_val = load_user_scenario(name)
    if scenario_val is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found.")
    return scenario_val


@app.put("/scenarios/{name}")
def put_scenario(name: str, body: StartSessionRequest) -> dict:
    """Saves or updates a user scenario."""

    linked_presets = list(body.character_preset_ids.values())
    if len(set(linked_presets)) != len(linked_presets):
        raise HTTPException(
            status_code=422,
            detail="A scenario cannot link the same character preset twice.",
        )
    save_scenario(name, dump(body, exclude_none=True))
    return {"saved": True}


@app.delete("/scenarios/{name}")
def delete_scenario_endpoint(name: str) -> dict:
    """Removes a user scenario."""

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

    return {"plugins": plugin_inventory(), **_runtime().plugins.public_status()}


@app.get("/plugins/events")
def get_plugin_events(
    limit: Annotated[int, Query(ge=1, le=MAX_READ_LIMIT)] = 200,
) -> list[dict[str, Any]]:

    return read(limit)


@app.post("/plugins/{plugin_id}/observe")
def observe_frontend_plugin(plugin_id: str, body: dict[str, Any]) -> dict[str, bool]:

    permission = body.pop("permission", "frontend.unknown")
    emit("permission_access", plugin_id, permission=permission, **body)
    return {"recorded": True}


@app.get("/plugins/{plugin_id}/config")
def get_plugin_config(plugin_id: str) -> dict[str, Any]:

    return PluginConfig(plugin_id).read()


@app.put("/plugins/{plugin_id}/config")
def put_plugin_config(plugin_id: str, body: dict[str, Any]) -> dict[str, bool]:

    PluginConfig(plugin_id).write(body)
    return {"saved": True}


@app.post("/plugins/install")
def install_plugin(body: PluginInstallRequest) -> dict[str, Any]:

    try:
        return install_zip(Path(body.zip_path).expanduser().resolve())
    except PluginInstallError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


async def _receive_plugin_zip(
    request: Request,
    handler: Callable[[Path], dict[str, Any]],
    *,
    prefix: str,
) -> dict[str, Any]:
    """Stream an uploaded ZIP to a temporary file and hand it to ``handler``.

    The body is bounded while it streams, so an oversized upload is refused
    without ever being fully buffered or written.
    """
    with tempfile.TemporaryDirectory(prefix=prefix) as temporary:
        path = Path(temporary) / "plugin.zip"
        size = 0
        with path.open("wb") as handle:
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_PLUGIN_ZIP_BYTES:
                    raise HTTPException(status_code=422, detail="Plugin ZIP exceeds 100 MiB")
                handle.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="Plugin ZIP is empty")
        try:
            return handler(path)
        except PluginInstallError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/install-upload")
async def upload_plugin(request: Request) -> dict[str, Any]:

    return await _receive_plugin_zip(request, install_zip, prefix="alex-tavern-upload-")


@app.post("/plugins/inspect-upload")
async def inspect_uploaded_plugin(request: Request) -> dict[str, Any]:
    """Validate an external ZIP and expose its review contract without installing it."""

    return await _receive_plugin_zip(request, inspect_zip, prefix="alex-tavern-inspect-")


@app.get("/plugins/catalog")
def get_plugin_catalog(refresh: bool = False) -> dict[str, Any]:

    try:
        ensure_hub_synced(force=refresh)
        return curated_catalog()
    except HubSyncError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (PluginInstallError, json.JSONDecodeError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/catalog/{plugin_id}/install")
def install_curated_plugin(plugin_id: str, version: str | None = None) -> dict[str, Any]:

    try:
        return install_curated(plugin_id, version)
    except PluginInstallError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/plugins/catalog/{plugin_id}/update")
def update_curated_plugin(
    plugin_id: str,
    body: PluginUpdateRequest,
) -> dict[str, Any]:

    try:
        result = update_curated(plugin_id, body.version, body.sha256)
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return result


@app.post("/plugins/{plugin_id}/activate")
def activate_plugin(
    plugin_id: str,
    body: PluginActivationRequest,
) -> dict[str, Any]:

    try:
        result = switch_activation(plugin_id, body.version, body.sha256)
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {**result, "restart": True}


@app.post("/plugins/{plugin_id}/deactivate")
def deactivate_plugin(plugin_id: str) -> dict[str, Any]:

    changed = deactivate(plugin_id)
    environment = rebuild_environment()
    return {"deactivated": changed, "environment": environment, "restart": changed}


@app.delete("/plugins/{plugin_id}/installations/{version}/{sha256}")
def uninstall_plugin(
    plugin_id: str,
    version: str,
    sha256: str,
) -> dict[str, Any]:

    try:
        result = uninstall(plugin_id, version, sha256)
        environment = rebuild_environment() if result["deactivated"] else None
    except (PluginInstallError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "uninstalled": result,
        "environment": environment,
        "restart": result["deactivated"],
    }


@app.post("/plugins/restart")
def restart_plugins(background_tasks: BackgroundTasks) -> dict[str, bool]:
    """Apply the persisted active set by replacing the supervised server process."""

    background_tasks.add_task(request_restart)
    return {"restart": True}


@app.get("/plugins/assets/{plugin_id}/{relative_path:path}")
def plugin_asset(plugin_id: str, relative_path: str) -> FileResponse:
    path = _runtime().plugins.asset(plugin_id, relative_path)
    if path is None:
        raise HTTPException(status_code=404, detail="Plugin asset not found")
    return FileResponse(path)


@app.get("/experiences")
def get_experiences() -> list[dict[str, Any]]:

    return list_experiences()


@app.get("/experiences/assets/{relative_path:path}")
def experience_asset(relative_path: str) -> FileResponse:

    root = (EXPERIENCES_DIR / "assets").resolve()
    path = (root / relative_path).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Experience asset not found")
    return FileResponse(path)


@app.put("/experiences/{experience_id}")
def put_experience(experience_id: str, body: dict[str, Any]) -> dict[str, Any]:

    if body.get("id") != experience_id:
        raise HTTPException(status_code=422, detail="Path and Experience id must match")
    try:
        experience = save_experience(body)
    except ExperienceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return experience.public_dict()


@app.post("/experiences/{experience_id}/activate")
def activate_experience_endpoint(
    experience_id: str,
) -> dict[str, Any]:

    try:
        result = activate_experience(experience_id)
        result["environment"] = rebuild_environment()
    except (ExperienceError, OSError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return result


@app.get("/version")
def get_version() -> dict:
    """Returns the current build identity and development-mode status."""
    return {"commit": build_commit(), "debug": debug_mode()}


@app.get("/health")
def health() -> dict:
    """Simple health check."""
    return {"status": "ok"}


# ── Static Files (frontend) ──────────────────────────────────────────────
# Mounted after API routes to avoid conflicts
# Mounted conditionally: on Android the frontend may not be packaged alongside
# the Python sources, and StaticFiles raises on every request to a missing
# directory. Skipping the mount makes "/" a clean 404, which is the signal the
# Android launcher uses to load the frontend from the APK assets instead.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
