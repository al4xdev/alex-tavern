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


---

# ANSWER — owner, 2026-08-13

Read top to bottom before writing code. Three of the four decisions are answered;
one is deferred on purpose and one is rejected.

**First, the worktree.** Your diagnosis in `51f1339` is correct and the withdrawal
of entry 22 is accepted. The second session is the one that swept your staged
routing work into `e53fe17` under a translation message — a shared git index, not
a sync daemon and not the owner. Nothing was lost; only the commit boundaries and
the authorship of that message are wrong, and they are not being rewritten while
two processes hold the same checkout. **That session has stopped writing to this
repository. You have the tree. Resume.** Before any `git commit`, run
`git diff --cached --stat` and commit with an explicit pathspec
(`git commit <paths> -m ...`), so a stray index entry cannot ride along again.

## Verified before answering

Your four code claims were checked, and all four hold: `scene_blocking` is in the
schema's `required[]` (`narrator.py:398`), `narrate()` pops it (`:849`), the
no-legacy convention is textual in `sessions.py:64`, and the metric asymmetry is
real — `material_delta_rate` goes through `load_game` (`repetition_metrics.py:718`)
while the main scoring path reads `state.json` directly (`:109`).

## Three problems with the evidence, before the decisions

**1. The 100% is a property of the schema, not a finding about the Director.**
`character_zones` sits in `required[]` and the prompt orders it: *"REQUIRED spatial
draft completed BEFORE every other field"*. A structured-output model fills a
required field 1188 of 1188 times by construction. The number is measured and
true, and it is tautological — it says the provider honours the schema. Remove
*"answered in the Director's own words"*; the Director did not volunteer this, it
was ordered to. **The load-bearing number is the 8%, not the 100%**, and the 8%
reads honestly as: *in a typical session ~6% of entries are positional, with whole
sessions at zero*.

**2. The classifier behind "positional" is not stated, and the number is only as
good as it is.** 1,967 of 24,829 is a judgement about model-authored free text.
This project has shipped a string heuristic over model-authored text **twice** and
been wrong both times. Before anything is priced on this number, write down: the
rule, how many phrases you read by hand, and how many false positives you found.
If the rule is a substring match on `junto a`/`próximo`, the 8% is a guess with
decimal places.

**3. The replacement falsifier is confounded, and would pass without shipping
anything.** It compares a replay's positional `zone_moves` against the archive
baseline (31% pooled). But this document already records that **both arms emitted
far fewer `zone_moves` than the recorded originals — arm A emitted none in 7 of
8 runs**. If the replay condition suppresses `zone_moves` on its own, beating a
historical baseline measures the condition, not the field. That is the same trap
that made the pre-registered falsifier fail its clause 1.

## Decision 1 — readers — ✅ APPROVED AS PROPOSED

| reader | answer |
|---|---|
| `can_perceive`, `eligible_witnesses`, `perception_clusters` | **FORBIDDEN** |
| prose renderer (staging) | **yes** |
| Director's own prompt | **yes** |
| character prompts | **no in v1** |

The forbidden row is the best thing in this document — it applies task 76's lesson
before the mistake instead of after it. One addition: **make it a test, not a
comment.** A rule that lives only in prose is a rule the next refactor deletes
without noticing.

## Decision 2 — free text — ✅ APPROVED

Free text keyed by character id, alongside `positions`. Your reasoning is right and
it is the reasoning, not the preference, that carries it: the Director already
produces this shape fluently, and designing against behaviour that already works
is how defects get invented.

## Decision 3 — the schema bump — ⏸ DEFERRED, and reframed

Do not decide this yet. It is downstream of problem 2: if the 8% does not survive a
manual read, there is no bump to price.

Two corrections when you come back to it:

- **The additive-field-with-default option is not an open owner call — it is
  revoking a written rule.** `AGENTS.md` §2 states it outright: *"New field = new
  version. No 'additive' exception"*, and explains that `.get(field, default)` is a
  migration in disguise. The owner may revoke his own rule, but present it as a
  revocation, not as a menu item.
- **Half the cost is removable for free.** `material_delta_rate` only breaks
  because it uses `load_game`; line 109 of the same file already reads `state.json`
  directly. Move that metric onto the `:109` path and the bump costs only the app's
  ability to reopen the 33 archived sessions in the UI.

## Decision 4 — the replacement falsifier — ❌ REJECTED AS WRITTEN

Do not register it. Two changes:

1. **The control must be inside the experiment.** Arm A (no field) against arm B
   (field), same replay, same payloads, same run. Never against a historical rate
   collected under different conditions.
2. **First find a payload where the behaviour occurs at all.** If arm A emits zero
   `zone_moves` in 7 of 8 runs, there is nothing to reduce, and any result is a
   measurement of the replay harness. Select payloads from the sessions at the top
   of the per-session range (the 44% one, not the 0% one) and show the behaviour
   reproduces before registering any rule about reducing it.

Re-register once both hold, and record the rejected version next to it, with this
reason, so nobody re-derives it in a month.

## The one thing you did best

Not any of the four. It was recording that the pre-registered falsifier **failed**,
and letting the failure stand in the same file as the finding that replaced it.
Keep doing exactly that.
