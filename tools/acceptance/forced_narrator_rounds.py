"""Task 28's real-LLM acceptance protocol, run end to end for the first time.

The task specified it precisely and closed with every line unchecked:

  - a real conversation with MORE THAN FOUR characters present (five or more
    including the human-controlled one);
  - at least four consecutive rounds forcing `Narrator` and never an NPC;
  - every round produces Narrator output only, even when the raw model response
    picks an NPC - no Character call, no Character response;
  - for every round `debug.jsonl` shows `force_speaker: "Narrator"` in
    `turn_input` and `effective_force_speaker: "Narrator"` in
    `turn_input_effective`;
  - the skip-turn variant proves the same routing with no player content.

The cast comes from the xfailed3 fixture, which is the only nine-character
scenario in the repository - the two-character defaults cannot exercise a rule
about the Director preferring an NPC.

Why a live run and not another unit test: the unit tests force the Director's
answer, so they prove the runner ignores an NPC it was handed. They cannot show
how often a real Director actually tries, which is the risk the regression was
about. This script reports that count instead of assuming it.

Usage: python -m tools.acceptance.forced_narrator_rounds [base_url]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8903"
ROUNDS = 4
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{' | ' + detail if detail else ''}")
    if not ok:
        failures.append(f"{label} — {detail}")


fixture = json.loads(Path("tests/fixtures/xfailed3_counter_canon.json").read_text(encoding="utf-8"))
session_config = fixture["session_config"]
cast_size = len(session_config["characters"])

with httpx.Client(base_url=BASE, timeout=600) as client:
    token = client.get("/bootstrap").json()["access_token"]
    client.headers["x-tavern-token"] = token
    client.headers["Origin"] = BASE

    config = client.get("/config").json()
    # One beat per turn: the burst would add turns nobody forced, and the
    # criterion is about consecutive FORCED rounds.
    config["autonomous_burst_max_beats"] = 1
    client.put("/config", json=config)
    print(f"provider={config['active_provider']} cast={cast_size}")

    check("more than four characters present", cast_size > 4, f"{cast_size} characters")

    started = client.post(
        "/session/start",
        json={
            "characters": session_config["characters"],
            "scene": session_config["scene"],
            "controlled_character_id": session_config["controlled_character_id"],
            "narrator_directives": fixture.get("narrator_directives", ""),
        },
    ).json()
    sid = started["session_id"]
    print(f"session {sid}")

    speeches = [
        "Que todos fiquem onde estao. Vou registrar o que vejo.",
        "Continuo observando a sala sem falar com ninguem.",
        "Espero. Deixo o silencio trabalhar.",
        "Anoto a posicao de cada pessoa.",
    ]
    rounds: list[dict] = []
    for index in range(ROUNDS):
        response = client.post(
            f"/session/{sid}/turn",
            json={"speech": speeches[index], "force_speaker": "Narrator"},
        ).json()
        rounds.append(response)
        print(
            f"  round {index + 1}: next_speakers={response.get('next_speakers')} "
            f"responses={len(response.get('character_responses') or [])}"
        )

    # The skip variant: same routing, no player content at all.
    skipped = client.post(
        f"/session/{sid}/turn", json={"skip": True, "force_speaker": "Narrator"}
    ).json()
    print(f"  skip round: next_speakers={skipped.get('next_speakers')}")

    every = [*rounds, skipped]
    check(
        "every forced round routed to the Narrator",
        all(r.get("next_speakers") == ["Narrator"] for r in every),
        str([r.get("next_speakers") for r in every]),
    )
    check(
        "no character response in any forced round",
        all(not (r.get("character_responses") or []) for r in every),
        str([len(r.get("character_responses") or []) for r in every]),
    )
    check(
        "every forced round still produced narration",
        all((r.get("narration") or "").strip() for r in every),
        str([len(r.get("narration") or "") for r in every]),
    )

    state = client.get(f"/session/{sid}/state").json()

# The debug log is the evidence the task asked for by name.
debug_path = Path(".data/sessions") / sid / "debug.jsonl"
records = [
    json.loads(line)
    for line in debug_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if line.strip()
]

forced_turns = {
    record["turn_number"]
    for record in records
    if record.get("agent") == "turn_input"
    and (record.get("input") or {}).get("force_speaker") == "Narrator"
}
effective = {
    record["turn_number"]
    for record in records
    if record.get("agent") == "turn_input_effective"
    # Top-level, not inside `input`: the effective speaker is what the runner
    # DECIDED, so it is logged beside the request rather than within it.
    and record.get("effective_force_speaker") == "Narrator"
}
check(
    "turn_input records force_speaker=Narrator for every round",
    len(forced_turns) == len(every),
    f"{len(forced_turns)} of {len(every)}",
)
check(
    "turn_input_effective records effective_force_speaker=Narrator for every round",
    effective == forced_turns,
    f"{sorted(effective)} vs {sorted(forced_turns)}",
)

character_calls = [
    record
    for record in records
    if (record.get("agent") or "").startswith("character:")
    and record.get("turn_number") in forced_turns
]
check(
    "no Character call was made in any forced round",
    not character_calls,
    str([(r["turn_number"], r["agent"]) for r in character_calls]),
)

# What the unit tests cannot report: how often the real Director tried anyway.
attempted = 0
for record in records:
    if record.get("agent") != "director" or record.get("turn_number") not in forced_turns:
        continue
    raw = json.dumps(record.get("response"), ensure_ascii=False)
    if any(f'"{cid}"' in raw for cid in session_config["characters"]):
        attempted += 1
print(f"\n  (o Diretor propos um NPC mesmo forcado em {attempted}/{len(forced_turns)} rodadas)")

# Forcing the Narrator forces WHO ACTS, not silence in the fiction. A forced
# round can still persist NPC-attributed speech, because the Director may stage
# audible speech in its own narration - that is the audible_speech persistence
# WT-09 depends on, and it carries an `audience_origin`. What must not appear is
# speech produced by a Character CALL, which is what the task forbids.
npc_records = [
    record
    for record in state["history"]
    if record["turn_number"] in forced_turns
    and record["content_type"] != "narration"
    and record["speaker"] != "Player"
]
unstaged = [record for record in npc_records if not record.get("audience_origin")]
check(
    "every NPC line in a forced round was staged by the Director, not a Character call",
    not unstaged,
    f"{len(unstaged)} unstaged of {len(npc_records)} NPC records",
)
print(
    f"  (o Diretor encenou {len(npc_records)} falas de NPC nas rodadas forcadas, "
    "todas via audible_speech)"
)

print()
if failures:
    print(f"{len(failures)} FALHA(S):")
    for item in failures:
        print("  -", item)
    raise SystemExit(1)
print(f"protocolo da task 28 cumprido: {len(every)} rodadas forcadas, elenco de {cast_size}")
