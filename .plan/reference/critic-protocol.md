# The critic protocol — how this project decides a claim was worth writing

**Written 2026-08-13, for whoever works here next, model or human.**

This project has produced, in three weeks, more retractions than most projects
produce claims. That is not a failure — it is the only reason its numbers are
worth anything. This file is the procedure that produced them, written down so
it survives a change of model.

It has one job: **stop content that reads well and says nothing from entering
the record.**

---

## Why this exists

Every real finding in this project came from **reading**. Not one came from a
counter noticing its own error. The full list, from the phase log:

| found by | count |
|---|---|
| reading a session as fiction | task 71's defect, task 77, task 78, decision 12's false headline |
| a metric announcing a problem | **0** |

And the counters have been wrong, repeatedly and confidently:

- `SequenceMatcher` scored **0.02** between paragraphs a reader sees as the same
  paragraph four times.
- `named_exclusions` matched *"a menos de dois metros"*, 15 false positives.
- A `HOLD`-order counter matched `fila` inside *"saídas laterais, em fila"* —
  an order to MOVE.
- The intra-room movement rate is 34% pooled and **0% to 97% per session**,
  because all three detectors measured naming style rather than behaviour.

So the instrument is never the evidence. **A human or a model that has read the
text is the evidence, and the metric is how you check the reader was not fooling
themselves.** That order does not reverse.

---

## The unit is a CLAIM, not a line

Do not send lines to a critic. A critic holding one line cannot tell whether it
advances anything — it can only tell you whether it is well written, which is
the least useful thing it could say and the easiest thing to fake.

**A claim is any sentence a reader would act on.** A number, a causal story, a
recommendation, a status, a closure. Prose that carries no claim (framing,
transitions, quoted transcript) is not reviewed, because there is nothing to be
wrong about.

Batch by artifact: one task file, one decision entry, one closure, one report
section. A critic needs enough to judge "does this advance", and one paragraph
is usually not enough.

---

## The critic's isolation contract

**The critic receives content and nothing else.**

- **No code.** If the claim is only defensible by reading the implementation,
  the claim is not written well enough.
- **No task files, no roadmap, no history.** The critic must not be able to
  infer what it is *supposed* to conclude.
- **No author identity, no prior verdicts, no framing.** "I found this by
  reading, which is the method that works" is exactly the sentence that talks a
  critic into agreeing.
- **No inherited conversation.** A critic that watched the work happen has
  already been convinced.

This is not a new invention here. `.claude/skills/memory-playtest` already
evaluates narrative with *"um subagente limpo no papel de roteirista"*, without
inherited context, and for the same reason. This generalises it.

**What the critic MAY be given:** the content under review, the metric register
(`.plan/reference/metric-validity.md`), and this file. Nothing else.

---

## The four verdicts

The critic returns exactly one per claim, and the third one is the point of the
whole exercise.

| verdict | means |
|---|---|
| **ADVANCES** | A reader can do something after this that they could not do before. The critic must say **what**, concretely. "It is useful" is not a verdict. |
| **NEUTRAL** | True, defensible, and adds nothing. Costs a reader time and gives nothing back. |
| **WORSE THAN ABSENT** | The record is harder to use with this in it. Dilution, false confidence, a number that will be quoted without its caveat, a restatement that makes a reader think two sources agree. |
| **UNSUPPORTED** | The content does not contain what would be needed to believe it. Distinct from false — the critic is not ruling on the world, only on whether the text carries its own weight. |

**WORSE THAN ABSENT is the verdict this protocol exists for.** Most review
processes can only say "good" or "needs work", so nothing is ever deleted, and
the record fills with true, useless, confidently-worded sentences. A verdict
that means *delete this* has to exist or the phase drowns.

### The critic must also answer

1. **What would falsify this claim?** If the critic cannot name a falsifier, the
   claim is not empirical and must not be phrased as if it were.
2. **What is the strongest reading against it?** Written as an argument, not a
   caveat.
3. **Would the record be worse if this were deleted?** Yes/no, before any
   nuance.

---

## Every claim carries a STATUS, independent of its verdict

The verdict says whether a claim is worth keeping. The **status** says what kind
of thing it is. They are orthogonal: a THEORY can be the most valuable sentence
in a document, and a MEASURED number can be worse than absent.

| status | means |
|---|---|
| **MEASURED** | a number exists, with named method, n, and a control; another person could reproduce it |
| **OBSERVED** | somebody read it and saw it; n is small and stated, no instrument involved |
| **THEORY** | a proposed mechanism or explanation; nothing has been measured |
| **ASSUMED** | inherited from earlier text and never checked here |

**Mislabelling is not a style error.** A THEORY written in the grammar of a
MEASURED fact — no hedge, no n, causal verb — is automatically **WORSE THAN
ABSENT**, however plausible the theory is, because the next reader will quote it
as established. The fix is one word, and the cost of not fixing it is permanent.

Write the status in the text, not only in the review. *"Undiagnosed"*,
*"read in six sessions"*, *"pooled across N sessions, median M"* are the words
that carry it.

### Promotion and demotion happen DURING the work, not at the end

This is the part a review pass cannot do for you. As you write, and as each
piece of evidence lands, re-tag the claims you already wrote.

