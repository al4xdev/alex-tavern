"""Calibrate _INTENT_CARRIED_RATIO against real character replies under a real mandate.

THE QUESTION. `_carries_intent` decides whether a character's line carried the
fact the Director ruled aloud. Above the ratio the mandate worked and one record
is written; below it the turn is logged `mandate_ignored` and falls to the
degradation path. The threshold ships at 0.5 and is the one number in task 65
that could not be sized against the archive, because it judges compliance with a
prompt that did not exist until 2026-08-06.

WHAT THIS MEASURES. The archive has no positives for this prompt, so this builds
them. It takes the intents the VALIDATED Director variant actually produced
(from validate_dialogue_ownership.py, reported form, no quoted spans), hands
each to the real character agent through the shipped mandate note at its shipped
position, and scores the reply with the shipped `_carries_intent`.

WHAT DECIDES THE NUMBER. Not a target compliance rate - a separating band. The
language guard in this same task was accepted because 0.5 sat in an empty band
between 0.012 and 1.000. The same test applies here:

  - if replies that a reader would call compliant cluster well ABOVE 0.5 and the
    non-compliant ones well below, the threshold sits in a gap and 0.5 stands;
  - if compliant replies land NEAR or BELOW 0.5, the threshold is too strict: it
    fires `mandate_ignored` on characters who obeyed, and case C pays for a
    dedicated call it did not need;
  - if a large share of case C is `mandate_ignored` regardless of threshold, the
    mandate is a prompt promise that loses, which is the falsifier already
    written into the task, and case C goes back to case A's dedicated call.

The ratio is reported per reply so the distribution decides, not the pass/fail
of the shipped constant.

POSITION. The mandate is substituted into the RECORDED character user prompt
immediately before "Return your audible speech and private thought in the
requested fields.", which is exactly where `_build_user_prompt` puts it.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "/home/alex/git/my/alex-tavern")

import httpx  # noqa: E402

from src.agents.character import _speech_mandate_note  # noqa: E402
from src.runner import _carries_intent, _intent_words  # noqa: E402

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern")
SESSION = ROOT / "plans/artifacts/p1-archive/base-P1-r2/sessions/8bd4d0f1"
RUNS_DIR = pathlib.Path(__file__).parent / "runs"
OUT = pathlib.Path(__file__).parent / "calibration"

TAIL = "Return your audible speech and private thought in the requested fields."


def roster() -> dict[str, str]:
    state = json.loads((SESSION / "state.json").read_text(encoding="utf-8"))
    return {
        cid: (data.get("mind") or {}).get("name") or data.get("name")
        for cid, data in state.get("characters", {}).items()
    }


@dataclass
class Intent:
    subject_id: str
    name: str
    text: str
    source: str


def collect_intents() -> list[Intent]:
    """Every audible_speech the VALIDATED Director variant produced."""
    names = roster()
    intents: list[Intent] = []
    for path in sorted(RUNS_DIR.glob("T*-new-r*.json")):
        parsed = json.loads(path.read_text(encoding="utf-8"))
        for event in parsed.get("perception_events") or []:
            if event.get("event_kind") != "audible_speech":
                continue
            subject = str(event.get("subject_id", ""))
            name = names.get(subject)
            if not name:
                continue
            intents.append(
                Intent(
                    subject_id=subject,
                    name=name,
                    text=str(event.get("content", "")),
                    source=path.stem,
                )
            )
    return intents


def character_payloads() -> dict[str, dict]:
    """The most recent archived call per character, as the carrier prompt."""
    found: dict[str, dict] = {}
    for line in (SESSION / "debug.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        agent = record.get("agent") or ""
        if not agent.startswith("character:") or record.get("error"):
            continue
        request = record.get("request") or {}
        messages = request.get("messages") or []
        if len(messages) < 2 or TAIL not in messages[-1].get("content", ""):
            continue
        found[agent.split(":", 1)[1]] = request
    return found


@dataclass
class Row:
    name: str
    intent: str
    source: str
    ok: bool
    spoken: str = ""
    ratio: float = 0.0
    wanted: int = 0
    shared: int = 0
    carried: bool = False
    error: str = ""


def score(name: str, intent: str, source: str, raw: str) -> Row:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return Row(name, intent, source, ok=False, error=f"unparseable: {exc}")
    spoken = str(parsed.get("speech") or "")
    wanted = _intent_words(intent)
    shared = wanted & _intent_words(spoken)
    return Row(
        name=name,
        intent=intent,
        source=source,
        ok=True,
        spoken=spoken,
        ratio=(len(shared) / len(wanted)) if wanted else 1.0,
        wanted=len(wanted),
        shared=len(shared),
        carried=_carries_intent(spoken, intent),
    )


async def fire(client: httpx.AsyncClient, cfg: dict, request: dict, intent: Intent) -> Row:
    messages = [dict(m) for m in request["messages"]]
    tail = messages[-1]["content"]
    if tail.count(TAIL) != 1:
        return Row(intent.name, intent.text, intent.source, ok=False, error="tail not unique")
    mandate = _speech_mandate_note([intent.text])
    messages[-1]["content"] = tail.replace(TAIL, f"{mandate}\n\n{TAIL}")

    body = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": request.get("max_tokens", 12288),
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
    except Exception as exc:  # noqa: BLE001
        return Row(
            intent.name, intent.text, intent.source, ok=False, error=f"{type(exc).__name__}: {exc}"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{intent.source}-{intent.subject_id}.json").write_text(raw, encoding="utf-8")
    return score(intent.name, intent.text, intent.source, raw)


async def main() -> None:
    cfg = json.loads((ROOT / ".data/config.json").read_text(encoding="utf-8"))["providers"][
        "deepseek"
    ]
    payloads = character_payloads()
    intents = [i for i in collect_intents() if i.name in payloads]
    skipped = [i for i in collect_intents() if i.name not in payloads]
    for i in skipped:
        print(f"  skip {i.name}: no archived character call to carry the mandate", flush=True)
    print(f"firing {len(intents)} mandated character calls", flush=True)

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(4)

        async def guarded(intent: Intent) -> Row:
            async with semaphore:
                row = await fire(client, cfg, payloads[intent.name], intent)
                print(
                    f"  {'ok ' if row.ok else 'ERR'} {row.name:<24} "
                    f"ratio={row.ratio:.2f} ({row.shared}/{row.wanted}) "
                    f"carried={row.carried} {row.error}",
                    flush=True,
                )
                return row

        rows = await asyncio.gather(*(guarded(i) for i in intents))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps([r.__dict__ for r in rows], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report(rows)


def report(rows: list[Row]) -> None:
    good = [r for r in rows if r.ok]
    print("\n" + "=" * 72)
    print(f"{len(good)} replies scored\n")
    for r in sorted(good, key=lambda r: r.ratio):
        print(f"  ratio={r.ratio:.2f} ({r.shared}/{r.wanted}) carried={r.carried}  {r.name}")
        print(f"      intent: {r.intent}")
        print(f"      spoken: {r.spoken}")
    if not good:
        return
    ratios = sorted(r.ratio for r in good)
    carried = sum(1 for r in good if r.carried)
    print(f"\n  min={ratios[0]:.2f} median={ratios[len(ratios) // 2]:.2f} max={ratios[-1]:.2f}")
    print(f"  carried at shipped 0.5: {carried}/{len(good)} = {carried / len(good):.0%}")
    print(f"  mandate_ignored rate:   {1 - carried / len(good):.0%}")
    print("\n  sensitivity:")
    for threshold in (0.3, 0.4, 0.5, 0.6, 0.7):
        passing = sum(1 for r in good if r.ratio >= threshold)
        print(f"    {threshold:.1f} -> carried {passing}/{len(good)} ({passing / len(good):.0%})")
    print("\n  gap search (sorted ratios):", " ".join(f"{r:.2f}" for r in ratios))


if __name__ == "__main__":
    asyncio.run(main())
