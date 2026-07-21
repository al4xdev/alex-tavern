# Task 43 — Character disposition substrate (derived state)

**Status:** ✅ CLOSED WITH A MEASURED NEGATIVE (2026-07-21). Trust/Warmth shipped
as lazy witnessed dyads behind the existing opt-in feedback flag. Composure was
cut after failing 5/5/7. Phase 4's public-prior reuse failed 5/8 then 4/8 and was
removed; public-vs-real persona remains a separate backlog problem, not a hidden
partial implementation.
**Frontier article:** `docs/cases/15-character-disposition-substrate-2026-07-20.md`.
**Article of record:** `docs/cases/16-disposition-substrate-measured-verdict-2026-07-21.md`.
**Origin:** design conversation with the owner (2026-07-20), based on an external
suggestion (the "memory/faith system" mentioned from Sword Art Online) and the note
`.plan/backlog/player-persona-public-vs-real.md`.

## Idea

Characters cease to have a **static sheet** (personality + free-text `current_mood`)
and gain **dispositions that DERIVAM along the story**: trust that erodes and
affection that turns. They are measurable, persisted and readable in prose.

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
2. **Starting candidates and measured outcome**:
   - **Trust** (generalizes "faith") — pairwise (dyadic) — acts on another's word, lowers
     guard, shares secrets.
   - **Affection** (warmth ↔ hostility) — pairwise (dyadic) — tone, willingness to help, aggression.
   - **Composure** (calm ↔ shaken) was tested as a global candidate and CUT after
     failing every blind-read battery (5/5/7).
3. **4th axis (Boldness: cautious ↔ reckless, global) does NOT enter by design — it is
   decided by CURL** (Phase 3.5). We design for 3; the 4th proves it pays off (changes
   behavior a blind judge can name, above the 3) or stays out. — owner acceptance.
4. **Dyadic scope from Phase 1** (owner acceptance): Trust/Affection are born
   dyadic (`A→B`), but **lazily materialized** — entries only where there is
   live witnessed divergence. This kills the O(N²) explosion.
5. **History derives, gravity pulls back.** Each dyadic axis carries a neutral
   `baseline`, a `value` moved by delta, and `gravity` that relaxes in calm turns.
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

### Phase 1 — The substrate (PURE CODE, zero model) — ✅ COMPLETED
`{(observer, target): {axis: (baseline, value, gravity)}}` is lazy-dyadic.
Deterministic gravity, clamping, projection, serialization and undo snapshots are
test-locked. No entry means no persisted or prompt cost.

### Phase 2 — Projection in voice (model READS band) — 🟢 GATE MET (2/3 SHIP)
Injects the band into the character-agent prompt (`_build_disposition_note` → "CURRENT PRIVATE STATE"; number NEVER enters). 3 unit tests (band appears, scalar does not leak, idle dyad remains silent). Suite 686 green.
- **Curl-first gate EXECUTED** (real deepseek, blind critic, pre-registered rule ≥8/10 per axis + ≥2/3 to ship; threshold never moved; v1/v2/v3 all logged). Evidence: `plans/artifacts/disposition-voice/VALIDATION.md`.
  - **Warmth: PASS 3× (8/9/9)** — band honored and readable by blind judge.
  - **Trust: PASS 10/10** (v3, balanced 5/5 judge) when stimulus gives room to both poles ("hold this package until tomorrow").
  - **Composure: FAIL in all 3 (5/5/7) → CUT.** It did not separate at one
    utterance and never entered appraisal. Schema 13 removes it completely.
- **Acceptance:** ✅ band readable by blind judge in 2/3 axes; ✅ number never in
  prompt; ✅ failed axis removed rather than parked.

### Phase 3 — The feedback loop (model WRITES delta, code integrates) — 🟢 GATE MET (4/5) + WIRED
Appraisal auditor blind/Director-side (`appraise_relationships` in `src/disposition.py`): reads the last turn block and emits DIRECTIONAL deltas per pair (`observer→target`, axis trust|warmth, direction up|down, intensity slight|strong). Code integrates (`integrate_appraisal` → `ensure_dyad` + `nudge`), then 1 gravity step. Wired in `Runner._apply_disposition_feedback` behind `disposition_feedback_enabled` (OFF by default). Schema 13 also clamps every proposal to speech/action the observer actually perceived.
- **Curl-first gate EXECUTED** (real deepseek, 5 scenarios × 4 runs, pre-registered rule ≥3/4 per scenario + ≥4/5 to ship; v1/v2 logged). Evidence: `plans/artifacts/disposition-appraisal/VALIDATION.md`.
  - **Direction + pair reliable** (always C1→C2, correct signal). **Zero false positives** (silent neutral 4/4 in both rounds).
  - **Attribution rule** ("when B acts on A, A→B is what changes") fixed signature case: **betrayal 2/4→4/4**.
  - **Honest soft spot:** trust/warmth split is soft for acts that move both (rescue reads as warmth, not trust) — harmless: both push the dyad in the same direction and show the same warmer band. Shipped = prompt v2.
- **Acceptance:** ✅ delta tracks provocation (4/5) + gravity restores (unit) + mocked integration test (provoke→scalar moves→band flips→OFF stays static).

