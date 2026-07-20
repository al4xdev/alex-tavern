"""A/B curl: roteiro stall-disruption OLD (loose) vs NEW (causal) — Task 38 ressalva.

The 38 ressalva: "make disruptions advance the planned arc, not interrupt
loosely" (disconnected-disruption pile-up). The OLD `stalled` prompt asked for
"an arrival, an interruption, something breaking or bursting in" — which invites
a figure/force from nowhere. The NEW prompt requires the disruption to grow
causally from a thread ALREADY open in the scene.

PRE-REGISTERED DECISION RULE (frozen before this run):

On two real stalled roteiro sessions, generate the next beat with each arm
(3 runs) and score the beat INTENT with a BLIND causality judge that never
learns which arm produced it — grounded (grows from an existing thread) vs
disconnected (from nowhere).

  SHIP the NEW prompt iff, over 6 beats per arm:
    - NEW grounded >= 5/6, AND
    - NEW grounded strictly greater than OLD grounded.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path

import httpx

from src.llm.client import chat_completion_json
from src.models import GameState, dict_to_game_state, speaker_label
from src.roteiro import build_next_beat_messages, build_next_beat_schema

SORTEIO = "plans/artifacts/roteiro-ab-turma-dos-portais-pt/roteiro/data/sessions/ccb521ab/state.json"
FIRE = "plans/artifacts/roteiro-ab/roteiro/data/sessions/e7760040/state.json"
RUNS = 3

# The NEW status text lives in the shipped source; reproduce the OLD one here so
# the A arm rebuilds the pre-change prompt by string substitution.
OLD_STALLED = (
    "The current beat STALLED: the scene is STUCK, circling one topic "
    "without a new development (measured: the same events/subject repeat). "
    "The next beat MUST be a concrete external DISRUPTION that happens THIS "
    "turn - an arrival, an interruption, something breaking or bursting in - "
    "that changes what the scene is ABOUT. Never continue or rephrase the "
    "stalled topic."
)
NEW_STALLED = (
    "The current beat STALLED: the scene is STUCK, circling one topic "
    "without a new development (measured: the same events/subject repeat). "
    "The next beat MUST be a concrete external DISRUPTION that happens THIS "
    "turn AND grows causally from a thread ALREADY open in the scene - a "
    "tension, an unanswered question, an object in play, a pending action, "
    "or an approaching force. It ESCALATES or COMPLICATES that existing "
    "thread and forces it to a head, changing what the scene is ABOUT. "
    "Never merely continue or rephrase the stalled topic; and never "
    "introduce a figure, object, or force disconnected from the scene "
    "(no arrival or intrusion from nowhere)."
)

JUDGE_SYS = (
    "You judge story coherence. You are given the RECENT EVENTS of a roleplay\n"
    "scene and ONE planned next development for it. Rule, as a json object,\n"
    "whether that development GROWS from a tension, question, object, or force\n"
    "already present in those events, or whether it is DISCONNECTED — a figure,\n"
    "object, or force from nowhere with no root in the scene.\n"
    'Return {"grounded": true|false, "why": "<one short sentence>"}.'
)


def load_game(state_path: str) -> GameState:
    data = json.loads(Path(state_path).read_text())
    data = {k: v for k, v in data.items() if k != "character_notes"}
    return dict_to_game_state(data)


def config() -> dict:
    cfg = json.loads(Path(".data/config.json").read_text())
    p = cfg["providers"]["deepseek"]
    return {"provider": "deepseek", "model": p.get("model", ""),
            "api_base": p.get("api_base", ""), "api_key": p.get("api_key", ""),
            "language": "portuguese"}


def window(game: GameState) -> str:
    recent = [r for r in game.history[-12:]
              if r.content_type in ("speech", "action", "narration")]
    return "\n".join(
        f"  {speaker_label(r.speaker, game.characters, game.player.controlled_character_id)}:"
        f" {r.content[:160]}" for r in recent
    )


def messages_for(game: GameState, arm: str) -> list[dict]:
    msgs = build_next_beat_messages(game, game.roteiro, "stalled", "beat")  # NEW (shipped)
    if arm == "OLD":
        msgs = copy.deepcopy(msgs)
        for m in msgs:
            m["content"] = m["content"].replace(NEW_STALLED, OLD_STALLED)
    return msgs


async def gen_intent(client: httpx.AsyncClient, cfg: dict, game: GameState, arm: str) -> str:
    result = await chat_completion_json(
        client, messages_for(game, arm), model=cfg["model"], language=cfg["language"],
        max_tokens=1024, json_schema=build_next_beat_schema("beat"),
        provider=cfg["provider"], api_base=cfg["api_base"], api_key=cfg["api_key"],
        agent="exp:roteiro_stall",
    )
    return str((result.get("beat") or {}).get("intent", "")).strip()


async def judge(client: httpx.AsyncClient, cfg: dict, win: str, intent: str) -> dict:
    user = f"RECENT EVENTS:\n{win}\n\nPLANNED NEXT DEVELOPMENT:\n{intent}"
    return await chat_completion_json(
        client, [{"role": "system", "content": JUDGE_SYS}, {"role": "user", "content": user}],
        model=cfg["model"], max_tokens=128, provider=cfg["provider"],
        api_base=cfg["api_base"], api_key=cfg["api_key"], agent="exp:roteiro_judge",
    )


async def main() -> None:
    cfg = config()
    games = {"SORTEIO": load_game(SORTEIO), "FIRE": load_game(FIRE)}
    grounded = {"OLD": 0, "NEW": 0}
    records = []
    async with httpx.AsyncClient() as client:
        for name, game in games.items():
            win = window(game)
            for arm in ("OLD", "NEW"):
                print(f"\n===== {name} / {arm} =====")
                for i in range(RUNS):
                    intent = await gen_intent(client, cfg, game, arm)
                    verdict = await judge(client, cfg, win, intent)
                    g = bool(verdict.get("grounded"))
                    grounded[arm] += int(g)
                    records.append({"session": name, "arm": arm, "run": i,
                                    "intent": intent, "grounded": g, "why": verdict.get("why")})
                    print(f"  run {i}: grounded={g} | {intent[:88]}")
                    print(f"          judge: {str(verdict.get('why',''))[:88]}")

    total = 2 * RUNS
    print("\n===== VERDICT =====")
    print(f"OLD grounded: {grounded['OLD']}/{total}")
    print(f"NEW grounded: {grounded['NEW']}/{total}")
    ship = grounded["NEW"] >= 5 and grounded["NEW"] > grounded["OLD"]
    print(f"\nSHIP (NEW): {ship}")
    Path("scratchpad/exp_roteiro_causal_stall_raw.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    asyncio.run(main())
