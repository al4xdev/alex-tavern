# Decisions taken alone — 2026-08-12, 18:56 to 21:45

*Two hours and forty-nine minutes, not a night. The file called itself NIGHT and
everyone downstream repeated it, including the owner's answers. Corrected
against the commit timestamps, which were there the whole time.*

The owner authorised working past the checkpoint without them, on the standing
instruction that **reading the text outranks the metrics, because this product
does not yet have instruments anybody should trust.** Every decision below was
taken under that rule; each one says what I read, not only what I counted.

Read this top to bottom when you pick it up. Anything marked **⚠ NEEDS YOU** is a
call I made to keep moving and would unmake on request.

---

## 1. Task 64 re-scoped from "missing trigger" to "shy trigger" — DECIDED

**What I did.** Ran the battery the task demanded: nine post-70 sessions,
historically counted as 323 Director turns. **Correction, 2026-09-24:** the nine
retained session states and logs contain 314 committed Director decisions. The
original 323 calculation was not recovered; the 0/9 sessions with neither
handoff route remains in the retained records. The pooled-turn p-values in the
historical table below are withdrawn because turns within a session are not
independent. See the [Task 64 audit](../plans/artifacts/64-return-control-calibration/RESULT.md).

| signal | pre-70 | post-70 | |
|---|---|---|---|
| sessions where control NEVER returned by either route | **5 of 12** | **0 of 9** | historical p withdrawn |
| `return_control=True` | 1.0% | 3.2% (10/314 retained) | historical p withdrawn |
| either path | 3.3% | 6.4% (20/314 retained) | historical p withdrawn |

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
## 4. Task 71 shipped a defect earlier today; I found it the same evening by reading — FIXED

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
two of this block's were wrong. Check the PARENT pid, not the child.

**⟳ Owner asked for the waiter itself to be fixed, not documented.** Done:
`tools/acceptance/wait_for_battery.sh` watches the parent
(`-m tools.acceptance.repetition_battery`), which lives for the whole run, and
cannot exit on a child gap. The reasoning is in the script header so the next
person does not rewrite the one-liner.

**⟳ The second post-fold replicate landed: `377582f0`, 37 turns.** It produced
**0 cluster narrations at all** - the scene never split - so like `75d9f36f` it
is uninformative rather than confirming. **The fold's live evidence is still one
cell** (`d8310b8b`, 2 cluster narrations, 0 eventless). Recorded as it landed,
per the owner's instruction; not re-opened on one thin cell.

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

### ⟳ r2 landed and killed half of this entry

**Kept:** frozen rate 95.2% and 89.7% against the control's 90.8%. Replicates
cleanly. An active player does not unstick the scene, and the confound is
dismissed on two sessions rather than one.

**Withdrawn:** the containment story. HOLD was 29.7% on r1 and **11.6%** on r2
(control 9.1%); GO was 25.0% and **4.2%** (control 12.0%). I wrote *"the room is
quiet with twenty people shouting instructions"* from one session, an hour after
adding a page to the register about exactly this failure. The reading was true of
`5d60575d`. It is not a property of the engine.

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
and the one I re-derived at 27.8% earlier today - **swings between 1% and 51%
across sessions on identical code.** Task 71's cost and value estimates inherit
that spread. I did not restate them, because I do not know which end is typical
and four sessions per era cannot tell me.

---

## 13. The unit-of-analysis error, and what it costs — this block's most important finding

Measured session-to-session variance under **identical code**, four sessions per
group:

| metric | sd | range | sessions to see a 10-point change |
|---|---|---|---|
| **split rate** | **17.9** | 28.6 - 67.3 | **~51 per arm** |
| frozen-position rate | 6.1 | 81.0 - 95.5 | ~6 |
| `return_control` rate | 3.9 | 0.0 - 8.3 | ~3 |
| `empty_audience` | — | **0 or 7** | bimodal; one decision drives all 7 |

**Nearly every test in these files pooled TURNS, including most of mine today.**
One Director decision - sealing a pulpit - produces seven empty-audience records
in one session; one graph shape produces thirty split narrations. The correlated
unit is the **session**, and pooling inside it inflates the effective n by about
an order of magnitude.

**Withdrawn as a result:**