**Promotion** — the bar goes up at each step, and nothing skips a rung:

- `ASSUMED → THEORY`: someone states the mechanism explicitly and it is
  falsifiable.
- `THEORY → OBSERVED`: someone reads actual material and reports n and method.
- `OBSERVED → MEASURED`: a metric, a control, a per-session spread, and a
  decision rule written **before** the numbers arrived.

**Demotion** — mandatory, and it is the move that keeps this record honest:

- `MEASURED → THEORY` when the instrument fails validity. This project has done
  it twice: the `0.02` similarity score and the 34% intra-room rate, both of
  which were real numbers of the wrong thing.
- `MEASURED → OBSERVED` when the number survives but only as a description of
  the sessions actually seen — a pooled figure whose per-session spread runs
  0% to 97% is an observation about a handful of sessions, not a rate.
- `OBSERVED → THEORY` when a control shows the effect is background. *Restated
  orders on frozen scenes, 36 of 39, Fisher p = 0.43.*
- anything `→ ASSUMED` when the source turns out to be an earlier document
  rather than evidence.

**A demotion is written where the claim lives**, not only in a new file. A
retraction filed somewhere else leaves the wrong sentence in the reader's path.
Carry the old status forward — *"measured, then demoted on <date> because
<what>"* — so the demotion cannot be silently re-promoted by whoever reads next.

---

## Metric culture — what a critic enforces

**The nine rules live in `.plan/guides/MEASURING.md`, and that is the only copy.** They are not review rules; they govern all measurement here, and they moved
there on 2026-08-13 so this page and the guide cannot drift from them.

A critic enforces them without needing to have read them all. The three that decide
most verdicts: **the session is the unit**, **every headline number carries its
per-session spread**, and **never match a model-authored name with a string
heuristic**.

The critic may be handed `metric-validity.md` along with the content — it is on the
short list of what isolation permits, precisely because a claim about a number
cannot be judged without knowing whether that number is trusted.

---

## Where a metric may come from

The three legitimate sources are listed once, in `.plan/guides/MEASURING.md`. A critic may
propose any of them, and the third is the one worth naming here: **the critic's own
judgement, stated as a metric** — *"I read six of these and could not tell them
apart"* is a measurement, and often the best available. Report it as what it is (n,
method, the critic's own uncertainty) and never launder it into a percentage.

---

## Routing a verdict into `.plan`

The schema already exists (`.plan/README.md`). The verdict decides the folder.

| verdict | destination |
|---|---|
| **ADVANCES** + closes a question | `closed/`, with the evidence that closed it |
| **ADVANCES** + opens work in this phase | `tasks/`, mechanism **undiagnosed** unless it was measured |
| **ADVANCES** + real but not this phase | `backlog/` — **this is the default for new findings**, not `tasks/` |
| **ADVANCES** + needs the owner | `para-o-dono/` — create it if absent; `.plan/README.md` already documents it |
| **NEUTRAL** | Do not write it. There is no folder for this. |
| **WORSE THAN ABSENT** | Delete it. Log the rejection where it would otherwise be re-derived — the task's measured-and-rejected section, or `metric-validity.md` |
| **UNSUPPORTED** | Back to the author with the falsifier attached, not into any folder |

**A phase is not allowed to grow while nobody is watching.** Three tasks were
opened in one 2h49 block, all legitimate, and the roadmap's own second paragraph
warns against exactly that. New findings go to `backlog/` by default; promoting
one to `tasks/` is an owner decision.

---

## What the critic is NOT for

- **Not a code reviewer.** It never sees code. `/code-review` exists.
- **Not a style pass.** Prose quality is not a verdict.
- **Not an approver.** It cannot authorise a schema change, a graph change, or a
  roadmap re-order. Those are owner decisions and stay owner decisions.
- **Not a source of confidence.** A critic returning ADVANCES on a claim does
  not make the claim true. It makes it worth keeping while someone checks.

---

## The failure mode this protocol has

Written here so the next model does not have to discover it.

**A critic can be gamed by an author who knows the rubric.** Claims will start
arriving pre-fitted with falsifiers and counter-arguments, and a rubric-shaped
claim passes a rubric-shaped critic. Two defences, neither complete:

1. **Vary the critic.** A different model, or a different framing, on anything
   that matters. Same-model self-review has the smallest possible disagreement
   surface.

   Fan out to several critics when a claim gates a decision — and read the
   result correctly. **Agreement between critics is not evidence**; identical
   prompts to identical models agree by construction. **The disagreement is the
   signal**: it points at exactly the claim whose support is thin, which is the
   only thing you wanted to find.

   Do not vote and do not average. Take the **harshest verdict** as the one to
   answer, and record that the critics split, with what each one saw. A claim
   that survives a critic which was actively trying to demote it is worth more
   than one that three agreeable critics passed.

   Different framings beat different seeds: one critic asked to demote, one
   asked whether deletion would hurt, one given only the numbers and no prose.
2. **Spot-check the critic against a read.** Periodically have a human or a
   fresh reader judge the same artifact and compare. When the critic and the
   reader disagree, **the reader wins and the critic gets an entry on the
   validity page** — the same rule that applies to every other instrument here.

The critic is an instrument. Everything on `metric-validity.md` applies to it.
