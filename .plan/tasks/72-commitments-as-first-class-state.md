# Task 72 — Commitments as first-class state

> **Status:** open, **GATED**. Proposed by a blind narrative reviewer who was
> asked one question the roadmap's author could not answer about his own work:
> *if all the other tasks ship perfectly, is the game meaningfully more
> immersive?*
>
> Its answer was **"cleaner, not alive"**, and this task is the gap.
>
> ---
>
> **Gate, set 2026-08-05.** This task does not start until the post-wave-1
> checkpoint and task 69 have both landed, and the evidence says stalls survived
> them. Two reasons, both recorded rather than argued:
>
> 1. **The roadmap and this file contradicted each other.** The roadmap scheduled
>    72 alongside 69 (*"without it, 69 converts twelve identical doors into twelve
>    distinct ones"*); this file's falsifier says *"if, after task 69, sessions no
>    longer show long stalls, then restaging was the whole of it and the social
>    layer is not needed."* The falsifier wins — it was written to be honoured.
> 2. **This is the largest item in the phase and the only one justified by an
>    argument rather than a count.** Every other task in wave 1 opens with a
>    number (28% of speech records, 100% of P2 turns, 33 empty-audience records).
>    This one opens with a reading. That is not a reason to refuse it; it is a
>    reason to make it earn its start.
>
> If the gate opens, the argument below was right and nothing in it needs
> rewriting. If it does not, say so here and close the task — the prediction is
> already written down, which is the point.

## The argument

Take `base-P1-r1` and imagine every other task in this phase landed. Gone: the
`[indistinct]`, the third-person restatements, the shouts into a void, the double
collapse at T16/T18, the seal changing hands unstaged, control returning to the
player around T20.

What remains: three people walk down a corridor and **every single turn something
opens in front of them.**

| turn | what opens |
|---|---|
| T10 | a tear in the wall |
| T11 | a beam falls |
| T12 | they squeeze through |
| T13 | the way back seals |
| T14 | a body |
| T19 | a chamber |
| T21 | a passage |
| T22 | a tunnel |
| T24 | the floor gives way |
| T25 | a lateral corridor |
| T27 | the ceiling breaks |
| T28 | an explosion |

Twelve openings in nineteen turns. **That is not a repetition defect.** Task 69
stops the same door being unlocked twice; it does not stop a *new* door appearing
every turn. A transition model that says "the ceiling has already collapsed" will
get a cracking wall instead. Twelve identical doors become twelve distinct doors
— better prose, same dead scene.

## The mechanism: three rules that make stillness illegal

Each defensible alone. Together they make it **impossible** to render a turn in
which nothing happens.

1. `perception_events` has `"minItems": 1` (`src/agents/narrator.py:333`). The
   Director **cannot** answer "no event occurred".
2. *"Narrate at least 150 words; a beat deserves full paragraphs."*
   (`src/agents/prose.py:59`).
3. *"Never narrate anyone's silence, hesitation to answer, or non-response — and
   never present someone's stillness or not-moving as an event."*
   (`src/agents/prose.py:46-49`).

Something must happen; it must be described at length; and stillness may not be
described. So the Director invents an opening and the renderer gives it a
paragraph.

The same prompt also contains the fallback *"Nothing new happens; render a short
atmospheric beat"* (`prose.py:263`) — an instruction that contradicts the 150-word
floor in the same message.

**And the escape valve is refused, not unused.** `time_skip_ticks` (1–8) exists
in the schema and the prompt. Corpus-wide the Director set it nonzero on **13 of
482 turns (2.7%)**; three of twelve sessions never skipped at all. In
`base-P1-r2` the engine explicitly signalled *"CLOCK SIGNAL: … Compress time now
(time_skip_ticks)"* on T2, T8, T14, T21, T27 and T34 and received `0` **six times
out of six**. A control signal declined 469 times out of 482 is a design failure,
not an unexploited option.

## The second absence: intentions never become outcomes

Every long stall in the archive is an **unresolved request**.

`base-P1-r2`, Mirella and the staircase — eleven turns:

- T29 *"posso descer e congelar o fluxo antes que alcance Liora. **Autorize-me.**"*
- T30 *"deixe-me descer com Bruna no encalço"*
- T32 *"Deixe-me verter uma casca de gelo sobre o artefato"*
- T36 `[ação] avançar para a borda do duto e **iniciar a descida**`
- T37 `[ação] **descer rapidamente** pela escada do duto`
- T38 `[ação] **precipitar-me para a borda do duto e descer**`

Three separate turns *begin* the descent. Maelis does it too: T30 `iniciar a
descida cautelosa dos degraus`; T31 *"principia a descida"*; T32 and T33 *"ainda
na escada do duto, interrompe a descida"*. She begins twice, interrupts twice,
and neither arrives nor returns.

At T31 Maelis orders *"Vocês cobrem a arquibancada e não descem até eu dar
sinal."* At T32 Mirella asks again. **The refusal never became a fact anyone was
bound by**, because there is nowhere to write "Mirella is forbidden to descend,
and Mirella has accepted that" except the same 40-key `physical_facts` bag that
is already saturated and evicting.

Same shape elsewhere: Riven demands his turn for eighteen turns; Garran is sealed
behind rubble at T16 of `base-P1-r1` and is still digging at T29; in
`null-P1-r2` T5–T8 Maelis's thumb presses the first name-plaque *"mas não a
move"* across four turns and ~800 words.

The engine models rocks falling. It does not model **requests, refusals,
commitments and grants** — the load-bearing beams of scene drama.

## Direction

Same shape as task 69's closed transitions, applied to the social layer:

- a request has a resolution — granted, refused, or deferred **with a stated
  condition**;
- a resolved request cannot be re-raised until the world changes in a way the
  condition names;
- an intention that has been acted on cannot be re-declared as an intention;
- **a turn is allowed to resolve to nothing.** Whatever shape that takes —
  relaxing `minItems`, a first-class "no material change" event, a lower floor
  for empty beats — the pipeline must have a legal way to say the scene held
  still. Note that the stillness prohibition in `prose.py:46-49` exists for a
  reason (narrating non-response reads as padding) and must be reconciled, not
  simply deleted.

## Counter-argument, recorded

*"This is scope creep — the phase is about repetition and leaks, and this is a
new narrative subsystem."* Fair, and it is the largest item in the phase.

> **Its size is no longer an argument against it (2026-08-05).** `AGENTS.md` §2
> makes cost and effort the cheap resources here, so *"this is the biggest item"*
> stops being a reason to gate it. **The gate stands on the falsifier alone**: if
> the checkpoint shows stalls survive task 69, this ships, however large it is.
> If stalls do not survive 69, it closes — also regardless of size.

But the
argument for it is not aesthetic: without it, task 69's measured success would be
*"the ceiling stopped collapsing three times"* while the scene still does not
move, and the failure mode becomes harder to detect — three novel things happen
per turn instead of one thing three times. If that trade is acceptable, this task
can be deferred **explicitly**, with the prediction written down so the next
battery can check it.

## Closure evidence required

- [ ] a request record type with a resolution, asserted against the real prompt
      builders;
- [ ] a resolved request cannot be re-raised without a stated condition being met
      — test with the Mirella sequence replayed;
- [ ] a turn may legally produce no material change, and the prose path renders
      it without violating the stillness rule;
- [ ] the `prose.py:59` / `prose.py:263` contradiction removed;
- [ ] `time_skip_ticks` acceptance rate measured before and after; if the valve
      is still declined ~97% of the time, the valve is the wrong mechanism and
      that goes in writing;
- [ ] the durable-state interface from task 69 is **reused**, not re-invented;
- [ ] measured on a live cell: consecutive turns with no net state change fall,
      and the blind read confirms the scenes read as *held*, not as *empty*.

> **Corrected 2026-08-05.** The last item used to end *"and `NSR` does not fall
> with them"*. That was **unsatisfiable by construction.** `NSR` is
> `len(novel) / turn_count` over lexically-novel stimuli
> (`repetition_metrics.py:555,609`). This task's central deliverable is *"a turn
> is allowed to resolve to nothing"* — a turn that resolves to nothing
> contributes zero novel stimuli, so `NSR` **must** fall if the task works. The
> same applies to `SIL`, which is `0.0` in 16/16 archived runs precisely because
> `minItems: 1` and the 150-word floor forbid the silence this task is trying to
> legalise; a nonzero `SIL` after this ships is the *feature*.
>
> The real risk this criterion was reaching for is real: a scene that holds still
> because it is *paused* reads the same to a metric as one that holds still
> because it is *tense*. Only a reader can tell those apart, so the gate is the
> blind read. See `.plan/ROADMAP.md` §"The acceptance gate this roadmap shipped
> with was inverted".

**The measurement that would falsify this task:** if, after task 69, sessions no
longer show long stalls, then restaging was the whole of it and the social layer
is not needed. **This is now the gate in the banner, evaluated at the checkpoint,
not a retrospective note.**
