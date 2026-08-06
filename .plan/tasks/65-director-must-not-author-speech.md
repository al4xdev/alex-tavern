# Task 65 — The Director must not author speech

> **Status:** open, **scope decided 2026-08-05, ready to implement.** Wave 1,
> still the largest measured defect in the archive; two blind reviewers with
> different framings — one auditing logs, one reading transcripts as fiction —
> independently concluded it should be the first cut of the phase, and that
> stands.
>
> **What did not stand is the 65a/65b split.** It was drawn on the assumption
> that 64% of the channel duplicates a line that already exists. Verified against
> the archive before implementation, the real figure is **21–42%**; the majority
> of this channel is dialogue that exists nowhere else, and the prose renderer is
> structurally forbidden from carrying it. See "⚠ 65a's premise did not survive
> verification" below. Shipping the original 65a would have deleted **264–362
> dialogue records** — exactly what Case 20's rule against buying quiet instead of
> movement exists to prevent.
>
> **The fix is now one task, not two halves:** the Director stops authoring
> persisted dialogue, and where a line is needed the character agent is routed to
> write it. 65b's open question is answered by the same decision — see
> "✅ The scope decision" below. What remains genuinely open is only how the
> Director's *intent* is expressed in the schema, which is an implementation
> question with a live-validation cost, not a design fork.

## Problem

`Runner._persist_audible_speech` (`src/runner.py:1404`) takes the Director's
`audible_speech` perception events and persists `event["content"]` — **text the
Director just wrote** — as a spoken record attributed to a character.

That makes the Director a second speaker. `AGENTS.md` §3 says it is not one:

| Papel | Responsabilidade |
|---|---|
| Narrador | Mundo físico, consequência, transição, cena, humor e próximo falante |
| Personagem | **Somente fala** e pensamento subjetivo em primeira pessoa |

The Director's own prompt forbids it too — *"DIALOGUE OWNERSHIP: never invent new
dialogue… Record only the stimulus or words already spoken in HISTORY"*. It is a
prompt promise, and prompt promises lose; this one loses 28% of the time.

## Scale

Measured over the twelve P1 sessions, matching each persisted `speech` record
against the Director's `audible_speech` event texts (`SequenceMatcher > 0.85`):

**467 of 1,649 speech records — 28.3% — were authored by the Director.**
Present in **12 of 12** sessions, in every cell, on both engines, on both input
profiles. Per-session it ranges 21%–40%.

Nothing else in this phase is close. For comparison: the redaction marker appears
in 11 of 12 sessions and 69 times total; the internal-id leak is n=1.

## What it produces

- **Duplication.** A character speaks, then the Director restates it in the third
  person in the same turn. `oldcode-P1-r1` T4 stacks **three** — *"Garran anuncia
  em voz alta…"*, *"Riven questiona em voz alta…"*, *"Lorde Cassian propõe…"* —
  so the last beat of the turn is a summary of the turn.
- **Self-narration.** `null-P1-r1` T26-T28: *"Téo, da arquibancada, comenta em voz
  alta que a decisão de desqualificar Link foi dura demais…"* — Téo speaking
  about Téo.
- **The player's own words read back.** `base-P2-r1` T2. The human typed
  *"Continuo aqui."* The turn ends:
  > **Link:** Link responde, em tom neutro, que continua aqui.
  > **Link:** Link acrescenta que sim, concorda em continuar ali.
- **The internal-id leak.** `oldcode-P1-r1` T39, *"C17 ordena que C20 permaneça
  com os estilhaços e que C18 a acompanhe"* — one record, three ids, and it came
  through this channel. n=1 in the corpus.
- **The language flip.** `null-P1-r2` T2 has **four** Director `audible_speech`
  events in English under a pinned Brazilian Portuguese — *"Asword said that
  Link's portal showed precise control…"* — two of which persisted. **Zero**
  narration records in the corpus are English. This was filed against the prose
  renderer; it belongs here.
- **42 of the 43** persisted records carrying `[indistinct]` are on this channel.
  Task 63's target population is almost entirely this task's population.

The existing guard cannot catch any of it. `_echoes_recent_speech` compares
against `voices = {subject}` only — by design, *"another speaker saying the same
thing is not an echo"* (`tests/test_audible_speech_echo.py`). Paraphrase in the
third person by a different producer is exactly what it is built not to flag.

