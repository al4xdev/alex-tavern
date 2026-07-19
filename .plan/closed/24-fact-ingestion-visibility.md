# Task 24 — Fact Ingestion Visibility (Narration/Action Facts Are Invisible to Characters)

## Goal

Prevent story facts from becoming permanently invisible to characters because of the
field they were ingested through, without giving characters the narrator's omniscient
prose wholesale.

## Current Problem

Characters never see `narration` or `action` records — by design, the content-type
filter in `src/agents/character.py` (`_format_history_for_character`) keeps only public
`speech` plus the character's own `thought` records. Consequently:

- A fact that enters the history as a player `action` (for example, an auto-suggestion
  submitted in the action field instead of speech) is unknowable to every character,
  forever.
- A fact established only in the narrator's prose (never spoken aloud) likewise never
  reaches any character, even characters the narration says witnessed it.

This is the leading hypothesis for the originally reported "character forgot" incident
(session driven through narrator auto-suggestions; original data lost). See
`docs/cases/07-multi-character-memory-retention-2026-07-14.md`, §4.1.

## Evidence

- Pinned behavior:
  `tests/test_memory_retention.py::TestFocusSwitchWithoutTrim::test_action_and_narration_facts_are_invisible_to_characters`.
- The four-layer localizer (`tools/analyze_memory_run.py`) classifies this failure mode
  as "LAYER 2: marker exists in state but never as speech".

## Proposed Direction (options to evaluate; pick the smallest that closes the hole)

1. **Ingestion-side**: make the suggestion/turn UI route factual utterances to `speech`
   and reserve `action` for genuinely physical acts; validate/warn when an action text
   looks like dialogue.
2. **Selection-side**: give characters a compact, per-turn digest of *witnessed* actions
   (their own scene) without full narrator prose — bounded in tokens, clearly labeled.
3. **Hybrid with Task 22**: once speech has an audience model, actions/narration could
   carry witnesses too, making visibility a single consistent rule.

## Acceptance Criteria

- A deterministic test where a fact enters via `action` in front of a character and that
  character can later reference it (or the chosen design explicitly documents why not,
  with the ingestion-side guard implemented instead).
- No regression in prompt-size economics: character prompt token budget impact measured
  in the playtest manifest (`max_prompt_chars`) stays within an agreed bound.

---

## Closure (2026-07-15)

**Implemented**: selection-side fix (option 2, simplified) — `action` records are now
visible to every present character in `_format_history_for_character`
(`src/agents/character.py`), labeled `TYPE=ACTION`. Narration remains narrator-only.
No audience model yet (that is Task 22); "witnessed" currently means "present".

**Validation**:
- Deterministic: new/updated pins in `tests/test_memory_retention.py`
  (`test_action_facts_are_visible_to_present_characters`,
  `test_narration_facts_remain_invisible_to_characters`,
  `test_action_planted_fact_reaches_character_prompt_end_to_end`) and
  `tests/test_integration.py`. Full suite: 318 passed, 2 xfailed.
- Real-LLM acceptance: `tools/playtests/memory_action_fact.json` (fact enters only via
  the player's `action` field — a shown-then-burned parchment), 3 repetitions against
  DeepSeek: recall check passed 3/3 at both prompt and reply level; invariants clean;
  layer localizer shows the `Player/action` record surviving all four layers.
  Artifacts: `plans/artifacts/memory_action_fact-run1/`.
- Blind continuity review (clean-context critic, transcript only): confirmed the
  knowledge is *earned* by reading in all sessions and recall is exact 3/3.

**Note on acceptance-criteria adjustment**: the first acceptance run failed only because
the reply regex was case-sensitive (`ORQU[ÍI]DEA-741` vs the model's "Orquídea-741");
raw evidence showed correct recall 3/3. Reply patterns were made case-insensitive and
forbidden patterns hardened with `(?i)` accordingly.

**Open findings routed to other tasks**: fiction/knowledge incoherence now also applies
to actions (narration says a character was inattentive while the action is in their
prompt) → Task 22; narrator fact invention and staging/duplication defects observed in
2 of 3 sessions → Task 26.
