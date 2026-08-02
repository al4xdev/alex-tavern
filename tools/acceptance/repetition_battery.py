"""Live repetition battery: run cells against a real provider, score them offline.

One CELL is one engine configuration; one RUN is one session inside a cell. Cells
are spawned as subprocesses because ``src/paths.py`` resolves ROLEPLAY_DATA_DIR at
import time, so two configurations cannot share a process (the same reason
``roteiro_ab.py`` and ``watcher_abc.py`` fork).

Controls held fixed for every cell, each one a confounder verified in the
evidence sessions:

* ``auto_event_enabled=False`` — the drive seeds events by design grown from a
  thread already in play, which is textually next door to a re-narration. It
  fired in both evidence sessions.
* ``character_roteiro_alignment_enabled=False`` — re-injects the same
  beat-derived impulse into the same actors every pinned turn
  (``alignment:impulse`` fired 21x in 20d4cdb3). Leaving it on makes the beat
  clock a two-variable manipulation.
* ``automatic_compaction_enabled=False`` — a long run in one cell must not
  compact while a short one does not.

Cell order is randomized inside each replicate block, so provider load and
prompt-cache warmth cannot line up with cell identity.

Phase 0.5 uses one cell (``base``) to re-baseline after the deterministic cuts.
The factor cells are declared here so the Phase 2 battery is a flag change, not
a rewrite.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "plans/artifacts/repetition-battery"
# A git worktree pinned at the pre-fix commit, holding today's tooling but the
# OLD engine. It exists because the provider updated `deepseek-v4-flash` in
# place on 2026-07-31: the reference sessions from 07-28 and everything run now
# carry the SAME model id in the log while being different weights, so a
# before/after against them conflates the code fixes with a model upgrade. The
# only way to attribute anything is to run the old engine on today's model.
PREFIX_REPO = Path("/tmp/alex-tavern-prefix")

# cell -> config overrides on top of the shared controls.
CELLS: dict[str, dict] = {
    # Roteiro off entirely. The cheapest possible refutation of the whole
    # premise: if repetition is no worse here, the roteiro is what causes it and
    # tuning its clock is the wrong lever.
    "null": {"roteiro_enabled": False},
    # The engine as shipped (post Phase-0.5 cuts).
    "base": {"roteiro_enabled": True},
    # The CONTROL: pre-fix engine, current model. `base` minus this is the
    # effect of the code; `oldcode` minus the 07-28 sessions is the effect of
    # the model. Without it neither is knowable.
    "oldcode": {"_repo": PREFIX_REPO, "roteiro_enabled": True},
    # The drive back ON. Pinning it off removed the only hint producer that has
    # a cooldown, which means every earlier measurement was blind to whether the
    # drive repeats its own seeds. Its prompt asks for an event grown from a
    # thread already in play, so it is the remaining plausible repeat source —
    # and this cell is the gate for building a producer-agnostic idempotence
    # guard, which is not worth a schema bump on a hypothesis.
    "drive": {"roteiro_enabled": True, "auto_event_enabled": True},
}

# Input profiles decide which engine PATH the session exercises, which matters
# more than it looks: a bare skip runs the autonomous burst (`max_beats` > 1)
# and is the only path where `repeats_event_text` dedups stimuli at all. Any
# turn with content collapses to a single beat and gets NO stimulus dedup
# whatsoever. P1 alone therefore measures the path that already has a filter.
#
# The lines are deliberately inert — the player observes and reacts without
# steering — so the NPCs and the roteiro still carry the scene in both profiles.
PROFILE_INPUTS: dict[str, list[tuple[str, str | None]]] = {
    # Length-matched to P1 on purpose. A skip commits up to 6 turns, a spoken
    # turn commits exactly 1, so the same 10 inputs give P1 ~40 turns and P2 ~10.
    # Recurrence can only rise with length (every stimulus gets a larger pool of
    # priors to match), so a short P2 would score near zero for reasons that have
    # nothing to do with the engine. 40 lines, 40 turns.
    #
    # All 40 DISTINCT. A first draft repeated 20 lines twice and scored 20
    # ECHO_PERSIST hits in every cell — the fixture duplicating itself, not the
    # engine. The metric now skips the Player sentinel as well; both fixes are
    # needed, because an input profile must not be able to author its own result.
    "P2": [
        ("speech", "Continuo aqui."),
        ("speech", "Que seja."),
        ("speech", "Estou vendo."),
        ("speech", "Nao tenho pressa."),
        ("speech", "Pode seguir."),
        ("speech", "Anotado."),
        ("speech", "Fico atento."),
        ("speech", "Sem problema."),
        ("speech", "Acompanho de perto."),
        ("speech", "Vamos ver no que da."),
        ("speech", "Nada a acrescentar."),
        ("speech", "Prossigam."),
        ("speech", "Escuto."),
        ("speech", "Como quiserem."),
        ("speech", "Aguardo."),
        ("speech", "Fica registrado."),
        ("speech", "Observo daqui."),
        ("speech", "Segue o baile."),
        ("speech", "Nao me oponho."),
        ("speech", "Concordo."),
        ("speech", "Faz sentido."),
        ("speech", "Vejo o mesmo."),
        ("speech", "Deixo com voces."),
        ("speech", "Estou junto."),
        ("speech", "Tudo anotado."),
        ("speech", "Sigo atras."),
        ("speech", "Nao atrapalho."),
        ("speech", "Melhor assim."),
        ("speech", "Percebi."),
        ("speech", "Vamos la."),
        ("speech", "Confirmo."),
        ("speech", "Sem objecao."),
        ("speech", "Entendido."),
        ("speech", "Ficou claro."),
        ("speech", "Acompanhando ainda."),
        ("speech", "Nada muda pra mim."),
        ("speech", "Por mim tudo bem."),
        ("speech", "Continuem entao."),
        ("speech", "Estou pronto."),
        ("speech", "Ate aqui, bem."),
    ],
}


SHARED_CONTROLS = {
    "auto_event_enabled": False,
    "character_roteiro_alignment_enabled": False,
    "automatic_compaction_enabled": False,
    "autonomous_burst_max_beats": 6,
    "llm_timeout_seconds": 180.0,
    # Pinned, not inherited. The evidence sessions 20d4cdb3 and 15d40dfa ran in
    # Brazilian Portuguese while `.data/config.json` has since moved to English;
    # scoring a Portuguese baseline against English runs would compare two
    # different repetition regimes (and two different SequenceMatcher regimes).
    # Pinning also stops a mid-battery config edit from splitting the cells.
    "language": "Brazilian Portuguese",
}


def run_one(
    cell: str,
    profile: str,
    replicate: int,
    scenario: str,
    max_inputs: int = 0,
    config_path: Path | None = None,
) -> dict:
    """Drive one session in THIS process. ROLEPLAY_DATA_DIR is already set."""
    import asyncio

    import httpx

    from src.config import load_config, resolve_active_config
    from src.runner import Runner
    from tools.acceptance.roteiro_ab import _build_session_args

    session_args, inputs = _build_session_args(scenario)
    if profile in PROFILE_INPUTS:
        inputs = PROFILE_INPUTS[profile]
    if max_inputs:
        inputs = inputs[:max_inputs]
    # Provider and key come from the real config; sessions are written to the
    # isolated dir the parent handed us.
    # Always the REAL config (provider, key, model). A cell running from the
    # pre-fix worktree has no `.data` of its own, and duplicating the API key
    # into /tmp to give it one would be worse than passing the path.
    config = resolve_active_config(load_config(config_path or (REPO / ".data/config.json")))
    config.update(SHARED_CONTROLS)
    config.update({k: v for k, v in CELLS[cell].items() if not k.startswith("_")})

    async def _go() -> dict:
        async with httpx.AsyncClient() as client:
            runner = Runner(client, config)
            sid = await runner.start_session(session_args)
            for kind, text in inputs:
                if kind == "speech":
                    await runner.player_turn(sid, speech=text)
                else:
                    await runner.player_turn(sid, skip=True)
            return {"session_id": sid}

    result = asyncio.run(_go())
    # Provenance: what actually produced these numbers. Without it a later
    # reader cannot tell whether two cells differed by the factor or by a
    # provider/model/language change between runs.
    provenance = {
        key: config.get(key)
        for key in (
            "provider",
            "model",
            "language",
            "context_max",
            "thinking_enabled",
            "roteiro_enabled",
            "character_roteiro_alignment_enabled",
            "auto_event_enabled",
            "automatic_compaction_enabled",
            "autonomous_burst_max_beats",
        )
    }
    return {
        "cell": cell,
        "profile": profile,
        "replicate": replicate,
        "inputs": len(inputs),
        "provenance": provenance,
        **result,
    }


def score(session_id: str, data_dir: Path) -> dict:
    from tools.acceptance.repetition_metrics import analyze

    report = analyze(session_id, root=data_dir / "sessions")
    from dataclasses import asdict

    return asdict(report)


def _spawn(cell: str, profile: str, replicate: int, scenario: str, max_inputs: int) -> dict:
    data_dir = BASE / f"{cell}-{profile}-r{replicate}"
    data_dir.mkdir(parents=True, exist_ok=True)
    # A cell may declare its own repo root: same tooling, different `src`.
    repo = Path(CELLS[cell].get("_repo", REPO))
    script = repo / "tools" / "acceptance" / "repetition_battery.py"
    env = dict(
        os.environ,
        ROLEPLAY_DATA_DIR=str(data_dir),
        PYTHONPATH=str(repo),
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--exec-one",
            "--cell",
            cell,
            "--profile",
            profile,
            "--replicate",
            str(replicate),
            "--scenario",
            scenario,
            "--max-inputs",
            str(max_inputs),
            "--config-path",
            str(REPO / ".data/config.json"),
        ],
        env=env,
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    # A provider hiccup must cost ONE run, not the battery. A malformed response
    # that survives all retries killed a 6-run P2 battery after 3.5 runs; the
    # completed cells were still valid and the remaining ones simply never ran.
    # Report the gap and carry on — an unbalanced design is analysable, a
    # truncated one is not even that.
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print(f"  !! {cell}/{profile} r{replicate} FAILED, continuing")
        return {}
    for line in proc.stdout.splitlines():
        if line.startswith("RUN "):
            return json.loads(line[4:])
    print(f"  !! {cell}/{profile} r{replicate} produced no RUN line, continuing")
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", action="append", help="cell name (repeatable); default: all")
    parser.add_argument("--profile", default="P1")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--scenario", default="turma-dos-portais-pt-full")
    parser.add_argument("--seed", type=int, default=20260801, help="cell-order randomization seed")
    parser.add_argument(
        "--max-inputs",
        type=int,
        default=0,
        help="truncate the input profile (0 = full); use a small value to smoke-test plumbing",
    )
    parser.add_argument("--config-path", default="", help=argparse.SUPPRESS)
    parser.add_argument("--exec-one", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--replicate", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.exec_one:
        assert args.cell and len(args.cell) == 1
        outcome = run_one(
            args.cell[0],
            args.profile,
            args.replicate,
            args.scenario,
            args.max_inputs,
            Path(args.config_path) if args.config_path else None,
        )
        print("RUN " + json.dumps(outcome, ensure_ascii=False))
        return

    cells = args.cell or list(CELLS)
    rng = random.Random(args.seed)
    runs: list[dict] = []
    for replicate in range(1, args.replicates + 1):
        block = list(cells)
        rng.shuffle(block)  # block on replicate, randomize cell order within it
        for cell in block:
            run = _spawn(cell, args.profile, replicate, args.scenario, args.max_inputs)
            if not run:
                continue
            data_dir = BASE / f"{cell}-{args.profile}-r{replicate}"
            run["metrics"] = score(run["session_id"], data_dir)
            run["data_dir"] = str(data_dir)
            runs.append(run)
            metrics = run["metrics"]
            print(
                f"  {cell:6s} r{replicate} {run['session_id']}  "
                f"turns={metrics['turns']:3d} "
                f"RSR_prop={_pct(metrics['rsr_prop'])} "
                f"ECHO={metrics['echo_persist']} "
                f"BOCC={metrics['beat_occupancy_max']} "
                f"SIL={_pct(metrics['sil'])} "
                f"GUARD={_pct(metrics['guard'])} "
                f"NSR={_round(metrics['nsr'])}"
            )

    BASE.mkdir(parents=True, exist_ok=True)
    results = BASE / "results.json"
    results.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRESULTS {results}")
    _summarize(runs)


def _pct(value: float | None) -> str:
    return "  n/a" if value is None else f"{value * 100:5.1f}%"


def _round(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _summarize(runs: list[dict]) -> None:
    by_cell: dict[str, list[dict]] = {}
    for run in runs:
        by_cell.setdefault(run["cell"], []).append(run["metrics"])
    print("\ncell    n  RSR_prop  ECHO  BOCC   SIL   GUARD  NSR")
    for cell, metrics in by_cell.items():

        def mean(field: str, rows: list[dict] = metrics) -> float | None:
            values = [row[field] for row in rows if row[field] is not None]
            return sum(values) / len(values) if values else None

        print(
            f"{cell:6s} {len(metrics):2d}  {_pct(mean('rsr_prop'))}  "
            f"{_round(mean('echo_persist'))}  {_round(mean('beat_occupancy_max'))}  "
            f"{_pct(mean('sil'))} {_pct(mean('guard'))} {_round(mean('nsr'))}"
        )


if __name__ == "__main__":
    main()
