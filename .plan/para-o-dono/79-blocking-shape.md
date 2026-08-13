# For the owner — task 79's shape, four decisions

**Written 2026-08-13. Nothing in `src/` has been touched. 79 is docs-only until
you answer, exactly as you instructed.**

This file exists because the four questions are buried in a 250-line task file
and they are the only thing standing between 79 and a two-hour change. The task
file (`.plan/tasks/79-blocking-as-durable-state.md`) has the full evidence; this
is the decision surface.

---

## What changed since you last saw this task

**79 is no longer "add a field to `Scene`". It is "stop discarding one."**

Measured over the 33 recorded sessions, on the shipped contract, unprompted:

| | |
|---|---|
| Director calls that carry `scene_blocking.character_zones` | **1188 of 1188 = 100%** |
| entries that are positional, pooled | **1967 of 24,829 = 8%** |
| per session | median **6%**, sd 9.0pts, range **0-44%**, one session at 0 |

What it writes there, verbatim from a replay:

```
"Link":               "junto a Asword, próximo ao portão norte"
"Mirella Valecourt":  "próximo à mesa central, afastando-se do gás"
"Doran Pedra-Rúnica": "ao lado de Bruna, tentando erguê-la"
```

That is this task's question answered in the Director's own words. And
`narrate()` pops the whole field (`src/agents/narrator.py:849`), so roughly
**1,967 positional phrases have been thrown away across the archive.**

⚠ **The pre-registered replay FAILED its own clause 1** — arm B populated a new
`blocking` key on **0 of 8 runs**. It failed because the Director already had a
key and filled that one instead. By the letter of the rule, the falsifier fired;
by the reading, it found something better. **Both halves are recorded and neither
is hidden.** The replacement falsifier is decision 4 below.

---

## Decision 1 — what may read it, and what must be FORBIDDEN

**This is the one that matters.** "Who may read a field" is exactly what turned
`zones` into the defect this task exists to remove.

| reader | my recommendation | why |
|---|---|---|
| `can_perceive`, `eligible_witnesses`, `perception_clusters` | **FORBIDDEN, in writing** | if blocking can narrow an audience, this task has rebuilt the defect it exists to remove |
| prose renderer (staging) | **yes** | it already stages zones; this is strictly better material |
| Director's own prompt | **yes** | the point is to stop it minting zones for positions |
| character prompts | **no in v1** | unmeasured token cost, and no evidence yet that a reply needs it |

**Needs your yes or no per row.** I will not implement a reader you have not
named.

## Decision 2 — free text or structured

**Answered by observation, not by preference: it is already free text**, already
written, already fluent, in every call. Designing a structure the Director is not
producing means fighting behaviour that already works.

The anchor problem solves itself: `Scene.positions` already maps character → zone,
so a blocking phrase is **always subordinate to a real place** without adding a
field to carry that.

**Recommendation: free text, keyed by character id, alongside `positions`.**

## Decision 3 — the 33 sessions on disk, and what a schema bump actually costs

The migration question mostly dissolves — old sessions never persisted this, so
there is nothing to migrate and their positional zones **stay zones**. Rewriting
history would change what those sessions meant.

**But there is a cost you should price before saying yes, and it is not the one I
expected.** `src/store/sessions.py:64` states the convention outright: *"This
project deliberately does not migrate old sessions (alpha, no legacy): an
incompatible session can never be opened again."* `load_game` compares
`schema_version` for **exact equality**. So bumping 15 → 16:

| | effect of a bump |
|---|---|
| reopening the 33 archived sessions in the app | ❌ **permanently refused** |
| `material_delta_rate` (the LLM-judge metric) | ❌ breaks — it is the one metric that goes through `load_game` (`repetition_metrics.py:718`) |
| the main scoring path | ✅ **survives** — it reads `state.json` directly (`repetition_metrics.py:109`) |
| `immersion_scanners.py`, every task-71/76/77 number | ✅ survives — reads `debug.jsonl` directly |
| the archive as evidence | ✅ survives — every number in this phase is re-derivable |

**So the bump costs the app's ability to reopen the batteries, and one metric.**
An additive field defaulted in the loader would avoid the bump entirely, but that
breaks the project's stated no-legacy convention, so it is your call and not mine.

## Decision 4 — the replacement falsifier

The registered one has fired and cannot be reused. Proposed, for your approval
before it is registered:

> **If persisting `character_zones` and showing it to the prose renderer does not
> reduce positional `zone_moves` below the archive baseline — 31% pooled, median
> 22%, range 0-95% — then the missing field was not the constraint and 79 closes
> without shipping a schema.**

⚠ **Its predecessor's guard clause is still unresolved and it limits this one.**
In the replay, both arms emitted far fewer `zone_moves` than the recorded
originals (arm A: 7 of 8 runs emitted none), so the "does it stop minting
positional zones" clause **was never testable**. Nothing measured so far says a
blocking field reduces positional zone-minting. The replacement falsifier is the
first thing that would.

---

## What I am doing while this waits

Nothing in `src/`. 79 stays docs-only. Wave 2 order is 79 → 69 → 64 → 77, and
**69 is the one that can proceed without you**, so that is where the work goes if
you do not answer before the next block.
