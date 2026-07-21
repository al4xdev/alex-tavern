# Characters that change: a governed disposition substrate, and the number the model never sees

> **Measured outcome:** this article is the frontier definition. The completed
> gates and narrower shipped contract are recorded in
> [Case No. 16](./16-disposition-substrate-measured-verdict-2026-07-21.md):
> Trust/Warmth survived, Composure was cut, and the proposed public-prior reuse
> failed 5/8 then 4/8 and did not ship.

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 15 |
| **Date** | 2026-07-20 (design / frontier definition — no measurements yet) |
| **Kind** | Forward-looking theory + roadmap frame (cf. No. 12, scene-state theory) |
| **Roadmap** | Closed Task 43 (`.plan/closed/43-character-disposition-substrate.md`) |
| **Predecessors** | No. 11 (scene stagnation), No. 12 (state-transition theory), No. 13 (watcher battery); Tasks 29.2 (subjective state), 39 (ledger memory), 41 (omniscient Director) |
| **Related design note** | `.plan/backlog/player-persona-public-vs-real.md` (public vs real persona) |
| **Status** | This article DEFINES the frontier the next roadmap explores. It states the discipline and the falsifiable claims; it does not yet report measurements. The article of record with evidence is written at the end of the roadmap (Phase 5). |

## Abstract

Today a character is a **static sheet**: personality, knowledge, a free-text
`current_mood`. Nothing about them *drifts* as the story runs. The frontier this
roadmap opens is **characters whose dispositions change over the arc** — trust
that erodes, warmth that turns, composure that shatters and slowly returns — in a
way that is (a) seeded at character creation, (b) measurable and persisted, and
(c) actually legible in the prose. The obvious implementation — give the model a
`trust: 0.7` field and ask it to act 70% trusting — does not work, and we already
have the evidence pattern for why (No. 13: the model honors qualitative bands and
directional deltas, not scalars it is asked to introspect on). This article
states the one discipline that makes the idea shippable — **the scalar belongs to
the code; only a qualitative band is ever shown to the model** — and the one razor
that keeps it from metastasizing into a psychology textbook: **an axis earns its
place only if a blind reader can name its pole from the prose alone.**

## 1. The frontier: from a sheet you read to a state that moves

The engine already models *what a character knows differently from another*
(perspective ledgers, 29.2) and *what the world knows omnisciently* (41). What it
does **not** model is *disposition that moves*: a character's stance toward
another, and their inner weather, as governed, drifting state rather than a
one-shot personality blob. The dramatic payoff is exactly the thing a static
sheet cannot give — a relationship that *becomes* hostile on-screen, a nerve that
*frays*, a trust that is *earned* and then *broken*.

## 2. The central discipline: the scalar is the code's, the band is the model's

