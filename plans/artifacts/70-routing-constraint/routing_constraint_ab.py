"""Task 70: choose the FORM of the fix for the named exclusion in the Director prompt.

AGENTS.md section 3 settles WHETHER: a rule that separates exactly one character
encodes controlled_character_id, and "uma invariante que aceita reprovacao por
metrica de qualidade nao e invariante". So this experiment cannot vote to keep
variant A. It chooses between the id-free replacements.

The task's own suggested direction - constrain the candidate set the model
chooses from - is ALREADY REJECTED IN THIS REPO with a measurement
(narrator.py:298-303): a narrowed enum made the provider-side validator reject
responses the lenient normalization was built to absorb, 3 straight schema
failures on a stalled skip turn. So the schema is not available and the choice
is between prompt formulations, with the code doing the enforcing either way.

WHAT THE CODE ALREADY DOES, which is why deletion is even on the table:
narrator.py:745 drops the excluded id from next_speakers during normalization
(`entry != exclude_speaker`), and :747 falls back to ["Narrator"] if that empties
the queue. The invariant is therefore held by code, not by this prompt line. The
line only stops the Director from spending routing slots on a character the code
will discard.

VARIANTS
  A  recorded, the named exclusion              (baseline; may not ship)
  B  the ROUTING CONSTRAINT block deleted       (the code still enforces)
  C  the block kept, the exclusion removed      (dramatic reason, no id)

PRE-REGISTERED DECISION RULE, written before any call:

  1. PRIMARY - queue health. An id-free variant is acceptable if its rate of
     beats that normalize to Narrator-only is not materially above A's, and its
     mean post-normalization queue length is not materially below A's. This is
     the real risk of deletion: the Director spends slots on the controlled
     character, the code discards them, and the beat ends up with nobody
     speaking.
  2. SECONDARY, reported and non-vetoing - the raw rate at which the controlled
     character is routed. Under A this should be near zero. Under B and C it
     costs a discarded slot, never a leak, so it informs the choice between B
     and C rather than gating either.
  3. If both B and C are acceptable, SHIP B - the simpler prompt, and the one
     that keeps the policy in exactly one place instead of two.
  4. If neither is acceptable, the answer is a third id-free formulation. It is
     never A.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern")
OUT = pathlib.Path(__file__).parent / "routing"
RUNS = 4
MAX_SPEAKERS_PER_TURN = 3

PAYLOADS = (
    ("base-P2-r1", 13),
    ("oldcode-P2-r1", 13),
)

CONSTRAINT_C = (
    "ROUTING CONSTRAINT:\n"
    "  Let this beat land on whoever the last events pressed hardest, and vary\n"
    "  who carries the scene from beat to beat; the scene is more interesting\n"
    "  when attention moves."
)

_MOOD_ID_RE = re.compile(r"^\s*ID=([A-Za-z0-9_]+)\s*\|", re.MULTILINE)
_BLOCK_RE = re.compile(
    r"\nROUTING CONSTRAINT:\n  Let someone other than (?P<cid>[A-Za-z0-9_]+) carry this beat;"
    r" the scene is more interesting when attention moves\.\n"
)


@dataclass
class Payload:
    cell: str
    turn: int
    messages: list[dict]
    max_tokens: int
    controlled: str
    present: set[str]
    recorded: list[str]


def load_payloads() -> list[Payload]:
    out: list[Payload] = []
    for cell, turn in PAYLOADS:
        session = next((ROOT / f"plans/artifacts/p2-archive/{cell}/sessions").glob("*/debug.jsonl"))
        for line in session.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("agent") != "director" or record.get("error"):
                continue
            if record.get("turn_number") != turn:
                continue
            request = record["request"]
            user = request["messages"][1]["content"]
            match = _BLOCK_RE.search(user)
            if match is None:
                raise SystemExit(f"{cell} T{turn}: routing constraint block not found verbatim")
            try:
                recorded = json.loads(record["response"]).get("next_speakers") or []
            except Exception:  # noqa: BLE001
                recorded = []
            out.append(
                Payload(
                    cell=cell,
                    turn=turn,
                    messages=[dict(m) for m in request["messages"]],
                    max_tokens=request.get("max_tokens", 24576),
                    controlled=match.group("cid"),
                    present=set(_MOOD_ID_RE.findall(user)),
                    recorded=[str(x) for x in recorded],
                )
            )
            break
    if len(out) != len(PAYLOADS):
        raise SystemExit("not every payload was found")
    return out


def build(payload: Payload, variant: str) -> list[dict]:
    messages = [dict(m) for m in payload.messages]
    user = messages[1]["content"]
    match = _BLOCK_RE.search(user)
    assert match is not None
    if variant == "A":
        return messages
    if variant == "B":
        # The block's own leading blank line goes with it, which is exactly what
        # the builder emits when it never appends the block at all.
        messages[1]["content"] = user[: match.start()] + user[match.end() :]
    elif variant == "C":
        messages[1]["content"] = user[: match.start()] + "\n" + CONSTRAINT_C + "\n"
    else:
        raise SystemExit(f"unknown variant {variant}")
    return messages


def normalize(raw: list, payload: Payload) -> list[str]:
    """Exactly what narrator.py:736-747 does to the model's next_speakers."""
    valid = payload.present | {"Narrator"}
    queue: list[str] = []
    for entry in raw if isinstance(raw, list) else []:
        if entry == "Narrator":
            break
        if entry in valid and entry != payload.controlled and entry not in queue:
            queue.append(entry)
    return queue[:MAX_SPEAKERS_PER_TURN] or ["Narrator"]


