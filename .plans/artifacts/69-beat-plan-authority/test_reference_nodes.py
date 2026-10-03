"""Citation provenance controls, without model or real-data access."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "node_diagnostic", HERE / "speech_extraction_references_v2.py"
)
assert spec and spec.loader
module: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture() -> dict[str, Any]:
    manifest = json.loads((HERE / "speech-extraction-v2-manifest.json").read_text())
    return copy.deepcopy(
        next(
            c
            for c in manifest["calls"]
            if c["case"] == "npc_owned_positive" and c["arm"] == "manual"
        )
    )


def result(reference: str) -> dict[str, Any]:
    return {
        "valid": True,
        "output": {
            "decisions": [
                {
                    "act_index": 0,
                    "support": "prospective_only",
                    "evidence_paths": ["/candidate/speech_proposals/0/text"],
                    "reason": "Prospective proposal.",
                },
                {
                    "act_index": 1,
                    "support": "realized_speech",
                    "evidence_paths": [reference],
                    "reason": "Claimed completed speech.",
                },
            ]
        },
    }


def test_actual_speech_collection_is_an_existing_evidence_node() -> None:
    row = fixture()
    reference = "/completed_actor_content/1/actual_spoken_words"
    assert module.nodes(row["input"])[reference] == ["O encaixe fica ao lado do arco."]
    graded = module.grade(row, result(reference))
    assert graded["citations_exist"] and graded["positive_reference_outside_claim"]
    assert graded["matches_label"]


def test_candidate_parent_does_not_prove_its_own_claim() -> None:
    graded = module.grade(fixture(), result("/candidate"))
    assert graded["citations_exist"]
    assert not graded["positive_reference_outside_claim"]
    assert not graded["matches_label"]


def test_empty_actual_speech_collection_exists_as_absence_evidence() -> None:
    row = fixture()
    row["input"]["completed_actor_content"][1]["actual_spoken_words"] = []
    assert module.nodes(row["input"])["/completed_actor_content/1/actual_spoken_words"] == []
