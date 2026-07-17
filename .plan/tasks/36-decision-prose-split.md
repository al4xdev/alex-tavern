# Task 36 — Decision/Prose Split, Character Action Intents, and the Resolver

**Type:** Supertask (the core of the Director/Resolver architecture,
`.plan/tasks/explore-29.2-architecture-map.md` §Decision layer). Runs under the
full protocol: implementation increments, real-run validation, blind critic ×2
with an uncontexted fixer between cycles.

## Goal

Unbundle the combined Narrator into single-authority boxes:

```text
Character  -> speech + thought + action_intent   (intent, never outcome)
Resolver   -> validates intent, adjudicates consequences, emits typed
              perception_events + state deltas    (single physical authority)
Prose renderer (blind) -> renders ONLY confirmed public facts into narration
```

A character may return "Avançar com a lança e bloquear a passagem" as intent;
it may never assert the outcome — the kill belongs to the Resolver. This
formalizes the existing rule "an action is an attempt until narration confirms
it" and executes the user's directive to SHRINK the Narrator and delegate.

## Why now (evidence)

- The Narrator is the measured weakest link: passivity, role violations,
  dialogue duplicated inside narration (Tasks 26 evidence, sessions 091b11c6,
  ef6b5b90, perspective/partition smokes).
- Prose leaks (thoughts, IDs, sheets) end structurally when the renderer
  receives only confirmed public facts — the selection-before-call principle
  measured at 0/13 vs 7/13.
- The foundation exists: typed perception_events with deterministic witness
  clamping (29.2 inc. 2) are exactly the Resolver's output format; the
  multi-speaker queue (task 34) is the routing seed.
- Character action was green-lit by the user ("dar aos personagens capacidade
  de agir, descentralizando o narrador"): character calls are the cheapest and
  cache-dominated.

## Scope notes

- **Zone movement lands here**: a movement intent is adjudicated by the
  Resolver into a typed position delta (removes the static-zones limitation
  recorded in 29.3 round 1).
- The Resolver contract is strictly "typed intent → typed outcome + events +
  deltas": no prose, no viewer context, no moods. Guard against it becoming a
  second overloaded narrator (recorded risk, exploration §9).
- Prompt-cache shape: Decision and Prose calls share the stable prefix; the
  Prose request appends the validated decision (29.2 doc §7 hypothesis —
  measure hit rates before freezing).

## Acceptance Criteria (headline)

- [ ] Character schema gains `action_intent`; runner never persists an intent
  as an outcome.
- [ ] Resolver adjudication is a structured call whose output passes
  deterministic validation (presence, zones, agency) before anything commits.
- [ ] Prose renderer receives only validated public facts: no thoughts, no
  sheets, no IDs, no roteiro material in its request (assertable from
  debug.jsonl).
- [ ] Movement intents change `Scene.positions` transactionally and are
  undo-safe.
- [ ] xfailed3 re-run (29.3 round 2) with the partition case now typed via
  zones + movement; before/after delta published.
- [ ] Blind critic ×2: dialogue-inside-narration class must drop to zero by
  construction (the renderer never sees unspoken replies).

## Async topology note (user, 2026-07-16)

Run the Director/Resolver call CONCURRENTLY with the characters' internal
variable updates (perspective/ledger updates): both consume the same committed
prior state and have no data dependency on each other, so the latency
concentrates only at the moments that reorder the narration (the beat
boundaries), instead of serializing every turn. Constraints: deterministic
merge order on completion (results keyed and applied in canonical order), and
the Prose call still waits for the validated Decision (hard dependency).
Zone-parallelism from the map also applies (parallel across zones, sequential
within one).

## Status (2026-07-16)

- **36.1 DELIVERED** (commit d7a3783): Director decision call + blind prose
  renderer + async beat-boundary topology. Cycle-1 blind critic found 6+
  dialogue-in-narration instances -> uncontexted fixer removed spoken words
  from ALL prose inputs by construction -> deterministic cycle-2 verification:
  0/4 instances, identity/isolation without regression.
- **36.2 DELIVERED** (commit 33b9a40): `action_intent` (attempt physics),
  `zone_moves`, dynamic `zone_link_updates`; full physics arc validated live
  2/2 (partition opens -> invite crosses -> intent -> move resolves ->
  perception), with one emergent refusal.
- **Cycle-2 subjective critic EXECUTED** (after API recovery): confirmed
  dialogue-in-narration = NO everywhere and the code never leaked; found
  verbatim narration blocks across turns, prose staging the isolated character
  "a few meters away" (renderer had no zone briefing), and a pre-void-guard
  isolated-hallucination take. Uncontexted fixer delivered the deterministic
  anti-repetition guard (fuzzy >0.85, one correction retry, never fails the
  turn) and the STAGING zone block + separation rule in the prose prompt.
  Fresh re-measurement: near-dup sentences 6/15 -> 0/0, staging red-flags
  NONE, isolated thoughts physically correct. Suite 490 passed.
- **REMAINING for full closure**: 29.3 round with the ZONED campaign fixture
  (re-author beats so the partition opens mid-campaign via zone_link_updates).