@dataclass
class Row:
    cell: str
    turn: int
    variant: str
    run: int
    ok: bool
    raw: list[str] = field(default_factory=list)
    final: list[str] = field(default_factory=list)
    pc_routed: bool = False
    narrator_only: bool = False
    error: str = ""


async def fire(client: httpx.AsyncClient, cfg: dict, payload: Payload, variant: str, run: int):
    body = {
        "model": cfg["model"],
        "messages": build(payload, variant),
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
        text = response.json()["choices"][0]["message"]["content"]
        raw = [str(x) for x in (json.loads(text).get("next_speakers") or [])]
    except Exception as exc:  # noqa: BLE001
        return Row(payload.cell, payload.turn, variant, run, ok=False, error=f"{exc!r}"[:120])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{payload.cell}-T{payload.turn}-{variant}-r{run}.json").write_text(
        text, encoding="utf-8"
    )
    final = normalize(raw, payload)
    return Row(
        cell=payload.cell,
        turn=payload.turn,
        variant=variant,
        run=run,
        ok=True,
        raw=raw,
        final=final,
        pc_routed=payload.controlled in raw,
        narrator_only=final == ["Narrator"],
    )


async def main() -> None:
    cfg = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
        "deepseek"
    ]
    payloads = load_payloads()
    for p in payloads:
        print(f"{p.cell} T{p.turn}: controlled={p.controlled} present={len(p.present)} recorded={p.recorded}")
    jobs = [(p, v, r) for p in payloads for v in ("A", "B", "C") for r in range(1, RUNS + 1)]
    print(f"firing {len(jobs)} calls\n", flush=True)

    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(4)

        async def guarded(job):
            async with sem:
                row = await fire(client, cfg, *job)
                print(
                    f"  {'ok ' if row.ok else 'ERR'} {row.cell} {row.variant} r{row.run} "
                    f"raw={row.raw} pc={row.pc_routed} final={row.final} {row.error}",
                    flush=True,
                )
                return row

        rows = await asyncio.gather(*(guarded(j) for j in jobs))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps([r.__dict__ for r in rows], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report(rows)


def report(rows: list[Row]) -> None:
    print("\n" + "=" * 72)
    label = {
        "A": "A  named exclusion (recorded, MAY NOT SHIP)",
        "B": "B  block deleted",
        "C": "C  block kept, no id",
    }
    for variant in ("A", "B", "C"):
        good = [r for r in rows if r.variant == variant and r.ok]
        if not good:
            print(f"{label[variant]}: no successful runs")
            continue
        pc = sum(1 for r in good if r.pc_routed)
        narr = sum(1 for r in good if r.narrator_only)
        qlen = sum(len(r.final) for r in good if not r.narrator_only)
        speaking = [r for r in good if not r.narrator_only]
        mean_q = qlen / len(speaking) if speaking else 0.0
        print(
            f"\n{label[variant]}\n"
            f"   runs={len(good)}  PC routed raw={pc}/{len(good)}  "
            f"Narrator-only={narr}/{len(good)}  mean queue={mean_q:.2f}"
        )
        for r in good:
            print(f"     {r.cell} r{r.run}: raw={r.raw} -> {r.final}")


if __name__ == "__main__":
    asyncio.run(main())
