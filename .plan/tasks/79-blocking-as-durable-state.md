# Task 79 — Blocking as durable state

> **Status:** open, **DOCS-ONLY** by the owner's instruction. No `Scene` field, no
> serialization, no contract edit until the shape below is agreed in writing.
> Task 76's graph and this schema are both frozen.
>
> **FIRST in wave 2 as of 2026-08-13.** Not because its symptom is the biggest,
> but because it is **the only task in the phase with an established mechanism**:
> the Director writes blocking in 1188 of 1188 director calls and `narrate()`
> pops it. Both halves are verified in code and across 33 sessions. Every other
> open task rests on a mechanism that is suspected or unknown.
>
> The change is also the cheapest available: **stop discarding a field we already
> receive.**
>
> The question, verbatim from where it was found:
>
> > **where does *"by the door, three paces from Marta"* live, such that it
> > survives the turn and does not sever anyone's hearing?**

## Why this exists

`Scene` (`src/models.py:81`) carries `location`, `time_of_day`,
`present_characters`, `physical_facts`, `zones`, `positions`. Nothing else.
`scene_blocking` is a scratch field and `narrate()` pops it
(`src/agents/narrator.py:849`, under a comment that says so).

**So there is no way to record where in a room somebody stands except by minting
a zone — and a zone is the unit of audibility.** Blocking detail becomes an
acoustic wall by construction. This is a property of the data model, not an
interpretation of one.

It is the shared root of three things previously treated as separate:

- **task 54, finding 1** — crossing a room made people deaf;
- **task 76** — sibling sub-zones cannot hear each other;
- **the two false positives task 76 ships with** — a wing and a building read as
  rooms, because names are all the engine has to go on.

## Measured, with the spread

⚠ **Read this section before quoting a number from it.** Three instruments were
built and they disagree, because **all three measure naming style, not intent.**

| what it counts | pooled | per session (median / sd / range) |
|---|---|---|
| destination whose prefix names the origin (hierarchical) | 34% | 15% / 35.0pts / 0-97% |
| destination containing a positional phrase (*"ao lado de"*) | 12% | 0% / 19.6pts / 0-79% |
| **union of both** | **31%** (163/523) | **22% / 31.5pts / 0-95%** |

26 sessions with at least 5 `zone_moves`. Quartiles of the union: **0% / 22% /
44%**, and **8 of 26 sessions sit at zero**.

**The distribution is bimodal and the modes are naming conventions, not
behaviours.** Two sessions doing the same thing score 97% and 0%:

```
a3e1ceda (97%):  "Academia Real do Primeiro Sino, jardins leste, próximo ao canil"
34390b86  (0%):  "avançando em direção ao corredor oeste, posicionando-se entre
                  a aranha e os alunos"
```

The second is the purest blocking in the corpus — *positioning himself between
the spider and the students* — and the hierarchical metric scores it zero because
it does not repeat its origin's name.

**So 31% is a floor, and the honest statement is: a third to a half of all
movement is somebody repositioning inside a space they never left, and no
name-based instrument can pin it more tightly than that.**

### The standing argument for this task

> **If a parser cannot tell a room from a position by its name, neither can the
> engine.**

Adopted 2026-08-13 as this task's justification, replacing the rate. It is the
stronger claim: **the field is warranted even if the true rate is 5%**, because
the engine cannot distinguish the two cases at all, and a field that exists does
not care which naming convention the Director picked that session.

`34390b86` settles it. It scores **0%** on every detector while writing
*"posicionando-se entre a aranha e os alunos"* — the purest blocking in the
corpus, invisible to the instrument. **A 0% score does not mean it is not
happening; it means the instrument cannot see it.** So 31% is a **lower bound,
not an estimate**, the true rate is unknown, and no string detector over
model-authored names can find it. Do not build a better regex: that is the same
trap the prefix rule already fell into.

## The four things to decide, before any code

### 1. What reads it, and what must be FORBIDDEN from reading it

**Perception first, and the answer there is: nothing.** `can_perceive`,
`eligible_witnesses` and `perception_clusters` must not see this field at all.
If blocking can narrow an audience, this task has rebuilt the defect it exists to
remove.

Candidate readers: the prose renderer (staging), the Director's own prompt (so it
stops minting zones), character prompts (so a reply can reference where someone
stands). **Each needs a written yes or no**, because "who may read a field" is
what turned `zones` into this problem.

### 2. Free text or structured

Evidence for free text: every example above is a phrase, none decomposes cleanly,
and the Director already writes them fluently.
Evidence for structure: free text is what `zones` effectively is, and it is
precisely the ambiguity that made a name-based parser impossible.

**Undecided on purpose.** A middle option exists and is not obviously right
either: free text plus a required `zone` anchor, so the position is always
subordinate to a real place.

### 3. What happens to the 33 sessions already on disk

They have no such field. Whatever is chosen must load them, and their positional
zones **stay zones** — rewriting history to move a zone into a blocking field
would change what those sessions meant. A migration that silently re-partitions
old audibility graphs is worse than no migration.

### 4. The falsifier

**If the Director keeps minting positional zones after the field exists and its
contract points at it, this field is not the fix.** Measure the union rate above
on a post-field cell against the 31% / median 22% baseline. If it does not fall,
the cause is not the missing field and this task closes without shipping.

