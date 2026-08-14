"""Task 69 capacity test, dossier v2 - the read, not the score.

v1 asked "is there a similar chunk anywhere in the prompt", which answers the
wrong question: the Director's own `perception_events` are never echoed back to
it, so a low similarity does not mean the EVENT was forgotten. What comes back is
the transcript and the `Physical facts` bag.

So this prints, for the same 20 sampled pairs, exactly what the Director was
looking at when it re-proposed:

  - every transcript line in the re-proposing prompt for the turns from the
    original up to the re-proposal;
  - the full `Physical facts` bag.

The verdict is a read over that. Nothing here scores it.
"""

from __future__ import annotations

import gc
import json
import pathlib
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern/plans/artifacts")
OUT = pathlib.Path(__file__).parent
TAU = 0.6
LOOKBACK = 3
SAMPLE = 20


def norm(text: str) -> str:
    flat = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", flat).strip()


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


@dataclass
class Event:
    turn: int
    kind: str
    text: str


@dataclass
class Pair:
    session: str
    cell: str
    orig: Event
    repeat: Event
    score: float


def distinct_sessions() -> dict[str, pathlib.Path]:
    found: dict[str, pathlib.Path] = {}
    for state in sorted(ROOT.rglob("state.json")):
        found.setdefault(state.parent.name, state.parent)
    return found


def director_records(base: pathlib.Path) -> list[dict]:
    path = base / "debug.jsonl"
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("agent") == "director" and record.get("turn_number") is not None:
                out.append(record)
    return out


def events_of(record: dict) -> list[Event]:
    try:
        parsed = json.loads(record.get("response") or "{}")
    except json.JSONDecodeError:
        return []
    turn = int(record["turn_number"])
    return [
        Event(turn, str(i.get("event_kind") or "?"), str(i.get("content") or "").strip())
        for i in parsed.get("perception_events") or []
        if isinstance(i, dict) and str(i.get("content") or "").strip()
    ]


def find_pairs(session: str, cell: str, records: list[dict]) -> list[Pair]:
    by_turn: dict[int, list[Event]] = {}
    for record in records:
        by_turn.setdefault(int(record["turn_number"]), []).extend(events_of(record))
    pairs: list[Pair] = []
    turns = sorted(by_turn)
    for turn in turns:
        earlier = [e for t in turns if turn - LOOKBACK <= t < turn for e in by_turn[t]]
        for event in by_turn[turn]:
            best, score = None, 0.0
            for candidate in earlier:
                value = sim(event.text, candidate.text)
                if value > score:
                    best, score = candidate, value
            if best is not None and score >= TAU:
                pairs.append(Pair(session, cell, best, event, score))
    return pairs


def prompt_at(records: list[dict], turn: int) -> str:
    for record in records:
        if int(record["turn_number"]) == turn:
            messages = (record.get("request") or {}).get("messages") or []
            return "\n\n".join(str(m.get("content") or "") for m in messages)
    return ""


def transcript_window(prompt: str, lo: int, hi: int) -> list[str]:
    out = []
    for line in prompt.splitlines():
        match = re.match(r"\s*Turn (\d+) \|", line)
        if match and lo <= int(match.group(1)) <= hi:
            out.append(line.strip())
    return out


def facts_bag(prompt: str) -> str:
    idx = prompt.find("Physical facts:")
    if idx < 0:
        return "(no Physical facts block)"
    end = prompt.find("\n", idx)
    return prompt[idx : end if end > 0 else idx + 2000]


def main() -> None:
    sessions = distinct_sessions()
    all_pairs: list[Pair] = []
    per_session: dict[str, list[dict]] = {}
    for sid, base in sorted(sessions.items()):
        records = director_records(base)
        if not records:
            continue
        per_session[sid] = records
        all_pairs.extend(find_pairs(sid, base.parent.parent.name, records))
        gc.collect()

    all_pairs.sort(key=lambda p: (p.session, p.repeat.turn, p.orig.turn, p.repeat.text[:40]))
    step = max(1, len(all_pairs) // SAMPLE)
    sample = all_pairs[::step][:SAMPLE]

    lines: list[str] = []
    for n, pair in enumerate(sample, 1):
        prompt = prompt_at(per_session[pair.session], pair.repeat.turn)
        window = transcript_window(prompt, pair.orig.turn, pair.repeat.turn)
        best = max((sim(pair.orig.text, line) for line in window), default=0.0)
        lines.append(
            f"## {n}. `{pair.session}` T{pair.orig.turn} -> T{pair.repeat.turn} "
            f"(detector {pair.score:.2f}, best transcript match {best:.2f})\n"
        )
        lines.append(f"**ORIGINAL** T{pair.orig.turn} [{pair.orig.kind}]: {pair.orig.text}\n")
        lines.append(f"**REPEAT**   T{pair.repeat.turn} [{pair.repeat.kind}]: {pair.repeat.text}\n")
        lines.append(f"**What the T{pair.repeat.turn} prompt showed for turns {pair.orig.turn}-{pair.repeat.turn}:**\n")
        if window:
            for line in window:
                lines.append(f"    {line[:400]}")
        else:
            lines.append("    (NO transcript line for those turns in the prompt)")
        lines.append("")
        lines.append(f"**Facts bag:** {facts_bag(prompt)[:1400]}\n")
        lines.append("---\n")

    report = OUT / "visibility_dossier2.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {report}  ({len(sample)} pairs of {len(all_pairs)})")


if __name__ == "__main__":
    main()
