# Task 64 — Return control to the protagonist

> **Status:** open, **and now re-scoped by measurement.** **Wave 2, after 69.**
> The battery this task demanded has run (2026-08-12, nine sessions): the
> never-returned count is **5 of 12 → 0 of 9**, and reading every
> `return_control` turn shows the Director picks the right moments and simply
> picks few. **This is a calibration problem, not a missing mechanism** — do not
> design a new trigger. See "The battery has run" below.
>
> Two blind reviewers destroyed both of this task's original trigger designs and
> one of its citations. What survives is a well-measured *problem* with no
> validated *mechanism*, and this file says so rather than pretending otherwise.
> **Do not design the trigger before task 70 lands and is re-measured.**
>
> **70 landed and was re-measured, 2026-08-06.** The gate is open, and the
> numbers below are stale — see the box immediately after them.

## ⚠ First post-70 measurement — 2026-08-06

Session `34390b86`, a 40-turn P2 base cell run with the named exclusion removed
from the Director prompt:

| | archive, WITH the exclusion | fresh cell, WITHOUT it |
|---|---|---|
| `return_control=True` | 5 of 482 turns (**1.0%**) | 2 of 40 (**5.0%**) |
| controlled character routed | 11 of 482 (**2.3%**) | 1 of 40 (**2.5%**) |

**Removing the instruction moved `return_control` about fivefold and left PC
routing flat.** That is the direction task 70 hypothesised, and it means this
task's problem statement is measured against an engine that no longer exists.

**It does NOT resolve 64.** 5% is still low, both samples are tiny (2 events
against 5), and one cell cannot re-take the number that matters most here —
*"control never returned by either path in 5 of 12 sessions"*, which needs a
battery. **Re-measure across several sessions before designing any trigger**,
and treat the table below as the pre-70 baseline rather than the current state.

## ✅ The battery has run — 2026-08-12, nine post-70 sessions

323 Director turns across nine sessions (`34390b86`, `d0cc98e5`, `00997daa`,
`b11b38dc`, `55d03896`, `21f7c4e1`, `c76037ff`, `09aabf25`, `54bcdace`).

| signal | pre-70 (482 turns, 12 sessions) | **post-70 (323 turns, 9)** | |
|---|---|---|---|
| `return_control=True` | 5 (1.0%) | **10 (3.1%)** | p = 0.059 |
| controlled character routed | 11 (2.3%) | **10 (3.1%)** | — |
| either path | 16 (3.3%) | **20 (6.2%)** | p = 0.057 |
| **sessions where control NEVER returned** | **5 of 12** | **0 of 9** | **p = 0.045** |

**The number this task said needed a battery is now zero.** Every one of the
nine sessions hands control back at least once. That was the strongest single
statement in the problem section and it no longer describes the engine.

### And the read says the trigger is not broken — it is shy

Per-turn rates are still low, so the tempting conclusion is that the mechanism
picks badly. Reading every `return_control` turn says the opposite. They are all
the same shape, and it is the right one — a held beat with the outcome open:

> **T11** *"o silêncio que se segue é espesso, como se o próprio ar aguardasse o
> próximo movimento"* — the creature still, everyone's hand drifting to a weapon.
> **T23** Riven steps up to the mural, blade raised, the map beginning to breathe.
> **T24** *"a diretora … hesita por um instante, o metal tremendo na mão,
> enquanto os alunos … recuam alguns passos"* — the threat now holds the only exit.

Not one is a lull or a hand-off in the middle of somebody else's sentence. The
Director gives the turn back exactly where a player would want it.

**That reframes the task.** It was written as *"the trigger is missing or wrong"*.
The evidence says the trigger exists, chooses well, and fires **rarely** — a
calibration problem, not a design one. A task that designs a new mechanism would
be replacing something that works.

**Recommended re-scope:** ask why a Director that recognises these moments only
declares them ~3% of the time. The first place to look is the contract wording
for `return_control`, not a new trigger, and the pre-70 lesson applies directly —
removing one sentence tripled this number without anybody designing anything.

## The problem, measured (PRE-70 — see the box above)

Corpus-wide across 482 Director turns in twelve sessions:

| signal | rate |
|---|---|
| `return_control=True` | **5 turns (1%)** |
| controlled character routed as a speaker | **11 turns (2.3%)** |
| sessions where control never returned by either path | **5 of 12** |

Control reaches the human on roughly 3% of turns. This is not an anomaly in one
session; it is the engine's steady state, and the blind reader ranked stall the
worst pattern in the archive.

The sharpest instance, `base-P1-r2` **T30–T39** — ten turns, verified:

```
T30  return_control=None   next_speakers=['C8','C3','C17']
T31  return_control=None   next_speakers=['C3','C8','C17']
…
T39  return_control=False  next_speakers=['C17','C3','C8']
```

