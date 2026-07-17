"""Task 38 acceptance: A/B same scenario with and without roteiro.

Identical player inputs in both arms; the only difference is roteiro_enabled.
Arm outputs go to plans/artifacts/roteiro-ab/{control,roteiro}/data.

IMPORTANT — arm isolation: ``src/paths.py`` resolves ROLEPLAY_DATA_DIR at
import time, so both arms must NOT share one process (that put both sessions
under the same data dir on the first run). The orchestrator spawns one
subprocess per arm with the env var set before any src import; the
confidentiality scan runs in its own subprocess for the same reason.

Usage:
  python tools/acceptance/roteiro_ab.py                 # orchestrate both arms
  python tools/acceptance/roteiro_ab.py --arm roteiro --enabled 1   # one arm
  python tools/acceptance/roteiro_ab.py --scan roteiro <sid>        # scan only
"""
import argparse
import asyncio
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

_SENT = re.compile(r"(?<=[.!?…])\s+")


def _sentences(text: str) -> list[str]:
    return [" ".join(s.lower().split()) for s in _SENT.split(text) if len(s.strip()) >= 25]


def lexical_metrics(sid: str) -> dict:
    """Deterministic lexical-variation metrics over a session's narration.

    max_echo: highest similarity between any narration sentence and any EARLIER
    narration sentence (0 = every sentence fresh, 1 = a verbatim repeat).
    near_dups: how many narration sentences echo an earlier one above 0.8.
    """
    from src.store.sessions import load_game

    game = load_game(sid)
    assert game is not None
    narrations = [r.content for r in game.history if r.content_type == "narration"]
    seen: list[str] = []
    max_echo, near_dups, total = 0.0, 0, 0
    worst = ("", "")
    for text in narrations:
        for sentence in _sentences(text):
            total += 1
            for prior in seen:
                ratio = difflib.SequenceMatcher(None, sentence, prior).ratio()
                if ratio > max_echo:
                    max_echo, worst = ratio, (prior, sentence)
                if ratio >= 0.8:
                    near_dups += 1
                    break
            seen.append(sentence)
    return {
        "narration_sentences": total,
        "max_echo": round(max_echo, 2),
        "near_dups": near_dups,
        "worst_pair": worst if max_echo >= 0.8 else None,
    }

REPO = Path("/home/alex/git/my/roleplay")
BASE = REPO / "plans/artifacts/roteiro-ab"

CHARACTER_SPEC = {
    "C1": {
        "mind": {"name": "Rui", "personality": "Viajante cansado.", "knowledge": [], "current_mood": "entediado"},
        "body": {"name": "Rui", "physical_description": "Botas sujas.", "outfit": "Capa"},
    },
    "C2": {
        "mind": {"name": "Marta", "personality": "Estalajadeira faladeira que puxa os outros para a conversa.", "knowledge": ["Ouviu lobos mais cedo"], "current_mood": "inquieta"},
        "body": {"name": "Marta", "physical_description": "Avental.", "outfit": "Avental"},
    },
    "C3": {
        "mind": {"name": "Bento", "personality": "Cacador pratico que age quando algo acontece.", "knowledge": ["A trilha do norte esta perigosa"], "current_mood": "alerta"},
        "body": {"name": "Bento", "physical_description": "Barba rala.", "outfit": "Couro"},
    },
}

INPUTS = [
    ("speech", "Que noite parada."),
    ("skip", None),
    ("speech", "Hm. Pode ser só o vento."),
    ("skip", None),
    ("skip", None),
    ("speech", "Não liguem pra mim, continuem."),
    ("skip", None),
    ("skip", None),
    ("speech", "E agora, o que fazemos?"),
    ("skip", None),
]


async def run_arm(roteiro_enabled: bool) -> str:
    """Run one arm in THIS process — env var must already be set by the caller."""
    import httpx
    from src.config import load_config, resolve_active_config
    from src.models import Character, CharacterBody, CharacterMind, Scene
    from src.runner import Runner

    characters = {
        cid: Character(
            mind=CharacterMind(**spec["mind"]),
            body=CharacterBody(**spec["body"]),
        )
        for cid, spec in CHARACTER_SPEC.items()
    }
    config = resolve_active_config(load_config(REPO / ".data/config.json"))
    config.update({
        "autonomous_burst_max_beats": 1,
        "roteiro_enabled": roteiro_enabled,
        "llm_timeout_seconds": 120.0,
    })
    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)
        sid = runner.start_session({
            "characters": characters,
            "scene": Scene(
                location="Estalagem - salao",
                time_of_day="Madrugada",
                present_characters=["C1", "C2", "C3", "Player"],
                physical_facts={"lareira": "quase apagada"},
            ),
            "controlled_character_id": "C1",
        })
        for kind, text in INPUTS:
            if kind == "speech":
                await runner.player_turn(sid, speech=text)
            else:
                await runner.player_turn(sid, skip=True)
        game = await runner.get_state(sid)
    summary = {
        "session_id": sid,
        "turns": game.history[-1].turn_number if game.history else 0,
        "roteiro": None,
    }
    if game.roteiro is not None:
        summary["roteiro"] = {
            "premise": game.roteiro.premise,
            "acts": [a.summary for a in game.roteiro.acts],
            "act_index": game.roteiro.act_index,
            "anchors_seen": game.roteiro.anchors_seen,
            "beat": game.roteiro.beat.intent if game.roteiro.beat else None,
            "beat_log": game.roteiro.beat_log,
        }
    print("ARM_SUMMARY " + json.dumps(summary, ensure_ascii=False))
    return sid


