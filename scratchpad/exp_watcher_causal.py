"""Curl-validate the causal intervention (Task 33b piece 3) on real windows.

PRE-REGISTERED DECISION RULE (frozen before this run):

The disruption rung must GROW its event from a thread already in the scene,
never a shock from nowhere. Generate interventions at three real stalled
points, then score each event_now with a BLIND causality judge that never
learns it is a watcher intervention — it only sees the scene window + one event
and rules whether the event grows from an existing tension (grounded) or
appears disconnected (a figure/object/force from nowhere).

  Stalled points:
    - SORTEIO T2: the narration itself says the scene froze ("uma pausa se
      estabelece; o ar carregado de mana não se move").
    - SORTEIO T8: post-explosion aftermath, nothing material advancing.
    - FIRE   T4: pre-ignition stall (sparks die, characters re-urge leaving).

  3 interventions per point (9 total). SHIP iff:
    - blind judge rules >= 8/9 GROUNDED, AND
    - every intervention is structurally usable (source_thread + event_now
      non-empty; refractory_turns in [2,4]).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from src.llm.client import chat_completion_json
from src.models import GameState, dict_to_game_state
from src.watcher import build_causal_intervention_messages, generate_causal_intervention

SORTEIO = "plans/artifacts/roteiro-ab-turma-dos-portais-pt/roteiro/data/sessions/ccb521ab/state.json"
FIRE = "plans/artifacts/roteiro-ab/roteiro/data/sessions/e7760040/state.json"
POINTS = [("SORTEIO", SORTEIO, 2), ("SORTEIO", SORTEIO, 8), ("FIRE", FIRE, 4)]
RUNS = 3

JUDGE_SYS = (
    "You judge story coherence. You are given the RECENT EVENTS of a roleplay\n"
    "scene and ONE new event that just occurred. Rule, as a json object, whether\n"
    "the new event GROWS from a tension, question, object, or force already\n"
    "present in those events, or whether it appears DISCONNECTED — a figure,\n"
    "object, sound, or force from nowhere with no root in the scene.\n"
    'Return {"grounded": true|false, "why": "<one short sentence>"}.'
)


def load_game_truncated(state_path: str, upto_turn: int) -> GameState:
    data = json.loads(Path(state_path).read_text())
    data = {k: v for k, v in data.items() if k != "character_notes"}
    game = dict_to_game_state(data)
    game.history = [r for r in game.history if r.turn_number <= upto_turn]
    return game


def config() -> dict:
    cfg = json.loads(Path(".data/config.json").read_text())
    p = cfg["providers"]["deepseek"]
    return {
        "provider": "deepseek",
        "model": p.get("model", ""),
        "api_base": p.get("api_base", ""),
        "api_key": p.get("api_key", ""),
        "language": "portuguese",
    }


async def judge(client: httpx.AsyncClient, cfg: dict, window: str, event: str) -> dict:
    user = f"RECENT EVENTS:\n{window}\n\nNEW EVENT:\n{event}"
    return await chat_completion_json(
        client,
        [{"role": "system", "content": JUDGE_SYS}, {"role": "user", "content": user}],
        model=cfg["model"],
        max_tokens=128,
        provider=cfg["provider"],
        api_base=cfg["api_base"],
        api_key=cfg["api_key"],
        agent="exp:causal_judge",
    )


async def main() -> None:
    cfg = config()
    records = []
    grounded_count = 0
    structural_ok = True
    async with httpx.AsyncClient() as client:
        for name, path, turn in POINTS:
            game = load_game_truncated(path, turn)
            window = build_causal_intervention_messages(game)[1]["content"]
            print(f"\n===== {name} T{turn} =====")
            for i in range(RUNS):
                iv = await generate_causal_intervention(client, game, cfg, turn_number=turn)
                usable = iv.grounded and 2 <= iv.refractory_turns <= 4
                structural_ok = structural_ok and usable
                verdict = await judge(client, cfg, window, iv.event_now)
                g = bool(verdict.get("grounded"))
                grounded_count += int(g)
                records.append({
                    "point": f"{name} T{turn}", "run": i,
                    "source_thread": iv.source_thread, "event_now": iv.event_now,
                    "expected_delta": iv.expected_delta, "refractory_turns": iv.refractory_turns,
                    "structurally_usable": usable, "judge_grounded": g, "judge_why": verdict.get("why"),
                })
                print(f"  run {i}: grounded={g} usable={usable} refr={iv.refractory_turns}")
                print(f"    thread: {iv.source_thread[:90]}")
                print(f"    event:  {iv.event_now[:90]}")
                print(f"    judge:  {verdict.get('why', '')[:90]}")

    total = len(records)
    print("\n===== VERDICT =====")
    print(f"grounded (blind judge): {grounded_count}/{total} (need >= 8/9)")
    print(f"structurally usable:    {'ALL' if structural_ok else 'NOT ALL'}")
    ship = grounded_count >= 8 and structural_ok
    print(f"\nSHIP: {ship}")
    Path("scratchpad/exp_watcher_causal_raw.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    asyncio.run(main())
