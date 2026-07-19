"""Task 33b+40 battery: A free / B arbitrary disruption / C clock+causal watcher.

Doc §7 of docs/cases (scene-state-transition): same scenario, same passive
player inputs; arms differ only in the system driving the world forward.
B and C share the SAME deterministic stall trigger (delta audit + ladder), so
the isolated variable between them is the intervention CONTRACT: an arbitrary
template event versus the causal contract tied to existing threads.

Arms (one subprocess each, isolated ROLEPLAY_DATA_DIR — see roteiro_ab.py):
  A a_free       roteiro OFF, no watcher (free baseline)
  B b_arbitrary  roteiro OFF, watcher trigger -> fixed unrelated template event
  C c_causal     roteiro ON (clock), watcher trigger -> causal intervention

Measurement (offline, arm-neutral): per-turn material-delta audit over each
final history; lexical metrics; blind critic scoring sustained progress and
causal coherence WITHOUT knowing the arm.

Usage:
  python tools/acceptance/watcher_abc.py            # orchestrate everything
  python tools/acceptance/watcher_abc.py --arm b_arbitrary   # one arm
  python tools/acceptance/watcher_abc.py --audit <sid>       # offline audit
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BASE = REPO / "plans/artifacts/watcher-abc"
SCENARIO = "turma-dos-portais-pt"
ARBITRARY_EVENT = (
    "Uma figura encapuzada irrompe pela porta principal, derruba um lampiao "
    "acesso e exige a atencao de todos no salao."
)
ARMS = ["a_free", "b_arbitrary", "c_causal"]


def _config() -> dict:
    from src.config import load_config, resolve_active_config

    config = resolve_active_config(load_config(REPO / ".data/config.json"))
    config.update(
        {
            "autonomous_burst_max_beats": 1,
            "llm_timeout_seconds": 120.0,
        }
    )
    return config


async def run_arm(arm: str) -> str:
    import httpx

    from src.runner import Runner
    from tools.acceptance.roteiro_ab import SCENARIOS, _build_session_args
    from tools.watcher_experiment import StallLadder, audit_turn, causal_intervention

    assert SCENARIO in SCENARIOS
    session_args, inputs = _build_session_args(SCENARIO)
    config = _config()
    config["roteiro_enabled"] = arm == "c_causal"
    watched = arm in ("b_arbitrary", "c_causal")

    ladder = StallLadder(threshold=2, refractory_turns=3)
    injections: list[dict] = []
    audits: list[dict] = []
    pending_hint = ""

    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)
        sid = runner.start_session(session_args)
        for kind, text in inputs:
            hint = pending_hint
            pending_hint = ""
            if kind == "speech":
                result = await runner.player_turn(sid, speech=text, narrator_hint=hint)
            else:
                result = await runner.player_turn(sid, skip=True, narrator_hint=hint)
            turn = result["turn_number"]
            if not watched:
                continue
            game = await runner.get_state(sid)
            audit = await audit_turn(client, config, game, turn)
            audits.append(
                {"turn": turn, "deltas": audit.get("deltas"), "j": audit.get("justification")}
            )
            if ladder.observe(turn, list(audit.get("deltas") or [])):
                if arm == "b_arbitrary":
                    pending_hint = ARBITRARY_EVENT
                    injections.append({"turn_injected_after": turn, "hint": pending_hint})
                else:
                    proposal = await causal_intervention(client, config, game)
                    event = str(proposal.get("intervention", {}).get("event_now", "")).strip()
                    if event:
                        pending_hint = event
                        injections.append(
                            {
                                "turn_injected_after": turn,
                                "hint": event,
                                "source_thread": proposal["intervention"].get("source_thread"),
                                "expected_delta": proposal["intervention"].get("expected_delta"),
                            }
                        )
        game = await runner.get_state(sid)

    summary = {
        "arm": arm,
        "session_id": sid,
        "turns": game.history[-1].turn_number if game.history else 0,
        "narrative_tick": game.narrative_tick,
        "live_audits": audits,
        "injections": injections,
        "ladder_fired_at": ladder.fired,
    }
    print("ARM_SUMMARY " + json.dumps(summary, ensure_ascii=False))
    return sid


async def offline_audit(sid: str) -> None:
    """Arm-neutral measurement: audit every committed turn of a finished run."""
    import httpx

    from src.store.sessions import load_game
    from tools.watcher_experiment import audit_turn

    game = load_game(sid)
    assert game is not None
    config = _config()
    turns = sorted({r.turn_number for r in game.history if r.content_type != "thought"})
    out = []
    async with httpx.AsyncClient() as client:
        for turn in turns:
            audit = await audit_turn(client, config, game, turn)
            deltas = [d for d in (audit.get("deltas") or []) if d != "none"]
            out.append({"turn": turn, "deltas": deltas, "j": str(audit.get("justification"))[:120]})
    material = sum(1 for entry in out if entry["deltas"])
    print(
        "OFFLINE_AUDIT "
        + json.dumps(
            {"session_id": sid, "material_turns": material, "total_turns": len(out), "turns": out},
            ensure_ascii=False,
        )
    )


def transcript_of(sid: str) -> str:
    from src.store.sessions import load_game
    from tools.watcher_experiment import format_records

    game = load_game(sid)
    assert game is not None
    visible = [r for r in game.history if r.content_type != "thought"]
    return format_records(game, visible, clip=400)


async def blind_critic(transcripts: dict[str, str]) -> None:
    """Score shuffled, unlabeled transcripts: progress + causal coherence."""
    import random

    import httpx

    from src.config import llm_request_options
    from src.llm.client import chat_completion_json, resolve_llm_timeout

    config = _config()
    schema = {
        "name": "blind_critique",
        "schema": {
            "type": "object",
            "properties": {
                "sustained_progress": {"type": "integer", "minimum": 1, "maximum": 5},
                "causal_coherence": {"type": "integer", "minimum": 1, "maximum": 5},
                "stagnation_stretches": {"type": "integer", "minimum": 0},
                "incoherent_events": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
            "required": [
                "sustained_progress",
                "causal_coherence",
                "stagnation_stretches",
                "incoherent_events",
                "notes",
            ],
            "additionalProperties": False,
        },
    }
    system = (
        "You are a blind story critic. You receive ONE interactive-fiction "
        "transcript. Score it:\n"
        "- sustained_progress (1-5): does the story keep producing material "
        "change, or does it linger reacting to the same stimulus?\n"
        "- causal_coherence (1-5): do new events grow from what was already in "
        "play, or do unrelated things intrude out of nowhere?\n"
        "- stagnation_stretches: count of stretches of 2+ consecutive turns "
        "with no material change.\n"
        "- incoherent_events: quote any event that appears with no causal root.\n"
        "Judge only the text. Answer in the transcript's language."
    )
    order = list(transcripts)
    random.shuffle(order)
    async with httpx.AsyncClient() as client:
        for label in order:
            for attempt in range(2):
                result = await chat_completion_json(
                    client,
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"TRANSCRIPT:\n{transcripts[label]}"},
                    ],
                    model=config.get("model", ""),
                    language=config.get("language", ""),
                    max_tokens=800,
                    timeout=resolve_llm_timeout(config),
                    json_schema=schema,
                    session_id="",
                    turn_number=0,
                    agent="watcher:critic",
                    **llm_request_options(config),
                )
                print(
                    "CRITIC "
                    + json.dumps({"arm": label, "attempt": attempt, **result}, ensure_ascii=False)
                )


def _spawn(args: list[str], data_dir: Path) -> str:
    env = dict(os.environ, ROLEPLAY_DATA_DIR=str(data_dir), PYTHONPATH=str(REPO))
    proc = subprocess.run(
        [sys.executable, __file__, *args],
        env=env,
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stdout.flush()
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"{args} failed (exit {proc.returncode})")
    return proc.stdout


def _sid_from(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("ARM_SUMMARY "):
            return json.loads(line[len("ARM_SUMMARY ") :])["session_id"]
    raise SystemExit("no ARM_SUMMARY in arm output")


def orchestrate() -> None:
    sids: dict[str, str] = {}
    for arm in ARMS:
        out = _spawn(["--arm", arm], BASE / arm / "data")
        sids[arm] = _sid_from(out)
    for arm in ARMS:
        _spawn(["--audit", sids[arm]], BASE / arm / "data")
    transcripts = {}
    for arm in ARMS:
        out = _spawn(["--transcript", sids[arm]], BASE / arm / "data")
        transcripts[arm] = out.split("TRANSCRIPT_BEGIN\n", 1)[-1]
    asyncio.run(blind_critic(transcripts))
    print("ARTIFACT_DIR " + str(BASE))
    print("SESSIONS " + json.dumps(sids))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--audit", metavar="SID")
    parser.add_argument("--transcript", metavar="SID")
    args = parser.parse_args()
    if args.arm:
        asyncio.run(run_arm(args.arm))
    elif args.audit:
        asyncio.run(offline_audit(args.audit))
    elif args.transcript:
        print("TRANSCRIPT_BEGIN")
        print(transcript_of(args.transcript))
    else:
        orchestrate()


if __name__ == "__main__":
    main()
