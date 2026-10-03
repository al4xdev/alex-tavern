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

**Task 69 update, 2026-09-24:** a manually written contradiction report on
the archived T38 Director draft gave 4/4 coherent full-draft retries versus
0/4 with generic feedback; all eight passed the current JSON schema and a
blind reader inspected the full draft. This is local steerability after a
human supplied the blocked-gate diagnosis, **not** an automatic producer or
detector. A later independent reporter screen tested that boundary and failed,
as recorded below. See
`plans/artifacts/69-closed-transition-contract/T38-MANUAL-RETRY-RESULT.md`.

**Task 69 update, 2026-09-25:** the independent reporter screen is incomplete
(21/28 technically valid); its valid archived responses missed the kennel
repeat and left T38's separate repeated closure out of the report. It cannot
yet supply the manual correction. See
`plans/artifacts/69-closed-transition-contract/WHOLE-DRAFT-REPORTER-RESULT.md`.

**Task 69 update, 2026-09-25:** the Director-authored gate-proposal screen
exposed repeated closures with matching tags in blue T38, but one kennel T34
proposal quoted an event absent from its draft and another labelled ongoing
sealing as a new aperture closure. Public actor attribution also failed.
This selected eight-draft screen is incomplete under its frozen technical
rule; no producer or automatic retry follows. See
`plans/artifacts/69-closed-transition-contract/DIRECTOR-PROPOSALS-RESULT.md`.

**Task 69 update, 2026-09-25:** a counterfactual authoritative-transaction
screen got expected ordered gate operations on four outcome-specified scenes,
but its V2 final prose had two invalid envelopes and one valid narration that
re-opened a gate already open at beat start. A different narration supplied an
unconfirmed earlier ice seal. The technical gate and whole-prose fidelity
failed locally; no runtime producer or reliability claim follows. See
`plans/artifacts/69-closed-transition-contract/AUTHORITATIVE-TRANSACTION-RESULT.md`.

**Task 69 update, 2026-09-25:** a renderer time-packet A/B reused four fixed
Director transactions. The B packet passed the local narration schema in
16/16 preserved outputs (A 12/16), but a blind fiction read found unconfirmed
recently melted ice in B, plus unsupported trees at the tunnel gate. A
second reader disputed stronger spatial contradiction labels. English prose
appeared in both arms because the fixture omitted the shared client's
language instruction; its counts are not a candidate language result. The
registered content gate failed. No runtime
renderer packet or physical-state producer follows; the fixture supplied
the viewer roster directly, so production-cluster occurrence is unproven. See
`plans/artifacts/69-closed-transition-contract/RENDERER-TIME-PACKET-RESULT.md`.

**Task 69 source check, 2026-09-25:** archived `ea6620fb` T12 confirms Bruna
crossing into a new corridor while its real prose prompt omits her from the
post-move present-action roster. The actual narration nevertheless includes
her crossing. A content critic read this as unresolved beat-time wording,
not a proven instruction contradiction or fiction failure. See
`plans/artifacts/69-closed-transition-contract/T12-BRUNA-RENDERER-BOUNDARY-FINDING.md`.

**Task 69/80 source check, 2026-09-25:** `d5a2ccf0` T6 confirms Garran
crossing into a corridor. Raw prose narrated it; persisted prose lost its
first sentence and begins with an orphan `ele`. Replaying the current
offstage filter on the raw text returns the persisted text exactly, and a
fiction-only reader judged the crossing materially lost. This is one real
deterministic failure at the post-move renderer boundary, not a rate. See
`plans/artifacts/69-closed-transition-contract/T6-GARRAN-CROSSING-STRIPPED-FINDING.md`.

**Task 69 update, 2026-09-25:** an actual T6 prose replay compared current
post-render filtering with a time-scoped instruction and mover exemption.
All eight curls passed schema. Blind reading found the named crossing in
current-filter prose 1/4 and in candidate prose 4/4, but the candidate also
narrated Garran after reaching a corridor outside the origin audience. Its
registered content gate failed; no runtime change follows. See
`plans/artifacts/69-closed-transition-contract/T6-TRANSIT-EXEMPTION-RESULT.md`.

