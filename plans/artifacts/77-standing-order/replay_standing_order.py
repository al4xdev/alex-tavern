"""Task 77: does the Director enact a standing order if its contract lets it?

PRE-REGISTERED DECISION RULE - written before any call was fired.

  Task 77 read a transcript where the Director orders everyone through the north
  gate on three consecutive turns and moves nobody. Reading the contract, two
  rules explain that behaviour as OBEDIENCE rather than failure:

    rule 3  "Resolve the final HISTORY action" - singular, so fifteen of sixteen
            declared attempts are out of scope before the turn starts.
    rule 2  "Meaningful travel ... ends only after a later explicit arrival.
            Never teleport someone ... or skip the journey."

  Arm A is the RECORDED system prompt, verbatim. Arm B makes two surgical edits
  that permit enacting an order already in force, and keeps the anti-teleport
  intent that rule 2 exists for.

  B is a CANDIDATE for a contract change if BOTH hold:

  (1) ENACTMENT RISES. Non-empty `zone_moves` on materially more runs under B
      than under A - at least twice the A rate and at least half of B's runs.

  (2) IT DOES NOT TELEPORT. Reading every destination B produces, the moves go
      where the standing order sends people. A Director that starts scattering
      characters to invented places has not fixed the scene, it has broken the
      rule that rule 2 exists to enforce, and clause (2) is the one that
      matters: clause (1) is trivially winnable by a Director that moves people
      at random.

  FALSIFIER for task 77 itself: if arm A already emits non-empty `zone_moves` on
  half its runs or more, the recorded nulls were sampling noise, the diagnosis in
  task 77 is wrong, and the task should be re-opened rather than acted on.

  Reported but NOT deciding: number of characters moved, next_speakers, event
  counts. They describe the arms; they do not gate them.

PAYLOAD CHOICE, also pre-registered, on the RECORDED output only:
  T32 - recorded `zone_moves: null` with the gate order standing since T31.
  T34 - recorded `zone_moves: null`, the order still standing three turns later.
  Both are turns where the scene demonstrably failed to move, so both have
  something to enact. Chosen before any new call.

METHOD: edits are substituted into the RECORDED system prompt rather than
rebuilt, so position inside the prompt is preserved (AGENTS.md section 6). This
harness does NOT read the production builder, because the change it tests is not
shipped: if B wins, the text here becomes the patch and gets re-validated as the
shipped variant.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

SESSION = pathlib.Path(
    "/home/alex/git/my/alex-tavern/plans/artifacts/repetition-battery/"
    "base-P1-r1/sessions/09aabf25/debug.jsonl"
)
OUT = pathlib.Path(__file__).parent / "runs"
RUNS = 4
PAYLOAD_TURNS = (32, 34)

OLD_RESOLVE = (
    "3. RESOLVE LOCALLY. Resolve the final HISTORY action only where its actor\n"
    "   currently is. Describe only its immediate local consequence before adding\n"
    "   any event elsewhere."
)
NEW_RESOLVE = (
    "3. RESOLVE LOCALLY, AND ENACT WHAT WAS ORDERED. Resolve the final HISTORY\n"
    "   action where its actor currently is, and describe only its immediate\n"
    "   local consequence before adding any event elsewhere. When an instruction\n"
    "   already given in HISTORY is being followed, also enact it: put the\n"
    "   characters who accepted it where it sends them, using zone_moves, in this\n"
    "   beat. An order the room agrees to and nobody carries out is the scene\n"
    "   failing to move."
)

OLD_TRAVEL = (
    " Meaningful travel takes multiple beats when the\n"
    "   fiction requires it and ends only after a later explicit arrival. Never\n"
    "   teleport someone, invent a convenient connection, or skip the journey just\n"
    "   to bring characters together."
)
NEW_TRAVEL = (
    " Meaningful travel takes multiple beats when the\n"
    "   fiction requires it. A short move inside the current place, or one a\n"
    "   standing order names, completes in the beat where it is taken. Never\n"
    "   teleport someone across the map, invent a convenient connection, or skip\n"
    "   a journey just to bring characters together."
)


@dataclass
class Payload:
    turn: int
    messages: list[dict]
    max_tokens: int


def load_payloads() -> dict[int, Payload]:
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
        )
    missing = set(PAYLOAD_TURNS) - set(found)
    if missing:
        raise SystemExit(f"payload turns not found: {sorted(missing)}")
    return found


def build_variant(payload: Payload, variant: str) -> list[dict]:
    messages = [dict(m) for m in payload.messages]
    system = messages[0]
    if system.get("role") != "system":
        raise SystemExit(f"turn {payload.turn}: first message is not the system prompt")
    if variant == "A":
        return messages
    text = system["content"]
    for old, new in ((OLD_RESOLVE, NEW_RESOLVE), (OLD_TRAVEL, NEW_TRAVEL)):
        if text.count(old) != 1:
            raise SystemExit(f"turn {payload.turn}: expected exactly one {old[:44]!r}")
        text = text.replace(old, new)
    system["content"] = text
    return messages


@dataclass
class RunResult:
    turn: int
    variant: str
    run: int
    ok: bool
    enacted: bool = False
    moved: int = 0
    destinations: list[str] = field(default_factory=list)
    speakers: list[str] = field(default_factory=list)
    events: int = 0
    error: str = ""


def score(turn: int, variant: str, run: int, raw: str) -> RunResult:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return RunResult(turn, variant, run, ok=False, error=f"bad json: {exc}")
    moves = parsed.get("zone_moves") or {}
    if not isinstance(moves, dict):
        moves = {}
    return RunResult(
        turn,
        variant,
        run,
        ok=True,
        enacted=bool(moves),
        moved=len(moves),
        destinations=sorted({str(v) for v in moves.values()}),
        speakers=list(parsed.get("next_speakers") or []),
        events=len(parsed.get("perception_events") or []),
    )


async def fire(
    client: httpx.AsyncClient, cfg: dict, payload: Payload, variant: str, run: int
) -> RunResult:
    body = {
        "model": cfg["model"],
        "messages": build_variant(payload, variant),
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
        return RunResult(payload.turn, variant, run, ok=False, error=f"{type(exc).__name__}: {exc}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"T{payload.turn}-{variant}-r{run}.json").write_text(raw, encoding="utf-8")
    return score(payload.turn, variant, run, raw)


async def main() -> None:
    cfg = json.loads(
        pathlib.Path("/home/alex/git/my/alex-tavern/.data/config.json").read_text(encoding="utf-8")
    )["providers"]["deepseek"]
    payloads = load_payloads()
    jobs = [
        (payloads[turn], variant, run)
        for turn in PAYLOAD_TURNS
        for variant in ("A", "B")
        for run in range(1, RUNS + 1)
    ]
    print(f"firing {len(jobs)} calls at {cfg['model']}", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(job):  # noqa: ANN001, ANN202
            async with semaphore:
                result = await fire(client, cfg, *job)
                flag = "MOVED" if result.enacted else ("err" if not result.ok else "-----")
                print(
                    f"  T{result.turn} {result.variant} r{result.run}: {flag} "
                    f"moved={result.moved} dest={result.destinations} {result.error}",
                    flush=True,
                )
                return result

        results = await asyncio.gather(*(guarded(job) for job in jobs))

    print()
    for turn in PAYLOAD_TURNS:
        for variant in ("A", "B"):
            rows = [r for r in results if r.turn == turn and r.variant == variant and r.ok]
            if not rows:
                continue
            enacted = sum(1 for r in rows if r.enacted)
            print(
                f"T{turn} arm {variant}: enacted {enacted}/{len(rows)}  "
                f"mean moved {sum(r.moved for r in rows) / len(rows):.2f}"
            )
    for variant in ("A", "B"):
        rows = [r for r in results if r.variant == variant and r.ok]
        enacted = sum(1 for r in rows if r.enacted)
        print(f"ARM {variant} TOTAL: enacted {enacted}/{len(rows)}")
    print()
    print("destinations produced (read these, do not trust the count):")
    for variant in ("A", "B"):
        dests = sorted({d for r in results if r.variant == variant and r.ok for d in r.destinations})
        print(f"  {variant}: {dests}")

    (OUT / "summary.json").write_text(
        json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
