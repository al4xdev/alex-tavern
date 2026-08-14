"""Live validation of task 65's Director prompt variant (AGENTS.md section 6).

PRE-REGISTERED DECISION RULE - written before any call was fired.

  The NEW variant ships if, over 4 runs per payload on two real archived
  payloads:

  (1) DEFECT RATE FALLS. On the payload where the old variant demonstrably
      authors dialogue (T10, whose recorded output quoted 2 of 2), the share of
      audible_speech events carrying a quoted span is materially lower under
      NEW than under OLD.

  (2) THE CHANNEL DOES NOT COLLAPSE. On both payloads, mean audible_speech
      events per call under NEW is not near zero, and specifically stays above
      half the OLD mean. A Director that simply stops using the channel has not
      fixed the defect, it has broken WT-09.

  Both clauses must hold. Clause (2) is the one that matters: it is easy to
  "win" clause (1) by making the Director abandon the channel, which would
  silently delete facts witnesses need.

  Reported but NOT deciding: first-person voice markers, total perception_event
  count. They describe the variant, they do not gate it.

PAYLOAD CHOICE, also pre-registered:
  T10  - recorded output has 2 audible_speech, BOTH quoted. The defect is
         present, so the variant has something to fix.
  T23  - recorded output has 4 audible_speech, NONE quoted (already reported
         form). The richest turn in the session, so it is the sharpest test of
         clause (2): if the channel collapses anywhere, it collapses here.

  Chosen on the RECORDED (old-variant) output only, before any new call.

METHOD: the two changed blocks are substituted into the RECORDED system prompt
rather than rebuilt, so position inside the prompt is preserved exactly
(AGENTS.md section 6, measured 2026-07-18: same rules at the END worked 3/3,
buried in the MIDDLE failed 3/3). The NEW text is read out of the production
builder, so the validated text IS the shipped text.
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

from src.agents.narrator import _build_system_prompt  # noqa: E402

ARCHIVE = pathlib.Path(
    "/home/alex/git/my/alex-tavern/plans/artifacts/p1-archive/"
    "base-P1-r2/sessions/8bd4d0f1/debug.jsonl"
)
OUT = pathlib.Path(__file__).parent / "runs"
RUNS = 4
PAYLOAD_TURNS = (10, 23)

OLD_OWNERSHIP = (
    "- DIALOGUE OWNERSHIP: never invent new dialogue for a routed character inside\n"
    "  perception_events. Record only the stimulus or words already spoken in\n"
    "  HISTORY, then select the reacting characters in next_speakers. Their\n"
    "  Character agents, not you, decide what they say."
)
OLD_CONTENT = (
    '  thoughts, no facts a witness could not sense); "witness_ids": the IDs of\n'
    "  every present character who could genuinely perceive it given the zones,\n"
    "  distance, and noise. Never include someone who could not perceive it.}"
)


def shipped_blocks() -> tuple[str, str]:
    """Read the two changed blocks out of the production builder verbatim."""
    prompt = _build_system_prompt(["C1", "C2"])

    start = prompt.index("- DIALOGUE OWNERSHIP:")
    end = prompt.index("\n- HISTORY entries marked", start)
    ownership = prompt[start:end]

    start = prompt.index("  thoughts, no facts a witness could not sense)")
    end = prompt.index("who could not perceive it.}", start) + len("who could not perceive it.}")
    content = prompt[start:end]

    return ownership, content


@dataclass
class Payload:
    turn: int
    messages: list[dict]
    max_tokens: int


def load_payloads() -> dict[int, Payload]:
    found: dict[int, Payload] = {}
    for line in ARCHIVE.read_text(encoding="utf-8").splitlines():
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
        raise SystemExit(f"payload turns not found in archive: {sorted(missing)}")
    return found


def build_variant(payload: Payload, variant: str) -> list[dict]:
    messages = [dict(m) for m in payload.messages]
    system = messages[0]
    if system.get("role") != "system":
        raise SystemExit(f"turn {payload.turn}: first message is not the system prompt")
    if variant == "old":
        return messages

    ownership, content = shipped_blocks()
    text = system["content"]
    for old, new in ((OLD_OWNERSHIP, ownership), (OLD_CONTENT, content)):
        if text.count(old) != 1:
            raise SystemExit(f"turn {payload.turn}: expected exactly one {old[:40]!r}")
        text = text.replace(old, new.rstrip("\n"))
    system["content"] = text
    return messages


QUOTE_SPAN = re.compile(
    r"""["“”«»'‘’]\s*[^"“”«»'‘’]{8,}?\s*["“”«»'‘’]"""
)
FIRST_PERSON = re.compile(
    r"\b(eu|meu|minha|meus|minhas|nos|nossa|nosso|precisamos|vamos|estou|sou)\b",
    re.IGNORECASE,
)


def has_quoted_span(text: str) -> bool:
    """A quoted span of at least two words is the Director writing the line."""
    for match in QUOTE_SPAN.finditer(text):
        inner = match.group(0)[1:-1].strip()
        if len(inner.split()) >= 2:
            return True
    return False


@dataclass
class RunResult:
    turn: int
    variant: str
    run: int
    ok: bool
    events: int = 0
    audible: int = 0
    quoted: int = 0
    first_person: int = 0
    contents: list[str] = field(default_factory=list)
    error: str = ""


def score(turn: int, variant: str, run: int, raw: str) -> RunResult:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return RunResult(turn, variant, run, ok=False, error=f"unparseable: {exc}")
    events = parsed.get("perception_events") or []
    audible = [e for e in events if e.get("event_kind") == "audible_speech"]
    contents = [str(e.get("content", "")) for e in audible]
    return RunResult(
        turn=turn,
        variant=variant,
        run=run,
        ok=True,
        events=len(events),
        audible=len(audible),
        quoted=sum(1 for c in contents if has_quoted_span(c)),
        first_person=sum(1 for c in contents if FIRST_PERSON.search(c)),
        contents=contents,
    )


async def fire(
    client: httpx.AsyncClient,
    cfg: dict,
    payload: Payload,
    variant: str,
    run: int,
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
        pathlib.Path("/home/alex/git/my/alex-tavern/.data/config.json").read_text(
            encoding="utf-8"
        )
    )["providers"]["deepseek"]
    payloads = load_payloads()

    jobs = [
        (payloads[turn], variant, run)
        for turn in PAYLOAD_TURNS
        for variant in ("old", "new")
        for run in range(1, RUNS + 1)
    ]
    print(f"firing {len(jobs)} calls at {cfg['model']}", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(job):
            async with semaphore:
                result = await fire(client, cfg, *job)
                mark = "ok " if result.ok else "ERR"
                print(
                    f"  {mark} T{result.turn} {result.variant} r{result.run} "
                    f"audible={result.audible} quoted={result.quoted} {result.error}",
                    flush=True,
                )
                return result

        results = await asyncio.gather(*(guarded(job) for job in jobs))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report(results)


def report(results: list[RunResult]) -> None:
    print("\n" + "=" * 72)
    for turn in PAYLOAD_TURNS:
        print(f"\nTURN {turn}")
        for variant in ("old", "new"):
            rows = [r for r in results if r.turn == turn and r.variant == variant and r.ok]
            if not rows:
                print(f"  {variant:>3}: no successful runs")
                continue
            audible = sum(r.audible for r in rows)
            quoted = sum(r.quoted for r in rows)
            first = sum(r.first_person for r in rows)
            rate = f"{quoted / audible:.0%}" if audible else "n/a"
            print(
                f"  {variant:>3}: runs={len(rows)} "
                f"audible/run={audible / len(rows):.2f} "
                f"quoted={quoted}/{audible} ({rate}) "
                f"first_person={first} "
                f"events/run={sum(r.events for r in rows) / len(rows):.2f}"
            )
        for variant in ("old", "new"):
            for r in [x for x in results if x.turn == turn and x.variant == variant and x.ok]:
                for c in r.contents:
                    flag = "Q" if has_quoted_span(c) else " "
                    print(f"    [{variant} r{r.run}] {flag} {c}")


if __name__ == "__main__":
    asyncio.run(main())
