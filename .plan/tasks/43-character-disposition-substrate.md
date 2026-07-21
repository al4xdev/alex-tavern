# Task 43 — Character disposition substrate (derived state)

**Status:** 🟡 OPEN (new roadmap, 2026-07-20) — independent track, does not block
nor depend on open tasks (26/26b, 16, 38, xfailed3). Phase 0 (definition +
article) completed; Phases 1–5 open.
**Frontier article:** `docs/cases/15-character-disposition-substrate-2026-07-20.md`.
**Origin:** design conversation with the owner (2026-07-20), based on an external
suggestion (the "memory/faith system" mentioned from Sword Art Online) and the note
`.plan/backlog/player-persona-public-vs-real.md`.

## Idea

Characters cease to have a **static sheet** (personality + free-text `current_mood`)
and gain **dispositions that DERIVAM along the story**: trust that erodes, affection
that turns, composure that breaks and recovers slowly. Seeded in character creation
(in the preset), measurable and persisted, and — the point — readable in prose.

## The core discipline (what makes this mergeable)

**The 0–1 scalar belongs to the CODE; only the qualitative BAND reaches the model.** Resolves the
apparent contradiction ("the model does not honor a numeric credence field" — true)
with "we want 0–1 values" (also true): number and model live on opposite sides of a wall.
- Scalar (0–1): deterministic, persisted, testable **without spending model calls**. Provides the
  measurable side (preset seed, drift, thresholds, before/after).
- Qualitative band: this is what the character-agent **reads** (`"distrustful"`, never
  `0.72`) and the directional delta is what it **writes** ("this turn broke my
  trust"); the **code** integrates the delta into the scalar.
- This is the SAME division of labor already proven in the watcher's delta auditor (33b /
  article No. 13): the model classifies the qualitative event, the code does the arithmetic.

## The anti-complexity razor (acceptance of each axis)

> **An axis only earns its place if a BLIND reader, looking only at speech/action, can tell
> which end of the axis the character is at.** If it doesn't change observable behavior,
> it's decoration — cut it.

This is a curl test (blind critic guesses the band from prose; if it doesn't beat chance, the
axis dies). This is how "complexity with reason" becomes falsifiable, not an aspiration.

## Design decisions FROZEN (owner acceptance, 2026-07-20)

1. **Scalar-code / band-model wall** — firm (the foundation; §"discipline").
2. **Set of 3 starting axes**:
   - **Trust** (generalizes "faith") — pairwise (dyadic) — acts on another's word, lowers
     guard, shares secrets.
   - **Affection** (warmth ↔ hostility) — pairwise (dyadic) — tone, willingness to help, aggression.
   - **Composure** (calm ↔ shaken) — global — speech rhythm, impulsiveness; it is
     literally "the tone of speech". Disciplines a slice of the already existing `current_mood`.
3. **4th axis (Boldness: cautious ↔ reckless, global) does NOT enter by design — it is
   decided by CURL** (Phase 3.5). We design for 3; the 4th proves it pays off (changes
   behavior a blind judge can name, above the 3) or stays out. — owner acceptance.
4. **Dyadic scope from Phase 1** (owner acceptance): Trust/Affection are born
   dyadic (`A→B`), but **lazily materialized** — entries only where there is
   live divergence. Composure is global. This distinction kills the O(N²) explosion.
5. **Preset seeds, history derives, gravity pulls back.** Each axis carries a
   `baseline` (seeded in the preset), `value` (moved by delta), and `gravity` (relaxes
   to baseline in calm turns).
6. **Reuse watcher delta taxonomy** (`relationship_changed` already exists)
   to move the scalar — reuse proven machinery, do not build a parallel subsystem.

## Boundaries (what this is NOT)

- NOT a new memory store. "Faith" is a **belief stamp** on top of already existing
  perception/memory, not a third bank (see article No. 15 §2 and the design turn:
  "killing the word 'three memories'").
- NOT a replacement for perspective ledgers (29.2). This governs derived DISPOSITION;
  the ledgers govern PERCEPTION/subjective knowledge. Complementary.
- Built for long-term correctness, empirically validated — not optimized for
  per-call cost right now (owner's stance: cheap frontier model = spend on
  validation, design for the arc).

## Roadmap (each phase cheap and testable in isolation; curl-first gate where there is a model)

### Phase 0 — Definition + frontier article — ✅ COMPLETED (2026-07-20)
`docs/cases/15-character-disposition-substrate-2026-07-20.md`. Axes, the scalar/band wall, the razor, the unifier (public/real persona), falsifiable claims (§9). This task is the roadmap companion to the article.

### Phase 1 — The substrate (PURE CODE, zero model) — ⬜ OPEN
Data model per character: `{axis: (baseline, value, gravity)}` for global axes +
`{(observer, target): {axis: (baseline, value, gravity)}}` lazy-dyadic.
Seed from the preset. Deterministic drift/gravity per turn/tick (consumes the
clock from 40). `scalar → band` projection (pure function). Bump of schema. Testable
for free (arithmetic + projection).
- **Acceptance:** preset seed populates baselines; N calm turns relax value to baseline within tolerance; projection maps ranges → stable bands; dyadic materializes lazily (no entry = no cost); ruff+mypy clean; offline unit tests. **No model calls in this phase.**

