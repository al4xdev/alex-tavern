# ROADMAP — the immersion phase, on low heat

*Branch: `fogo-baixo`. Named for the way you cook something that is supposed to
take a while — slow because it is cooking properly, not slow because it is
stuck. The distinction is the whole point of the re-review below, and it is not
a joke about the engine's throughput: it is the acceptance criterion.*

**Opened 2026-08-02.** Supersedes nothing: the previous roadmap was a single
`ROADMAP.md` removed on 2026-07-20 in favour of distributed state, and that
removal was right for that phase. This file exists because a *phase* boundary
needs one place that says what the phase is and in what order it is being
attacked. Per-task detail still lives in `tasks/`, history in `closed/`, and the
reasoning in `docs/cases/`. **This file is an index and an ordering argument, not
a container.**

Close it when the last wave lands, and do not let it grow into the thing that was
deleted in July.

---

## The phase

Everything here is judged on one thing: **immersion**. Two things break it, in
this order:

1. **Repetition.** Beta testers report it is the number one thing that makes a
   human notice they are talking to a machine.
2. **Leaks.** A whispered secret reaching someone who did not hear it, a private
   thought becoming speech, an internal id in prose, the machinery becoming
   visible.

The previous phase closed one deterministic repetition defect and three smaller
ones on the same theme, each with a counterfactual against the pre-fix engine
(`docs/cases/20-repetition-baseline-2026-08-01.md`, batteries in `benchmarks/`).
What remains is a different problem, and this phase names it:

> **The engine cannot render a turn in which nothing happens, and it cannot
> record that anything has been settled.** Three rules make the first true —
> `perception_events` requires `minItems: 1`, prose must reach 150 words, and
> prose may not narrate stillness. Nothing at all makes the second true: there is
> durable state for *rocks*, and none for *what was already staged*, *who was
> refused*, or *what a character committed to*.
>
> So when a scene has nowhere to go, the Director invents somewhere and the
> renderer gives it a paragraph. Restaging is one symptom. A corridor where a new
> door opens every single turn is the same defect wearing better prose.

Alongside it, a second family that is pure leak: the Director writes speech it
should not write, the redaction guard mutilates public dialogue, narration has no
per-viewer projection, and the Director's prompt names the player's character.

Three of those four are scheduled below. The fourth — per-viewer narration
(task 71) — turned out not to be an engineering decision. It was parked until it
was answered as a product one, which happened on 2026-08-05: **narration renders
per zone-cluster**. It is now scheduled into wave 3, behind the zone-graph fix it
depends on.

## ⟳ Re-reviewed 2026-08-05 under the budget rule — what actually changed

`AGENTS.md` §2 now says cost, latency and backwards compatibility are cheap and
narrative quality is expensive. This roadmap was written before that was stated,
and six of its decisions were made partly on the cheap resource. They were
re-derived. **Four changed, two did not, and the two that did not matter as much
as the four.**

### 1. The checkpoint battery stops being n=3 — this is the biggest one

`benchmarks/README.md` §7 says it plainly: *"`RSR_prop`, `GUARD` — cells overlap
at n=3 — indicative only"*, and the within-`base` spread of `NSR` is **7× the
effect a task in this phase would be asked to produce**. Half the instrument
cannot decide anything, and **the only reason it is n=3 is that batteries cost
provider calls.**

That reason is gone. The checkpoint re-run goes to **as many replicates per cell
as patience allows** — and patience, not money, is now the limit. This is the
highest-value consequence of the new rule anywhere in the phase: it does not
improve one task, it upgrades the instrument every remaining task is judged with.
It also lets the blind read cover more sessions, which is the acceptance
instrument for everything narrative.

**Concretely:** the checkpoint's own definition changes from "re-run the P1
battery" to "re-run it wide enough that a within-cell spread is visible", and the
`oldcode` control cell is replicated too, or the comparison is still worth
nothing.

### 2. Task 63 stops shopping for the cheapest option

63 lists four fixes and says *"run 68's scanner first — if five events per
session would be dropped, option 4 ships; if it is twenty, it does not."* That is
choosing an architecture by how much content the cheap version destroys.

Under the rule there is nothing to shop for: **option 1, per-viewer projection,
is the correct one and the drop path is dead.** Redaction belongs in the render
for one viewer, never in the shared persisted record. It costs more work and
possibly more calls, and neither is a reason.

