from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
KINDS = {"physical_outcome", "observation"}
EXCLUDED = {"ea6620fb", "bb72dc94"}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    if (OUT / "results.json").exists():
        raise RuntimeError("Preserve the existing experiment; output already exists")
    original = ROOT / "plans/artifacts/69-capacity-read/sat_visibility2.py"
    spec = importlib.util.spec_from_file_location("archived_capacity", original)
    assert spec and spec.loader
    detector = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = detector
    spec.loader.exec_module(detector)
    sources = {}
    for state in sorted((ROOT / "plans/artifacts").rglob("state.json")):
        if state.parent.name not in EXCLUDED:
            sources.setdefault(state.parent.name, state.parent)
    assert len(sources) == 33
    sessions = []
    dossier = []
    for sid, base in sorted(sources.items()):
        debug = base / "debug.jsonl"
        raw = debug.read_bytes()
        records = []
        problems = Counter()
        facts_sizes = []
        for line_number, line in enumerate(raw.decode().splitlines(), 1):
            row = json.loads(line)
            if row.get("agent") != "director":
                continue
            chunks = [
                message["content"].split("Physical facts:", 1)[1].lstrip()
                for message in row["request"]["messages"]
                if "Physical facts:" in message["content"]
            ]
            if len(chunks) != 1:
                problems["facts_block_not_unique"] += 1
                continue
            try:
                facts, _ = json.JSONDecoder().raw_decode(chunks[0])
                assert isinstance(facts, dict)
            except (ValueError, AssertionError):
                problems["facts_invalid"] += 1
                continue
            facts_sizes.append(len(facts))
            try:
                response = json.loads(row["response"])
                events = response["perception_events"]
                assert isinstance(events, list)
            except (ValueError, TypeError, KeyError, AssertionError):
                problems["response_invalid"] += 1
                continue
            records.append(
                {
                    "turn": row["turn_number"],
                    "line": line_number,
                    "facts": facts,
                    "messages": row["request"]["messages"],
                    "events": events,
                }
            )
        if problems["facts_block_not_unique"] or problems["facts_invalid"]:
            raise RuntimeError(f"{sid}: incomplete facts inventory {dict(problems)}")
        last_by_turn = {record["turn"]: record for record in records}
        discarded = len(records) - len(last_by_turn)
        records = list(last_by_turn.values())
        cohort = "reaches_40" if max(facts_sizes) >= 40 else "below_40"
        candidates = [
            {"turn": record["turn"], "line": record["line"], "index": index, "event": event}
            for record in records
            for index, event in enumerate(record["events"])
            if event["event_kind"] in KINDS
        ]
        counts = {}
        pairs = []
        for item in candidates:
            turn = item["turn"]
            if turn <= 3:
                continue
            tally = counts.setdefault(turn, {"events": 0, "flags": 0})
            tally["events"] += 1
            earlier = [
                candidate for candidate in candidates if turn - 3 <= candidate["turn"] < turn
            ]
            if not earlier:
                continue
            best = max(
                earlier,
                key=lambda candidate: detector.sim(
                    item["event"]["content"], candidate["event"]["content"]
                ),
            )
            score = detector.sim(item["event"]["content"], best["event"]["content"])
            if score < 0.6:
                continue
            tally["flags"] += 1
            pairs.append({"original": best, "repeat": item, "similarity": score})
        row = {
            "session_id": sid,
            "path": str(debug.relative_to(ROOT)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "cohort": cohort,
            "peak_prompt_facts": max(facts_sizes),
            "director_records": len(records),
            "earlier_parseable_responses_discarded": discarded,
            "problems": dict(problems),
            "turns": counts,
            "events": sum(tally["events"] for tally in counts.values()),
            "flags": sum(tally["flags"] for tally in counts.values()),
        }
        row["rate"] = row["flags"] / row["events"] if row["events"] else None
        sessions.append(row)
        if cohort == "below_40" and pairs:
            pair = min(
                pairs,
                key=lambda pair: (
                    pair["repeat"]["turn"],
                    pair["original"]["turn"],
                    pair["repeat"]["event"]["content"],
                ),
            )
            record = next(record for record in records if record["line"] == pair["repeat"]["line"])
            dossier.append(
                {
                    "session_id": sid,
                    "peak_prompt_facts": max(facts_sizes),
                    **pair,
                    "repeating_facts": record["facts"],
                    "repeating_messages": record["messages"],
                }
            )
        print(f"{sid}: {cohort}, flags {row['flags']}/{row['events']}", flush=True)
    represented = {
        cohort: {turn for row in sessions if row["cohort"] == cohort for turn in row["turns"]}
        for cohort in ("below_40", "reaches_40")
    }
    common = represented["below_40"] & represented["reaches_40"]
    summaries = {}
    for restriction, selected in (("all", None), ("shared_turn_indices", common)):
        summaries[restriction] = {}
        for cohort in represented:
            rates = []
            events = flags = 0
            for row in sessions:
                if row["cohort"] != cohort:
                    continue
                tallies = [
                    value
                    for turn, value in row["turns"].items()
                    if selected is None or turn in selected
                ]
                n = sum(value["events"] for value in tallies)
                k = sum(value["flags"] for value in tallies)
                if n:
                    rates.append(k / n)
                    events += n
                    flags += k
            summaries[restriction][cohort] = {
                "sessions": len(rates),
                "flags": flags,
                "events": events,
                "pooled": flags / events,
                "median": statistics.median(rates),
                "population_sd": statistics.pstdev(rates),
                "range": [min(rates), max(rates)],
            }
    write_json(
        OUT / "results.json",
        {
            "detector_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "excluded_sessions": sorted(EXCLUDED),
            "sessions": sessions,
            "common_turn_indices": sorted(common),
            "summary": summaries,
        },
    )
    write_json(OUT / "dossier.json", dossier)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
