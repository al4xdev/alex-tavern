from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main() -> None:
    data_root = Path(tempfile.mkdtemp(prefix="tavern-intake-boundary-"))
    os.environ["ROLEPLAY_DATA_DIR"] = str(data_root)
    sys.path.insert(0, str(ROOT))
    import src.runner as runner_module
    from src.paths import SESSIONS_DIR
    from src.store.sessions import load_game, save_game
    from tests.factories import make_game

    assert SESSIONS_DIR.is_relative_to(data_root)
    cases = json.loads((OUT / "cases.json").read_text())
    case = cases[4]
    assert case["turn"] == 8 and case["line"] == 92
    assert case["proposed_delta"]["doors_state"] == "trancadas"
    before_rule = json.loads((OUT / "intake-before.json").read_text())
    namespace = dict(vars(runner_module))
    namespace["_TRANSIENT_FACT_KEY"] = re.compile(before_rule["suffix_pattern"])
    exec(before_rule["predicate"], namespace)
    old_predicate = namespace["_fact_key_admissible"]
    current_predicate = runner_module._fact_key_admissible
    game = make_game(session_id="intake-boundary")
    game.scene.physical_facts = copy.deepcopy(case["prior_facts"])
    old_game = copy.deepcopy(game)
    runner = runner_module.Runner.__new__(runner_module.Runner)
    runner_module._fact_key_admissible = old_predicate
    try:
        runner._update_scene(old_game, case["proposed_delta"])
    finally:
        runner_module._fact_key_admissible = current_predicate
    runner._update_scene(game, case["proposed_delta"])
    assert "doors_state" not in old_game.scene.physical_facts
    assert game.scene.physical_facts["doors_state"] == "trancadas"
    without_door = dict(game.scene.physical_facts)
    without_door.pop("doors_state")
    assert without_door == old_game.scene.physical_facts
    save_game(game)
    loaded = load_game(game.session_id)
    assert loaded is not None and loaded.scene.physical_facts == game.scene.physical_facts
    result = {
        "source": case["source"],
        "line": case["line"],
        "before": old_game.scene.physical_facts,
        "after": game.scene.physical_facts,
        "sole_added_fact": {"doors_state": "trancadas"},
        "save_load_equal": True,
        "isolated_data_root": str(data_root),
        "runner_sha256": hashlib.sha256(Path(runner_module.__file__).read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with (OUT / "boundary-result.json").open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(
        "PASS: original predicate drops the lock; new predicate preserves it; "
        "other facts equal; save/load preserves result"
    )


if __name__ == "__main__":
    main()
