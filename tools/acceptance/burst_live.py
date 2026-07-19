"""Task 37 live: one skip -> the world plays several beats and stops with a reason."""
# ruff: noqa: E402  (script: sys.path bootstrap precedes imports)
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/home/alex/git/my/roleplay")
OUT = Path("/home/alex/git/my/roleplay/plans/artifacts/burst-live")
os.environ["ROLEPLAY_DATA_DIR"] = str(OUT / "data")
import httpx

from src.config import load_config, resolve_active_config
from src.models import Character, CharacterBody, CharacterMind, Scene
from src.runner import Runner
from src.store.sessions import session_debug_path

CH = {
    "C1": Character(
        mind=CharacterMind(
            name="Rui", personality="Viajante cansado.", knowledge=[], current_mood="entediado"
        ),
        body=CharacterBody(name="Rui", physical_description="Botas sujas.", outfit="Capa"),
    ),
    "C2": Character(
        mind=CharacterMind(
            name="Marta",
            personality="Estalajadeira faladeira que puxa os outros para a conversa.",
            knowledge=["Ouviu lobos mais cedo"],
            current_mood="inquieta",
        ),
        body=CharacterBody(name="Marta", physical_description="Avental.", outfit="Avental"),
    ),
    "C3": Character(
        mind=CharacterMind(
            name="Bento",
            personality="Cacador pratico que age quando algo acontece.",
            knowledge=["A trilha do norte esta perigosa"],
            current_mood="alerta",
        ),
        body=CharacterBody(name="Bento", physical_description="Barba rala.", outfit="Couro"),
    ),
}

async def main():
    config = resolve_active_config(
        load_config(Path("/home/alex/git/my/roleplay/.data/config.json"))
    )
    config.update({
        "autonomous_burst_max_beats": 4,
        "auto_event_enabled": True,
        "auto_event_base_probability": 0.9,
        "llm_timeout_seconds": 120.0,
    })
    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)
        sid = runner.start_session({
            "characters": dict(CH),
            "scene": Scene(location="Estalagem - salao", time_of_day="Madrugada",
                           present_characters=["C1", "C2", "C3", "Player"],
                           physical_facts={"lareira": "quase apagada"}),
            "controlled_character_id": "C1",
        })
        await runner.player_turn(sid, speech="Que noite parada.")
        result = await runner.player_turn(sid, skip=True)
    print(json.dumps({
        "beats": len(result.get("beats") or []),
        "stop_reason": result.get("burst_stop_reason"),
        "turns": [b["turn_number"] for b in (result.get("beats") or [])],
    }, ensure_ascii=False))
    for b in result.get("beats") or []:
        print(f"--- beat T{b['turn_number']} (queue={b['next_speakers']})")
        print("  N:", (b.get("narration") or "")[:150])
        for e in b.get("character_responses", []):
            print(f"  {e['character_id']}: {(e.get('speech') or '(...)')[:120]}")
    burst_logs = [
        json.loads(line)
        for line in session_debug_path(sid).read_text().splitlines()
        if '"autonomous_burst"' in line
    ]
    print("burst log:", burst_logs)

asyncio.run(main())
