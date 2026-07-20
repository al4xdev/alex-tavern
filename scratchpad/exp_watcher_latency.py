"""33b acceptance: measure the watcher's added per-turn latency (real payloads).

Per audited turn the watcher costs ONE delta-audit call. The causal
intervention costs a second call, but only when the ladder reaches the
disruption rung (rare — gated by quiet threshold + refractory). We report both.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

from src.models import GameState, dict_to_game_state
from src.watcher import audit_delta, generate_causal_intervention

SORTEIO = "plans/artifacts/roteiro-ab-turma-dos-portais-pt/roteiro/data/sessions/ccb521ab/state.json"
FIRE = "plans/artifacts/roteiro-ab/roteiro/data/sessions/e7760040/state.json"
N = 6


def load_game(p: str, upto: int) -> GameState:
    data = {k: v for k, v in json.loads(Path(p).read_text()).items() if k != "character_notes"}
    g = dict_to_game_state(data)
    g.history = [r for r in g.history if r.turn_number <= upto]
    return g


def config() -> dict:
    c = json.loads(Path(".data/config.json").read_text())["providers"]["deepseek"]
    return {"provider": "deepseek", "model": c.get("model", ""), "api_base": c.get("api_base", ""),
            "api_key": c.get("api_key", ""), "language": "portuguese"}


async def timed(coro):  # noqa: ANN001, ANN201
    t = time.perf_counter()
    await coro
    return time.perf_counter() - t


async def main() -> None:
    cfg = config()
    games = [load_game(SORTEIO, 8), load_game(FIRE, 4)]
    audit_ms: list[float] = []
    interv_ms: list[float] = []
    async with httpx.AsyncClient() as client:
        for g in games:
            for _ in range(N):
                audit_ms.append(await timed(audit_delta(client, g, cfg, 1)) * 1000)
            for _ in range(N):
                interv_ms.append(
                    await timed(generate_causal_intervention(client, g, cfg, 1)) * 1000
                )

    def report(name: str, xs: list[float]) -> None:
        xs.sort()
        p90 = xs[int(len(xs) * 0.9) - 1]
        print(f"{name}: median {statistics.median(xs):.0f} ms | p90 {p90:.0f} ms | "
              f"min {xs[0]:.0f} | max {xs[-1]:.0f} (n={len(xs)})")

    print("\n===== WATCHER ADDED LATENCY (deepseek, real windows) =====")
    report("delta_audit   (EVERY audited turn)", audit_ms)
    report("causal_intervene (only at disruption rung)", interv_ms)
    print("\nPer-turn added cost when enabled = one delta_audit call.")
    print("Intervention adds a second call only when the ladder disrupts.")


if __name__ == "__main__":
    asyncio.run(main())
