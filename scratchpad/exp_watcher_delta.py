"""Curl-validate the delta auditor (Task 33b piece 1) on TWO real stalled windows.

PRE-REGISTERED DECISION RULE (frozen before this run):

The auditor's job in the recovery ladder is a bidirectional classifier:
  (a) reliably flag IMMOBILITY (re-narration / pure description / reaction),
  (b) reliably catch a REAL material event (so it is not stuck-at-none).

Two real production windows, deepseek-v4-flash, 4 runs per turn:

  SORTEIO (ccb521ab) — the lexical trap:
    T7 = RE-narration of the T6 explosion (SAME vocabulary) -> want none.
    T8 = aftermath (smoke thins, describes debris)          -> want none.

  FIRE (e7760040) — clean material events after a 4-turn stall:
    T5 = the gas finally IGNITES (no fire before, fire now)  -> want moved.
    T9 = a roof beam COLLAPSES, foreclosing the back door    -> want moved.

  SHIP iff every gated turn meets its target in >= 3/4 runs.

Turns deliberately LEFT OUT of the gate (report-only), because they are
genuinely ambiguous and would make the gate a coin flip:
  - sorteio T6 (explosion after an already-failing lamp + countdown: new
    escalation vs predicted culmination — auditor splits ~50/50, confirmed).
  - sorteio T3 (messenger only ARRIVES; its stakes-changing reveal lands at T4,
    since this session re-narrates every event across two turns).
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

import httpx

from src.models import GameState, dict_to_game_state
from src.watcher import audit_delta, build_delta_audit_messages

RUNS = 4
SORTEIO = "plans/artifacts/roteiro-ab-turma-dos-portais-pt/roteiro/data/sessions/ccb521ab/state.json"
FIRE = "plans/artifacts/roteiro-ab/roteiro/data/sessions/e7760040/state.json"

# (state_path, turn, want_moved | None for report-only)
CASES = [
    (SORTEIO, 3, None),
    (SORTEIO, 6, None),
    (SORTEIO, 7, False),
    (SORTEIO, 8, False),
    (FIRE, 5, True),
    (FIRE, 9, True),
]


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


async def main() -> None:
    cfg = config()
    rows = []
    async with httpx.AsyncClient() as client:
        for state_path, turn, want in CASES:
            game = load_game_truncated(state_path, turn)
            build_delta_audit_messages(game)  # smoke-check window builds
            audits = [await audit_delta(client, game, cfg, turn_number=turn) for _ in range(RUNS)]
            name = "SORTEIO" if state_path == SORTEIO else "FIRE"
            rows.append((name, turn, want, audits))
            n_moved = sum(a.moved for a in audits)
            print(f"{name} T{turn}: moved {n_moved}/{RUNS}")
            for i, a in enumerate(audits):
                print(f"    run {i}: moved={a.moved} {a.categories} | {a.evidence[:70]}")

    print("\n===== VERDICT =====")
    ship = True
    for name, turn, want, audits in rows:
        n_moved = sum(a.moved for a in audits)
        cats = Counter(c for a in audits for c in a.categories)
        if want is None:
            tag = "report-only"
        else:
            ok = (n_moved >= 3) if want else ((RUNS - n_moved) >= 3)
            ship = ship and ok
            tag = f"GATE want {'moved' if want else 'none'} -> {'PASS' if ok else 'FAIL'}"
        print(f"{name} T{turn}: moved {n_moved}/{RUNS} | {tag} | cats={dict(cats)}")
    print(f"\nSHIP: {ship}")
    Path("scratchpad/exp_watcher_raw.json").write_text(
        json.dumps(
            [
                {
                    "session": name, "turn": turn, "want_moved": want,
                    "audits": [
                        {"moved": a.moved, "categories": list(a.categories), "evidence": a.evidence}
                        for a in audits
                    ],
                }
                for name, turn, want, audits in rows
            ],
            ensure_ascii=False, indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
