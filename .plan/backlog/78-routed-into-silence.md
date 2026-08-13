# Task 78 — Routed into silence

> **Status:** open, found 2026-08-12 while auditing task 67's closure metrics.
> Rare in aggregate and severe where it happens. The fix is not designed here.
>
> **Moved from `tasks/` to `backlog/` on 2026-08-13, on its own numbers.** It is
> **13 of 1,255 speech records (1.0%)**, it has never been investigated, and it
> has no next action with a decision rule attached. `.plan/README.md` defines
> `backlog/` as *"future without active work"*, which is exactly what this is.
> The critic protocol makes `backlog/` the default for a new finding and
> promotion to `tasks/` an owner decision; this file was opened straight into
> `tasks/` and is being put where it belongs.
>
> **Nothing here is retracted or downgraded.** The seven-turn case in `21f7c4e1`
> is real and severe where it lands. What changed is the folder, not the
> evidence. Promote it back the moment somebody reads more cases or wants
> direction 3 tested.

## What a reader sees

`21f7c4e1`, turns 24 to 30. Lorde Cassian Aurel is on the `púlpito central`,
which the Director sealed at T23 with `zone_link_updates: {"púlpito central": []}`.

**He then speaks on seven consecutive turns, and every one of those records has
`audience: []`.** Twenty people are in the courtyard in front of him. Not one of
them hears a word, and the Director keeps choosing him to speak.

`09aabf25` has the same shape at a smaller scale: C5, three times between T13
and T21.

## Measured

Across twelve sessions (pre-67 through post-76):

| | |
|---|---|
| speech records (excluding the player) | **1,255** |
| spoken to an empty audience | **13 (1.0%)** |
| of those, in runs of 3+ turns by one character | **10** |

So it is uncommon per record and **concentrated**: when it happens it is not one
odd line, it is a character stuck addressing nobody for a third of a scene.

## Why this is not task 67, and not task 76

The isolation is **declared and correctly applied**. The Director sealed the
pulpit; the engine honoured the seal; the clamp emptied the audience because
nobody could perceive him. Every layer did its job.

The defect is that **the Director then routed him anyway, seven turns running.**
Its own contract, rule 5:

> *"ROUTE FROM PERCEPTION. Choose next_speakers only among characters with a
> concrete event they personally witnessed."*

A man sealed off from the room witnessed nothing. He should not have been in
`next_speakers` at all, let alone seven times.

## Why no metric caught it

`empty_audience` DID count these — 7 of them — and classified them
`graph_isolated`, which reads as "the zone graph broke". They are the opposite:
the graph worked. That misclassification is also why task 67's closure looked
cleaner than it was; see the note added to that task.

## Direction — not prescribed

Three shapes, none measured:

1. **Refuse the route.** The runner already knows who can perceive whom; a
   speaker with no eligible witness could be dropped from the queue before the
   call is made. Cheapest, and it silently deletes a character's turn.
2. **Let it happen but make it cost something.** A character who has spoken into
   silence three turns running is a person realising nobody can hear them, which
   is *better* fiction than the engine currently produces — if anything reacts to
   it. Nothing does.
3. **Fix it upstream: do not seal a speaker mid-scene.** The Director sealed a
   pulpit in the middle of its own assembly, which is the questionable decision
   underneath all of this.

**3 is the one to check first**, because it also produces the singleton clusters
task 71's fold hides, and both would go away together.

## The measurement that would falsify this task

If a character speaking into silence is always immediately un-sealed or moved by
the next Director turn, this is a one-beat artifact and not worth a task. It is
not: `21f7c4e1` sustains it for seven turns and never resolves it.
