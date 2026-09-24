# Task 80 — The narration does not convey space

> **2026-09-05: quantitative support withdrawn; hypothesis remains in backlog.**
> The old 35/40 came from targets such as C11, not canonical character names.
> The collector read the wrong schema level. Those outputs cannot establish
> omission for correctly identified characters. Correcting names in a paired
> reconstruction also exposed semantic judge errors, so its diagnostic output
> is not a replacement baseline. See
> `plans/artifacts/79-reader-identity-audit/REPORT.md`.
> Historical observations below are preserved with this correction.

> **Status:** backlog, **candidate finding, not a defect.** Opened 2026-08-13 out
> of task 79's method section, where it did not belong: this is an **immersion**
> claim and 79 is a schema task.
>
> **OBSERVED, n=40.** Not measured: the control that would make it a defect does
> not exist yet, and is described below.
>
> No next action. Promotion to `tasks/` is an owner decision.

## The observation

A blind reader was given the **narration of a turn** and **one character's name**,
and asked whether that character moved to a different place, repositioned inside
the place they were already in, or whether the text does not say.

**Correction:** the method intended a name but supplied an unresolved ID in all
40 cases, and joined narration records across audiences. The claim below about
what the prose fails to tell a properly identified reader is withdrawn.

It never saw the zone graph, the destination, the origin, or any instrument's
verdict. 40 cases, stratified 20/20 on an independent classifier's judgement,
shuffled, one call each, zero failures.

| | |
|---|---|
| **"não dá para saber"** | **35 of 40 = 88%** |
| determinable | 5 |

**In 35 of 40 turns where the engine recorded a character changing zone, the prose
does not tell a reader that the character moved at all.**

## Why this is an immersion claim and not a measurement note

This phase is judged on immersion, and its own roadmap says *"the narrative
baseline is the blind read, not a number"*. A reader who cannot tell where anyone
is standing, or that anyone moved, is the phenomenon this phase exists to fix —
the same family as *"the scene does not move"* (task 77), reached from the
opposite direction: **77 asks whether anything happened; this asks whether the
reader could tell.**

It also explains a smaller thing already recorded: task 79's audit found that no
string rule, and not the engine's own perception data, can recover
room-versus-position. **The prose cannot either.** Three independent instruments,
three failures, and this is the one that matters to a player.

## ⚠ The caveat that keeps this OBSERVED, and it cannot be waved away

**Good fiction omits movement all the time.** A well-written scene does not
narrate every step of every one of twenty characters, and it should not. Nothing
in these 40 cases establishes:

- how often omission is **correct** here — no control was run against prose a
  reader judged good;
- whether the 5 determinable cases are typical of anything, at n=5;
- whether a reader **needs** the information in the turns where it is missing.

So the honest statement is: **the prose does not carry this information, and
nobody has shown that it should.** Anyone promoting this task owes that control
first — the obvious shape is a blind read that asks *"did you want to know where
they were?"* rather than *"can you tell?"*.

## What was read, and one case worth keeping

The three determinable disagreements are in
`.plan/tasks/79-blocking-as-durable-state.md`. One of them is a separate finding
and has its own file: `81-narration-and-state-describe-different-events.md`.

## Related

- **79** — where this was found. Its ship-now half hands the Director's real
  blocking to the prose renderer, which is the cheapest thing that could move this
  number, and 79's acceptance instrument is this same blind read.
- **77** — the same complaint measured on the state instead of the prose.
- **71** — narration is already rendered per perception cluster, so any fix here
  is per viewer by construction.

**Method and raw results:** `plans/artifacts/79-positional-audit/blind_read_judge.py`
(gitignored output).
