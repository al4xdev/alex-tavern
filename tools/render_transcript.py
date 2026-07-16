"""Render a recorded session as a readable screenplay-style markdown transcript.

The output is meant for narrative evaluation by a human reader or a clean-context
reviewer agent: it contains only what happened in the story (narration, dialogue,
actions, and clearly marked private thoughts) — no code, config, or prompts.

Usage:

    uv run python -m tools.render_transcript <run_dir_or_session_dir> [--out FILE]

Accepts either one playtest run directory (renders every session under
``sessions/``) or one session directory containing ``state.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.models import GameState, dict_to_game_state, speaker_label  # noqa: E402


def load_state(session_dir: Path) -> GameState:
    return dict_to_game_state(json.loads((session_dir / "state.json").read_text(encoding="utf-8")))


def render_session(game: GameState) -> str:
    """One markdown screenplay: turn-ordered narration, dialogue, and thoughts."""
    controlled_id = game.player.controlled_character_id
    lines = [
        f"# Sessão {game.session_id}",
        "",
        f"Local: {game.scene.location} — {game.scene.time_of_day}",
        "Personagens: " + ", ".join(character.mind.name for character in game.characters.values()),
        "",
        "---",
        "",
    ]
    last_turn: int | None = None
    for record in game.history:
        if record.turn_number != last_turn:
            lines.append(f"### Turno {record.turn_number}")
            last_turn = record.turn_number
        if record.speaker in game.characters:
            label = game.characters[record.speaker].mind.name
        else:
            label = speaker_label(record.speaker, game.characters, controlled_id)
        whisper = ""
        if record.audience is not None:
            if record.audience:
                hearers = ", ".join(
                    game.characters[cid].mind.name if cid in game.characters else cid
                    for cid in record.audience
                )
                verb = "percebe" if len(record.audience) == 1 else "percebem"
                # A scoped ACTION is limited perception, not a whisper.
                kind = "sussurrado — " if record.content_type == "speech" else ""
                whisper = f" ({kind}só {hearers} {verb})"
            else:
                whisper = " (ninguém além dele percebe)"
        if record.content_type == "narration":
            lines.append(f"*{record.content}*")
        elif record.content_type == "speech":
            lines.append(f"**{label}{whisper}:** {record.content}")
        elif record.content_type == "thought":
            lines.append(f"({label}, pensamento privado): {record.content}")
        elif record.content_type == "action":
            lines.append(f"[{label} — ação{whisper}] {record.content}")
        else:
            lines.append(f"[{label} — {record.content_type}] {record.content}")
        lines.append("")
    return "\n".join(lines)


def _session_dirs(root: Path) -> list[Path]:
    if (root / "state.json").exists():
        return [root]
    sessions = root / "sessions"
    if sessions.is_dir():
        return sorted(path for path in sessions.iterdir() if (path / "state.json").exists())
    raise SystemExit(f"No state.json or sessions/ found under {root}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="Playtest run directory or session directory")
    parser.add_argument("--out", type=Path, help="Write to this file instead of stdout")
    args = parser.parse_args(argv)

    rendered = "\n\n".join(render_session(load_state(path)) for path in _session_dirs(args.root))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"Transcript written to {args.out}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
