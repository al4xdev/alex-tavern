"""Retained local-chain control with textual field semantics added."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "local_chain", HERE.parent / "69-local-chain/chain.py"
)
assert spec and spec.loader
base: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OriginalRunner = base.LocalRunner


class DescribedRunner(OriginalRunner):
    async def _call_narrator(self, game: Any, turn_number: int, *args: Any, **kwargs: Any) -> dict:
        context = list(kwargs.pop("extra_context", None) or [])
        context.append(
            "ADDITIONAL OUTPUT FIELD CONTRACT (native grammar constrains shape; "
            "these descriptions define meaning): "
            + json.dumps({"physical_steps": base.candidate.STEPS_SCHEMA}, ensure_ascii=False)
        )
        return await super()._call_narrator(
            game, turn_number, *args, extra_context=context, **kwargs
        )


old_hashes = base.hashes


def hashes() -> dict[str, str]:
    import hashlib

    values = old_hashes()
    for path in (Path(__file__), HERE / "PREREGISTRATION.md"):
        values[str(path.relative_to(base.ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


# Reuse orchestration without editing or rescoring the frozen control.
base.HERE = HERE
base.LocalRunner = DescribedRunner
base.hashes = hashes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(base.prepare() if parser.parse_args().command == "prepare" else base.run())
