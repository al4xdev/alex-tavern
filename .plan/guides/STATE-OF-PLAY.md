# State of play — handover, 2026-08-14

> **Update, 2026-09-05:** the first proposed acceptance measurement below had
> a broken identity contract. All 40 judge targets were IDs, not names; 35/40
> is withdrawn as a canonical-name baseline. The paired reconstruction and
> manual read are in `plans/artifacts/79-reader-identity-audit/REPORT.md`.
> Task 79's current-turn blocking implementation remains; quality acceptance
> is open. Task 80 loses that quantitative support, and task 81's quoted
> movement of Link was actually Asword's. Historical text is retained below.

**Content follow-up, 2026-09-05:** isolated literary readers and a paired prose
comparison retain concrete strengths and continuity concerns without assigning
a quality score. Garran stands before being described as “ainda de joelhos”;
the beam crossing leaves membership of “o grupo” unclear. Task 79 acceptance
remains open. See `plans/artifacts/79-content-read/REPORT.md` and
`plans/artifacts/79-content-comparison/REPORT.md` for passages, source checks and
the comparison's missing and schema-invalid responses.

**Read `GUIDE.md` first (it is the hour before `AGENTS.md`), then this.** That one
teaches you the place. This one tells you where the work actually stands on the
day it changed hands, what is true, what only looks true, and what to do next.

Written by the outgoing agent. **Everything below that is a claim carries its
status.** Where I got something wrong and found out, the wrong version is still in
the task file with the correction next to it — that is deliberate and it is the
single most useful property of this record.

---

## The one-paragraph version

The phase is **immersion**. Wave 1 shipped. Wave 2 is `79 → 69 → 64 → 77`, and
**79's cheap half shipped on 2026-08-13**. The phase has produced **many measured
symptoms and very few confirmed mechanisms**, and that asymmetry is the finding
the checkpoint is organised around. Seven causal stories were falsified here in
two days, **every one of them by reading records, none by a number looking
wrong.** Expect to falsify yours too; the record is built so that costs you an
afternoon instead of a week.

## What is actually TRUE, with the strongest evidence for each

| | status | evidence |
|---|---|---|
| Narration renders per perception cluster and the cross-cluster leak is closed | **MEASURED** | 16/29 → 3/78, and **0 of 48** on the post-79 cell |
| The Director writes blocking into `scene_blocking.character_zones` and the engine used to discard it | **MEASURED** | `narrate()` popped it; it now reaches the prose renderer |
| Historical visibility read found prior events still in the prompt | **OBSERVED; causal exclusion withdrawn 2026-09-05** | Visibility is not use. The completed session-cohort read leaves capacity/attention undiagnosed; see `plans/artifacts/69-session-cohorts/REPORT.md` |
| The Director does not narrow audiences; the engine's clamp does all of it | **MEASURED** | median `witness_ids` is **95% of the cast**, n=4,843 |
| Historical P3 “active player” comparison | **ACTION INTERPRETATION WITHDRAWN, 2026-09-14** | P3's declared physical actions were dispatched as skips; the two logs retain steering speeches, whose effect the dispatch audit does not evaluate. Old positional rates do not measure response to the unsent actions. See `plans/artifacts/77-p3-input-dispatch/REPORT.md` |
| Restated orders sit on frozen scenes no more often than any other turn pair | **MEASURED** | 36/39 vs a 184/213 control, Fisher p = 0.43 |

## What is NOT true, though the record used to say it was

**Read this section before you quote any number from this project.**

- ~~"A third of all movement is repositioning inside a room"~~ — **the detector matched at building level.** Every zone is `Academia Real do Primeiro Sino, <somewhere>`, so a walk to the outer courtyard scored as repositioning. Corrected 37.6% → **16.7% pooled, median 5.6%, 12 of 27 sessions at zero** — and then the accepted set was read and it is only **60-80% precise**, clustered onto a handful of turns. **It is not a rate.**
- ~~"Nothing can measure room-versus-position"~~ — over-reach, killed by three critics. **Four instruments were tried and each failed differently.** That is a statement about four attempts.
- ~~"The Director writes blocking in 1188 of 1188 calls"~~ — **tautological.** The field is in the schema's `required[]`. The load-bearing number is the 8.4% of entries that are positional.
- ~~"Nothing is being forgotten"~~ — presence in a prompt is not use.
- Nearly every **p-value** produced before 2026-08-12 was withdrawn for pooling turns instead of sessions.

