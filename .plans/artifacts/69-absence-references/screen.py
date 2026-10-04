"""Repeat the isolated screen with an explicit admitted-event citation obligation."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/alex/git/my/alex-tavern")
PARENT = ROOT / ".plans/artifacts/69-source-references"
spec = importlib.util.spec_from_file_location("reference_screen", PARENT / "screen.py")
assert spec and spec.loader
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OLD_SCHEMA = base.schema
OLD_HASHES = base.hashes
REF_DESCRIPTION = (
    "JSON pointers relative to 'source' establishing 'kind'; values are "
    "resolved from 'source'. For 'unsupported_transition', include "
    "'/confirmed_events' or its containing source root ''. Context references may "
    "support other premises, but cannot replace that collection for this absence."
)
DETAIL_DESCRIPTION = (
    "Explain 'kind' using the facts at 'source_refs'. Distinguish the absence "
    "of an admitted event in 'confirmed_events' from the absence of a cause in "
    "'supported_this_beat'. Do not attribute one field's contents to another."
)


def schema(source):
    result = OLD_SCHEMA(source)
    fields = result["schema"]["properties"]["issues"]["items"]["properties"]
    fields["source_refs"]["description"] = REF_DESCRIPTION
    fields["detail"]["description"] = DETAIL_DESCRIPTION
    return result


def hashes():
    result = OLD_HASHES()
    result[str(PARENT / "screen.py")] = hashlib.sha256(
        (PARENT / "screen.py").read_bytes()
    ).hexdigest()
    result[str(PARENT / "manifest.json")] = hashlib.sha256(
        (PARENT / "manifest.json").read_bytes()
    ).hexdigest()
    return result


base.HERE = HERE
base.MANIFEST = HERE / "manifest.json"
base.schema = schema
base.hashes = hashes


async def prepare():
    protocol = (HERE / "PREREGISTRATION.md").read_text()
    assert REF_DESCRIPTION in protocol.replace("\n", " ")
    assert DETAIL_DESCRIPTION in protocol.replace("\n", " ")
    await base.prepare()
    manifest = base.prior.read(base.MANIFEST)
    previous = base.prior.read(PARENT / "manifest.json")
    old_cases = {case["id"]: case for case in previous["cases"]}
    for case in manifest["cases"]:
        expected = copy.deepcopy(old_cases[case["id"]]["request"])
        old_fields = OLD_SCHEMA(case["source"])["schema"]["properties"]["issues"]["items"][
            "properties"
        ]
        content = expected["messages"][0]["content"]
        for name, replacement in [("source_refs", REF_DESCRIPTION), ("detail", DETAIL_DESCRIPTION)]:
            original = old_fields[name]["description"]
            assert content.count(original) == 1
            content = content.replace(original, replacement)
        expected["messages"][0]["content"] = content
        assert case["request"] == expected, "Change beyond two field descriptions"
    print("Only two schema descriptions differ from retained reference requests", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "run"])
    asyncio.run(prepare() if parser.parse_args().operation == "prepare" else base.run())
