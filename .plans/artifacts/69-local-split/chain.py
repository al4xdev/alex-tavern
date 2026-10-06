"""Separate physical operation contracts; deterministic lowering to authority API."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
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

from src.runner import Runner  # noqa: E402


def array(fields: list[str], description: str) -> dict:
    properties = {field: base.candidate.FIELDS[field] for field in fields}
    # Empty placeholders belong to the old flat wire contract, not these operations.
    properties = json.loads(json.dumps(properties))
    for value in properties.values():
        if "enum" in value:
            value["enum"] = [item for item in value["enum"] if item != ""]
    return {
        "type": "array",
        "description": description,
        "items": {
            "type": "object",
            "properties": properties,
            "required": fields,
            "additionalProperties": False,
        },
    }


CONTRACT = {
    "aperture_changes": array(
        ["target", "from_state", "to_state", "cause"],
        "New portal aperture changes in causal order. [] if no aperture changes. "
        "A failed crossing does not change aperture.",
    ),
    "attempt_results": array(
        ["target", "actor", "result"],
        "Results of all declared crossings, after 'aperture_changes'. "
        "[] if no crossing is declared for this turn.",
    ),
}
# Each operation includes only its relevant fields, with unconditional descriptions.
CONTRACT["aperture_changes"]["items"]["properties"]["from_state"]["description"] = (
    "Current aperture of 'target' before this change."
)
CONTRACT["aperture_changes"]["items"]["properties"]["to_state"]["description"] = (
    "New aperture of 'target' after this change; must differ from 'from_state'."
)
CONTRACT["aperture_changes"]["items"]["properties"]["cause"]["description"] = (
    "New witnessed cause changing 'target' now."
)
CONTRACT["attempt_results"]["items"]["properties"]["actor"]["description"] = (
    "Character making this declared crossing through 'target'."
)
CONTRACT["attempt_results"]["items"]["properties"]["result"]["description"] = (
    "'blocked' keeps 'actor' in place; 'crossed' completes the declared crossing "
    "through open 'target'."
)


class SplitRunner(base.candidate.AuthorityRunner):
    async def _call_narrator(
        self,
        game: Any,
        turn_number: int,
        forced_speaker: str | None = None,
        narrator_hint: str = "",
        **kwargs: Any,
    ) -> dict:
        context = list(kwargs.pop("extra_context", None) or [])
        context.extend(
            [
                "SOURCE FOR THIS BEAT (supported causes, not yet committed): "
                + json.dumps(
                    {"new_causes": {"value": base.CAUSES[turn_number]}}, ensure_ascii=False
                ),
                "PHYSICAL CONTRACT: committed_physical is already true; history may contain "
                "older states. Propose tracked changes ONLY in aperture_changes and crossings "
                "ONLY in attempt_results. Do not invent causes or attempts. Do not restage "
                "completed crossings. Preserve other events and audiences in perception_events. "
                "Parallel scene_update/zone_moves must agree.\ncommitted_physical: "
                + json.dumps(base.candidate.project(game, turn_number), ensure_ascii=False),
                "ADDITIONAL OUTPUT FIELD CONTRACT: " + json.dumps(CONTRACT, ensure_ascii=False),
            ]
        )
        properties = dict(kwargs.pop("extra_schema_properties", None) or {})
        properties.update(CONTRACT)
        required = [*(kwargs.pop("extra_schema_required", None) or []), *CONTRACT]
        raw = await Runner._call_narrator(
            self,
            game,
            turn_number,
            forced_speaker,
            narrator_hint,
            extra_context=context,
            extra_schema_properties=properties,
            extra_schema_required=required,
            **kwargs,
        )
        # Mechanical lowering of two non-overlapping operation types, no inference,
        # coercion, skipped operation, alternate old-format read or response repair.
        steps = []
        for kind, field in (
            ("aperture_change", "aperture_changes"),
            ("attempt_result", "attempt_results"),
        ):
            for operation in raw.pop(field):
                steps.append(
                    {
                        "kind": kind,
                        "target": "",
                        "actor": "",
                        "from_state": "",
                        "to_state": "",
                        "result": "",
                        "cause": "",
                        **operation,
                    }
                )
        raw["physical_steps"] = steps
        if not await self.review(
            "director", {"start": base.candidate.project(game, turn_number), "candidate": raw}
        ):
            raise base.candidate.TurnRejectedError("Director review refused candidate")
        return raw


old_hashes = base.hashes


def hashes() -> dict[str, str]:
    values = old_hashes()
    for path in (Path(__file__), HERE / "PREREGISTRATION.md"):
        values[str(path.relative_to(base.ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


base.HERE = HERE
base.LocalRunner = SplitRunner
base.hashes = hashes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run"))
    asyncio.run(base.prepare() if parser.parse_args().command == "prepare" else base.run())
