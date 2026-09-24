import argparse
import hashlib
import json
import random
import re
from pathlib import Path

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("case", choices=("evacuation", "roof"))
args = parser.parse_args()
base = root / "plans/artifacts/69-anchor-heading-replay"
out = base / ("reading-" + args.case)
out.mkdir(exist_ok=False)
manifest = json.loads((base / "manifest.json").read_text())
case = next(c for c in manifest["cases"] if c["label"] == args.case)
source = (root / case["source"]).with_name("state.json")
state = json.loads(source.read_text())
names = {cid: value["mind"]["name"] for cid, value in state["characters"].items()}
cid = state["player"]["controlled_character_id"]
context = ["# Trecho anterior\n\nHistória em andamento."]
for record in state["history"]:
    if not case["turn_number"] - 5 <= record["turn_number"] < case["turn_number"]:
        continue
    if record["content_type"] not in ("speech", "action", "narration"):
        continue
    if (
        record["audience"] is not None
        and cid not in record["audience"]
        and record["speaker"] != cid
    ):
        continue
    speaker = cid if record["speaker"] == "Player" else record["speaker"]
    label = names.get(speaker, speaker)
    if record["content_type"] == "action":
        label += " (tentativa de ação)"
    context.append(
        record["content"]
        if record["content_type"] == "narration"
        else label + ": " + record["content"]
    )


def canonical(text):
    return re.sub(r"\bC\d+\b", lambda match: names[match.group()], str(text))


paths = sorted((base / "runs-recharged").glob(args.case + "-*.result.json"))
assert len(paths) == 8
random.Random(691106).shuffle(paths)
key = {f"V{i + 1}": str(path.relative_to(base)) for i, path in enumerate(paths)}
assert not (out / "reader-key.json").exists()
(out / "reader-key.json").write_text(json.dumps(key, indent=2) + "\n")
lines = context + [
    "# Continuações independentes\n\nCada alternativa abaixo retoma o final do trecho anterior. "
    "São acontecimentos e descrições de situação propostos para a história, ainda sem a redação "
    "final da narração nem as falas posteriores. As alternativas não são uma sequência entre si."
]
blind = []
for label, path in zip(key, paths, strict=True):
    row = json.loads(path.read_text())
    parsed = row.get("parsed")
    blind.append(
        {
            "label": label,
            "schema_valid": row.get("schema_valid", False),
            "output": parsed,
            "error": row.get("error"),
        }
    )
    lines.append("## " + label)
    if parsed is None:
        lines.append("(Continuação indisponível.)")
        continue
    block = parsed["scene_blocking"]
    lines.append(
        "Posições descritas (o trecho não marca explicitamente se são anteriores ou posteriores "
        "aos acontecimentos abaixo):"
    )
    lines.extend(names[c] + ": " + canonical(v) for c, v in block["character_zones"].items())
    lines.append("Local da ação: " + canonical(block["action_location"]))
    lines.extend(canonical(v) for v in block["spatial_constraints"])
    if "destination_reachable_this_beat" in block:
        lines.append(
            "O destino é alcançável neste momento: "
            + ("sim" if block["destination_reachable_this_beat"] else "não")
        )
    else:
        lines.append("Não foi informado se o destino é alcançável neste momento.")
    lines.append("Acontecimentos:")
    lines.extend(canonical(e["content"]) for e in parsed["perception_events"])
    if parsed["time_skip_summary"]:
        lines.append("Com a passagem do tempo: " + canonical(parsed["time_skip_summary"]))
    if parsed["scene_update"]:
        lines.append("Situação resultante:")
        lines.extend(
            k.replace("_", " ") + ": " + canonical(v) for k, v in parsed["scene_update"].items()
        )
    if parsed["zone_moves"]:
        lines.append("Destinos dos deslocamentos:")
        lines.extend(names[c] + ": " + canonical(v) for c, v in parsed["zone_moves"].items())
(out / "reader.md").write_text("\n\n".join(lines) + "\n")
(out / "blind-outputs.json").write_text(json.dumps(blind, ensure_ascii=False, indent=2) + "\n")
print("Saved literary packet and opaque full-output dossier. Labels remain in the separate key.")

(out / "provenance.json").write_text(json.dumps({
    "state_source": str(source.relative_to(root)),
    "state_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "context_turns": [case["turn_number"] - 5, case["turn_number"] - 1],
    "shuffle_seed": 691106,
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}, indent=2) + "\n")
