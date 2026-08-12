# Task 77 — The order that nobody executes

> **Status:** open, found 2026-08-12 by **reading a session as fiction**, not by
> any metric. No metric in this project reports it, and the one measurement I
> tried failed its own control — that failure is recorded below so nobody
> re-derives it.
>
> This is the phase's headline complaint, *"the scene does not move"*, caught in
> the act with a transcript rather than a number.

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

**Three turns. The same order four times. Nobody enters the gate.** Asword says
the identical sentence at T31 and T33 with one clause changed. Everyone agrees
with the order every time, and the world does not advance past it.

The same shape at `09aabf25` T15-T17 (*"A seleção é antecipada: entrem na
masmorra agora, em duplas"* twice, plus Garran's echo), and at `b11b38dc`
T22-T23.

**This is not a repetition defect.** A commander repeating an ignored order is
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
2 is the one I would investigate first on the evidence above: at T33 Asword's
   `action` field literally reads *"avançar com Link em direção ao portão norte"*
   and his position does not change.
3. **The prompt asks for intent rather than outcome**, so agents describe what
   they are about to do forever.

**Do not design a fix before deciding which of these it is.** All three would
produce identical transcripts.

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
