from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main() -> None:
    source = ROOT / "plans/artifacts/77-p3-input-dispatch/live/sessions/fb62cc2f"
    state_raw = (source / "state.json").read_bytes()
    log_raw = (source / "debug.jsonl").read_bytes()
    state = json.loads(state_raw)
    rows = [json.loads(line) for line in log_raw.splitlines()]
    before = next(
        record["scene_snapshot"] for record in state["history"] if record["turn_number"] == 3
    )
    row = rows[41]
    assert row["agent"] == "director" and row["turn_number"] == 4 and row["error"] is None
    delta = json.loads(row["response"])["scene_update"]
    old_key = "plataforma_de_comando"
    new_key = "feridos_no_portao_leste"
    before_facts = before["physical_facts"]
    assert old_key in before_facts and new_key not in before_facts
    assert old_key not in delta and new_key in delta
    os.environ["ROLEPLAY_DATA_DIR"] = tempfile.mkdtemp(prefix="tavern-state-delta-")
    sys.path.insert(0, str(ROOT))
    from src.runner import Runner

    game = SimpleNamespace(scene=SimpleNamespace(**copy.deepcopy(before)))
    Runner.__new__(Runner)._update_scene(game, delta)
    after = game.scene.physical_facts
    assert after[old_key] == before_facts[old_key]
    assert after[new_key] == delta[new_key]
    next_snapshot = next(
        record["scene_snapshot"] for record in state["history"] if record["turn_number"] == 4
    )
    assert after == next_snapshot["physical_facts"]
    result = {
        "session_id": "fb62cc2f",
        "turn_number": 4,
        "accepted_debug_line": 42,
        "state_sha256": hashlib.sha256(state_raw).hexdigest(),
        "log_sha256": hashlib.sha256(log_raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "previous_retained": {old_key: after[old_key]},
        "new_added": {new_key: after[new_key]},
        "delta_mentions_old_key": False,
        "matches_next_persisted_snapshot": True,
    }
    with (OUT / "state-delta-trace.json").open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
