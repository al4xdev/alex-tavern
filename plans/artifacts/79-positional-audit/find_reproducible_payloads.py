"""Task 79, decision 4 step 1: which payloads could a falsifier even be run on?

The owner rejected the replacement falsifier partly because nothing showed the
behaviour reproduces: arm A emitted zero `zone_moves` in 7 of 8 runs of the
earlier replay, so "did the field reduce positional zone_moves" was measuring the
harness.

  "Select payloads from the sessions at the top of the per-session range (the 44%
   one, not the 0% one) and show the behaviour reproduces before registering any
   rule about reducing it."

This ranks candidates. It costs nothing: it only reads what was recorded. It does
NOT test reproduction - that needs calls, and it is the next step.

A destination counts as positional by the union rule already used in task 79:
either the origin zone is its comma-prefix, or it carries a spatial preposition.
The preposition list is the FIXED one from the audit (`classify_positional.py`),
which caught four Portuguese contractions the first cut missed.
"""

from __future__ import annotations

import gc
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from classify_positional import PREPOSITIONS, distinct_sessions, norm  # noqa: E402


def positions_by_turn(base: pathlib.Path) -> dict[int, dict]:
    state = json.loads((base / "state.json").read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for record in state.get("history", []):
        turn = record.get("turn_number")
        snap = record.get("scene_snapshot") or {}
        if turn is not None and snap.get("positions"):
            out.setdefault(int(turn), snap["positions"])
    return out


def is_positional(destination: str, origin: str | None) -> bool:
    """A destination that is a spot INSIDE the place the mover already occupied.

    The hierarchical half must be the FULL origin plus a comma suffix. The first
    cut of this function tested whether the destination's first comma-segment was
    a SUBSTRING of the origin, which matches at the BUILDING level: it scored
    "Academia Real do Primeiro Sino, Salao dos Quatro Arcos" ->
    "Academia Real do Primeiro Sino, Patio Externo" as positional, 21 times in one
    turn, when it is a walk from the hall to the outer courtyard.

    That is the identical failure task 76 shipped two of - a wing and a building
    read as rooms - reappearing in a new instrument three weeks later. The rule
    now requires the whole origin as a prefix, which is what EXTENDS_A_ZONE in
    classify_positional.py already did correctly.
    """
    flat = norm(destination)
    if origin:
        base = norm(origin)
        if base and len(base) > 3 and flat.startswith(base + ","):
            return True
    return bool(PREPOSITIONS.search(flat))


def main() -> None:
    rows = []
    for sid, base in sorted(distinct_sessions().items()):
        positions = positions_by_turn(base)
        debug = base / "debug.jsonl"
        if not debug.exists():
            continue
        turns: list[tuple[int, int, int, list[str]]] = []
        total = positional_total = 0
        with debug.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("agent") != "director":
                    continue
                turn = record.get("turn_number")
                try:
                    parsed = json.loads(record.get("response") or "{}")
                except json.JSONDecodeError:
                    continue
                moves = parsed.get("zone_moves") or {}
                if not isinstance(moves, dict) or not moves:
                    continue
                origins = positions.get(int(turn) - 1, {})
                hits = [
                    str(dest)
                    for cid, dest in moves.items()
                    if is_positional(str(dest), origins.get(cid))
                ]
                total += len(moves)
                positional_total += len(hits)
                if hits:
                    turns.append((int(turn), len(moves), len(hits), hits))
        if total:
            rows.append((positional_total / total, sid, total, positional_total, turns))
        gc.collect()

    rows.sort(reverse=True)
    print("sessions ranked by positional share of recorded zone_moves\n")
    print(f"{'session':10} {'positional/total':>18} {'rate':>7}  turns with a positional move")
    for rate, sid, total, pos, turns in rows:
        if total < 5:
            continue
        marks = ",".join(f"T{t}({h})" for t, _, h, _ in turns[:8])
        print(f"{sid:10} {pos:8}/{total:<9} {rate:6.0%}  {marks}")

    print("\n\nCANDIDATE PAYLOADS - the turns with the most positional moves at once:")
    best = sorted(
        ((h, t, sid, hits) for rate, sid, total, pos, turns in rows for t, _, h, hits in turns),
        reverse=True,
    )[:10]
    for h, t, sid, hits in best:
        print(f"\n  {sid} T{t}: {h} positional destinations")
        for hit in hits[:4]:
            print(f"      {hit[:110]}")


if __name__ == "__main__":
    main()
