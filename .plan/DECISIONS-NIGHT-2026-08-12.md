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
## 3. Task 77's mechanism: I wrote a diagnosis, tested it, and it was wrong — DECIDED

**What I claimed** (committed `2f076bc`, ~2h before this): the Director's own
contract forbids enactment. Rule 3 resolves only *"the final HISTORY action"*,
rule 2 says travel *"ends only after a later explicit arrival"*, so a Director
obeying its instructions lands nobody anywhere.

**What I did about it.** Wrote the replay the task called for, pre-registered the
decision rule, fired 16 calls. Arm A = recorded contract verbatim; arm B =
rules 2 and 3 rewritten to permit enacting an order already in force.

| | enacted `zone_moves` | mean moved |
|---|---|---|
| A (recorded) | **3 of 8 (37.5%)** | 0.50 |
| B (permitted) | **5 of 8 (62.5%)** | 1.50 |

**Both results are negative, and the second one is against me.**

1. **B fails its own gate** (needed 2x, got 1.67x; Fisher p = 0.62). Not adopted.
2. **Arm A moves people 3 of 8 times on the exact payloads that recorded
   `null`.** So the contract permits enactment; the Director simply takes it
   about a third of the time. My diagnosis was wrong.

**Decision.** Task 77 keeps the transcript (it is solid: three turns, four
orders, nobody through the gate) and now carries an **open cause** with a
warning at the top that two diagnoses have already been falsified in it. The
replay points at **variance** rather than prohibition — nothing in the engine
remembers an order is outstanding, so every turn re-rolls a biased coin instead
of resuming a commitment.

**⚠ NEEDS YOU:** on that reading, **77 may be evidence FOR task 72 (commitments
as first-class state) rather than a task of its own.** I have not merged them.
That is a roadmap call and it is yours.

**Kept but not acted on:** arm B moved 3x as many characters per run, and every
destination it produced was the place the order names, while arm A also produced
one move back *into* the hall it had just ordered everyone out of. Directionally
better, not adoptable at n=8 per arm.

---
## 4. Task 71 shipped a defect this morning; I found it tonight by reading — FIXED

**What I read.** `c76037ff`, the five-person cluster. Sixteen narrations, and
**eight had no events at all**, so the renderer described the room instead:

| word | small cluster | main cluster |
|---|---|---|
| `quietude` | **44%** | 3% |
| `penumbra` | **50%** | 0% |
| `halos` | **19%** | 0% |

**The number that makes this worth your time:** consecutive pairs score **0.02**
on sequence similarity. Every repetition guard in this project reads that as two
unrelated paragraphs. A reader sees one paragraph four times. The model varies
its wording enough to defeat `SequenceMatcher` while saying the same thing.

**Decision.** A cluster with no events of its own is no longer rendered. The
rule already existed one level up — the burst path refuses to narrate a beat
with no novel events, and its comment gives the exact reason ("a null recap
turn"). The player's cluster is still never folded.

On the metric-validity page as the sharpest case there: *lexical distance
measures whether the words changed; nothing here measures whether anything
happened.*

---
## 5. Task 76's last item closed — no regression, smaller footprint than claimed

The post-76 cell shows `empty_audience` 0 and `with_others_present` 0, so 76
added no wrong edges. But `clamp_lost_half_unsealed` went **0 → 2**, and reading
it matters more than the count:

> Garran calls from `porta lateral do salão` asking if everyone is safe. **17
> people are in `túnel oculto`, 2 on the stairs, 1 in the hall.** All three zones
> link to the hall, none to each other, so he reaches one person out of twenty.

That is 76's own defect, and **the shipped rule cannot touch it** — none of those
names contains a comma. The prefix rule catches siblings the Director named as
sub-positions and is blind to siblings it named as places.

**⚠ NEEDS YOU — this reopens 76's design question.** Candidate rule 1 (link all
siblings of a common origin) would fix the case above. I rejected it earlier
because it also joins a ventilation duct to a secret passage in `base-P1-r2`.
The evidence now points both ways. **Task 54's doctrine favours rule 1**
(separation must be declared; undeclared deafness is the expensive error), and
on that doctrine I would switch — but it widens audibility across the whole
engine and that is your call, not mine.

---
## 6. Task 69 re-measured post-wave-1 — it survives — INFORMATIONAL

The checkpoint requires re-measuring before designing. Over the nine post-70
sessions: **97 of 987 Director physical/observation events (9.8%) are
re-proposed within three turns** at similarity ≥ 0.6. Top case 0.94 —
*"Doran golpeia a base de uma pedra caída e uma runa se acende"* at T26, T27
**and** T28.

So 69's evidence is not a pre-wave-1 artifact and the task is real as written.

**Worth noticing:** 69 ("the ceiling collapses three times"), 77 ("the order is
given four times and never executed") and 72 (commitments as state) are three
faces of one thing — **the engine keeps no record of what has already been
settled.** I have not merged them; that is a roadmap call.

---
