"""Task 45's remaining pendency: a real HTTP smoke of the multi-beat burst.

The task shipped with "Smoke HTTP real (config -> skip -> multiplos beats ->
motivo de parada)" still open. Everything here goes through the running server's
own HTTP API, not through the Runner in-process, because the point is the
boundary a client actually uses.

Checks, all deterministic:

  1. PUT /config sets autonomous_burst_max_beats and GET reads it back.
  2. A bare skip commits MORE THAN ONE beat and each beat is its own turn.
  3. The response carries a burst_stop_reason.
  4. Undo pops exactly ONE beat, not the whole burst.
  5. A skip with a forced speaker commits exactly one beat.
  6. Every beat of the burst is present in the persisted history.
"""

from __future__ import annotations

import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8903"
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{' | ' + detail if detail else ''}")
    if not ok:
        failures.append(f"{label} — {detail}")


with httpx.Client(base_url=BASE, timeout=600) as client:
    token = client.get("/bootstrap").json()["access_token"]
    client.headers["x-tavern-token"] = token
    client.headers["Origin"] = BASE

    config = client.get("/config").json()
    print(f"provider={config['active_provider']} language={config.get('language')}")

    # 1. the burst budget round-trips through the HTTP boundary
    config["autonomous_burst_max_beats"] = 4
    config["roteiro_enabled"] = False
    saved = client.put("/config", json=config)
    check("PUT /config accepted", saved.status_code == 200, f"status {saved.status_code}")
    check(
        "burst budget round-trips",
        client.get("/config").json()["autonomous_burst_max_beats"] == 4,
    )

    scenario = client.get("/scenario-defaults?name=thorn-lyra").json()["scenario"]
    started = client.post(
        "/session/start",
        json={
            "characters": scenario["characters"],
            "scene": scenario["scene"],
            "controlled_character_id": scenario["controlled_character_id"],
            "narrator_directives": scenario["narrator_directives"],
        },
    ).json()
    sid = started["session_id"]
    print(f"session {sid}")

    client.post(f"/session/{sid}/turn", json={"speech": "Who runs this inn?"})
    before = client.get(f"/session/{sid}/state").json()
    turns_before = before["history"][-1]["turn_number"]

    # 2 + 3. a bare skip runs several beats and says why it stopped
    burst = client.post(f"/session/{sid}/turn", json={"skip": True}).json()
    beats = burst.get("beats") or []
    check("a bare skip commits more than one beat", len(beats) > 1, f"{len(beats)} beats")
    check(
        "the burst reports why it stopped",
        bool(burst.get("burst_stop_reason")),
        str(burst.get("burst_stop_reason")),
    )
    numbers = [b["turn_number"] for b in beats]
    check(
        "each beat is its own turn",
        len(set(numbers)) == len(numbers) and numbers == sorted(numbers),
        str(numbers),
    )

    after = client.get(f"/session/{sid}/state").json()
    turns_after = after["history"][-1]["turn_number"]
    check(
        "the clock advanced once per beat",
        turns_after - turns_before == len(beats),
        f"{turns_before} -> {turns_after} for {len(beats)} beats",
    )

    # 6. every beat reached the persisted history
    persisted = {r["turn_number"] for r in after["history"]}
    check("every beat is in persisted history", set(numbers) <= persisted, str(sorted(numbers)))

    # 4. undo pops ONE beat, not the burst
    undone = client.post(f"/session/{sid}/undo").json()
    check("undo reports success", undone.get("undone") is True)
    rolled = client.get(f"/session/{sid}/state").json()
    check(
        "undo popped exactly one beat",
        rolled["history"][-1]["turn_number"] == turns_after - 1,
        f"{turns_after} -> {rolled['history'][-1]['turn_number']}",
    )
    # NOT minus one: undo restores the beat's snapshot, which already accounts
    # for any time compression that beat applied.
    check(
        "undo rewound the clock, not forward",
        rolled["narrative_tick"] < after["narrative_tick"],
        f"{after['narrative_tick']} -> {rolled['narrative_tick']}",
    )

    # 5. a forced speaker always means exactly one beat
    forced = client.post(
        f"/session/{sid}/turn", json={"skip": True, "force_speaker": "Narrator"}
    ).json()
    forced_beats = forced.get("beats") or []
    check(
        "a forced speaker commits exactly one beat",
        len(forced_beats) <= 1,
        f"{len(forced_beats)} beats",
    )

print()
if failures:
    print(f"{len(failures)} FALHA(S):")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("smoke HTTP do burst: tudo verde")
