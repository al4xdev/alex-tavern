from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main() -> None:
    sys.path.insert(0, str(ROOT))

    from tools.playtest_harness import prepare_output_dir

    run_dir = prepare_output_dir(OUT / "live")
    os.environ["ROLEPLAY_DATA_DIR"] = str(run_dir)

    from src.config import load_config, resolve_active_config
    from src.paths import DATA_DIR
    from tools.acceptance.repetition_battery import CELLS, SHARED_CONTROLS, run_one

    assert DATA_DIR.resolve() == run_dir
    config_path = ROOT / ".data/config.json"
    assert config_path.is_file()
    config = resolve_active_config(load_config(config_path))
    config.update(SHARED_CONTROLS)
    config.update(CELLS["base"])
    settings = {
        key: config.get(key)
        for key in (
            "provider",
            "model",
            "language",
            "context_max",
            "thinking_enabled",
            "max_tokens_narrator",
            "max_tokens_character",
            "llm_timeout_seconds",
            "autonomous_burst_max_beats",
            "roteiro_enabled",
            "automatic_compaction_enabled",
            "auto_event_enabled",
            "character_roteiro_alignment_enabled",
        )
    }
    sources = [
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("src/scenarios/*.json"),
        *ROOT.glob("src/characters/*.json"),
        ROOT / "tools/acceptance/repetition_battery.py",
        ROOT / "tools/acceptance/roteiro_ab.py",
        OUT / "LIVE-PLAN.md",
        Path(__file__),
    ]
    manifest = {
        "started_unix": time.time(),
        "settings": settings,
        "source_hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (run_dir / "executed-script.py").write_bytes(Path(__file__).read_bytes())
    try:
        result = run_one("base", "P3", 1, "turma-dos-portais-pt-full", 3, config_path)
    except Exception as exc:
        (run_dir / "outcome.json").write_text(
            json.dumps({"error_type": type(exc).__name__, "finished_unix": time.time()}) + "\n"
        )
        raise
    else:
        result["finished_unix"] = time.time()
        (run_dir / "outcome.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