This also unblocks **task 59** earlier and more cleanly, since 59 is blocked
precisely on redaction moving to the per-viewer projection.

### 3. Task 71's singleton question was framed on the wrong axis

Recorded on 2026-08-05 as *"folding singleton clusters is the difference between
1.56x and 1.21x prose calls — the single biggest cost lever in this task."*
**Cost lever is not a reason to decide anything here.** The question is a quality
one and has to be re-asked as such: *does a lone character's own experience need a
narrated paragraph, when they already receive perception events and memory?*

The answer may well still be "fold" — but for being redundant, not for being
expensive, and the distinction decides what happens when someone later asks to
un-fold it.

### 4. Task 72's gate survives; the argument for it was half wrong

The gate is *"ships only if the checkpoint shows stalls survive 69"*, and that is
a falsifier — it stands. But the roadmap justified it partly with *"it is the
largest item in the phase"*, which is a cost argument and no longer counts. **The
gate stays, on the falsifier alone.** If stalls survive 69, 72 ships regardless of
its size.

### What did NOT change, and must not be "revived because cost is free now"

- **`material_delta_rate` stays unauthorised.** It was killed in task 68 because
  its premise was falsified — the lexical instrument *did* see the restaging and
  a reporting bug hid it — **not** because it was expensive. Evidence, not
  budget. Do not resurrect it on the grounds that the semantic judge is now
  affordable.
- **Task 69's 40-key cap on `physical_facts` needs the two arguments separated.**
  The cap bounds prompt growth, which was partly a cost concern (dead) and partly
  a **model-attention** concern (very much alive — a bigger prompt is a worse
  prompt long before it is an expensive one). 69 owns the storage decision, and it
  must say which of the two it is optimising. "Tokens are cheap" is not a licence
  to hand the Director an unbounded fact bag.

**The general form, for whoever reads this next:** the rule makes the *cheap*
option stop being an argument. It does not make the *expensive* option correct by
default. Every item above still had to be argued on quality.

### 5. Two new proposals the rule unlocks — and why the order does NOT change

The same day, two designs became thinkable that were previously priced out
(`.plan/backlog/74-orchestrator-agent-with-tools.md`,
`.plan/backlog/75-post-turn-critic.md`):

- **74 — an orchestrator with tools** instead of a fixed pipeline: an agent that
  reads the situation and fires the calls it judges necessary, including *none*.
- **75 — a critic at the end of the turn** that flags leaks or unfluent prose and
  triggers a redo.

**74 is the more serious of the two, because it is the only proposal in this
phase with a structural answer to the phase's headline defect** — "the engine
cannot render a turn in which nothing happens" is a property of a pipeline where
every stage always runs. It also raises a real subsumption question: tasks **64,
70 and part of 65** may all be symptoms of one cause, too many decisions in one
call and a pipeline that cannot choose.

**75 splits and half of it is already rejected**: leak detection belongs to the
scanners — deterministic, testable, free — and asking a model to find what a
regex finds converts a hard invariant into a probabilistic one. The fluency half
survives, with a falsifier.

**Neither changes the running order, and that is deliberate.** Wave 1's ordering
is derived from *measured damage*; 74 and 75 have proposals and falsifiers, not
measurements. Re-sequencing a phase around an unmeasured design is the exact
failure this roadmap has now recorded three times. Worse for 74 specifically: its
own case rests on defects that **wave 1 is about to attack**, so its evidence is
being changed underneath it right now.

What does change:

1. **The checkpoint gains two questions** — did wave 1 already fix what 74 claims
   the pipeline causes (a routed protagonist, a turn allowed to be quiet)? And
   does an offline critic see anything the scanners do not?
2. **Both proposals have a free offline experiment that can run BEFORE the
   checkpoint**, without touching the engine. 74's dispatcher can be run
   read-only over the archived turns and its *proposed* calls compared with what
   actually happened — the ten stalled turns of `base-P1-r2` T30–T39 are the
   direct test. 75's critic can be run over the twelve archived sessions and its
   ranking compared against the blind reader's, which is already committed. Both
   are pure reads over data on disk.
3. **Wave 2's shape is now genuinely open.** If 74 survives its offline test,
   task 64 is likely its first consumer rather than a task of its own.

