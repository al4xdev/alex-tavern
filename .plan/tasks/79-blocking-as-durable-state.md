# Task 79 — Blocking as durable state

> **Status:** open. **Decisions 1 and 2 are APPROVED by the owner (2026-08-13);
> decision 3 is DEFERRED and decision 4 is REJECTED.** Still no `Scene` field and
> no serialization until the deferred bump is decided. Task 76's graph stays
> frozen.
>
> **Next action, and it is not code:** find replay payloads where positional
> `zone_moves` reproduce, from the sessions at the top of the per-session range,
> then re-register the falsifier with its control *inside* the experiment.
>
> **FIRST in wave 2 as of 2026-08-13.** Not because its symptom is the biggest,
> but because it is **the only task in the phase with an established mechanism**,
> which after the owner's 2026-08-13 correction is stated precisely as: **8.4% of
> `character_zones` entries carry positional detail (audited, 64 entries hand-read,
> a floor) and `narrate()` discards every one of them.** Every other open task
> rests on a mechanism that is suspected or unknown.
>
> ⚠ **Not** *"the Director writes blocking in 1188 of 1188 calls"* — that is the
> schema's `required[]` being honoured, and it is tautological. See the audit.
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

## ✅ THE OWNER ANSWERED — 2026-08-13

Full text and reasoning in `.plan/para-o-dono/79-blocking-shape.md`. Binding
summary; the four sections below are kept as the reasoning that produced them.

| decision | answer |
|---|---|
| **1 — readers** | ✅ **APPROVED as proposed.** Perception (`can_perceive`, `eligible_witnesses`, `perception_clusters`) **FORBIDDEN**; prose renderer **yes**; Director's prompt **yes**; character prompts **no in v1**. **Plus: the forbidden rule must be a TEST, not a comment** — *"a rule that lives only in prose is a rule the next refactor deletes without noticing"* |
| **2 — free text or structured** | ✅ **APPROVED.** Free text keyed by character id, alongside `positions` |
| **3 — the schema bump** | ⏸ **DEFERRED**, and it was downstream of the audit above, not of anything else |
| **4 — the replacement falsifier** | ❌ **REJECTED as written.** See below; do not register it |

### Decision 3's two corrections, recorded before anyone re-opens it

- **The "additive field with a default" option is not an owner call, it is a
  revocation.** `AGENTS.md` §2 says it outright: *"New field = new version. No
  'additive' exception"*, because `.get(field, default)` *"is a migration in
  disguise and it will survive forever"*. I offered it as a menu item; it is not
  one. The owner may revoke his own rule, but it must be presented as a
  revocation.
- **Half the bump's cost is removable for free.** `material_delta_rate` breaks
  only because it calls `load_game` (`repetition_metrics.py:718`); line **109** of
  that same file already reads `state.json` directly. Move the metric onto the
  `:109` path and a bump costs only the app's ability to reopen the 33 archived
  sessions in the UI.

### Decision 4 — the REJECTED falsifier, recorded so nobody re-derives it

> ~~*"If persisting `character_zones` and showing it to the prose renderer does
> not reduce positional `zone_moves` below the archive baseline — 31% pooled,
> median 22% — the missing field was not the constraint."*~~

**Rejected 2026-08-13, for two reasons that are both right:**

1. **The control was outside the experiment.** It compares a replay against a
   historical rate collected under different conditions. The replay condition
   suppresses `zone_moves` on its own — **arm A emitted none in 7 of 8 runs** —
   so beating the archive baseline would measure the harness, not the field. It
   is the same trap that made the first pre-registered falsifier fail its clause
   1.
2. **There was no demonstration that the behaviour reproduces at all.** With arm A
   at zero `zone_moves` in 7 of 8 runs there is nothing to reduce, and any result
   is a property of the replay.

**Re-register only when both hold:** the control is **arm A against arm B in the
same run on the same payloads**, and payloads are drawn from the sessions at the
**top** of the per-session range (`b11b38dc` at 23.8%, `4351ed30`, `21f7c4e1`,
`34390b86`) with the behaviour **shown to reproduce first**. Not from the 0.5%
sessions.

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
| entries that are positional, pooled | **2,088 of 24,829 = 8.4%** (audited; see below) |
| per session | median **6.8%**, mean 9.0%, sd 7.0pts, range **0.5-25.4%** |

⚠ **The 100% is tautological and must not be quoted as a finding about the
Director.** Owner, 2026-08-13: `character_zones` sits in the schema's `required[]`
(`narrator.py:398`) and the prompt orders it — *"REQUIRED spatial draft completed
BEFORE every other field"*. A structured-output model fills a required field 1188
of 1188 times **by construction**. The number is true and it says only that the
provider honours the schema. The earlier phrasing *"answered in the Director's own
words"* is **withdrawn**: the Director did not volunteer this, it was ordered to.

