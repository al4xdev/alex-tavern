"""FastAPI server para o sistema de roleplay multi-agente."""

from __future__ import annotations

import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Annotated, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from src.config import (
    ConfigValidationError,
    load_config,
    merge_config_update,
    public_config,
    resolve_active_config,
)
from src.llm.debug_log import read_entries
from src.paths import DATA_DIR
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
    config_lock: threading.RLock = field(default_factory=threading.RLock)


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    stored_config = load_config()
    server_config = resolve_active_config(stored_config)
    llm_client = httpx.AsyncClient()
    app.state.runtime = RuntimeState(
        stored_config=stored_config,
        server_config=server_config,
        llm_client=llm_client,
        runner=Runner(llm_client, server_config),
    )
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
    preset_name: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    state: dict


class PlayerTurnRequest(BaseModel):
    speech: str = ""
    thought: str = ""
    action: str = ""
    force_speaker: str | None = None

    @model_validator(mode="after")
    def require_content(self) -> PlayerTurnRequest:
        if not any(value.strip() for value in (self.speech, self.thought, self.action)):
            raise ValueError("A turn needs speech, thought, or action")
        return self


class CharacterResponse(BaseModel):
    speech: str | None = None
    thought: str | None = None


class PlayerTurnResponse(BaseModel):
    narration: str | None = None
    character_response: CharacterResponse | None = None
    next_speaker: str | None = None
    scene_update: dict | None = None
    turn_number: int | None = None
    error: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[dict] | None = None
    error: str | None = None


class CompactResponse(BaseModel):
    compacted: bool
    reason: str | None = None
    backup_path: str | None = None
    evicted_turns: int | None = None
    kept_turns: int | None = None
    error: str | None = None


class RestoreCompactionResponse(BaseModel):
    restored: bool
    reason: str | None = None
    history_length: int | None = None
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
    from src.store.presets import list_defaults, load_default, load_preset

    preset_data: dict[str, Any] = {}
    if req.preset_name:
        preset_val = load_preset(req.preset_name)
        if preset_val is None:
            raise HTTPException(status_code=404, detail=f"Preset '{req.preset_name}' not found.")
        preset_data = preset_val

    if not preset_data and not req.characters and not req.scene:
        defaults = list_defaults()
        if defaults:
            first_def = load_default(defaults[0])
            if first_def:
                preset_data = first_def

    characters = {}
    if req.characters:
        for cid, ci in req.characters.items():
            characters[cid] = dict_to_character(ci.dict())
    elif "characters" in preset_data:
        for cid, cdata in preset_data["characters"].items():
            characters[cid] = dict_to_character(cdata)

    scene = None
    if req.scene is not None:
        scene = Scene(
            location=req.scene.location,
            time_of_day=req.scene.time_of_day,
            present_characters=[],  # recomputed by the runner
            physical_facts=dict(req.scene.physical_facts),
        )
    elif "scene" in preset_data:
        sdata = preset_data["scene"]
        scene = Scene(
            location=sdata["location"],
            time_of_day=sdata["time_of_day"],
            present_characters=list(sdata.get("present_characters", [])),
            physical_facts=dict(sdata.get("physical_facts", {})),
        )

    directives = ""
    if req.narrator_directives is not None:
        directives = req.narrator_directives
    elif "narrator_directives" in preset_data:
        directives = preset_data["narrator_directives"]

    controlled_id = ""
    if req.controlled_character_id:
        controlled_id = req.controlled_character_id
    elif "controlled_character_id" in preset_data:
        controlled_id = preset_data["controlled_character_id"]

    cfg: dict[str, Any] = {
        "controlled_character_id": controlled_id,
        "narrator_directives": directives,
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
    )
    return result


@app.post("/session/{session_id}/suggest", response_model=SuggestResponse)
async def suggest_actions(session_id: str) -> dict:
    """Possible move suggestions from the Narrator for the controlled character (manual trigger)."""
    result = await _runtime().runner.suggest_actions(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/session/{session_id}/compact", response_model=CompactResponse)
async def compact_session(session_id: str) -> dict:
    """Compacts the session: summarizes old turns, keeps only the most recent ones.

    Manual trigger (no automatic trigger in this version) — overwrites the
    active history. See ``Runner.compact_session`` for full
    behavior (backup, window, post-compaction undo).
    """
    result = await _runtime().runner.compact_session(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/session/{session_id}/restore_compaction", response_model=RestoreCompactionResponse)
async def restore_compaction(session_id: str) -> dict:
    """Undoes the last compaction, restoring the most recent backup.

    ⚠️ Only restores if no new turns have been played since that compaction —
    otherwise it refuses (see ``Runner.restore_last_compaction``), to
    never discard actual turns.
    """
    result = await _runtime().runner.restore_last_compaction(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
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


@app.get("/defaults")
def get_defaults(name: str | None = None) -> dict:
    """Returns the default preset for the UI to pre-fill."""
    from src.store.presets import list_defaults, load_default

    defaults = list_defaults()
    target_name = name
    if not target_name:
        target_name = defaults[0] if defaults else ""

    if not target_name:
        raise HTTPException(status_code=404, detail="No default preset available.")

    preset_val = load_default(target_name)
    if not preset_val:
        raise HTTPException(status_code=404, detail=f"Default preset '{target_name}' not found.")

    return {
        "presets": defaults,
        "preset": preset_val,
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
        runtime.runner = Runner(runtime.llm_client, resolved)
        return public_config(stored)


# ── Presets API ──────────────────────────────────────────────────────────


@app.get("/presets")
def get_presets() -> list[str]:
    """Lists the names of all user presets."""
    from src.store.presets import list_presets

    return list_presets()


@app.get("/presets/{name}")
def get_preset(name: str) -> dict:
    """Returns the complete preset configuration."""
    from src.store.presets import load_user_preset

    preset_val = load_user_preset(name)
    if preset_val is None:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found.")
    return preset_val


@app.put("/presets/{name}")
def put_preset(name: str, body: StartSessionRequest) -> dict:
    """Saves or updates a user preset."""
    from src.store.presets import save_preset

    save_preset(name, body.dict(exclude_none=True))
    return {"saved": True}


@app.delete("/presets/{name}")
def delete_preset_endpoint(name: str) -> dict:
    """Removes a user preset."""
    from src.store.presets import delete_preset

    success = delete_preset(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found.")
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