**Task 69 content check, 2026-09-25:** simple concatenation of T6's three
origin-witnessed event texts preserves the crossing and pronoun antecedents,
but a fiction-only reader found it too abrupt for finished prose. Event-local
reader-ready narration is a candidate to test, not a validated solution. See
`plans/artifacts/69-closed-transition-contract/T6-EVENT-UNITS-READ.md`.

**Task 69 update, 2026-09-27:** the T6 event-local reader-unit screen retained
Garran's named crossing in four joined outputs. Its registered content gate
failed: one output omitted the block's confirmed several-metre roll, another
omitted Elowen's stabilization prayer. A reader also noticed repeated dust
and lamp imagery across units. The mover binding was manual and only the
origin view was tested. No runtime producer follows; see
`plans/artifacts/69-closed-transition-contract/T6-EVENT-LOCAL-RESULT.md`.

**Task 69 update, 2026-09-28:** a real-source typed-transaction producer
screen failed its frozen gate. Blue T38 produced no mechanically accepted
final chain in four tries, including two schema-invalid first outputs; a
rejected draft hid Téo's crossing in untyped text. Legal T8 kept the main
gate opening in four mechanically valid outputs but omitted or changed
Maelis/Garran material in three raw Director step lists. Character speech
was not generated for those candidates. The assembler also had a deterministic
grammar defect, so its awkward gate sentences are not model-quality evidence.
No runtime producer follows; see
`plans/artifacts/69-closed-transition-contract/REAL-TRANSACTION-PRODUCER-RESULT.md`.

**Task 69 physical-only screen, 2026-09-28:** source-grounded T38 gate/attempt
labels matched in 4/4 calls without the rejected draft and 4/4 with it; the
legal T8 opening matched in 4/4. This tests a manually identified single gate
and actor, not event prose or an integrated producer. Next test whether full
Director drafts respect those labels while retaining scene content. See
`plans/artifacts/69-closed-transition-contract/PHYSICS-ONLY-DRAFT-AB-RESULT.md`.

**Task 69 full-draft follow-up, 2026-09-28:** eight real T38 retries were
technically valid but 0/4 coherent in both generic and three-label arms.
The label arm kept Téo in the hall after a blocked attempt, yet all four
drafts still restaged the completed T37 blue-gate closure. The isolated
physical selector is therefore insufficient as complete-draft feedback; no
runtime producer follows. See
`plans/artifacts/69-closed-transition-contract/T38-LABEL-CONDITIONED-RETRY-RESULT.md`.

**Task 69 event-delta follow-up, 2026-09-28:** a direct T38 A/B differing
only by `aperture_delta=none` left two of four B drafts re-closing the
already sealed gate; two did not. The four A drafts re-closed it. A T8
legal-opening packet produced one malformed JSON response, so the all-12
technical gate failed; two of its three valid Director rewrites omitted
shield handling, and one omitted Maelis's proposed speech intent while
still routing her. No Character call ran. These readings are diagnostic, not an admitted
full-draft contract. See
`plans/artifacts/69-closed-transition-contract/EVENT-DELTA-FEEDBACK-RESULT.md`.

**Task 69 boundary, 2026-09-28:** code review found durable physical state
bootstrapped and validated but not applied from Director proposals. Its free
event text still feeds prose, so state labels by themselves have not closed
reader-visible contradictions in the local screens. A selected-source
inventory of T38/T8/T6 plus conversational T23 frames a possible full-event
program feasibility test; that architecture is a hypothesis, not admitted
runtime work. See
`plans/artifacts/69-closed-transition-contract/SEMANTIC-PROGRAM-COVERAGE-INVENTORY.md`.

**Task 69 hand-bound screen, 2026-09-28:** four selected event programs
(T38/T8/T6/T23) rendered once under a frozen template grammar, then were
read for continuity and fiction. The continuity reader accepted the
obligations supplied for all four, but T6's far-side position was outside
that packet. The fiction reader rejected all four as finished RPG prose;
repetition, dialogue pre-announcement and checklist cadence were visible.
This exact pair fails the registered gate. Neither model-program production
nor complete event coverage was validated; no runtime implementation follows.
See `plans/artifacts/69-closed-transition-contract/SEMANTIC-PROGRAM-FEASIBILITY-RESULT.md`.