**The load-bearing number is the 8.4%, and the engine throws all of it away.**

The replay adds one thing on top: asking explicitly raises the positional share
**4% → 35%** between arms A and B on the same payloads. So the behaviour is
present unprompted and improves when invited.

### ✅ THE 8% AUDITED — 2026-08-13, on the owner's objection

> *"1,967 of 24,829 is a judgement about model-authored free text. This project
> has shipped a string heuristic over model-authored text twice and been wrong
> both times. Write down: the rule, how many phrases you read by hand, and how
> many false positives you found."*

Fair, and the original number had **no stated rule at all**. One exists now
(`plans/artifacts/79-positional-audit/classify_positional.py`), it is written in
the file before the count, and it has a bucket for what it cannot judge:

| bucket | rule | n | share |
|---|---|---|---|
| `NAMES_A_ZONE` | the entry **is** a zone the session declares | 17,400 | 70.1% |
| `EXTENDS_A_ZONE` | a declared zone is its comma-prefix, plus detail | 254 | 1.0% |
| `PREPOSITIONAL` | contains a spatial preposition phrase | 1,834 | 7.4% |
| `UNCLASSIFIED` | **none of the above — counted as neither** | 5,341 | 21.5% |

**Positional = 2,088 of 24,829 = 8.4%.** Per session median **6.8%**, sd 7.0pts,
range 0.5-25.4%.

**Hand-read: 64 entries, in both directions.** 20 `EXTENDS_A_ZONE`, 20
`PREPOSITIONAL`, 24 newly caught after a bug fix, all systematically sampled.

> **Zero clear false positives. Three marginal**, all of them movement verbs
> (*"salão principal, recuando para a entrada"*, *"grupo oeste, recuando"*).

That is better than the objection feared, and the reason is worth recording:
**this rule matches PREPOSITIONS, which are language, not model-authored names.**
That is a materially different instrument from the two that burned this project —
`named_exclusions` matching *"a menos de dois metros"* and the prefix rule reading
a wing as a room — and it is why it survives a read that they did not.

#### The first cut was wrong, and the fix is why 8.4% is not 5.6%

The rule as first written scored **5.6%**. Reading its misses found four
Portuguese contractions it did not match — **"perto da", "ao lado do", "junto às",
"sobre sua"** — in a single twenty-line sample. Fixing the article into a suffix
group instead of a hand-enumerated list moved it to 8.4%.

**That is the fourth detector in this project to fail on morphology rather than on
meaning**, after `proxim[oa] a` missing an a-grave, `fila` inside *"em fila"*, and
`named_exclusions`. The correction is recorded in the script.

⚠ **The original 8% was right in magnitude by luck.** With no rule stated, nobody
could have known whether it was the 5.6% version, the 8.4% version, or something
else. Being right and being checkable are different properties.

#### The undercount is real, it is READ, and one source of it is this task's own defect

The 8.4% is a **floor**. Three sources of miss, each found by reading, each named:

1. **`NAMES_A_ZONE` — 70.1% of all entries — 2 of 20 read are positional phrases
   that the Director minted as a zone**, and which the rule therefore scores as
   *"just naming a place"*:

   ```
   saída lateral, junto a Garran
   próximo à saída norte
   ```

   **This is not a detector bug. It is task 79's defect converting its own
   evidence into zone names.** Once a position has become a zone, no instrument
   can tell it from a room, because at that point the engine cannot either. The
   measurement is biased downward *by the thing it is measuring*.

2. **`UNCLASSIFIED` — 21.5% — about 6 of 20 read clearly positional**, another 6
   marginal: *"flanco oeste, observando a aranha"*, *"antecâmara, grupo oeste"*,
   *"marcas de espera, grupo sul"*.

3. **English leakage.** At least 3 of those 20 are in English — *"central floor,
   mid"*, *"near Marta, at equipment chest"*, *"retreating with short steps, near
   debris edge"* — while the prompt orders Brazilian Portuguese and the rule is
   Portuguese-only. A separate small finding worth someone's attention: this field
   leaks English that no other channel does.

**Honest statement, and it is the same shape this task already reached for
`zone_moves`: 8.4% is a lower bound, not an estimate.** The hand read says the
true figure is materially higher; no string rule can pin it; and do not build a
better regex, because source 1 is not reachable by one.

#### What the audit does NOT change

**The decision.** This task's standing argument is already *"the field is
warranted even if the true rate is 5%, because the engine cannot distinguish a
room from a position at all"*. The audit **strengthens that argument rather than
the rate**: it demonstrates by hand that the instrument cannot distinguish them,
and shows exactly why — the positional phrases become zones and disappear.

**Status: MEASURED**, with a stated rule, a 64-entry hand read in both directions,
a per-session spread, and a named, read, unquantified undercount.

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
