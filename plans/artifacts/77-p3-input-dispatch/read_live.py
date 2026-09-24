from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
outcome = json.loads((BASE / "live/outcome.json").read_text())
source = BASE / "live/sessions" / outcome["session_id"] / "state.json"
raw = source.read_bytes()
state = json.loads(raw)
names = {cid: character["mind"]["name"] for cid, character in state["characters"].items()}
viewer = state["player"]["controlled_character_id"]
lines = ["# História\n\nAs ações declaradas são tentativas; a narração mostra o que acontece."]
for record in state["history"]:
    kind = record["content_type"]
    if kind not in ("speech", "action", "narration"):
        continue
    speaker = viewer if record["speaker"] == "Player" else record["speaker"]
    if record["audience"] is not None and viewer not in record["audience"] and speaker != viewer:
        continue
    label = names.get(speaker, speaker)
    if kind == "action":
        label += " (tentativa de ação)"
    lines.append(record["content"] if kind == "narration" else label + ": " + record["content"])
reader = BASE / "live-reader.md"
with reader.open("x") as stream:
    stream.write("\n\n".join(lines) + "\n")
(BASE / "live-reader-source.json").write_text(
    json.dumps(
        {
            "source": str(source.relative_to(BASE)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "viewer": viewer,
            "projection_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        indent=2,
    )
    + "\n"
)
print("Saved viewer-visible fiction")
