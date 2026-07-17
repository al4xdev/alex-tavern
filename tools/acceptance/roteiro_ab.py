"""Task 38 acceptance: A/B same scenario with and without roteiro.

Identical player inputs in both arms; the only difference is roteiro_enabled.
Arm outputs go to plans/artifacts/roteiro-ab/{control,roteiro}/data.
Also scans the roteiro arm's debug log: roteiro text must exist ONLY in
director/roteiro payloads (confidentiality invariant, Task 38).
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/home/alex/git/my/roleplay")
BASE = Path("/home/alex/git/my/roleplay/plans/artifacts/roteiro-ab")

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


async def run_arm(name: str, roteiro_enabled: bool) -> str:
    os.environ["ROLEPLAY_DATA_DIR"] = str(BASE / name / "data")
    # Fresh imports per arm would be ideal; the store reads the env var lazily
    # per call in this codebase, so setting it before the runner works.
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
    config = resolve_active_config(load_config(Path("/home/alex/git/my/roleplay/.data/config.json")))
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
        "arm": name,
        "session_id": sid,
        "turns": game.history[-1].turn_number if game.history else 0,
        "roteiro": None,
    }
    if game.roteiro is not None:
        summary["roteiro"] = {
            "premise": game.roteiro.premise,
            "acts": [a.summary for a in game.roteiro.acts],
            "act_index": game.roteiro.act_index,
            "beat": game.roteiro.beat.intent if game.roteiro.beat else None,
            "beat_log": game.roteiro.beat_log,
        }
    print(json.dumps(summary, ensure_ascii=False))
    return sid


def confidentiality_scan(name: str, sid: str) -> None:
    from src.store.sessions import session_debug_path, load_game

    os.environ["ROLEPLAY_DATA_DIR"] = str(BASE / name / "data")
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
            replans.append({k: record[k] for k in ("turn_number", "action", "reason", "beat_id")})
        request = record.get("request")
        if not request:
            continue
        payload = json.dumps(request.get("messages", []), ensure_ascii=False)
        hit = [s for s in secret_strings if s in payload]
        if hit and agent != "director" and not agent.startswith("roteiro"):
            violations.append({"agent": agent, "turn": record.get("turn_number"), "hits": hit})
    print("replan decisions:", json.dumps(replans, ensure_ascii=False))
    print("CONFIDENTIALITY VIOLATIONS:", json.dumps(violations, ensure_ascii=False) if violations else "NONE")


async def main() -> None:
    sid_control = await run_arm("control", roteiro_enabled=False)
    sid_roteiro = await run_arm("roteiro", roteiro_enabled=True)
    confidentiality_scan("roteiro", sid_roteiro)
    print(json.dumps({"control": sid_control, "roteiro": sid_roteiro}))


asyncio.run(main())
