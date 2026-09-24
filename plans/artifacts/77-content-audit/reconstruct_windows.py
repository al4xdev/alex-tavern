"""Reconstruct the published task-77 window definition over archived states.

This is a diagnostic reconstruction, not the recovered historical instrument.
"""

import json
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[1] / "repetition-battery"
OUTPUT = Path(__file__).with_name("reconstruction.json")


class TurnRow(TypedDict):
    speech: list[str]
    position_states: list[dict[str, str]]


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    plain = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(plain.split())


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalized(left), normalized(right)).ratio()


def best_pair(left: list[str], right: list[str]) -> float:
    return max((similarity(a, b) for a in left for b in right), default=0.0)


def reconstruct(path: Path) -> list[dict[str, object]]:
    state = json.loads(path.read_text())
    turns: dict[int, TurnRow] = {}
    for record in state["history"]:
        turn = record["turn_number"]
        if turn > state["revision"]:
            continue
        row = turns.setdefault(turn, {"speech": [], "position_states": []})
        if record.get("scene_snapshot"):
            row["position_states"].append(record["scene_snapshot"]["positions"])
        if record["content_type"] == "speech":
            row["speech"].append(record["content"])

    found: list[dict[str, object]] = []
    for end in sorted(turns):
        begin = end - 2
        if begin not in turns or begin + 1 not in turns:
            continue
        first, middle, last = (turns[number] for number in (begin, begin + 1, end))
        if not all(row["position_states"] for row in (first, middle, last)):
            continue
        initial = first["position_states"][0]
        if any(
            positions != initial
            for row in (first, middle, last)
            for positions in row["position_states"]
        ):
            continue
        previous = best_pair(first["speech"], middle["speech"])
        current = best_pair(middle["speech"], last["speech"])
        if previous >= 0.6 and current >= 0.6:
            found.append(
                {
                    "session_id": path.parent.name,
                    "first_turn": begin,
                    "last_turn": end,
                    "adjacent_similarity": [round(previous, 4), round(current, 4)],
                }
            )
    return found


def main() -> None:
    paths = sorted(ROOT.glob("*/sessions/*/state.json"))
    paths = [path for path in paths if "P3" not in path.parents[2].name]
    windows = [window for path in paths for window in reconstruct(path)]
    result = {
        "scope": "Archived non-P3 state files; historical selector not recovered",
        "state_files": len(paths),
        "sessions_with_windows": len({row["session_id"] for row in windows}),
        "windows": windows,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    session_count = result["sessions_with_windows"]
    print(f"{len(paths)} states, {len(windows)} windows, {session_count} sessions")


if __name__ == "__main__":
    main()
