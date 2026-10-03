"""Controlled semantic guidance in prose versus JSON Schema descriptions."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src import roteiro as production

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-plan-label-current-builder/screen.py"
spec = importlib.util.spec_from_file_location("label_screen", BASE)
assert spec is not None and spec.loader is not None
shared: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
baseline = shared.baseline

DEFINITIONS = {
    "act_completed": (
        "Whether the CURRENT ACT's exit condition was satisfied by events ALREADY "
        "CONFIRMED before this new plan. An attempt is not its successful result. "
        "Actor/anchor coverage, elapsed time, replacing a beat, or a planned event "
        "does not prove act completion. False while its exit remains unsatisfied."
    ),
    "beat": (
        "The NEXT prospective situation to develop from the confirmed current world. "
        "The supplied old beat is planning guidance, not evidence that its intent "
        "or exit occurred. Confirmed events outrank that plan. Replacing a beat "
        "and completing an act are separate decisions."
    ),
    "intent": (
        "A prospective situation or external pressure, never a character's scripted "
        "choice. Start from confirmed events and current location. A settled "
        "physical result remains established: do not repeat its transition or "
        "presume its earlier state still holds. A subsequent reversal requires "
        "an explicitly new event with a cause."
    ),
    "expected_actors": (
        "Character IDs requested to receive stage time during the beat. Presence "
        "is requested; their decisions, speech and actions are not scripted."
    ),
    "expected_anchors": (
        "Two to four short concrete objects, places or names that physically enter "
        "or change when this beat lands, not conversation topics or a request "
        "to introduce an unchanged object that is already in play again."
    ),
    "exit_condition": (
        "One observable FUTURE condition ending this new beat, not a claim it "
        "already occurred and not evidence that the previous act is complete."
    ),
    "budget_turns": "How many turns this prospective beat deserves, from two to ten.",
}


def messages_for(game: Any, roteiro: Any, reason: str, scope: str, arm: str) -> list[dict]:
    messages = production.build_next_beat_messages(game, roteiro, reason, scope)
    if arm == "control":
        return messages
    system = messages[0]["content"]
    start = system.index("- expected_actors:")
    end = system.index("- Each act declares", start)
    system = system[:start] + system[end:]
    old = "Set act_completed\naccordingly."
    assert old in system
    system = system.replace(old, "", 1)
    if arm == "text_contract":
        system += "\nFIELD CONTRACT:\n" + "\n".join(
            f"{key}: {value}" for key, value in DEFINITIONS.items()
        )
    messages[0]["content"] = system
    return messages


def schema_for(scope: str, arm: str) -> dict:
    schema = copy.deepcopy(production.build_next_beat_schema(scope))
    if arm != "schema_contract":
        return schema
    props = schema["schema"]["properties"]
    props["act_completed"]["description"] = DEFINITIONS["act_completed"]
    props["beat"]["description"] = DEFINITIONS["beat"]
    for key, value in DEFINITIONS.items():
        if key not in {"act_completed", "beat"}:
            props["beat"]["properties"][key]["description"] = value
    return schema


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        Path(baseline.__file__),
        ROOT / "src/roteiro.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if shared.MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    cfg = baseline.config()
    cases = []
    for fixture in baseline.fixtures():
        if fixture["id"] not in {"portal_attempt", "portal_closed", "portal_left"}:
            continue
        early, late = baseline.game_for(fixture, False), baseline.game_for(fixture, True)
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        later = baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        decision = first if first.action else later
        game = early if first.action else late
        assert decision.action is not None
        scope = "act" if decision.action == "replan_act" else "beat"
        assert scope == "beat", "Act rewriting needs a separate field relocation"
        for arm in ("control", "text_contract", "schema_contract"):
            # Local capture only: no production globals or files modified.
            def build_messages(*args: Any, selected_arm: str = arm) -> list[dict]:
                return messages_for(*args, selected_arm)

            def build_schema(selected_scope: str, selected_arm: str = arm) -> dict:
                return schema_for(selected_scope, selected_arm)

            old_messages = baseline.build_next_beat_messages
            old_schema = baseline.build_next_beat_schema
            try:
                baseline.build_next_beat_messages = build_messages
                baseline.build_next_beat_schema = build_schema
                request = await baseline.captured_request(game, decision.reason, scope, cfg)
            finally:
                baseline.build_next_beat_messages = old_messages
                baseline.build_next_beat_schema = old_schema
            f = copy.deepcopy(fixture)
            f["id"] += "-" + arm
            cases.append(
                {
                    "fixture": f,
                    "arm": arm,
                    "request": request,
                    "decision": asdict(decision),
                    "canonical_scene": asdict(game.scene),
                    "schema": schema_for(scope, arm)["schema"],
                }
            )
    baseline.write(
        shared.MANIFEST,
        {
            "hashes": hashes(),
            "definitions": DEFINITIONS,
            "cases": cases,
            "provider": {k: cfg[k] for k in ("model", "api_base", "language")},
        },
    )
    print("Frozen nine cells, four curls each, matching text/schema definitions")


if __name__ == "__main__":
    shared.HERE = HERE
    shared.MANIFEST = HERE / "manifest.json"
    shared.hashes = hashes
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else shared.run())