- task 71's leak p = 9.8e-09. Per session it is 70%, 22% before and 0%, 9%, 0%,
  0% after: clean separation, but two informative sessions against four cannot
  beat **p = 0.13**. The task stands on the separation and a unit-tested
  mechanism.
- task 67/71's split-rate p = 1.7e-4. Per session, **72.4 / 17.9 / 75.0** before
  and **52.6 / 29.4 / 0** after - the ranges **overlap**.

**Still sound:** task 64's *"never returned in 5 of 12 sessions versus 0 of 9"*,
because its unit already is the session.

**⚠ NEEDS YOU:** this is the one that should change how you read everything
above, and everything in `.plan/` dated before today. Nothing shipped is wrong
because of it - the code changes stand on tests and on reading - but **the
confidence attached to most numbers in this project is not earned**, and the
split rate in particular cannot support any comparison at the sample sizes we
run.

---

---
# Owner answered — work done against `ANSWERS-2026-08-12-EVENING.md`

## 14. Task 76's falsifier fired, and it moved the fix out of the graph

**§5 said: measure before touching the graph. Measured; the graph stays frozen
and rule 1 is not adopted.**

Over 33 sessions, 403 `zone_moves` with a known origin: **136 (34%) send a
character to a position inside the room they are already in.**

```
Salão dos Quatro Arcos          ->  Salão dos Quatro Arcos, junto ao duto de ventilação
Ala Leste, túnel de manutenção  ->  Ala Leste, túnel de manutenção (lado Garran)
```

The contract invites it in one clause: *"PREFER splitting the stage with
zone_moves (creating a zone if needed)"* whenever self-location differs from
canon.

**⚠ And the contract cannot be fixed alone.** `Scene` holds `zones` and
`positions` and nothing else; `scene_blocking` is scratch that `narrate()` pops.
**There is no way to say "where in the room you are" except by minting a zone,
and a zone is the unit of audibility.** So blocking detail becomes an acoustic
wall by construction. Telling the Director to stop leaves it nowhere to go.

That is the root of task 54 finding 1, task 76, and the prefix rule's two false
positives. **It is a missing field, not a graph bug and not a prompt bug**, and
I handed it to **task 69**, which already owns the storage decision.

The shipped prefix rule stays: correct where it fires, and not the thing standing
between the engine and the defect.

## 15. Everything else in the answers file

- **§2 done** — 77 is now first in wave 2, above 69.
- **§3 done** — 69, 72 and 77 cross-linked, with the "three faces of one thing"
  framing written once in the roadmap and once in each file. Not merged.
- **§4 done** — second post-fold replicate `377582f0` landed with **0 cluster
  narrations at all**, so it is uninformative rather than confirming. The fold's
  live evidence remains one cell. Recorded, not re-opened.
- **§7 done** — P3 accented to match P1; noted that the two sessions already run
  used unaccented text, so a rerun is not byte-identical.
- **§8 done** — `tools/acceptance/wait_for_battery.sh` watches the parent pid.
  The reasoning is in the header so nobody rewrites the one-liner.
- **§12 done** — swept every pooled p-value out of `CHECKPOINT.md`, `ROADMAP.md`
  and task 71, including two that survived the first pass inside a closure item
  and a summary table calling the result *"overwhelming"*.

## 16. ⚠ The working tree arrived older than HEAD

Four `.plan` files came back as a stale copy — the SSH sync, most likely. The
diff would have **deleted decision 13 and reinstated the withdrawn p-values and
the retracted containment claim**: precisely the errors §12 credits me with
fixing. Restored from HEAD; the stale copies are in
`/tmp/alex-tavern-worktree-conflict/` if you want to see them.

Worth knowing because it can happen again, and a careless `git add -A` would
have committed the regression silently.

---
# Round 2 — work against the owner's answers to 14/15/16

## 17. §A — the per-session spread changed my own headline

The owner asked for the spread behind "34% of `zone_moves` are intra-room". It
was worth asking, because **the number is an artifact of naming style.**

| what it counts | pooled | per session (median / sd / range) |
|---|---|---|
| prefix names the origin (hierarchical) | 34% | 15% / 35.0pts / 0-97% |
| contains a positional phrase | 12% | 0% / 19.6pts / 0-79% |
| **union** | **31%** (163/523) | **22% / 31.5pts / 0-95%** |