## The traps, in the order you are likely to hit them

1. **Any test of the shape "is A part of B" over model-authored place names is measuring a naming convention.** Five registered false positives, **three of them this same failure**, the most recent written by someone who cited the earlier one in the same file. Substring, prefix, suffix and token overlap are one trap, not four.
2. **A metric that has never announced its own error is not validated.** Every real finding here came from reading flagged cases. Not one came from a number looking wrong.
3. **The session is the unit.** It costs an order of magnitude of effective n when you forget, and it is the most expensive mistake in this repo's history.
4. **Pre-register the decision rule, in the unit you will analyse.** One experiment here registered its gate in *runs* when the unit was *payloads*, and the design could not have returned a positive result — nobody noticed until a critic recomputed it.
5. **`ruff format` is not clean on this repo and never has been. The gate is `ruff check`.**
6. **Inspect `debug.jsonl` at the boundary relevant to the claim.** The raw Director response shows its proposal; the actual consumer request shows what that consumer received. In bb72dc94 T9, `time_skip_summary` says “Os alunos formam grupos hesitantes e começam a se mover em direção à rota de serviço”. Runner materializes it as a fifth prose event. Reading only the four original `perception_events` falsely attributed the grouping to renderer invention. State is also downstream of clamps; none of these records substitutes for every other boundary.
7. **Prompts may not contain em dashes or en dashes.**

## Where the work is

| task | where | state |
|---|---|---|
| **79** blocking as durable state | `tasks/` | **Cheap half SHIPPED.** Blocking reaches the prose renderer, filtered per cluster, nothing persisted. The **schema bump is deferred** — see `para-o-dono/79-blocking-shape.md` for the owner's answers and the re-pricing |
| **69** physical state as a closed transition | `tasks/` | Schema-16 durable storage and deterministic fixtures exist; **no model producer**. Two earlier local proposal screens met narrow fixture rules; T29 gap stayed unscored, and the second covered one hall gate. Source reading found T32's persisted physical contradiction, T37→T38's blue-gate closure repeated across a time skip, and a separate kennel-gate session with persisted closure at T33/T34/T35. The blue-gate duplicate and action-only screens then failed semantic gates despite 16/16 valid calls each. A 12-turn purposive retry read supplies no prevalence or retry-causation claim; its T23 early-render verdict was withdrawn after the omitted time-skip event was found in the real prose request. The retry replay (7/8 valid) and curated fidelity-reader screen (6/12 valid) were incomplete. No runtime change followed. See `plans/artifacts/69-closed-transition-contract/T34-T35-KENNEL-GATE-REPEAT-FINDING.md` |
| **64** return control | `tasks/` | Calibration corrected the historical denominator; a contract-wording screen stopped below its technical-validity gate, so no wording shipped. See `plans/artifacts/64-return-control-calibration/` |
| **77** the order nobody executes | `tasks/` | **Open research.** Three cited passages and one reconstructed candidate were read as fiction. Historical 13/33 is uncalibrated and its selector unrecovered; explicit reconstruction finds 27/15, with neither count estimating defect prevalence. Cause unknown; see `plans/artifacts/77-content-audit/REPORT.md` |
| **72** commitments as state | `tasks/` | Gated on "do stalls survive 69" |
| **80, 81, 82** narration/state findings | `backlog/` | Opened out of 79's and 69's method sections. **80** spatial omission hypothesis, former n=40 judge baseline withdrawn; **81** has T32's source-checked creature-state/prose contradiction, mechanism undiagnosed; original actor, T29 gap and T23 early-render candidates remain withdrawn; **82** a Director event that reached nothing (n=1) |

**All three of 80-82 are n small and uninvestigated on purpose.** They are
candidate findings, not defects, and each says in its own file what would kill it.
**82 is the one with the cheapest test** — counting events that produce no speech,
no narration and no fact update is mechanical, needs no judge, and needs no string
matching over names, which makes it almost unique in this corpus.

## What I would do first, in your place

