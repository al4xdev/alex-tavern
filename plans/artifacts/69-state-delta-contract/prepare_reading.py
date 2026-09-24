from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def main() -> None:
    os.environ["ROLEPLAY_DATA_DIR"] = tempfile.mkdtemp(prefix="tavern-delta-projection-")
    sys.path.insert(0, str(ROOT))
    from src.agents.narrator import _clean_fact_value
    from src.confidentiality import scene_fact_secret_tokens
    from src.models import dict_to_game_state
    from src.runner import Runner

    source = ROOT / "plans/artifacts/77-p3-input-dispatch/live/sessions/fb62cc2f"
    raw = (source / "state.json").read_bytes()
    state = json.loads(raw)
    state["scene"] = json.loads((OUT / "prior-scene.json").read_text())
    state["history"] = [record for record in state["history"] if record["turn_number"] < 4]
    game = dict_to_game_state(state)
    secret = scene_fact_secret_tokens(game.history, game.characters, game.scene)
    viewer = game.player.controlled_character_id
    names = {cid: ch.mind.name for cid, ch in game.characters.items()}
    story = ["# História anterior", "Ações declaradas são tentativas, não execução confirmada."]
    for record in state["history"]:
        kind = record["content_type"]
        if kind not in ("speech", "action", "narration"):
            continue
        speaker = viewer if record["speaker"] == "Player" else record["speaker"]
        if (
            record["audience"] is not None
            and viewer not in record["audience"]
            and speaker != viewer
        ):
            continue
        label = names.get(speaker, speaker)
        if kind == "action":
            label += " (tentativa)"
        story.append(record["content"] if kind == "narration" else label + ": " + record["content"])
    story += ["# Estado físico anterior", dump(game.scene.physical_facts)]
    literary = list(story)
    technical = list(story)
    technical += ["# Fontes anteriores; planos e tentativas não confirmam execução"]
    rows = [json.loads(line) for line in (source / "debug.jsonl").read_text().splitlines()]
    for number, row in enumerate(rows[:41], 1):
        if row.get("error") is None and row.get("response"):
            technical += [
                f"## Linha {number}, T{row.get('turn_number')}, {row.get('agent')}",
                str(row["response"]),
            ]
    technical += ["# Contexto do pedido atual", rows[41]["request"]["messages"][1]["content"]]
    files = sorted((OUT / "runs").glob("*.result.json"))
    assert len(files) == 8
    random.Random(404921).shuffle(files)
    key = {}
    projections = {}
    runner = Runner.__new__(Runner)
    for index, path in enumerate(files, 1):
        label = f"V{index}"
        key[label] = path.name
        result = json.loads(path.read_text())
        literary += [f"# Alternativa {label}"]
        technical += [f"# Alternativa {label}"]
        if not result.get("schema_valid"):
            literary.append("Resposta inelegível: não constitui continuação executada.")
            technical.append(dump({"error": result.get("error"), "parsed": result.get("parsed")}))
            projections[label] = {"eligible": False}
            continue
        parsed = result["parsed"]
        projected = copy.deepcopy(game)
        raw_delta = parsed["scene_update"]
        clean_delta = (
            {key: _clean_fact_value(value, secret) for key, value in raw_delta.items()}
            if raw_delta is not None
            else None
        )
        runner._update_scene(projected, clean_delta)
        projection = {
            "eligible": True,
            "raw_delta": raw_delta,
            "normalized_delta": clean_delta,
            "resulting_facts": projected.scene.physical_facts,
            "resulting_location": projected.scene.location,
            "unapplied_non_null_values": {
                key: value
                for key, value in (clean_delta or {}).items()
                if key not in ("location", "time_of_day")
                and value is not None
                and projected.scene.physical_facts.get(key) != value
            },
        }
        projections[label] = projection
        literary.append("Acontecimentos propostos para este turno, ainda não persistidos:")
        for event in parsed["perception_events"]:
            if viewer in event["witness_ids"]:
                literary.append(event["content"])
        if parsed.get("time_skip_summary"):
            literary.append("Passagem de tempo: " + str(parsed["time_skip_summary"]))
        literary += [
            "Estado físico após aplicar a atualização:",
            dump(projection["resulting_facts"]),
        ]
        technical += [dump(parsed), "Projeção pelo Runner:", dump(projection)]
    for name, content in (("reader.md", literary), ("source-reader.md", technical)):
        with (OUT / name).open("x") as stream:
            stream.write("\n\n".join(content) + "\n")
    (OUT / "reading-key.json").write_text(dump(key))
    (OUT / "projections.json").write_text(dump(projections))
    (OUT / "projection-source.json").write_text(
        dump(
            {
                "state_sha256": hashlib.sha256(raw).hexdigest(),
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        )
    )
    print("Saved eight opaque alternatives and actual Runner state projections")


if __name__ == "__main__":
    main()