26 sessions with ≥5 moves; quartiles 0% / 22% / 44%; **8 sessions at zero**.

**The bimodality is two naming conventions for the same act, not two
behaviours.** `a3e1ceda` scores 97% writing *"jardins leste, próximo ao canil"*.
`34390b86` scores **0%** writing *"avançando em direção ao corredor oeste,
posicionando-se entre a aranha e os alunos"* — the purest blocking in the corpus,
invisible to the hierarchical metric because it does not repeat its origin's
name.

So **31% is a floor** and no name-based instrument can pin it tighter. That is
now the argument rather than a caveat: **if a parser cannot tell a room from a
position by its name, neither can the engine.** The case for the field does not
depend on the rate.

## 18. §B — task 79 opened, docs-only

`.plan/tasks/79-blocking-as-durable-state.md`, carrying the question verbatim and
the four decisions demanded before any code: what may read it (**perception must
not**, or the defect is rebuilt), free text against structured, what happens to
the 33 saved sessions, and the falsifier. Added a cheaper second falsifier that
runs **before** any schema: replay a Director turn with a contract offering a
blocking slot and see whether it uses it.

69 now points at 79 instead of owning it; 76 and 54 cross-linked; 76's 34% line
corrected to the union figure.

## 19. §16 — the diagnosis, and I was wrong about the cause

I told the owner "the SSH sync, most likely". **The evidence does not support
that.**

**Ruled out:**
- **git** — reflog is commits only, no reset/checkout/merge/rebase; `ORIG_HEAD`
  is from 2026-08-06, six days stale.
- **a sync daemon** — no rsync, unison, syncthing, mutagen or sshfs process.
- **a shared or network mount** — plain local btrfs subvolume,
  `/dev/vdb[/rootfs_subvol]`, no snapshot directories.
- **timing coincidence with the owner's file** — `ANSWERS` was written 21:40:33,
  **24 minutes after** the last reverted commit (21:16:47), so it did not arrive
  in the same event.

**What is established:** exactly the files touched by four commits in a
2m36s window (21:14:11 → 21:16:47) reverted, and to precisely the state
immediately before that window. Nothing else in the tree moved.

**Most consistent remaining explanation:** an external writer holding pre-21:14
content and flushing it — an editor with stale buffers is the obvious candidate.
**I cannot prove it and am not asserting it.**

**Not recurred.** The tree currently matches HEAD exactly. Per the owner's
instruction, if it happens again I stop and report rather than work around it.

---
# Round 3

## 20. The naming-convention hypothesis — DIRECTIONALLY RIGHT, MECHANISM WRONG

Owner's hypothesis: *the prefix rule can only fire in sessions using the comma
convention, the convention is a per-session coin flip, so the rule is absent in
roughly half of sessions.*

Cross-tabulated over the six post-76 sessions (the only ones where it could fire):

| session | comma-named destinations | genuine sibling pairs | rule fired |
|---|---|---|---|
| `834f91e5` | 0% | 0 | 0 |
| `d8310b8b` | **53%** | **0** | 0 |
| `75d9f36f` | 34% | 3 | **3** |
| `377582f0` | **100%** | 0 *(see below)* | 0 |
| `5d60575d` | 100% | 1 | **1** |
| `d5a2ccf0` | 22% | 0 | 0 |

**Firings match opportunity exactly, 6 of 6.** The rule is not broken and does not
silently skip anything.

**But comma usage does not predict opportunity.** `d8310b8b` is 53% comma-named
with zero sibling pairs; `377582f0` is 100% with none. What the rule needs is not
the convention, it is **two SIBLING zones sharing a prefix**, which is rarer.

`377582f0` looked like a miss and is not one. Its only prefix-sharing pair is
`Academia Real do Primeiro Sino, Salão dos Quatro Arcos` and
`…, Pátio` — **parent and child**, not siblings: the movers came from the Salão,
so the origin rule had already linked both directions and the sibling rule
correctly added nothing and logged nothing. My first count of "opportunity" was
counting parent-child prefix matches, and that was wrong.

