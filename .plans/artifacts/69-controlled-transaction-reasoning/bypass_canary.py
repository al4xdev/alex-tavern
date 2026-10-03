"""Reproduce the mechanical validator's untyped narrative bypass."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transaction_bypass_fixture", HERE / "screen.py")
assert spec is not None and spec.loader is not None
screen: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)

fixture = screen.fixtures()[0]
source = HERE / "runs/submission1-high-1.result.json"
output = copy.deepcopy(json.loads(source.read_text())["output"])
output["steps"].append(
    {
        **dict.fromkeys(screen.FIELDS, ""),
        "kind": "other",
        "text": "O portal azul se abre e Téo atravessa para o túnel.",
    }
)
final = screen.mechanical(fixture, output)
assert final["apertures"]["portal azul"] == "closed"
assert final["positions"]["Téo"] == "salão"
screen.transport.write(
    HERE / "untyped-bypass-canary.json",
    {
        "synthetic_fault_injection": True,
        "source_fixture": fixture,
        "original_model_result": "submission1-high-1",
        "mutated_output": output,
        "mechanical_accepted": True,
        "mechanical_final_state": final,
        "literal_untyped_claim": output["steps"][-1]["text"],
    },
)
print("Synthetic text claims opening/crossing; validator accepts held closed/hall state")
