"""FastAPI server para o sistema de roleplay multi-agente."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.runner import Runner
from src.store.sessions import delete_session, fork_session, list_sessions

CONFIG_PATH = Path(".data/config.json")
DEFAULT_CONFIG = {
    "llm_host": "http://localhost:8888",
    "model": "",
    "context_max": 98304,
    "max_tokens_narrator": 2048,
    "max_tokens_character": 1024,
    "language": "Portuguese",
}

def load_config() -> dict[str, Any]:
    """Carrega a configuração a partir de .data/config.json com fallback."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with suppress(OSError):
            CONFIG_PATH.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


SERVER_CONFIG: dict[str, Any] = {}
llm_client: httpx.AsyncClient | None = None
runner: Runner | None = None


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    global llm_client, runner, SERVER_CONFIG  # noqa: PLW0603
    SERVER_CONFIG = load_config()
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
    personality: str = ""
    knowledge: list[str] = Field(default_factory=list)
    current_mood: str = ""
    physical_description: str = ""
    outfit: str = ""


class SceneInput(BaseModel):
    location: str = ""
    time_of_day: str = ""
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
    action: str = ""
    force_speaker: str | None = None


class PlayerTurnResponse(BaseModel):
    narration: str | None = None
    character_response: str | None = None
    next_speaker: str | None = None
    scene_update: dict | None = None
    turn_number: int | None = None
    error: str | None = None


class PreviewPromptRequest(BaseModel):
    speech: str = ""
    action: str = ""


class SuggestResponse(BaseModel):
    suggestions: list[dict] | None = None
    error: str | None = None


# ── Rotas ─────────────────────────────────────────────────────────────────


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest) -> dict:
    """Cria uma nova sessão de roleplay."""
    assert runner is not None, "Runner não inicializado"
    from src.models import (
        Character,
        Scene,
        dict_to_character,
        game_state_to_dict,
    )
    from src.store.presets import list_defaults, load_preset

    preset_data: dict[str, Any] = {}
    if req.preset_name:
        preset_val = load_preset(req.preset_name)
        if preset_val is None:
            raise HTTPException(
                status_code=404,
                detail=f"Preset '{req.preset_name}' não encontrado."
            )
        preset_data = preset_val

    if not preset_data and not req.characters and not req.scene:
        defaults = list_defaults()
        if defaults:
            first_def = load_preset(defaults[0])
            if first_def:
                preset_data = first_def

    def parse_character_data(cdata: dict[str, Any]) -> Character:
        from src.models import CharacterBody, CharacterMind, resolve_personality
        if "mind" in cdata and "body" in cdata:
            mind_data = cdata["mind"]
            body_data = cdata["body"]
            return Character(
                mind=CharacterMind(
                    name=mind_data["name"],
                    personality=resolve_personality(mind_data),
                    knowledge=list(mind_data.get("knowledge", [])),
                    current_mood=mind_data.get("current_mood", ""),
                ),
                body=CharacterBody(
                    name=body_data["name"],
                    physical_description=body_data["physical_description"],
                    outfit=body_data["outfit"],
                ),
            )
        else:
            return Character(
                mind=CharacterMind(
                    name=cdata["name"],
                    personality=resolve_personality(cdata),
                    knowledge=list(cdata.get("knowledge", [])),
                    current_mood=cdata.get("current_mood", ""),
                ),
                body=CharacterBody(
                    name=cdata["name"],
                    physical_description=cdata.get("physical_description", ""),
                    outfit=cdata.get("outfit", ""),
                ),
            )

    characters = {}
    if req.characters:
        for cid, ci in req.characters.items():
            characters[cid] = dict_to_character(
                {
                    "mind": {
                        "name": ci.name,
                        "personality": ci.personality,
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
    elif "characters" in preset_data:
        for cid, cdata in preset_data["characters"].items():
            characters[cid] = parse_character_data(cdata)

    scene = None
    if req.scene is not None:
        scene = Scene(
            location=req.scene.location,
            time_of_day=req.scene.time_of_day,
            present_characters=[],  # recomputado pelo runner
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
        session_id = runner.start_session(cfg)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

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
        force_speaker=body.force_speaker,
    )
    return result


@app.post("/session/{session_id}/suggest", response_model=SuggestResponse)
async def suggest_actions(session_id: str) -> dict:
    """Sugestões de jogada do Narrador para o personagem controlado (gatilho manual)."""
    assert runner is not None, "Runner não inicializado"
    result = await runner.suggest_actions(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/session/{session_id}/debug_log")
def get_debug_log(session_id: str, limit: int = 200) -> list[dict]:
    """Log bruto e sequencial de TODAS as chamadas LLM da sessão (request/response reais).

    Uma entrada por chamada real (inclui retries), na ordem em que aconteceram —
    cada uma com ``session_id``, ``turn_number`` e ``agent`` (quem disparou).
    Substitui o antigo debug embutido na resposta do turno.
    """
    path = Path(f".data/sessions/{session_id}.debug.jsonl")
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    for line in lines[-limit:]:
        with suppress(json.JSONDecodeError):
            entries.append(json.loads(line))
    return entries


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
def get_defaults(name: str | None = None) -> dict:
    """Retorna o preset padrão para a UI pré-preencher."""
    from src.store.presets import list_defaults, load_preset

    defaults = list_defaults()
    target_name = name
    if not target_name:
        target_name = defaults[0] if defaults else ""

    if not target_name:
        raise HTTPException(status_code=404, detail="Nenhum preset padrão disponível.")

    preset_val = load_preset(target_name)
    if not preset_val:
        raise HTTPException(
            status_code=404,
            detail=f"Preset padrão '{target_name}' não encontrado."
        )

    return {
        "presets": defaults,
        "characters": preset_val.get("characters", {}),
        "scene": preset_val.get("scene", {}),
    }


# ── Presets API ──────────────────────────────────────────────────────────


@app.get("/presets")
def get_presets() -> list[str]:
    """Lista os nomes de todos os presets de usuário."""
    from src.store.presets import list_presets
    return list_presets()


@app.get("/presets/{name}")
def get_preset(name: str) -> dict:
    """Retorna a configuração completa de um preset."""
    from src.store.presets import load_preset
    preset_val = load_preset(name)
    if preset_val is None:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' não encontrado.")
    return preset_val


@app.put("/presets/{name}")
def put_preset(name: str, body: StartSessionRequest) -> dict:
    """Salva ou atualiza um preset de usuário."""
    from src.store.presets import save_preset
    # Salva no mesmo formato que o request (que é compatível com o frontend)
    save_preset(name, body.dict(exclude_none=True))
    return {"saved": True}


@app.delete("/presets/{name}")
def delete_preset_endpoint(name: str) -> dict:
    """Remove um preset de usuário."""
    from src.store.presets import delete_preset
    success = delete_preset(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' não encontrado.")
    return {"deleted": True}


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
