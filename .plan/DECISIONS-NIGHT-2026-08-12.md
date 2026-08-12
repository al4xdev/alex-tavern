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
## 7. Every session this phase has ever measured had a passive player — ⚠ THE BIG ONE

**How I found it.** Reading the protagonist's own thread. In `09aabf25` Link
speaks **four times in thirty-nine turns**:

> *"..."* / *"Prefiro só observar por enquanto."* /
> *"Não se preocupem comigo, continuem."* / *"E agora?"*

That is not a player, it is the battery's input profile — and **both profiles
this project owns are deliberately inert.** P1 is six `skip`s out of ten, and its
own comment says the lines are *"deliberately inert: the player observes and
reacts without steering"*.

**Why that is the big one.** It is a defensible control for measuring
engine-driven repetition. It is the wrong control for *"the scene does not
move"*, which is this phase's headline complaint and the thing waves 2 and 3 are
sized against. **The engine has never been measured with a player who pushes.**

It does not explain the defect away — in task 77 the NPCs do not move either and
the Director's `zone_moves` are `null` — but every severity number this phase
carries was taken in the condition most favourable to the defect.

**What I did.** Added a **P3** profile that steers: *"Eu vou na frente. Abram
caminho."*, *"Nao vou esperar mais. Estou entrando."*, with `action` inputs that
take a direction. Additive only; P1 and P2 are untouched, so no existing baseline
moves. **Not run yet** — a cell was already in flight.

**⚠ NEEDS YOU:** two things.

1. **Is the passive profile the right baseline for this phase at all?** If the
   product is *"your character's experience"*, measuring it with a character who
   never acts may be measuring the wrong game. I did not change P1 or P2, because
   that would invalidate every number in the roadmap.
2. **P3's lines are mine.** They are a guess at what an active player sounds
   like. If they do not match how you actually play, they will measure the wrong
   thing confidently, which is this project's characteristic failure.

---
## 8. The empty-cluster fold is verified on ONE cell, not two — CORRECTED

I first reported two post-fold cells. **One of them was not post-fold.** Two
batteries overlapped: my waiter saw the gap between replicates, called DONE, and
I scored a session from the older run.

Checked against commit times: the fold landed 19:18. `d8310b8b` (19:48) came from
the battery launched 19:23 and **is** post-fold. `75d9f36f` (19:48) came from the
post-76 battery launched ~18:58 and is **pre**-fold — and it produced no cluster
narrations at all, so it carries no information either way.

**So the fold rests on `d8310b8b` alone: 2 cluster narrations, 0 with zero
events, against 8 of 16 before.** The mechanism is verified by its unit tests;
the live evidence is one thin cell. A second post-fold replicate was still
running when this was written.

**Lesson worth keeping:** the waiter polls for `--exec-one` and a battery has no
such child between replicates. Every "DONE" it has ever reported is suspect, and
two of tonight's were wrong. Check the PARENT pid, not the child.

---
## 9. I audited task 67's own closure metrics, and they were luckier than strong

Scoring twelve cells rather than the two 67 closed on:

| era | `empty_audience` / `with_others_present` | `clamp_lost_half_unsealed` |
|---|---|---|
| pre-67 | 2 / 2 | 5 |
| post-67, 4 cells | **0 / 0** | **0** |
| post-71, 4 cells | **7, 0, 7, 0** | 0, 4, 0, 0 |
| post-76, 3 cells | 0 / 0 | 2, 0, 0 |

**None of the movement is a graph regression.** The 7s are one man on a
deliberately sealed pulpit; the 4 and the 2 are the same class. Every layer did
its job and the metrics filed it as `graph_isolated`, which reads as "the zone
graph broke".

**Decision.** Both metrics are downgraded to **REPORT, DO NOT GATE** in the
register, and task 67 now carries the table with an explicit note that its
closure *numbers* were luckier than they were strong. **The graph fixes
themselves still stand** on their own tests — the T21 wipe replay, the merge
semantics, the sibling work — so I did not reopen the task.

