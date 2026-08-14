# Task 79 — Blocking as durable state

> **Status:** open. **Decisions 1 and 2 are APPROVED by the owner (2026-08-13);
> decision 3 is DEFERRED and decision 4 is REJECTED.** Still no `Scene` field and
> no serialization until the deferred bump is decided. Task 76's graph stays
> frozen.
>
> ## ✅ SHIPPED 2026-08-13 — the ship-now half, no schema change
>
> `narrate()` no longer discards `scene_blocking.character_zones`. It sanitizes it
> and hands it to the prose renderer **for that turn only**, as a `BLOCKING` block
> naming where each person stands. **Nothing is persisted, `Scene` gains no field,
> `SESSION_SCHEMA_VERSION` is untouched, and the 33 archived sessions stay
> openable.** 1131 tests pass, `ruff check` clean.
>
> | | |
> |---|---|
> | `src/agents/narrator.py` | keeps `character_zones` as `result["blocking"]`; the rest of `scene_blocking` is still popped |
> | `src/agents/prose.py` | `_blocking_lines()` + the `blocking` argument, filtered by `viewers` |
> | `src/runner.py` | threads it from the Director's result to the renderer |
> | `tests/test_per_viewer_narration.py` | **the cross-cluster leak case, in task 71's suite** |
> | `tests/test_blocking_is_not_perception.py` | **decision 1's FORBIDDEN row, as a test** |
>
> **Sanitized like event content, because it reaches a blind renderer's prompt:**
> present characters only, normalized, **redacted against the same thought
> secrets**, truncated at 160 chars. It is free text the Director wrote without
> being asked to keep a secret.
>
> **Structural guarantee, the same one task 71 made:** a turn with no blocking
> calls the renderer with the **pre-79 signature** and builds a **byte-identical**
> prompt. Pinned by a test. That is what keeps every injected renderer and every
> archived comparison on their own path.
>
> ✅ **Discharged 2026-08-14.** A `base`/P1 cell ran on the shipped code and
> `scan_cross_cluster_leak` reports **0 leaking of 48 split narrations**
> (`ea6620fb` 0/46, `bb72dc94` 0/2) against the 3/78 baseline. **Handing blocking
> to the renderer did not re-open task 71's leak.**
>
> **Next action: the owner's word on the re-priced proposal**
> (`.plan/para-o-dono/79-blocking-shape.md`). The schema bump is recommended
> **against** — median 5.6% symptom, irreversible cost, and no instrument that
> could verify the fix afterwards. Proposed instead is the half that needs no
> storage: `narrate()` hands `character_zones` to the prose renderer for the
> current turn.
>
> ⚠ **Decision 4 is not merely rejected, its whole SHAPE is dead.** Any falsifier
> asking *"did positional `zone_moves` fall?"* needs an instrument that classifies
> a move as positional, and **three independent attempts have now failed** - a
> string rule (five false positives), the Director's own `witness_ids` (median 95%
> of the cast), and a blind reader of the prose (88% not determinable).
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
| destination whose prefix names the origin (hierarchical) | ~~34%~~ | ~~15% / 35.0pts / 0-97%~~ |
| destination containing a positional phrase (*"ao lado de"*) | 12% | 0% / 19.6pts / 0-79% |
| ~~**union of both**~~ | ~~**31%** (163/523)~~ | ~~**22% / 31.5pts / 0-95%**~~ |
| ✅ **CORRECTED union, 2026-08-13** | **16.7%** (101/606) | **median 5.6% / sd 22.0pts / 0-79.3%**, and **12 of 27 sessions at zero** |

### ⚠ The 31% was inflated about 2x, by the failure task 76 already documented

**Found 2026-08-13** while looking for payloads the falsifier could run on. The
hierarchical half tested whether the destination's first comma-segment was a
**substring of** the origin. Every zone in this scenario is named
`Academia Real do Primeiro Sino, <somewhere>`, so it fired on **every move
anywhere inside the academy**:

```
from: Academia Real do Primeiro Sino, Salão dos Quatro Arcos
  to: Academia Real do Primeiro Sino, Pátio Externo        <- a walk outdoors
  to: Academia Real do Primeiro Sino, salão de reunião     <- a different hall
from: Academia Real do Primeiro Sino, salão de reunião
  to: Academia Real do Primeiro Sino, jardins leste        <- the gardens
```