This is the whole design in one sentence, and the reconciliation of an apparent
contradiction (an earlier session established "the model won't honor a 0–1
credence field"; this roadmap wants 0–1 values). Both hold, because the number
and the model live on opposite sides of a wall:

- **The scalar (0–1) is owned by the CODE.** Deterministic, persisted, testable
  with zero model spend. It is what delivers the *measurable* half of the goal:
  seeding at preset, drift over the arc, thresholds, before/after comparison.
- **The qualitative band is what the MODEL reads and writes.** The character
  never sees `0.72`; it sees `"wary"`. It never *emits* a number; it emits a
  **directional delta** ("this turn broke my trust"), and the **code** integrates
  that delta into the scalar.

This is the exact division of labor that the watcher's delta auditor already
proved (No. 13): the model classifies a qualitative event, the code does the
arithmetic. The number buys measurement and memory; the band keeps the model
inside its competence. Break the wall — show the model the number, or ask the
code to judge tone — and the design collapses back into the failure mode.

```
  preset ──seeds──▶ [ scalar 0..1 ]  ◀──integrates delta── code
                          │
                     project ▼ (code)
                    [ band: "wary" ] ──shown──▶ character agent (prose)
                          ▲                              │
                          └────── directional delta ◀────┘ (model, qualitative)
```

## 3. The razor: complexity with reason, not complexity for its own sake

The failure mode of "character state vectors" is that they grow to twelve
psychological axes nobody can observe. The guardrail is a single, testable rule:

> **An axis earns its place only if a blind reader, given only the character's
> speech or action, can name which pole of the axis they are on.** If the axis
> does not change observable behavior, it is decoration — cut it.

This is not a slogan; it is a **curl acceptance test** (a blind critic guesses the
band from the prose; if they can't beat chance, the axis is dead weight). It is
how "complexity with reason" becomes falsifiable instead of aspirational.

## 4. The axis set (three, with a fourth on probation)

Passing candidates through the razor yields a minimal, dramatically load-bearing
set:

| Axis | Scope | What the blind reader observes |
|---|---|---|
| **Trust** (generalizes "faith"/credence) | per-dyad | acts on the other's word, lowers guard, shares a secret |
| **Warmth** (affection ↔ hostility) | per-dyad | tone, willingness to help, aggression |
| **Composure** (calm ↔ rattled) | global | speech rhythm, impulsivity — literally *the tone of the voice* |

Two disciplines keep this from exploding:

- **Global vs dyadic is a deliberate cut, not an accident.** Composure is global
  (I am rattled at everyone right now). Trust and Warmth are per-dyad (I trust her,
  not him) — and even these are **lazily materialized**: an `A→B` entry exists only
  where there is a live divergence. This single distinction kills the O(N²)
  prompt blow-up. (Per the owner's Phase-scope decision, dyadic is present from
  Phase 1, not deferred — but always lazy.)
- **Preset seeds, the story drifts, gravity returns.** Each axis carries three
  things: a **baseline** (seeded at creation — a personality has a set-point), a
  **current value** (moved by deltas), and a **gravity** (relaxes back toward
  baseline over calm turns — a shock knocks you off, then you settle). Preset-seed
  and dynamic-change do not fight: the preset sets the set-point, the story pushes
  and releases.

**Composure is not new surface — it disciplines existing surface.** The
`current_mood` free-text field is already a half-formed version of this; the
roadmap turns one governed slice of it into a measurable scalar. We are
formalizing something half-present, not bolting on a stranger.

**The fourth axis is an open empirical question, not a design commitment.** A
candidate — **Boldness/Resolve** (cautious ↔ reckless, global, observable in
action-attempts) — is deliberately *left out of the initial design* and instead
**settled by curl**: does a fourth band measurably change behavior a blind reader
can name, over and above the three? If yes, it earns in; if not, it is decoration
and stays out. Per the owner's decision, we design for three and let the fourth
prove itself.

## 5. Where the number moves: reuse, don't rebuild

The scalar changes via the machinery that already exists. The watcher's delta
taxonomy **already contains `relationship_changed`**; extending the auditor to
emit a *directional* relationship/emotion delta, which the code integrates, is
reuse of proven apparatus rather than a new subsystem. Frugality is itself a form
of "complexity with reason."

## 6. The unification: one axis, three problems

The strongest evidence the idea is right is that it collapses three separate open
questions onto one mechanism:

- **Public vs real persona** (`player-persona-public-vs-real.md`): the public
  persona is the **default prior** — what anyone is entitled to believe about a
  character. A dyadic entry is where a specific observer's belief **deviates** from
  that prior.
- **Per-dyad memory** (the "x1" memory idea): a Trust/Warmth dyad *is* the
  compact, drama-relevant slice of "what A believes about B."
- **"Faith" / credence**: Trust is exactly this — how much I act as if what I
  perceived about you is true, which is what lets a character be *fooled*.

Bayesian in shape, dramatic in meaning: **public persona = prior; dyadic belief =
per-observer posterior; the axis value = the strength of the deviation.** Three
problems, one eigenvector.

## 7. Grounding: this dilemma is old

The scientific literature is the owner's ground already; the fictional and
formal anchors:

- **Epistemic logic — knowledge vs belief.** A memory is a log; a *belief* is a
  credence that can be wrong. "Trust" is the doxastic modifier on a remembered
  perception (`K_A(K_B(p))` — nested belief — is the per-dyad case).
- **Rashomon** (Akutagawa / Kurosawa) — the canonical divergent memory of one
  event across observers; the literary form of the perspective ledger.
- **Kazuo Ishiguro** (*The Remains of the Day*) — a narrator who remembers
  accurately but *believes* wrongly: the Composure/Trust drift in prose.
- **Lisa Zunshine, *Why We Read Fiction*** — the claim that fiction exists to
  exercise 4–5 levels of nested intentionality ("A thinks B believes C wants…").
  The formal argument that per-dyad belief is not ornament but the engine of story.

On paper this is beautiful; in a language model it is treacherous — which is
precisely why the scalar/band wall (§2) and the razor (§3) are load-bearing, not
stylistic.

## 8. The roadmap (each phase cheap and independently testable)

Detailed in Task 43. The shape, and why it is *disciplined* complexity:

- **Phase 0** — this definition + article (done: you are reading it).
- **Phase 1** — the substrate: pure code, **zero model spend**. Data model,
  preset seeding, deterministic drift/gravity, dyadic-lazy from the start, the
  scalar→band projection. Fully unit-testable for free.
- **Phase 2** — projection into voice: inject the band into the character agent.
  Curl gate = the §3 razor (blind critic names the band from prose).
- **Phase 3** — the feedback loop: extend the delta auditor to emit directional
  deltas; code integrates. Curl gate: under scripted provocation, does trust
  *fall* and the band *flip*? does gravity restore it over calm turns?
- **Phase 3.5** — the fourth-axis experiment: curl-decide whether Boldness earns in.
- **Phase 4** — meets the persona note: the public-prior / dyadic-posterior
  unification made real.
- **Phase 5** — the article of record, with measurements — including, honestly,
  wherever the model turns out to be variance-bound (as the roteiro clock was).

Built for long-term correctness and validated empirically, not shaved for
per-call cost — which is the stated posture: a cheap frontier model means we
*spend* on validation, and design for the arc, not for today.

## 9. What would falsify this

Stated up front, so the roadmap can kill its own darlings:

- If a blind critic **cannot** name any axis's pole from prose (§3 fails for all
  three), the model does not honor the band and the substrate is inert — stop.
- If the directional-delta loop (Phase 3) is **too noisy** to integrate stably
  (trust random-walks instead of tracking provocations), the feedback half fails
  and the substrate degrades to a static, preset-only sheet.
- If lazy dyadic materialization still **blows the prompt budget** at realistic
  N, the per-dyad scope was wrong and Trust/Warmth must fall back to global.

Any of these is a legitimate negative result, recorded by method — the same
standard as No. 13 and No. 14.