def confidentiality_scan(sid: str) -> None:
    """Scan the roteiro arm's debug log — env var must already point at its dir."""
    from src.store.sessions import load_game, session_debug_path

    game = load_game(sid)
    assert game is not None and game.roteiro is not None
    secret_strings = [game.roteiro.premise]
    if game.roteiro.beat:
        secret_strings += [game.roteiro.beat.intent, game.roteiro.beat.exit_condition]
    secret_strings += [act.summary for act in game.roteiro.acts]
    secret_strings = [s for s in secret_strings if len(s) >= 12]

    violations = []
    replans = []
    for line in session_debug_path(sid).read_text().splitlines():
        record = json.loads(line)
        agent = record.get("agent", "")
        if agent == "roteiro_replan":
            replans.append({k: record.get(k) for k in ("turn_number", "action", "reason", "beat_id", "anchors_missing", "actors_missing")})
        request = record.get("request")
        if not request:
            continue
        payload = json.dumps(request.get("messages", []), ensure_ascii=False)
        hit = [s for s in secret_strings if s in payload]
        if hit and agent != "director" and not agent.startswith("roteiro"):
            violations.append({"agent": agent, "turn": record.get("turn_number"), "hits": hit})
    print("REPLAN_DECISIONS " + json.dumps(replans, ensure_ascii=False))
    print("CONFIDENTIALITY " + ("NONE" if not violations else json.dumps(violations, ensure_ascii=False)))


def _spawn(args: list[str], data_dir: Path) -> str:
    """Run this script as a subprocess with an isolated data dir; return stdout."""
    # The child runs THIS file directly, so sys.path[0] is tools/acceptance,
    # not the repo root — inject REPO so ``import src`` resolves.
    env = dict(os.environ, ROLEPLAY_DATA_DIR=str(data_dir), PYTHONPATH=str(REPO))
    proc = subprocess.run(
        [sys.executable, __file__, *args],
        env=env, cwd=str(REPO), capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"arm {args} failed (exit {proc.returncode})")
    return proc.stdout


def _sid_from(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("ARM_SUMMARY "):
            return json.loads(line[len("ARM_SUMMARY "):])["session_id"]
    raise SystemExit("no ARM_SUMMARY in arm output")


def orchestrate() -> None:
    control_out = _spawn(["--arm", "control", "--enabled", "0"], BASE / "control" / "data")
    roteiro_out = _spawn(["--arm", "roteiro", "--enabled", "1"], BASE / "roteiro" / "data")
    sid_control = _sid_from(control_out)
    sid_roteiro = _sid_from(roteiro_out)
    _spawn(["--scan", sid_roteiro], BASE / "roteiro" / "data")
    ctrl_lex = _spawn(["--metrics", sid_control], BASE / "control" / "data")
    rot_lex = _spawn(["--metrics", sid_roteiro], BASE / "roteiro" / "data")
    sys.stdout.write("LEXICAL control " + ctrl_lex.split("LEXICAL ", 1)[-1])
    sys.stdout.write("LEXICAL roteiro " + rot_lex.split("LEXICAL ", 1)[-1])
    print("SESSIONS " + json.dumps({"control": sid_control, "roteiro": sid_roteiro}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["control", "roteiro"])
    parser.add_argument("--enabled", choices=["0", "1"])
    parser.add_argument("--scan", metavar="SID")
    parser.add_argument("--metrics", metavar="SID")
    args = parser.parse_args()
    if args.scan:
        confidentiality_scan(args.scan)
    elif args.metrics:
        print("LEXICAL " + json.dumps(lexical_metrics(args.metrics), ensure_ascii=False))
    elif args.arm:
        asyncio.run(run_arm(args.enabled == "1"))
    else:
        orchestrate()


if __name__ == "__main__":
    main()