One turn of `17ec48d5` scored **21 positional moves** and every one was the cast
walking to the outer courtyard.

**This is exactly the pair of false positives task 76 shipped** — a wing and a
building read as rooms — arriving in a **new** instrument three weeks later, in a
different file, written by someone who had read that lesson and written it down.
The correct test is the whole origin plus a comma suffix, which is what
`EXTENDS_A_ZONE` in the audit script does.

**Read to confirm the correction, 15 of the 127 rejected entries**: all 15 are
genuine room-to-room moves. Two of them are **origin identical to destination** —
the Director emitting a move to where the character already stands, which is a
small separate defect nobody has counted.

**What it does to this task, stated plainly: the headline shrinks by half.**
16.7% pooled, median **5.6%**, and 12 of 27 sessions never do it at all. That is
a much smaller symptom than *"a third of all movement"*.

**And the task is unaffected**, because it stopped resting on this number on the
same day it was written. The standing argument below — *if a parser cannot tell a
room from a position by its name, neither can the engine* — is now carrying the
whole justification, and this correction is the fifth piece of evidence for it:
**five instruments, five failures, all on names.**

⚠ **16.7% is itself a floor**, for the same reason as before: a destination that
renames its origin, or a position minted as a bare zone, still scores zero.

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

## The structural test — pre-registered 2026-08-13, BEFORE running

The owner's standing question, after the fifth naming failure:

> *"Is there a way to measure room-vs-position that never matches a zone name?
> Try one structural signal and compare it against the corrected string rule on
> the same corpus. If they agree, the string rule is vindicated. If they
> disagree, you have found the sixth one before it shipped."*

### The signal, and why it touches no name

**The Director's own `witness_ids`, as proposed, before the engine clamps them.**
Those are sets of character ids. Comparing them is set arithmetic: **no string is
ever matched against a place name.**

For each recorded move of character `C` from origin `O` to destination `D` at turn
`T`:

- `peers` = the characters standing in `O` at `T-1`, excluding `C`. Skip the move
  if `peers` is empty — with nobody left behind there is nothing to separate from.
- Over the `perception_events` of turn `T`, count:
  - **together** — events whose `witness_ids` contain `C` **and** at least one peer;
  - **apart** — events whose `witness_ids` contain `C` but no peer, or a peer but
    not `C`.
- **together > apart → the Director still treats C as co-present with the people
  it left. That is a POSITION inside the room.**
- **apart >= together → the Director treats them as separated. That is a ROOM
  CHANGE.**

It reads the **raw response** in `debug.jsonl`, not the persisted audience, so it
is the Director's own belief formed *before* the engine's name-derived graph
touches it. That independence is the whole point.

### The validity check that runs FIRST, and can kill the signal

**If the Director lists nearly everyone as a witness of nearly everything, this
signal has no discriminating power and the comparison is meaningless.** So before
any agreement rate:

> Report the distribution of `|witness_ids| / cast size`. **If the median is above
> 0.9, the signal is dead on arrival**, and that is reported as the result rather
> than dressed up as a comparison.

### The decision rule, written before the numbers exist

| result | conclusion |
|---|---|
| **agreement >= 80%** of comparable moves | the corrected string rule is **vindicated**. Stop worrying about it, keep using it, record the agreement rate next to it in the register |
| **agreement < 80%** | **read the disagreement set.** Whichever the reading supports wins; the loser gets an entry in `metric-validity.md`. This is the sixth naming failure caught **before** it shipped |
| the structural signal is **inapplicable** to most moves (no peers, no events) | report the coverage honestly and treat the test as **not run**, rather than quoting an agreement rate computed on a handful |

⚠ **The structural signal is not automatically the truth.** It has its own failure
mode — a lazy or generous Director — which is exactly what the validity check
above is for. If the two disagree, **neither wins on authority**; the reading of
the disagreement set decides, per rule 3 of `.plan/guides/MEASURING.md`.

### ❌ RAN 2026-08-13 — the signal FAILED its own validity check, and that is the result

**Median `|witness_ids| / cast` = 0.95.** Quartiles 0.86 / 0.95 / 1.00 over 4,843
Director events.

