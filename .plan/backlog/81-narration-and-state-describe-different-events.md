# Task 81 — The narration and the state change describe different events

**T23 early-render candidate WITHDRAWN, 2026-09-24:** the initial reading of
`p1-archive/07218133` T23 omitted the Director's `time_skip_summary`, which
explicitly reveals the second team. The actual prose request includes that
summary as a confirmed event. The renderer therefore had authority to narrate
the plaques; T24's repeat belongs to Task 69's Director-beat boundary, not a
source-checked prose/state divergence here. The clean text reader received an
incomplete event packet, so its early-render verdict is invalid. See the
[corrected source trace](../../plans/artifacts/69-closed-transition-contract/T23-EARLY-TEAM-REVEAL-FINDING.md).

**Source-checked physical contradiction, 2026-09-24:** in archived
`drive-P1-r1/5c994c42` T32, the accepted Director event partially disperses a
dust creature and `scene_update.dust_creature` says it remains active. The
renderer first described it regrouping, then received a lexical-repetition
correction; its second response says the creature's remains vanish without
trace and only a fading smell remains. The **second** version was persisted as
the T32 narration; the T33 Director request still lists the creature as
`ainda ativa` in physical facts. One isolated text-only model reader found the first version
compatible with the Director's state and the persisted second version
incompatible. This is an **observed one-turn example**, not a prevalence rate.
The retry prompt was present before the contradictory response; whether it
caused the change is undiagnosed. See the [source trace](../../plans/artifacts/69-closed-transition-contract/T32-PROSE-STATE-FINDING.md).

**T29 candidate withdrawn from this backlog item, 2026-09-24.** A same-day
source read of `8bd4d0f1` T29 initially compared a narrow gap in
`scene_blocking` with prose that completely seals access. The Director contract
defines `scene_blocking` as a **pre-decision** spatial draft; a later event may
block the gap without contradicting that starting position. The accepted
`scene_update` has no gap-closure field, so this is not a demonstrated
persisted-state/prose contradiction. The proposal's final passability is
ambiguous. The boundary correction remains in
[Task 69's pillar-pair result](../../plans/artifacts/69-closed-transition-contract/PILLAR-PAIR-RESULT.md);
it does not add a verified case here.

**Related reading, 2026-09-05:** the
[ea6620fb sequence read](../../plans/artifacts/79-content-read/REPORT.md)
finds Link's location ambiguous after the beam falls “atrás do grupo”. Asword's
claim that Link was separated comes from restricted perception and may be
mistaken; it is not a newly established state contradiction. This does not
restore the withdrawn actor attribution below or promote this backlog item.

> **2026-09-05: cited subject attribution withdrawn.** The candidate remains
> in backlog, but its one example does not establish the stated contradiction.
> C1 is Link; the quoted retreat explicitly follows **Asword** as its subject.
> The original judge received C1, not Link's name. See
> `plans/artifacts/79-reader-identity-audit/REPORT.md`. This correction does not
> establish that narration and state always agree.

> **Status:** backlog. T32's physical contradiction is source-checked. The
> original actor case, T29 gap reading and T23 early-render candidate are
> withdrawn. There is no prevalence estimate. Opened 2026-08-13
> so it stops being a footnote in task 79's method section.
>
> **Historical OBSERVED status withdrawn:** the original case compared
> different actors, and T29 supplies no persisted gap state to compare. The
> T32 observation is a separate case, not a reinstatement of either example.

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

**WITHDRAWN, 2026-09-05:** the passage actually begins *"Asword é o primeiro a
se mover. Ele recua da beira da rachadura"*. The retreat belongs to Asword,
not the target Link. The raw Director output likewise attributes the retreat
to `subject_id="C2"`. Thus the inference above compares different people.
Link's explicit narrated movement, if any, must be established separately.

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
read historically returned 88% undeterminable, but **that quantitative support
was withdrawn on 2026-09-05** because every target was an unresolved ID. It does
not establish widespread omission.

**The first question has one positive example:** T32's persisted prose asserts
disappearance where the accepted Director's state keeps the creature active.
The original `00997daa` movement, `8bd4d0f1` gap and `07218133` T23 early-render
examples remain withdrawn. The frequency and mechanism of T32 are unknown.

## Related

- **80** — the likelier explanation, and the one to test first.
- **79** — where this was found, in the disagreement set of its blind read.
- **71** — narration renders per cluster, so any check has to be per viewer.
