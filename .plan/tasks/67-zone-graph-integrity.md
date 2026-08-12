# Task 67 — Zone graph integrity

> **Status:** ✅ **CLOSED 2026-08-12.** Graph fixes shipped 2026-08-06; two
> post-fix cells pass on `clamp_lost_half_unsealed` (6 → 0 → 0) and on
> `with_others_present` (2 → 0 → 0).
> The last closure item — the mirror failure, *a character who can no longer
> perceive must not be listed as a witness* — was measured and **withdrawn**:
> the population is 25 audience entries and reading all of them shows the
> audience is right and the graph is wrong. It became **task 76**.
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

## ✅ The graph fixes are IN — 2026-08-06, re-run still owed

**Bug 1 was already fixed.** `_open_new_zones` (task 54, finding 1) has given a
new sub-zone a reciprocal edge to its parent since before this task was written.
This file's diagnosis was half stale; the surviving half is bug 2 alone, and the
compound is worse than either: the reciprocal edge added by `_open_new_zones`
could be **wiped by `zone_link_updates` in the same turn**.

**`zone_link_updates` now merges** (`Runner._apply_zone_links`). An empty list is
still a total seal, which is the only severance idiom the corpus actually uses
(**36 of 106** archived updates) and it stays honoured.

The ambiguity is real and is recorded rather than hidden: of 36 non-empty updates
to a zone that already had edges, **20 only add and 16 remove at least one**, and
reading them, some narrowings are clearly intentional (a team entering a tunnel
loses the hall) while others are clearly collateral (T21 above). Counts cannot
separate them. Resolved the way `_open_new_zones` already resolved the same
trade — **err toward hearing**: over-hearing costs realism, under-hearing costs
this defect, and a zone audience is `audience_origin="zone"`, which the model
layer declares to be perception and never a secrecy source.

**Stated cost:** removing ONE edge in a single update is no longer expressible.
Sealing is, and re-linking afterwards is.

**Two silences are now logged:** `log_zone_link_dropped` (a link naming a zone
the scene does not have, previously discarded inside a list comprehension) and
`log_witness_clamp` (a clamp that deletes half or more of a proposed witness
list, previously silent — the signal that would have surfaced this two batteries
ago).

### Verified against the archive

Replaying `base-P1-r2` T19-T23's real `zone_moves`/`zone_link_updates` through
the new code: the hall keeps all three edges including the rubble sub-zone, where
the archived run had it down to `['corredor leste']` at T21. Pinned as a
regression test with the data **inlined**, because `plans/` is gitignored and has
already vanished once mid-session.

**Still owed: the re-run cell.** Every closure item below that says "over a
re-run cell" is unmet until then, and `clamp_lost_half` is the one that decides.

## Closure evidence required

- [x] a test where a sub-zone opened via `zone_moves` is audible from its parent
      without an explicit link *(pre-existing, task 54)*;
- [x] a test that `zone_link_updates` merges, and that a link to a zone created
      in the same turn survives *(2026-08-06, plus a seal-still-wins test and a
      log for a link naming an unknown zone)*;
- [x] a clamp that deletes all proposed witnesses emits a counted warning
      *(2026-08-06 — `log_witness_clamp`, and it fires on severe PARTIAL losses
      too, because emptiness alone missed 17 of 19 on a live cell)*;
- [x] 68's scanner reports zero empty-audience records for events whose subject
      is co-located with other present characters, over a re-run cell — the
      `with_others_present` field, which is **31 + 2 = 33** today. A fix that only
      moves records from `graph_isolated` to `narrowed_to_none` has not closed
      this; *(2026-08-12, session `d0cc98e5`: `with_others_present` **0**, and
      `empty_audience_records` 0 as well, so nothing merely moved between bins)*;
- [x] **`clamp_lost_half` at zero on the re-run cell** — see the section below.
      Emptiness alone cannot close this task, because a shout heard by ONE person
      in a hall of twenty-one is this same bug one witness short of the count;
      *(2026-08-12, and the criterion had to be sharpened to survive a second
      cell: **`clamp_lost_half_unsealed` = 0 on BOTH post-fix cells, against 6
      pre-fix**. Raw `clamp_lost_half` is 0 and 2, and reading the 2 shows them
      to be the Director proposing across a seal the fiction supports, not graph
      damage)*;
- [x] ~~a character who can no longer perceive is not listed as a witness~~
      **MEASURED AND WITHDRAWN 2026-08-12.** Building this would have been a
      regression. Over the archive, **25 of 13,540 audience entries (0.18%), in
      5 records of 971**, name a witness the graph says cannot perceive the
      speaker — and reading all five, every one is a person who can plainly
      hear, wrongly separated by the graph: two flanks of one hall, two
      positions in one corridor, two ends of one tunnel, and a shout the
      narration explicitly describes as going *through the closed gate*.
      Re-clamping against the post-move graph would delete those 25 correct
      entries and silence the five shouts. The cause is a distinct defect, now
      **task 76** — sibling sub-zones minted from the same origin are never
      linked to each other, so they are mutually deaf while both hear the room
      between them. See 76 for why the two defects were masking each other;
