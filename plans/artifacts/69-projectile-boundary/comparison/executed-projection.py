import hashlib
import json
import random
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[2]
manifest = json.loads((base / "manifest.json").read_text())
case = manifest["cases"][0]
source = (root / case["source"]).with_name("state.json")
state = json.loads(source.read_text())
names = {key: value["mind"]["name"] for key, value in state["characters"].items()}
viewer = state["player"]["controlled_character_id"]
lines = ["# Trecho anterior"]
for record in state["history"]:
    if not 27 <= record["turn_number"] < 32:
        continue
    if record["content_type"] not in ("narration", "speech", "action"):
        continue
    if (
        record["audience"] is not None
        and viewer not in record["audience"]
        and record["speaker"] != viewer
    ):
        continue
    speaker = viewer if record["speaker"] == "Player" else record["speaker"]
    name = names.get(speaker, speaker)
    if record["content_type"] == "action":
        name += " (tentativa de ação)"
    lines.append(
        record["content"]
        if record["content_type"] == "narration"
        else name + ": " + record["content"]
    )
lines.append("# Continuações independentes\nCada alternativa continua o trecho anterior.")
paths = sorted((base / "runs").glob("*.result.json"))
assert len(paths) == 8
random.Random(693106).shuffle(paths)
out = base / "comparison"
out.mkdir(exist_ok=False)
key = {}
for index, path in enumerate(paths, 1):
    label = f"V{index}"
    key[label] = str(path.relative_to(base))
    row = json.loads(path.read_text())
    lines.append("## " + label)
    parsed = row.get("parsed")
    if parsed is not None:
        lines.append(parsed["narration"])
    else:
        if row.get("response", {}).get("choices"):
            raise ValueError("Returned invalid model text requires explicit projection review")
        lines.append("(Continuação indisponível.)")
(out / "reader.md").write_text("\n\n".join(lines) + "\n")
(out / "key.json").write_text(json.dumps(key, indent=2) + "\n")
(out / "executed-projection.py").write_bytes(Path(__file__).read_bytes())
(out / "source.json").write_text(
    json.dumps(
        {
            "source": str(source.relative_to(root)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "context_turns": [27, 31],
            "shuffle_seed": 693106,
        },
        indent=2,
    )
    + "\n"
)
print("Saved opaque prose packet and separate key")