**The Director lists nearly the entire cast as witnesses of nearly every event.**
By the check registered above the signal is dead on arrival: with everyone
witnessing everything, `together` wins almost automatically, and it does — the
structural rule calls **93.2%** of moves a POSITION, including a walk from the
hall to the outer courtyard with 20 peers left behind.

Agreement with the corrected string rule is **24.5%**, and that number means
nothing: it is one instrument disagreeing with a broken one.

| | structural=POSITION | structural=ROOM |
|---|---|---|
| **string=POSITION** | 77 | 2 |
| **string=ROOM** | **319** | 27 |

**Reported as registered, not dressed up as a comparison.** The string rule is
**neither vindicated nor falsified** by this. The test did not run.

#### What it did find, and it is worth more than the test was

**`witness_ids` carries no scoping information.** A field that names who perceives
an event, set to ~95% of the cast, is not a perception judgement — it is a
formality. This corroborates task 67's finding from the other end (*"only 2 of
1,868 raw Director events proposed an empty witness list"*) and generalises it:
the Director does not narrow audiences at all, the **engine's clamp does all of
the narrowing**, and every audience number in this project is a property of the
graph rather than of the Director's intent.

Registered in `.plan/reference/metric-validity.md` as **measured and rejected**
for this purpose, so nobody builds a scoping signal on it.

## The structural test, second attempt — a blind read, pre-registered before running

The witness signal died on its own check. The owner's third hint is the one left,
and `.plan/guides/MEASURING.md` ranks it as a legitimate source: *"a reader's
judgement, stated as a metric... often the best available"*.

> *"the narration either describes a room change or does not"*

**The instrument is a blind judge reading prose.** It never sees a zone name, a
destination string, or the string rule's verdict, so it cannot reproduce the
failure being tested for.

**Sample.** 40 recorded moves, **stratified**: 20 the corrected string rule calls
POSITION and 20 it calls ROOM CHANGE, systematically drawn within each stratum and
**shuffled** before dispatch.

**What the judge is given:** the narration of that turn, the moving character's
name, and nothing else. **What it is asked:** did this character move to a
different place, reposition within the place they were already in, or is it not
determinable from this text?

**Decision rule, before the data exists:**

| result | conclusion |
|---|---|
| **agreement >= 80%** on determinable cases | the corrected string rule is **vindicated**. Record the rate beside it in the register and stop worrying |
| **agreement < 80%** | **read the disagreements.** The reading decides; the loser gets a register entry. Sixth naming failure, caught before it shipped |
| **"not determinable" on more than half** | the prose does not carry the distinction, which is itself an answer: **no instrument of any kind can recover room-vs-position from this corpus**, and the task rests entirely on its standing argument |

⚠ **The third row is a live possibility and it is the most useful outcome.** If a
careful reader with the actual narration in front of them cannot tell whether
somebody changed rooms, then the engine certainly cannot, and that is this task's
standing argument promoted from an assertion to a measurement.

### ✅ RAN 2026-08-13 — the third row fires: 88% NOT DETERMINABLE

40 blind reads, 0 failures.

| | |
|---|---|
| `NAO_DA_PARA_SABER` | **35 of 40 = 88%** |
| determinable | **5** |
| agreement on those 5 | 2 of 5 — **n=5, quoted as n=5, not as 40%** |

**A careful reader holding the actual narration cannot tell, for 88% of recorded
moves, whether the character changed rooms or shifted position inside one.** Not
because the reader is weak: because *the prose does not say*. The judge was given
the whole narration and one character's name, and 35 times out of 40 the text
simply does not render that character's movement.

The three disagreements are worth reading, and they point in both directions:

- `00997daa` T16 — the recorded `zone_moves` sends the character from the hall to
  the central courtyard. The narration says only *"Ele recua da beira da
  rachadura, os calcanhares batendo com firmeza"* — he steps back from the edge of
  a crack. **The prose and the state change describe different events.** The judge
  read the prose correctly and the string rule read the state correctly, and they
  are describing different things that happened in the same turn.
- `09aabf25` T22 — *"dá um passo curto... em direção ao portão norte"*, one short
  step. The judge called it a place change; on reading, the string rule looks
  closer.
- `09aabf25` T35 — *"avança ao lado de Link pela ponte improvisada de pedra sobre
  a fissura"*. Genuinely ambiguous.

## ⛔ THREE INSTRUMENTS, THREE FAILURES — and that is now the measurement