**These experiments are worth running, and they are not a licence to start
building.** They cost nothing, they inform the checkpoint, and they can kill
either proposal before it acquires momentum — which is the cheapest moment to
kill anything.

## How this roadmap was built, and how much to trust it

A first version was written from `docs/cases/20` and
`docs/cases/21-independent-architecture-review-2026-08-02.md`. It was then given
to **two blind reviewers with different framings** — one auditing every numeric
and causal claim against the raw `debug.jsonl`, one reading the transcripts as
fiction and judging whether the roadmap aimed at what actually ruins the reading.
Neither knew of the other, and neither was told the author was on the team.

**Both overturned central parts.** The corrections are recorded in the tasks
themselves rather than quietly dropped, because the failure mode this project
keeps hitting is a wrong claim surviving into the next phase as a premise. In
particular, the v1 claim that *"the lexical instrument is exhausted; no threshold
works"* was **false** — see task 68 — and the v1 evidence for task 69 pointed at
a session that is not on disk and at a cause that had already been fixed.

Standing method rule, learned twice the hard way:

> **Verify against `debug.jsonl`, not `state.json`.** `perception_events` does
> not exist in the durable state — `grep -c perception_events state.json` returns
> `0`. Reading that absence as "the Director never proposed it" produced a wrong
> attribution that reached `benchmarks/blind-read.md` under the word "Verified".

## The waves

Ordered by **measured damage and dependency**, not by cost. Where cheapness and
damage disagreed, damage won.

### Wave 0 — restore the instrument

| task | why first |
|---|---|
| ~~**68** — Fix cluster reporting, then scan~~ | **✅ DONE 2026-08-05.** The span was wrong on 10 of 16 archived runs; both batteries re-scored. The three scanners ship with seeded positives and negatives and their output is archived as `immersion-scan.json`, so every wave-1 task now has a reproducible "before". Two findings changed a task: the redaction damage is **twice** what the transcripts show, because it is baked into character memory, and **31 of 33** empty audiences are the zone graph rather than the model |

### Wave 1 — close the leaks

Four items. **Three are small deletions or bug fixes; 65 is not, and calling this
wave "deterministic cuts" is what let it be under-scoped in the first place.**
Verification before implementation showed its cut would delete the majority of a
channel rather than de-duplicate it, so it now moves a producer — the character
agent writes the line the Director wanted voiced. That is a real change to the
turn loop, and it is still first, because it is still the largest measured defect
and it still subsumes parts of three other tasks.

| task | why here |
|---|---|
| **65** — The Director must not author speech | **28% of all speech records** in the corpus, 12/12 sessions, every cell. Largest measured defect. Both reviewers put it first, independently. **Re-scoped 2026-08-05:** the "64% is duplication" premise was false — the safe population is 21–42% and the rest is dialogue with no other path to the reader, so the fix needs a **producer**, not a deletion. Decided: **route the character**. 65a and 65b collapse into one task |
| **70** — The Director prompt names the protagonist | `AGENTS.md` §3 calls named exclusion a leak in as many words. Not negotiable by measurement |
| **63** — Redaction must not reach the persisted record | Depends on 68's scanner to choose the fix, and on 65 which removes 42 of its 43 cases |
| **67** — Zone graph integrity | Independent; the cause is the zone graph, not the model |

### ◆ Checkpoint — re-measure before anything in wave 2 is designed

**Added 2026-08-05. This is the load-bearing addition to this roadmap.**

Wave 1 changes the *population* that the later tasks are specified against:

- **65** removes the producer of 66's T23/T24 attribution bleed, of the id leak
  and of the English flip;
- **70** may resolve **64** outright — it is instructing the Director against the
  engine's primary control-return path on 33–100% of turns;
- **67** changes which records have an audience at all, which is an input to 71.

(**63** is the exception: it re-scans *inside* wave 1, immediately after 65
lands, because its 42-of-43 dependency is what chooses its fix. It does not wait
for the checkpoint.)

Designing wave 2 against pre-wave-1 numbers means designing against a confounded
baseline — the exact failure this project has now made twice (`main_doors`,
`perception_events`-in-`state.json`).

So: **land wave 0 + wave 1, then re-run the P1 battery and the blind read, then
re-derive.** Every wave-2 and wave-3 task is re-sized from that run before a line
of it is designed.

