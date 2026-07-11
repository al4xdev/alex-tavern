"""Dataclasses do sistema de roleplay multi-agente."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CharacterMind:
    """Visível ao próprio personagem e ao Narrador."""

    name: str
    personality: str  # descrição da personalidade, vai pro prompt do Narrador e do personagem
    knowledge: list[str]  # fatos que o personagem conhece
    current_mood: str  # atualizado pelo Narrador via mood_updates a cada turno


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
class GameState:
    """Persiste entre turnos no JSON da sessão."""

    session_id: str
    characters: dict[str, Character]  # {"C1": Character, "C2": Character}
    player: Player
    scene: Scene
    history: list[TurnRecord] = field(default_factory=list)
    pending_options: list[dict] | None = None  # options do turno anterior não consumidas
    created_at: str = ""  # ISO timestamp
    narrator_directives: str = ""  # instruções de mundo/tom/regras extras p/ o Narrador


def trim_history_by_tokens(
    history: list[TurnRecord], context_max: int, reserved_tokens: int
) -> list[TurnRecord]:
    """Seleciona, do mais recente ao mais antigo, os turnos que cabem no orçamento.

    Orçamento = ~70% de ``context_max`` menos ``reserved_tokens`` (espaço
    reservado para a resposta do LLM). Estimativa de tokens é ``len(texto) // 4``.
    Nunca corta pelo número de turnos — só pela proximidade do limite de tokens.
    Sempre inclui ao menos o turno mais recente, mesmo que ele sozinho já
    ultrapasse o orçamento.
    """
    budget = int(context_max * 0.7) - reserved_tokens
    if budget <= 0 or not history:
        return []
    selected: list[TurnRecord] = []
    used = 0
    for rec in reversed(history):
        cost = len(rec.content) // 4
        if selected and used + cost > budget:
            break
        selected.append(rec)
        used += cost
    selected.reverse()
    return selected


def deepcopy_scene(scene: Scene) -> Scene:
    """Retorna uma cópia profunda da Scene (obrigatório para snapshots)."""
    return copy.deepcopy(scene)


def speaker_label(speaker: str, characters: dict[str, Character], controlled_id: str) -> str:
    """Traduz o ``speaker`` armazenado no rótulo a exibir em qualquer prompt de LLM.

    ``"Player"`` é o marcador interno da jogada do humano — nunca deve chegar a
    uma LLM (Narrador ou Personagem). É sempre traduzido para o nome do
    personagem controlado. Os demais speakers (IDs de personagem, "Narrator")
    voltam como estão.
    """
    if speaker == "Player":
        controlled = characters.get(controlled_id)
        if controlled is not None:
            return controlled.mind.name
    return speaker


def game_state_to_dict(game: GameState) -> dict[str, Any]:
    """Converte GameState para dict serializável em JSON."""
    return asdict(game)


def resolve_personality(data: dict[str, Any]) -> str:
    """Lê ``personality`` ou migra do formato legado (``personality_summary`` +
    ``personality_full``), para não quebrar dados salvos antes da unificação.
    """
    personality = data.get("personality")
    if personality is not None:
        return str(personality)
    legacy = [data.get("personality_summary"), data.get("personality_full")]
    return "\n\n".join(p for p in legacy if p)


def dict_to_character(data: dict[str, Any]) -> Character:
    """Constrói um Character a partir de um dict com chaves ``mind`` e ``body``.

    Reusável tanto no round-trip de persistência quanto na API de criação.
    """
    mind_data = data["mind"]
    body_data = data["body"]
    return Character(
        mind=CharacterMind(
            name=mind_data["name"],
            personality=resolve_personality(mind_data),
            knowledge=list(mind_data["knowledge"]),
            current_mood=mind_data["current_mood"],
        ),
        body=CharacterBody(
            name=body_data["name"],
            physical_description=body_data["physical_description"],
            outfit=body_data["outfit"],
        ),
    )


def dict_to_game_state(data: dict[str, Any]) -> GameState:
    """Reconstrói GameState de um dict (carregado do JSON).

    Construção manual explícita — sem dependências de serialização mágica.
    """
    chars_raw: dict[str, Any] = data["characters"]
    characters: dict[str, Character] = {
        cid: dict_to_character(cdata) for cid, cdata in chars_raw.items()
    }

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
        narrator_directives=data.get("narrator_directives", ""),
    )
