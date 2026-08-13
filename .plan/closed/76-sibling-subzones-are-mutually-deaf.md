# Task 76 — Sibling sub-zones are mutually deaf

> **Status:** ✅ **SHIPPED 2026-08-12**, after task 71 closed. Sibling zones
> sharing a comma-prefix are linked at creation, so two positions inside one
> place hear each other.
>
> **What it fixes:** 5 of the 25 audience entries the graph wrongly denied, in 3
> of the 5 records. **What it does not:** the split rate, which is unchanged at
> 168 of 610 — connected components already bridged siblings through their
> shared parent — and **siblings the Director named as places rather than as
> sub-positions**, which a live cell then produced two more of. Three claims in
> this file were corrected after measuring the shipped rule; all three are below
> and none is subtle.
> **Not** a regression from 67. It is the half of task 54's finding 1 that the
> fix for that finding did not reach, and it has been in every session since.

## The defect

`Runner._open_new_zones` creates each new zone audible from the zone its movers
came from, and links the pair both ways. That is task 54's doctrine working as
designed: sound carries within a place unless something stops it.

It links the new zone to its **origin** and to nothing else. Two characters who
leave the same hall for two different new sub-zones in the same turn produce:

```
hall            -> [flanco esquerdo, flanco direito]
flanco esquerdo -> [hall]
flanco direito  -> [hall]
```

Perception is not transitive — `can_perceive` is same-zone or a direct edge — so
**the two flanks of one hall cannot hear each other**, while both can hear the
hall standing between them. Nobody declared that separation. It is the free,
undeclared deafness that task 54 set out to abolish, arriving one hop further
out than that task looked.

## The evidence, and how it was found

Task 67's last closure item reads *"a character who can no longer perceive is not
listed as a witness"* — the mirror of the bug 67 fixed. Measured over the 16
archived sessions: **25 of 13,540 audience entries (0.18%), in 5 records of 971**,
name a witness the graph says cannot perceive the speaker.

Then they were read, and every one of the five is the opposite of the alleged
defect:

| session | zones | text |
|---|---|---|
| `oldcode-P1-r1` T14 | `salão, flanco direito` / `salão, flanco esquerdo` | *"Garran grita do flanco direito: 'Firmem a linha!'"* |
| `base-P2-r1` T7 | `corredor sudeste, próximo à saída` / `corredor sudeste, guiando um grupo` | Nix announces the corridor is still clear |
| `base-P1-r1` T16 | `Ala Leste, túnel de manutenção (lado Garran)` / `Ala Leste, túnel de manutenção` | *"Garran grita do outro lado do desabamento"* |
| `null-P1-r1` T14 | `entrada do portão da equipe verde` / `túnel da equipe verde` | Garran, at the gate's threshold, to those in the tunnel |
| `null-P1-r1` T18 | gate / hall | *"grita pelo portão fechado"*, explicitly through the closed gate |

Two flanks of one hall. Two positions in one corridor. Two ends of one tunnel.
These are not deaf people wrongly included in an audience; they are people who
can plainly hear, whom the graph wrongly separates. The audience is right and
the graph is wrong.

**So task 67's closure item, implemented literally, would have been a
regression** — re-clamping witnesses against the post-move graph deletes 25
correct audience entries and silences five shouts, four of which the narration
describes as being shouted across exactly the barrier in question. That item is
rewritten in 67 rather than built.

### Why the stale list was rescuing them

`validate_perception_events` runs inside `narrate()` against the scene as it
stood at the START of the turn; `_apply_canon` applies that same Director call's
`zone_moves` afterwards, at `runner.py:912`. So a witness who moves into a fresh
sub-zone this turn was validated where they were standing before they moved. The
ordering is doing accidentally right what the graph does deliberately wrong.

That is not a defence of the ordering. It means **the two defects have been
masking each other**, and fixing either one alone makes the symptom worse.

## ~~Cost: it inflates task 71~~ — superseded, see "What this task actually fixes"

Task 71's split rate is the count of narrated turns whose scene is more than one
mutually-perceiving cluster. Recomputing the archive with sibling zones made
mutually audible (crude heuristic: any two zones sharing a common neighbour):

| | narrated | split | if siblings hear |
|---|---|---|---|
| all 16 sessions | 610 | **168 (27.5%)** | **142 (23.3%)** |
| `oldcode-P1-r1` | 40 | 17 | **0** |
| `base-P1-r2` | 39 | 7 | **0** |

⚠ **The 23.3% is not a claim.** The common-neighbour heuristic over-merges: it
also joins two genuinely sealed rooms that both open onto one corridor. Reading
the zone names separates the two sessions:

- `oldcode-P1-r1`'s children of the hall are `salão, flanco esquerdo` and
  `salão, flanco direito`. Positions inside one room. **All 17 splits are
  artifacts.**
- `base-P1-r2`'s children of the hall are `corredor leste`, `duto de ventilação`,
  `corredor interno da passagem secreta`. A ventilation duct and a secret
  passage are not the same room as the east corridor. **Its 7 splits are mostly
  legitimate** and the heuristic was wrong to erase them.

So the defensible figure is **about 17 of 168 splits (10%) are sibling
artifacts**, not 26. This is recorded because the tempting version of this
number is the bigger one and it does not survive being read.

## ⚠ I attributed a case to this task that does not belong to it

Corrected 2026-08-12, same day, after implementing the fix and checking whether
it would have helped.

The claim was: on the first live post-71 session `21f7c4e1`, all ten split turns
are this defect, Lorde Cassian Aurel sealed on `púlpito central` while addressing
an assembly. It was used to argue that task 71's singleton fold now *masks* this
defect, and to raise the priority.

**It is not this defect.** Tracing the zone graph turn by turn:

- **T10** the pulpit is created and correctly linked both ways:
  `{"Salão dos Quatro Arcos": ["púlpito central"], "púlpito central": ["Salão dos Quatro Arcos"]}`
- **T23** the Director issues `zone_link_updates: {"púlpito central": []}` — an
  **explicit, declared seal**, which the engine applied exactly as designed.

So Cassian is isolated because the Director said so, not because two siblings
failed to link. `púlpito central` has no comma and no sibling; this task's rule
would not touch it. Whether the Director *should* have sealed a pulpit in the
middle of its own assembly is a prompt question and belongs to whichever task
owns the Director's contract, not here.

**What survives:** singleton clusters exist, and 71's fold does hide them. The
cause is a declared seal rather than this defect, so the fold is hiding a
Director decision the engine honoured — which is a weaker complaint than the one
I made, and still worth someone's attention.

## What this task actually fixes, measured after implementation

**Not the split rate.** Re-derived over the 16 archived sessions with the rule
applied: **168 split turns before, 168 after.** No change at all, and the reason
is structural — `scene_clusters` takes connected components, so two flanks that
both link to an occupied hall are *already* one cluster. Sibling deafness never
inflated the cluster count while the parent was occupied.

> The earlier estimate in this file, that roughly 17 of 168 splits (10%) are
> sibling artifacts, came from a much broader common-neighbour heuristic that
> merges any two zones sharing a neighbour. **It does not describe the rule that
> shipped.** The section above it is kept because the reasoning about reading
> versus merging is still right; the number is not.

**It fixes perception, which is what the evidence was about.** Audience entries
the graph denies, over all 26 sessions: **25 before, 20 after** — 5 fixed, in 3
of the 5 records:

| session | pair | |
|---|---|---|
| `oldcode-P1-r1` T14 | `salão, flanco direito` / `flanco esquerdo` | ✅ fixed |
| `base-P2-r1` T7 | `corredor sudeste, …` two positions | ✅ fixed (2 entries) |
| `base-P1-r1` T16 | `Ala Leste, túnel …` two ends | ✅ fixed (2 entries) |
| `null-P1-r1` T14, T18 | gate / tunnel, gate / hall | ❌ untouched, 20 entries |

The 20 that remain are a character shouting **through a closed gate**, which the
narration states outright. They share no name prefix and are not siblings; they
are the case task 67 examined and left alone deliberately.

## The design question this task must answer first

Under task 54's doctrine — err toward hearing, because a wrong deafness cost 12
empty audiences and a lost shout, while a wrong audibility costs no secrecy
(`audience_origin="zone"` is declared to be perception, never a secrecy source)
— siblings should be linked and separation should be declared with
`zone_link_updates`.

Against that: it would make `duto de ventilação` audible from
`corredor interno da passagem secreta`, and no Director reliably declares the
seal it never thought about.

**Do not implement before deciding this in writing**, the same way 71 was
blocked until its product question was answered. The two candidate rules:

1. **Link all siblings of a common origin.** Simple, matches the doctrine,
   over-connects distinct rooms that happen to share a door.
2. **Link only siblings that are sub-positions of their origin**, detected by
   name containment. Matches every one of the five read cases and leaves
   `base-P1-r2`'s distinct places alone.

