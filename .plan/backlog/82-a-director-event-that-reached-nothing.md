# Task 82 — A Director event that reached nothing

> **Status:** backlog. **n=1, uninvestigated, no next action.** Filed 2026-08-14
> because two isolated critics, independently, said the same thing about it: it
> was reported only as an alibi for a hypothesis it disproved, and a
> recording-path failure is plausibly more serious than the defect it was
> exonerating.
>
> **OBSERVED**, n=1, found incidentally.

## The case

`b11b38dc`, turn 18. The Director emitted a `physical_outcome` event:

> *"a diretora Maelis anuncia que a entrada na masmorra é imediata e que cada
> equipe deve atravessar o limiar em um minuto ou será desclassificada"*

**It reached nothing.** At T18 there is no speech record for that character, no
C17 line at all, and the turn's narration covers the mist and Garran at the door
without a word of the announcement. The event was produced and left no trace
anywhere a reader or a later prompt could see it.

At T19 the Director emitted it again.

## Why it was nearly lost

It surfaced inside task 69's capacity investigation as the **single exception** in
a sample of 18 — the one re-proposal where the original was *not* visible in the
prompt. It was correctly dismissed as "not a capacity failure", and that
dismissal is how it almost disappeared: it entered the record only in its capacity
as a non-counterexample to somebody else's hypothesis.

A critic reading the write-up cold put it plainly: *a case where nothing was ever
recorded is not evidence that nothing is forgotten; it is the sample's one
instance of the general failure the section set out to investigate, exonerated on
a technicality of which store.*

## Why it might matter

Every other layer assumes `perception_events` is the substrate. The prose renderer
narrates from it, characters react to it, the transcript is built from it. An
event emitted and rendered nowhere means:

- the reader never learns something the world layer decided had happened;
- the next turn's prompt cannot show it, so the Director re-proposes it — which is
  **task 69's symptom with a completely different cause**, and would be miscounted
  as restaging by every instrument that exists;
- nothing reports it. There is no "events emitted versus events rendered" counter
  anywhere in this project.

## What would make it real, and what would kill it

**Real:** count, across the archive, Director `perception_events` that produce no
speech record, no narration mention and no fact update. That is a mechanical count
over `debug.jsonl` against `state.json`, and it needs **no judge and no string
matching over names** — a rare thing in this corpus (see
`.plan/reference/metric-validity.md`, where five instruments died on exactly that).
If the count is material, this is a real defect with a cheap detector.

**Killed:** if events routinely fail to surface *by design* — an empty witness
list, a cluster that renders nothing, a deterministic guard dropping it — then
this is the design working and T18 had an ordinary reason. **Check the guards in
`narrate()` before counting anything**; several could explain it, and finding that
out costs one read.

## Related

- **69** — where it was found, as the one exception in the visibility read.
- **78** (`backlog/`) — routed into silence: a character speaks and nobody hears.
  This is one level earlier — the event never becomes speech at all.
- **81** — narration and state describing different events. Same family: the
  layers disagreeing about what happened.
