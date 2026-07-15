# Task 22 — Speech Audience Model (Information Boundary)

## Goal

Give the engine a first-class representation of who actually hears a speech record, so
that a secret whispered to one character does not appear in every present character's
prompt — and so the narrator's fiction and the characters' knowledge can no longer
contradict each other.

## Current Problem

Every `speech` record reaches every present character's prompt. The selection layer
(`src/agents/character.py`, `_format_history_for_character`) filters only by
`content_type`; there is no notion of audience, whisper, or addressee.

Confirmed deterministically in 3/3 real DeepSeek runs (case study:
`docs/cases/multi-character-memory-retention-2026-07-14.md`): the pair-exclusive fact
`GIRASSOL-222` was always present in Vela's prompt, and `ORQUÍDEA-741` always in Rook's,
even though the scenario framed both as secrets between two characters.

The aggravating defect is fiction/knowledge incoherence: in run 1 the narrator narrates
that Rook "does not seem to hear" the whispered password, yet two turns later Rook lists
the full code among things he heard — the fiction promises a boundary the pipeline does
not implement.

## Evidence

- `plans/artifacts/memory_focus_xyz-run*/` — recall matrices show `prompt_forbidden`
  hits in every run.
- `tests/test_memory_retention.py::TestFocusSwitchWithoutTrim::test_speech_is_public_to_all_characters_today`
  pins today's behavior; it must be inverted (or replaced) by this task.
- Playtest checks 2 and 3 in `tools/playtests/memory_focus_xyz.json` are the live
  acceptance criteria: they are `required: true` and fail today by design.

## Proposed Direction

- Extend `TurnRecord` speech entries with an optional audience field (e.g.
  `audience: list[str] | None`, `None` meaning "everyone present" for backward
  compatibility with existing sessions).
- Let the narrator (or an explicit player control) mark whispered/private speech and its
  hearers; validate hearers against `present_characters`.
- Filter per-character history selection by audience membership.
- Keep the narrator's own view complete — it must know everything to narrate coherently,
  including who did *not* hear.

## Acceptance Criteria

- `memory_focus_xyz.json` checks 2 and 3 pass (no forbidden marker in the other
  character's prompt) while check 1 still passes.
- Existing sessions (records without an audience field) behave exactly as today.
- A narration asserting a character did not hear something can no longer coexist with
  that character having the utterance in its prompt.

## Additional Evidence (2026-07-15, Task 24 acceptance runs)

With Task 24 closed, `action` records are visible to every present character — so the
fiction/knowledge incoherence now covers actions too: in session `7b363465`
(`plans/artifacts/memory_action_fact-run1/`), the narration describes Rook as "do outro
lado do salão, sem dar atenção" during the parchment scene, yet his private thought at
turn 3 references "a rota da Orquídea" — knowledge his prompt legitimately contains but
the fiction says he never witnessed. The audience model must therefore cover both
`speech` and `action` records.

---

## Closure (2026-07-15)

**Implemented** (broke no compatibility on purpose; project is alpha):
- `TurnRecord.audience: list[str] | None` (`src/models.py`) — `None` = public;
  a list makes the record whispered. `record_visible_to()` is the single
  visibility rule (audience members + the speaker).
- Character selection filters speech/action by visibility and labels whispers
  (`src/agents/character.py`); narration stays narrator-only.
- Narrator sees `[WHISPERED, perceived only by: ...]` markers plus system rules:
  outsiders must not react/reference/overhear, and "beware of denials that
  reveal" (`src/agents/narrator.py`).
- `player_turn(audience=...)` with validation; the replying character inherits
  the turn's audience when it belongs to it (`src/runner.py`); API field
  `PlayerTurnRequest.audience`; harness `turn`/`recall_check` events accept
  `audience`; transcripts render whisper markers.
- **Deterministic guard** (cycle-2 fix by an uncontexted fixer subagent):
  `redact_whisper_leaks()` strips whispered-only rare tokens from
  `context_for_character` handed to whisper outsiders, wired at the single
  point before every character call. Narration never whitelists a secret.

**Bias-controlled iteration protocol** (2 cycles authorized, both used):
- Cycle 1 (fixer subagent, no inherited context): character-level "whisper
  discipline" + confidant-exception rules in the character system prompt —
  fixed the character quoting a whispered secret in public speech at the very
  next turn.
- Cycle 2 (fixer subagent, no inherited context): wired + tested the
  deterministic narrator-context guard after the narrator leaked a password
  via a "denial that reveals" ("a senha ORQUÍDEA-741 é desconhecida para você").

**Validation**:
- Deterministic: whisper visibility/inheritance/serialization pins plus 13
  redaction-guard tests. Full suite: 341 passed, 2 xfailed.
- Real-LLM acceptance (`memory_focus_xyz.json`, whispered plants, all 3 checks
  required): v1 2/2 completed reps fully green (1 infra flake); post-cycle-1
  2/3; post-cycle-2 2/3 with the narrator path clean — the only remaining
  failure is **earned knowledge** (Rook chose to speak the hideout aloud at
  public turns; Vela genuinely overheard). Pipeline never leaked.
- Blind continuity review (3 sessions, transcript-only): whisper semantics
  hold; best session keeps the secret for 28 turns with a real dramatic arc.
  Residual failures are behavioral/narrative, not architectural.

**Acceptance criteria status**: checks 1-3 pass architecturally (no forbidden
marker ever reached an outsider's prompt through the pipeline in the final
round); legacy sessions (no audience field) behave as before; narration can now
truthfully assert non-hearing.

**Residuals routed**: character speaking whispered secrets aloud in public
(stochastic, decreasing) → Task 25. Narration contradicting established public
facts, whisper markers reinterpreted by the narrator ("words lost in the
noise"), internal ID "C3" leaking into a character thought, confabulated
"vault password", "diesel" anachronism, verbatim thought loops → Task 26.