### Phase 2 — Projection in voice (model READS band) — 🟢 GATE MET (2/3 SHIP)
Injects the band into the character-agent prompt (`_build_disposition_note` → "CURRENT PRIVATE STATE"; number NEVER enters). 3 unit tests (band appears, scalar does not leak, idle dyad remains silent). Suite 686 green.
- **Curl-first gate EXECUTED** (real deepseek, blind critic, pre-registered rule ≥8/10 per axis + ≥2/3 to ship; threshold never moved; v1/v2/v3 all logged). Evidence: `plans/artifacts/disposition-voice/VALIDATION.md`.
  - **Warmth: PASS 3× (8/9/9)** — band honored and readable by blind judge.
  - **Trust: PASS 10/10** (v3, balanced 5/5 judge) when stimulus gives room to both poles ("hold this package until tomorrow").
  - **Composure: FAIL in all 3 (5/5/7)** — does not separate at the level of ONE speech utterance. Diagnosis: it is internal "mood" that colors the delivery; a line from a competent professional reads as composed regardless of the band, and any stimulus strong enough to shake saturates the calm pole. Feels like SCENE/prosody stance, not a single utterance signal. **Owner decision pending:** demote / treat at scene level / cut (the razor might be rejecting composure at the utterance level).
- **Acceptance:** ✅ band readable by blind judge in 2/3 axes (gate); ✅ number never in prompt (test + scan). RESERVATION open: composure (see owner decision).

### Phase 3 — The feedback loop (model WRITES delta, code integrates) — 🟢 GATE MET (4/5) + WIRED
Appraisal auditor blind/Director-side (`appraise_relationships` in `src/disposition.py`): reads the last turn block and emits DIRECTIONAL deltas per pair (`observer→target`, axis trust|warmth, direction up|down, intensity slight|strong). Code integrates (`integrate_appraisal` → `ensure_dyad` + `nudge`), then 1 gravity step. Scope trust+warmth (composure parked). Wired in `Runner._apply_disposition_feedback` behind `disposition_feedback_enabled` (OFF by default). 10 unit tests + 2 integration tests; suite 696 green.
- **Curl-first gate EXECUTED** (real deepseek, 5 scenarios × 4 runs, pre-registered rule ≥3/4 per scenario + ≥4/5 to ship; v1/v2 logged). Evidence: `plans/artifacts/disposition-appraisal/VALIDATION.md`.
  - **Direction + pair reliable** (always C1→C2, correct signal). **Zero false positives** (silent neutral 4/4 in both rounds).
  - **Attribution rule** ("when B acts on A, A→B is what changes") fixed signature case: **betrayal 2/4→4/4**.
  - **Honest soft spot:** trust/warmth split is soft for acts that move both (rescue reads as warmth, not trust) — harmless: both push the dyad in the same direction and show the same warmer band. Shipped = prompt v2.
- **Acceptance:** ✅ delta tracks provocation (4/5) + gravity restores (unit) + mocked integration test (provoke→scalar moves→band flips→OFF stays static).

### Phase 3.5 — Experiment of the 4th axis (Boldness) — ⬜ OPEN
Decision #3 via curl, not hypothesis. Does the Boldness band change behavior that a blind judge can name, ABOVE the 3? Pre-registered rule before running. Enters or stays out based on evidence.

### Phase 4 — Unification with public/real persona — ⬜ OPEN
Implements `player-persona-public-vs-real.md`: public persona = **default prior**; dyadic entry = **posterior** of an observer that deviates from prior; axis value = strength of deviation. A witnessed contradiction revises the posterior (ledger revision path 29.2/39).
- **Acceptance:** inherits the acceptance criteria from the persona note (public prior seeds; dyadic posterior deviates; witness testimony revises) expressed over the substrate.

### Phase 5 — Registry article (WITH measurements) — ⬜ OPEN
The evidence article (not the definition one): what the model honored, where it was variance-bound (honest, like the screenplay clock), real cost/latency. Closes task with evidence or with a method-documented negative.

## General Acceptance Criteria (draft — freeze when starting each phase)
- [ ] Scalar substrate per character (global) + dyadic-lazy, seeded in preset, with deterministic drift/gravity and scalar→band projection. (F1)
- [ ] Band is readable in prose by blind critic in ≥2/3 axes. (F2, razor)
- [ ] Directional delta tracks provocation and gravity restores. (F3)
- [ ] Number (0–1) never appears in character/prose prompt (scan NONE). (F1/F2)
- [ ] 4th axis decided by curl (enters/stays out with pre-registered rule). (F3.5)
- [ ] Persona public=prior / dyadic=posterior realized; witness testimony revises. (F4)
- [ ] Evidence article (next case No.) with measurements and reservations. (F5)

## Project Invariant (the reason for complexity)
Each axis/feature added passes the razor (blind judge names the end of the axis from prose) OR is cut. Complexity without observability is decoration. This is what separates this substrate from a "personality vector" that bloats until nobody can measure it.
