# Task 74 — An orchestrator with tools, instead of a fixed pipeline

> **Status:** backlog, **proposed 2026-08-05** by the owner, enabled by the budget
> rule (`AGENTS.md` §2). **Not scheduled.** It is the largest architectural
> proposal this project has had, and it must not be designed before the phase
> checkpoint — see §5.

## 1. The proposal

Today the Runner *is* the orchestration: a fixed pipeline runs every turn —
Director → character queue → prose — with hard-coded clocks, burst rules and
exclusion windows deciding the variations.

Instead: an agent that reads the situation and **fires the tools it judges
necessary**, the way a coding agent decides which tool to call. Route these three
characters; resolve this whisper; replan the beat; skip the prose; do nothing at
all this turn.

## 2. Why this is not scope creep — it answers the phase's headline defect

The roadmap's own statement of the problem:

> **The engine cannot render a turn in which nothing happens.** `perception_events`
> requires `minItems: 1`, prose must reach 150 words, and prose may not narrate
> stillness.

Those are properties of a **fixed pipeline**: every stage must produce, because
every stage always runs. An orchestrator can call nothing. That is a structural
answer rather than another guard, and no other proposal in this phase has one.

Three more findings point the same way:

- **Task 64** — `return_control=True` on 5 of 482 turns, and 5 of 12 sessions
  never returned control. `BURST_PROTAGONIST_EXCLUDE_BEATS` excludes the
  protagonist by clock while the fiction is screaming for them (case 21 §3.2: ten
  turns of standoff where the Director's own events say *"Link, abra o portal"*).
  A situation-reading dispatcher routes the PC because the scene needs them.
- **Task 70** — the Director's prompt names the protagonist to exclude them,
  because routing lives inside the narration call. Move routing out and the
  narration prompt stops carrying a cast-exclusion instruction at all.
- **Task 65** — the Director authors speech partly because it is the only agent
  awake at that moment. A dispatcher that can call a character instead does not
  need the Director to improvise one.

**So 64, 70 and part of 65 may be symptoms of one cause: too many decisions in
one call, and a pipeline that cannot choose.** That subsumption claim is the
thing to test, and it is why this cannot be designed before those tasks land —
if wave 1 already fixes them, the case for 74 shrinks a great deal.

## 3. The constraint that decides whether this is safe

**Every leak invariant in this engine is enforced by code *before* the call** —
perception clamped by the zone graph, prose never given minds, speech reduced to
markers, redaction applied per viewer. This project has measured, repeatedly,
that **a prompt promise loses to a code-issued mandate** (task 59 finding 1, task
65's ignored DIALOGUE OWNERSHIP rule, task 71's ignored zone rule in `prose.py`).

An orchestrator is, by construction, a prompt deciding control flow.

> **Non-negotiable if this is ever built: the orchestrator chooses WHAT happens
> and never HOW. Every tool enforces its own invariant internally, and there is
> no tool, argument or ordering that can skip a clamp.** If "call the prose
> renderer with the whispers included" is expressible, the design has already
> failed.

## 4. The cost that is NOT free

`AGENTS.md` §2 makes tokens and latency cheap, which is what makes this thinkable.
Two costs it does not cover:

- **Comparability.** Batteries compare runs that made the same calls. A dynamic
  call graph makes `llm_calls_per_action` a *variable* rather than a control, and
  the archive's whole method is controlled cells. Any battery with an
  orchestrator cell needs the fixed pipeline running beside it, exactly as
  `oldcode` does today.
- **Complexity**, which §2 explicitly keeps expensive. One more call is cheap;
  one more layer that can reorder the engine is not.

## 5. How to test it for almost nothing, before building anything

**Run the orchestrator read-only over the archived sessions.** The 16 sessions in
`plans/artifacts/` carry every turn's full state and the Director's raw decisions.
Give a dispatcher agent the same situation each archived turn presented, let it
say what it *would* have called, and never execute anything.

Then score its decisions against what actually happened:

- on the **ten stalled turns of `base-P1-r2` T30–T39**, does it route the
  protagonist? (`return_control` was false on every one of them);
- on turns the blind reader called restaging, does it choose to **do nothing**?
- how often does it propose a call the fixed pipeline did not make, and does that
  correlate with the turns a reader disliked?

Zero engine change, zero risk, and it directly tests the one claim that justifies
the whole idea: *can it represent a turn where nothing happens?* If it cannot, or
if it fires the same calls the fixed pipeline already fires, this task closes
cheaply and honestly.

**The measurement that would falsify this task:** if wave 1 + 69 already produce
turns that can be quiet and a protagonist that gets routed, the pipeline was not
the cause and this is a rewrite in search of a defect.
