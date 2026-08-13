# Checkpoint — 2026-08-13

Written after a block of work that produced **many measured symptoms and almost
no confirmed mechanisms.** That asymmetry is the finding, and it is what this
checkpoint reorders the phase around.

---

## The theory question, asked plainly

For each open task, two separate things: **does the symptom exist** (a count over
sessions), and **do we know why** (a mechanism that survived a test).

| task | symptom | mechanism |
|---|---|---|
| **79** blocking has nowhere to live | not a symptom; a **code fact** | ✅ **ESTABLISHED.** The Director writes blocking in **1188 of 1188** director calls, 8% of entries positional (median 6%, range 0-44%). `narrate()` pops the field. Both halves verified in code and in 33 sessions |
| **69** events re-proposed | ✅ measured: **703 of 5,064** flagged over 33 sessions (13.9%; median 12.5%, sd 5.2pts) — but **43.4% of those are speech**, so 69 owns about half | ✅ **CAPACITY EXCLUDED 2026-08-13.** 17 of 18 genuine re-proposals happen with the original **still in the prompt** — one with `"parede_rompida": "true"` in the facts bag as the wall breaks again. Nothing is forgotten. The mechanism is that settled state does not bind the output |
| **77** the order nobody executes | ✅ measured: **13 of 33 sessions (39%)**, 23 windows, median 0 | ❌ **UNKNOWN after three falsified attempts** (contract-forbids, variance, beat machinery) |
| **64** control returns rarely | ✅ measured: never-returned **5/12 → 0/9**; rate ~3% | ~ suspected: contract wording. Untested |
| **78** routed into silence | ✅ measured: **13 of 1,255** speech records (1%), concentrated in runs | ❌ not investigated |
| **72** commitments as state | ✗ no symptom of its own | ✗ a design, gated |

**One task has an established mechanism, and it is the cheapest one.** That is
the whole basis for the reordering below.

### Why so many mechanisms died

Every causal story written in this block was falsified by its own evidence:

- 77's *"the contract forbids enactment"* — arm A moves people 3/8 times on the
  exact payloads that recorded `null`.
- 77's *"variance"* — untestable, replaced.
- 77's *"the beat is never consumed"* — the beat advances and replans; beats with
  unsatisfiable positional exit conditions run **shorter** (0.94x).
- 79's *"the Director needs a new field"* — it ignored the new key because it
  **already fills an existing one**.
- 76's *"the naming convention gates the rule"* — firings track opportunity 6/6;
  convention does not predict opportunity.
- 69's *"the fact store is full, so the engine forgets"* — **17 of 18**
  re-proposals happen with the original still in the prompt, one of them while
  the bag says `"parede_rompida": "true"`.
- 69's *"the mandatory UPCOMING EVENT clause forces a non-event into slot 0"* —
  re-proposal turns carry that block **23.7%** of the time against a **27.0%**
  control, **down in 20 of 31 sessions.** Killed by a control that cost nothing,
  under a rule written before the number existed.

**Not one was caught by a number looking wrong. Every one was caught by reading
records or code.** That is now seven for seven, and it is the standing method.

Two of the seven landed on 69 in one afternoon, and the first of them is the only
falsification in this phase that made a task **cheaper and better aimed** rather
than smaller: 69 no longer has to solve remembering, only binding.

---

## Reordered wave 2 — by mechanism confidence, not by symptom size

**Principle:** prefer work whose mechanism is established and whose change is
cheap and reversible, over work whose design rests on an unconfirmed story. A
task with a big symptom and no mechanism is a **research** item, not a build item,
and scheduling it as a build item is how a phase turns into the loop it is trying
to avoid.

