"""Dataclasses do sistema de roleplay multi-agente."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CharacterMind:
    """Visível ao próprio personagem e ao Narrador."""

    name: str
    personality_summary: str  # ~2 frases, vai pro user prompt
    personality_full: str  # descrição longa, vai pro system prompt
    knowledge: list[str]  # fatos que o personagem conhece
    current_mood: str  # mutável a cada turno


@dataclass
class CharacterBody:
    """Só o Narrador vê — aparência física."""

    name: str
    physical_description: str  # aparência, corpo
    outfit: str  # roupa atual (mutável)


@dataclass
class Character:
    """Agrega Mind + Body. Sem referência ao LLM client."""

    mind: CharacterMind
    body: CharacterBody


@dataclass
class Player:
    """O humano que joga."""

    name: str
    controlled_character_id: str  # qual personagem o jogador controla, fixo na sessão


@dataclass
class Scene:
    """Estado da cena atual."""

    location: str
    time_of_day: str
    present_characters: list[str]  # ["C1", "C2", "Player"]
    physical_facts: dict[str, str]  # {"weather": "chuva", "door": "aberta"}


@dataclass
class TurnRecord:
    """Uma entrada no histórico — contém cópia da cena naquele momento."""

    turn_number: int
    speaker: str  # "Player", "C1", "C2", "Narrator"
    content: str
    content_type: str  # "speech", "thought", "narration", "action"
    scene_snapshot: Scene  # deepcopy da cena naquele turno


@dataclass
class TurnState:
    """Resetado a cada turno — nunca persiste entre turnos."""

    turn_number: int
    player_speech: str
    player_action: str
    narrator_raw: dict | None = None
    character_response: str | None = None
    next_speaker: str | None = None
    player_options: list[dict] | None = None  # [{"index":0, "label":"...", "description":"..."}]


@dataclass
class GameState:
    """Persiste entre turnos no JSON da sessão."""

    session_id: str
    characters: dict[str, Character]  # {"C1": Character, "C2": Character}
    player: Player
    scene: Scene
    history: list[TurnRecord] = field(default_factory=list)
    pending_options: list[dict] | None = None  # options do turno anterior não consumidas
    created_at: str = ""  # ISO timestamp


def deepcopy_scene(scene: Scene) -> Scene:
    """Retorna uma cópia profunda da Scene (obrigatório para snapshots)."""
    return copy.deepcopy(scene)


def game_state_to_dict(game: GameState) -> dict[str, Any]:
    """Converte GameState para dict serializável em JSON."""
    return asdict(game)


def dict_to_game_state(data: dict[str, Any]) -> GameState:
    """Reconstrói GameState de um dict (carregado do JSON).

    Construção manual explícita — sem dependências de serialização mágica.
    """
    chars_raw: dict[str, Any] = data["characters"]
    characters: dict[str, Character] = {}
    for cid, cdata in chars_raw.items():
        mind_data = cdata["mind"]
        body_data = cdata["body"]
        characters[cid] = Character(
            mind=CharacterMind(
                name=mind_data["name"],
                personality_summary=mind_data["personality_summary"],
                personality_full=mind_data["personality_full"],
                knowledge=list(mind_data["knowledge"]),
                current_mood=mind_data["current_mood"],
            ),
            body=CharacterBody(
                name=body_data["name"],
                physical_description=body_data["physical_description"],
                outfit=body_data["outfit"],
            ),
        )

    player_data = data["player"]
    player = Player(
        name=player_data["name"],
        controlled_character_id=player_data["controlled_character_id"],
    )

    scene_data = data["scene"]
    scene = Scene(
        location=scene_data["location"],
        time_of_day=scene_data["time_of_day"],
        present_characters=list(scene_data["present_characters"]),
        physical_facts=dict(scene_data["physical_facts"]),
    )

    history_raw: list[dict[str, Any]] = data.get("history", [])
    history: list[TurnRecord] = []
    for h in history_raw:
        snap = h["scene_snapshot"]
        scene_snap = Scene(
            location=snap["location"],
            time_of_day=snap["time_of_day"],
            present_characters=list(snap["present_characters"]),
            physical_facts=dict(snap["physical_facts"]),
        )
        history.append(
            TurnRecord(
                turn_number=h["turn_number"],
                speaker=h["speaker"],
                content=h["content"],
                content_type=h["content_type"],
                scene_snapshot=scene_snap,
            )
        )

    return GameState(
        session_id=data["session_id"],
        characters=characters,
        player=player,
        scene=scene,
        history=history,
        pending_options=data.get("pending_options"),
        created_at=data.get("created_at", ""),
    )
