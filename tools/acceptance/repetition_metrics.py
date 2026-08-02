"""Repetition metrics over a recorded session — the ruler, built before the cut.

Why not the existing lexical metrics: ``roteiro_ab.lexical_metrics`` measures
narration sentence echo, which is exactly the invariant ``prose._strip_echoed_
sentences`` already enforces by deletion. It is near-floor by construction, and
"the same event described in new words" passes it untouched. Measured on the two
evidence sessions the failure modes are disjoint — 20d4cdb3 fired the prose
repetition guard on 5 of 11 turns, 15d40dfa on 0 of 6 — so any single primary
metric masks one of them.

What this module measures instead is the DECISION: which stimuli the Director
proposed, and how many of them restate something already in play. Two guards
against a degenerate engine that "fixes" repetition by going quiet: NSR (novel
stimuli per turn) and SIL (silent turns) must not degrade while RSR falls.

Everything here except ``material_delta_rate`` is pure stdlib and offline: it
reads ``state.json`` and ``debug.jsonl`` and spends nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# Default similarity above which a stimulus counts as restating something
# already in play. Pre-registered at 0.8; report the sensitivity band with it.
DEFAULT_TAU = 0.8
# Verbatim-duplication threshold for ECHO_PERSIST. Deliberately much higher than
# TAU: this metric answers "was the identical line persisted twice", not "is this
# similar", so it must not absorb genuine restatement.
ECHO_TAU = 0.95
# Turn blocks of prior transcript handed to the material-delta judge. Windowing
# by TURNS, not by records: a record window spans fewer turns in an arm that
# routes more speakers, which would hand busier arms a shorter memory and bias
# them toward "moved".
MDR_CONTEXT_TURNS = 4

_PROGRESS_TYPES = ("speech", "action", "narration")
_SPOKEN_TYPES = ("speech", "action")

# "<attribution>: '<payload>'" — the Director's re-voicing wrapper. Stripping it
# is what turns the two measured duplicates in 15d40dfa from 0.8207 / 0.8327
# (under the 0.88 echo guard, therefore persisted) into 1.0000.
_FRAME = re.compile(r"^.{0,90}?[:—–-]\s*[\"'“‘](.+)[\"'”’]\s*$", re.S)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def norm(text: str) -> str:
    """Casefolded, accent-stripped, whitespace-collapsed text."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def unframe(text: str) -> str:
    """The quoted payload of an attribution frame, or the text unchanged."""
    match = _FRAME.match(text.strip())
    return match.group(1) if match else text


def key(text: str) -> str:
    """Comparison key: the payload, normalized. Frames must not hide a repeat."""
    return norm(unframe(text))


def sim(left: str, right: str) -> float:
    return SequenceMatcher(None, key(left), key(right)).ratio()


def recurrence(text: str, priors: list[str]) -> float:
    """Highest similarity of ``text`` against anything already in play (0 if none)."""
    return max((sim(text, prior) for prior in priors), default=0.0)


# ---------------------------------------------------------------------------
# Session loading (raw JSON on purpose: an analysis tool must keep reading
# sessions written before whatever schema the engine is on today)
# ---------------------------------------------------------------------------


def _sessions_root() -> Path:
    import os

    return Path(os.environ.get("ROLEPLAY_DATA_DIR", ".data")).expanduser() / "sessions"