> **The re-run is WIDE (added 2026-08-05).** Not three replicates per cell — as
> many as patience allows, `oldcode` control included. n=3 was a cost compromise
> and cost is no longer a constraint (`AGENTS.md` §2); it is also the single
> reason `RSR_prop`, `GUARD` and `NSR` cannot decide anything, since the
> within-cell spread is several times the effect any task here would produce. A
> checkpoint measured at n=3 would re-derive wave 2 from an instrument this
> phase has already documented as blind. **Widening the battery is part of the
> checkpoint, not an optimisation of it.** Tasks **64, 66 and 72** already carry falsifiers, and this
checkpoint is where they are evaluated — three of the phase's remaining tasks can
legitimately close here without being built.

### Wave 2 — make the scene move

| task | why here |
|---|---|
| **69** — Physical state as a closed transition | The residual restaging, with evidence that survives audit. **Owns the durable-state storage decision** (below) |
| **64** — Return control | Depends on what 69 builds; **may be closed by 70 alone at the checkpoint** — and if task 74's offline test survives, 64 is likely its first consumer rather than a task of its own |
| **72** — Commitments as first-class state | **Gated.** Ships only if the checkpoint shows stalls survive 69 — see below |

**69 owns the storage decision.** Tasks 69, 72 and 66 all want durable state, and
`scene.physical_facts` is already pinned at its 40-key cap in **4 of 12 P1 runs**
(`base-r2`, `base-r3`, `drive-r1`, `drive-r2` — verified in `metrics.json`)
and evicting. Whoever builds first decides the storage model for all three. That
is 69, and it is now an explicit deliverable of 69 rather than a footnote.

**72 is gated, not scheduled.** The roadmap previously argued 72 must ship
alongside 69 ("otherwise twelve identical doors become twelve distinct ones")
while 72's own falsifier says *"if, after task 69, sessions no longer show long
stalls, then restaging was the whole of it."* Both cannot hold. **The falsifier
wins** — 72 is the largest item in the phase, it is the only one justified by a
narrative argument rather than a count, and it is the single most likely place for
this phase to turn into the loop it is trying to avoid. Evaluate at the
checkpoint; if stalls survive, it ships and its argument is confirmed.

### Wave 3

| task | why last |
|---|---|
| **66** — Identity and possession as data | Costs a schema bump; part of it disappears with 65. Inherits the phantom-cast scanner cut from 68 |
| **59** — Knowledge visibility | Already open. Blocked on 63 |
| **71** — Per-viewer narration | Product question answered 2026-08-05, then **parked until 67 has shipped**. It projects narration through the zone graph, so it cannot be built on a graph that wrongly severs a sub-zone — and every cost figure it carries was measured on that same broken graph. **Its first action is a re-measurement, not a design**; if the split rate collapses on the fixed graph, the task shrinks or closes |

### The product decision this phase was waiting on — answered

**2026-08-05, by the owner: narration renders per zone-cluster** (task 71's first
option). One narration per set of mutually-perceiving zones, each with its own
audience; the reader receives the cluster their character is in. So at the
narration layer this is *"your character's experience"*, while the ensemble
quality survives inside a cluster.

It is the most expensive of the three options and it was chosen knowing that.
The falsifier was evaluated before scheduling it: scenes split on **168 of 610
narrated turns (28%)** across the archive, bimodally — 8 of 16 sessions never
split, 5 split on 42–78% of their turns. So the defect is not rare enough to live
with, and 71 enters wave 3 rather than closing unbuilt.

**And then it was parked, on the same day, until 67 ships.** Every number above
is an upper bound taken on the broken zone graph, whose two bugs each manufacture
a spurious cluster — so the task's **first action is a re-measurement, not a
design**, and a collapsed split rate is a legitimate reason to shrink or close
it. The owner's leaning on the phase's biggest cost lever is recorded there too
(fold singleton clusters: 1.56x prose calls becomes 1.21x), for the same reason
held short of a decision: the graph bugs are what produce isolated single
characters in the first place.

```
68 ✅ ─▶ 65 ───▶ 63     70       67
                 │        │        │
                 └────────┼────────┘
                          ▼
        ╔══════════════════════════════════════╗
        ║  CHECKPOINT — re-run P1 + blind read  ║
        ║  re-derive 64 / 66 / 72 from it       ║
        ╚══════════════════════════════════════╝
                          ▼
                 69 ──▶ 64        [72 — only if stalls survive]
                  │
                  ▼
          66      59      71 (after 67)
```