## Why the channel exists (do not delete the requirement)

WT-09, documented in the docstring at `runner.py:1407-1425`: a fact voiced to the
room must reach the memory of **every witness**, not just whoever happened to
reply that turn. Before this channel, events were rendered to the turn's repliers
and then discarded, so a silent witness never got the fact and memory — which
reads history — never had it. That need is real and stays.

**Only the producer of the text changes.**

## ⚠ 65a's premise did not survive verification — 2026-08-05

**The version below claimed a pure win with zero content loss. It is wrong, and
implementing it would delete between 264 and 362 lines of dialogue that exist
nowhere else in the session.** Read this section before the next one.

### What the 64% actually counts

*"64% of Director `audible_speech` events are for a character who was routed that
same turn, **so a persisted record already exists**"* — the first clause is right
(the scanner measures 66%), the second does not follow. "The character also spoke
this turn" is a proxy for "the Director restated the line they spoke", and the
proxy fails: the Director usually re-voices **something else**.

Measured over all 458 Director-authored records in P1, against every line the
same character spoke in the same turn **and the four before it** — the window the
existing echo guard uses — scored by shared content words, which is far more
forgiving of third-person paraphrase than the lexical ratio that found them:

| "restates a recent line" at overlap ≥ | restatements | **new content** |
|---|---|---|
| 0.3 — barely more than sharing a topic | 194 (42%) | **264 (58%)** |
| 0.4 | 135 (30%) | **323 (71%)** |
| **0.5** — a defensible reading | **96 (21%)** | **362 (79%)** |
| 0.8 — near-verbatim | 14 (3%) | **444 (97%)** |

**The conclusion is robust across the whole threshold range**: even at the most
generous setting, where "restatement" means little more than talking about the
same subject, the majority of this channel is new dialogue. Only **19 of 458**
are close paraphrases of the character's own line *in the same turn*, which is
the case the original text described.

### And the prose renderer cannot carry the content

This is what makes the cut expensive rather than merely debatable. The prose
prompt **never receives `audible_speech` content** — the event is filtered out of
`event_lines` entirely and `_stage_event_content` reduces it to *"X diz algo
audível para Y"* (`prose.py:98-107`, `:262`). That is a deliberate leak guard:
the renderer must not be able to re-voice dialogue.

So the persisted speech record is the **only** path by which those words reach
the reader. Dropping it does not move the line into narration; it removes it from
the story. Case 20's pre-registered rule binds directly: *a cut that buys quiet
instead of movement is a failure, not a fix.*

### What survives, and what this does to the 65a/65b split

The channel is still a role-boundary violation and still owns the duplication,
the self-narration, the player's words read back, the id leak, the language flip
and 40 of the redaction markers. **None of that is retracted.** What changes is
the shape of the fix:

- the population that can be dropped or referenced with no content loss is
  **21–42%**, not 64%;
- the population that needs a *producer*, not a deletion, is **58–79%** — it is
  the majority of the channel, and it was scoped as 65b's minority case;
- so **65b option 1 — route the character for a real line — stops being one of
  three alternatives for a corner and becomes the primary mechanism.** Costed
  against the archive it is roughly **+38 character calls per session (~+33%)**,
  which is the number that has to be decided before anything ships.

## ✅ The scope decision — 2026-08-05, by the owner

**Route the character.** When the Director wants a line voiced and there is no
existing record to reference, the Runner calls that character's agent with the
Director's intent as a stimulus, and persists **the line the character wrote**.
The Director never authors persisted dialogue again.

This was chosen over the cheap alternative (persist it as a narrated report by
the Narrator, zero extra calls) with the cost on the table and the reasoning
recorded, because the reasoning is the part that has to survive:

> *"daqui a 2 anos, se lançar uma LLM de baixíssima latência e alta taxa de
> tok/s, eu vou me arrepender e nem vou me lembrar dessa micro decisão que deixei
> passar."*

That is the right way round. **The cost here is a property of today's models; the
compromise would be a property of the engine forever.** Latency and throughput
have moved every year of this project's life; the role boundary in `AGENTS.md` §3
is what made the whole of `docs/cases/21` possible to write. Trading the second
for the first buys a temporary saving with a permanent defect.