| order | task | why here |
|---|---|---|
| **1** | **79** — blocking as durable state | The only established mechanism in the phase, and the change is *stop discarding a field we already receive*. Still **docs-only** pending the owner's shape decisions. Everything else waits behind less certainty than this |
| **2** | **69** — physical state as a closed transition | Symptom measured and stable post-wave-1. **Its capacity story is now excluded** (17 of 18 re-proposals happen with the original still in the prompt), which narrows it: settled state must **bind the output**, not be easier to retrieve. Owns the storage model that 79 must fit. ⚠ No replay payload reliably reproduces the defect, so its fix will need a live cell |
| **3** | **64** — return control | Re-scoped to calibration. Cheapest possible test: a contract-wording replay, which is the same lever that tripled the rate in task 70 |
| **4** | **77** — the order nobody executes | **Demoted from first.** Real in 39% of sessions and sparse inside them, cause unknown after three attempts. **Keep observing, do not design.** It is the best-documented symptom in the phase and the least understood |
| **5** | **78** — routed into silence | 1% of speech records. Leave until someone reads more cases |
| gated | **72** — commitments as first-class state | Unchanged. Its gate is *"do stalls survive 69"*, and 69 has not shipped |

**⚠ 77 was moved down and that reverses the owner's 2026-08-13 instruction**,
which raised it above most of wave 2. The instruction predates the sizing (39% of
sessions, median 0 windows) and the third falsification. **Reordered under the
authorisation given the same day; say the word and it goes back to first.**

---

## The folder the phase actually lives in — corrected the same day

The reorder above says what to work on next. It did not fix the fact that
`tasks/` had stopped meaning *"active"*: it held **five finished tasks** (67, 68,
70, 71, 76, every closure item discharged) and **four files opened in a single
block** (76-79), which the critic protocol warns against by name.

**Rule applied: a file is in `tasks/` if it has a next action.** Not if its
symptom is big.

| moved | to | measure |
|---|---|---|
| 67, 68, 70, 71, 76 | `closed/` | every closure checklist fully discharged; 76's falsifier ran and fired |
| **78** routed into silence | `backlog/` | **13 of 1,255 speech records (1.0%)**, uninvestigated, no next action |

**77 stays in `tasks/` and by this rule it should not have.** It has no next
action either — its cause has survived three falsifications and its leading story
(un-remembered commitments) is task 72's, which is gated. It stays because **72's
gate cites 77's stalls**, so shelving it would leave a gated task pointing at a
shelved file. Recorded as the exception it is, in
`para-o-dono/routing-2026-08-13.md`, reversible in one line.

**79 stays in `tasks/`** — the only established mechanism in the phase, and its
four shape decisions are now on one page in `para-o-dono/79-blocking-shape.md`
instead of buried at line 91 of a 250-line file.

`ROADMAP.md`'s wave-2 table was still listing 77 first, disagreeing with this
checkpoint. It now carries the reordered table.

## What did NOT change

- **Task 76's graph stays frozen.** Its falsifier fired: the mass is in naming,
  the fix is not a graph rule, and the shipped prefix rule stays because it is
  correct where it fires.
- **79 stays docs-only.** The finding makes it cheaper, not approved.
- **`empty_audience`, `with_others_present`, `clamp_lost_half_unsealed` remain
  REPORT, DO NOT GATE.**
- **Session is the unit.** No pooled-turn p-value gets quoted without the caveat.
  Every headline number carries its per-session spread.

## Standing numbers, with spreads

| number | pooled | per session |
|---|---|---|
| cross-cluster narration leak (task 71) | 16/29 → 3/78 | 55%, 22% before; 0%, 9%, 0%, 0% after |
| split rate | 27.8% post-67 | **sd 17.9pts**, range 28.6-67.3 — untrustworthy at n≤4 |
| intra-room `zone_moves` (lower bound) | 31% | median 22%, sd 31.5pts, range 0-95% |
| positional entries in `character_zones` | 8% | median 6%, sd 9.0pts, range 0-44% |
| beat exit conditions phrased as a position | 13% | median 16%, sd 10.3pts, range 0-36% |
| restate-and-freeze windows | 23 total | **13/33 sessions**, median 0, max 5 |
| frozen adjacent turn pairs | 90.8% | P3 active player: 95.2%, p = 0.70 |

## The one thing to read first, next session

`.plan/reference/metric-validity.md`. Five instruments in this block reported a
clean number and were wrong, and the page now carries the general form: **lexical
distance measures whether the words changed; nothing here measures whether
anything happened.**
