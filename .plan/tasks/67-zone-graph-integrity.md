# Task 67 — Zone graph integrity

> **Status:** open. **Wave 1.**
>
> An earlier draft of this task named the wrong cause and prescribed a fix that
> would have made things worse. Both are recorded below, because the wrong
> version was plausible and will be re-proposed by anyone who reads only the
> transcripts.

## The symptom

Characters shout in a crowded hall and the record says nobody heard.

`base-P1-r3` T25, in its most absurd form:

> **Instrutor Garran Holt (só Diretora Maelis Ordan percebe):** Garran grita para
> Doran e Bruna: 'Sustentem o ritmo, eu seguro a retaguarda!'

He shouts *at two named people* and the only listed perceiver is a third.

`base-P1-r1` T16–T18 and T28–T29: six of Garran's lines carry
`(ninguém além dele percebe)` — and the **next turn's narration renders them as
heard**: *"a voz de Garran, abafada e áspera, atravessa o entulho: ele anuncia
que seguirá pela passagem secreta"*. The decision layer says nobody heard it; the
prose layer tells everyone.

Scale: **33 empty-audience records across 5 of 12 sessions**; zero in the other
seven.

## The cause the first draft got wrong

The draft claimed: *"the model narrows the witness list to zero for shouts in the
same hall; `validate_perception_events` only intersects, never floors, so a floor
by zone adjacency is missing."*

**The model does not narrow it.** Across **1,868 raw Director events in 12
sessions, exactly 2 have an empty `witness_ids`**, and neither is shout-like.
At the cited turn, verified in `8bd4d0f1`'s `debug.jsonl`:

```
T23 witnesses=18 :: Riven grita que Liora está presa e avança em direção aos escombros…
T23 witnesses=18 :: Bruna grita que a fonte está sob os escombros…
```

The Director proposed eighteen witnesses. The **deterministic clamp deleted all
eighteen**, and the persisted record carries `audience: []`.

And the prescribed fix — a floor by zone adjacency — targets the wrong layer:
adjacency is exactly what deleted them.

## The real cause

Two bugs in how the zone graph is mutated, both in `Runner._apply_canon`'s zone
handling:

**1. `zone_moves` mints a zone with no inbound edge.** `base-P1-r2` T20:

```json
{"C13": "Salão dos Quatro Arcos, junto aos escombros da passagem"}
```

A new sub-zone of the hall. The same turn's `zone_link_updates` only declares
`{"corredor leste": ["…Salão dos Quatro Arcos"]}` — nothing connects the hall
*to* the new sub-zone.

**2. `zone_link_updates` replaces instead of merging** (`runner.py:1210-1212`):

```python
for zone, audible in (narrator_raw.get("zone_link_updates") or {}).items():
    if zone in game.scene.zones:
        game.scene.zones[zone] = [other for other in audible if other in game.scene.zones]
```

A straight assignment. `base-P1-r2` T21 sets the main hall's audible list to
`["corredor leste"]` — wiping every other edge it had, including any that might
have reached C13's new sub-zone. The list comprehension also silently drops any
named zone that is not already known, so a link to a zone created in the same
turn is discarded without a trace.

From T20 onward nobody in the hall could perceive C13. `eligible_witnesses`
(`perception.py:50-56`) returns the empty set, `validate_perception_events`
intersects to nothing, and eighteen witnesses become zero.

## Also here: the mirror failure

The dead stay in the audience. In `base-P1-r2` Liora dies at T36, T37 and T38,
and Maelis's lines at T38 and T39 still carry
`(… Liora Celestria, Bruna Ferrugem, Noa Véu percebem)`. Same clamp, opposite
direction: nothing removes a character who can no longer perceive anything. The
death itself is task 69's problem; being listed as a witness after it is this
one's.

## What 68's scanner says, 2026-08-05 — this task's diagnosis holds

`benchmarks/*/immersion-scan.json`. The scanner deliberately **does not ask the
zone graph** whether an audience should have been empty — that question is
circular when the graph is the suspect — and classifies by whether anyone else
was present in the scene at all:

