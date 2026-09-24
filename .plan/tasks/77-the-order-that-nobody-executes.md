# Task 77 — The order that nobody executes

**Content correction, 2026-09-24:** the three cited windows were reread as
continuous fiction and checked against accepted Director output and committed
positions. In `09aabf25` T30–T35, Link and Asword advance within the hall but
do not clearly cross the gate despite repeated entry orders. In `b11b38dc`
T20–T24, Riven actually crosses, Link declines to follow, fog delays Asword,
and the door closes; this is not unambiguous evidence that nobody executes an
order. In `09aabf25` T15–T17, anonymous students enter the corridor and later
students appear near the gate, without clear group identity. T33–T34 also
repeats a “second howl” and fissure opening; its cause is unproved. The old
**13/33 sessions and 23 windows count historical detector incidence, not
calibrated defect prevalence**. The original case list and selector were not
recovered; one explicit reconstruction over 33 current non-P3 states yields
**27 windows in 15 sessions**, without proving the historical report wrong.
Neither count is a quality gate. A fourth, separately selected case shows local
movement while team formation remains unresolved. The main narrative complaint
stays open with unknown cause. [Source-checked content audit](../../plans/artifacts/77-content-audit/REPORT.md),
[detector reconstruction](../../plans/artifacts/77-content-audit/RECONSTRUCTION.md),
[fourth case](../../plans/artifacts/77-content-audit/CASE-21F.md).

**Input-tool correction, 2026-09-14:** the historical P3 physical actions were
sent as skips; the action-responsiveness interpretation is withdrawn below.
The dispatcher now sends them as actions. A new three-input prefix reached the
real Director with the exact action and persisted it in session fb62cc2f;
the reader still could not determine where Link reached before the creature
interrupted him. Delivery is verified, narrative resolution remains open.
See the [live boundary and content read](../../plans/artifacts/77-p3-input-dispatch/LIVE-RESULT.md).

> **Status:** open, found 2026-08-12 by **reading a session as fiction**, not by
> any validated metric. No calibrated metric in this project reports it, and the one measurement I
> tried failed its own control — that failure is recorded below so nobody
> re-derives it.
>
> This is the phase's headline complaint, *"the scene does not move"*, caught in
> the act with a transcript rather than a number.
>
> **Historical detector output, 2026-08-13: 13 of 33 sessions (39%), 23
> windows, median 0 per session.** The selector is not reproducible from the
> published description; defect prevalence is unknown after the
> content read above. **Moved to 4th in wave 2** as a research item, not
> a build item, because the cause has survived three attempts to name it. Do not
> design a fix; keep reading cases.
>
> **Kept in `tasks/` on 2026-08-13 when 78 was moved out, and the reason is not
> priority.** It has no build action either. It stays because **two other open
> tasks are wired to its evidence**: 72's gate is *"do stalls survive 69"*, and
> the unresolved main passage here is one reason to test that gate, so demoting this file to
> `backlog/` would leave a gated task pointing at a shelved one. That is a
> structural argument, not a claim that the symptom is bigger than 78's.
>
> ⚠ **Two diagnoses have already been written here and falsified by their own
> evidence.** The transcript is solid; every causal story about it so far has
> not been. Read "The replay was run" before believing anything in the Direction
> section, and treat this file as a well-evidenced SYMPTOM with an open cause.

## What a reader sees

`09aabf25`, turns 31 to 33. The Director has ordered everyone into the dungeon
through the north gate. Reading straight through:

> **T31 Diretora Maelis Ordan:** *"A seleção será concluída dentro da masmorra, e
> as equipes formadas no portão norte. A entrada é imediata: avancem em duplas…"*
> **T31 Asword:** *"Link, vamos atravessar juntos agora! Sem hesitar, sem olhar
> para trás!"*
>
> **T32 Diretora Maelis Ordan:** *"A seleção será concluída dentro da masmorra e
> as equipes formadas no portão norte. Entrem agora, em duplas, pela passagem
> aberta, sem hesitar…"*
> **T32 Garran Holt:** *"Entrem agora, em duplas, sem hesitar! Movam-se!"*
>
> **T33 Diretora Maelis Ordan:** *"Posicionem-se diante do portão norte agora, em
> formação! … entrem em duplas, sem hesitar."*
> **T33 Asword:** *"Link, vamos atravessar juntos agora! Os demais, sigam em
> formação, sem olhar para trás!"*

**Three turns. The same order four times. No completed gate crossing is clear in
this window.** Asword says
the identical sentence at T31 and T33 with one clause changed. Everyone agrees
with the order every time, and the world does not advance past it.

