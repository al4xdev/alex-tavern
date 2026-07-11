"""FastAPI server para o sistema de roleplay multi-agente."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.runner import Runner
from src.store.sessions import delete_session, fork_session, list_sessions

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


class CharacterInput(BaseModel):
    name: str
    personality_summary: str = ""
    personality_full: str = ""
    knowledge: list[str] = Field(default_factory=list)
    current_mood: str = ""
    physical_description: str = ""
    outfit: str = ""


class SceneInput(BaseModel):
    location: str = ""
    time_of_day: str = ""
    physical_facts: dict[str, str] = Field(default_factory=dict)


class StartSessionRequest(BaseModel):
    player_name: str | None = None
    controlled_character_id: str | None = None
    characters: dict[str, CharacterInput] | None = None
    scene: SceneInput | None = None
    narrator_directives: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    state: dict


class PlayerTurnRequest(BaseModel):
    speech: str = ""
    action: str = ""
    chosen_option: int | None = Field(default=None, ge=0)
    debug: bool = False


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
    debug: dict | None = None


class PreviewPromptRequest(BaseModel):
    speech: str = ""
    action: str = ""


# ── Rotas ─────────────────────────────────────────────────────────────────


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest) -> dict:
    """Cria uma nova sessão de roleplay."""
    assert runner is not None, "Runner não inicializado"
    from src.models import Scene, dict_to_character, game_state_to_dict

    cfg: dict[str, Any] = {}
    if req.player_name:
        cfg["player_name"] = req.player_name
    if req.controlled_character_id:
        cfg["controlled_character_id"] = req.controlled_character_id
    if req.narrator_directives is not None:
        cfg["narrator_directives"] = req.narrator_directives

    if req.characters:
        characters = {}
        for cid, ci in req.characters.items():
            characters[cid] = dict_to_character(
                {
                    "mind": {
                        "name": ci.name,
                        "personality_summary": ci.personality_summary,
                        "personality_full": ci.personality_full,
                        "knowledge": ci.knowledge,
                        "current_mood": ci.current_mood,
                    },
                    "body": {
                        "name": ci.name,
                        "physical_description": ci.physical_description,
                        "outfit": ci.outfit,
                    },
                }
            )
        cfg["characters"] = characters

    if req.scene is not None:
        cfg["scene"] = Scene(
            location=req.scene.location,
            time_of_day=req.scene.time_of_day,
            present_characters=[],  # recomputado pelo runner
            physical_facts=dict(req.scene.physical_facts),
        )

    try:
        session_id = runner.start_session(cfg)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Carrega o estado completo para retornar junto (evita GET /state extra)
    game = runner.get_state(session_id)
    assert game is not None, "Sessão recém-criada deveria existir"
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
        debug=body.debug,
    )
    return result


@app.post("/session/{session_id}/undo")
async def undo_turn(session_id: str) -> dict:
    """Desfaz o último turno da sessão."""
    assert runner is not None, "Runner não inicializado"
    result = await runner.undo_turn(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
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


@app.get("/defaults")
def get_defaults() -> dict:
    """Retorna o preset Thorn & Lyra (personagens + cena) para a UI pré-preencher."""
    from dataclasses import asdict

    from src.runner import DEFAULT_CHARACTERS, DEFAULT_SCENE
    return {
        "characters": {cid: asdict(ch) for cid, ch in DEFAULT_CHARACTERS.items()},
        "scene": asdict(DEFAULT_SCENE),
    }


@app.post("/session/{session_id}/preview_prompt")
def preview_prompt(session_id: str, body: PreviewPromptRequest) -> dict:
    """Retorna os messages do Narrador para o estado atual — sem chamar o LLM."""
    assert runner is not None, "Runner não inicializado"
    messages = runner.preview_narrator_prompt(
        session_id, speech=body.speech, action=body.action
    )
    if not messages:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"narrator_messages": messages}




@app.get("/sessions")
def get_sessions() -> list[dict]:
    """Lista todas as sessões com resumo."""
    return list_sessions()


@app.post("/session/{session_id}/fork")
def fork_session_endpoint(session_id: str) -> dict:
    """Cria cópia da sessão com novo ID."""
    new_id = fork_session(session_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"session_id": new_id}


@app.delete("/session/{session_id}")
def delete_session_endpoint(session_id: str) -> dict:
    """Remove uma sessão."""
    path = Path(f".data/sessions/{session_id}.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    delete_session(session_id)
    return {"deleted": True}


@app.get("/health")
def health() -> dict:
    """Health check simples."""
    return {"status": "ok"}


# ── Static Files (frontend) ──────────────────────────────────────────────
# Montado depois das rotas da API para não conflitar
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