`clamp_lost_half_unsealed` needed **three repairs in one day**, and every one was
found by reading a flagged case. The number has never once announced its own
error. That is the argument for the downgrade, more than any single miss.

---
## 10. Task 78 opened — a man addressing a room that cannot hear him

`21f7c4e1` T24-T30: Lorde Cassian is sealed on the pulpit and **the Director
routes him to speak on seven consecutive turns**, every record with
`audience: []`, twenty people in front of him.

Measured over twelve sessions: 13 of 1,255 speech records (1.0%) go to an empty
audience, **10 of them in runs of three or more by one character.** Rare per
record, and when it happens it lasts a third of a scene.

The Director's own rule 5 says to route only characters "with a concrete event
they personally witnessed". A sealed man witnessed nothing.

**Not** task 67 and **not** task 76: the seal was declared and correctly applied.
The defect is the routing. Fix deliberately not designed; the file names three
shapes and says which to check first.

---
## 11. P3 ran, and it dismissed my own confound — DECIDED

Decision rule was registered before the run, against P1's control of 90.8%
frozen adjacent turn pairs over nine sessions.

**`5d60575d`: frozen 95.2% (20 of 21). Fisher p = 0.70.** Above the 82% line, so
by the pre-registered rule the engine stalls **regardless of who pushes**, and
the passive-profile confound I raised against task 77 is dismissed.

**Reading it is where the value is.** The scene is far from static: the ceiling
collapses, the west exit is buried, then the south, then a crack opens north.
What never happens is anybody moving. Counting how the cast talks, per NPC line:

| | P1 passive | P3 active |
|---|---|---|
| orders to HOLD | 9.1% | **29.7%** |
| orders to GO | 12.0% | **25.0%** |

Both double or triple, and the world obeys neither. **The room is not quiet
because nobody asked. It is quiet with twenty people shouting instructions.**
That is a stronger case for task 77 than the transcript it opened with.

**⚠ NEEDS YOU (softened):** I asked earlier whether the passive profile was the
wrong baseline for this phase. On this evidence it is **not** distorting the
stall finding, so the answer is less urgent than I made it sound. P3 is still
worth keeping, because it is the only profile that can ever answer this
question, and it should be re-run when task 77 is actually fixed.

**And I got the number wrong first.** My initial HOLD count said 46.9%; the
pattern included `fila`, which appears in *"saídas laterais, em fila"* - an order
to MOVE. Six of the first ten flagged lines were that. **Fourth guard of this
shape to fail today**, and the fourth time reading the flagged lines caught it
rather than the number looking suspicious.

---
## 12. A number I nearly reported as a triumph, and did not — CAUTION

Live split rates by era: post-67 **27.8%**, post-71 **51.2%**, post-76 **1.3%**
(2 of 159 narrated turns), Fisher p = 1.2e-12 for the last step.

Read cold that says task 76 all but eliminated scene splitting, and it would
have been a satisfying headline given the archive replay said 76 changed nothing.

**It is not true.** `sibling_zones_linked` fired **0 times in three of the four
post-76 sessions and 3 times in the fourth**. The rule barely ran. It cannot have
caused a collapse from 51% to 1%.

What actually differs is the Director. In three of the four post-76 sessions it
built mutually-linked zone graphs (hall ↔ children), which are one connected
cluster by construction; the post-71 group happened to contain the sealed-pulpit
sessions. **That is Director behaviour varying across sessions, not code.**

So: the 51.2% post-71 figure is also not a task 71 effect - 71 does not touch the
graph. **Both of those era comparisons are confounded by which scenes the
Director happened to seal**, and neither belongs in a summary as a result.

**⚠ NEEDS YOU:** this means the split rate - the number task 71 was sized on,
and the one I re-derived at 27.8% this morning - **swings between 1% and 51%
across sessions on identical code.** Task 71's cost and value estimates inherit
that spread. I did not restate them, because I do not know which end is typical
and four sessions per era cannot tell me.

---
