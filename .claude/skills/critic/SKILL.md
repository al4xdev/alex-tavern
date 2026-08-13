---
name: critic
description: Send content you just wrote (a task, a decision entry, a closure, a report, a roadmap entry) to an isolated critic subagent that reads only the content — no code, no tasks, no history — and returns a per-claim verdict (ADVANCES / NEUTRAL / WORSE THAN ABSENT / UNSUPPORTED) with a falsifier and a metric. Use before writing anything into `.plan/`, when reviewing what another model produced, or when deciding whether a finding deserves to exist. The full doctrine is in `.plan/reference/critic-protocol.md`.
---

# Critic — content defends itself or it does not enter

This project found **every** real finding by reading text, and **none** by a
metric announcing a problem. This skill is the counterpart: before text becomes
record, somebody who did not take part in writing it tries to knock it down.

Read `.plan/reference/critic-protocol.md` before running. That file is the
source of truth and is portable — it holds for any model or tool, not just
Claude. This skill is only the dispatch procedure.

## 1. Extract the claims

The unit is **not the line**. It is the **claim**: any sentence a reader would
act on — a number, a cause, a recommendation, a status, a closure. A critic
holding one loose line can only tell you whether it is well written, which is
the least useful thing it could say and the easiest to fake.

Prose carrying no claim (framing, transitions, quoted transcript) does not go to
review — there is nothing in it to be wrong about.

Number the artifact's claims. An artifact with zero claims does not need a
critic; it needs a reason to exist.

### Tag each claim's status — and keep the tag alive

Alongside the verdict, every claim carries a **status**, which says what kind of
thing it is. The two axes are independent: a THEORY can be the most valuable
sentence in the document, and a MEASURED number can be worse than absent.

| status | means |
|---|---|
| **MEASURED** | a number with named method, n and a control; someone else can reproduce it |
| **OBSERVED** | somebody read it and saw it; small n, stated, no instrument |
| **THEORY** | a proposed mechanism; nothing measured |
| **ASSUMED** | inherited from earlier text, never checked here |

**Theory written in the grammar of a measurement is WORSE THAN ABSENT by
default** — however plausible, because the next reader will quote it as
established. Write the status into the text, not only into the review:
*"undiagnosed"*, *"read across six sessions"*, *"pooled over N sessions, median
M"* are the words that carry it.

**Promotion and demotion happen during the work, not at the end.** Every time a
piece of evidence lands, go back and re-tag what you already wrote:

- promotion climbs one rung at a time — `ASSUMED → THEORY` (mechanism stated and
  falsifiable) → `OBSERVED` (real reading, with n and method) → `MEASURED`
  (metric + control + per-session spread + a decision rule pre-registered
  **before** the numbers). Nothing skips a rung.
- demotion is **mandatory** when the instrument fails (`MEASURED → THEORY`: the
  0.02 score and the 34% rate), when the spread shows the number only describes
  the sessions actually seen (`MEASURED → OBSERVED`), or when a control shows
  the effect is background (`OBSERVED → THEORY`: 36 of 39, Fisher p = 0.43).

A demotion is written **where the claim lives**, carrying its history —
*"measured, demoted on <date> because <what>"*. A retraction filed somewhere
else leaves the wrong sentence in the reader's path, and without the history
somebody silently re-promotes it a month later.

## 2. Choose the batch

One artifact per dispatch: one task file, one decision entry, one closure, one
report section. The critic needs enough context to judge "does this advance?",
and one isolated paragraph usually is not.

## 3. Dispatch the isolated critic

Launch a **fresh** `general-purpose` subagent. Never `SendMessage` an existing
agent — a critic that watched the work happen has already been convinced.

The verbatim prompt is in `.claude/skills/critic/agents/critic-prompt.md`. Use
it as it stands, pasting the content under review where marked.

**Isolation contract** (breaking it invalidates the verdict):

- Hand over ONLY: the content under review, the critic prompt text, and — if a
  number is in play — `.plan/reference/metric-validity.md`.