### The cost, measured rather than estimated

Re-derived from the archive after the decision, because the option list quoted a
per-session figure and a per-turn figure is what a player feels:

| | |
|---|---|
| Director-authored speech records **per turn** | mean **1.02**, median **1**, p90 **2**, max **4** |
| turns needing no extra call at all | **135 of 450 (30%)** |
| character call latency | median **2,716 ms**, p90 **3,461 ms** |
| character prompt-cache hit ratio | **50.4%** |

So the typical turn costs **one extra character call**, not thirty-eight. The
"+38 per session / +33%" figure quoted in the fork was true and misleading in the
same breath.

**And the extra calls parallelise.** The reply loop is sequential today
(`for speaker in queue: … await self._call_character(...)`), but these events are
all known the moment the Director returns and none of them depends on another, so
they issue in one `asyncio.gather` — the pattern already used at
`runner.py:1313-1317`. That turns the worst turn in the archive from four serial
calls (~11 s) into one round trip (~3.5 s). **Gathering is part of the task, not
an optimisation to consider later**: without it the p90 turn pays twice.

### The fallback, and why it is a fallback

The narrated-report option is not discarded — it becomes the **degradation path**
for the cases routing cannot serve: a character who is not present, a routing
call that fails, or a Director event whose subject cannot be resolved. In those
cases the record is persisted as a Narrator report with the same audience,
reporting the speech instead of quoting it (*"Maelis anuncia que a seleção
começa"*), which is world-event territory and belongs to the Narrator by the
`AGENTS.md` §3 table. What must never happen again is a record that **claims a
character said words the character did not author**.

That phrasing is also the corrected invariant. The scanner counts *speech*
records matching Director events, so a pure relabel would drive it to zero by
reclassification without fixing anything — noted here so nobody mistakes the
metric for the goal.

**Nothing is implemented against the section below until that fork is chosen.**

## 65a — the half with no design risk (wave 1) — SUPERSEDED, see above

Measured by the audit: **64%** of Director `audible_speech` events are for a
character who **was routed that same turn**, i.e. the character agent produced a
real line and the Director restated it. For these, a persisted record already
exists.

Direction: persist a **reference** to the existing record, never the Director's
text. Where the referenced line already exists in history, the Director's version
is dropped with zero content loss — it was duplication.

~~This is the pure win.~~ It kills all the duplication, the self-narration, the
player-words-read-back, and the id leak; it takes most of `[indistinct]` with it
— **and it deletes the majority of the channel's content along with them.**

## 65b — ANSWERED 2026-08-05 by the scope decision above

The other **36%** are for a character who was **not routed that turn**. There is
no agent output to reference. Referencing-only deletes them — roughly **18% of
all dialogue in the corpus**. *(And the verification above shows this population
is larger than 36%: routing is not the same as restating, so most of the 64% side
needs a producer too. 65b's case is the majority case.)*

Case 20's pre-registered rule binds here: *a cut that buys quiet instead of
movement is a failure, not a fix.* So 65b is a design question, not a cut:

- ✅ **CHOSEN** — have the Runner route the character for a real line when the
  Director wants one voiced (costs a call, keeps the role boundary);
- let the Director emit a *stimulus* (not dialogue) that a later turn's character
  agent may voice — **rejected**: it defers the line to a turn where the scene has
  moved on, and the fact voiced to the room is what WT-09 exists to preserve;
- accept a narrated, unattributed record — audible to witnesses, owned by no
  speaker — **kept as the degradation path only**, for events routing cannot
  serve.

~~Ship 65a, then measure at the checkpoint before choosing.~~ The choice was made
before shipping instead, because the verification showed 65a could not ship in
its original form and the two halves collapse into one decision.

> **Corrected 2026-08-05.** This line used to read *"ship 65a with an `NSR`/`SIL`
> interlock"*. That interlock does not work: `NSR` measures event volume and runs
> **anti**-correlated with read quality on this corpus (ρ = +0.923), `SIL` is
> `0.0` in 16/16 runs, and `base`'s own within-cell `NSR` spread (1.12) is 7× the
> effect 65a could produce. Derivation in `.plan/ROADMAP.md`.
>
> The question 65b needs answered is *"did removing 18% of the dialogue thin the
> fiction?"* — which is a reading question. **The blind read answers it**; a
> volume counter cannot. Re-run it at the checkpoint against the pre-65a
> transcripts.

## Counter-argument, recorded

*"28% is inflated — some of those matches are the Director faithfully echoing a
line, which is the WT-09 feature working."* Correct, and that is precisely the
64/36 split. The 64% is duplication because the original record is already there;
the echo adds a second copy. The 36% is the feature. The number that decides 65a
is not the 28% — it is that in the 64% case a persisted original **already
exists**, which is parameter-free.

> **This paragraph is the error, and it is left standing so the shape of it is
> visible.** It says the deciding number is "parameter-free", and it is: *whether
> the character was routed*. The mistake is that the parameter-free number
> **answers a different question** than the one the design needs. Routing tells
> you an agent ran; it does not tell you the Director restated what came out of
> it. Measuring the second question directly (above) moves the safe population
> from 64% to 21–42%. A number being clean and cheap is not evidence that it is
> the right number.

## The scanner exists, and this is its "before" — 2026-08-05

`tools/acceptance/immersion_scanners.py`, archived at
`benchmarks/*/immersion-scan.json` and defined in `benchmarks/README.md` §8. It
matches each persisted speech record back to the Director event in `debug.jsonl`
that produced it, because nothing in `state.json` distinguishes the two producers
— a re-voiced line carries `audience_origin='zone'` exactly like an ordinary one.

| | P1 (12 sessions) | P2 (4) |
|---|---|---|
| Director-authored speech records | **458 of 1,601 (28.6%)** | **181 of 618 (29.3%)** |
| sessions affected | **12 of 12** (21.3–40.6%) | **4 of 4** (24.5–33.1%) |
| …for a character routed that same turn | **303 (66%)** | **132 (73%)** |
| …carrying a redaction marker | 40 | 15 |

An independent re-derivation of this task's headline number, off a second
implementation. The threshold that separates the two producers is not a judgement
call: matched pairs score 0.857–1.000 (median 1.000) and the nearest non-match in
the whole archive is 0.827, an empty band the scanner's constant sits inside. One
record scores above the line unmatched, so **458 is conservative by one**.

## Implementation shape, after the decision

Written down so the next session does not re-derive it. Order matters: the two
cheap deterministic items are independent of the routing work and can land first.

1. **The Director's `audible_speech` stops carrying dialogue.** The event
   declares *who speaks and what they are conveying*, not the words. This is a
   schema + prompt change, so it is the one part that carries a live-validation
   cost — `AGENTS.md` §6, the validated variant IS the shipped variant, and its
   position in the prompt is part of the variant.
2. **`_persist_audible_speech` routes instead of persisting** (`runner.py:1404`).
   For each event, call the subject's character agent with the Director's intent
   as the stimulus and persist that reply, keeping the event's already-clamped
   `witness_ids` as the audience. **Issue them in one `asyncio.gather`** —
   independent by construction, and without it the p90 turn pays two round trips.
3. **The degradation path**, for a subject who is absent, unresolvable or whose
   routing call fails: a Narrator record with the same audience that REPORTS the
   speech rather than quoting it. Counted and logged, never silent.
4. **The two deterministic guards, independent of all of the above:** no `C\d+`
   reaches a persisted record, and an event whose language does not match the
   session's pinned language does not persist.

### ✅ Item 4 DELIVERED — 2026-08-06

`src/runner.py::_leaks_internal_id` and `::_foreign_language`, both refusing
inside `_persist_audible_speech`. 17 tests
(`tests/test_audible_speech_deterministic_guards.py`, plus three end-to-end in
`tests/test_audible_speech_persistence.py`). Suite 1012 green, ruff clean. No
provider calls were needed, as predicted.

**The id guard checks membership, not shape.** `\bC\d+\b` only nominates
candidates; a hit counts only if it is a key of `game.characters`. Matching the
shape alone would refuse *"a carga de C4 na viga"* in a scenario where C4 is an
explosive rather than a student — a guard that deletes real dialogue to prevent a
leak that is not there fails this phase's own rule as surely as the leak does.

**The language guard's threshold was measured, not chosen.** Scored over **all
3,936** speech/narration/action records in the 16 archived sessions, using
function-word markers with the cross-language collisions removed from both lists
(`for` is an English preposition *and* the Portuguese subjunctive of *ser*; so are
`a`, `as`, `no`, `do`, `e`):

| | |
|---|---|
| most English-looking **Portuguese** record | **0.012** (one loanword in 263 words) |
| the **nine** English records | **1.000**, every one |
| records between 0.012 and 1.000 | **zero** |

The threshold sits at 0.5, in an empty band. The floor of two markers is set by
the shortest true positive (`drive-P1-r1` T10, *"Guard, report! What breached the
wall?"*); of the 415 records carrying fewer than two markers, none scores above
the line, so the floor costs nothing.

It is deliberately narrow — it answers *"is this English in a Portuguese
session"*, the only flip the corpus contains. Any other pinned language returns
`False` rather than guessing, because the marker lists cannot separate a pair
they were not built for. Extending it means measuring the new pair first.

#### The finding: **all nine** English records came through this channel

The task text said the language flip *"was filed against the prose renderer; it
belongs here"*. That is now measured rather than argued. Cross-checking every
English record against the task-68 matcher:

| | |
|---|---|
| English records in the archive | **9** |
| …Director-authored (score 0.899–1.000) | **9** |
| …written by a character agent | **0** |
| …in narration | **0** |

Four in `null-P1-r2` T2, three in `base-P2-r2` T19, one each in `oldcode-P2-r2`
T3 and `drive-P1-r1` T10. Not one character reply and not one narration record
ever flipped language, across 3,936 records. **The channel does not merely carry
most of the defect; it carries all of it.**

#### Two things changed that were not in the plan

- **Every refusal on this channel is now logged** (`log_audible_speech_drop`,
  reasons `echo` / `whisper_leak` / `internal_id` / `foreign_language`). The two
  pre-existing skips dropped lines silently, and a refusal here is a line the
  reader never sees — invisible content loss is exactly what the closure list
  below forbids for the degradation path, and there was no reason for the older
  guards to be exempt. It also gives item 3 its logging surface for free.
- **`tools/acceptance/drive_label_ab.py` was under-reporting.** Its `ID_RE` was
  `\bC\d\b`, which cannot match `C10`–`C21` — and the scenario it runs against
  has 21 characters, so it was checking a third of the cast. Widened to `\bC\d+\b`
  (same fix applied to `tests/test_internal_ids_in_prompts.py`, whose 3-character
  fixture made it correct today but fragile). `no_internal_ids_live.py` was
  already right: it builds its pattern from the scenario's actual ids.

**Both guards survive the rest of the task.** After routing lands they stop
guarding the Director's prose and start guarding the routed character's, which is
why they were worth building before the part that needs live validation.

### ✅ Items 1-3 IMPLEMENTED — 2026-08-06, with the mechanism CHANGED

**The written shape did not survive measurement either, for the second time in
this task.** It said *"for each event, call the subject's character agent and
persist that reply"*. Measured first: of the 639 Director-authored records,
**403 (63%) are for a character who already speaks that turn.** Routing those
separately gives the same character two records in one turn — the duplication
this task exists to remove, re-authored in a better voice. The owner chose the
alternative on 2026-08-06.

| population | n | mechanism |
|---|---|---|
| **A** subject silent this turn | **209 (33%)** | one call of their own, gathered |
| **B** intent restates their own line | **27 (4%)** | dropped as an echo |
| **C** subject already speaks this turn | **403 (63%)** | the intent becomes a **mandate inside the call they were already making** |

Case C costs **zero** extra calls and yields one record instead of two. Only
case A adds calls: **257 of 434 turns (59%) need none**, 149 need one, 24 need
two, 4 need three — and those issue in one `asyncio.gather`, so the archive's
worst turn is one round trip rather than three.

The plumbing was already there and pointed the wrong way: `render_events_for_viewer`
(`perception.py:121`) already shows a character the `audible_speech` event where
they are the subject. They read *"Nix shouts: 'the beam is pinning the fresta'"*
as **ambient perception**, treat it as something that already happened, answer
it — and the Director's sentence persisted beside their answer. So the fix for
case C is not new machinery; it is moving that line out of the perception stream
and into an obligation (`_speech_mandate_note`, `character.py`).

**Two corrections found by the tests, both worth keeping in writing:**

1. **Routing would have voiced the player.** The first version routed any
   non-queued subject, and `tests/test_perception.py` caught it immediately: the
   runner would have generated the human's own dialogue. The controlled
   character can be neither mandated nor routed.
2. **But refusing them outright breaks WT-09**, which the original persistence
   test caught in turn. WT-09's founding case *is* the player's character — a
   cipher read aloud whose content exists **only** in the Director's event, never
   in what the human typed. So a controlled-character intent takes the
   degradation path: the Narrator reports it, every witness can still recall it,
   and no record claims the human said words they did not write. The other half
   of that defect — the Director paraphrasing what the player actually submitted
   (`base-P2-r1` T2) — never reaches there, because `_echoes_recent_speech`
   already counts the `Player` sentinel as the same voice.

**Refusals are now six, all logged** (`log_audible_speech_drop`): `echo`,
`whisper_leak`, `internal_id`, `foreign_language`, plus the two outcomes
`voiced_by_owner` (the mandate worked) and `mandate_ignored` / `routing_failed` /
`player_voice` (the degradation path fired). That log **is** the calibration
instrument for the next section.

### ⚠ What is NOT validated, and must be before the checkpoint

- **The Director prompt change is unvalidated live.** `AGENTS.md` §6 says the
  validated variant is the shipped variant and its position is part of the
  variant. The DIALOGUE OWNERSHIP rule had to change — it told the Director to
  *"never invent new dialogue… record only words already spoken in HISTORY"*,
  which the new engine contradicts, so leaving it was not an option. But the
  replacement has not faced a live Director. **Run the replay before the
  checkpoint.**
- **`_INTENT_CARRIED_RATIO` (0.5) is the one threshold in this task that could
  not be measured first.** It judges compliance with a prompt that did not exist
  until today, so the archive contains no positives for it. Everything else here
  was sized against 3,936 archived records; this was not, and saying so is
  cheaper than pretending otherwise. Calibrate it at the checkpoint from
  `mandate_ignored` counts in `debug.jsonl`.
- **The falsifier for the whole case-C mechanism:** if `mandate_ignored` fires on
  a large share of case C, the mandate is a prompt promise that loses — exactly
  what this task says about prompt promises — and case C should fall back to
  case A's dedicated call, at the cost the owner already accepted.

## Closure evidence required

- [ ] no persisted record claims a character said words the character did not
      author — the scanner from task 68 at zero
      (`director_speech.director_authored`, **458** in P1 today), **and** the
      scanner extended to count the degradation-path records, so the invariant
      cannot be satisfied by reclassifying speech as narration;
- [x] the routing calls are gathered, not serial — asserted on a turn with more
      than one `audible_speech` event (the archive's worst turn has four)
      *(2026-08-06; asserted by overlap, not by timing — each stub call parks
      until every call has started, which serial execution can never satisfy)*;
- [x] the degradation path is counted and logged every time it fires, with the
      reason *(2026-08-06)*;
- [x] WT-09 preserved: a test where a witness who did not reply can still recall
      a fact voiced to the room on a later turn *(2026-08-06 — the original
      WT-09 test still passes, now through the degradation path)*;
- [x] `oldcode-P1-r1` T39's id leak cannot recur — a test asserting no `C\d+`
      reaches a persisted record *(2026-08-06)*;
- [x] a test that the player's own submitted line is never re-voiced back
      *(2026-08-06 — and the neighbouring case, a reveal caused BY the player
      that they never typed, still reaches every witness)*;
- [x] the language-flip case: a Director event in the wrong language cannot
      become a persisted record *(2026-08-06)*;
- [ ] a blind read of the post-65a cell against the archived pre-65a transcripts,
      same protocol, judging whether the fiction thinned;
- [ ] 65b written up as its own decision with the three options costed, whichever
      is chosen.

**The measurement that would falsify this task:** if the blind read says the
post-65a sessions read thinner — fewer voices, flatter rooms — the duplication was
carrying narrative load and the reference-only direction is wrong. `NSR` is
reported alongside but decides nothing (see the correction above).