## The baseline — the numbers this phase has to beat

Everything below is measured on the archive at engine fingerprint
**`6ed5639e049f`** (`benchmarks/2026-08-02-6ed5639e049f-p1-burst`, 12 runs, and
`-p2-spoken`, 4 runs). **If you are implementing a task, this is your "before".**

**Read `benchmarks/README.md` §7 first** — it defines every metric name used here
(`RSR_prop`, `BOCC`, `GUARD`, `cluster_max`/`cluster_span`, `max_hint_repeats`),
what each one can and cannot see, and which three of them ever decided anything.
**§8 defines the three invariant counters** that gate wave 1, archived per battery
as `immersion-scan.json`. Do not gate on a metric before reading what it measures;
this phase already shipped one inverted gate by skipping that step.

> **The wave-1 rows below were re-derived by the scanners on 2026-08-05** and now
> quote what the committed `immersion-scan.json` says, not the hand audit. The two
> agree within a few counts everywhere they overlap (the audit had 467/1,649 for
> 65 against the scanner's 458/1,601; 43 persisted redaction records against 42).
> **Where they differ, the scanner wins** — it is reproducible from committed code
> over a committed output, which is the whole point of the phase rule that an
> invariant which cannot be scanned offline cannot be defended.

| task | baseline in the archive | what "done" looks like | judged by |
|---|---|---|---|
| **68** | ~~`cluster_span` reported **5 / 5 / 8 / 3** on `base-r2` / `oldcode-r1` / `null-r2` / `drive-r2`; true maxima **15 / 37 / 36 / 24**~~ | **DONE 2026-08-05.** Reports maxima; **10 of 16** runs' spans were wrong, up to 5 → 37. Both batteries re-scored | unit test with a hand-built cluster set |
| **65** | **458 of 1,601 speech records (28.6%)** Director-authored, **12 of 12** sessions, 21.3–40.6% per session. **66%** of them are for a character routed that same turn (P2: 181/618, 29.3%, 4 of 4) | scanner at **0** | 68's scanner + blind read (did the fiction thin?) |
| **70** | named exclusion on **100% of P2 turns** (41/41, 41/41, 44/44) and **33–41% of P1** | **0** prompts naming exactly one cast id | new `prompt_contract` check, fails before / passes after |
| **63** | **87 markers in P1, 28 in P2** — of which **42 / 15** in persisted speech records, 7 / 4 in narration, and **33 / 6** in the perspective **ledger** (`recent_memory` and `memory_summary`, never `people`). The ledger half was not in the hand audit | **0** in persisted records, prose and **all three ledger channels** | 68's channel-split scanner |
| **67** | **33 empty-audience records across 5 of 12** sessions, **every one with other characters present**: **31** cut off by the zone graph, **2** narrowed to nothing by the Director's own list — while only **2 of 1,868** raw Director events proposed an empty witness list. Largest witness list clamped to zero: **18** | **0** for a subject co-located with others | 68's audience scanner; `base-P1-r2` T23 replayed |
| **69** | ceiling restaged **T33/T34/T35**, Liora dies **T36/T37/T38**, pillar **T28/T29** (`base-P1-r2`); `cluster_max` `base` median **3**; `physical_facts` pinned at the 40-key cap in **4 of 12** runs | ceiling family does not recur **and** the T28→T29 pillar escalation still passes | fixed `cluster_max`/`cluster_span` + blind read |
| **64** | `return_control=True` **5 of 482 turns (1%)**; controlled character routed **11 (2.3%)**; **5 of 12** sessions never returned control at all | both rates rise; 5/12 falls | direct count, one cell |
| **72** | `time_skip_ticks` nonzero on **13 of 482 turns (2.7%)**, and **0 of 6** explicit `CLOCK SIGNAL` invitations accepted in `base-P1-r2`; 12 openings in 19 turns in `base-P1-r1` | consecutive no-net-change turns fall | blind read — a held scene and an empty one score identically to every metric here |
| **66** | phantom names in **4 of 16** sessions; pronoun flip n=1; the seal changes hands 5 times with **0** staged transfers | scanner at **0** | 66's cast-integrity scanner |

**The narrative baseline is the blind read, not a number.** On this archive it
ranked `oldcode` at **9, 10 and 11 of 12** — independent confirmation of the
previous phase's fixes from a reader that did not know which engine it was
reading — and it ranked **`base-P1-r2` worst of twelve** while every metric scored
that session clean. That session is the bar: a re-run where its successor is no
longer bottom-ranked is the phase's headline result.

> **Comparability.** Two batteries compare only if they share an engine
> fingerprint or ran in the same provider-weights window
> (`benchmarks/README.md` §5 — DeepSeek replaced `deepseek-v4-flash` **in place**
> on 2026-07-31 and it explained most of a headline number). The checkpoint
> re-run must carry the `oldcode` control cell, or its numbers are not
> attributable to anything in this phase.

## Rules this phase inherits

- **A cut that buys quiet instead of movement is a failure, not a fix.** Written
  before the last phase's data and it still binds — **but not through `NSR`.**
  See the correction below; the rule survives, its instrument does not.
- **An invariant that cannot be scanned offline cannot be defended.** Every task
  here ships a scanner or extends one. **Qualified 2026-08-05:** a scanner that no
  task in the current wave reads is not built in that wave. This is why 68 ships
  three scanners and not five.
- **Forward-only** (`AGENTS.md` §2). Tasks 66 and 59 both want the schema bump;
  they coordinate or one waits.
- **Cite turn and excerpt, or `file.py:line`.** A claim without one does not
  enter a task.

## ⚠ The acceptance gate this roadmap shipped with was inverted

**Found 2026-08-05, re-deriving from `benchmarks/2026-08-02-6ed5639e049f-p1-burst/metrics.json`.**

The rule above was originally written as *"any task that reduces repetition while
`NSR` falls must be rejected"*, and six tasks carried an `NSR`/`SIL` interlock in
their closure evidence. **Applied to this archive, that gate endorses the worst
session in it and rejects the three best.**

`NSR` is `len(novel) / turn_count` (`repetition_metrics.py:609`), where `novel` is
a stimulus whose lexical similarity to every prior stimulus is `<= tau`
(`:555`). It measures **event volume**, not narrative substance. Against the blind
reader's ranking of the same twelve sessions:

| | |
|---|---|
| Spearman ρ, blind rank (1 = best read) vs `NSR` | **+0.923** |
| `base-P1-r2` — ranked **worst of twelve** by the reader | **highest `NSR` in its cell** (4.54 vs 3.41 / 3.78) |
| within-`base` spread | **1.12** |
| `base` − `oldcode` median delta | **−0.15** |

Higher `NSR` tracks *worse* reading, almost monotonically, because this corpus's
failure mode is over-production. And the within-cell spread is **7× the effect
the metric would be asked to detect** — at n=3 it cannot see anything a task in
this phase would do.

`SIL` is worse: **0.0 in 16 of 16 runs**, both batteries. It cannot degrade,
because `perception_events` `minItems: 1` and the 150-word floor make a silent
turn structurally impossible. It is a floor-effect metric, like `REVERT`.

**And the gate is aimed at task 72's success.** 72 exists to make *"a turn may
legally produce no material change"* possible. A turn that produces nothing
contributes zero novel stimuli and one silent turn — so 72 working looks exactly
like `NSR` falling and `SIL` rising. Its own closure line, *"`NSR` does not fall
with them"*, was **unsatisfiable by construction**.

### What replaces it

The rule stands; the instrument changes. Per `benchmarks/README.md` §7, three
metrics ever decided anything — repeated injected event, `BOCC`, `ECHO_PERSIST`,
all with zero within-cell spread — and *"reading the transcripts found more,
faster, than any of them."*

1. **The blind read is the acceptance instrument for anything narrative.** It
   recovered the cell design unprompted and put `oldcode` at 9, 10 and 11 of 12.
   Re-run it at the checkpoint, same protocol (`blind-read.md` §"Reproducing").
2. **Deterministic per-defect counters gate their own task** — each task's
   scanner at zero, which is parameter-free and needs no replicates.
3. **`NSR` and `SIL` are reported, never a gate.** Recording them is still
   right; a large move in either is a prompt to go read, not a verdict.
4. **The quiet-engine rule is checked by reading**, which is what caught the
   `null` cell being "dull" — a judgement `NSR` also made (2.87) and that was
   then misread as "the roteiro is better".
