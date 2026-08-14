"""Task 79's cheap falsifier: does the Director use a blocking slot if offered?

The decision rule is pre-registered in `.plan/tasks/79-blocking-as-durable-state.md`
under "The slot replay". Summary, so this file stands alone:

  The field is worth building only if BOTH hold.
    1. B populates `blocking` on a majority of runs, with content naming a position.
    2. B's positional-`zone_moves` rate falls materially below A's.

  FALSIFIER for task 79: if B ignores the slot, or keeps minting positional zones
  at A's rate, the missing field is not the fix and no schema should ship.

  GUARD: if B's `zone_moves` collapses to null everywhere that is NOT a win. It
  would mean the Director stopped moving people rather than relocating the
  detail, trading this defect for task 77's. Reported separately; blocks clause 2.

PAYLOADS, chosen on recorded output before any new call: `09aabf25` T7 and T22,
both of which recorded positional `zone_moves` and so have something to redirect.

METHOD: arm B substitutes into the RECORDED system prompt rather than rebuilding
it, so position inside the prompt is preserved (AGENTS.md section 6). Nothing here
touches `src/`; the Director call uses `response_format: {"type": "json_object"}`,
so a new key is expressible by prompt alone. Task 79 stays docs-only.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import re
import sys
import unicodedata
from dataclasses import dataclass, field

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

SESSION = pathlib.Path(
    "/home/alex/git/my/alex-tavern/plans/artifacts/repetition-battery/"
    "base-P1-r1/sessions/09aabf25/debug.jsonl"
)
OUT = pathlib.Path(__file__).parent / "runs"
RUNS = 4
PAYLOAD_TURNS = (7, 22)

ANCHOR = '- "zone_moves": null OR an object mapping character_id to the zone they'

# Inserted immediately BEFORE the zone_moves entry, so the reader meets the
# distinction before the field that has been absorbing both meanings.
SLOT = (
    '- "blocking": null OR an object mapping character_id to a short phrase for\n'
    "  WHERE THEY STAND inside the place they already occupy (\"junto a porta\",\n"
    '  "atras da mesa virada", "entre a fenda e os alunos"). This is staging, not\n'
    "  a move: it never changes which zone anyone is in and it never affects who\n"
    "  can hear whom. Use it whenever a character shifts position without leaving\n"
    "  the place they are in.\n"
    '- "zone_moves" is for CHANGING PLACE, not for position inside one. If someone\n'
    '  crosses the room they are already in, that is "blocking" and zone_moves\n'
    "  stays null for them.\n"
)

# Matched against ACCENT-STRIPPED text. Written unaccented for the same reason:
# the first version had "proxim[oa] a" and missed "proximo A-GRAVE saida sul", a
# real recorded destination, because the preposition carries a grave accent. That
# is the fourth detector in this project to fail on a character class, so this one
# normalizes first and never sees an accent at all.
POSITIONAL = re.compile(
    r"(junto a|ao lado de|proxim[oa] a|perto de|entre |atras de|em frente|na borda|"
    r"posicionand|avancando|recuando|escalando|diante de|encostad|no centro de|ao pe de)",
    re.I,
)


def _norm(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )


@dataclass
class Payload:
    turn: int
    messages: list[dict]
    max_tokens: int
    origins: dict[str, str]


def load_payloads() -> dict[int, Payload]:
    """Recorded request per turn, plus where each character stood beforehand.

    Origins come from the state snapshot of the PREVIOUS turn, because a
    destination only counts as positional if it names the place the mover was
    already in.
    """
    state = json.loads((SESSION.parent / "state.json").read_text(encoding="utf-8"))
    positions: dict[int, dict] = {}
    for record in state.get("history", []):
        turn = record.get("turn_number")
        snapshot = record.get("scene_snapshot") or {}
        if turn is not None and snapshot.get("positions"):
            positions.setdefault(int(turn), snapshot["positions"])

    found: dict[int, Payload] = {}
    for line in SESSION.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("agent") != "director":
            continue
        turn = record.get("turn_number")
        if turn not in PAYLOAD_TURNS or turn in found:
            continue
        request = record["request"]
        found[turn] = Payload(
            turn=turn,
            messages=[dict(m) for m in request["messages"]],
            max_tokens=request.get("max_tokens", 24576),
            origins=positions.get(turn - 1, {}),
        )
    missing = set(PAYLOAD_TURNS) - set(found)
    if missing:
        raise SystemExit(f"payload turns not found: {sorted(missing)}")
    return found


def build_variant(payload: Payload, arm: str) -> list[dict]:
    messages = [dict(m) for m in payload.messages]
    system = messages[0]
    if system.get("role") != "system":
        raise SystemExit(f"turn {payload.turn}: first message is not the system prompt")
    if arm == "A":
        return messages
    text = system["content"]
    if text.count(ANCHOR) != 1:
        raise SystemExit(f"turn {payload.turn}: expected exactly one zone_moves entry")
    system["content"] = text.replace(ANCHOR, SLOT + ANCHOR)
    return messages


def is_positional(destination: str, origin: str | None) -> bool:
    """A destination that names a spot inside the place the mover already was.

    Two ways to qualify, because the Director expresses the same act in two
    naming conventions and a detector that sees only one reports 0% on sessions
    that are doing it constantly (see task 79, "Measured, with the spread").
    """
    flat = _norm(destination)
    if origin and "," in destination and _norm(destination.split(",")[0]) in _norm(origin):
        return True
    return bool(POSITIONAL.search(flat))


@dataclass
class RunResult:
    turn: int
    arm: str
    run: int
    ok: bool
    blocking_entries: int = 0
    blocking_text: list[str] = field(default_factory=list)
    moves: int = 0
    positional_moves: int = 0
    destinations: list[str] = field(default_factory=list)
    error: str = ""


def score(payload: Payload, arm: str, run: int, raw: str) -> RunResult:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return RunResult(payload.turn, arm, run, ok=False, error=f"bad json: {exc}")
    blocking = parsed.get("blocking") or {}
    if not isinstance(blocking, dict):
        blocking = {}
    moves = parsed.get("zone_moves") or {}
    if not isinstance(moves, dict):
        moves = {}
    positional = [
        dest for cid, dest in moves.items() if is_positional(str(dest), payload.origins.get(cid))
    ]
    return RunResult(
        payload.turn,
        arm,
        run,
        ok=True,
        blocking_entries=len(blocking),
        blocking_text=[str(v) for v in blocking.values()][:4],
        moves=len(moves),
        positional_moves=len(positional),
        destinations=sorted({str(v) for v in moves.values()}),
    )


async def fire(
    client: httpx.AsyncClient, cfg: dict, payload: Payload, arm: str, run: int
) -> RunResult:
    body = {
        "model": cfg["model"],
        "messages": build_variant(payload, arm),
        "max_tokens": payload.max_tokens,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }
    try:
        response = await client.post(
            f"{cfg['api_base']}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json=body,
            timeout=300.0,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 - a failed call is a datum, not a crash
        return RunResult(payload.turn, arm, run, ok=False, error=f"{type(exc).__name__}: {exc}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"T{payload.turn}-{arm}-r{run}.json").write_text(raw, encoding="utf-8")
    return score(payload, arm, run, raw)


async def main() -> None:
    cfg = json.loads(
        pathlib.Path("/home/alex/git/my/alex-tavern/.data/config.json").read_text(encoding="utf-8")
    )["providers"]["deepseek"]
    payloads = load_payloads()
    jobs = [
        (payloads[turn], arm, run)
        for turn in PAYLOAD_TURNS
        for arm in ("A", "B")
        for run in range(1, RUNS + 1)
    ]
    print(f"firing {len(jobs)} calls at {cfg['model']}", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(job):  # noqa: ANN001, ANN202
            async with semaphore:
                result = await fire(client, cfg, *job)
                print(
                    f"  T{result.turn} {result.arm} r{result.run}: "
                    f"blocking={result.blocking_entries} moves={result.moves} "
                    f"positional={result.positional_moves} {result.error}",
                    flush=True,
                )
                return result

        results = await asyncio.gather(*(guarded(job) for job in jobs))

    print()
    for arm in ("A", "B"):
        rows = [r for r in results if r.arm == arm and r.ok]
        if not rows:
            continue
        slot = sum(1 for r in rows if r.blocking_entries)
        moves = sum(r.moves for r in rows)
        pos = sum(r.positional_moves for r in rows)
        null_moves = sum(1 for r in rows if r.moves == 0)
        share = f"{pos / moves:.0%}" if moves else "n/a"
        print(
            f"ARM {arm}: runs={len(rows)}  slot populated {slot}/{len(rows)}  "
            f"zone_moves={moves} of which positional={pos} ({share})"
        )
        print(f"        runs with zone_moves EMPTY (guard clause): {null_moves}/{len(rows)}")
    print()
    print("blocking content produced by B (read this, do not trust the count):")
    for r in results:
        if r.arm == "B" and r.blocking_text:
            print(f"  T{r.turn} r{r.run}: {r.blocking_text}")
    print()
    print("positional destinations still minted, by arm:")
    for arm in ("A", "B"):
        dests = sorted(
            {
                d
                for r in results
                if r.arm == arm and r.ok
                for d in r.destinations
                if POSITIONAL.search(d) or "," in d
            }
        )
        print(f"  {arm}: {dests}")

    (OUT / "summary.json").write_text(
        json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
