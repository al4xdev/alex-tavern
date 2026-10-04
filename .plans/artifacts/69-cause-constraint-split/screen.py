"""Isolate source-role separation without replacing retained narration or schema rules."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/alex/git/my/alex-tavern")
PARENT = ROOT / ".plans/artifacts/69-reference-full-screen"
spec = importlib.util.spec_from_file_location("full_refs", PARENT / "screen.py")
assert spec and spec.loader
full = importlib.util.module_from_spec(spec)
spec.loader.exec_module(full)
base = full.base
OLD_HASHES = full.hashes
CAUSE = (
    "Bento retira a barra do portal azul e puxa a folha azul até abrir "
    "completamente a passagem. Sua intervenção é suficiente."
)
CONSTRAINTS = [
    "Não há nova ventania neste turno: nenhuma rajada forte que empurre pessoas, "
    "objetos ou folhas de portal.",
    "O ar pode circular fracamente, sem essa força nem mudança de abertura ou deslocamento.",
    "Não há outra causa de mudança de abertura de qualquer portal.",
]
DESCRIPTION = "Constraints for 'current_beat.turn_number', not new causal events."


def split(source):
    result = copy.deepcopy(source)
    supported = result["supported_this_beat"]
    assert supported["new_causes"]["value"] == " ".join([CAUSE, *CONSTRAINTS])
    supported["new_causes"]["value"] = CAUSE
    supported["world_constraints"] = {"description": DESCRIPTION, "value": CONSTRAINTS.copy()}
    restored = copy.deepcopy(result)
    moved = restored["supported_this_beat"].pop("world_constraints")["value"]
    restored["supported_this_beat"]["new_causes"]["value"] = " ".join([CAUSE, *moved])
    assert json.dumps(restored, ensure_ascii=False) == json.dumps(source, ensure_ascii=False)
    return result


def hashes():
    result = OLD_HASHES()
    for path in [PARENT / "screen.py", PARENT / "manifest.json"]:
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


base.HERE = HERE
base.MANIFEST = HERE / "manifest.json"
base.hashes = hashes


async def prepare():
    assert not base.MANIFEST.exists()
    protocol = (HERE / "PREREGISTRATION.md").read_text()
    assert CAUSE in protocol and DESCRIPTION in protocol and all(c in protocol for c in CONSTRAINTS)
    previous = base.prior.read(PARENT / "manifest.json")
    cases = [copy.deepcopy(c) for c in previous["cases"] if c["id"] in ["r1", "r5", "r6", "r8"]]
    for case in cases:
        assert await base.capture(case) == case["request"], "Prior builder drift"
        original = copy.deepcopy(case["source"])
        old_schema = base.schema(original)
        case["source"] = split(original)
        new_schema = base.schema(case["source"])
        modified = copy.deepcopy(old_schema)
        modified["schema"]["properties"]["issues"]["items"]["properties"]["source_refs"]["items"][
            "enum"
        ] = list(base.nodes(case["source"]))
        assert modified == new_schema, "Change beyond source-reference enum"
        request = await base.capture(case)
        expected = copy.deepcopy(case["request"])

        def encode(value):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

        content = expected["messages"][0]["content"]
        assert content.count(encode(old_schema["schema"])) == 1
        expected["messages"][0]["content"] = content.replace(
            encode(old_schema["schema"]), encode(new_schema["schema"])
        )
        payload = json.loads(expected["messages"][1]["content"])
        payload["source"] = case["source"]
        expected["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
        assert expected == request, "Change beyond source representation and reference enum"
        case["original_source"] = original
        case["request"] = request
        assert not base.reviewer.base.operator_ontology_hits(str(request["messages"]))
    jobs = [[c["id"], n] for n in range(1, 5) for c in cases]
    random.Random(439).shuffle(jobs)
    base.reviewer.write(base.MANIFEST, {"hashes": hashes(), "cases": cases, "jobs": jobs})
    print(
        "Frozen 16 reviews; source reconstruction and exact request intervention checked",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else base.run())
