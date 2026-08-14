"""Task 79: state the positional classifier, then audit it by hand in BOTH directions.

The owner's objection, 2026-08-13: "1,967 of 24,829 is a judgement about
model-authored free text. This project has shipped a string heuristic over
model-authored text twice and been wrong both times. Write down: the rule, how
many phrases you read by hand, and how many false positives you found."

THE RULE, stated before the number.

  Z = every zone name known to the session (keys of `zones`, values of
      `positions`, across every snapshot and every director call).

  For each `scene_blocking.character_zones` value e:

    NAMES_A_ZONE   e is exactly a member of Z (accent- and case-insensitive).
                   The Director just restated where the character is. NOT
                   positional.

    EXTENDS_A_ZONE e is not in Z, and some z in Z is a comma-delimited prefix of
                   e. The Director named a place and added detail to it.
                   POSITIONAL.

    PREPOSITIONAL  e is not in Z and contains a spatial preposition phrase from
                   the list below. POSITIONAL.

    UNCLASSIFIED   none of the above. Reported as its own bucket and NEVER folded
                   into either answer - "arco C", "fileira de alunos", "area de
                   espera" are genuinely ambiguous and the instrument should say
                   so rather than guess.

Note on rule 5 of the metric culture ("never match a NAME with a string
heuristic"): PREPOSITIONAL matches PREPOSITIONS, which are language and not
model-authored names, so it is not the failure mode that burned this project
twice. EXTENDS_A_ZONE *does* compare against model-authored names, which is why
it compares against the session's own declared zone set rather than guessing at
what looks like a place, and why both buckets are hand-read below.
"""

from __future__ import annotations

import gc
import json
import pathlib
import re
import statistics
import unicodedata
from collections import Counter

ROOT = pathlib.Path("/home/alex/git/my/alex-tavern/plans/artifacts")
OUT = pathlib.Path(__file__).parent

PREPOSITIONS = re.compile(
    # Head + an OPTIONAL article/contraction. The first cut of this list wrote the
    # contractions out by hand and missed "perto da", "ao lado do", "junto as" and
    # "sobre sua" - four misses in a twenty-line hand sample. That is the fourth
    # detector in this project to fail on Portuguese morphology rather than on
    # meaning, so the article is now a suffix group instead of an enumeration.
    r"\b(junto|proxim[oa]s?|perto|ao lado|atras|em frente|a frente|na borda|no centro|"
    r"ao pe|diante|encostad[oa]s?|apoiad[oa]s?|rente|a direita|a esquerda|no meio|"
    r"no alto|na base|ao redor|acima|abaixo|sob|sobre|entre|afastand[oa]|recuando|"
    r"avancando|posicionand[oa])"
    r"(\s+(a|o|as|os|da|do|das|dos|na|no|nas|nos|sua|seu|suas|seus|um|uma|de|dele|dela))?\b"
)


def norm(text: str) -> str:
    flat = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", flat).strip(" .,")


def distinct_sessions() -> dict[str, pathlib.Path]:
    found: dict[str, pathlib.Path] = {}
    for state in sorted(ROOT.rglob("state.json")):
        found.setdefault(state.parent.name, state.parent)
    return found


def zone_universe(base: pathlib.Path) -> set[str]:
    zones: set[str] = set()
    state = json.loads((base / "state.json").read_text(encoding="utf-8"))
    for record in state.get("history", []):
        snap = record.get("scene_snapshot") or {}
        zones.update(norm(z) for z in (snap.get("zones") or {}))
        zones.update(norm(z) for z in (snap.get("positions") or {}).values())
    scene = state.get("scene") or {}
    zones.update(norm(z) for z in (scene.get("zones") or {}))
    zones.update(norm(z) for z in (scene.get("positions") or {}).values())
    return {z for z in zones if z}


def classify(entry: str, zones: set[str]) -> str:
    flat = norm(entry)
    if not flat:
        return "EMPTY"
    if flat in zones:
        return "NAMES_A_ZONE"
    for zone in zones:
        if len(zone) > 3 and (flat.startswith(zone + ",") or flat.startswith(zone + " ,")):
            return "EXTENDS_A_ZONE"
    if PREPOSITIONS.search(flat):
        return "PREPOSITIONAL"
    return "UNCLASSIFIED"


def main() -> None:
    per_session: list[tuple[str, int, int, Counter]] = []
    everything: list[tuple[str, str, str]] = []  # (session, verdict, entry)
    total = Counter()

    for sid, base in sorted(distinct_sessions().items()):
        zones = zone_universe(base)
        counts: Counter = Counter()
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
                blocking = (parsed.get("scene_blocking") or {}).get("character_zones") or {}
                if not isinstance(blocking, dict):
                    continue
                for entry in blocking.values():
                    verdict = classify(str(entry), zones)
                    counts[verdict] += 1
                    everything.append((sid, verdict, str(entry)))
        total += counts
        n = sum(counts.values())
        if n:
            positional = counts["EXTENDS_A_ZONE"] + counts["PREPOSITIONAL"]
            per_session.append((sid, n, positional, counts))
        gc.collect()

    grand = sum(total.values())
    pos = total["EXTENDS_A_ZONE"] + total["PREPOSITIONAL"]
    print(f"entries classified: {grand} across {len(per_session)} sessions\n")
    for key in ("NAMES_A_ZONE", "EXTENDS_A_ZONE", "PREPOSITIONAL", "UNCLASSIFIED", "EMPTY"):
        print(f"  {key:16} {total[key]:6}  {total[key] / grand:6.1%}")
    print(f"\n  POSITIONAL (extends + prepositional) = {pos}/{grand} = {pos / grand:.1%}")
    print(f"  UNCLASSIFIED is {total['UNCLASSIFIED'] / grand:.1%} and is NOT counted either way")

    rates = [p / n for _, n, p, _ in per_session if n >= 50]
    print(
        f"\nper session (n={len(rates)}): median {statistics.median(rates):.1%}  "
        f"mean {statistics.mean(rates):.1%}  sd {statistics.stdev(rates) * 100:.1f}pts  "
        f"range {min(rates):.1%}-{max(rates):.1%}"
    )
    print("\ntop and bottom sessions by positional share:")
    ranked = sorted(((p / n, sid, n, p) for sid, n, p, _ in per_session if n >= 50), reverse=True)
    for rate, sid, n, p in ranked[:5] + ranked[-5:]:
        print(f"  {sid}  {p:4}/{n:4} = {rate:5.1%}")

    # Systematic samples for the hand read, in BOTH directions.
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for bucket, want in (("EXTENDS_A_ZONE", 20), ("PREPOSITIONAL", 20), ("NAMES_A_ZONE", 20), ("UNCLASSIFIED", 20)):
        rows = [(s, e) for s, v, e in everything if v == bucket]
        step = max(1, len(rows) // want)
        sample = rows[::step][:want]
        lines.append(f"\n## {bucket} — {len(rows)} total, systematic sample of {len(sample)}\n")
        for i, (sid, entry) in enumerate(sample, 1):
            lines.append(f"{i:3}. [{sid}] {entry}")
    (OUT / "hand_sample.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT / 'hand_sample.md'} for the hand read")


if __name__ == "__main__":
    main()
