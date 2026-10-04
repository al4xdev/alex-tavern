"""Exercise retained full controls with the unchanged renderer-source reviewer."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT = HERE.parent / "69-renderer-source"
spec = importlib.util.spec_from_file_location("renderer_boundary", PARENT / "screen.py")
assert spec and spec.loader
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
base = boundary.base
OLD_HASHES = boundary.hashes


def hashes():
    result = OLD_HASHES()
    for path in [PARENT / "screen.py", PARENT / "manifest.json"]:
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


base.HERE = HERE
base.MANIFEST = HERE / "manifest.json"
base.hashes = hashes


async def prepare():
    assert not base.MANIFEST.exists(), "Preserve execution"
    previous = base.prior.read(PARENT / "manifest.json")
    retained = base.prior.read(HERE.parent / "69-reference-full-screen/manifest.json")
    old = {c["id"]: c for c in previous["cases"]}
    template = old["r1"]
    cases = []
    for original in retained["cases"]:
        cid = original["id"]
        case = {
            "id": cid,
            "candidate": original["candidate"],
            "source": copy.deepcopy(template["source"]),
            "expected_reject": cid not in ["r1", "r4"],
        }
        case["request"] = await base.capture(case)
        expected = copy.deepcopy(template["request"])
        expected["messages"][1]["content"] = case["request"]["messages"][1]["content"]
        assert case["request"] == expected, "Contract/settings/source enum drift"
        if cid in old:
            assert case == old[cid], "Retained boundary case changed"
        cases.append(case)
    admitted = copy.deepcopy(old["r9"])
    assert await base.capture(admitted) == admitted["request"]
    cases.append(admitted)
    assert len(cases) == 9
    for case in cases:
        prompt = str(case["request"]["messages"])
        assert not base.reviewer.base.operator_ontology_hits(prompt)
        assert "private-blue" not in prompt and "private-green" not in prompt
    jobs = [[c["id"], n] for n in range(1, 5) for c in cases]
    random.Random(479).shuffle(jobs)
    base.reviewer.write(base.MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print("Frozen 36 reviews; unchanged actual renderer source and reviewer contract", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else base.run())
