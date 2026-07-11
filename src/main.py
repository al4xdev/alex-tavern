"""FastAPI server para o sistema de roleplay multi-agente."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.runner import Runner

# ── Config ────────────────────────────────────────────────────────────────

SERVER_CONFIG: dict[str, Any] = {
    "llm_host": "http://localhost:8888",
    "context_max": 98304,
    "temperature_narrator": 0.0,
    "temperature_character": 0.8,
    "max_tokens_narrator": 1024,
    "max_tokens_character": 256,
}

llm_client: httpx.AsyncClient | None = None
runner: Runner | None = None


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    global llm_client, runner  # noqa: PLW0603
    llm_client = httpx.AsyncClient(
        base_url=SERVER_CONFIG["llm_host"],
        timeout=httpx.Timeout(60.0),
    )
    runner = Runner(llm_client, SERVER_CONFIG)
    yield
    await llm_client.aclose()


app = FastAPI(lifespan=lifespan)

# CORS — permitir tudo no MVP (frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────


class StartSessionRequest(BaseModel):
    player_name: str | None = None
    controlled_character_id: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    state: dict


class PlayerTurnRequest(BaseModel):
    speech: str = ""
    action: str = ""
    chosen_option: int | None = Field(default=None, ge=0)


class PlayerTurnResponse(BaseModel):
    narration: str | None = None
    character_response: str | None = None
    next_speaker: str | None = None
    player_options: list[dict] | None = None
    scene_update: dict | None = None
    turn_number: int | None = None
    type: str | None = None
    options: list[dict] | None = None
    error: str | None = None


# ── Rotas ─────────────────────────────────────────────────────────────────


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest) -> dict:
    """Cria uma nova sessão de roleplay."""
    assert runner is not None, "Runner não inicializado"
    cfg: dict[str, Any] = {}
    if req.player_name:
        cfg["player_name"] = req.player_name
    if req.controlled_character_id:
        cfg["controlled_character_id"] = req.controlled_character_id
    session_id = runner.start_session(cfg)
    # Carrega o estado completo para retornar junto (evita GET /state extra)
    game = runner.get_state(session_id)
    assert game is not None, "Sessão recém-criada deveria existir"
    from src.models import game_state_to_dict
    return {"session_id": session_id, "state": game_state_to_dict(game)}


@app.post("/session/{session_id}/turn", response_model=PlayerTurnResponse)
async def player_turn(session_id: str, body: PlayerTurnRequest) -> dict:
    """Processa um turno do Player."""
    assert runner is not None, "Runner não inicializado"
    result = await runner.player_turn(
        session_id=session_id,
        speech=body.speech,
        action=body.action,
        chosen_option=body.chosen_option,
    )
    return result


@app.get("/session/{session_id}/state")
def get_state(session_id: str) -> dict:
    """Retorna o estado completo da sessão."""
    assert runner is not None, "Runner não inicializado"
    game = runner.get_state(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    from src.models import game_state_to_dict
    return game_state_to_dict(game)


@app.get("/session/{session_id}/history")
def get_history(session_id: str, limit: int = 50) -> list[dict]:
    """Retorna o histórico de turnos da sessão."""
    assert runner is not None, "Runner não inicializado"
    records = runner.get_history(session_id, limit=limit)
    return [
        {
            "turn_number": r.turn_number,
            "speaker": r.speaker,
            "content": r.content,
            "content_type": r.content_type,
        }
        for r in records
    ]


@app.get("/health")
def health() -> dict:
    """Health check simples."""
    return {"status": "ok"}


# ── Static Files (frontend) ──────────────────────────────────────────────
# Montado depois das rotas da API para não conflitar
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
