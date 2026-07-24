"""Task 29.1 — `xfailed3` counter-canon baseline benchmark.

Three tiers over ``tests/fixtures/xfailed3_counter_canon.json``:

1. **Structural (ordinary CI, no provider)**: fixture shape, ledger referential
   integrity, source-material exclusions, and exception isolation.
2. **Reduced (``llm`` marker, strict xfail)**: turns 1-12 + compaction 1 +
   turn 13 + one restoration — the cheapest boundary containing the first
   whisper, the first compaction, and the first retention probe.
3. **Full (``llm`` marker, strict xfail)**: the complete 24-turn campaign with
   both compactions and both restorations.

The provider tiers classify NARRATIVE defects into ``Xfailed3ConsistencyError``
(the only exception the strict xfail accepts). Provider/HTTP/malformed-JSON/
persistence errors surface as ordinary failures — infrastructure must never
satisfy the narrative xfail. A run with zero classified violations XPASSes,
which strict xfail reports loudly: that is the (future) signal to start the
exit-criteria clock of the task document, never an error.

Baseline policy (Task 29.1): expected violations — e.g. the private-Historian
audience defect and the unearned-name defect — are PRESERVED and classified,
not fixed here. Task 29.2 consumes these artifacts as evidence.

Set ``XFAILED3_ARTIFACTS_DIR`` to also export the session artifacts and a
comparison manifest after a provider run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from tools.playtest_harness import (
    build_session_config,
    evaluate_recall_check,
    load_scenario,
    whisper_leak_records,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPOSITORY_ROOT / "tests" / "fixtures" / "xfailed3_counter_canon.json"
REAL_CONFIG_PATH = REPOSITORY_ROOT / ".data" / "config.json"

LUMEN = r"(?i)L[UÚ]MEN[- ]?17"

TAXONOMY = {
    "pretrained_canon_regression",
    "world_truth_contradiction",
    "character_belief_collapse",
    "unauthorized_knowledge_leak",
    "secret_disclosure",
    "identity_drift",
    "unearned_identity_familiarity",
    "relationship_drift",
    "chronology_error",
    "spatial_continuity_error",
    "unestablished_interaction",
    "impossible_staging",
    "forgotten_object_or_promise",
    "incorrect_presence",
    "speaker_routing_failure",
    "narrator_role_failure",
    "player_agency_violation",
    "compaction_loss",
    "stale_pre_compaction_state",
    "duplicated_narration",
    "verbatim_repetition",
    "language_drift_pt_br",
}


class Xfailed3ConsistencyError(Exception):
    """Classified narrative violations found by the deterministic oracle."""

    def __init__(self, violations: list[dict[str, Any]]) -> None:
        self.violations = violations
        lines = "\n".join(
            f"  [{v['violation_class']}] {v['rule']} (turn {v.get('turn')}): {v['detail'][:160]}"
            for v in violations
        )
        super().__init__(f"{len(violations)} classified violation(s):\n{lines}")


# ---------------------------------------------------------------------------
# Canon ledger: machine-readable rules keyed by stable IDs. `turn` refers to
# player-turn numbers (1..24), independent of compact/restore event positions.
# Pattern probes reuse the harness recall matrix (prompt vs reply localization).
# ---------------------------------------------------------------------------

CANON_LEDGER: dict[str, dict[str, Any]] = {
    "WT-02-kansas-refusal": {
        "turn": 3,
        "probe": {"reply_patterns": [r"(?i)\boz\b"]},
        "violation_class": "pretrained_canon_regression",
        "detail": "Dorothy must anchor her origin in Oz, not accept Kansas as home",
    },
    "SEC-01-whisper-reply-pre": {
        "turn": 4,
        "probe": {"reply_patterns": [LUMEN]},
        "violation_class": "forgotten_object_or_promise",
        "detail": "the confidant may and should confirm the whispered instrument to its owner",
    },
    "WT-03-road-direction": {
        "turn": 7,
        "probe": {"reply_patterns": [r"(?i)(afasta|longe|opost|para fora|nunca chega)"]},
        "violation_class": "pretrained_canon_regression",
        "detail": "the yellow road leads AWAY from the city in this canon",
    },
    "SOC-01a-delegate-never-learns-signatory-name": {
        "turn": 8,
        "probe": {"prompt_forbidden_patterns": [r"\bAlice\b"]},
        "violation_class": "unearned_identity_familiarity",
        "detail": "no introduction ever happens; the delegate's prompt must not carry 'Alice'",
        "earned_name_exception": True,
    },
    "WT-10-created-not-creator": {
        "turn": 8,
        "probe": {
            "reply_patterns": [
                r"(?i)(fui criado|fui construido|fui construído|me criou|me construiu)"
            ],
            "reply_forbidden_patterns": [r"(?i)eu criei"],
        },
        "violation_class": "world_truth_contradiction",
        "detail": "the delegate was created by A Criatura and created nobody",
    },
    "WT-08-natural-routing-witch": {
        "turn": 9,
        "expected_responder": "Bruxa do Oeste",
        "violation_class": "speaker_routing_failure",
        "detail": "a question addressed to the Witch by title should reach her without force",
    },
    "AGENCY-forced-controlled": {
        "turn": 11,
        "max_character_calls": 0,
        "violation_class": "player_agency_violation",
        "detail": "forcing the controlled character must return control, never generate speech",
    },
    "SEC-01-rightful-recall-pre-compaction": {
        "turn": 12,
        "probe": {"reply_patterns": [LUMEN]},
        "violation_class": "forgotten_object_or_promise",
        "detail": "whispered confirmation to the secret's owner, pre-compaction",
    },
    "WT-12-ribbon-retention": {
        "turn": 13,
        "probe": {"reply_patterns": [r"(?i)fita", r"(?i)pulso esquerdo"]},
        "violation_class": "compaction_loss",
        "detail": "the turn-2 promise (blue ribbon, left wrist) must survive compaction 1",
    },
    "WT-02-origin-retention": {
        "turn": 14,
        "probe": {"reply_patterns": [r"(?i)\boz\b"]},
        "violation_class": "compaction_loss",
        "detail": "Dorothy's origin must survive compaction 1",
    },
    "NARRATOR-forced-travel": {
        "turn": 15,
        "max_character_calls": 0,
        "violation_class": "speaker_routing_failure",
        "detail": "a forced-Narrator turn must not produce character calls",
    },
    "SOC-01a-delegate-still-anonymous": {
        "turn": 16,
        "probe": {"prompt_forbidden_patterns": [r"\bAlice\b"]},
        "violation_class": "unearned_identity_familiarity",
        "detail": "after 15 turns of acquaintance there was still no introduction",
        "earned_name_exception": True,
    },
    "WT-06-public-mortality": {
        "turn": 17,
        "probe": {
            "reply_patterns": [
                r"(?i)(mortal|humano|(?:n[aã]o|nenhum|sem)"
                r"(?![^.]{0,80}\b(?:sei|sabe(?:mos)?|saber|ser[áã]|seria|talvez|certeza)\b)"
                r"[^.]{0,80}(?:sobrenatural|vampir))"
            ]
        },
        "violation_class": "world_truth_contradiction",
        "detail": (
            "the blood assay makes the doctor's mortality public, including a "
            "negative supernatural/vampiric finding stated without the word mortal"
        ),
    },
    "NARRATOR-forced-solar": {
        "turn": 18,
        "max_character_calls": 0,
        "violation_class": "speaker_routing_failure",
        "detail": "a forced-Narrator turn must not produce character calls",
    },
    "WT-07-solar-canon-trap": {
        "turn": 18,
        "narration_forbidden": [
            r"(?i)van helsing[^.]{0,90}(queim|arde|cinza|fumeg|encolhe|fraquej)"
        ],
        "violation_class": "pretrained_canon_regression",
        "detail": "sunlight STRENGTHENS vampires here; narration must not burn Van Helsing",
    },
    "SEC-01-rightful-recall-post-compaction": {
        "turn": 21,
        "probe": {"reply_patterns": [LUMEN]},
        "violation_class": "compaction_loss",
        "detail": "the whispered instrument must survive both compactions for its confidant",
    },
    "SEC-01-watson-unauthorized": {
        "turn": 22,
        "probe": {
            "prompt_forbidden_patterns": [LUMEN],
            "reply_forbidden_patterns": [LUMEN],
        },
        "violation_class": "unauthorized_knowledge_leak",
        "detail": "Watson must neither receive nor produce the instrument's name",
    },
    "WT-02-epilogue-origin": {
        "turn": 24,
        "probe": {"reply_patterns": [r"(?i)\boz\b"]},
        "violation_class": "compaction_loss",
        "detail": "epilogue audit: origin",
    },
    "WT-09-epilogue-alias": {
        "turn": 24,
        "probe": {"reply_patterns": [r"(?i)glinda"]},
        "violation_class": "chronology_error",
        "detail": "the alias became public at turn 20 and must be recalled",
    },
    "MORIARTY-stays-unknown": {
        "turn": 24,
        "probe": {
            "reply_forbidden_patterns": [
                r"(?i)moriarty (esta|está|foi visto|foi preso|se esconde) em",
                r"(?i)moriarty (esta|está) (preso|escondido|selado)",
            ]
        },
        "violation_class": "world_truth_contradiction",
        "detail": "Moriarty's location is canonically unknown; inventing one is a violation",
    },
}

# Rules evaluated over the WHOLE recorded run, not one probe turn.
NARRATION_FORBIDDEN_CANON = [
    (r"(?i)sapatinhos? de rubi", "ruby slippers belong to excluded adaptation canon"),
    (r"(?i)dorothy[^.]{0,60}do kansas", "narration asserting Dorothy is from Kansas"),
]
# Alice (the whisperer) and Dracula (the confidant) legitimately know the
# instrument, so their PRIVATE notes and perspective calls may carry it; the
# world summary is narrator-side objective memory no character prompt receives.
# 29.3 note: the campaign fixture stays zone-less this round — zone positions
# are static in the v1 graph and the campaign requires the partition to OPEN at
# turn 8. The identity half of SP-01 is structural via the ledger (the delta
# under measurement); the spatial half stays a recorded limitation until zone
# movement lands.
SECRET_AUTHORIZED_AGENTS = {
    "character:Dracula",
    "summarizer:Dracula",
    "summarizer:Alice",
    "summarizer:world",
    "perspective:init:C5",
    "perspective:update:C5",
    "perspective:memory:C5",
    "perspective:init:C1",
    "perspective:update:C1",
    "perspective:memory:C1",
}
ANONYMOUS_PAIR = {
    # User criterion (2026-07-16): the two strangers deepen their acquaintance
    # across the whole session WITHOUT ever exchanging names.
    "delegate_agent": "character:Victor",
    "signatory_name_pattern": r"\bAlice\b",
    "delegate_name_pattern": r"\bVictor\b",
}


def _load_fixture():
    return load_scenario(FIXTURE_PATH)


def _turn_events(scenario) -> list[dict[str, Any]]:
    return [event for event in scenario.events if event["type"] == "turn"]


# ---------------------------------------------------------------------------
# Tier 1 — structural (no provider)
# ---------------------------------------------------------------------------


class TestXfailed3Structural:
    def test_fixture_shape(self) -> None:
        scenario = _load_fixture()
        types = [event["type"] for event in scenario.events]
        assert types.count("turn") == 24
        assert types.count("compact") == 2
        assert types.count("restore_compaction") == 2
        # Compactions land after player turns 12 and 20; restores close the run.
        assert types[12] == "compact" and types[21] == "compact"
        assert types[-2:] == ["restore_compaction", "restore_compaction"]

    def test_session_config_builds_with_full_cast(self) -> None:
        scenario = _load_fixture()
        config = build_session_config(scenario)
        assert config is not None
        assert len(config["characters"]) == 9
        assert config["controlled_character_id"] == "C1"
        assert config["scene"].present_characters[-1] == "Player"
        assert config["scene"].zones == {"salao_prisma": [], "compartimento_leste": []}
        assert config["scene"].positions["C9"] == "compartimento_leste"
        for character in config["characters"].values():
            assert character.mind.personality.strip()
            assert character.mind.knowledge
            assert character.body.physical_description.strip()
            assert character.body.outfit.strip()

    def test_ledger_referential_integrity(self) -> None:
        scenario = _load_fixture()
        turn_count = len(_turn_events(scenario))
        for rule_id, rule in CANON_LEDGER.items():
            assert 1 <= rule["turn"] <= turn_count, rule_id
            assert rule["violation_class"] in TAXONOMY, rule_id
            for field in (
                "prompt_patterns",
                "prompt_forbidden_patterns",
                "reply_patterns",
                "reply_forbidden_patterns",
            ):
                for pattern in rule.get("probe", {}).get(field, []):
                    re.compile(pattern)
            for pattern in rule.get("narration_forbidden", []):
                re.compile(pattern)
        for pattern, _reason in NARRATION_FORBIDDEN_CANON:
            re.compile(pattern)

    def test_whisper_audiences_are_the_confidant_only(self) -> None:
        scenario = _load_fixture()
        audiences = [event["audience"] for event in _turn_events(scenario) if event.get("audience")]
        assert audiences == [["C5"], ["C5"], ["C5"]]

    def test_source_material_exclusions(self) -> None:
        # Story-side material only: the narrator directives legitimately NAME the
        # excluded adaptation terms inside the negative role policy.
        value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        value.pop("narrator_directives", None)
        raw = json.dumps(value, ensure_ascii=False).lower()
        for term in ("sapatinho", "ruby", "renfield", "igor", "baskerville", "toto"):
            assert not re.search(rf"\b{term}\b", raw), term

    def test_anonymous_pair_is_anonymous_in_the_fixture(self) -> None:
        scenario = _load_fixture()
        config = build_session_config(scenario)
        assert config is not None
        delegate = config["characters"]["C9"]
        assert "alice" not in " ".join(delegate.mind.knowledge).lower()
        for event in _turn_events(scenario):
            assert "victor" not in event["speech"].lower()
            assert "victor" not in event["action"].lower()

    def test_exception_isolation(self) -> None:
        # Infrastructure errors must never satisfy the strict xfail.
        for exc in (ValueError("x"), RuntimeError("x"), httpx.ConnectError("x")):
            assert not isinstance(exc, Xfailed3ConsistencyError)
        assert not issubclass(Xfailed3ConsistencyError, (ValueError, AssertionError))

    def test_public_mortality_oracle_accepts_negative_supernatural_assay(self) -> None:
        pattern = CANON_LEDGER["WT-06-public-mortality"]["probe"]["reply_patterns"][0]
        assert re.search(
            pattern,
            "Meu sangue não apresenta qualquer traço de contaminação sobrenatural.",
        )
        assert not re.search(pattern, "Não posso responder a essa pergunta.")
        # Uncertainty about the supernatural is not a public negative finding.
        assert not re.search(pattern, "Não sei se ele é sobrenatural.")
        assert not re.search(pattern, "Sem exames, talvez haja algo sobrenatural nele.")
        assert not re.search(pattern, "Não temos certeza de que o doutor seja um vampiro.")


# ---------------------------------------------------------------------------
# Provider execution and deterministic oracle
# ---------------------------------------------------------------------------


def _real_config() -> dict[str, Any]:
    if not REAL_CONFIG_PATH.exists():
        pytest.skip("No real provider config at .data/config.json")
    from src.config import load_config, resolve_active_config

    config = resolve_active_config(load_config(REAL_CONFIG_PATH))
    if not config.get("api_key") and config.get("provider") == "deepseek":
        pytest.skip("Provider config has no API key")
    config.update(
        {
            "compaction_keep_recent_turns": 8,
            "automatic_compaction_enabled": False,
            "llm_timeout_seconds": max(120.0, float(config.get("llm_timeout_seconds") or 0)),
        }
    )
    return config


async def _execute_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Run fixture events against the real provider inside the isolated data dir.

    Any exception here is an ORDINARY failure: infrastructure and mechanical
    problems must never be classified as narrative evidence.
    """
    from src.runner import Runner
    from src.store.sessions import session_debug_path

    scenario = _load_fixture()
    config = _real_config()
    async with httpx.AsyncClient() as client:
        runner = Runner(client, config)
        session_id = runner.start_session(build_session_config(scenario))
        turn_numbers: list[int] = []
        for event in events:
            if event["type"] == "turn":
                result = await runner.player_turn(
                    session_id,
                    speech=event["speech"],
                    thought=event["thought"],
                    action=event["action"],
                    force_speaker=event.get("force_speaker"),
                    audience=event.get("audience"),
                )
                assert isinstance(result.get("turn_number"), int)
                turn_numbers.append(result["turn_number"])
            elif event["type"] == "compact":
                result = await runner.compact_session(session_id)
                assert result.get("compacted") is True, f"compaction failed: {result}"
            elif event["type"] == "restore_compaction":
                result = await runner.restore_last_compaction(session_id)
                assert result.get("restored") is True, f"restore failed: {result}"
            else:  # pragma: no cover - fixture is validated structurally
                raise AssertionError(event["type"])
        game = await runner.get_state(session_id)
        assert game is not None
    debug_path = session_debug_path(session_id)
    records = [
        json.loads(line)
        for line in debug_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "session_id": session_id,
        "game": game,
        "debug_records": records,
        "turn_numbers": turn_numbers,
        "session_dir": debug_path.parent,
    }