This is the result the owner's instruction was fishing for, and it is stronger
than a vindication would have been.

| instrument | independent of names? | outcome |
|---|---|---|
| string rules over zone names | ❌ no | **five registered false positives**, the latest making a headline **2x** too high for three weeks |
| the Director's own `witness_ids` | ✅ yes, set arithmetic | **dead on its validity check** — median witness list is **95% of the cast** |
| a blind reader of the narration | ✅ yes, no names shown | **88% not determinable** |

**No instrument TRIED can measure room-versus-position on this corpus** — four of
them now, each failing for a different reason.

⚠ **The earlier wording here said "nothing available can measure it" and that was
over-reach.** Three isolated critics killed it independently on 2026-08-13: it is
a universal impossibility claim drawn from a handful of attempts, each of which
failed for a reason that is a property of *the instrument*, not of the corpus.
**"Tried" is the whole difference**, and the record now says only what was shown.

**The fourth instrument, run because a critic caught that this project's own rule
names it and it had never been tried.** `MEASURING.md` rule 5's corollary says
*"prefer a structural signal to a string one... `Scene.positions` maps a character
to a zone without parsing anything"* — written the same day, by the same author,
who then reached for `witness_ids` instead. Exactly the shape rule 5 already logs
about itself.

> **The signal:** was the destination a zone that already existed at T-1, and was
> anyone else standing in it? A move to a place that exists, or where people
> already are, is a place. A destination that is newly minted and empty is the
> Director inventing somewhere for one character — which is what this task says
> happens when a position has nowhere to live. Set membership on keys and ids,
> no string matching at all.
>
> **It passes its validity check** — fires on 73.2% of 512 moves, so it is not
> degenerate the way `witness_ids` was — **and then fails on reading.**
> `salão dos quatro arcos → pátio central` scores POSITION because the courtyard
> is newly minted and empty. **A genuinely new room is also newly minted and
> empty.** It separates novel destinations from familiar ones, which is a real
> distinction and not this one. Agreement with the string rule: 35.4%.

**So: four instruments, four different failures.** A string rule that measures
naming; a perception signal that is saturated at 95% of cast; a blind reader that
answers "cannot tell" 88% of the time; and a structural signal that measures
novelty. That is a strong statement about four attempts and **not** a proof that a
fifth cannot exist.

**Reopening condition, which the earlier version lacked:** any instrument whose
positives **and** negatives have both been read, on this corpus. Write it down
here when it exists.

### What that does to the standing argument — it promotes it

> **If a parser cannot tell a room from a position by its name, neither can the
> engine.**

Adopted 2026-08-13 as an assertion. It is now **MEASURED**, and in a stronger form
than it was written: *nothing* can tell them apart, and the engine is merely the
worst-placed of the three. The field is warranted not because the rate is large —
**it is small: 16.7% pooled, median 5.6%, 12 of 27 sessions at zero** — but
because the distinction is **structurally unrecoverable** once a position has been
minted as a zone. A field that exists does not have to recover anything.

### ⚠ And it kills an entire CLASS of falsifier, including the one being re-drafted

Decision 4's rejected falsifier, and every replacement in the same shape, asks:
**does positional `zone_moves` fall after the change?** That question requires an
instrument that can classify a move as positional. **There isn't one.** The
rejected version's flaw was its control; the deeper flaw is that its *measurement*
cannot exist.

**So decision 4 is not re-registered here.** Any falsifier for this task has to be
about something observable: whether the prose renderer stages people where the
Director actually put them, judged by a blind read of narration quality, which is
the one instrument on this page that produced a usable answer about anything.

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

### ⛔ WITHDRAWN ENTIRELY, 2026-08-13 — do not rebuild it a third time