- [x] replayed against the archived `base-P1-r2`, the T23 shout keeps a non-empty
      audience *(2026-08-06, data inlined into the test)*;
- [x] **the re-run cell** — `clamp_lost_half` and `with_others_present` both at
      zero. Nothing above substitutes for it. *(2026-08-12, `base-P2-r1` session
      `d0cc98e5`, 37 of 40 turns before the process was cut. See below.)*

**The measurement that would falsify this task:** if the 33 empty-audience
records survive after the graph fixes, the cause is elsewhere and the intersect
is the problem after all.

## The re-run cell — 2026-08-12

`base-P2-r1`, session `d0cc98e5`, 37 of 40 turns (the process was cut short; the
missing three turns are not worth another cell, because the metric is not near
its threshold — it is at the floor).

A **second** post-fix session, `00997daa` (`base-P1-r1`, 38 turns), was scored
afterwards and is included here. It matters: on `clamp_lost_half` alone the two
post-fix cells disagree, and the disagreement is what produced the refinement
below.

| | pre-fix `34390b86` | `d0cc98e5` | `00997daa` |
|---|---|---|---|
| `empty_audience_records` | 2 | **0** | **0** |
| `with_others_present` | 2 | **0** | **0** |
| `clamp_lost_half` | 6 | **0** | 2 |
| **`clamp_lost_half_unsealed`** | **6** | **0** | **0** |
| `clamp_lost_most` | 5 | **0** | 1 |
| `clamp_worst_loss` | 20 → 1 (0.95) | none | 19 → 1 (0.95) |
| `clamp_matched_events` | 14 | 8 | 37 |

All three were scored with the corrected counter described below, so the
comparison is like for like: the baseline's six severe losses are still six.

### The two post-fix cells disagreed, and the second one was right

`d0cc98e5` gave `clamp_lost_half` = 0 and closure was written against it. Then
`00997daa` gave **2**, which on the pre-registered criterion is a partial
regression. Reading both:

> **T19**, C18 in `corredor da ala norte`, 19 proposed, 1 kept:
> *"Afastem-se dessa fenda agora e preparem as armas!"*
> **T28**, C8 in the same corridor, 18 proposed, 5 kept.
>
> Graph: `{"Salao": ["corredor da ala norte", "patio"], "corredor da ala norte": []}`

The corridor is **explicitly sealed** — Garran is behind the collapse the T16
narration describes. The Director proposed nineteen courtyard witnesses across
that seal and the clamp correctly cut it to one. **The engine is right and the
Director over-proposed.**

So `clamp_lost_half` does not measure graph damage. It measures *disagreement
between the Director and the engine*, which has two causes, and only one of them
is an engine bug:

1. **the graph is wrong** — the pre-fix cause, 67's actual defect;
2. **the Director ignores a seal that is correct** — a prompt-side issue, and
   arguably not a defect at all.

`clamp_lost_half_unsealed` counts only cause 1. Across the three cells it reads
**6 → 0 → 0** with no crossover: every pre-fix loss is unsealed, both post-fix
losses are sealed. That is the number this task closes on.

"Sealed" is detected by **asymmetry, not emptiness** — `zones[Z] == []` while
some other zone still lists Z, which is what a `zone_link_updates` seal leaves
behind. A zone *born* isolated (`_open_new_zones` with no recorded origin) is
empty in both directions and keeps counting as damage, because it is damage.

### What reading the records changed

The first pass showed two surviving losses, 19 → 18 and 20 → 19. Small, but the
whole point of this task is that a small audience loss is the same defect as a
total one, so they were read rather than waved through. Both were the same
thing, and it was not a graph fault:

> T24, subject **C11**, `witness_ids` = `[C1, C3 … C11 … C21]`
> T10, subject **C17**, `witness_ids` = `[C1 … C17 … C21]`

The Director listed **the speaker inside their own witness list**. The clamp
drops them, correctly, and the counter read that removal as a lost witness. So
the metric charged a ~5% audience loss to every event where the Director
self-lists, which is common.

Fixed in both places that count, so the runtime log and the scanner agree:
`_proposed_witness_counts` (`src/agents/narrator.py`) and
`scan_witness_clamp_loss` (`tools/acceptance/immersion_scanners.py`) now subtract
the subject and de-duplicate. Pinned by
`TestWitnessClampIsNeverSilent::test_the_speaker_listing_themself_is_not_a_loss`.

This never mattered at the 0.5 reporting threshold — one witness out of twenty
is nowhere near it. It mattered because `clamp_worst_loss` and `clamp_evidence`
are what somebody reads to diagnose a real graph bug, and they were pointing at
a non-bug. The evidence field is the product here, not the count.

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
