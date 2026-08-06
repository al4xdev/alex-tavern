# Task 75 — A critic at the end of the turn

> **Status:** backlog, **proposed 2026-08-05** by the owner, enabled by the budget
> rule (`AGENTS.md` §2). **Not scheduled**, and **half of it is already rejected
> on this project's own evidence** — see §2.

## 1. The proposal

An optional agent at the end of the turn that looks at what was produced and says
*"this leaked context"* or *"this does not read fluidly"*, and the turn is redone.

## 2. The proposal splits in two, and the halves get opposite answers

### ❌ Leak detection — rejected, and not on cost

A leak is **deterministic and checkable in code**. The phase rule is already
written: *"An invariant that cannot be scanned offline cannot be defended"*, and
task 68 shipped three scanners that count exactly this — a redaction marker
reaching a persisted record, an internal id in prose, an audience the zone graph
contradicts — at zero cost, zero variance and with seeded tests proving they fire.

Asking a model to find what a regex finds is **strictly worse**: it is
nondeterministic, it cannot be unit-tested against a seeded positive, and it can
be wrong in both directions. Worse, it converts a hard invariant into a
probabilistic one, which is the exact inversion of everything the engine's leak
defense is built on (selection *before* the call, never inspection after it).

**If a leak can reach the critic, the bug is that it was renderable at all.**
Fix the producer; do not hire a reader.

This half is rejected for being *wrong*, not for being expensive — recorded that
way so it is not revived the day judging gets cheaper.

### ⚠ Fluency judging — the interesting half, and it needs a falsifier

*"Does this read well"* is genuinely **not** scannable. It is the one thing this
project has never automated, and the acceptance instrument for it today is the
blind read — which works (it ranked `oldcode` 9, 10 and 11 of 12 unprompted, and
found three defects no metric did) but is **offline, manual and post-hoc**.

An inline critic would make that judgement act on the turn the reader is about to
see. That is a real capability, and the budget rule now permits paying for it.

But this project has a bad record with judges in the loop, and the evidence must
be in front of whoever builds this:

- **`material_delta_rate`** was specified as a semantic judge and never ran; task
  68 then falsified its premise outright — the lexical instrument *did* see the
  restaging, and a reporting bug hid it.
- **The hint-materialization retry** burned ~170k tokens per session, ~13% of the
  run, on a correction that could never succeed — a retry loop that could not
  reach its own success condition, invisible until someone counted.
- **The prose repetition guard** fires and retries; `GUARD` measures it, and case
  21 showed it firing one layer below where the defect actually lived.

A retry driven by a judge is the same shape as all three. So it ships with a
budget and a falsifier or it does not ship.

## 3. What it has to prove before it is allowed in the loop

1. **It must catch something the scanners do not.** Run it offline over the
   archived sessions first. Every complaint it makes that a scanner already makes
   is redundancy; the task's value is *only* in the remainder.
2. **Its remainder must agree with the blind reader.** The blind read has already
   ranked twelve archived sessions. A critic that cannot reproduce that ranking
   has no claim to judge fluency — and this is a free experiment, because both the
   sessions and the ranking are committed (`benchmarks/*/blind-read.md`).
3. **A bounded retry.** One retry, counted and logged, never a loop, and the
   rejected output kept in `debug.jsonl` so the disagreement is auditable.
4. **A measured effect on the reading**, at the checkpoint battery, against a cell
   without it. Not "it flagged 40 turns" — did the sessions read better.

**The measurement that would falsify this task:** if the critic's complaints are
a subset of what the scanners already catch, or if its ranking of the twelve
archived sessions does not correlate with the blind reader's, it is an expensive
second opinion and closes.

## 4. Where it does belong, today, for free

Nothing above prevents the critic from running **offline over an archive**, which
is where it should start: same shape as the blind read, no turn-loop risk, and it
can be compared against a ranking that already exists. If it earns its place
there, moving it into the loop becomes an engineering question instead of a bet.
