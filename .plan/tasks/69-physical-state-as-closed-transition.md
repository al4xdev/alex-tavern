# Task 69 — Physical state as a closed transition

> **Status:** open. **Wave 2, first.** This is the residual restaging — what is
> left after the previous phase closed every *code loop* that fed the Director
> the same input twelve times.
>
> The first draft of this task cited evidence that does not survive audit. Both
> the bad evidence and the good evidence are below; do not let the bad one back
> in.

## Problem

The Director re-proposes physical events it has already resolved.

`8bd4d0f1` (`base-P1-r2`), verbatim from `perception_events`:

| turn | event |
|---|---|
| T33 | `physical_outcome` — "O teto da câmara oculta desaba com um estrondo, abrindo um buraco de onde a névoa verde jorra…" |
| T34 | `observation` — "O teto da câmara oculta desaba com um rugido, abrindo um buraco por onde um jato espesso de névoa verde dispara…" |
| T35 | `physical_outcome` — "O teto da câmara oculta desaba com estrondo, e um jato espesso de névoa verde dispara pelo buraco…" |

Liora dies at T36, T37 **and** T38. The pillar collapses at T28 and T29. The
hidden duct is "revealed" six times. In `null-P1-r1` — roteiro **off** — the
green gate closes "com um baque surdo" at T18, T19 and T20 and Link's
disqualification is announced on all three. **No cell escapes this**, which rules
out the roteiro as the root cause.

Contradiction is worse than repetition. Once Liora has died twice, the reader
stops assigning weight to anything, including the next death.

## Evidence that the advisory channel does not prevent it

**This is the citation to use.** In the Director's own prompt at T34 of
`base-P1-r2`, the `Physical facts` block already contained:

```
"câmara_oculta": "teto desabou, buraco aberto", "entrada_câmara": "soterrada"
```

and the Director then emitted *"O teto da câmara oculta desaba com um rugido…
enquanto a entrada fica soterrada por blocos."* Same at T35. This is the
**post-R0 engine**, with no mandatory `UPCOMING EVENT` injection on those turns.
The state channel said the ceiling had already fallen, in the same message, and
the Director staged it again.

### The evidence the first draft used, and why it is withdrawn

The draft cited: *"`main_doors: trancadas` was in `physical_facts` from T11 of
`base-r1` and the Director re-sealed the doors seven times."* Two problems:

1. **The session is not on disk.** `main_doors` appears in **zero** files under
   `plans/artifacts/`. It came from an unarchived round-1 run.
2. **That effect already had a known cause, and it was fixed.** Case 20
   established that the terminal-act loop injected byte-identical text as a
   MANDATORY `UPCOMING EVENT` twelve times, and its own words are *"the
   doors-sealing cluster is a subset of the injection turns… the mandatory
   instruction won, correctly."* Using it to prove the state channel fails is
   re-attributing an effect to a cause that was not responsible.

## The input contradiction nothing currently addresses

At T33, T34 and T35 the ROTEIRO block of the same prompt carried, together:

> `Current beat: O teto da câmara oculta desaba de repente, abrindo uma nova
> fonte de névoa…`
>
> `Not in play yet — introduce as concrete perception events: pedras do teto
> desabado, entrada soterrada da câmara, gritos de alunos próximos`

The prompt asserts *"this is the current beat"* and *"this is not in play yet"*
about the same event, in the same message, while `physical_facts` says it has
already happened. The anchor matcher cannot close the beat because
"pedras do teto desabado" does not lexically match "O teto da câmara oculta
desaba", so coverage never completes and the turn clock forces a replan that
regenerates the same standoff.

**Closed transitions constrain the output. Nothing here reconciles the input.**
A task that only guards the output will be fighting a prompt that is still asking
for the event.

## Why not semantic similarity

`docs/cases/21` recommends durable memory plus **semantic comparison** applied to
the Director. Right target, wrong instrument, for two reasons:

1. **Similarity cannot separate escalation from repetition**, and escalation is
   the engine of a story. "The pillar cracks" → "the pillar collapses" is
   progress.
2. The advisory version of the state channel has now been measured failing
   (T34 above). Making it *louder* is the same class of fix as the reverted
   `602e562`.

A closed transition distinguishes them by construction: a ceiling that is
`desabado` cannot transition to `desabado`; it can transition to
`escombros removidos`. A door that is `trancada` cannot become `trancada`; it can
become `arrombada`.

**One measured caveat against my own argument:** the audit found that at
`CLUSTER_TAU = 0.6` the existing lexical clustering *did* catch the ceiling
restaging, and produced **zero** escalation false positives across `base-P1-r2`'s
16 clusters. So lexical detection is more capable than this task assumed. That
strengthens the *scanner* (task 68) but not the *runtime guard* — an offline
metric may accept a false positive rate that a guard blocking the Director's
output may not.

## Also in scope

- **`burst.event_texts` dies every submission** (`runner.py:1163-1169`). It only
  exists `if multi_beat`, so cross-submission re-proposal has no barrier at all.
  A durable equivalent is part of this task.
- **`scene.physical_facts` saturation.** Re-derived from `metrics.json`
  2026-08-05: **4 of 12 P1 runs finished pinned at the 40-key cap** — `base-r2`,
  `base-r3`, `drive-r1`, `drive-r2`. (The archive also shows the cap is the
  *current* engine's: `oldcode-P2-r1` and `-r2` finish at 70 and 59 keys.) Closed
  transitions will live in that same bag, so measure what gets evicted **before**
  building on it. Case 20 called fact churn "no harm observed"; a blind reviewer
  argued the harm is visible and misattributed. The low-salience entries that get
  evicted are exactly the ones worth keeping.

- **This task owns the durable-state storage decision for the phase.** Added
  2026-08-05. Tasks **72** (commitments) and **66** (possession) both want durable
  state, and 66 says outright that possession *"should reuse [69's machinery]
  rather than build a parallel one"*. 69 builds first, so 69 decides — the shape,
  where it lives, and what happens at the cap — and writes it down here as an
  interface the other two consume. Three tasks each inventing their own store,
  on top of a bag that is already evicting, is the most expensive mistake
  available in this phase.

## Closure evidence required

- [ ] a re-proposed transition into a state already held is rejected or corrected
      deterministically, with a test per transition family;
- [ ] a genuine escalation is **not** blocked — the T28→T29 pillar pair and a
      seeded crack→collapse both pass;
- [ ] the input contradiction is closed: a beat whose anchors are already
      satisfied cannot be re-issued as "not in play yet";
- [ ] cross-submission coverage: the same event proposed in two consecutive
      submissions is caught;
- [ ] eviction instrumented before any state is trusted to persist;
- [ ] the storage model written down here as an interface, **before** 72 or 66
      designs against it;
- [ ] measured on a live cell: the ceiling-family cluster does not recur, judged
      with the fixed `cluster_max`/`cluster_span` from task 68 and a blind read
      (`NSR` is reported, not a gate — `.plan/ROADMAP.md`);
- [ ] `docs/cases/21`'s semantic-comparison recommendation answered in writing —
      either adopted after this ships, or refused with the counterfactual.

**The measurement that would falsify this task:** if closed transitions land and
the restaging cluster count does not fall, the state model is not the mechanism
and the production mandate (task 72) is carrying all of it.