**So:** the conclusion the owner drew survives and the reason changes. The prefix
rule **applied in 2 of 6 post-76 sessions**, not because of naming style but
because genuine sibling pairs are rare. That is a narrower and better-evidenced
statement than *"absent in roughly half of sessions because of a style coin
flip"*, and it does **not** support a fifth entry on `metric-validity.md`: nothing
here is an instrument misreading itself, and the rule's own behaviour is exact.

**What does survive from §A, independently:** the Director's naming convention IS
an uncontrolled per-session variable (0–97% on the same code), and every
*detector* that reads zone names inherits it. That is already recorded. The link
from that to `sibling_zones_linked` is the part that does not hold.

**31% is a lower bound, not an estimate**, and adopted as the standing phrasing.

## 21. Is 79 a prerequisite for 77 and 69? — ANSWERED: for 77 in part, for 69 no

Checked against the transcripts each task is built on rather than reasoned from
the framing.

**77's order is half blocking and half room-change:**

> T33: *"**Posicionem-se diante do portão norte agora, em formação!** A seleção
> será concluída dentro da masmorra; **entrem em duplas**…"*

*Position yourselves before the north gate, in formation* has **nowhere to
live** — that is exactly 79's gap. *Enter the dungeon in pairs* is a room change
and `zone_moves` expresses it fine; the Director simply emits `null`.

So **79 is a prerequisite for 77's positional half only.** With a blocking field,
"they formed up at the gate" would be recordable, partial compliance would be
visible, and the Director would have less reason to re-issue. Without it, the
positional half of every order is unrepresentable and silently drops. But 79
would not fix the `zone_moves: null` half, which is 77's other face.

**69 is NOT blocked by 79.** Its re-proposals are world facts, not positions:

> T26/T27/T28: *"Doran golpeia a base de uma pedra caída e uma runa se acende,
> **criando uma protuberância que pode servir de cobertura**"*

"There is now cover at the base of that stone" has a channel —
`scene.physical_facts` — and that channel **exists and is full**:
`_MAX_PHYSICAL_FACTS = 40` with `_evict_oldest_facts`, and `09aabf25` is sitting
at exactly **40 keys**. So 69 is a **capacity and idempotence** problem in an
existing field, not a missing-field problem. Different failure, different fix.

### Recommendation

**Do not move 79 wholesale to the front.** The evidence supports something
narrower and cheaper:

- **79 stays where it is**, docs-only, and gains "77's positional half depends on
  this" as a stated consumer.
- **77 proceeds**, because its `zone_moves: null` half is independent of 79 and is
  the half with a live replay behind it.
- **69 proceeds independently.** Its channel is not missing, it is capped at 40
  and evicting, and one of the two sessions I checked is pinned at the cap.

The owner's worry — *"building the same thing twice"* — does not materialise:
79 builds a position field, 69 fixes a saturated fact store. They are adjacent,
not duplicate. **If 69's storage decision changes `physical_facts`, 79 should
inherit that model**, which is the dependency that is real and is already
recorded in both files.

## 22. §16 CLOSED — owner-attributed, probable, not established

Owner's lead: content left staged, and something restored the tree from the index
or a stash rather than from HEAD. Timeboxed to one pass as instructed.

**Stash: ruled out.** The newest stash in this repo is **2026-08-02**, ten days
before the event, and **none of the four stashes contains a single `.plan`
file**. A stash pop cannot have produced this revert.

**Index: cannot be tested, and the mechanism is hard to reconcile.** `.git/index`
has been rewritten by every commit since, so its mtime says nothing now. More
substantively: `git commit` syncs the index to the new commit, and I committed
those four files *inside* the 21:14-21:16 window, so the index held the NEW
content immediately afterwards. A restore-from-index would have produced the
new state, not the old one.

**Recorded as the owner states it: probable, owner-attributed, not established.**
The supporting precedent is real — `stash@{0}` is literally labelled *"popped by
accident 2026-08-02"*, so index/stash confusion has happened in this repo before.
What is established remains only the shape: exactly the files touched in a 2m36s
window reverted to precisely their pre-window state, no git operation appears in
the reflog, and no sync daemon or shared mount exists.

**Not recurred.** Standing instruction if it does: stop and write it down.