def load_session(session_id: str, root: Path | None = None) -> tuple[dict, list[dict]]:
    """(state, debug records) for one session."""
    base = (root or _sessions_root()) / session_id
    state = json.loads((base / "state.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (base / "debug.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return state, records


def _is_llm_call(record: dict) -> bool:
    """LLM calls carry a provider; the markers (turn_input, undo, ...) do not."""
    return "provider" in record


# ---------------------------------------------------------------------------
# Stimulus extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Stimulus:
    turn_number: int
    event_kind: str
    subject_id: str
    content: str


def proposed_stimuli(records: list[dict]) -> list[Stimulus]:
    """Perception events the Director PROPOSED, one effective set per turn.

    A turn can hold several ``director`` records: transport retries and the
    hint-materialization guard retry. Only the last successful one is what the
    runner actually consumed, so earlier attempts must not be counted as extra
    proposals.
    """
    effective: dict[int, Any] = {}
    for record in records:
        if record.get("agent") != "director" or not record.get("response"):
            continue
        try:
            parsed = json.loads(record["response"])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            effective[int(record.get("turn_number") or 0)] = parsed

    stimuli: list[Stimulus] = []
    for turn in sorted(effective):
        for event in effective[turn].get("perception_events") or []:
            if not isinstance(event, dict):
                continue
            content = str(event.get("content", "")).strip()
            if content:
                stimuli.append(
                    Stimulus(
                        turn_number=turn,
                        event_kind=str(event.get("event_kind", "")),
                        subject_id=str(event.get("subject_id", "")),
                        content=content,
                    )
                )
    return stimuli


def spoken_before(state: dict, turn: int) -> list[str]:
    """Speech and action already in the transcript before ``turn``."""
    return [
        str(record["content"])
        for record in state.get("history", [])
        if record.get("content_type") in _SPOKEN_TYPES and int(record["turn_number"]) < turn
    ]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class RepetitionReport:
    session_id: str
    tau: float
    turns: int
    player_actions: int

    # Primary mechanism metric: does the Director still WANT to repeat?
    rsr_prop: float | None
    stimuli: int
    repeated_stimuli: int
    # Throughput and silence interlocks: a degenerate engine that stops emitting
    # scores rsr_prop 0 and fails both of these.
    nsr: float | None
    sil: float | None
    # Verbatim speech duplication persisted into history (the framed re-voicing).
    echo_persist: int
    # Lexical pressure on the renderer, free from guard_retry.
    guard: float | None
    guard_turns: int
    prose_turns: int
    # Beat pinning and replan thrash.
    beat_occupancy_max: int
    beat_runs: list[dict] = field(default_factory=list)
    exit_reasons: dict[str, int] = field(default_factory=dict)
    replans_per_action: float | None = None
    llm_calls_per_action: float | None = None
    # Act-skeleton rewrites. A live turn ceiling makes beat replans routine,
    # which makes ACT_REPLAN_THRESHOLD reachable for the first time — before the
    # cuts it was effectively dead code. Churning the act skeleton is the way
    # this fix could pay for less repetition with less coherence, so it is a
    # pre-registered cost guard, not a footnote.
    act_rewrites: int = 0
    act_rewrites_per_action: float | None = None
    # Recurring-stimulus clusters. RSR alone under-detects the defect it was
    # built for: a pairwise threshold asks "is THIS event a repeat of some
    # earlier one", and a scene re-staged with fresh wording sits just under it
    # every time. Measured in base-P1-r1, the Director sealed the same doors
    # across 8 turns with pairwise similarities of 0.53-0.89; RSR counted 4.
    # Clustering at a deliberately looser threshold asks the right question:
    # how many times did ONE situation come back?
    cluster_max: int = 0
    cluster_span: int = 0
    clusters: list[dict] = field(default_factory=list)
    # INPUT, not output. Every metric above scores what the model PRODUCED; the
    # dominant defect measured in base-P1-r1 was in what the code ORDERED — the
    # same world_event injected as a mandatory UPCOMING EVENT twelve times,
    # because the terminal act's clock re-fired forever. Eleven output metrics
    # could not see it. This one would have found it in a single command.
    # Split, because conflating them makes the metric unusable: the clock
    # signal is a CONTROL instruction that legitimately recurs once per skip
    # turn, so counting it hid a 4x-repeated world event behind a 6x-repeated
    # instruction. Only a repeated EVENT is a defect.
    max_hint_repeats: int = 0
    control_injections: int = 0
    distinct_hints: int = 0
    injected_turn_fraction: float | None = None
    act_deadlines: int = 0
    hint_detail: list[dict] = field(default_factory=list)
    # Physical contradiction, countable and free. A fact value returning to a
    # value it already held ("alarm: soando -> silencioso -> soando") is the
    # signature of an event being re-staged, and it survives in the state channel
    # even when the prose guard hides it. This is the coherence instrument.
    revert_total: int = 0
    revert_max_per_key: int = 0
    revert_detail: list[dict] = field(default_factory=list)
    # The state channel's own health: it is unbounded and never pruned.
    fact_keys: int = 0
    fact_bytes: int = 0
    fact_synonym_pairs: int = 0
    fact_transient_keys: int = 0
    # Churn risk introduced by the two beat clocks: beats cut before they land.
    beat_life_mean: float | None = None
    beats_replaced_with_anchors_pending: float | None = None
    # Sensitivity band around the pre-registered tau.
    rsr_prop_by_tau: dict[str, float] = field(default_factory=dict)
    # Evidence, not just numbers.
    worst_repeats: list[dict] = field(default_factory=list)
    echo_pairs: list[dict] = field(default_factory=list)


CLUSTER_TAU = 0.6


def _cluster_stimuli(stimuli: list[Stimulus], tau: float = CLUSTER_TAU) -> list[dict]:
    """Clusters of stimuli that keep re-staging ONE situation.

    Leader clustering, not single linkage: every member must be similar to the
    cluster's FIRST member, never merely to a neighbour. Single linkage chains —
    measured on null-P1-r2 it fused 22 stimuli whose first and last sit at 0.249
    similarity, because the Director announces successive names in a recurring
    FORMAT ("A Diretora anuncia que...") with genuinely new content each time.
    A recurring format is not a recurring event, and the metric must not confuse
    them.

    The threshold is looser than the pairwise one on purpose: a restaged scene
    drifts in wording, so "the doors seal again" lands at 0.6-0.8 against its
    own first staging and never trips a 0.8 pairwise test.

    Only clusters spanning more than one TURN count: several facets of one event
    inside a single turn are staging, not repetition.
    """
    leaders: list[tuple[Stimulus, list[Stimulus]]] = []
    for stim in stimuli:
        for leader, members in leaders:
            if sim(leader.content, stim.content) > tau:
                members.append(stim)
                break
        else:
            leaders.append((stim, [stim]))

    clusters = []
    for _, members in leaders:
        turns = sorted({m.turn_number for m in members})
        if len(turns) < 2:
            continue
        clusters.append(
            {
                "turns": turns,
                "size": len(turns),
                "span": turns[-1] - turns[0] + 1,
                "sample": members[0].content[:140],
            }
        )
    return sorted(clusters, key=lambda c: -c["size"])


# The Director prompt renders the injected hint as a header line followed by one
# indented line (src/agents/narrator.py, _build_user_prompt).
_HINT_HEADER = "UPCOMING EVENT (incorporate this into your narration):"
# Per-character transient state. These belong in zone_moves / mood_updates, not
# in durable world facts; 14 of the 54 keys in base-P1-r1 were this shape.
_TRANSIENT_KEY = re.compile(r"_(action|position|stance|state|status)$")
_FACT_SYNONYM_TAU = 0.75


def injected_hints(records: list[dict]) -> dict[int, str]:
    """The UPCOMING EVENT text handed to the Director, per turn.

    Reads the PROMPT, not the response. The block is mandatory by contract
    ("no coherence concern overrides it") and backed by a correction retry, so a
    repeated injection is an order repeated, not a model preference.
    """
    hints: dict[int, str] = {}
    for record in records:
        if record.get("agent") != "director" or not record.get("request"):
            continue
        messages = record["request"].get("messages") or []
        if not messages:
            continue
        text = str(messages[-1].get("content", ""))
        head, sep, tail = text.partition(_HINT_HEADER)
        if not sep:
            continue
        line = tail.lstrip("\n").split("\n", 1)[0].strip()
        if line:
            hints[int(record.get("turn_number") or 0)] = line
    return hints


def _is_control_signal(text: str) -> bool:
    from src.runner import CLOCK_SKIP_INVITE

    return sim(text, CLOCK_SKIP_INVITE) > 0.9


def _hint_repetition(records: list[dict], turns: int) -> dict:
    hints = injected_hints(records)
    control = sum(1 for text in hints.values() if _is_control_signal(text))
    grouped: dict[str, list[int]] = {}
    for turn, text in sorted(hints.items()):
        if _is_control_signal(text):
            continue
        grouped.setdefault(key(text), []).append(turn)
    detail = sorted(
        ({"repeats": len(t), "turns": t, "sample": hints[t[0]][:120]} for t in grouped.values()),
        key=lambda entry: -entry["repeats"],
    )
    deadlines = sum(
        1
        for record in records
        if record.get("agent") == "roteiro_replan" and record.get("action") == "act_deadline"
    )
    return {
        "max_hint_repeats": max((entry["repeats"] for entry in detail), default=0),
        "control_injections": control,
        "distinct_hints": len(grouped),
        "injected_turn_fraction": (len(hints) / turns) if turns else None,
        "act_deadlines": deadlines,
        "hint_detail": detail[:5],
    }


def _fact_timeline(state: dict) -> list[tuple[int, dict]]:
    """(turn, physical_facts) as the scene looked when each turn was recorded."""
    seen: dict[int, dict] = {}
    for record in state.get("history", []):
        snapshot = record.get("scene_snapshot") or {}
        facts = snapshot.get("physical_facts")
        if isinstance(facts, dict):
            seen[int(record["turn_number"])] = facts
    return sorted(seen.items())


def _reverts(state: dict) -> tuple[int, int, list[dict]]:
    """Fact values that return to a value the key already held.

    Doors cannot seal twice; an alarm cannot start after it already started
    unless it stopped. Walking each key's value history turns "physical
    contradiction" into an integer, offline and for free.
    """
    history: dict[str, list[str]] = {}
    reverts: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    for _, facts in _fact_timeline(state):
        for fact_key, value in facts.items():
            text = str(value)
            seen = history.setdefault(fact_key, [])
            if seen and seen[-1] == text:
                continue  # unchanged, not a revert
            if text in seen:
                reverts[fact_key] = reverts.get(fact_key, 0) + 1
            seen.append(text)
            examples.setdefault(fact_key, []).append(text[:40])
    detail = [
        {"key": k, "reverts": n, "values": examples.get(k, [])[:6]}
        for k, n in sorted(reverts.items(), key=lambda item: -item[1])
    ]
    return sum(reverts.values()), max(reverts.values(), default=0), detail[:5]


def _fact_health(state: dict) -> dict:
    facts = state.get("scene", {}).get("physical_facts", {}) or {}
    keys = list(facts)
    synonyms = sum(
        1
        for i in range(len(keys))
        for j in range(i + 1, len(keys))
        if SequenceMatcher(None, norm(keys[i]), norm(keys[j])).ratio() > _FACT_SYNONYM_TAU
    )
    return {
        "fact_keys": len(keys),
        "fact_bytes": len(json.dumps(facts, ensure_ascii=False)),
        "fact_synonym_pairs": synonyms,
        "fact_transient_keys": sum(1 for k in keys if _TRANSIENT_KEY.search(k)),
    }


def _beat_life(records: list[dict], runs: list[dict]) -> dict:
    """Mean beat lifetime, and how often a beat is replaced still owing anchors.

    The two beat clocks made replans routine; cutting beats before they land is
    the way that fix could pay for less repetition with less coherence.
    """
    replaced = [
        record
        for record in records
        if record.get("agent") == "roteiro_replan"
        and record.get("action") in ("replan_beat", "replan_act")
    ]
    pending = sum(1 for record in replaced if record.get("anchors_missing"))
    return {
        "beat_life_mean": (sum(r["length"] for r in runs) / len(runs)) if runs else None,
        "beats_replaced_with_anchors_pending": (pending / len(replaced)) if replaced else None,
    }


def _turn_numbers(state: dict) -> list[int]:
    return sorted({int(r["turn_number"]) for r in state.get("history", [])})


def _echo_persist(state: dict) -> tuple[int, list[dict]]:
    """Speech records that verbatim-duplicate an earlier line by the same voice."""
    seen: list[tuple[int, str, str]] = []
    hits: list[dict] = []
    for record in state.get("history", []):
        if record.get("content_type") != "speech":
            continue
        turn = int(record["turn_number"])
        speaker = str(record["speaker"])
        content = str(record["content"])
        for prior_turn, prior_speaker, prior in seen:
            if prior_speaker != speaker:
                continue
            ratio = sim(content, prior)
            if ratio >= ECHO_TAU:
                hits.append(
                    {
                        "speaker": speaker,
                        "first_turn": prior_turn,
                        "repeat_turn": turn,
                        "ratio": round(ratio, 4),
                        "raw_ratio": round(
                            SequenceMatcher(None, norm(content), norm(prior)).ratio(), 4
                        ),
                        "text": content[:160],
                    }
                )
                break
        seen.append((turn, speaker, content))
    return len(hits), hits


def _beat_timeline(records: list[dict], turns: list[int]) -> tuple[int, list[dict]]:
    """Longest run of consecutive turns under one beat, keyed by beat CONTENT.

    Never keyed by ``beat_id``: that string is written by the model, is unstable
    across replans and collides across acts.
    """
    generated: list[tuple[int, str, str]] = []  # (turn, identity, beat_id)
    for record in records:
        agent = record.get("agent")
        if agent not in ("roteiro:compile", "roteiro:replan") or not record.get("response"):
            continue
        try:
            parsed = json.loads(record["response"])
        except json.JSONDecodeError:
            continue
        beat = parsed.get("first_beat") if agent == "roteiro:compile" else parsed.get("beat")
        if not isinstance(beat, dict):
            continue
        anchors = sorted(norm(str(a)) for a in beat.get("expected_anchors") or [])
        identity = norm(str(beat.get("intent", ""))) + "|" + "|".join(anchors)
        generated.append((int(record.get("turn_number") or 0), identity, str(beat.get("beat_id"))))

    if not generated:
        return 0, []

    runs: list[dict] = []
    for turn in turns:
        active = [g for g in generated if g[0] <= turn]
        if not active:
            continue
        _, identity, beat_id = active[-1]
        if runs and runs[-1]["identity"] == identity:
            runs[-1]["turns"].append(turn)
        else:
            runs.append({"identity": identity, "beat_id": beat_id, "turns": [turn]})

    for run in runs:
        run["length"] = len(run["turns"])
        run["identity"] = run["identity"][:120]
    return max((r["length"] for r in runs), default=0), runs


def analyze(
    session_id: str, tau: float = DEFAULT_TAU, root: Path | None = None
) -> RepetitionReport:
    """Every offline metric for one recorded session. Spends nothing."""
    state, records = load_session(session_id, root)
    turns = _turn_numbers(state)
    turn_count = len(turns)
    player_actions = sum(1 for r in records if r.get("agent") == "turn_input")

    stimuli = proposed_stimuli(records)
    scored: list[tuple[Stimulus, float, str]] = []
    for stim in stimuli:
        priors = [s.content for s in stimuli if s.turn_number < stim.turn_number]
        priors += spoken_before(state, stim.turn_number)
        best, best_text = 0.0, ""
        for prior in priors:
            ratio = sim(stim.content, prior)
            if ratio > best:
                best, best_text = ratio, prior
        scored.append((stim, best, best_text))

    repeated = [s for s in scored if s[1] > tau]
    novel = [s for s in scored if s[1] <= tau]

    narrated_turns = {
        int(r["turn_number"])
        for r in state.get("history", [])
        if r.get("content_type") == "narration"
    }
    silent = [t for t in turns if t not in narrated_turns]

    prose_turns = {int(r["turn_number"]) for r in records if r.get("agent") == "prose"}
    guard_turns = {
        int(r["turn_number"])
        for r in records
        if r.get("agent") == "prose" and r.get("guard_retry") == "repetition"
    }

    echo_count, echo_pairs = _echo_persist(state)
    occupancy, runs = _beat_timeline(records, turns)

    decisions = [r for r in records if r.get("agent") == "roteiro_replan"]
    exit_reasons: dict[str, int] = {}
    for decision in decisions:
        if decision.get("action") in (None, "none"):
            continue
        label = f"{decision.get('action')}:{decision.get('reason')}"
        exit_reasons[label] = exit_reasons.get(label, 0) + 1
    replans = sum(exit_reasons.values())
    llm_calls = sum(1 for r in records if _is_llm_call(r))
    # Counted from the RESPONSE, not from the decision label: an act-scope
    # replan is the one whose payload carries a rewritten `acts` array, which
    # stays true if the decision vocabulary ever changes.
    act_rewrites = 0
    for record in records:
        if record.get("agent") != "roteiro:replan" or not record.get("response"):
            continue
        try:
            parsed = json.loads(record["response"])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("acts"):
            act_rewrites += 1

    clusters = _cluster_stimuli(stimuli)
    revert_total, revert_max, revert_detail = _reverts(state)
    worst = sorted(scored, key=lambda item: -item[1])[:8]

    return RepetitionReport(
        session_id=session_id,
        tau=tau,
        turns=turn_count,
        player_actions=player_actions,
        rsr_prop=(len(repeated) / len(scored)) if scored else None,
        stimuli=len(scored),
        repeated_stimuli=len(repeated),
        nsr=(len(novel) / turn_count) if turn_count else None,
        sil=(len(silent) / turn_count) if turn_count else None,
        echo_persist=echo_count,
        guard=(len(guard_turns) / len(prose_turns)) if prose_turns else None,
        guard_turns=len(guard_turns),
        prose_turns=len(prose_turns),
        beat_occupancy_max=occupancy,
        beat_runs=[
            {"beat_id": r["beat_id"], "turns": r["turns"], "length": r["length"]} for r in runs
        ],
        exit_reasons=exit_reasons,
        replans_per_action=(replans / player_actions) if player_actions else None,
        llm_calls_per_action=(llm_calls / player_actions) if player_actions else None,
        act_rewrites=act_rewrites,
        act_rewrites_per_action=(act_rewrites / player_actions) if player_actions else None,
        cluster_max=clusters[0]["size"] if clusters else 0,
        cluster_span=clusters[0]["span"] if clusters else 0,
        clusters=clusters[:5],
        **_hint_repetition(records, turn_count),
        revert_total=revert_total,
        revert_max_per_key=revert_max,
        revert_detail=revert_detail,
        **_fact_health(state),
        **_beat_life(records, runs),
        rsr_prop_by_tau={
            f"{probe:.1f}": (sum(1 for s in scored if s[1] > probe) / len(scored))
            if scored
            else 0.0
            for probe in (0.7, 0.8, 0.9)
        },
        worst_repeats=[
            {
                "turn": stim.turn_number,
                "kind": stim.event_kind,
                "recur": round(ratio, 4),
                "event": stim.content[:150],
                "matched": match[:150],
            }
            for stim, ratio, match in worst
            if ratio > 0.5
        ],
        echo_pairs=echo_pairs,
    )


# ---------------------------------------------------------------------------
# Material delta rate — the only metric here that costs tokens
# ---------------------------------------------------------------------------


async def material_delta_rate(
    client: Any, config: dict, session_id: str, votes: int = 3
) -> dict[str, Any]:
    """Fraction of committed turns that produced a material delta.

    Reuses the validated auditor in ``tools/watcher_experiment.py`` — the only
    NOVELTY-GATE prompt in the repo ("an event described a second time in
    different words is none"). Arm-neutral by construction: it never sees which
    engine produced the turn. Majority of ``votes`` per turn; the per-turn
    agreement is reported so a coin-flip judge is visible rather than trusted.
    """
    from src.store.sessions import load_game
    from tools.watcher_experiment import audit_turn, audit_window

    game = load_game(session_id)
    assert game is not None, f"session {session_id} not found"
    turns = sorted({record.turn_number for record in game.history})

    per_turn: list[dict[str, Any]] = []
    for turn in turns:
        # Window by turn blocks, then translate to the record count audit_window
        # expects, so busier arms do not get a shorter memory than quiet ones.
        block = [t for t in turns if t < turn][-MDR_CONTEXT_TURNS:]
        context_records = len(
            [r for r in game.history if r.turn_number in block and r.content_type != "thought"]
        )
        audit_window(game, turn, context_records=context_records)
        ballots: list[bool] = []
        for _ in range(votes):
            result = await audit_turn(client, config, game, turn)
            deltas = [d for d in (result.get("deltas") or []) if d != "none"]
            ballots.append(bool(deltas))
        moved = sum(ballots) > votes / 2
        per_turn.append(
            {
                "turn": turn,
                "moved": moved,
                "agreement": max(ballots.count(True), ballots.count(False)) / votes,
            }
        )

    moved_count = sum(1 for entry in per_turn if entry["moved"])
    return {
        "mdr": moved_count / len(per_turn) if per_turn else None,
        "turns": len(per_turn),
        "mean_agreement": (
            sum(e["agreement"] for e in per_turn) / len(per_turn) if per_turn else None
        ),
        "per_turn": per_turn,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _pct_or_na(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _summary_line(report: RepetitionReport) -> str:
    def pct(value: float | None) -> str:
        return "  n/a" if value is None else f"{value * 100:5.1f}%"

    return (
        f"{report.session_id}  turns={report.turns:3d} actions={report.player_actions:2d}  "
        f"RSR_prop={pct(report.rsr_prop)} ({report.repeated_stimuli}/{report.stimuli})  "
        f"NSR={report.nsr if report.nsr is None else round(report.nsr, 2)}  "
        f"SIL={pct(report.sil)}  GUARD={pct(report.guard)}  "
        f"ECHO={report.echo_persist}  BOCC={report.beat_occupancy_max}  "
        f"RPA={report.replans_per_action}  ACTR={report.act_rewrites}  "
        f"CLUSTER={report.cluster_max}/{report.cluster_span}t  "
        f"CPA={report.llm_calls_per_action}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", action="append", required=True, help="session id (repeatable)")
    parser.add_argument("--tau", type=float, default=DEFAULT_TAU)
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    parser.add_argument("--evidence", action="store_true", help="print the worst repeats")
    args = parser.parse_args()

    reports = [analyze(sid, tau=args.tau) for sid in args.session]
    if args.json:
        print(json.dumps([asdict(r) for r in reports], ensure_ascii=False, indent=2))
        return

    for report in reports:
        print(_summary_line(report))
        print(
            f"  INPUT: evento repetido {report.max_hint_repeats}x  "
            f"sinais de controle={report.control_injections}  "
            f"distintos={report.distinct_hints}  act_deadline={report.act_deadlines}  "
            f"turnos com injecao={_pct_or_na(report.injected_turn_fraction)}"
        )
        for entry in report.hint_detail:
            if entry["repeats"] > 1:
                print(f"    {entry['repeats']}x turnos {entry['turns']}: {entry['sample'][:80]}")
        print(
            f"  ESTADO: reverts={report.revert_total} (pior chave {report.revert_max_per_key})  "
            f"fatos={report.fact_keys} chaves/{report.fact_bytes}b  "
            f"sinonimos={report.fact_synonym_pairs}  transitorias={report.fact_transient_keys}"
        )
        for entry in report.revert_detail:
            if entry["reverts"]:
                print(f"    {entry['key']}: {entry['reverts']}x  {' -> '.join(entry['values'])}")
        print(f"  exit reasons: {report.exit_reasons or '{}'}")
        print(f"  beat runs:    {[(r['beat_id'], r['length']) for r in report.beat_runs]}")
        print(f"  RSR by tau:   {report.rsr_prop_by_tau}")
        if report.echo_pairs:
            print("  verbatim speech duplicated into history:")
            for pair in report.echo_pairs:
                print(
                    f"    T{pair['first_turn']}->T{pair['repeat_turn']} {pair['speaker']} "
                    f"key={pair['ratio']} raw={pair['raw_ratio']} | {pair['text'][:90]}"
                )
        if args.evidence:
            print("  worst repeated stimuli:")
            for item in report.worst_repeats:
                print(f"    T{item['turn']} recur={item['recur']} {item['kind']}")
                print(f"      event:   {item['event']}")
                print(f"      matched: {item['matched']}")
        print()


if __name__ == "__main__":
    main()
