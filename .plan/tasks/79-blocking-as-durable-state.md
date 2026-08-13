# Task 79 — Blocking as durable state

> **Status:** open, **DOCS-ONLY** by the owner's instruction. No `Scene` field, no
> serialization, no contract edit until the shape below is agreed in writing.
> Task 76's graph and this schema are both frozen.
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

That last clause is not a footnote. **If a parser cannot tell a room from a
position by its name, neither can the engine** — which is the argument for the
field, independent of the rate.

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