def _earned_name(game: Any, viewer_id: str, subject_id: str, name: str, turn: int) -> bool:
    """Whether the viewer's ledger legitimately learned this name by that turn.

    Post-29.2 the perspective ledger carries provenance, so the oracle can
    distinguish EARNED knowledge (e.g. a third party spoke the name aloud in the
    viewer's presence) from a leak. Pre-29.2 sessions have no snapshots and this
    returns False, preserving the baseline's binary reading.
    """
    final = game.character_perspectives.get(viewer_id)
    if final is not None:
        view = final.people.get(subject_id)
        if view and view.known_name == name and view.source_turn <= turn:
            return True
    latest: dict[str, Any] | None = None
    for record in game.history:
        if record.turn_number > turn:
            break
        snap = record.perspective_snapshot.get(viewer_id)
        if snap:
            latest = snap
    if not latest:
        return False
    view = latest.get("people", {}).get(subject_id)
    return bool(view and view.get("known_name") == name)


def _character_calls(records: list[dict[str, Any]], turn: int) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("turn_number") == turn
        and str(record.get("agent", "")).startswith("character:")
        and isinstance(record.get("request"), dict)
    ]


def collect_violations(run: dict[str, Any], executed_turns: int) -> list[dict[str, Any]]:
    """The deterministic oracle: classify narrative violations of the ledger."""
    game = run["game"]
    records = run["debug_records"]
    violations: list[dict[str, Any]] = []

    def add(rule: str, violation_class: str, turn: int | None, detail: str) -> None:
        violations.append(
            {"rule": rule, "violation_class": violation_class, "turn": turn, "detail": detail}
        )

    for rule_id, rule in CANON_LEDGER.items():
        turn = rule["turn"]
        if turn > executed_turns:
            continue
        if "probe" in rule:
            probe = evaluate_recall_check(rule["probe"], turn, records)
            if not probe["passed"]:
                if rule.get("earned_name_exception") and _earned_name(
                    game, "C9", "C1", "Alice", turn
                ):
                    continue
                add(rule_id, rule["violation_class"], turn, f"{rule['detail']} | {probe}")
        if "max_character_calls" in rule:
            calls = _character_calls(records, turn)
            if len(calls) > rule["max_character_calls"]:
                agents = [record["agent"] for record in calls]
                add(rule_id, rule["violation_class"], turn, f"{rule['detail']} | got {agents}")
        if "expected_responder" in rule:
            agents = {record["agent"] for record in _character_calls(records, turn)}
            if f"character:{rule['expected_responder']}" not in agents:
                add(rule_id, rule["violation_class"], turn, f"{rule['detail']} | got {agents}")
        for pattern in rule.get("narration_forbidden", []):
            for record in game.history:
                if (
                    record.content_type == "narration"
                    and record.turn_number == turn
                    and re.search(pattern, record.content)
                ):
                    add(rule_id, rule["violation_class"], turn, record.content[:200])

    # SP-01 structural: before the partition opens, no salon speech/action may
    # be visible to the isolated delegate. Post-29.2 the zone graph computes
    # record audiences, so this is deterministic. Calibration 2026-07-19 (3/3
    # blind naturalness samples, owner decision): the player opens the
    # partition MID turn 7, so within the boundary turn only records BEFORE
    # the opening action stay isolated - sound reaches the delegate the
    # moment the divider is open.
    from src.models import record_visible_to

    opening_index = next(
        (
            index
            for index, record in enumerate(game.history)
            if record.turn_number == 7
            and record.content_type == "action"
            and record.speaker == "Player"
            and "divis" in record.content.lower()
        ),
        None,
    )
    for index, record in enumerate(game.history):
        if record.turn_number > 7 or record.turn_number > executed_turns:
            continue
        if record.content_type not in ("speech", "action"):
            continue
        if record.speaker in ("C9", "Narrator"):
            continue
        if opening_index is not None and index > opening_index:
            continue
        if record_visible_to(record, "C9"):
            add(
                "SP-01-structural-isolation",
                "spatial_continuity_error",
                record.turn_number,
                f"pre-open salon record visible to the delegate: {record.content[:80]}",
            )

    # Whole-run invariants -------------------------------------------------
    for leak in whisper_leak_records(game):
        add("GLOBAL-whisper-leak", "secret_disclosure", leak["turn_number"], str(leak))

    for record in records:
        agent = str(record.get("agent", ""))
        request = record.get("request")
        if not isinstance(request, dict):
            continue
        prompt_text = "\n".join(
            str(message.get("content", "")) for message in request.get("messages", [])
        )
        if (
            (
                agent.startswith("character:")
                or agent.startswith("summarizer:")
                or agent.startswith("perspective:")
            )
            and agent not in SECRET_AUTHORIZED_AGENTS
            and re.search(LUMEN, prompt_text)
        ):
            add(
                "GLOBAL-secret-in-unauthorized-prompt",
                "unauthorized_knowledge_leak",
                record.get("turn_number"),
                f"{agent} request contains the whispered instrument",
            )
        if (
            agent == ANONYMOUS_PAIR["delegate_agent"]
            and re.search(ANONYMOUS_PAIR["signatory_name_pattern"], prompt_text)
            and not _earned_name(game, "C9", "C1", "Alice", record.get("turn_number") or 0)
        ):
            add(
                "GLOBAL-anonymous-pair-prompt",
                "unearned_identity_familiarity",
                record.get("turn_number"),
                "delegate prompt carries the signatory's never-learned name",
            )

    for record in game.history:
        if record.speaker not in game.characters or record.content_type not in (
            "speech",
            "thought",
        ):
            continue
        if record.speaker != "C9" and re.search(
            ANONYMOUS_PAIR["delegate_name_pattern"], record.content
        ):
            add(
                "GLOBAL-anonymous-pair-reply",
                "unearned_identity_familiarity",
                record.turn_number,
                f"{record.speaker} used the delegate's never-learned name: {record.content[:120]}",
            )
        if (
            record.speaker == "C9"
            and re.search(ANONYMOUS_PAIR["signatory_name_pattern"], record.content)
            and not _earned_name(game, "C9", "C1", "Alice", record.turn_number)
        ):
            add(
                "GLOBAL-anonymous-pair-reply",
                "unearned_identity_familiarity",
                record.turn_number,
                f"delegate used the signatory's never-learned name: {record.content[:120]}",
            )

    for pattern, reason in NARRATION_FORBIDDEN_CANON:
        for record in game.history:
            if record.content_type == "narration" and re.search(pattern, record.content):
                add(
                    "GLOBAL-narration-canon",
                    "pretrained_canon_regression",
                    record.turn_number,
                    f"{reason}: {record.content[:160]}",
                )

    return violations


