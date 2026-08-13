# How this project measures

**Read this once, in full, before you generate a number. It is short on purpose.**

This is the only copy of these rules. `AGENTS.md` §0, `GUIDE.md` and
`.plan/reference/critic-protocol.md` point here rather than restate them, so they
cannot drift apart.

Two folders, two reading habits: **`guides/` is read once, end to end, to learn how
work is done here. `reference/` is consulted, by searching for the name of the thing
you are holding.** These are the rules; the verdict on any individual instrument —
trusted, downgraded, measured and rejected — lives in
`.plan/reference/metric-validity.md`, and you look that one up rather than read it.

## The nine rules

These are not style preferences. Each one is here because it was violated and cost
something.

1. **The session is the unit.** Count per session, compare sessions. Pooling turns
   treats one Director decision — sealing a pulpit — as seven independent
   observations, and inflates effective n by roughly an order of magnitude.
   *Cost: nearly every p-value in this project, withdrawn on 2026-08-12.*

2. **Every headline number carries its per-session spread.** Pooled figure plus
   median, sd and range. A pooled 34% over a median of 15% means a handful of
   sessions carried the claim.
   *Cost: "a third of all movement in this engine", which was never true of a
   typical session.*

3. **A new metric is not believed until it has a control.** "Restated orders sit on
   frozen scenes 36 of 39 times" is damning until you learn adjacent turn pairs are
   frozen 184 of 213 anyway. **Fisher p = 0.43.**
   *Cost: nothing, because the control was run. That is the point.*

4. **Pre-register the decision rule before firing.** What result would change your
   mind, written down before the data exists. A gate invented after the numbers
   arrive is not a gate.

5. **Never match a NAME with a string heuristic.** Zone names, character names,
   place names are model-authored and follow no convention the engine controls.
   This project shipped this failure **twice** and nearly a third time.
   *Corollary: when a detector scores 0%, ask whether it cannot see the thing
   before concluding the thing is absent.*

6. **Record measured-and-rejected.** A hypothesis that failed its control goes in
   the file with its numbers, so nobody re-derives it in a month.

7. **Lexical distance measures whether the words changed. Nothing measures whether
   anything happened.** Any similarity-based guard needs a read before it is
   trusted.

8. **A metric that has never announced its own error gets REPORT, DO NOT GATE.**
   `clamp_lost_half_unsealed` needed three repairs in one day; every one was found
   by reading a flagged case, never by the number looking wrong.

9. **A negative result is a result.** An arm that fails its own pre-registered gate
   is not adopted, however good it looked directionally.

### Where a number may come from

Three sources, in order of preference:

1. **An existing metric from the register** — `.plan/reference/metric-validity.md`
   says which are trusted, which were downgraded, and which were measured and
   rejected. Look yours up before you quote it.
2. **A new metric**, which then owes: a control, a per-session spread, a
   pre-registered rule, and an entry in the register.
3. **A reader's judgement, stated as a metric.** Legitimate and often the best
   available. *"I read six of these and could not tell them apart"* is a
   measurement. Report it as what it is — n, method, and the reader's own
   uncertainty — never laundered into a percentage.

Option 3 exists because of the 0.02 case. When the instruments say the paragraphs
are unrelated and a reader says *"this is the same paragraph again"*, the reader
wins and the number is what gets an entry in the register.

---

*Moved out of `metric-validity.md` on 2026-08-13. They had been written inside the
critic protocol, which misfiled them — they govern all measurement here, not only
review — and then sat at the top of the register, which grows with every instrument
measured while these do not. Different lifetimes, different folders.*
