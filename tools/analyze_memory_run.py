"""Localize where a memory marker is lost in a recorded playtest run.

Given a playtest run directory and one or more deterministic markers (for example
``ORQUÍDEA-741``), this tool answers, layer by layer, where each marker survives:

1. STATE      — is the marker in the persisted session history, and as which
                ``content_type``/``speaker``?
2. SELECTION  — does the marker survive ``_format_history_for_character`` (the
                content-type filter plus token trim) recomputed offline for each
                character?
3. PROMPT     — did the marker reach the actual LLM request of each character
                call, per turn, according to ``debug.jsonl``?
4. RESPONSE   — did any character response contain the marker?

A marker absent from a layer while present in the previous one pinpoints the
losing layer. Usage:

    uv run python -m tools.analyze_memory_run <run_dir> \
        --marker "ORQUÍDEA-741" --marker "GIRASSOL-222" \
        --context-max 65536 --max-tokens-character 512
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.agents.character import _format_history_for_character  # noqa: E402
from src.models import GameState, dict_to_game_state  # noqa: E402

LAYERS = ("state", "selection", "prompt", "response")


def load_session_state(session_dir: Path) -> GameState:
    state_path = session_dir / "state.json"
    return dict_to_game_state(json.loads(state_path.read_text(encoding="utf-8")))


def load_debug_records(session_dir: Path) -> list[dict[str, Any]]:
    debug_path = session_dir / "debug.jsonl"
    if not debug_path.exists():
        return []
    records = []
    for line in debug_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def analyze_state_layer(game: GameState, marker: str) -> list[dict[str, Any]]:
    """Layer 1: marker occurrences in the persisted, append-only history."""
    return [
        {
            "turn_number": record.turn_number,
            "speaker": record.speaker,
            "content_type": record.content_type,
        }
        for record in game.history
        if re.search(marker, record.content)
    ]


def analyze_selection_layer(
    game: GameState, marker: str, context_max: int, max_tokens_character: int
) -> dict[str, bool]:
    """Layer 2: recompute the character history selection offline per character."""
    return {
        character_id: bool(
            re.search(
                marker,
                _format_history_for_character(
                    game.history,
                    game.characters,
                    game.player.controlled_character_id,
                    character_id,
                    context_max=context_max,
                    max_tokens_character=max_tokens_character,
                ),
            )
        )
        for character_id in game.characters
    }


def _character_calls(debug_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in debug_records
        if str(record.get("agent", "")).startswith("character:")
        and isinstance(record.get("request"), dict)
    ]


def analyze_prompt_layer(debug_records: list[dict[str, Any]], marker: str) -> list[dict[str, Any]]:
    """Layer 3: marker presence in each real character LLM request."""
    rows = []
    for record in _character_calls(debug_records):
        prompt_text = "\n".join(
            str(message.get("content", ""))
            for message in record["request"].get("messages", [])
            if isinstance(message, dict)
        )
        rows.append(
            {
                "turn_number": record.get("turn_number"),
                "agent": record.get("agent"),
                "present": bool(re.search(marker, prompt_text)),
            }
        )
    return rows


def analyze_response_layer(
    debug_records: list[dict[str, Any]], marker: str
) -> list[dict[str, Any]]:
    """Layer 4: marker presence in each real character LLM response."""
    rows = []
    for record in _character_calls(debug_records):
        response = record.get("response")
        rows.append(
            {
                "turn_number": record.get("turn_number"),
                "agent": record.get("agent"),
                "present": isinstance(response, str) and bool(re.search(marker, response)),
            }
        )
    return rows


def localize_loss(analysis: dict[str, Any]) -> str:
    """Name the first layer where the marker disappears."""
    if not analysis["state"]:
        return "CAMADA 1 (estado): o marcador nunca foi persistido no histórico"
    if not any(row["content_type"] in ("speech", "action") for row in analysis["state"]):
        return (
            "CAMADA 2 (seleção): o marcador existe no estado mas nunca como speech/action — "
            "o filtro de content_type o esconde de todos os personagens"
        )
    if not any(analysis["selection"].values()):
        return "CAMADA 2 (seleção): filtro/trim removeu o marcador do contexto recomputado"
    prompt_hits = [row for row in analysis["prompt"] if row["present"]]
    if not prompt_hits:
        return "CAMADA 3 (prompt): o marcador não chegou a nenhuma request de personagem"
    response_hits = [row for row in analysis["response"] if row["present"]]
    if not response_hits:
        return (
            "CAMADA 4 (provider/modelo): o marcador estava no prompt mas nunca "
            "apareceu em uma resposta"
        )
    return "sem perda: o marcador sobreviveu às quatro camadas"


def analyze_marker(
    game: GameState,
    debug_records: list[dict[str, Any]],
    marker: str,
    context_max: int,
    max_tokens_character: int,
) -> dict[str, Any]:
    analysis = {
        "marker": marker,
        "state": analyze_state_layer(game, marker),
        "selection": analyze_selection_layer(game, marker, context_max, max_tokens_character),
        "prompt": analyze_prompt_layer(debug_records, marker),
        "response": analyze_response_layer(debug_records, marker),
    }
    analysis["localization"] = localize_loss(analysis)
    return analysis


def render_text(session_id: str, analyses: list[dict[str, Any]]) -> str:
    lines = [f"Sessão {session_id}"]
    for analysis in analyses:
        lines.append(f"\n## Marcador: {analysis['marker']}")
        state_rows = analysis["state"]
        if state_rows:
            occurrences = ", ".join(
                f"turno {row['turn_number']} ({row['speaker']}/{row['content_type']})"
                for row in state_rows
            )
            lines.append(f"1. ESTADO    : presente — {occurrences}")
        else:
            lines.append("1. ESTADO    : AUSENTE do histórico persistido")
        selection = analysis["selection"]
        lines.append(
            "2. SELEÇÃO   : "
            + ", ".join(
                f"{cid}={'ok' if present else 'PERDIDO'}" for cid, present in selection.items()
            )
        )
        prompt_by_agent: dict[str, list[int]] = {}
        for row in analysis["prompt"]:
            if row["present"]:
                prompt_by_agent.setdefault(str(row["agent"]), []).append(row["turn_number"])
        lines.append(
            "3. PROMPT    : "
            + (
                "; ".join(f"{agent} nos turnos {turns}" for agent, turns in prompt_by_agent.items())
                or "AUSENTE de todas as requests de personagem"
            )
        )
        response_hits = [row for row in analysis["response"] if row["present"]]
        lines.append(
            "4. RESPOSTA  : "
            + (
                "; ".join(f"{row['agent']} no turno {row['turn_number']}" for row in response_hits)
                or "AUSENTE de todas as respostas de personagem"
            )
        )
        lines.append(f"=> {analysis['localization']}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path, help="Playtest run directory (contains sessions/)")
    parser.add_argument("--marker", action="append", required=True, dest="markers")
    parser.add_argument("--context-max", type=int, default=65536)
    parser.add_argument("--max-tokens-character", type=int, default=512)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    sessions_root = args.run_dir / "sessions"
    session_dirs = sorted(path for path in sessions_root.iterdir() if path.is_dir())
    if not session_dirs:
        raise SystemExit(f"No sessions found under {sessions_root}")
    output: list[dict[str, Any]] = []
    for session_dir in session_dirs:
        game = load_session_state(session_dir)
        debug_records = load_debug_records(session_dir)
        analyses = [
            analyze_marker(
                game, debug_records, marker, args.context_max, args.max_tokens_character
            )
            for marker in args.markers
        ]
        output.append({"session_id": session_dir.name, "markers": analyses})
        if not args.json:
            print(render_text(session_dir.name, analyses))
            print()
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