| | P1 | P2 |
|---|---|---|
| empty-audience records | **33** in 5 of 12 sessions | 2 in 1 of 4 |
| …with other characters **present** | **33** | 2 |
| …**cut off by the graph** (nobody reachable) | **31** | 2 |
| …the graph allows a witness, the record is empty anyway | **2** | 0 |
| raw Director events proposing an empty witness list | **2 of 1,868** | 1 of 704 |
| largest witness list clamped to zero | **18** (`base-P1-r2`), **19** (`null-P1-r1`) | — |

**Not one of the 33 is a character alone in the world**, and the T23 clamp this
task cites is reproduced independently: eighteen proposed witnesses, zero
persisted. The corrected attribution above — the graph, not the model — is now
measured rather than argued.

### The 2 that are not this bug

`oldcode-P1-r1` T18 and T19, the only records where the graph left witnesses in
earshot and the audience is empty anyway. Cause, from the raw log:

```
T18 audible_speech subject=C20 witness_ids=['C20']
T19 audible_speech subject=C20 witness_ids=['C13','C18','C20']
```

At T18 the Director listed **the speaker as the only witness of their own
shout**, and the clamp correctly removes the subject → empty. At T19 it listed
three, one of them the speaker again and the other two out of earshot. Marta is
standing in a hall with eighteen people who could hear her.

This is the model narrowing to a bad set — which is what this task's *first
draft* claimed was the whole cause, and the audit correctly cut it to two cases.
It is a footnote, not a task, and **the graph fixes below will not remove it**.
Whoever ships the "clamp deleted every proposed witness" warning gets it almost
free: warn on an empty result whatever emptied it, and this shape shows up in the
log the first time it happens. Do not build more for n=2.

## Direction

- `zone_link_updates` **merges**, and a link naming a zone created in the same
  turn resolves instead of being dropped.
- A zone opened by `zone_moves` gets a reciprocal edge to its parent by
  construction — a sub-zone of the hall is audible from the hall unless the
  Director explicitly severs it.
- A **counted, logged** signal when a clamp deletes every proposed witness. That
  is a graph bug every time; it should never be silent. This is what would have
  surfaced the defect two batteries ago.
- Perception eligibility accounts for characters who can no longer perceive.

Note what is *not* proposed: a volume-based floor. The Director's numbers were
right; the graph was wrong.

## Explicitly out of scope

- **Scene headers naming the wrong location.** No verified instance exists. The
  blind reader saw it, `docs/cases/21` declined to confirm it, and the audit
  found only `oldcode-P1-r1` setting location to "Pátio de Demonstração" at
  T10/T11 and back at T13 — which may be correct. **Unverified is not
  deterministic.** Bring a turn and an excerpt or leave it out.
- **The literal `"null"` action record** (`null-P1-r1` T3): one occurrence in
  ~1,300 turns, and a one-line normalizer fix. Do it in whichever validator is
  already open; it does not justify a task.

## Closure evidence required

- [ ] a test where a sub-zone opened via `zone_moves` is audible from its parent
      without an explicit link;
- [ ] a test that `zone_link_updates` merges, and that a link to a zone created
      in the same turn survives;
- [ ] a clamp that deletes all proposed witnesses emits a counted warning;
- [ ] 68's scanner reports zero empty-audience records for events whose subject
      is co-located with other present characters, over a re-run cell — the
      `with_others_present` field, which is **31 + 2 = 33** today. A fix that only
      moves records from `graph_isolated` to `narrowed_to_none` has not closed
      this;
- [ ] **`clamp_lost_half` at zero on the re-run cell** — see the section below.
      Emptiness alone cannot close this task, because a shout heard by ONE person
      in a hall of twenty-one is this same bug one witness short of the count;
- [ ] a character who can no longer perceive is not listed as a witness;
- [ ] replayed against the archived `base-P1-r2`, the T23 shout keeps a non-empty
      audience.

