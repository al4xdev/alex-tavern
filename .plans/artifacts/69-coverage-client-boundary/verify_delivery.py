"""Recapture two persisted Runner submissions and check measured request parity."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / ".plans/artifacts/69-runner-anchor-coverage/screen.py"
LABEL = "Beat elements awaiting coverage:"


async def verify() -> None:
    spec = importlib.util.spec_from_file_location("coverage_delivery_fixture", SOURCE)
    assert spec is not None and spec.loader is not None
    fixture: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    # Reuse its controlled Runner topology; keep the historical script intact.
    delivery = HERE / "delivery"
    delivery.mkdir()
    fixture.HERE = delivery
    fixture.MANIFEST = delivery / "manifest.json"
    fixture.OLD = LABEL
    fixture.NEW = LABEL
    paths = [ROOT / "src/roteiro.py", SOURCE, Path(__file__)]
    fixture.hashes = lambda: {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
    }
    await fixture.prepare()
    produced = json.loads(fixture.MANIFEST.read_text())
    measured = json.loads((HERE / "manifest.json").read_text())
    for index in (1, 2):
        case_id = f"submission{index}-coverage"
        actual = next(c for c in produced["cases"] if c["fixture"]["id"] == case_id)
        expected = next(c for c in measured["cases"] if c["fixture"]["id"] == case_id)
        assert actual["request"] == expected["request"], case_id
    assert [s["revision"] for s in produced["snapshots"]] == [0, 1, 2]
    print("Delivered builder matches both measured candidate requests after persisted submissions")


if __name__ == "__main__":
    asyncio.run(verify())
