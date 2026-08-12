# Decisions taken alone — night of 2026-08-12

The owner authorised working past the checkpoint without them, on the standing
instruction that **reading the text outranks the metrics, because this product
does not yet have instruments anybody should trust.** Every decision below was
taken under that rule; each one says what I read, not only what I counted.

Read this top to bottom in the morning. Anything marked **⚠ NEEDS YOU** is a
call I made to keep moving and would unmake on request.

---

## 1. Task 64 re-scoped from "missing trigger" to "shy trigger" — DECIDED

**What I did.** Ran the battery the task demanded: nine post-70 sessions, 323
Director turns.

| signal | pre-70 | post-70 | |
|---|---|---|---|
| sessions where control NEVER returned | **5 of 12** | **0 of 9** | p = 0.045 |
| `return_control=True` | 1.0% | 3.1% | p = 0.059 |
| either path | 3.3% | 6.2% | p = 0.057 |

**What the numbers alone would have said:** rates are still ~3%, so the
mechanism picks badly and needs replacing. That is what the task was written to
do.

**What reading all ten `return_control` turns said instead:** every one is a
held beat with the outcome open — the creature motionless and every hand
drifting to a weapon, Riven stepping up to a mural that is beginning to breathe,
the director hesitating with the metal trembling in her hand while the students
give ground. None is a lull. None hands the turn over mid-sentence.

**Decision.** The trigger exists and chooses well; it fires rarely. That is
calibration, not design. **Do not build a new mechanism.** Re-scoped in the task
file to ask why a Director that recognises these moments declares them 3% of the
time, with the contract wording as the first suspect — the pre-70 lesson being
that deleting one sentence tripled this number with nobody designing anything.

**⚠ NEEDS YOU:** this rewrites what task 64 *is*. If you wanted the trigger
redesigned regardless, say so and I will put it back.

---
## 2. Task 77 opened — "the order that nobody executes" — DECIDED

**How I found it.** By reading `09aabf25` straight through as fiction, which is
the method that found task 71 and which no instrument here replaces.

**What a reader gets**, turns 31 to 33:

> The Director orders everyone into the dungeon through the north gate. Asword
> answers *"Link, vamos atravessar juntos agora!"* The Director gives the same
> order at T32. Garran echoes it. The Director gives it again at T33. Asword
> repeats his line with one clause changed. **Nobody enters the gate.**

**I ran the task's own falsifier rather than leaving it**, and it does not fire.
The Director emits `zone_moves: null` at T31, T32 and T34, and its single move at
T33 sends a character *back into the hall*. So the decision layer issues an
instruction it never enacts. A character's `action` string — literally
*"avançar com Link em direção ao portão norte"* — has no mechanical path to the
world; only the Director's `zone_moves` moves anyone.

**Decision.** Written up as task 77 with the mechanism **undiagnosed on purpose**
and three candidates, because all three produce identical transcripts and
picking one now would be guessing.

**⚠ NEEDS YOU:** where this sits in the roadmap. On the reading it is the
phase's headline complaint made concrete, which would put it above most of
wave 2. I have not re-ordered anything.

### A metric I built for it, and threw away

Hypothesis: restated orders mark stalled scenes. Restated orders sit on a frozen
scene 36 times of 39 — damning, until the control: adjacent turn pairs are frozen
184 of 213 anyway. **Fisher p = 0.43.** Recorded in the task as
measured-and-rejected so nobody re-derives it.

The control did produce the bluntest number this project has for *"the scene does
not move"*: **86.4% of adjacent turn pairs have no position change.** The task
says explicitly why that must NOT be quoted as "86% static scenes" — position is
one narrow axis, and misreading it would put a fourth entry on the
metric-validity page.

---