- FORBIDDEN to hand over: code, task files, the roadmap, git history, earlier
  verdicts, who wrote it, or why you think it is right.
- FORBIDDEN to the critic: opening any file beyond what it was handed, editing
  files, or proposing an implementation.

For anything that really matters, **vary the critic** — another model or another
framing. Same-model self-review has the smallest possible disagreement surface.

### Several critics: the disagreement is the signal

When a claim decides something, dispatch more than one critic **in parallel**
(independent calls in the same block). And read the result the right way:

- **Agreement is not evidence.** Identical prompts to identical models agree by
  construction — that measured nothing.
- **The disagreement points at exactly the claim whose support is thin**, which
  was the only thing you wanted to find.
- **Do not vote and do not average.** Take the **harshest verdict** as the one
  to answer, and record that the critics split and what each one saw. A claim
  that survives a critic trying to demote it is worth more than one three
  agreeable critics passed.

Different framings beat different seeds. A trio that works: one critic told to
**demote** (hunt theory dressed as measurement), one answering only **"would the
record be worse without this?"**, and one given **the numbers and no prose**.
The cost is real — do not fan out on everything, only on what blocks a decision.

## 4. Read the return

Per claim, the critic returns a verdict and three mandatory answers: what would
falsify the claim, the strongest reading against it, and whether the record
would be worse without it.

| verdict | reading |
|---|---|
| **ADVANCES** | a reader can do something they could not before — the critic must say **what** |
| **NEUTRAL** | true, defensible, and adds nothing |
| **WORSE THAN ABSENT** | the record is harder to use with this in it |
| **UNSUPPORTED** | the text does not carry its own weight; back to the author with the falsifier attached |

The critic **is not an approver**. `ADVANCES` does not make the claim true — it
makes it worth keeping while somebody checks. A schema change, a graph change or
a roadmap re-order stays an owner decision.

## 5. Metrics

Every numeric claim needs a named metric, from one of three sources (in order of
preference):

1. **An existing metric** — check `.plan/reference/metric-validity.md` first; it
   says which are trusted, which were downgraded, and which were measured and
   rejected.
2. **A new metric** — which then owes: a control, the per-session spread, a
   pre-registered rule, and an entry in the register.
3. **The critic's own judgement, stated as a metric** — legitimate and often the
   best available. *"I read six of these and could not tell them apart"* is a
   measurement. Report it as what it is (n, method, the critic's own
   uncertainty), never laundered into a percentage.

The rules the critic enforces — none of them style preferences, each one there
because it was violated and cost something — are in the protocol's *Metric
culture* section. The three that come up most: **the session is the unit**,
**every headline number carries its per-session spread**, and **never match a
NAME with a string heuristic**.

## 6. Close into the `.plan` schema

The verdict decides the folder:

| verdict | destination |
|---|---|
| ADVANCES + closes a question | `closed/`, with the evidence that closed it |
| ADVANCES + opens work in this phase | `tasks/`, mechanism **undiagnosed** unless measured |
| ADVANCES + real but not this phase | `backlog/` — **this is the default for a new finding** |
| ADVANCES + needs the owner | `para-o-dono/` |
| NEUTRAL | do not write it; there is no folder for this |
| WORSE THAN ABSENT | delete it, and log the rejection where it would be re-derived (the task's *measured-and-rejected* section, or `metric-validity.md`) |
| UNSUPPORTED | back to the author, into no folder at all |

**A phase does not grow while nobody is watching.** A new finding goes to
`backlog/` by default; promoting it to `tasks/` is an owner decision.

## 7. Consolidate

Report in a single block: the numbered claims, the verdict **and status** of
each, the falsifier for everything left as ADVANCES, everything deleted and why,
everything promoted or demoted and on what evidence, and which metric held up
each number. If the critic and a human reading disagree, **the reading wins and
the critic gets an entry in `metric-validity.md`** — the same rule that applies
to every other instrument here.
