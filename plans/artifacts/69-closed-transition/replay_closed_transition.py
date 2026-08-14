"""Task 69's thesis, tested before any code: does an output constraint stop it?

The decision rule is pre-registered in `.plan/tasks/69-physical-state-as-closed-transition.md`
under "The closed-transition replay". Summary, so this file stands alone:

  A = the recorded system prompt verbatim.
  B = one extra bullet in the existing RULES block: SETTLED FACTS DO NOT HAPPEN
      TWICE. Restatement forbidden, transition and consequence explicitly allowed.

  recurrence = a run emits an event matching the known re-staged original at
  sim >= 0.6.

  ADOPT if B's recurrence <= half of A's AND B's mean event count >= 70% of A's.
  WORSE if B's recurrence falls but the event count collapses - the rule bought
  silence rather than coherence.
  MECHANICAL if B's recurrence does not fall - a clause is not enough and the
  engine has to reject the transition, which is the expensive answer.
  VARIANCE if A's own recurrence is under 40% of runs - then the re-staging is
  not a contract property and neither arm can be credited. This is the outcome
  task 77's identically-shaped replay produced, and it is registered in advance.

PAYLOADS, chosen on recorded output before any new call: the four cases from the
visibility read where the original was demonstrably in the prompt and the
Director re-staged it anyway.

METHOD: B substitutes into the RECORDED system prompt rather than rebuilding it,
so position is preserved (AGENTS.md section 6). Nothing here touches `src/`.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern/plans/artifacts")
OUT = pathlib.Path(__file__).parent / "runs"
RUNS = 4
TAU = 0.6

# (session, repeat turn, the original event the recorded run re-staged)
PAYLOADS = [
    (
        "834f91e5",
        29,
        "Com um estrondo, garras enormes rompem a parede atrás dos guardas, "
        "lançando estilhaços de pedra contra o grupo e arrancando um grito do aluno ferido.",
    ),
    (
        "8bd4d0f1",
        38,
        "Liora Celestria solta um grito breve antes de desabar sob os escombros, "
        "e seus chamados cessam por completo.",
    ),
    (
        "a3e1ceda",
        22,
        "A diretora Maelis bate a bengala no piso e, com voz de comando, determina que "
        "as forças de resposta saiam imediatamente pela porta leste e que os demais "
        "se preparem para reforço.",
    ),
    (
        "d5a2ccf0",
        32,
        "Um projétil mágico atinge a parede atrás de Link, lançando estilhaços de pedra.",
    ),
]

ANCHOR = "- Resolve the immediate consequence of the final HISTORY event before adding"

CLAUSE = (
    "- SETTLED FACTS DO NOT HAPPEN TWICE. Every entry in Physical facts is already\n"
    "  true, and every HISTORY line has already been perceived. Do not emit a\n"
    "  perception_event that states one of them again, however differently worded.\n"
    "  An event MAY change a settled fact to a new state, and MAY describe its\n"
    "  consequences; it may never re-stage the moment it became true.\n"
)


def norm(text: str) -> str:
    flat = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", flat).strip()


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


@dataclass
class Payload:
    session: str
    turn: int
    original: str
    messages: list[dict]
    max_tokens: int


def load_payloads() -> list[Payload]:
    out = []
    for session, turn, original in PAYLOADS:
        base = next(p.parent for p in ROOT.rglob("state.json") if p.parent.name == session)
        found = None
        with (base / "debug.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("agent") == "director" and record.get("turn_number") == turn:
                    found = record
                    break
        if found is None:
            raise SystemExit(f"{session} T{turn}: no director record")
        request = found["request"]
        out.append(
            Payload(
                session,
                turn,
                original,
                [dict(m) for m in request["messages"]],
                request.get("max_tokens", 24576),
            )
        )
    return out


def build(payload: Payload, arm: str) -> list[dict]:
    messages = [dict(m) for m in payload.messages]
    system = messages[0]
    if system.get("role") != "system":
        raise SystemExit(f"{payload.session} T{payload.turn}: first message is not the system prompt")
    if arm == "A":
        return messages
    text = system["content"]
    if text.count(ANCHOR) != 1:
        raise SystemExit(f"{payload.session} T{payload.turn}: anchor not unique")
    system["content"] = text.replace(ANCHOR, CLAUSE + ANCHOR)
    return messages


@dataclass
class Result:
    session: str
    turn: int
    arm: str
    run: int
    ok: bool
    events: int = 0
    recurred: bool = False
    best: float = 0.0
    best_text: str = ""
    texts: list[str] = field(default_factory=list)
    error: str = ""


def score(payload: Payload, arm: str, run: int, raw: str) -> Result:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return Result(payload.session, payload.turn, arm, run, ok=False, error=f"bad json: {exc}")
    texts = [
        str(e.get("content") or "")
        for e in (parsed.get("perception_events") or [])
        if isinstance(e, dict)
    ]
    best, best_text = 0.0, ""
    for text in texts:
        value = sim(payload.original, text)
        if value > best:
            best, best_text = value, text
    return Result(
        payload.session,
        payload.turn,
        arm,
        run,
        ok=True,
        events=len(texts),
        recurred=best >= TAU,
        best=best,
        best_text=best_text,
        texts=texts,
    )


async def fire(client: httpx.AsyncClient, cfg: dict, payload: Payload, arm: str, run: int) -> Result:
    body = {
        "model": cfg["model"],
        "messages": build(payload, arm),
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
        return Result(
            payload.session, payload.turn, arm, run, ok=False, error=f"{type(exc).__name__}: {exc}"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{payload.session}-T{payload.turn}-{arm}-r{run}.json").write_text(raw, encoding="utf-8")
    return score(payload, arm, run, raw)


async def main() -> None:
    cfg = json.loads(
        pathlib.Path("/home/alex/git/my/alex-tavern/.data/config.json").read_text(encoding="utf-8")
    )["providers"]["deepseek"]
    payloads = load_payloads()
    jobs = [(p, arm, run) for p in payloads for arm in ("A", "B") for run in range(1, RUNS + 1)]
    print(f"firing {len(jobs)} calls at {cfg['model']}", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(job):  # noqa: ANN001, ANN202
            async with semaphore:
                result = await fire(client, cfg, *job)
                print(
                    f"  {result.session} T{result.turn} {result.arm} r{result.run}: "
                    f"events={result.events} recurred={result.recurred} "
                    f"best={result.best:.2f} {result.error}",
                    flush=True,
                )
                return result

        results = await asyncio.gather(*(guarded(job) for job in jobs))

    print()
    stats = {}
    for arm in ("A", "B"):
        rows = [r for r in results if r.arm == arm and r.ok]
        if not rows:
            continue
        rec = sum(1 for r in rows if r.recurred)
        events = sum(r.events for r in rows) / len(rows)
        stats[arm] = (rec / len(rows), events)
        print(f"ARM {arm}: runs={len(rows)}  recurrence {rec}/{len(rows)} = {rec / len(rows):.0%}  "
              f"mean events/run {events:.2f}")

    if "A" in stats and "B" in stats:
        a_rec, a_ev = stats["A"]
        b_rec, b_ev = stats["B"]
        print()
        print(f"pre-registered gates: B recurrence <= {a_rec / 2:.0%} (half of A)  "
              f"AND B events >= {a_ev * 0.7:.2f} (70% of A)")
        if a_rec < 0.40:
            print("VERDICT: A's own recurrence is under 40% -> VARIANCE row. "
                  "Neither arm credited; design question untouched.")
        elif b_rec <= a_rec / 2 and b_ev >= a_ev * 0.7:
            print("VERDICT: ADOPT row - a contract clause is enough.")
        elif b_rec <= a_rec / 2:
            print("VERDICT: WORSE row - the rule bought silence. Not adopted.")
        else:
            print("VERDICT: MECHANICAL row - a clause is not enough.")

    print()
    print("per payload:")
    for session, turn, _ in PAYLOADS:
        for arm in ("A", "B"):
            rows = [r for r in results if r.session == session and r.arm == arm and r.ok]
            if rows:
                rec = sum(1 for r in rows if r.recurred)
                print(f"  {session} T{turn} {arm}: recurred {rec}/{len(rows)}  "
                      f"events {sum(r.events for r in rows) / len(rows):.1f}")

    print()
    print("closest event to the re-staged original, per run (READ THIS):")
    for r in results:
        if r.ok and r.best_text:
            print(f"  {r.session} {r.arm} r{r.run} [{r.best:.2f}]: {r.best_text[:150]}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(
        json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
