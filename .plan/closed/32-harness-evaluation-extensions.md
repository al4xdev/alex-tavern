# Task 32 — Harness Evaluation Extensions: Cost×Quality and Routing Quality

## Goal

Extend the generic playtest harness with two measurements it cannot make today:
per-check cost attribution (what a green check actually costs) and narrator
routing quality (does the story reach the right speaker without being forced).

**Explicitly out of scope (user decision, 2026-07-15):** multi-model /
multi-provider comparison. We already know llama.cpp misbehaves on structured
output; adding it now only adds noise. This also matches Task 29.1's "no
combinatorial matrix" rule.

**Boundary with Task 29.1:** the `xfailed3` benchmark owns its own ledger,
taxonomy, and external evaluator. This task only extends the *generic* harness
(`tools/playtest_harness.py`) so every scenario benefits.

## Current Problem

- Every `recall_check` uses `force_speaker`, so the suite measures memory but
  never routing: we have zero evidence that the Narrator would deliver the
  question to the right character on its own. Task 26's blind reviews flagged
  routing/staging drift, but nothing quantifies it.
- `analyze_debug_records` counts calls, tokens, retries, and cache hits per
  run, but nothing ties cost to outcomes. We cannot answer "what did this green
  recall matrix cost?" or notice a fix that keeps checks green while doubling
  token spend.

## Proposed Direction

- **Routing probe event**: a `turn` variant (or new event) *without*
  `force_speaker` that asserts on the routing outcome — expected speaker ID (or
  set), with the same required/optional semantics as `recall_check`. Failure
  localization: narrator chose someone else vs. no character call at all.
- **Per-check cost attribution**: the harness already knows which debug records
  each check consumed (`turn_number`, `agent`); aggregate the provider `usage`
  fields per check and per run into the analysis report (prompt tokens,
  completion tokens, cache hit/miss) so cost regressions are visible next to
  pass/fail.
- Add at least one scenario (or extend `memory_focus_xyz`) with natural-routing
  probes at the moments we currently force, keeping the forced variants as the
  memory baseline.

## Acceptance Criteria

- [ ] Unit tests for the routing-probe event: validation, expected-speaker
  match, mismatch localization, and the no-character-call case.
- [ ] Unit tests for cost aggregation from synthetic debug records, including
  runs with missing `usage` fields (older providers) degrading gracefully.
- [ ] Harness report shows per-check and per-run token/cost columns.
- [ ] One real-LLM run of a scenario containing at least two natural-routing
  probes, with the routing outcomes and costs recorded in the run artifacts.
- [ ] No multi-model matrix anywhere in the deliverable.

> **CLOSED 2026-07-16.** Delivered: `routing_check` event (natural routing,
> force_speaker forbidden, expected-speaker set, localization
> no_character_call vs routed_elsewhere), per-check cost attribution
> (`turn_usage`: prompt/completion/cache tokens per checked turn), per-run
> usage totals + routing counters in the analysis, token/cache/routing columns
> in the markdown report, PT second person added to the narration metric, and
> the analyzer adapted to the post-split agents (director/prose; legacy
> narrator label still read). Real measurement: 6/6 natural-routing probes
> passed across 3 repeats (by-name and by-competence addressing), with visible
> prefix-cache warm-up (2.1k -> 6.8k -> 7.5k hit tokens) — recontextualizing
> the WT-08 benchmark signal as scenario-specific, now rate-measurable. 9 unit
> tests. Multi-model matrix explicitly absent (user decision).
