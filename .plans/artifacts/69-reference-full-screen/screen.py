"""Exercise all retained conditions with the unchanged absence-reference contract."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/alex/git/my/alex-tavern")
PARENT = ROOT / ".plans/artifacts/69-absence-references"
spec = importlib.util.spec_from_file_location("absence_screen", PARENT / "screen.py")
assert spec and spec.loader
absence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(absence)
base = absence.base
OLD_HASHES = absence.hashes


def hashes():
    result = OLD_HASHES()
    for path in [PARENT / "screen.py", PARENT / "manifest.json"]:
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


base.HERE = HERE
base.MANIFEST = HERE / "manifest.json"
base.hashes = hashes


async def prepare():
    assert not base.MANIFEST.exists(), "Preserve frozen execution"
    retained = base.prior.read(base.PARENT / "manifest.json")
    isolated = base.prior.read(PARENT / "manifest.json")
    previous = {case["id"]: case for case in isolated["cases"]}
    template = previous["r1"]
    cases = copy.deepcopy(retained["cases"])
    assert len(cases) == 8
    for case in cases:
        assert case["source"] == template["source"], "Full source changed"
        request = await base.capture(case)
        expected = copy.deepcopy(template["request"])
        expected["messages"][1] = case["request"]["messages"][1]
        assert request == expected, "Builder/contract/settings drift"
        if case["id"] in previous:
            assert request == previous[case["id"]]["request"]
        case["request"] = request
        prompt = str(request["messages"])
        assert not base.reviewer.base.operator_ontology_hits(prompt)
        assert "private-blue" not in prompt and "private-green" not in prompt
    jobs = [[case["id"], repeat] for repeat in range(1, 5) for case in cases]
    random.Random(401).shuffle(jobs)
    base.reviewer.write(base.MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print("Frozen 32 reviews; unchanged contract/source/settings; isolated body parity", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else base.run())