A second, cheaper falsifier available *before* any code: **replay a Director turn
with a contract that offers a blocking slot and see whether it uses it.** That is
the §6 discipline and it should run before the schema is designed, not after.

### The slot replay — decision rule, pre-registered 2026-08-13

Written before any call. It answers the expensive question — **does the Director
know how to use such a field?** — before anyone pays for a schema bump and a
migration of 33 saved sessions.

**Payloads**, chosen on recorded output only: `09aabf25` **T7** and **T22**, both
of which recorded positional `zone_moves` (*"salão, próximo à saída sul"*,
*"salão, próximo ao portão norte"*, the latter for three characters at once). Both
therefore have something to redirect. 4 runs per arm per payload, 16 calls.

**Arms.** A is the recorded contract verbatim. B adds a `blocking` key to the
output contract and one rule: a position INSIDE the place a character already
occupies goes there, and `zone_moves` is for changing place. The Director's call
uses `response_format: {"type": "json_object"}`, so a new key needs no schema
change to be expressible.

**The field is worth building if BOTH hold:**

1. **B populates the slot.** `blocking` non-empty on a majority of B's runs, with
   content that actually names a position.
2. **B stops minting positional zones.** B's positional-`zone_moves` rate falls
   materially below A's on the same payloads.

**Falsifier for task 79: if B ignores the slot, or keeps minting positional zones
at A's rate, the missing field is not the fix** and this task should not ship a
schema. That outcome is cheap here and expensive after a migration.

⚠ **Guard clause, and it decides more than it looks.** If B's `zone_moves`
collapses to `null` everywhere, that is **not** a win: it would mean the Director
stopped moving people rather than relocating the detail, which trades this defect
for task 77's. Reported separately and it blocks clause 2.

**Read whatever the counts say.** A slot populated with junk is not a populated
slot.

### ✅ RAN 2026-08-13 — the registered clause FAILED, and the answer is better than the question

**Clause 1 failed outright: arm B populated `blocking` on 0 of 8 runs.** By the
letter of the rule registered above, the falsifier fires and this task should not
ship a schema.

**It fired for a reason the rule did not anticipate, and reading the responses is
what found it.** The Director ignored the new key because **it already has one and
filled that instead.** From arm B's `scene_blocking.character_zones`:

```
"Link":               "junto a Asword, próximo ao portão norte"
"Asword":             "apoiado em Link, tossindo, próximo ao portão norte"
"Mirella Valecourt":  "próximo à mesa central, afastando-se do gás"
"Doran Pedra-Rúnica": "ao lado de Bruna, tentando erguê-la"
```

That is this task's question answered verbatim. **And `narrate()` pops the whole
field** (`src/agents/narrator.py:849`).

### The evidence that does NOT depend on the replay

Measured over **33 recorded sessions**, unprompted, on the shipped contract:

| | |
|---|---|
| Director calls carrying `character_zones` | **1188 of 1188 = 100%** |
| entries that are positional, pooled | **1967 of 24,829 = 8%** |
| per session | median **6%**, mean 8%, sd 9.0pts, range **0-44%**, one session at 0 |

**The Director already writes blocking, in every single call, and the engine
throws it away.** ~1,967 positional phrases discarded across the archive.

The replay adds one thing on top: asking explicitly raises the positional share
**4% → 35%** between arms A and B on the same payloads. So the behaviour is
present unprompted and improves when invited.

### What this does to the task

**79 is no longer "add a field". It is "stop discarding one".** Which is far
cheaper and changes three of the four decisions:

1. **What reads it** — unchanged and still the hard part. Perception must not.
2. **Free text or structured** — **answered by observation**: it is already free
   text, already written, already fluent. Do not design a structure the Director
   is not producing.
3. **The 33 saved sessions** — **the migration question mostly dissolves.** Old
   sessions never persisted it, so there is nothing to migrate; the field simply
   starts populating going forward. Their `debug.jsonl` still holds the values if
   anyone ever wants to backfill.
4. **The falsifier** — needs replacing, since the registered one has now fired
   for the wrong reason. Proposed: **if persisting `character_zones` and showing
   it to the prose renderer does not reduce positional `zone_moves`, the field
   was not the constraint.**

⚠ **Still docs-only.** This is a bigger change to what the task IS than to what
it costs, and the owner has not seen it yet.

⚠ **The guard clause is unresolved.** Both arms produced far fewer `zone_moves`
than the recorded originals (A: 7 of 8 runs emitted none), so **clause 2 was
never testable** and nothing here says whether a blocking field reduces
positional zone-minting. That question is still open and is what the replacement
falsifier is for.

## Explicitly NOT in scope

- **Task 76's graph rule.** It stays shipped and frozen. It is correct where it
  fires and it is not what stands between this engine and the defect.
- **Rule 1 (link all siblings).** Rejected on measurement, and this task removes
  its last justification.
- **Movement resolution.** `positions` being static in v1 is a different task.

## Related

- **69** owns durable state generally, and this was handed to it first. Split out
  on size: this is a schema change with its own migration, contract work and
  closure evidence, and inside 69 it reads as one bullet.
- **76** — its false positives are this defect.
- **54** — its finding 1 is this defect.
- **71** — narration clusters are built from the audibility graph, so anything
  that moves blocking out of `zones` changes how scenes split.
