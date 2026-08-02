"""Materialize a battery run into `benchmarks/`, keyed by the engine that ran it.

A benchmark number is only meaningful next to the thing that produced it, and in
this project TWO things move underneath: the engine and the provider's weights.
DeepSeek updated `deepseek-v4-flash` in place on 2026-07-31 — same model id in
every log, different model — which silently confounded a before/after until a
control cell was added. So a benchmark is filed under BOTH, and either one
changing invalidates comparison with it.

The engine key is a fingerprint of `src/**/*.py`, not a commit: batteries are
routinely run from a dirty tree, and a commit hash would claim precision the run
did not have. The commit is recorded too, for humans.

Raw sessions are NOT archived — one is ~14MB and a battery is ~500MB. What is
kept is what can be read or re-checked later: the scored metrics, the
provenance, and a readable transcript per run (``tools/render_transcript``),
because reading the transcript is what found the defects the metrics missed.

    uv run python -m tools.acceptance.archive_benchmark <artifact-dir> --label p1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO / "benchmarks"


def engine_fingerprint(repo: Path) -> str:
    """Stable short hash of the engine source, dirty tree included."""
    digest = hashlib.sha256()
    for path in sorted((repo / "src").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        digest.update(path.relative_to(repo).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def describe_engine(repo: Path) -> dict:
    return {
        "fingerprint": engine_fingerprint(repo),
        "commit": _git(repo, "rev-parse", "--short", "HEAD"),
        "commit_subject": _git(repo, "log", "-1", "--format=%s"),
        "dirty": bool(_git(repo, "status", "--porcelain", "src")),
    }


def collect(artifact_dir: Path, label: str) -> dict:
    """Score every run under ``artifact_dir`` and gather its provenance."""
    from tools.acceptance.repetition_metrics import analyze

    results_file = artifact_dir / "results.json"
    provenance = {}
    if results_file.exists():
        for row in json.loads(results_file.read_text()):
            provenance[row["session_id"]] = row.get("provenance", {})

    runs = []
    for run_dir in sorted(artifact_dir.glob("*-r*")):
        states = list((run_dir / "sessions").glob("*/state.json"))
        if not states:
            continue
        session_id = states[0].parent.name
        cell, _, replicate = run_dir.name.rpartition("-r")
        cell_name, _, profile = cell.rpartition("-")
        runs.append(
            {
                "run": run_dir.name,
                "cell": cell_name,
                "profile": profile,
                "replicate": int(replicate),
                "session_id": session_id,
                "provenance": provenance.get(session_id, {}),
                "metrics": asdict(analyze(session_id, root=run_dir / "sessions")),
                "_session_dir": states[0].parent,
            }
        )
    return {"label": label, "runs": runs}


def write_archive(collected: dict, engine: dict, out: Path) -> Path:
    from tools.render_transcript import load_state, render_session

    out.mkdir(parents=True, exist_ok=True)
    (out / "transcripts").mkdir(exist_ok=True)

    models = sorted(
        {r["provenance"].get("model", "?") for r in collected["runs"] if r["provenance"]}
    )
    manifest = {
        "label": collected["label"],
        "archived_at": datetime.now(UTC).isoformat(),
        "engine": engine,
        "models": models,
        "model_note": (
            "Provider weights can change without the id changing; a benchmark is "
            "comparable only to runs on the same id AND the same weights window."
        ),
        "runs": [
            {k: v for k, v in run.items() if k not in ("metrics", "_session_dir")}
            for run in collected["runs"]
        ],
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "metrics.json").write_text(
        json.dumps(
            [{k: v for k, v in r.items() if k != "_session_dir"} for r in collected["runs"]],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for run in collected["runs"]:
        text = render_session(load_state(run["_session_dir"]))
        (out / "transcripts" / f"{run['run']}.md").write_text(text, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--label", required=True, help="what this battery answered, e.g. 'p1'")
    parser.add_argument(
        "--engine-repo",
        type=Path,
        default=REPO,
        help="repo whose src produced the runs (a worktree for a control cell)",
    )
    args = parser.parse_args()

    engine = describe_engine(args.engine_repo)
    collected = collect(args.artifact_dir, args.label)
    if not collected["runs"]:
        raise SystemExit(f"no scored runs under {args.artifact_dir}")
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    out = BENCHMARKS / f"{stamp}-{engine['fingerprint']}-{args.label}"
    write_archive(collected, engine, out)
    print(f"ARCHIVED {out}  ({len(collected['runs'])} runs, engine {engine['fingerprint']})")


if __name__ == "__main__":
    main()
