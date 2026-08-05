# Task 64 — Return control to the protagonist

> **Status:** open, **and deliberately under-specified**. **Wave 2, after 69.**
>
> Two blind reviewers destroyed both of this task's original trigger designs and
> one of its citations. What survives is a well-measured *problem* with no
> validated *mechanism*, and this file says so rather than pretending otherwise.
> **Do not design the trigger before task 70 lands and is re-measured.**

## The problem, measured

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