**The measurement that would falsify this task:** if the 33 empty-audience
records survive after the graph fixes, the cause is elsewhere and the intersect
is the problem after all.

## ⚠ The metric was too narrow — refined 2026-08-06, before the fix

A live post-65/70 cell (`34390b86`) reported **`empty_audience` = 2**, which
looks nearly clean. Reading the transcript instead of the number:

> T31 **Garran**: *"Todos para o corredor lateral agora! …"* — audience **1**
> T31 **Nix**: *"Todo mundo pro corredor novo, agora!"* — audience **1**
> T26 **Asword**: *"Link, eu seguro sua mão e te puxo para cá"* — audience **0**

**19 of 72 scoped records (26%) reached two or fewer witnesses with 21
characters present.** Only 2 of them were empty, so the metric this task closes
against saw 2 and missed 17 — and the 17 are the same bug, one witness short of
being counted. **A graph fix could take `empty_audience` to zero and leave every
one of them in place**, which is the reclassification trap this task already
warned about, arriving through a door the warning did not cover.

### `clamp_lost_half` — added to 68's scanner

For every Director `audible_speech` event, what the model **proposed** against
what the engine **persisted**. Non-circular for the same reason the existing
classification is: it never asks the zone graph whether an audience was right,
it compares the model's number to the code's.

| session | `with_others_present` | `clamp_lost_half` | worst |
|---|---|---|---|
| `base-P1-r2` | 10 | 2 | **T23 18 → 0** (this task's cited case) |
| `null-P1-r1` | 11 | 7 | T19 19 → 0 |
| `oldcode-P1-r3` | 0 | 3 | T14 **20 → 6** — invisible to emptiness |
| **fresh cell** | **2** | **6** | **T31 21 → 1** |
| archive total | — | **25** | against 14 clamped to zero |

**It is strictly more informative than the empty count** and it recovers every
case this task already cites, which is the check that it measures the same
defect rather than a new one.

### And three graph-health metrics were tried and REJECTED

`deaf_occupied` (an occupied zone that can hear nothing), `unreciprocated`
(A hears B, B does not hear A) and `edges_lost` (an edge present at turn N gone
at N+1) were each measured per turn across all 16 archived sessions. **None
predicts the damage:**

| session | `deaf`·turns | `unrecip`·turns | empty-audience |
|---|---|---|---|
| `oldcode-P1-r3` | 288 | **1764** | **0** |
| `drive-P1-r3` | 243 | 9 | **0** |
| `base-P1-r2` | **0** | 270 | **10** |
| `oldcode-P1-r1` | 0 | 0 | 2 |

Graph damage is **exposure, not damage** — a broken edge costs nothing until
someone speaks across it. They are recorded here so nobody re-derives them as a
proxy; they would each be a plausible-looking dashboard number that ranks
sessions wrong. Kept as diagnostics for *this* task's implementation (they are
how the fresh cell's deaf main hall and `base-P1-r2`'s T20→T21 edge wipe were
both located), not as acceptance metrics.

## ⤴ Hand-off: task 71 is waiting on this fix's numbers

**Do this as part of closing 67, not later.** Task 71 (per-viewer narration) is
parked until this ships, and it is parked specifically because *every cost figure
it carries was measured on the graph this task fixes*. Both of its bugs
manufacture a spurious cluster — a sub-zone with no inbound edge is a cluster of
one — so 71's split rate, cluster counts and prose-call multiplier are all upper
bounds of unknown tightness.

On the post-fix cell, re-derive and write the numbers into
`.plan/tasks/71-per-viewer-narration.md`:

- the fraction of narrated turns whose scene holds more than one
  mutually-perceiving cluster (**168 of 610, 28%** before);
- mean clusters per narrated turn (**1.56** before) and mean clusters holding two
  or more characters (**1.21** before) — the gap between those two is what
  decides whether singleton clusters get their own render;
- how many sessions never split at all (**8 of 16** before).

If the split rate collapses, say so plainly: 71 shrinks or closes, and this task
will have removed a wave-3 item as a side effect.