The re-registration conditions above were met in the sense that better payloads
were found (`5d60575d` T3 moves 18 characters to *"...Salão dos Quatro Arcos,
junto à saída lateral"*; `c76037ff` T16 moves 16). **It does not matter, and the
conditions are moot.**

**The target does not exist.** Every version of this falsifier asks *"did
positional `zone_moves` fall?"*, which requires an instrument that can classify a
move as positional. Three independent attempts have now failed:

| instrument | outcome |
|---|---|
| string rules over zone names | five registered false positives, latest 2x too high |
| the Director's own `witness_ids` | dead: median witness list is **95% of the cast** |
| a blind reader given the narration | **88% not determinable** |

**The control was never the deepest problem.** Version 1 failed its clause for the
wrong reason, version 2 was rejected for measuring the harness, and version 3
cannot be built at all. All three are recorded here, in order, so the next person
does not start a fourth.

### What replaces it: the ship-now half is a QUALITY change, judged by a blind read

**Stated plainly so nobody looks for a rate later and concludes it failed.**

The half that ships without a schema bump — `narrate()` handing
`character_zones` to the prose renderer as staging — **is not a defect fix.** It
does not reduce a count. It gives the renderer better material: where the Director
actually put people, instead of a zone name that no instrument can interpret.

**Its acceptance instrument is the blind read**, which the roadmap already names
as the acceptance instrument for anything narrative (*"the narrative baseline is
the blind read, not a number"*).

> **Baseline, measured 2026-08-13 and already on record:** a blind reader given a
> turn's narration and one character's name answers *"não dá para saber"* for
> **35 of 40** stratified cases (88%). Full method in
> `.plan/backlog/80-the-narration-does-not-convey-space.md`.
>
> **Done looks like:** that share falls on a post-change cell, arms in the same
> run, judged by the same prompt. **No `zone_moves` rate is a gate for this
> change, and quoting one against it is a category error.**

### ⚠ DESIGN REVIEW, before the ship-now half is written: it can re-open task 71's leak

Raised by the owner 2026-08-13, and it is right.

`scene_blocking.character_zones` maps **every present character** to a position.
Task 71 made narration render **per perception cluster** and closed a
cross-cluster leak from **16/29 to 3/78** on 2026-08-04. If the blocking is handed
to the renderer whole, **the renderer for cluster A now holds where cluster B's
people are standing** — the same leak returning through a door nobody is watching,
inside the task that closed it.

**The filter point is already there.** `build_prose_messages` and `_staging_lines`
both take `viewers: set[str] | None` (`src/agents/prose.py:201,246`) and it
already scopes the cast, the staging block and the transcript. `character_zones`
must be filtered by **that same set** before it reaches the renderer, not
afterwards and not by a separate rule.

**Required before this ships:**

- [ ] `character_zones` is filtered by `viewers` at the same point the cast is;
- [ ] a test that a character in cluster B does **not** appear in cluster A's
      staging material — **added to task 71's suite
      (`tests/test_per_viewer_narration.py`), not only to 79's**, because that is
      the suite whose job is to catch this and the place the next person will look;
- [ ] `scan_cross_cluster_leak` re-run on a post-change cell against 3/78.

Cheaper now than after.

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

#### ⚠ The set the rule ACCEPTS was finally read — 2026-08-14 — and 16.7% is not a rate

Three critics independently caught the same gap: the 15 entries read in the 2x
correction came from the **127 the corrected rule rejects**. That validates the
correction and says nothing about the 101 it accepts, which are the entire
numerator. `MEASURING.md` rule 5 requires reading **the set it separates** — both
sides.

Read at last, 20 systematic of 92 accepted moves:

| what the read found | n of 20 |
|---|---|
| genuine repositions | ~12 |
| **origin identical to destination** — a no-op move counted as a reposition | 2 |
| **room changes matched by a stray preposition** | 2 clear, 4 arguable |

The clear failures:

```
Salão dos Quatro Arcos  ->  corredor, atrás de C17, mantendo distância
degraus da entrada      ->  pátio central, próximo ao corredor
```

Both are moves to a **different place** that matched only because the destination
happens to describe a position relative to a person or a corridor. (The first also
carries a raw character id inside a zone name, which is its own small finding.)

**And the clustering is severe: 92 accepted moves come from 15 sessions, with one
turn contributing 5 identical entries (`5d60575d` T3) and another 4
(`c76037ff` T16).** The effective n is nowhere near 92.

**Conclusion: precision on the accepted set is roughly 60-80%, not the ~100% the
`character_zones` audit found on its own different population.** Combined with a
median of 5.6% and 12 of 27 sessions at zero, the honest description is:

> **zero-inflated, heavily clustered, and carried by a handful of turns. 16.7% is
> not a rate and must not be quoted as one.** It is the output of an instrument
> whose positives are 60-80% precise, over a corpus where most sessions score
> zero.

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
