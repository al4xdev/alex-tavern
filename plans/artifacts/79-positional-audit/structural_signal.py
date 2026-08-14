"""Task 79: room-vs-position measured WITHOUT matching any zone name.

Rule pre-registered in `.plan/tasks/79-blocking-as-durable-state.md` under
"The structural test", before this ran.

The signal is the Director's own proposed `witness_ids` - sets of character ids,
compared by set arithmetic. No string is ever tested against a place name. It
reads the raw response in `debug.jsonl`, not the persisted audience, so it is the
Director's belief formed BEFORE the engine's name-derived graph touches it.

For a move C: O -> D at turn T, with `peers` = whoever else stood in O at T-1:
  together = events of turn T whose witness_ids hold C and at least one peer
  apart    = events holding C but no peer, or a peer but not C
  together > apart  -> POSITION (still co-present with the people left behind)
  apart >= together -> ROOM CHANGE

The validity check runs first and can kill the whole thing: if the Director lists
nearly everyone as a witness of nearly everything, the signal cannot discriminate.
"""

from __future__ import annotations

import gc
import json
import pathlib
import statistics
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from classify_positional import distinct_sessions  # noqa: E402
from find_reproducible_payloads import is_positional, positions_by_turn  # noqa: E402


@dataclass
class Move:
    session: str
    turn: int
    cid: str
    origin: str
    dest: str
    peers: int
    together: int
    apart: int
    string_says_position: bool

    @property
    def structural_says_position(self) -> bool:
        return self.together > self.apart

    @property
    def agree(self) -> bool:
        return self.structural_says_position == self.string_says_position


def main() -> None:
    moves: list[Move] = []
    coverage = {"total": 0, "no_peers": 0, "no_events": 0, "usable": 0}
    witness_fractions: list[float] = []

    for sid, base in sorted(distinct_sessions().items()):
        positions = positions_by_turn(base)
        debug = base / "debug.jsonl"
        if not debug.exists():
            continue
        by_turn: dict[int, dict] = {}
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
                by_turn[int(record["turn_number"])] = parsed

        for turn, parsed in sorted(by_turn.items()):
            events = [e for e in (parsed.get("perception_events") or []) if isinstance(e, dict)]
            witness_sets = [
                {str(w) for w in (e.get("witness_ids") or []) if w}
                for e in events
            ]
            prior = positions.get(turn - 1, {})
            cast = len(prior) or len(set().union(*witness_sets)) if witness_sets else 0
            if cast:
                witness_fractions.extend(len(w) / cast for w in witness_sets if w)

            zone_moves = parsed.get("zone_moves") or {}
            if not isinstance(zone_moves, dict):
                continue
            for cid, dest in zone_moves.items():
                coverage["total"] += 1
                origin = prior.get(str(cid))
                if not origin:
                    coverage["no_peers"] += 1
                    continue
                peers = {c for c, z in prior.items() if z == origin and c != str(cid)}
                if not peers:
                    coverage["no_peers"] += 1
                    continue
                if not witness_sets:
                    coverage["no_events"] += 1
                    continue
                together = apart = 0
                for wset in witness_sets:
                    if not wset:
                        continue
                    has_c = str(cid) in wset
                    has_peer = bool(peers & wset)
                    if has_c and has_peer:
                        together += 1
                    elif has_c != has_peer:
                        apart += 1
                if together + apart == 0:
                    coverage["no_events"] += 1
                    continue
                coverage["usable"] += 1
                moves.append(
                    Move(
                        sid, turn, str(cid), origin, str(dest), len(peers),
                        together, apart, is_positional(str(dest), origin),
                    )
                )
        gc.collect()

    print("=== VALIDITY CHECK (runs first; can kill the signal) ===")
    med = statistics.median(witness_fractions)
    print(f"|witness_ids| / cast, over {len(witness_fractions)} events:")
    print(f"  median {med:.2f}   mean {statistics.mean(witness_fractions):.2f}")
    q = statistics.quantiles(witness_fractions, n=4)
    print(f"  quartiles {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f}")
    if med > 0.9:
        print("\n  >>> MEDIAN ABOVE 0.90 - the signal cannot discriminate. Reported as dead.")
    else:
        print("\n  >>> below 0.90: the Director does scope its witness lists. Signal is usable.")

    print("\n=== COVERAGE ===")
    for key, value in coverage.items():
        print(f"  {key:10} {value}")

    if not moves:
        print("no comparable moves")
        return

    agree = sum(1 for m in moves if m.agree)
    print("\n=== AGREEMENT, structural vs the corrected string rule ===")
    print(f"  comparable moves: {len(moves)}")
    print(f"  agree:            {agree}  ({agree / len(moves):.1%})")
    s_pos = sum(1 for m in moves if m.structural_says_position)
    t_pos = sum(1 for m in moves if m.string_says_position)
    print(f"  structural says POSITION: {s_pos} ({s_pos / len(moves):.1%})")
    print(f"  string     says POSITION: {t_pos} ({t_pos / len(moves):.1%})")
    print("\n  confusion:")
    for sv in (True, False):
        for tv in (True, False):
            n = sum(1 for m in moves if m.structural_says_position == sv and m.string_says_position == tv)
            print(f"    structural={'POS' if sv else 'ROOM'}  string={'POS' if tv else 'ROOM'}: {n}")

    rates = {}
    for m in moves:
        rates.setdefault(m.session, []).append(m.agree)
    per = [sum(v) / len(v) for v in rates.values() if len(v) >= 3]
    if per:
        print(f"\n  per session (n={len(per)}): median {statistics.median(per):.1%}  "
              f"range {min(per):.1%}-{max(per):.1%}")

    print("\n=== THE DISAGREEMENT SET (read this) ===")
    dis = [m for m in moves if not m.agree]
    step = max(1, len(dis) // 14)
    for m in dis[::step][:14]:
        print(f"\n  [{m.session} T{m.turn} {m.cid}] structural={'POS' if m.structural_says_position else 'ROOM'} "
              f"string={'POS' if m.string_says_position else 'ROOM'} (together={m.together} apart={m.apart} peers={m.peers})")
        print(f"     from: {m.origin[:88]}")
        print(f"       to: {m.dest[:88]}")


if __name__ == "__main__":
    main()
