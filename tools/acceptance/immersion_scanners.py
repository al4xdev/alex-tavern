"""Offline scanners for three immersion defects, over an archived session.

Same shape and the same promise as ``repetition_metrics``: raw ``state.json`` +
``debug.jsonl``, pure stdlib, zero provider cost, and readable by a session
written under an older schema. What they add is that these three defects are
*leaks* rather than repetition — they are not "how repetitive is this" numbers,
they are counts of an invariant being violated, so each one is parameter-free
enough to gate its own task at zero.

Standing rule they all obey (`.plan/ROADMAP.md`): **verify against
``debug.jsonl``, not ``state.json``.** Twice in this investigation a conclusion
was built on a key that does not exist in the durable state, and the empty result
was read as evidence of absence. Anything here that claims what the Director
DECIDED reads the Director's own records.

The three, and the task each one exists to close:

``redaction``      Where ``REDACTION_MARKER`` ends up, split by channel — prose,
                   persisted speech/action record, and the perspective ledger.
                   Task 63 cannot choose between its options without the split:
                   a marker in a transient render is the guard working, a marker
                   in a persisted record is durable damage to the fiction.

``director_speech`` Persisted speech records whose text came from a Director
                   ``audible_speech`` event rather than from the character agent.
                   The largest measured defect in the archive and task 65's
                   primary number.

``empty_audience``  Speech and action records persisted with an audience of
                   nobody while the zone graph put someone in earshot — a
                   character shouting in a full hall that no one hears. Task 67's
                   closure evidence. Reported next to how many raw Director
                   events actually proposed an empty witness list, because that
                   is what separates "the model narrowed perception" from "the
                   engine dropped the audience".

    uv run python -m tools.acceptance.immersion_scanners --battery plans/artifacts/p1-archive
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.confidentiality import REDACTION_MARKER
from tools.acceptance.repetition_metrics import load_session, sim

# A persisted record and the Director event it came from are the same string,
# except that redaction may have replaced tokens in one of them, so the match is a
# similarity and not an equality. Measured over the whole 16-session archive, the
# two populations do not overlap and 0.85 falls in the empty band between them:
#
#   matched pairs (n=639)          min 0.857, 5th pct 0.942, median 1.000
#   records with a same-turn,
#   same-speaker event that is
#   NOT their source (n=475)       median 0.319, max below the line 0.827
#
# Exactly one record in the archive sits above the line unmatched, at 1.000 — a
# second copy of a line the Director had already re-voiced, so the count this
# scanner reports is conservative by one, never inflated. Re-derive this band if
# the threshold is ever moved: it is the whole argument for the number.
DIRECTOR_SPEECH_TAU = 0.85

_SPOKEN_TYPES = ("speech", "action")
_PLAYER = "Player"


# ---------------------------------------------------------------------------
# Director events, straight from the log
# ---------------------------------------------------------------------------


def director_events(records: list[dict], effective_only: bool = True) -> list[tuple[int, dict]]:
    """``(turn, perception_event)`` as the Director wrote them.

    ``effective_only`` keeps the LAST successful ``director`` record of each turn,
    which is the one the runner consumed — transport retries and the
    hint-materialization retry are not extra proposals. The raw count (every
    parsed record) is reported alongside it in the audience scanner, because
    "what did the model ever propose" and "what did the engine act on" are
    different questions and mixing them is how an engine-side drop gets blamed on
    the model.
    """
    parsed_by_turn: dict[int, list[dict]] = {}
    for record in records:
        if record.get("agent") != "director" or not record.get("response"):
            continue
        try:
            parsed = json.loads(record["response"])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            parsed_by_turn.setdefault(int(record.get("turn_number") or 0), []).append(parsed)

    out: list[tuple[int, dict]] = []
    for turn in sorted(parsed_by_turn):
        attempts = parsed_by_turn[turn][-1:] if effective_only else parsed_by_turn[turn]
        for attempt in attempts:
            for event in attempt.get("perception_events") or []:
                if isinstance(event, dict):
                    out.append((turn, event))
    return out


def _character_names(state: dict) -> dict[str, str]:
    return {
        cid: str((character.get("body") or {}).get("name", ""))
        for cid, character in (state.get("characters") or {}).items()
    }


def _routed_turns(records: list[dict], names: dict[str, str]) -> set[tuple[int, str]]:
    """``(turn, character_id)`` pairs where the character agent was actually called.

    The debug channel names the agent by CHARACTER NAME (``character:Bruna
    Ferrugem``), so it is mapped back through the cast. This is the honest source
    for "was this character routed this turn": a character can be routed and
    return an empty speech, which leaves no trace in ``state.json`` at all.
    """
    by_name = {name: cid for cid, name in names.items() if name}
    routed: set[tuple[int, str]] = set()
    for record in records:
        agent = str(record.get("agent") or "")
        if not agent.startswith("character:"):
            continue
        cid = by_name.get(agent.split(":", 1)[1])
        if cid:
            routed.add((int(record.get("turn_number") or 0), cid))
    return routed


# ---------------------------------------------------------------------------
# Scanner 1 — where the redaction marker ends up
# ---------------------------------------------------------------------------


def _ledger_texts(perspective: dict) -> list[tuple[str, str, str]]:
    """``(channel, text, target)`` for every durable string in one viewer's ledger.

    Three sub-channels, because they fail differently. ``ledger_recent_memory``
    is a character's own recollection of what was said in the room and carries
    the bulk of the damage — one mutilated public line propagates into every
    witness's memory, so the persisted-record count understates the reach.
    ``ledger_memory_summary`` is the compacted version of the same, which is what
    survives after the window rolls. ``ledger_people`` is the identity ledger,
    where a marker corrupts how one character KNOWS another.
    """
    out: list[tuple[str, str, str]] = []
    for line in perspective.get("recent_memory") or []:
        out.append(("ledger_recent_memory", str(line), ""))
    summary = str(perspective.get("memory_summary") or "")
    if summary:
        out.append(("ledger_memory_summary", summary, ""))
    for target, entry in (perspective.get("people") or {}).items():
        text = " ".join(str(entry.get(name) or "") for name in ("known_name", "reference"))
        out.append(("ledger_people", text, str(target)))
    return out


def scan_redaction(state: dict) -> dict:
    """``REDACTION_MARKER`` occurrences, split by the channel it landed in.

    The split is the whole point. The guard is *supposed* to redact a transient
    render for one viewer; every count here is a marker that outlived the render
    — in narration a reader sees, in a speech record that feeds RECENT EVENTS
    forever after, or baked into a character's durable ledger entry for another
    character. Those three call for different fixes, which is why task 63 blocks
    on this number rather than on a total.
    """
    channels: dict[str, dict[str, Any]] = {}
    evidence: list[dict] = []

    def hit(channel: str, count: int) -> dict:
        entry = channels.setdefault(channel, {"occurrences": 0, "records": 0})
        entry["occurrences"] += count
        entry["records"] += 1
        return entry

    for record in state.get("history", []):
        content = str(record.get("content") or "")
        count = content.count(REDACTION_MARKER)
        if not count:
            continue
        channel = str(record.get("content_type") or "?")
        hit(channel, count)
        evidence.append(
            {
                "turn": int(record.get("turn_number") or 0),
                "channel": channel,
                "speaker": str(record.get("speaker") or ""),
                "text": content[:180],
            }
        )

    affected_viewers: set[str] = set()
    for viewer, perspective in (state.get("character_perspectives") or {}).items():
        for entry_channel, text, target in _ledger_texts(perspective):
            count = text.count(REDACTION_MARKER)
            if not count:
                continue
            affected_viewers.add(viewer)
            hit(entry_channel, count)
            evidence.append(
                {
                    "turn": 0,
                    "channel": entry_channel,
                    "speaker": f"{viewer}->{target}" if target else viewer,
                    "text": text[:180],
                }
            )

    persisted = sum(entry["records"] for name, entry in channels.items() if name in _SPOKEN_TYPES)
    ledger_entries = sum(
        entry["records"] for name, entry in channels.items() if name.startswith("ledger_")
    )
    return {
        "occurrences": sum(entry["occurrences"] for entry in channels.values()),
        "records_with_marker": sum(entry["records"] for entry in channels.values()),
        "persisted_speech_records": persisted,
        "ledger_entries": ledger_entries,
        "ledger_viewers": len(affected_viewers),
        "by_channel": channels,
        "evidence": evidence[:10],
    }


# ---------------------------------------------------------------------------
# Scanner 2 — speech the Director wrote and the engine attributed to a character
# ---------------------------------------------------------------------------


def match_director_speech(state: dict, records: list[dict]) -> dict[int, tuple[int, dict, float]]:
    """``id(record) -> (turn, director event, ratio)`` for Director-authored speech.

    ``_persist_audible_speech`` (``runner.py``) writes a Director
    ``audible_speech`` event into history as a speech record attributed to the
    character — so the corpus contains two producers of dialogue wearing the same
    byline. Matching is by content rather than by any stored flag: the record
    carries ``audience_origin='zone'`` exactly like an ordinary zone-scoped line,
    so there is nothing in ``state.json`` that distinguishes them. The text is
    persisted verbatim from the event, which is why a similarity match at a high
    threshold recovers the pairing.

    Where a turn has several candidates for one speaker, the LAST unmatched
    record wins the tie: the persistence runs after the reply loop, so the
    Director's version is appended after the character's own line.
    """
    events = [
        (turn, event)
        for turn, event in director_events(records)
        if event.get("event_kind") == "audible_speech" and str(event.get("content") or "").strip()
    ]

    by_turn_speaker: dict[tuple[int, str], list[dict]] = {}
    for record in state.get("history", []):
        if record.get("content_type") != "speech":
            continue
        by_turn_speaker.setdefault((int(record["turn_number"]), str(record["speaker"])), []).append(
            record
        )

    matched: dict[int, tuple[int, dict, float]] = {}
    for turn, event in events:
        subject = str(event.get("subject_id") or "")
        best: tuple[float, dict] | None = None
        for record in by_turn_speaker.get((turn, subject), []):
            if id(record) in matched:
                continue
            ratio = sim(str(record["content"]), str(event["content"]))
            if best is None or ratio >= best[0]:  # ties go to the later record
                best = (ratio, record)
        if best is None or best[0] < DIRECTOR_SPEECH_TAU:
            continue
        ratio, record = best
        matched[id(record)] = (turn, event, ratio)
    return matched


def scan_director_speech(state: dict, records: list[dict]) -> dict:
    """How much of the persisted dialogue the Director wrote instead of the actor.

    ``routed_same_turn`` is the number a fix has to answer for — a re-voiced line
    for a character who was standing right there with an agent call of their own
    is the shape that produces the duplication, the third-person self-reference
    and the identity bleed.
    """
    names = _character_names(state)
    routed = _routed_turns(records, names)
    pairs = match_director_speech(state, records)

    speech = [
        record for record in state.get("history", []) if record.get("content_type") == "speech"
    ]
    matched: list[dict] = []
    for record in speech:
        found = pairs.get(id(record))
        if found is None:
            continue
        turn, _event, ratio = found
        subject = str(record["speaker"])
        matched.append(
            {
                "turn": turn,
                "character_id": subject,
                "name": names.get(subject, ""),
                "ratio": round(ratio, 4),
                "routed_same_turn": (turn, subject) in routed,
                "redacted": REDACTION_MARKER in str(record["content"]),
                "text": str(record["content"])[:180],
            }
        )

    events = [
        event
        for _turn, event in director_events(records)
        if event.get("event_kind") == "audible_speech" and str(event.get("content") or "").strip()
    ]
    non_player = [r for r in speech if str(r.get("speaker")) != _PLAYER]
    return {
        "speech_records": len(speech),
        "speech_records_excluding_player": len(non_player),
        "director_authored": len(matched),
        "share_of_speech": (len(matched) / len(non_player)) if non_player else None,
        "routed_same_turn": sum(1 for hit in matched if hit["routed_same_turn"]),
        "carrying_redaction": sum(1 for hit in matched if hit["redacted"]),
        "audible_speech_events": len(events),
        "evidence": matched[:10],
    }


# ---------------------------------------------------------------------------
# Scanner 3 — a record nobody heard, in a room full of people
# ---------------------------------------------------------------------------


def can_perceive(scene: dict, witness_id: str, subject_id: str) -> bool:
    """Raw-dict mirror of ``src.perception.can_perceive``.

    Deliberately a mirror and not an import: this reads scene SNAPSHOTS off
    archived sessions, which must keep parsing after the live model has moved on.
    ``tests/test_immersion_scanners.py`` asserts the mirror agrees with the
    shipped function across the topologies that matter, so it cannot drift
    silently.
    """
    zones = scene.get("zones") or {}
    if not zones:
        return True
    positions = scene.get("positions") or {}
    witness_zone = positions.get(witness_id)
    subject_zone = positions.get(subject_id)
    if witness_zone is None or subject_zone is None:
        return True
    if witness_zone == subject_zone:
        return True
    return subject_zone in (zones.get(witness_zone) or [])


def eligible_witnesses(scene: dict, characters: dict, subject_id: str) -> set[str]:
    return {
        cid
        for cid in scene.get("present_characters") or []
        if cid in characters and cid != subject_id and can_perceive(scene, cid, subject_id)
    }


def scan_empty_audience(state: dict, records: list[dict]) -> dict:
    """Speech and action records the engine says nobody heard.

    ``audience: []`` and ``audience: null`` are different things: null means "the
    default audience, everyone who can perceive it", and an empty LIST means the
    engine decided this line reached no one.

    **The classification deliberately does not trust the zone graph**, because the
    zone graph is the suspect. Asking ``eligible_witnesses`` whether the audience
    should have been empty is circular: when a sub-zone is minted with no inbound
    edge, the graph agrees that nobody can hear, and the scanner would certify the
    bug as correct. So each hit is sorted by a question the graph cannot answer:

    ``isolated``         nobody else is present in the scene. Legitimately empty.
    ``graph_isolated``   others ARE present and the graph says none of them can
                         perceive the speaker. Physically a person shouting in a
                         crowded hall that the graph has cut off — task 67.
    ``narrowed_to_none`` the graph left witnesses in earshot, and the audience is
                         empty anyway: only a Director-sourced record can reach
                         this state, by proposing a witness list that intersects
                         the eligible set to nothing. Both archive cases are
                         `oldcode-P1-r1` T18/T19, where the Director listed the
                         SPEAKER as the only witness of their own shout, and then
                         three people the graph put out of earshot. A different
                         defect from the graph one, and two orders smaller.

    ``proposed_witnesses`` is the smoking gun where the record came from a Director
    ``audible_speech`` event: how many witnesses the Director actually listed
    before the deterministic clamp ran. Eighteen becoming zero is not a model
    mistake.

    The Director's own witness lists are counted for the session too. If the model
    almost never proposes an empty list and history is full of them, the audience
    was emptied on the engine's side of the boundary, and no prompt change fixes it.
    """
    characters = state.get("characters") or {}
    controlled = str((state.get("player") or {}).get("controlled_character_id") or "")
    pairs = match_director_speech(state, records)

    hits: list[dict] = []
    counts = {"isolated": 0, "graph_isolated": 0, "narrowed_to_none": 0}
    for record in state.get("history", []):
        if record.get("content_type") not in _SPOKEN_TYPES:
            continue
        if record.get("audience") != []:
            continue
        speaker = str(record.get("speaker") or "")
        subject = controlled if speaker == _PLAYER else speaker
        scene = record.get("scene_snapshot") or {}
        positions = scene.get("positions") or {}
        present = [
            cid
            for cid in scene.get("present_characters") or []
            if cid in characters and cid != subject
        ]
        reachable = eligible_witnesses(scene, characters, subject)
        same_zone = [cid for cid in present if positions.get(cid) == positions.get(subject)]

        if not present:
            verdict = "isolated"
        elif reachable:
            verdict = "narrowed_to_none"
        else:
            verdict = "graph_isolated"
        counts[verdict] += 1

        found = pairs.get(id(record))
        hits.append(
            {
                "turn": int(record.get("turn_number") or 0),
                "type": str(record.get("content_type")),
                "speaker": subject,
                "verdict": verdict,
                "zone": positions.get(subject),
                "present_others": len(present),
                "same_zone": len(same_zone),
                "zone_reachable": len(reachable),
                "proposed_witnesses": (
                    len(found[1].get("witness_ids") or []) if found is not None else None
                ),
                "text": str(record.get("content") or "")[:180],
            }
        )

    effective = director_events(records)
    raw = director_events(records, effective_only=False)

    def empty_witnesses(events: list[tuple[int, dict]]) -> int:
        return sum(1 for _, event in events if event.get("witness_ids") == [])

    return {
        "empty_audience_records": len(hits),
        "isolated": counts["isolated"],
        "with_others_present": counts["graph_isolated"] + counts["narrowed_to_none"],
        "graph_isolated": counts["graph_isolated"],
        "narrowed_to_none": counts["narrowed_to_none"],
        "clamped_from_proposed": sum(1 for hit in hits if (hit["proposed_witnesses"] or 0) > 0),
        "max_witnesses_clamped": max((hit["proposed_witnesses"] or 0) for hit in hits)
        if hits
        else 0,
        "director_events_effective": len(effective),
        "director_events_effective_empty_witnesses": empty_witnesses(effective),
        "director_events_raw": len(raw),
        "director_events_raw_empty_witnesses": empty_witnesses(raw),
        "evidence": hits[:10],
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass
class ScanReport:
    session_id: str
    turns: int
    redaction: dict = field(default_factory=dict)
    director_speech: dict = field(default_factory=dict)
    empty_audience: dict = field(default_factory=dict)


def scan(session_id: str, root: Path | None = None) -> ScanReport:
    state, records = load_session(session_id, root)
    turns = len({int(r["turn_number"]) for r in state.get("history", [])})
    return ScanReport(
        session_id=session_id,
        turns=turns,
        redaction=scan_redaction(state),
        director_speech=scan_director_speech(state, records),
        empty_audience=scan_empty_audience(state, records),
    )


def _summary_line(report: ScanReport) -> str:
    redaction = report.redaction
    speech = report.director_speech
    audience = report.empty_audience
    share = speech["share_of_speech"]
    return (
        f"{report.session_id}  turns={report.turns:3d}  "
        f"REDACT={redaction['occurrences']:3d} "
        f"(persisted {redaction['persisted_speech_records']}, "
        f"ledger {redaction['ledger_entries']})  "
        f"DIRSPEECH={speech['director_authored']:3d}/{speech['speech_records_excluding_player']:4d}"
        f" ({'n/a' if share is None else f'{share * 100:4.1f}%'}, "
        f"routed {speech['routed_same_turn']})  "
        f"NOAUD={audience['with_others_present']:2d}/{audience['empty_audience_records']:2d}"
        f" (graph-cut {audience['graph_isolated']}, narrowed "
        f"{audience['narrowed_to_none']}, clamped from up to "
        f"{audience['max_witnesses_clamped']}; director proposed empty: "
        f"{audience['director_events_raw_empty_witnesses']}/{audience['director_events_raw']})"
    )


def scan_battery(battery: Path) -> list[dict]:
    """Every run under an artifact directory, in the layout the battery writes."""
    out: list[dict] = []
    for run_dir in sorted(battery.glob("*-r*")):
        states = list((run_dir / "sessions").glob("*/state.json"))
        if not states:
            continue
        session_dir = states[0].parent
        report = scan(session_dir.name, root=session_dir.parent)
        out.append({"run": run_dir.name, **asdict(report)})
    return out


def _totals(rows: list[dict]) -> dict:
    def total(section: str, name: str) -> int:
        return sum(int(row[section][name] or 0) for row in rows)

    speech_total = total("director_speech", "speech_records_excluding_player")
    authored = total("director_speech", "director_authored")
    return {
        "sessions": len(rows),
        "redaction_occurrences": total("redaction", "occurrences"),
        "redaction_sessions": sum(1 for row in rows if row["redaction"]["occurrences"]),
        "redaction_persisted_records": total("redaction", "persisted_speech_records"),
        "redaction_ledger_entries": total("redaction", "ledger_entries"),
        "speech_records": speech_total,
        "director_authored": authored,
        "director_authored_share": (authored / speech_total) if speech_total else None,
        "director_authored_routed_same_turn": total("director_speech", "routed_same_turn"),
        "director_authored_sessions": sum(
            1 for row in rows if row["director_speech"]["director_authored"]
        ),
        "empty_audience_records": total("empty_audience", "empty_audience_records"),
        "empty_audience_with_others_present": total("empty_audience", "with_others_present"),
        "empty_audience_graph_isolated": total("empty_audience", "graph_isolated"),
        "empty_audience_narrowed_to_none": total("empty_audience", "narrowed_to_none"),
        "empty_audience_isolated": total("empty_audience", "isolated"),
        "empty_audience_sessions": sum(
            1 for row in rows if row["empty_audience"]["with_others_present"]
        ),
        "director_events_raw": total("empty_audience", "director_events_raw"),
        "director_events_raw_empty_witnesses": total(
            "empty_audience", "director_events_raw_empty_witnesses"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", action="append", default=[], help="session id (repeatable)")
    parser.add_argument(
        "--battery", type=Path, help="artifact dir holding <cell>-<profile>-rN runs"
    )
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    parser.add_argument("--out", type=Path, help="write the JSON report here as well")
    args = parser.parse_args()

    if args.battery:
        rows = scan_battery(args.battery)
    else:
        rows = [asdict(scan(sid)) for sid in args.session]
    if not rows:
        raise SystemExit("nothing to scan: pass --session or --battery")

    payload = {"totals": _totals(rows), "runs": rows}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    for row in rows:
        label = row.get("run")
        report = ScanReport(**{k: v for k, v in row.items() if k != "run"})
        print(f"{label or '':16s} {_summary_line(report)}")
    totals = payload["totals"]
    share = totals["director_authored_share"]
    print(
        f"\nTOTAL over {totals['sessions']} sessions: "
        f"redaction {totals['redaction_occurrences']} occurrences in "
        f"{totals['redaction_sessions']} sessions "
        f"({totals['redaction_persisted_records']} persisted records, "
        f"{totals['redaction_ledger_entries']} ledger entries)  |  "
        f"Director-authored speech {totals['director_authored']}/{totals['speech_records']}"
        f" ({'n/a' if share is None else f'{share * 100:.1f}%'}) in "
        f"{totals['director_authored_sessions']} sessions, "
        f"{totals['director_authored_routed_same_turn']} for a character routed that turn  |  "
        f"empty audience {totals['empty_audience_records']} records, "
        f"{totals['empty_audience_with_others_present']} with others present in "
        f"{totals['empty_audience_sessions']} sessions "
        f"({totals['empty_audience_graph_isolated']} cut off by the graph, "
        f"{totals['empty_audience_narrowed_to_none']} narrowed to none), against "
        f"{totals['director_events_raw_empty_witnesses']}/{totals['director_events_raw']}"
        f" Director events proposing one"
    )


if __name__ == "__main__":
    main()