### Phase 3.5 — Experiment of the 4th axis (Boldness) — ✅ RESOLVED (by Task 44, 2026-07-20)
Original question: does a Boldness band change behavior a blind judge can READ, above
the 3? That framing was answered indirectly and reframed by Task 44's curl gate:
**Boldness does NOT earn a substrate axis.** Its value is not being read in prose (it
failed that, like composure) — it is **tilting the CHOICE under the screenplay**, and
that works as a TRANSIENT injected impulse (Task 44 arm C: 2.00 contribution, zero
leak, voice preserved), needing no scalar/band/gravity/feedback. So Boldness stays OUT
of the persisted substrate (which remains trust/warmth); it lives as Task 44's
alignment nudge. See the durable benchmark in
`.plan/closed/44-roteiro-character-alignment-toggles.md`.

### Phase 4 — Unification with public/real persona — ❌ MEASURED NEGATIVE
Implements `player-persona-public-vs-real.md`: public persona = **default prior**; dyadic entry = **posterior** of an observer that deviates from prior; axis value = strength of deviation. A witnessed contradiction revises the posterior (ledger revision path 29.2/39).
- **Acceptance:** inherits the acceptance criteria from the persona note (public prior seeds; dyadic posterior deviates; witness testimony revises) expressed over the substrate.

#### Phase 4 gate pre-registration (2026-07-21, before calls)

The candidate implementation used authored `public_disposition` trust/warmth scalars as the
code-owned first-impression prior. An absent prior is neutral and silent. The first
witnessed relationship event lazily materializes `observer→target` with that prior
as `baseline`; the appraisal delta moves `value`, which is the posterior. Only the
qualitative band reaches Character prompts. `composure` is CUT, not parked: it
failed the Phase 2 razor in all three batteries (5/5/7), never entered appraisal,
and keeping a persisted inert axis would violate the anti-complexity rule.

Real-provider gates, with targets frozen before execution:

1. **Public-prior boundary:** use production Character builders for one observer
   facing the same target/stimulus under low vs high public Trust, 4 renders per
   pole. A blind forced-choice judge must score ≥7/8 and choose both poles at least
   once. No scalar, target real personality, or secret may appear in the prompt.
2. **Real-persona adjudication:** use the production Narrator builder on a player
   whose real sheet says power 8 and whose public prior is highly trustworthy/warm,
   then have them claim overwhelming power and attempt to defeat an elite. Pass
   only if 3/3 outcomes refuse victory by assertion and preserve player agency.
3. **Witness revision:** deterministic gate, not a model tendency: an appraisal
   proposal changes `A→B` only when A perceived B's speech/action in that turn.
   Heard evidence must pass; the identical whispered-away evidence must be dropped.

The task closes only if all three pass. A failed target is recorded without moving
the threshold; any prompt variant must be isolated, pre-registered, then rerun as
the exact production variant.

**V1 result (recorded before changing production):** public-prior boundary FAILED
5/8 (both poles chosen); real-persona adjudication PASSED 3/3; witnessed-evidence
code gate PASSED. Low-Trust failures accepted custody with contractual safeguards,
which the blind judge reasonably read as acceptance/high Trust. The scalar and the
target's real secret were absent from every Character prompt. This is not a privacy
failure; the qualitative band was behaviorally too soft at the chosen extreme.

**V2 pre-registration (before code/calls):** keep the same characters, balanced
bundle stimulus, 4+4 renders, blind judge and ≥7/8 threshold. Change only the
production disposition header to define observable semantics already owned by the
axes: Trust controls reliance/verification; Warmth controls receptiveness/kindness.
The note still cannot prescribe an action or expose a number. Run the exact
production builder. If v2 fails, public priors do not ship and Phase 4 cannot be
marked successful.

**V2 result and decision:** FAILED 4/8 with both poles chosen. Per the frozen rule,
the public-prior field, UI, state and prompt path were removed completely. The
experiment rejects Trust/Warmth reuse as the representation for public persona;
it does not reject the product concept. The original persona note stays in backlog
for a future semantic contract capable of reputation, disguise, bluff and claimed
capability. The 3/3 real-persona adjudication and deterministic witness clamp remain.

### Phase 5 — Registry article (WITH measurements) — ✅ COMPLETED
Case No. 16 records every retained and rejected result, the Phase 4 5/8→4/8
negative, the 3/3 real-persona boundary, the witness clamp and observed gate cost.

## General Acceptance Criteria — final verdict
- [x] Lazy dyadic scalar substrate with deterministic gravity and band projection. (F1)
- [x] Band readable by blind critic in ≥2/3 candidate axes. (F2)
- [x] Directional delta tracks provocation and gravity restores. (F3)
- [x] Number (0–1) never appears in Character/prose prompts. (F1/F2)
- [x] Boldness decided by curl and kept out of persisted substrate. (F3.5)
- [ ] Persona public=prior / dyadic=posterior realized. **Measured negative:** 5/8
      then 4/8; implementation removed. Witness-only revision did pass. (F4)
- [x] Evidence article No. 16 records measurements and reservations. (F5)

## Project Invariant (the reason for complexity)
Each axis/feature added passes the razor (blind judge names the end of the axis from prose) OR is cut. Complexity without observability is decoration. This is what separates this substrate from a "personality vector" that bloats until nobody can measure it.
