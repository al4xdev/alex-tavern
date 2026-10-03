"""Production Director replies to generated beats with cognition/clue contrast."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

from src.models import RoteiroBeat, TurnRecord, deepcopy_scene

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cognition_director", HERE / "director_refusal.py")
assert spec is not None and spec.loader is not None
director: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(director)
baseline = director.baseline
director.OUT = HERE / "director-cognition"
director.MANIFEST = HERE / "director-cognition-manifest.json"


def definitions() -> list[dict[str, Any]]:
    mapping = json.loads((HERE / "adversarial-reader-mapping.json").read_text())
    rows = []
    for name, label in (
        ("prescribed_cognition", "held-B"),
        ("observable_clue", "held-B"),
        ("external_shockwave", "held-C"),
    ):
        source = HERE / "adversarial-runs" / mapping[label]
        raw = json.loads(source.read_text())
        assert raw["valid"]
        beat = copy.deepcopy(raw["output"]["beat"])
        if name == "observable_clue":
            old = "Bento enxerga a lógica do mecanismo"
            assert beat["intent"].count(old) == 1
            beat["intent"] = beat["intent"].replace(
                old, "Uma sequência de marcas do mecanismo fica visível para Bento"
            )
        rows.append(
            {"id": name, "intent": beat["intent"], "exit": beat["exit_condition"], "beat": beat}
        )
    return rows


def game_for(case: dict[str, Any]) -> Any:
    fixture = next(row for row in baseline.fixtures() if row["id"] == "portal_attempt")
    fixture = copy.deepcopy(fixture)
    fixture["accepted"].append(
        "Após a tentativa, Iara ainda segura firme o mapa. Ela não o largou nem o colocou no chão."
    )
    fixture["facts"].update({"mapa": "seguro nas mãos de Iara", "runas": "oscilantes"})
    game = baseline.game_for(fixture, False)
    game.scene.zones = {fixture["now"]: []}
    assert game.roteiro is not None
    raw = case["beat"]
    game.roteiro.beat = RoteiroBeat(
        raw["beat_id"],
        raw["intent"],
        raw["expected_actors"],
        raw["expected_anchors"],
        raw["exit_condition"],
        raw["budget_turns"],
    )
    game.history.extend(
        [
            TurnRecord(
                3,
                "Player",
                "Continuo segurando o mapa. Não vou entregá-lo nem colocá-lo no chão.",
                "speech",
                deepcopy_scene(game.scene),
            ),
            TurnRecord(
                3,
                "C2",
                "Ainda não entendi esse mecanismo. Não sei como fechar o portal.",
                "speech",
                deepcopy_scene(game.scene),
            ),
        ]
    )
    return game


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "director_refusal.py",
        HERE / "DIRECTOR-COGNITION-PREREGISTRATION.md",
        HERE / "adversarial-reader-mapping.json",
        ROOT / "src/agents/narrator.py",
        ROOT / "src/roteiro.py",
        ROOT / "src/models.py",
        ROOT / "src/prompting.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
        ROOT / "plans/artifacts/69-beat-only-baseline/beat_only_baseline.py",
    ]
    mapping = json.loads((HERE / "adversarial-reader-mapping.json").read_text())
    paths.extend(HERE / "adversarial-runs" / mapping[label] for label in ("held-B", "held-C"))
    return {str(path.relative_to(ROOT)): baseline.digest(path) for path in paths}


director.definitions = definitions
director.game_for = game_for
director.hashes = hashes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(director.prepare() if parser.parse_args().command == "prepare" else director.run())