## 23. Routing decided on measurement, not on how interesting the finding felt

Taken under *"you have freedom to choose, based on measures of course"*. Full
detail and the one-line reversals in `.plan/para-o-dono/routing-2026-08-13.md`.

**The rule: a file is in `tasks/` if it has a next action.** Not if its symptom is
big. Applied, six files moved, no claim altered:

- **67, 68, 70, 71, 76 → `closed/`.** Every closure checklist fully discharged
  (9, 8, 5, 8 and 5 items); 70's last open item was 64's re-measurement, which
  ran (5/12 → 0/9); 76's falsifier ran and fired.
- **78 → `backlog/`.** 13 of 1,255 speech records (1.0%), never investigated, no
  next action. `README.md` defines `backlog/` as *"future without active work"*.
- **77 stays in `tasks/` and this is the exception I am flagging rather than
  hiding.** By the rule it should have gone to `backlog/` with 78: both are real,
  sparse and undiagnosed, and 77's leading story is task 72's territory, which is
  gated. It stays because **72's gate cites 77's stalls**, so shelving 77 would
  leave a gated task pointing at a shelved file. Structural, not priority.
- **79 stays in `tasks/`** and its four shape decisions were lifted out of the
  task file onto one page in `para-o-dono/`, which did not exist until today
  although `README.md` has documented it all along.

**What drove it:** the critic protocol makes `backlog/` the default for a new
finding and promotion to `tasks/` an owner decision, and I had opened four task
files (76-79) in one block. Meanwhile `tasks/` was carrying five finished tasks,
so the folder had stopped carrying information at all.

**One inconsistency fixed on the way.** `ROADMAP.md`'s wave-2 table still listed
**77 first** while `CHECKPOINT-2026-08-13.md` had reordered to 79 → 69 → 64 → 77.
Two documents in the same folder disagreeing about the order of the phase is
worse than either being wrong alone. The roadmap now carries the reordered table,
with the ⚠ that the reorder reverses the owner's instruction.

### Priced while writing this: what a schema bump for 79 actually costs

Not asked for, found while answering decision 3, and it changes the question.
`src/store/sessions.py:64` states the convention outright — *"an incompatible
session can never be opened again"* — and `load_game` compares `schema_version`
for exact equality. So bumping 15 → 16:

| | |
|---|---|
| reopening the 33 archived sessions in the app | ❌ permanently refused |
| `material_delta_rate` | ❌ the one metric that goes through `load_game` |
| the main scoring path | ✅ survives, reads `state.json` directly |
| `immersion_scanners.py` and every task-71/76/77 number | ✅ survives, reads `debug.jsonl` |

**So "we do not migrate" costs the app's ability to reopen the batteries and one
metric — and costs the evidence nothing.** That is a cheaper bill than it sounds,
and it is the owner's to accept.

## 24. §16 SOLVED, and it is still happening right now — a SECOND agent shares this working tree

**Found 2026-08-13 13:30, by accident, and it invalidates entry 22's attribution.**

Two Claude sessions are running in this repository at the same time:

| session | pid | started |
|---|---|---|
| `743b2089` (this one) | **31711 `claude -c`** | 2026-08-06, resumed today |
| **`50d16fe0`** | **32226 `claude`** | **2026-08-12 21:14:15 local** |

⚠ **The two pids were swapped in the first version of this entry, corrected
2026-08-13 19:53.** Settled when the owner closed the other session: **32226
disappeared and 31711 survived**, and the transcript still being written is
`743b2089`. **Nothing else in this entry depends on it** — the coincidence that
opens the case is between `50d16fe0`'s first *transcript timestamp* and the revert
window, and transcript timestamps do not come from pids.

**Entry 22's §16 window was 21:14:11 → 21:16:47.** The second session's first
record is **21:14:15 — four seconds after that window opened.** Its transcript
shows it reading and writing `.plan` files continuously from that moment on.

The diagnosis in `746d6c6` said the most consistent remaining explanation was
*"an external writer holding pre-21:14 content"*. **That writer has a name.** A
second agent starting at 21:14:15 read those files as they stood before the four
commits landed, and later wrote them back from its own copy. It explains every
established fact at once, and it is the only candidate that does:

- exactly the files touched in that window, and no others — those are the files
  the other session had open;
- reverted to *precisely* the pre-window state — a stale read, not a merge;
- **no git operation in the reflog** — because no git operation occurred;
- no sync daemon, no shared mount, no stash — all correctly ruled out.

**Entry 22 is superseded.** The owner-attributed stale-index/stash story is
withdrawn: I had already shown the index could not produce it (I committed inside
the window, so the index held the NEW content) and that no stash touches `.plan`.
Both objections stand; the explanation was simply the wrong one, mine included.

### It happened again today, watched live

While staging the routing work of entry 23:

1. I ran `git add -A` and saw three `.plan/closed/` files modified that I never
   touched — 42, 47 and `next-pre-1.0-cleanup`, mtimes **13:29:44, 13:29:58,
   13:30:26**, seconds apart, being translated into English by the other session.
2. I unstaged them. By the time the next command ran, **the other session had
   committed everything in the tree**, including all of entry 23's work, as
   `e53fe17` *"docs(closed): tasks 40, 42, 47 and the pre-1.0 cleanup in
   English"* — a message that says nothing about a routing decision.
3. It also committed **`.claude/settings.local.json`**, a local settings file
   that is not in `.gitignore` and probably should be.

Earlier the same morning I committed `a7a9794` *"case 11 in English"* — which was
**the other session's in-flight translation**, sitting unstaged in the tree. It
then committed its own `5e4b6ac` covering cases 11, 12 and 21. Neither of us knew
the other existed.

**Nothing was lost.** Both sessions' work is in the history and the tree is
coherent: `tasks/` holds 9 files, the six moves landed, `para-o-dono/` exists.
What was lost is the record's ability to say **who decided what, and why** —
entry 23's rationale now sits under a commit message about translating Portuguese.

### The standing instruction, discharged

> *"If the tree ever disagrees with HEAD again, stop and write it down rather
> than working around it."*

Written down. **Not worked around: I am not touching another file in this repo
until the owner decides which session continues.** Two agents committing into one
index will keep producing mixed commits, and the next collision may land in
`src/` where it costs more than a confusing commit message.

**Status: MEASURED for the live event** (two pids, two transcripts, timestamps to
the second, a commit that contains both sessions' work). **OBSERVED, not proven,
for the 2026-08-12 attribution** — the four-second coincidence and the transcript
are strong, but nobody watched that write happen.

## 25. The tree reverted a second time, 19:41:16, and this one was watched

**Standing instruction discharged: stopped, wrote it down, did not work around it.**

At 19:41:16 two files I had committed minutes earlier in `176efcc` appeared as
modified in the working tree. The diff was **81 deletions and 0 insertions** —
purely the removal of what that commit added.

**Established, by md5:**

| | |
|---|---|
| `.plan/para-o-dono/79-blocking-shape.md` | **byte-identical to `176efcc^`** |
| `.plan/reference/metric-validity.md` | **byte-identical to `176efcc^`** |
| both written at | **19:41:16**, 29ms apart |
| no git operation in the reflog | confirmed |

**Byte-identical to the pre-commit state is the signature**, and it is the same
one as entry 24: an external writer holding a copy of the file from before my
commit, writing it back. Not a merge, not an edit, not a conflict — a stale copy
landing on top.

**Session `50d16fe0` was still running**, 11.5 hours in, and had stopped
**committing** since 13:36. *(Written here as pid 31711; that was the swap
corrected in entry 24 — it was **32226**. The owner closed it at 19:52 and 32226
is the process that disappeared.)*

**What is NOT established, and I am not going to guess it.** A human editor with a
stale buffer doing "save all" produces this signature exactly as well as an agent
does, and the owner has been editing `79-blocking-shape.md` by hand — that file is
where their answer was written. Two writes 29ms apart fits either. **The mechanism
is the same as entry 24; the writer is not identified.**

**Repaired, not worked around.** The working-tree version contained **no content
that is not already in HEAD** — the diff is pure deletion — so `git restore`
loses nothing and no other author's work is discarded. Verified before running it.

**Cost this time: zero.** Both files were committed before the revert landed. That
is the only reason this is a note rather than an incident, and it is an argument
for committing in small pieces rather than for trusting the tree.