Rule 2 is the better fit for the evidence and the more dangerous to build: it is
a string heuristic over model-authored names, and this project has already
shipped one of those wrong this month (`named_exclusions` matched *"a menos de
dois metros"*, 15 false positives on a live cell, 0 on the archive). If rule 2
is chosen it needs the same treatment: measured against the archive's real zone
names before it ships, decoys included.

## ✅ The decision — 2026-08-12, measured over 26 sessions

**Rule 2, in a sharper form than the one sketched above: two zones are linked
when they share a comma-prefix.** Not parent-name containment, which the data
kills — `salão, flanco esquerdo` has to link to `salão, flanco direito` while
their actual parent is named `Academia Real do Primeiro Sino, Salão dos Quatro
Arcos`, so a containment test finds nothing.

Every mutually-deaf sibling pair across all 26 sessions was collected: **63
distinct pairs**. The prefix rule links **13** and leaves 42 alone. All 13 read:

| pairs | verdict |
|---|---|
| `corredor, ao lado de C17` / `, parada junto à porta` / `, atrás de C17` (3 pairs) | ✅ three positions in one corridor |
| `salão, flanco direito` / `flanco esquerdo` | ✅ the case this task opened with |
| `zona de segurança, recuado` / `, recuado da entrada` / `, recuado do corredor A` (3) | ✅ three marks in one hall |
| `base da brecha, ao lado de Garran` / `, escalando borda` | ✅ two spots at one breach |
| `corredor sudeste, guiando um grupo` / `, próximo à saída` / `, com o kit` (3) | ✅ the Nix case from the audience audit |
| `Academia Real do Primeiro Sino, Salão dos Quatro Arcos` / `, jardins leste` | ❌ a hall and a garden |
| `Ala Leste, câmara do sino quebrado` / `, túnel de manutenção` | ❌ two rooms in one wing |

**11 right, 2 wrong: 85% precision, and the two failures share a shape.** Their
prefix is a *building* or a *wing* (`Academia Real do Primeiro Sino`, `Ala
Leste`); every true positive's prefix is a *room* (`corredor`, `salão`, `zona de
segurança`, `base da brecha`). That distinction is semantic and there is no
length or word-count cut that separates them — I looked.

**Ship the 2 false positives deliberately.** Task 54's doctrine decides it: a
wrong deafness cost 12 empty audiences and a shouted warning nobody heard, while
a wrong audibility costs no secrecy at all, because a zone audience is
`audience_origin="zone"`, which the model layer already declares to be
perception and never a secrecy source. Two rooms in one wing hearing each other
is the cheap error, and `zone_link_updates` is the declared way to sever it. The
same doctrine that inverted the default in task 54 answers this the same way.

Recorded so nobody has to rediscover it: **the tempting extra condition is to
require the prefix to be a room, and there is no way to know that from the
string.** If this needs tightening later, the lever is the Director's contract,
not the parser.

### ⚠ Sequencing: do not implement while a task 71 cell is in flight

Written 2026-08-12 while the post-71 confirmation cell was running. Changing the
zone graph changes the cluster split, which is exactly what that cell measures,
and §6 requires the validated variant to BE the shipped variant. This decision
is docs-only until that cell lands and is scored.

## Closure evidence required

- [x] the design question above answered in writing, here, before implementation;
      *(2026-08-12: the comma-prefix rule, with the doctrine argument for
      accepting its two false positives)*;
- [x] if rule 2: the name test measured over every zone name in the archive, with
      the false-positive population reported, not just the true-positive one;
      *(63 mutually-deaf sibling pairs collected over 26 sessions; the rule links
      13, of which 11 are right and 2 are wrong, and both failures are named)*;
- [x] the five read cases become a regression test with their real zone names;
      *(`TestPrefixSiblingsHearEachOther`, including the two known false
      positives pinned as deliberate)*;
- [x] the split rate re-derived with `scan_scene_splits` after the fix, against
      the post-67 baseline task 71 records; *(**unchanged, 168 of 610**, and the
      reason is structural rather than a null result - see above)*;
- [x] `empty_audience` and `clamp_lost_half` do not regress — this task adds
      edges, so the risk is the opposite one: an audience that should have been
      narrow. *(2026-08-12, cell `834f91e5`: `empty_audience` **0**,
      `with_others_present` **0**. No wrong-edge regression: nothing got a wider
      audience than it should have. But `clamp_lost_half_unsealed` moved **0 →
      2**, and reading it changed what this task claims to cover - see below.)*

## ⚠ The rule covers a subset of the defect, and a live cell showed the rest

The post-76 cell flagged two severe clamp losses, both `C18` at 18 proposed and
1 kept. Read:

> *"Garran, da porta lateral, grita que está indo em direção ao túnel e pergunta
> se todos estão a salvo do outro lado."*
>
> ```
> Salão dos Quatro Arcos: [porta lateral do salão, escada para arcos superiores, túnel oculto]
> porta lateral do salão: [Salão dos Quatro Arcos]
> escada para arcos superiores: [Salão dos Quatro Arcos]
> túnel oculto: [Salão dos Quatro Arcos]
> ```
>
> Standing where everyone is: **17 in `túnel oculto`, 2 on the stairs, 1 in the
> hall**, Garran alone at the side door.

**This is exactly this task's defect** — three openings off one hall, each linked
to the hall and none to each other, so Garran calling from the side door reaches
one person out of twenty. **And the shipped rule does not fix it**, because none
of those three names contains a comma. The prefix rule matches siblings that the
Director *named* as sub-positions; it cannot see siblings it named as places.

So the honest statement of what shipped:

- **No regression.** 76 added no wrong edges; `empty_audience` and
  `with_others_present` are both 0, and nothing was heard that should not have
  been.
- **The rule's footprint is narrower than the defect's.** It fixed 5 of the 25
  archived wrongly-denied entries. This cell produced 2 more of the same kind
  that it cannot reach.

**⚠ This reopens the design question rather than settling it.** Candidate rule 1
(link all siblings of a common origin) WOULD fix the case above. It was rejected
because it also joins `duto de ventilação` to `corredor interno da passagem
secreta` in `base-P1-r2`. Both of those judgements are defensible and the
evidence now points both ways, so the choice belongs to the owner rather than to
me. Task 54's doctrine favours rule 1: separation should be declared, and
undeclared deafness is the expensive error.

## ✅ THE FALSIFIER RAN — 2026-08-13, and it fires. Do not adopt rule 1.

The owner froze the graph until this was measured. It is measured, and it moves
the fix out of the graph entirely.

> *"if sibling sub-zones are rare once the Director stops being handed a contract
> that invites them, this is a prompt problem and not a graph problem."*

**Over 33 sessions, 403 `zone_moves` with a known origin:**

| | |
|---|---|
| destination whose own prefix names the zone the mover just left | **136 (34%)** |
| destination whose name literally contains the origin | 39 (10%) |

Unambiguous on reading:

```
Salão dos Quatro Arcos          ->  Salão dos Quatro Arcos, junto ao duto de ventilação
Salão dos Quatro Arcos          ->  Salão dos Quatro Arcos, porta dos fundos, junto com Marta
Ala Leste, túnel de manutenção  ->  Ala Leste, túnel de manutenção (lado Garran)
```

**A third of all movement is somebody crossing the room they are already in.**
That is the mass, and the falsifier's own words make it a prompt problem.

### The clause that invites it

`narrator.py`, on reconciling a character's self-declared position with canon:

> *"PREFER splitting the stage with zone_moves (creating a zone if needed)"*
> *"When canon and self-location differ, create or use a separate zone with
> zone_moves first."*

A character says *"I step toward the rubble"*, that differs from canon, and the
contract instructs the Director to split the stage. It is obeying.

### ⚠ But the contract cannot be fixed on its own, and this is the real finding

`Scene` holds exactly two spatial fields: `zones` (the audibility graph) and
`positions` (character -> zone). `scene_blocking` is a scratch field and
`narrate()` pops it before anything durable sees it.

**So there is no representation of "where in the room you are" that is not a
zone, and a zone is the unit of audibility.** Every positional detail the
Director wants to keep becomes an acoustic barrier. Telling it *"zone_moves is
for changing rooms"* leaves it two options: drop the detail, or keep doing this.

That is the root cause of this whole family - task 54's finding 1, this task, and
the two false positives the prefix rule ships with. It is not a graph bug and not
a prompt bug. **It is a missing field.**

### What to do, in order

1. **Do not adopt rule 1.** The owner's two objections stand and the measurement
   removes its justification: the mass is in naming, not in the graph.
2. **Do not ship a contract clause alone either.** It has nowhere to send the
   Director instead.
3. **This is now task 79 — blocking as durable state**, split out of 69 by the
   owner because it is a schema change with its own migration and closure
   evidence. 69 keeps durable state generally. **79 also corrects the 34%
   quoted below**: with the per-session spread and a second naming style
   counted, the honest figure is a union of **31% pooled, median 22%, range
   0-95%**, and no name-based instrument can pin it tighter.
4. The shipped prefix rule **stays** - it is correct where it fires, it fired 3
   times in 4 live sessions, and it is not the thing standing between this
   engine and the defect.

**The measurement that would falsify this task:** if sibling sub-zones are rare
once the Director stops being handed a contract that invites them, this is a
prompt problem and not a graph problem. Worth checking, because the true fix may
be teaching the Director that `zone_moves` is for changing rooms and blocking is
for positions within one — which is what task 54 already tried to say.