1. **Repair and validate the acceptance read before evaluating 79's quality.** The former **35/40 baseline is withdrawn (2026-09-05)**: all targets were IDs. A paired name-corrected reconstruction still produced wrong-actor and movement-category errors. It is a diagnostic, not a new baseline. Use canonical names and per-viewer narration, and distinguish useful staging from invented movement. **No `zone_moves` rate is a gate for this change.**
2. **69's storage boundary exists; its model producer remains open.** The hall-gate source screen classified one existing aperture on three turns in one session, but T29's newly shaped rubble gap remains unscored and dynamic entity creation untested. T32 demonstrates a persisted proposal/prose physical conflict; T37→T38 supplies a completed blue-gate closure repeated across a time skip. A separate kennel-gate session persists closure on T33, T34 and T35 with no intervening reopening; T37's additional proposal is absent from that viewer's prose. The blue-gate duplicate and action-only shapes failed their local semantic gates, and T23's apparent early-render defect was withdrawn when its accepted time-skip event was found in the real prose request. The purposive retry read does not establish mechanism or prevalence, and the single-payload replay was incomplete and did not validate a fix. The earlier cohort and ceiling replays still do not exclude capacity as a cause. See `plans/artifacts/69-session-cohorts/REPORT.md` and `plans/artifacts/69-closed-transition-contract/T34-T35-KENNEL-GATE-REPEAT-FINDING.md`.
3. **64's wording candidate stopped at technical validity.** Keep the calibration result; a new wording experiment needs a newly registered question, not another call under the failed gate.

## How to decide things without the owner

The owner's standing instruction, 2026-08-13: **dispatch critics, do not queue the
question.** Three fresh subagents in parallel with *different framings* — one told
to demote, one asked only "would the record be worse without this", one given the
numbers with the prose stripped out. Take the **harshest** verdict as the one to
answer and record that they split.

It works. The three run on 2026-08-13 caught: an over-reaching universal claim, an
audit that had read only one side of its classifier, an agreement figure that was
arithmetically below chance, a pre-registered gate specified in the wrong unit,
and an untried instrument that this project's own rules name by name. **None of
that came from the numbers looking wrong.**

What still goes to the owner: schema changes, graph changes, roadmap re-orders,
anything irreversible, and anything where the missing input is a *preference*
rather than an argument.

## ⚠ What a clone does NOT give you

**The repository is not the whole record.** Cloning gets you every document, every
test, and every analysis script. It does **not** get you the evidence.

| | travels? | where |
|---|---|---|
| all of `.plan/`, `docs/cases/`, `AGENTS.md`, tests, `src/` | ✅ | git |
| **the analysis scripts and hand-read dossiers** | ✅ **as of 2026-08-14** | `plans/artifacts/**/*.py` and `*.md`, newly un-ignored for exactly this reason |
| archived metric outputs, blind reads, `immersion-scan.json` | ✅ | `benchmarks/`, 2.1 MB, committed |
| **the 33 recorded sessions — every `debug.jsonl` and `state.json`** | ❌ | `plans/artifacts/**/sessions/`, **1.8 GB, local only** |
| replay outputs (`runs/`, `blind_read/`) | ❌ | same |
| the provider key | ❌ | `.data/config.json`, correctly ignored — never commit it |

**Consequence, and it is the important one: without the sessions you cannot
re-derive a single number in this record.** Every measurement here reads
`debug.jsonl` directly. The scripts will run and find nothing.

**If you are moving machines, copy `plans/artifacts/` across separately** (rsync,
external disk, whatever) *before* you conclude that a number cannot be reproduced.
If it is genuinely gone, say so in the file that quotes the number rather than
re-deriving it from a smaller corpus and quietly changing the figure — the record
already carries several corrections and one more honest gap is cheaper than a
silent restatement.

**`benchmarks/` is the fallback.** It is committed and it holds the archived
battery outputs and blind reads, so the *conclusions* remain checkable even when
the raw sessions do not.

## One housekeeping fact you need

**This repository was edited by two agent sessions at once on 2026-08-12 and
2026-08-13**, and it produced a working tree that twice reverted to a pre-commit
state, byte-identical, with no git operation in the reflog. It is written up in
`DECISIONS-2026-08-12-EVENING.md`, entries 22, 24 and 25. **Commit in small
pieces, check `git diff --cached --stat` before every commit, and use an explicit
pathspec** — that habit is the only reason nothing was lost.