**Task 69 T38 follow-up, 2026-09-28:** the program × style-reference
curl screen failed its all-valid gate (15/16) and had three clear
counterfactual L transition/order errors: two newly opened an already
ajar gate and one closed before Téo crossed. All eight S outputs avoided
new closure and crossing locally, but most were rejected as finished
fiction. In a separate one-shot packet-only authoring screen, the
continuity reader accepted both S and L, while the fiction reader
rejected S as report-like and accepted L. One author cannot establish
impossibility; neither candidate enters runtime. Task 69 remains open.
See `plans/artifacts/69-closed-transition-contract/T38-PROGRAM-STYLE-CROSS-RESULT.md`
and `T38-CONSTRUCTIVE-PACKET-RESULT.md`.

**Per-viewer guard correction, 2026-10-01:** when every sentence in a
cluster's prose was filtered as offstage, `render_narration` restored the
entire raw draft. It now returns empty; a split-turn integration test
confirms the Runner persists no narration record for that cluster. This is
a deterministic boundary repair with no measured live frequency, and T6's
witnessed crossing stripped from mixed prose remains open. See
`plans/artifacts/69-closed-transition-contract/OFFSTAGE-EMPTY-FALLBACK-RESULT.md`.

| task | where | state |
|---|---|---|
| **79** blocking as durable state | `tasks/` | **Cheap half SHIPPED.** Blocking reaches the prose renderer, filtered per cluster, nothing persisted. The **schema bump is deferred** — see `para-o-dono/79-blocking-shape.md` for the owner's answers and the re-pricing |
| **69** physical state as a closed transition | `tasks/` | Schema-16 durable storage and deterministic fixtures exist; **no model producer**. T29 gap remains unscored. Source reads found T32's persisted contradiction, T37→T38's repeated blue closure and a separate kennel-gate session with persisted closure at T33/T34/T35. In T38, deleting the closure event alone leaves a repeated crossing; its real request contains a closed gate, a stale all-open fact and Téo's unresolved crossing intent. Changing only the stale fact did not remove closure repetition in the B arm of a real-payload replay (4/4); the causal contribution remains undiagnosed, and the replay used only minimal JSON validation. Blue-gate duplicate and action-only screens failed semantic gates. Manually bound admission (86/88 valid) exposed wrong-gate extraction and checker acceptance of inadequate offered support. Support-only and context A/B checker runs were incomplete. A two-channel checker passed 32/32 technical calls but failed its semantic gate on correction/reopening sequences. A two-stage screen passed 52/52 technical calls and handled correction versus reopening, but admitted antecedent-free T37 evidence for the blue gate in Stage A. The later identity/aspect screen was incomplete (33/36) and again bound an ungrounded or competing `o portão` to blue. Content readers disagree on the longer T37 offer's anaphora; it is not calibrated ground truth. T23's alleged early reveal was withdrawn after its time-skip event was found in the real prose request. No prevalence estimate or runtime change. See `plans/artifacts/69-closed-transition-contract/T38-STALE-FACT-AB-RESULT.md` and `IDENTITY-ASPECT-RESULT.md` |
| **64** return control | `tasks/` | Calibration corrected the historical denominator; a contract-wording screen stopped below its technical-validity gate, so no wording shipped. A T11 source read found the boolean's named-person criterion has no target field even when its scene addresses NPCs and control goes to Link. Handoff quality remains unjudged by an interactive reader. See `plans/artifacts/64-return-control-calibration/` |
| **77** the order nobody executes | `tasks/` | **Open research.** Three cited passages and one reconstructed candidate were read as fiction. Historical 13/33 is uncalibrated and its selector unrecovered; explicit reconstruction finds 27/15, with neither count estimating defect prevalence. Cause unknown; see `plans/artifacts/77-content-audit/REPORT.md` |
| **72** commitments as state | `tasks/` | Gated on "do stalls survive 69" |
| **80, 81, 82** narration/state findings | `backlog/` | Opened out of 79's and 69's method sections. **80** spatial omission hypothesis, former n=40 judge baseline withdrawn; **81** has T32's source-checked creature-state/prose contradiction and T35 Liora crossing persisted one beat before her zone changed, both one-case observations with mechanism undiagnosed; original actor, T29 gap and T23 early-render candidates remain withdrawn; **82** a Director event that reached nothing (n=1) |

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
