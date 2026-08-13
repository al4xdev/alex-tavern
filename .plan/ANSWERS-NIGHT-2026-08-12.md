# Owner's answers — DECISIONS-NIGHT-2026-08-12

Read the whole file plus `6f2bad2`. The judgement in it is sound. Every ⚠ is
answered below; where I say "your call" it stays yours.

**Standing authorisation: it is not dawn yet. Keep going, keep deciding.** The
same rule as before — reading the text outranks the metrics — plus the two
constraints at the bottom of this note.

---

## 1. Task 64 — re-scope ACCEPTED

Keep it as calibration. The reading carries it: ten `return_control` turns and
none of them a lull is not a mechanism that picks badly. Do not build a new
trigger. Contract wording is the right first suspect.

## 2. Task 77 — roadmap position: RAISE IT

Put 77 above most of wave 2. It is the phase's headline complaint made concrete
and it is the only one with a transcript a reader can check. Go ahead and
re-order for it.

## 3. Task 77 vs task 72 — KEEP SEPARATE, CROSS-LINK

Do not merge. 77 has evidence; 72 has a design. Merging costs the evidence its
own name and makes 72 unfalsifiable. Link them both ways and say in each file
that 69, 72 and 77 are three faces of "the engine keeps no record of what has
already been settled" — that framing is right and worth writing down once.

Also: you were right not to adopt arm B. Failing its own pre-registered gate is
the end of the argument, whatever direction it pointed.

## 4. The empty-cluster fold — APPROVED as shipped

Reviewed the diff. The optional `events` argument means no existing caller
changes behaviour, and the player's cluster is never folded. Correct and
conservative. Land the second post-fold replicate when it finishes and record
whichever way it lands; do not re-open on one thin cell alone.

## 5. Task 76 — DO NOT adopt rule 1 yet. Run the falsifier first.

This is the one I am changing. The file itself names the measurement that would
settle it:

> if sibling sub-zones are rare once the Director stops being handed a contract
> that invites them, this is a prompt problem and not a graph problem.

**Do that measurement before touching the graph.** How often does the Director
create siblings that ought to have been positions inside one room? If that is
where the mass is, the fix is the Director's contract — `zone_moves` is for
changing rooms, positions within one room are something else — and that is
cheaper, more correct, and does not widen audibility permanently.

Two reasons I am not taking rule 1 on the doctrine argument alone:

1. Rule 1 is a permanent global widening. `zone_link_updates` is the declared
   way to sever, but a Director that never thought about the seal will never
   issue it, so in practice the widening is one-way.
2. **A cost neither of us has written down:** `scene_clusters` takes connected
   components, so linking all siblings of a common origin also *merges the
   narration clusters*. "The group split up" stops being a separate scene. That
   is a narrative feature being run over sideways, and it is not in the
   audibility trade-off table.

If the falsifier comes back saying the Director's naming is not the driver, then
adopt rule 1 on task 54's doctrine, accept the false positives, and log the
cluster-merge cost explicitly as part of the price. But measure first.

## 6. Task 69 — noted, no action

Survives post-wave-1. Correct not to design anything on it yet.

## 7 + 11. P3 — KEEP IT. The lines are good.

They read like a player who pushes: intention, direction, an outcome demanded,
and two of them are `action` inputs, which P1 has none of. Structurally matching
P1 (four content inputs, six skips, same positions) was the right call — length
drives every recurrence number here and you protected that.

- **P1 and P2 stay as they are.** Do not touch them. Additive was correct.
- **The passive-baseline question is answered** by your own decision 11 and I am
  closing it. 95.2% frozen with a player pushing settles it.
- One nit, do it only if it is free: P3's lines have no accents while P1's do.
  Make it consistent if nothing depends on the current strings.
- Re-run P3 when 77 is actually fixed, as you proposed.

Worth saying plainly: you raised a red flag against your own work and then
knocked it down with a pre-registered test. That is the behaviour I want.

## 8. The contaminated cell — CORRECTION ACCEPTED

Do not leave the waiter fix as a lesson in a doc. **Fix the waiter itself** —
watch the parent pid, not the `--exec-one` child — so no future run inherits
this. Any conclusion still resting on a "DONE" from the old waiter gets
re-checked against commit times before it is quoted.

## 9. Task 67's metrics — DOWNGRADE APPROVED

`empty_audience`, `with_others_present` and `clamp_lost_half_unsealed` are
REPORT, DO NOT GATE. Correct not to re-open 67: the graph fixes stand on their
own tests, which is a different thing from the closure numbers. Keep the table
in 67 with the note.

## 10. Task 78 — ACCEPTED as opened

Good separation from 67 and 76 — the seal was declared and correctly applied, so
the defect is the routing. Leave the fix undesigned until someone reads more
cases.

## 12 + `6f2bad2` — THE MOST IMPORTANT THING YOU WROTE LAST NIGHT

The session-is-the-unit correction is now standing policy, not a note:

- **Count per session, compare sessions.** If that leaves too few points, say so
  instead of pooling turns until something looks significant.
- **No p-value from a pooled-turn test gets quoted anywhere** — roadmap, task
  closures, summaries — without the caveat. Directions survive; confidence does
  not.
- Anything built on the split rate is untrustworthy at n<=4. sd of 17.9 points
  on identical code means the 51% -> 1.3% story was never a result, and you were
  right to kill it before it became a headline.

Task 71's cost and value estimates inherit that spread. Leave them unrestated,
exactly as you did.

---

## Constraints while you keep going

1. **No new production code without an ⚠ answered above.** Docs, tasks, replays
   and measurements are yours to take. `src/` changes are: the fold was the only
   one last night and that ratio is right.
2. **Task 76's graph is frozen** until the falsifier in §5 is measured.
3. When you open a task, keep doing what you did with 77 — leave the mechanism
   undiagnosed rather than guessing, and record measured-and-rejected metrics so
   nobody re-derives them.

Keep reading transcripts. Four of the five real findings last night came from
reading and none came from a counter noticing its own error.
