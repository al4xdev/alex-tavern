# Task 76 — Sibling sub-zones are mutually deaf

> **Status:** open, found 2026-08-12 while measuring task 67's last closure item.
> **Design decided 2026-08-12 on measurement** (comma-prefix rule, see below);
> implementation deliberately held until task 71's confirmation cell lands,
> because changing the graph changes what that cell measures.
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

## Cost: it inflates task 71

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

## It is now partly hidden, which raises the priority

Task 71 shipped 2026-08-12 and folds singleton clusters: a lone character who is
not the player gets no narration render of their own, on the redundancy argument
(they already receive per-viewer events and memory).

On the first live post-71 session, `21f7c4e1`, **all ten split turns are this
defect** — Lorde Cassian Aurel alone on `púlpito central`, addressing an assembly
he is sealed from:

```json
{"Salão dos Quatro Arcos": ["púlpito central", "Pátio norte da Academia"],
 "púlpito central": [], "Pátio norte da Academia": ["Salão dos Quatro Arcos"]}
```

The pulpit and the courtyard are siblings under the hall, so neither hears the
other. The fold then fired ten times and each time denied narration to a
character who should have been standing in the main cluster.

Two consequences:

1. **The symptom is now quieter, not smaller.** Before 71 the isolation showed up
   as a spurious cluster in the split count; now it shows up as a character
   quietly receiving nothing. That is harder to notice, not easier.
2. **The claim "there are no singletons after 67" is dead.** It held across four
   sessions and broke on the fifth. Anyone reasoning about singleton folding
   should read this section first.

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
- [ ] the five read cases become a regression test with their real zone names;
- [ ] the split rate re-derived with `scan_scene_splits` after the fix, against
      the post-67 baseline task 71 records;
- [ ] `empty_audience` and `clamp_lost_half` do not regress — this task adds
      edges, so the risk is the opposite one: an audience that should have been
      narrow.

**The measurement that would falsify this task:** if sibling sub-zones are rare
once the Director stops being handed a contract that invites them, this is a
prompt problem and not a graph problem. Worth checking, because the true fix may
be teaching the Director that `zone_moves` is for changing rooms and blocking is
for positions within one — which is what task 54 already tried to say.
