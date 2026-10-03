"""Compare coverage-label wording on controlled temporal and agency cases."""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / ".plans/artifacts/69-production-reasoning/screen.py"
PRIOR = ROOT / ".plans/artifacts/69-descriptions-applied/manifest.json"
spec = importlib.util.spec_from_file_location("coverage_shared", BASE)
assert spec is not None and spec.loader is not None
production: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(production)
baseline = production.baseline
MANIFEST = HERE / "manifest.json"


def hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        HERE / "PREREGISTRATION.md",
        BASE,
        PRIOR,
        ROOT / "src/roteiro.py",
        ROOT / "src/llm/client.py",
        ROOT / "src/llm/adapters/deepseek.py",
    ]
    return {str(p.relative_to(ROOT)): baseline.digest(p) for p in paths}


async def prepare() -> None:
    if MANIFEST.exists():
        raise RuntimeError("Preserve manifest")
    prior = json.loads(PRIOR.read_text())
    fixtures = [
        copy.deepcopy(c["fixture"])
        for c in prior["cases"]
        if c["fixture"]["id"] in ("portal_attempt-descriptive", "portal_left-descriptive")
    ]
    for f in fixtures:
        f["id"] = f["id"].removesuffix("-descriptive")
    common = {"before": "Pátio", "now": "Pátio", "question": "O que está acontecendo agora?"}
    fixtures.extend(
        [
            {
                **common,
                "id": "gate_reversed",
                "premise": (
                    "Iara e Bento precisam manter a grade fechada para proteger o pátio, "
                    "depois buscar ajuda."
                ),
                "act": "Manter a grade fechada bloqueando o acesso ao pátio.",
                "act_exit": "No estado atual, a grade está fechada e bloqueia o acesso ao pátio.",
                "next_act": "Buscar ajuda para o pátio.",
                "intent": "A grade desce e o guincho se trava.",
                "anchors": ["grade", "guincho"],
                "accepted": [
                    "Iara baixou a grade e travou o guincho.",
                    (
                        "Depois uma carga de cerco explodiu: a grade saiu dos trilhos. "
                        "Agora o acesso ao pátio está aberto e sem bloqueio."
                    ),
                ],
                "facts": {"grade": "fora dos trilhos", "acesso": "aberto e sem bloqueio"},
                "required_act_completed": False,
            },
            {
                **common,
                "before": "Enfermaria",
                "now": "Enfermaria",
                "id": "antidote_secured",
                "premise": (
                    "Iara e Bento devem obter o antídoto e então lidar com a pessoa envenenada."
                ),
                "act": "Obter o frasco de antídoto.",
                "act_exit": "O frasco de antídoto foi obtido e está em posse de Iara.",
                "next_act": (
                    "Lidar com a pessoa envenenada sem escolher por Iara ou Bento "
                    "se o antídoto será usado."
                ),
                "intent": "O antídoto é apresentado enquanto o veneno avança.",
                "anchors": ["frasco de antídoto", "veneno"],
                "accepted": [
                    (
                        "O boticário colocou o frasco de antídoto na mesa. "
                        "Iara pegou o frasco; agora o segura lacrado."
                    ),
                    (
                        "O veneno faz uma pessoa convulsionar na maca. "
                        "Iara e Bento continuam parados. Ninguém abriu nem administrou "
                        "o antídoto, nem decidiu fazê-lo."
                    ),
                ],
                "facts": {"frasco": "lacrado em posse de Iara", "antidoto": "não administrado"},
                "required_act_completed": True,
            },
        ]
    )
    cfg = baseline.config()
    cases = []
    for f in fixtures:
        early, late = baseline.game_for(f, False), baseline.game_for(f, True)
        first = baseline.evaluate_roteiro(early.roteiro, early.history, "C1", 3)
        decision = (
            first
            if first.action
            else baseline.evaluate_roteiro(late.roteiro, late.history, "C1", 4)
        )
        assert decision.reason == "coverage_complete", (f["id"], decision)
        game = early if first.action else late
        request = await production.captured_request(game, decision.reason, cfg)
        for arm in ("control", "coverage"):
            selected = copy.deepcopy(request)
            if arm == "coverage":
                text = selected["messages"][1]["content"]
                old = "STATUS: The current beat COMPLETED (its actors and anchors all landed)."
                assert text.count(old) == 1
                selected["messages"][1]["content"] = text.replace(
                    old,
                    (
                        "STATUS: Previous beat coverage: "
                        "its expected actors and anchors were observed."
                    ),
                )
            fixture = copy.deepcopy(f)
            fixture["id"] += "-" + arm
            cases.append(
                {
                    "fixture": fixture,
                    "arm": arm,
                    "request": selected,
                    "schema": baseline.build_next_beat_schema("beat")["schema"],
                }
            )
    baseline.write(MANIFEST, {"hashes": hashes(), "cases": cases})
    print("Frozen four paired fixtures, four repetitions: 32 curls")


async def run() -> None:
    production.HERE = HERE
    production.MANIFEST = MANIFEST
    production.hashes = hashes
    await production.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(prepare() if parser.parse_args().command == "prepare" else run())
