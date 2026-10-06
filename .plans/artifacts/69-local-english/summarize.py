"""Retain per-chain telemetry and exact prose/request evidence for text readers."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "69-local-split"


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def summarize(folder: Path) -> dict:
    calls = []
    chains = []
    for directory in sorted((folder / "runs").glob("chain*")):
        result = read(directory / "result.json")
        assert "calls" in result, "Chain still running; never report an observation timeout as done"
        rows = [json.loads(line) for line in (directory / "debug.jsonl").read_text().splitlines()]
        turn_intervals = []
        for turn in result["turns"]:
            times = [
                datetime.fromisoformat(r["ts"])
                for r in rows
                if r.get("turn_number") == turn["turn"]
            ]
            turn_intervals.append(
                {
                    "turn": turn["turn"],
                    "committed": turn["committed"],
                    "log_interval_seconds": round((max(times) - min(times)).total_seconds(), 3),
                    "wall_seconds": turn.get("wall_seconds"),
                }
            )
        prose = [
            json.loads(r["response"])["narration"]
            for r in rows
            if r.get("agent") == "prose" and r.get("response")
        ]
        chains.append(
            {
                "chain": directory.name,
                "complete": result["complete"],
                "calls": result["calls"],
                "committed": sum(r["committed"] for r in result["turns"]),
                "attempted_turns": len(result["turns"]),
                "turn_intervals": turn_intervals,
                "errors": [
                    {
                        "turn": r["turn"],
                        "error": r.get("error"),
                        "rollback_pass": r.get("rollback_pass"),
                    }
                    for r in result["turns"]
                    if not r["committed"]
                ],
                "prose_word_counts": [len(text.split()) for text in prose],
                "agent_calls": dict(Counter(r["agent"] for r in rows if r.get("usage"))),
            }
        )
        for path in directory.glob("*.raw.json"):
            calls.append(read(path))
    assert len(calls) == sum(c["calls"] for c in chains)
    times = [
        t["log_interval_seconds"] for c in chains for t in c["turn_intervals"] if t["committed"]
    ]
    return {
        "chains": chains,
        "calls": len(calls),
        "completed_chains": sum(c["complete"] for c in chains),
        "committed_submissions": sum(c["committed"] for c in chains),
        "attempted_submissions": sum(c["attempted_turns"] for c in chains),
        "total_input": sum(c["usage"]["prompt_tokens"] for c in calls),
        "total_output": sum(c["usage"]["completion_tokens"] for c in calls),
        "max_input": max(c["usage"]["prompt_tokens"] for c in calls),
        "max_output": max(c["usage"]["completion_tokens"] for c in calls),
        "max_combined": max(c["usage"]["total_tokens"] for c in calls),
        "finish_reasons": dict(Counter(c["choices"][0]["finish_reason"] for c in calls)),
        "committed_log_interval_median": median(times) if times else None,
        "committed_log_interval_range": [min(times), max(times)] if times else None,
    }


def reader_packet(directory: Path, manifest: dict) -> dict:
    result = read(directory / "result.json")
    reviews = read(directory / "reviews.json")
    packet = {
        "chain": directory.name,
        "initial_history": manifest["start"]["history"][0]["content"],
        "controlled_action_each_turn": manifest["action"],
        "world_causes": manifest["causes"],
        "note": "Physical source/prose/speech only. Character thoughts are subjective and omitted. "
        "Actual renderer messages define eligible history/events and larger staging. "
        "audible_speech is deliberately absent from renderer; dialogue is displayed separately.",
        "turns": [],
    }
    for turn in result["turns"]:
        number = turn["turn"]
        entry = {
            "turn": number,
            "committed": turn["committed"],
            "error": turn.get("error"),
            "state_before": read(directory / f"t{number}.start.json")["scene"],
            "state_after": read(directory / f"t{number}.persisted.json")["scene"],
            "director": [
                r["payload"]["candidate"]
                for r in reviews
                if r["turn"] == number and r["stage"] == "director"
            ],
            "prose": [],
            "character_speech": [],
        }
        for path in sorted(directory.glob(f"t{number}-call*.raw.json")):
            raw = read(path)
            content = raw["choices"][0]["message"]["content"]
            try:
                output = json.loads(content)
            except json.JSONDecodeError:
                continue  # Remains a retained raw failure, not a prose output.
            if "narration" in output:
                request = path.with_name(path.name.replace(".raw.json", ".request.json"))
                scope = path.with_name(path.name.replace(".raw.json", ".scope.json"))
                entry["prose"].append(
                    {
                        "call": path.stem,
                        "scope": read(scope),
                        "renderer_context": read(request)["messages"],
                        "generated_prose": output["narration"],
                    }
                )
        output_path = directory / f"t{number}.output.json"
        if output_path.exists():
            entry["character_speech"] = [
                r["speech"] for r in read(output_path)["character_responses"]
            ]
        packet["turns"].append(entry)
    return packet


def main() -> None:
    manifest = read(HERE / "manifest.json")
    comparison = {"portuguese_split": summarize(PRIOR), "english_split": summarize(HERE)}
    write(HERE / "runs/comparison.json", comparison)
    transcript = [
        "# Second local Gemma round: English transcripts\n",
        "Actual viewer prose and public Character speech; private thoughts omitted.\n",
        "C1 Iara, C2 Bento, C3 Téo. Viewer recipients and physical staging may differ.\n",
    ]
    for directory in sorted((HERE / "runs").glob("chain*")):
        packet = reader_packet(directory, manifest)
        write(directory / "reader-packet.json", packet)
        transcript.append(f"## {directory.name}\n")
        for turn in packet["turns"]:
            transcript.append(f"### Turn {turn['turn']}\n")
            transcript.append(f"World cause: {manifest['causes'][str(turn['turn'])]}\n")
            transcript.append(f"Committed: {turn['committed']}; error: {turn['error']}.\n")
            result = read(directory / "result.json")
            projection = next(r["projection"] for r in result["turns"] if r["turn"] == turn["turn"])
            transcript.append(
                "Persisted: "
                + json.dumps(
                    {"apertures": projection["apertures"], "positions": projection["positions"]}
                )
                + "\n"
            )
            for prose in turn["prose"]:
                transcript.extend(
                    [f"Scope: {json.dumps(prose['scope'])}.\n", prose["generated_prose"] + "\n"]
                )
            for speech in turn["character_speech"]:
                transcript.append("Bento: " + speech + "\n")
    # Markdown presentation removes trailing whitespace; raw provider strings
    # remain unchanged in response files and reader packets.
    display = "\n".join(line.rstrip() for line in "\n".join(transcript).splitlines()) + "\n"
    (HERE / "TRANSCRIPTS.md").write_text(display)
    print(json.dumps(comparison, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
