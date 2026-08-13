# Task 81 — The narration and the state change describe different events

> **Status:** backlog. **n=1, uninvestigated, no next action.** Opened 2026-08-13
> so it stops being a footnote in task 79's method section.
>
> **OBSERVED**, and deliberately not generalised: one case, found incidentally,
> never counted. Nobody has looked for a second.

## The case

`00997daa`, turn 16, character `C1`.

**What the state recorded.** The Director's `zone_moves` sends C1 from
`Academia Real do Primeiro Sino, Salão dos Quatro Arcos` to `pátio central` — out
of the hall, into the central courtyard.

**What the prose said.** A blind reader given that turn's narration and the
character's name reported, with high confidence, that the character *repositioned
within the place they already were*, quoting:

> *"Ele recua da beira da rachadura, os calcanhares batendo com firmeza"*
>
> (*He steps back from the edge of the crack, his heels landing firmly*)

**Both readings are correct about their own source.** The engine moved him to
another place; the narration shows him taking a step backwards from a hazard. The
turn produced two accounts of what happened to one character, and they are not the
same account.

## Why it might matter

The persisted state is what every later turn reasons from — the Director's next
prompt, the perception graph, who can hear whom. The prose is what the **player**
receives. If they diverge, the player's model of the scene and the engine's model
of the scene drift apart silently, and nothing in the engine can detect it: each
layer is internally consistent.

That is a different failure from anything currently tracked:

- **69** is the Director re-proposing an event it already resolved — one layer
  repeating itself.
- **77** is an order issued and never enacted — the state failing to follow the
  fiction.
- **This** is the state moving while the fiction does not, which is 77 **inverted**.

## What would make it real, and what would kill it

**Real:** count turns where a `zone_moves` destination differs from the origin and
the narration for that turn contains no rendering of that character moving.
Requires a judge, because no string rule can do it — see 79's audit, three
instruments, three failures.

**Killed:** if the prose routinely omits movement for most characters while the
state is right, then this is not divergence, it is **omission**, and it is
`80-the-narration-does-not-convey-space.md` rather than a defect of its own.
**That is the likelier explanation and it should be tested first.** 80's blind
read already found 88% of such turns undeterminable, which is exactly what
widespread omission looks like.

**So the first question is not "how often do they diverge" but "is there any case
where the prose asserts something the state contradicts", as opposed to merely
staying silent.** This case is silence plus a small contrary detail, not a flat
contradiction. n=1 and it may be nothing.

## Related

- **80** — the likelier explanation, and the one to test first.
- **79** — where this was found, in the disagreement set of its blind read.
- **71** — narration renders per cluster, so any check has to be per viewer.