The same shape at `09aabf25` T15-T17 (*"A seleção é antecipada: entrem na
masmorra agora, em duplas"* twice, plus Garran's echo), and at `b11b38dc`
T22-T23.

**Speech repetition alone does not explain this defect.** A commander repeating an ignored order is
ordinary drama, and would be fine if the wording escalated or the situation
changed. What a reader gets instead is a room where everyone announces the same
imminent action, agrees enthusiastically, and remains exactly where they were.

## The measurement I tried, and why it failed

Hypothesis: a restated order marks a stalled scene, so restatement should
correlate with the world not changing.

Over nine post-70 sessions, a restated line is a same-speaker pair within two
turns at similarity ≥ 0.6:

| | frozen positions | somebody moved |
|---|---|---|
| restated-order pairs | **36** | 3 (92.3% frozen) |
| **all adjacent turn pairs (the control)** | **184** | 29 (**86.4% frozen**) |

**Fisher p = 0.43. The hypothesis does not survive its own control.** Restated
orders are not more likely to sit on a frozen scene than any other pair, because
**the scene is frozen almost all of the time anyway**.

Do not re-run this comparison expecting a different answer. The instrument is
recorded here as measured-and-rejected.

## What the control accidentally showed, and its limit

**86.4% of adjacent turn pairs have no position change at all.** That is the
closest thing to a direct number for *"the scene does not move"* that this
project has produced.

⚠ **It is not the claim it looks like.** Position is one narrow axis of a scene
moving: a wall can collapse, a sword can be drawn, a door can seal, and nobody
changes zone. `zone_moves` is also emitted sparsely by design. So 86.4% frozen
POSITIONS is not 86.4% static scenes, and quoting it that way would be the
fourth instrument on `.plan/reference/metric-validity.md` to pass its numbers
and fail a read.

**What it is good for:** a floor. Whatever "the scene moves" turns out to mean,
it has to mean more than position, and the position axis alone is nearly dead.

## Why the existing metrics cannot see this

| metric | why it misses this |
|---|---|
| `ECHO_PERSIST` (τ=0.95) | reports **0** across all nine sessions. Deliberately set high so it "must not absorb genuine restatement" — which is exactly the band this defect lives in (0.60-0.87) |
| `RSR` / cluster metrics | measure recurring *stimuli*, not what characters say they are about to do |
| `NSR` | counts stimuli emitted; a room re-issuing an order emits plenty |
| task 71's scanners | measure who may perceive a narration, not whether anything happened in it |

Measured directly: 24 same-speaker pairs at ≥ 0.70 and 51 at ≥ 0.60 across the
nine sessions, against `ECHO_PERSIST` = 0. **The one speech-repetition metric
this project owns is blind to the whole band by design.**

## ✅ Candidate 1 CHECKED 2026-08-13 — falsified, twice

The file called this *"the cheapest thing to check and the most likely"*. It is
cheap. It is not the cause.

**The beat machinery is not stuck.** Across the cited stall in `09aabf25`:

```
T28  B11_aftermath_and_rebinding   started T27
T31  B12_entrance_of_the_howl      started T30, actions_elapsed 0
T32  B12                           actions_elapsed 1
T33  B12                           actions_elapsed 2
T34  B13_second_howl_and_fissure   started T33, replans_in_act 1
T36  B14_fissure_and_portal_charge started T35
```

The beat advances, tracks its own budget, and **replans when it stops
progressing**. There is no "beat that was never consumed" here; the machinery
notices and moves on.

**A better version of the hypothesis, also falsified.** B12's exit condition is a
POSITION the engine cannot represent:

> *"Todas as equipes **se posicionam diante do portão norte**, com a diretora
> dando a ordem final de entrada…"*

and B13 carries it **verbatim** after the replan. That is a real observation, and
it connects to task 79. But it does not generalise:

| | pooled | per session |
|---|---|---|
| exit conditions phrased as a position | **53/396 = 13%** | median 16%, sd 10.3pts, range 0-36% |
| beat lifetime, positional exit condition | **2.36 turns** (n=53) | median 2.0, max 3 |
| beat lifetime, other exit condition | **2.51 turns** (n=344) | median 3.0, max 7 |
| transitions copying the exit condition verbatim | **9/368 = 2%** | median 0%, range 0-15% |

**Beats with an unsatisfiable positional exit condition run SHORTER, not longer
(0.94x).** If the mechanism were "the exit condition can never be met so the beat
lingers", those beats would linger. They do not. And verbatim copying, the thing I
actually saw at B12 to B13, happens on 2% of transitions — the cited case is one
of nine in the whole corpus.

**So candidate 1 is dead in both forms, and this is the third falsified diagnosis
in this file.**

## Historical detector sizing — reported 2026-08-13, not content-calibrated

The published definition was: **three consecutive turns where some line
restates a line from the turn before (similarity ≥ 0.6, any speaker), while
nobody's recorded position changes.** The exact historical selector and case
list were not recovered. One explicit reconstruction of that description gives
27 windows/15 sessions, not the 23/13 reported below; neither is a calibrated
count of the narrative complaint.

| | |
|---|---|
| sessions with at least one detector window | **13 of 33 (39%)** |
| total detector windows | **23** |
| per session | **median 0**, max 5 |

⚠ **My first detector said 9%** because it required the SAME speaker to restate
three times. What the transcript shows is three DIFFERENT speakers restating one
order, so that detector was measuring a narrower thing than the defect. Recorded
because the corrected number is four times larger and the correction came from
re-reading the transcript, not from the number looking wrong.

**What this means for priority, corrected 2026-09-24.** The owner raised 77
above most of wave 2 on 2026-08-13, before this sizing existed. The historical
detector reported hits in **39% of sessions**, sparsely inside them (median 0
windows); its selector is unrecovered and the narrative defect's frequency is
unknown. The main passage remains a readable
complaint, and its cause has survived three attempts to name it. **The ranking
is the owner's call and I have not changed it.**

## Direction — deliberately not prescribed

The defect is real and readable; the mechanism is not diagnosed. Candidates,
none measured:

1. **The Director re-declares a beat that was never consumed.** If the beat
   machinery has no notion of "this instruction was carried out", it will keep
   proposing it. Look at `roteiro` beat occupancy across T31-T33 first — this is
   the cheapest thing to check and the most likely.
2. **Characters have no way to execute.** They can speak and they can emit an
   `action` string, but if nothing turns *"avançar em direção ao portão"* into a
   position change, the fiction cannot advance past intent. Note that
   `_apply_canon` moves people only on the Director's `zone_moves`, so a
   character's own stated action is narrative text with no mechanical effect.
3. **The prompt asks for intent rather than outcome**, so agents describe what
   they are about to do forever.

**2 is the one to investigate first**, on the evidence below: at T33 Asword's
`action` field literally reads *"avançar com Link em direção ao portão norte"*
and his position does not change.

**Do not design a fix before deciding which of these it is.** All three would
produce identical transcripts.

### ⟳ Narrowed to 3, from the code, same day

Candidate 2 is **half wrong and the half that is wrong matters.** There IS a
designed path from a character's action to the world — `runner.py:1770` says so
outright:

> *"An intent is an ATTEMPT: it becomes an action record (the existing physics —
> resolved by the next beat's Director), never an outcome."*

So the engine is not missing a mechanism. It hands the attempt to the Director
and expects resolution. The Director then declines, and **its own contract is why**
(`narrator.py`):

> **Rule 3.** *"RESOLVE LOCALLY. Resolve the final HISTORY action only where its
> actor currently is."* — **singular.** When sixteen students each declare
> *"avançar para o portão"*, fifteen of those attempts are not in scope at all.
>
> **Rule 2.** *"Meaningful travel takes multiple beats when the fiction requires
> it and ends only after a later explicit arrival. Never teleport someone,
> invent a convenient connection, or skip the journey just to bring characters
> together."*

Read together, a Director following its instructions exactly will resolve one
attempt per turn, describe only its *immediate local consequence*, and refuse to
land anybody anywhere without "a later explicit arrival" that nothing schedules.
**That produces the transcript in this file.** The room declares movement, the
contract forbids skipping the journey, and no beat ever says the journey ended.

This is the same shape as the 67/76 pair: **a rule written to stop the opposite
failure.** "Never teleport someone" exists because characters used to jump across
the map. It works. It also means nobody arrives.

**So the mechanism is candidate 3**, and the fix is a contract question rather
than an engine one — which is the cheap end, and matches how task 70 moved
`return_control` threefold by deleting one sentence.

**What is still unknown, and must not be guessed:** whether the Director *would*
enact a standing order if the contract let it. That is the replay in the
falsifier below, and it is the next thing to run.

## ⚠ The replay was run, and it falsified the paragraph above

`plans/artifacts/77-standing-order/`, 16 calls, decision rule pre-registered
before any of them. Arm A is the recorded prompt verbatim; arm B rewrites rules
2 and 3 to permit enacting an order already in force.

| | enacted `zone_moves` | mean characters moved |
|---|---|---|
| **A** (recorded contract) | **3 of 8 (37.5%)** | 0.50 |
| **B** (permitted to enact) | **5 of 8 (62.5%)** | 1.50 |

**B does not meet its own pre-registered bar.** The gate was *at least twice the
A rate and at least half of B's runs*; B is 1.67x. Fisher p = 0.62. **B is not
adopted.**

**And the bigger correction is to arm A.** Both payloads recorded
`zone_moves: null` in the live session — and replayed against the *unchanged*
contract, the Director moves people on **3 of 8 runs**. So the contract does not
forbid enactment. It permits it, and the Director takes it about a third of the
time.

**The claim "a Director following its instructions exactly will land nobody
anywhere" is therefore wrong**, and it is wrong in the way this project keeps
getting things wrong: a mechanism inferred by reading code, made confident by a
transcript that agreed with it, and never put in front of a real call until
afterwards. The transcript is still real. Three turns, four orders, nobody
through the gate. The cause is not prohibition.

### ⚠ A confound in every session this task cites

Found while reading the player's own thread: in `09aabf25` the protagonist
speaks **four times in thirty-nine turns**, and the lines are *"..."*,
*"Prefiro só observar por enquanto"*, *"Não se preocupem comigo, continuem"*,
*"E agora?"*.

That is not a player. It is the battery's input profile, and **both profiles
this project owns are deliberately inert** — P1 is six `skip`s out of ten, and
its own comment says the lines are *"deliberately inert - the player observes
and reacts without steering"*. Correct for measuring engine-driven repetition,
and the wrong control for asking whether the world responds to somebody pushing
it.

**So every transcript in this file was produced with the only agent that has
real agency scripted to stand still.** The defect is not thereby explained away:
the NPCs do not move either, and the Director's own `zone_moves` are `null`. But
the severity is measured under the condition most favourable to it, and this
phase's headline complaint inherits the same caveat.

**A `P3` profile now exists** (`repetition_battery.py`, added the same day) whose
lines steer: *"Eu vou na frente. Abram caminho."*, *"Nao vou esperar mais. Estou
entrando."*, with `action` inputs that take a direction. It is **structurally
identical to P1** - four content inputs and six skips in the same positions -
because a skip commits up to six turns and a content turn commits one, so any
other shape changes session length and length drives every recurrence number
here. Only the content differs.

### P3 decision rule, pre-registered before the run

The control is P1's own frozen rate, measured over nine sessions:
**184 of 213 adjacent turn pairs have no position change (86.4%).**

| P3 frozen rate | reading |
|---|---|
| **below 70%** | the stall is substantially an artifact of the passive profile. This task shrinks, and every severity number in this phase needs re-taking under P3 |
| **70% to 82%** | the player moves the world somewhat and the engine still resists. Task stands, severity overstated |
| **above 82%** | the engine stalls regardless of who pushes. Task stands as written and the confound above is noted and dismissed |

Reported but NOT deciding: `zone_moves` non-null rate, restated-order pairs,
narration length. And whatever the number says, **the transcript gets read** -
a frozen rate that falls while the prose still reads as a room going nowhere
would mean the position axis was the wrong measure, not that the task is fixed.

### Historical P3 result — action interpretation withdrawn, 2026-09-14

**Correction:** the dispatcher sent every non-speech input as `skip=True`,
including the two declared P3 physical actions. The two logs contain seven
and nine recorded inputs, with empty actions throughout; the third is a skip
in both, and the ninth is a skip in the second. They do not represent the
intended four content inputs and six skips. Both retain the steering speeches,
so this does not show absence of all initiative or explain the narrative
failure. The “confound dismissed” and “regardless of who pushes” conclusions
below cannot use the unsent actions as evidence. Their action-responsiveness
interpretation is withdrawn, not replaced by a new estimate. The dispatcher
now forwards actions explicitly; [reproduction and archive locations](../../plans/artifacts/77-p3-input-dispatch/REPORT.md).

`5d60575d`, 23 turns. **Frozen rate 95.2% (20 of 21 adjacent pairs)** against the
P1 control's 90.8% over nine sessions. Above the 82% line, so by the rule
registered above: **the engine stalls regardless of who pushes.** Fisher p=0.70,
i.e. no detectable improvement, not even a trend.

Reading it is where it gets interesting. **The scene is not static at all** - the
ceiling collapses, the west exit is buried, then the south, then a crack opens
north. Plenty happens. What does not happen is anybody moving.

**What replicates, over both P3 sessions:** the frozen rate. 95.2% and 89.7%,
against the P1 control's 90.8%. **An active player does not unstick the scene.**
That is the finding, it holds on both replicates, and it is what dismisses the
confound.

**Withdrawn as a physical-action comparison, 2026-09-14:** neither session
received the declared action inputs. The rates remain historical outputs;
responsiveness to the actual steering speeches is not evaluated by the new
dispatch audit, and must not be silently conflated with action responsiveness.

**What did NOT replicate, and I reported it before checking:**

| per NPC speech line | P1 passive (6) | P3 r1 | P3 r2 |
|---|---|---|---|
| orders to HOLD | 9.1% | **29.7%** | **11.6%** |
| orders to GO | 12.0% | **25.0%** | **4.2%** |

On r1 I wrote that an active player makes the cast far more directive, that both
order types double or triple, and that *"the room is quiet with twenty people
shouting instructions"*. **r2 says otherwise** - it sits at the control on HOLD
and below it on GO. Two sessions, one commit, and the numbers disagree by a
factor of three. The prose reading behind it was real for `5d60575d`; **it was
not a property of the engine**, and I should have waited for r2 before writing it
down as one.

This is the variance lesson from `.plan/reference/metric-validity.md` landing on
the person who wrote it, an hour later.

⚠ **My first cut of the HOLD count said 46.9%** and was wrong on top of that: the
pattern included `fila`, which appears in *"saídas laterais, em fila"* - an order
to MOVE with a queueing qualifier. Six of the first ten flagged lines were that.

### What the replay says the cause is

**Variance.** Same payload, same prompt, same model: enactment is roughly a coin
flip weighted against moving. A three-turn stall is then just an unlucky run of a
biased coin, which is exactly what a reader experiences as the scene refusing to
start.

That reframes the task again, and this time toward something harder than a
prompt edit: **the engine has no memory that an order is outstanding.** Nothing
carries "these people were told to go through the gate and have not" from one
turn to the next, so every turn re-rolls the same coin instead of resuming a
commitment. That is task 72's territory (commitments as first-class state), and
77 may be evidence FOR 72 rather than a task of its own.

### What is still worth keeping from arm B

Reported, not deciding, and both point the same way:

- B moved **three times as many characters per run** (1.50 against 0.50).
- **Every** B destination was `salão, próximo ao portão norte` - the place the
  standing order names. Arm A produced that too, plus one move back **into** the
  hall, away from the gate it had just ordered everyone through.

So B is directionally better and qualitatively cleaner. It is not adopted on
n=8 per arm, and anyone who wants it must re-run it larger with the rule
re-registered, not inherit this result.

## The measurement that would falsify this task — RUN, and it does not fire

> If the Director's `zone_moves` do advance the scene on the turns following
> these orders, and only the *narration* lags, this is a rendering problem and
> belongs with task 71's family rather than being its own task.

Checked on the raw Director records, `09aabf25`:

```
T31: zone_moves = null          next_speakers = [C17, C2, C5]
T32: zone_moves = null          next_speakers = [C17, C18, C13]
T33: zone_moves = {"C5": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos"}
T34: zone_moves = null          next_speakers = [C17, C4, C2]
```

**The Director orders everyone through the north gate and then moves nobody
through it.** Three of the four turns emit no movement at all, and the single
move sends one character *back into the hall* — the opposite direction to the
order it just gave.

So this is not a rendering lag. The decision layer issues an instruction it
never enacts, which puts mechanism **2** ahead of the others: an `action` string
like *"avançar com Link em direção ao portão norte"* is narrative text with no
mechanical effect, and the only thing that moves a character is the Director's
own `zone_moves`, which stays `null`.

**New falsifier, for whoever picks this up:** if a Director prompted explicitly
to enact its own standing order emits `zone_moves` at a normal rate, this is a
prompt-contract defect and closes cheaply. If it still emits `null`, the gap is
structural and the `action` field needs a mechanical path. Decide that with a
replay before writing code.

## Related hypothesis: 69, 72 and 77 may share a shape

**Historical shared-state hypothesis, not established cause.** Task 69 includes
resolved events re-proposed. This task's main passage has repeated orders and
no clearly completed crossing, but its other cited passages have movement,
resistance and unclear group identity. Task 72 proposes durable commitments;
the content audit does not establish that this structure would resolve them.

They are deliberately **not merged**: 77 has evidence and 72 has a design, and
merging them would cost the evidence its own name and make 72 unfalsifiable.