def _export_artifacts(run: dict[str, Any], violations: list[dict[str, Any]], tier: str) -> None:
    target_root = os.environ.get("XFAILED3_ARTIFACTS_DIR")
    if not target_root:
        return
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = Path(target_root) / f"{tier}-{stamp}-{run['session_id']}"
    shutil.copytree(run["session_dir"], target / "session")
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unknown"
    manifest = {
        "tier": tier,
        "session_id": run["session_id"],
        "source_revision": revision,
        "executed_turns": run["turn_numbers"],
        "violations": violations,
        "generated_at": stamp,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Tier 2/3 — provider-backed, classified strict xfail
# ---------------------------------------------------------------------------


@pytest.mark.llm
@pytest.mark.xfail(strict=True, raises=Xfailed3ConsistencyError)
async def test_xfailed3_reduced_tier() -> None:
    scenario = _load_fixture()
    events = list(scenario.events[:14]) + [{"type": "restore_compaction"}]
    run = await _execute_events(events)
    violations = collect_violations(run, executed_turns=13)
    _export_artifacts(run, violations, tier="reduced")
    if violations:
        raise Xfailed3ConsistencyError(violations)


@pytest.mark.llm
@pytest.mark.xfail(strict=True, raises=Xfailed3ConsistencyError)
async def test_xfailed3_full_tier() -> None:
    scenario = _load_fixture()
    run = await _execute_events(list(scenario.events))
    assert sorted(set(run["turn_numbers"])) == list(range(1, 25))
    violations = collect_violations(run, executed_turns=24)
    _export_artifacts(run, violations, tier="full")
    if violations:
        raise Xfailed3ConsistencyError(violations)
