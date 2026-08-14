"""Task 79, third structural attempt: the signal MEASURING.md's own corollary names.

A critic caught the omission, and it is the failure rule 5 already logs about
itself. The corollary added 2026-08-13 says:

    "prefer a structural signal to a string one. Before writing the regex, ask
     what the engine already knows as data - Scene.positions maps a character to
     a zone without parsing anything."

The structural attempt that was actually run used the Director's `witness_ids`.
`positions` was never tried. So "nothing can measure this" was claimed without
trying the signal this project's own rule points at.

THE SIGNAL, and it matches no name:

  For a recorded move of C from origin O to destination D at turn T, ask two
  questions answerable from `zones` and `positions` alone, by set membership:

    existed_before  - was D already a key of `zones` at T-1?
    occupied_before - was any OTHER character standing in D at T-1?

  A move to a place that already existed, or where people already are, is a move
  to a PLACE.
  A move to a zone that did not exist and that nobody occupies is the Director
  MINTING a destination for one character - which is exactly what task 79 says
  happens when a position has nowhere else to live.

    minted-and-empty  -> POSITION
    otherwise         -> ROOM CHANGE

No substring, no prefix, no token overlap. Set membership on ids and keys only.

VALIDITY CHECK FIRST, registered before the comparison is printed, in the same
shape that killed the witness signal: if nearly every destination is newly minted
(or nearly none is), the signal has no discriminating power and is reported dead
rather than dressed up as a comparison.
"""

from __future__ import annotations

import gc
import json
import pathlib
import statistics
import sys
from collections import Counter
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from classify_positional import distinct_sessions, norm  # noqa: E402
from find_reproducible_payloads import is_positional  # noqa: E402


@dataclass
class Move:
    session: str
    turn: int
    cid: str
    origin: str
    dest: str
    existed_before: bool
    occupied_before: bool
    string_says_position: bool

    @property
    def structural_says_position(self) -> bool:
        return not self.existed_before and not self.occupied_before

    @property
    def agree(self) -> bool:
        return self.structural_says_position == self.string_says_position


def snapshots(base: pathlib.Path) -> dict[int, dict]:
    """Zones and positions as they stood at the END of each turn."""
    state = json.loads((base / "state.json").read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for record in state.get("history", []):
        turn = record.get("turn_number")
        snap = record.get("scene_snapshot") or {}
        if turn is None:
            continue
        if snap.get("positions") or snap.get("zones"):
            out[int(turn)] = {
                "zones": {norm(z) for z in (snap.get("zones") or {})},
                "positions": {c: norm(z) for c, z in (snap.get("positions") or {}).items()},
            }
    return out


def main() -> None:
    moves: list[Move] = []
    coverage = Counter()
    for sid, base in sorted(distinct_sessions().items()):
        snaps = snapshots(base)
        debug = base / "debug.jsonl"
        if not debug.exists():
            continue
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
                try:
                    parsed = json.loads(record.get("response") or "{}")
                except json.JSONDecodeError:
                    continue
                turn = int(record["turn_number"])
                zone_moves = parsed.get("zone_moves") or {}
                if not isinstance(zone_moves, dict):
                    continue
                prior = snaps.get(turn - 1)
                if not prior:
                    coverage["no_prior_snapshot"] += len(zone_moves)
                    continue
                for cid, dest in zone_moves.items():
                    coverage["total"] += 1
                    origin = prior["positions"].get(str(cid))
                    if not origin:
                        coverage["no_origin"] += 1
                        continue
                    flat_dest = norm(str(dest))
                    existed = flat_dest in prior["zones"]
                    occupied = any(
                        z == flat_dest and c != str(cid) for c, z in prior["positions"].items()
                    )
                    coverage["usable"] += 1
                    moves.append(
                        Move(
                            sid, turn, str(cid), origin, str(dest), existed, occupied,
                            is_positional(str(dest), origin),
                        )
                    )
        gc.collect()

    print("=== COVERAGE ===")
    for key, value in sorted(coverage.items()):
        print(f"  {key:20} {value}")
    if not moves:
        print("no comparable moves")
        return

    minted = sum(1 for m in moves if not m.existed_before)
    empty = sum(1 for m in moves if not m.occupied_before)
    signal = sum(1 for m in moves if m.structural_says_position)
    print("\n=== VALIDITY CHECK (registered before the comparison) ===")
    print(f"  destination did NOT exist at T-1: {minted}/{len(moves)} = {minted / len(moves):.1%}")
    print(f"  destination unoccupied at T-1:    {empty}/{len(moves)} = {empty / len(moves):.1%}")
    print(f"  both (signal fires):              {signal}/{len(moves)} = {signal / len(moves):.1%}")
    if signal / len(moves) > 0.9 or signal / len(moves) < 0.1:
        print("\n  >>> DEAD: the signal fires on nearly all or nearly no moves.")
    else:
        print("\n  >>> usable: the signal separates the corpus.")

    agree = sum(1 for m in moves if m.agree)
    print("\n=== AGREEMENT with the corrected string rule ===")
    print(f"  comparable moves: {len(moves)}")
    print(f"  agree: {agree} = {agree / len(moves):.1%}")
    print("\n  confusion:")
    for sv in (True, False):
        for tv in (True, False):
            n = sum(
                1 for m in moves if m.structural_says_position == sv and m.string_says_position == tv
            )
            print(f"    structural={'POS ' if sv else 'ROOM'}  string={'POS ' if tv else 'ROOM'}: {n}")

    per: dict[str, list[bool]] = {}
    for m in moves:
        per.setdefault(m.session, []).append(m.agree)
    rates = [sum(v) / len(v) for v in per.values() if len(v) >= 3]
    if rates:
        print(f"\n  per session (n={len(rates)}): median {statistics.median(rates):.1%}  "
              f"range {min(rates):.1%}-{max(rates):.1%}")

    print("\n=== DISAGREEMENTS (read these) ===")
    dis = [m for m in moves if not m.agree]
    step = max(1, len(dis) // 12)
    for m in dis[::step][:12]:
        print(f"\n  [{m.session} T{m.turn} {m.cid}] structural="
              f"{'POS' if m.structural_says_position else 'ROOM'} "
              f"string={'POS' if m.string_says_position else 'ROOM'} "
              f"(existed={m.existed_before} occupied={m.occupied_before})")
        print(f"     from: {m.origin[:86]}")
        print(f"       to: {m.dest[:86]}")


if __name__ == "__main__":
    main()