The same three NPCs, every turn. Meanwhile the fiction is screaming for the
player: *"Link, agora! Abra o portal para Liora…"* recurs from T33 to T36. The
scene's resolution is held by a character the engine will not route.

Burst exits over the session: `player_addressed` once (T2), then
`budget_exhausted` five times at T8/T14/T21/T27/T34 — **neither designed exit
fired for 32 turns across five consecutive bursts.**

## What the first draft got wrong

**1. The structural trigger would not have fired.** It proposed: *N consecutive
turns with no player action **and no new physical state change** returns control.*
But at T34–T39 every turn carries a fresh event — a beam falls, a duct is
revealed, Liora dies. They are restagings, and **knowing that is exactly what
task 69 builds**. Ship this trigger before 69 and it does not fire on the session
it was written for. **64 depends on 69.**

**2. The textual citation was false.** The draft rejected `docs/cases/21`'s
signal ("the Director's own events name the PC") as *"text heuristics over model
output"* — and then cited *"Link, abra o portal"* as its own evidence. Verified:
that string appears **0 times** in `perception_events` and **6 times** in
character-agent speech. The only channel where it exists is the one the draft
rejected. Case 21 was right that the fiction names the PC; the draft was wrong
about where.

**3. The exclusion arithmetic was wrong.** The draft said
`BURST_PROTAGONIST_EXCLUDE_BEATS = 2` cannot be the cause because "the standoff
is six times longer than the exclusion". But `exclude_controlled` **defaults to
`True`** (`runner.py:2401`) and is only overridden inside the burst loop
(`runner.py:1150`), so it re-arms on the first two beats of every burst and on
every non-burst turn. Measured: present on **16 of 39 turns (41%)** in
`base-P1-r2`, including T33/T34/T35, and on **100%** of turns in every P2 cell.
The conclusion survives — 7 of the 10 stall turns were unconstrained, so the
exclusion is not sufficient — but the stated reasoning did not.

**4. `_beat_settled` has four exits, not two** (`runner.py:1519-1536`):
`controlled in queue`, `return_control`, empty `perception_events`, and
`narrator_only_streak >= 2`. The last two never fire here because NPCs always
respond, which resets the streak.

## Why this waits for task 70

`AGENTS.md` §3 states the designed control-return path:

> quando o Narrador escolhe o personagem controlado como próximo falante, o
> Runner devolve o controle ao humano

That is the primary mechanism, and task 70 shows the Director prompt is actively
instructing against it on 33–100% of turns (`narrator.py:531-534`, naming the
controlled character in an exclusion clause). **It is plausible that 70 alone
substantially fixes this**, and designing a new trigger against numbers taken
while that instruction was in the prompt would be building on a confounded
baseline.

Sequence: land 70 → re-measure `return_control` and PC-routing rates on one cell
→ write this task's trigger against the new numbers.

## Candidate triggers, none validated

Kept as options, explicitly not a decision:

- **Post-69 structural.** Once "already staged" exists, "no *new* physical state
  change for N turns" becomes meaningful and is the cleanest signal.
- **The fiction names the PC.** Case 21's proposal. It lives in character speech,
  not Director events — which makes it a check over a persisted record against a
  known cast id, not a heuristic over free text. Cheaper than it was dismissed
  for being.
- **Burst exit accounting.** Five consecutive `budget_exhausted` exits with no
  `player_addressed` is itself a detectable pattern and needs no state model.

Note the tension to resolve in whichever is chosen: `AGENTS.md` §4 says the
Runner holds *"agência, ordem das chamadas, estado, locks, persistência e
routing"* but *"nunca decisões narrativas heurísticas"*. Returning control is
agency, which is squarely the Runner's. Inferring *when* the story needs the
player is closer to a narrative judgement, and the chosen trigger has to sit on
the right side of that line.

## Closure evidence required

- [ ] task 70 landed and control-return rates re-measured **before** any trigger
      is designed; the new numbers written into this file;
- [ ] whichever trigger is chosen, a test replaying `base-P1-r2` T30–T39 that
      shows it firing;
- [ ] a test that it does **not** fire during a healthy burst where the world is
      genuinely reacting;
- [ ] no new prompt text that separates exactly one character (task 70's
      invariant must not be reintroduced by this task's fix);
- [ ] measured on a live cell: sessions where control never returns fall from
      5/12 (`NSR` reported, not a gate — `.plan/ROADMAP.md`).

**The measurement that would falsify this task:** if control-return rates recover
after task 70 alone, there is no trigger to build and this closes as resolved.
**This is evaluated at the post-wave-1 checkpoint**, and it is the most likely
task in the phase to close without being built.
