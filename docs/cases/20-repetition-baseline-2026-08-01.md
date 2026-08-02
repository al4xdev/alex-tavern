# 20 — Repetition: the ruler, and the "before" it reads

Recorded 2026-08-01, before any cut. Every number here comes from
`tools/acceptance/repetition_metrics.py` over the two evidence sessions already
on disk. No tokens were spent producing it.

Context: `602e562` ("clamp expected_actors to 4, single-noun anchors") was
shipped as a fix for the Narrator re-narrating the same scene, then reverted in
`2eabc81`. Its confirmation compared one session before and one after, using
`roteiro_ab.lexical_metrics` — a metric that `prose._strip_echoed_sentences`
already drives to the floor by deleting the offending sentences. The session
cited as proof of the fix fails in its own log. This file exists so the next
claim has a ruler that was fixed in advance.

## Why the old metric could not have worked

`max_echo` / `near_dups` measure narration sentence echo. `prose.py:165` deletes
exactly those sentences before the record is written, so the metric measures an
invariant rather than the defect. Two sessions, two disjoint failure modes:

| session | prose repetition guard fired | mode |
|---|---|---|
| `20d4cdb3` | 5 of 10 prose turns | lexical |
| `15d40dfa` | 0 of 6 prose turns | purely semantic |

Any single primary metric masks one of them.

## Baseline

τ = 0.8 unless stated. `RSR_prop` = share of Director-proposed perception events
that restate something already in play (prior proposals + prior speech/action),
compared on the frame-stripped, accent-folded payload.

| metric | `20d4cdb3` | `15d40dfa` | reads |
|---|---|---|---|
| turns / player actions | 11 / 2 | 6 / 2 | both sessions are almost entirely autonomous burst |
| **`RSR_prop`** | **41.0%** (16/39) | **31.2%** (5/16) | the Director *proposes* a repeat about a third of the time |
| `RSR_prop` @ τ=0.7 / 0.9 | 46.2% / 33.3% | 31.2% / 31.2% | not an artefact of the threshold |
| `NSR` (novel stimuli/turn) | 2.09 | 1.83 | throughput interlock |
| `SIL` (silent turns) | 9.1% | 0.0% | silence interlock |
| `GUARD` | 50.0% | 0.0% | the two modes |
| **`ECHO_PERSIST`** | **7** | **2** | verbatim lines persisted twice |
| **`BOCC`** (max turns/beat) | **5** | **5** | `HARD_BEAT_TURN_CAP` is 3 |
| `RPA` / `CPA` | 1.0 / 52.5 | 0.5 / 14.0 | cost reference |
| beat exits | `stalled`×1, `act_deadline`×1 | `act_deadline`×1 | see below |

### The beat clock never fired as designed

`20d4cdb3`: beat runs `B1.1`=3 turns, `B1.2`=**5**, `B2.1`=3.
`15d40dfa`: `A1B1`=**5**, `A2B1`=1.

Across 17 turns there were **two** beat exits. One was `act_deadline` (the act
clock, not the beat cap) in each session; the single `stalled` in `20d4cdb3`
fired only because `beat_actions_elapsed` was 0 and the
`or len(turn_numbers)` fallback happened to read committed turns instead. The
intended path — `actions_elapsed >= min(budget, HARD_BEAT_TURN_CAP=3)` — never
fired once, because `beat_actions_elapsed` increments once per PLAYER ACTION
while a burst commits up to 6 turns per action.

### The speech echo guard is defeated twice over

`_echoes_recent_speech` (`runner.py:160`, τ=0.88, lookback 8 **records**) let all
9 verbatim duplicates through. Mechanism per pair, measured:

| pair | raw ratio | ≥0.88 | gap (records) | ≤8 | escaped via |
|---|---|---|---|---|---|
| `20d4cdb3` T1→T2 C3 | 0.8377 | no | 12 | no | both |
| `20d4cdb3` T1→T2 C5 | 0.8421 | no | 11 | no | both |
| `20d4cdb3` T1→T2 C13 | 0.8581 | no | 10 | no | both |
| `20d4cdb3` T4→T5 C5 | 0.8410 | no | 11 | no | both |
| `20d4cdb3` T7→T9 C17 | 0.8978 | **yes** | 19 | no | lookback |
| `20d4cdb3` T7→T9 C5 | 0.9091 | **yes** | 18 | no | lookback |
| `20d4cdb3` T8→T9 C3 | 0.9521 | **yes** | 12 | no | lookback |
| `15d40dfa` T1→T1 C17 | 0.8207 | no | — | yes | threshold (frame) |
| `15d40dfa` T3→T4 C19 | 0.8327 | no | — | yes | threshold (frame) |

Every pair scores **1.0000** once the attribution frame
(`"<name> anuncia: '<line>'"`) is stripped. Two independent holes:

1. **Lookback.** 8 records is ~1 turn at a 21-character cast. Every single
   duplicate in `20d4cdb3` escaped it, including three the threshold would have
   caught on its own. The window must be counted in turns, not records.
2. **Frame.** The wrapper drops similarity by ~0.16, straight under 0.88. The
   comparison must run on the quoted payload.

These persist as new `speech` records attributed to the character, so they
re-enter `RECENT EVENTS` and are fed back to the Director every subsequent turn.
Self-reinforcing.

## Pre-registered acceptance for the deterministic cuts

Measured on fresh sessions after the cuts, same scenario and profile:

- `ECHO_PERSIST` = 0
- `BOCC` ≤ the beat turn ceiling
- no beat exiting by `act_deadline` without first having had a chance to exit by
  stall
- `SIL` no higher than baseline, `NSR` no more than 10% relative below baseline
  — a cut that buys quiet instead of movement is a failure, not a fix

## The two deterministic cuts

Both are code, not prompts, and both were verified against the old engine before
being kept — a test that passes on both sides proves nothing.

### Cut A — the speech echo guard sees payloads, over turns

`_echoes_recent_speech` now compares `perception.comparable_text` (attribution
frame stripped, accent- and case-folded) and windows by
`_SPEECH_ECHO_LOOKBACK_TURNS = 4` instead of 8 records.

Regression tests in `tests/test_audible_speech_echo.py` use the measured strings
verbatim. Against the old guard, 3 of the 4 new tests fail; the fourth is a
negative case that must pass on both sides, because a frame-blind comparison
could just as easily collapse two genuinely different quoted lines.

### Cut B — two clocks in `src/roteiro.py`

* `HARD_BEAT_ACTION_CAP` (3) keeps the declared budget in player actions, which
  is the Task 45 calibration.
* `HARD_BEAT_TURN_CAP` (3) is new and counts narrated turns. A burst cannot
  outrun it.
* The `or len(turn_numbers)` fallback is gone, so the action clock is monotonic.
* `DRIFT_WINDOW_TURNS` and `PARTIAL_ADVANCE_PATIENCE` moved onto the turn clock
  as well. Both measure the scene DWELLING and both were being compared against
  an action counter — a unit mismatch that only ever worked because the fallback
  made that counter read turns. Notably, the two tests covering them passed
  unchanged after the move, which is what you would expect if turns were always
  the unit they were written against.

The unit rule now stated in the module: **dwelling is counted in narrated turns,
budget is counted in player actions.**

## The manipulation check

`tests/test_beat_clock.py` drives real bursts through the Runner with only the
architect model stubbed — `replan_roteiro` runs for real, so the cooldown, the
counter reset and `beat_started_turn` are production transitions, and every
replan mints a DISTINCT beat (the sibling harness in `test_roteiro.py` returns
one shared roteiro object, which would make any assertion about beat identity
vacuous).

Counterfactual, old logic with only the new constant name aliased in:

| | old | new |
|---|---|---|
| 1 skip, 6 beats | one beat held all **6** turns | max **3** turns per beat |
| 2 skips, 12 turns | one beat held all **12** turns, zero replans | max **3** turns per beat |

Twelve consecutive narrated turns under a single beat contract, never replanned
— worse than the live sessions only because here no act deadline ever intervened
to hide it.

Two of the six tests are invariant guards rather than reproductions, and say so
in their docstrings: monotonicity holds on the old code under this fixture
(no replan fires, so no counter is ever reset to 0), and the hysteresis check
exists to keep cooldown and ceiling in the same unit.

One fixture note worth keeping: the first draft used templated event texts
(`"Algo distinto acontece no turno N"`), which the burst's own dedup filter
correctly dropped as near-identical, so every turn after the first went silent
and the test measured that filter instead of the clock. The fixture now uses
genuinely unrelated stimuli.

## Re-baseline after the cuts

Live, 21-character `turma-dos-portais-pt-full`, language pinned to the
baseline's Brazilian Portuguese, `auto_event` / `alignment` / `automatic
compaction` all off, cell order randomized within replicate blocks.

Planned 6 runs (2 cells x 3 replicates). **4 completed, 1 truncated at 10 turns,
1 never ran**: the DeepSeek account hit `402 Payment Required` mid-battery
(balance `-0.02 USD`, granted balance `0.00`). What follows is 4 complete
sessions and ~160 turns, not the pre-registered n.

| cell | run | turns | RSR_prop | ECHO | BOCC | SIL | GUARD | NSR | RPA | ACTR |
|---|---|---|---|---|---|---|---|---|---|---|
| base | r1 | 38 | 13.7% | 0 | 3 | 0.0% | 15.8% | 3.47 | 1.80 | 0 |
| base | r2 | 34 | 3.5% | 0 | 3 | 0.0% | 14.7% | 4.09 | 1.30 | 0 |
| null | r1 | 39 | 8.8% | 0 | 0 | 0.0% | 28.2% | 2.92 | 0.00 | 0 |
| null | r2 | 39 | 9.0% | 0 | 0 | 0.0% | 48.7% | 2.59 | 0.00 | 0 |
| null | r3* | 10 | 10.5% | 0 | 0 | 0.0% | 18.2% | 3.40 | 0.00 | 0 |

\* truncated by the billing failure; shown for completeness, excluded from means.

### Acceptance criteria — met

| criterion | baseline | after | verdict |
|---|---|---|---|
| `ECHO_PERSIST` = 0 | 7 and 2 in 17 turns | **0 in every run**, ~160 turns | met |
| `BOCC` <= ceiling | 5 and 5 | **3 and 3**, exactly the ceiling | met |
| `SIL` not up | 9.1% / 0.0% | **0.0%** everywhere | met |
| `NSR` not down | 2.09 / 1.83 | **3.78** mean (base) | met, improved |
| `ACTR` no thrash | 0 (unreachable) | **0** | met |

The act-rewrite worry did not materialize: a live turn ceiling makes
`ACT_REPLAN_THRESHOLD` reachable in principle, but at 1.3-1.8 replans per action
the act deadline resets the counter before it escalates.

### What the null arm forces us to admit

`RSR_prop`: base 8.6% mean, **null 9.4% mean**. A tie.

The pre-registered halt rule (null <= 0.5x base, meaning the roteiro is itself
the cause) does **not** fire — good. But the tie says something else that must
be stated plainly: **the fall in `RSR_prop` from 31-41% to ~9% cannot be
attributed to the beat clock.** The roteiro-off arm has no beats at all and
scores the same. Whatever drove that number down is Cut A and/or the change of
input profile, not Cut B.

What Cut B demonstrably bought is `BOCC` 5 -> 3, and beat pinning is precisely
the "five turns of the same tableau" the complaint was about. What Cut A
demonstrably bought is `ECHO_PERSIST` 9 -> 0. Those two are mechanically
attributable — each has a unit test that fails on the old engine. `RSR_prop` is
an observation, not an attribution.

Two further honesty notes:

* This is **not** a controlled before/after. The baseline sessions had 2 player
  actions over 6-11 turns; these have 10 inputs over 34-39. Only the cuts were
  meant to differ, and more did.
* That difference biases *against* the result rather than for it: a longer
  session gives every stimulus a larger pool of priors to match, so recurrence
  can only rise with length. These runs are 3-6x longer and score 3-4x lower.

`GUARD` favours roteiro-on (15.2% vs 31.7%) and so does `NSR` (3.78 vs 2.97),
but with n=2 vs n=3 and a null spread of 18-49% neither is worth a claim.

### The defect is only half fixed, and RSR hid the other half

Reading a transcript by eye found what the numbers did not. In `base-P1-r1` the
Director staged *"the emergency alarm sounds and the main doors seal with a
metallic thud, bolts locking"* at turns **11, 17, 21, 27, 29, 31 and 37**. The
doors seal seven times. That is not merely repetition, it is a physical
contradiction, and it is the original complaint.

`RSR_prop` scored that session at 13.7% and caught 4 of the 7. The restagings
sit at 0.53-0.89 pairwise — T21 missed the 0.8 threshold by 0.0016 — because a
pairwise test asks "is THIS event a repeat of some earlier one" and a scene
restaged with fresh wording slips under it every time. This is precisely the
failure the `MDR` semantic judge was specified to catch, and `MDR` never ran.

`cluster_max` / `cluster_span` were added in response. They answer the right
question — how many times did ONE situation come back, and over how long:

| session | RSR_prop | ECHO | BOCC | cluster | shape |
|---|---|---|---|---|---|
| before `20d4cdb3` | 41.0% | 7 | 5 | 3x over 3 turns | contiguous (pinning) |
| before `15d40dfa` | 31.2% | 2 | 5 | 4x over 4 turns | contiguous (pinning) |
| after base r1 | 13.7% | 0 | 3 | **7x over 27 turns** | intermittent |
| after base r2 | 3.5% | 0 | 3 | 3x over 3 turns | contiguous |
| after null r1 | 8.8% | 0 | 0 | 2x over 26 turns | intermittent |
| after null r2 | 9.0% | 0 | 0 | 5x over 6 turns | intermittent |

**The cuts changed the shape of the defect, not its existence.** Contiguous
pinning is bounded — nothing exceeds the 3-turn ceiling. Intermittent
recurrence of one physical event across a whole scene is untouched, because
nothing in the engine remembers what the Director already staged: perception
events are not persisted, `burst.event_texts` dies with each submission, and
`_strip_echoed_sentences` deletes the only prose trace. That is knot N3/N4, and
it is exactly the MEMORY factor Phase 2 was built to test.

Cluster counts do not separate `base` from `null` (7/3 vs 2/5/2) at this n. No
claim either way.

A note on the metric itself: the first implementation used single linkage and
reported a 22-stimulus cluster in `null-P1-r2` whose first and last members sit
at 0.249 similarity. It had chained through a recurring *format* ("the Diretora
announces that...") carrying genuinely new content each time. A recurring format
is not a recurring event. It now uses leader clustering — every member must
resemble the cluster's first member, never merely a neighbour.

### Blocked

The Phase 2 factor battery (MEMORY, PROMPT, `ceiling`, profiles P2/P3, the
mixed-effects model and the blind reader judge) needs provider credit. Nothing
about it is written yet beyond the cell scaffolding in
`tools/acceptance/repetition_battery.py`.

---

# Round 2 — the cause was in the INPUT, and eleven metrics could not see it

## The correction that matters

Round 1 concluded "the Director has no memory of what it staged." **That was
wrong, and it was wrong because of a query bug of mine.** The probe read
`scene_update["physical_facts"]` — a nested key that does not exist, because
facts are flat keys. Corrected, the Director wrote physical facts on **37 of 38
turns**; `main_doors: "trancadas"` entered at turn 11 and sat in its prompt for
every turn after. It re-sealed the doors seven times anyway. The state channel
had already run the experiment round 1 was about to propose, and it failed.

## The actual cause: a code loop, ordering the repeat

Every metric in this document scores what the model **produced**. The defect was
in what the code **ordered**.

- `roteiro_replan` logged `act_deadline:clock` **17 times in 38 turns**.
- `act_index=2`, `len(acts)=3`, `duration_ticks=[3,3,2]` — the terminal act.
- `runner.py` guarded the index advance but still reset `act_started_tick` and
  returned `world_event`, so the last act re-fired its climax every 2 ticks,
  forever.
- The byte-identical text was injected as `UPCOMING EVENT` on turns 11, 13, 17,
  19, 21, 23, 25, 27, 29, 31, 33, 37 — **twelve orders**.
- `narrator.py` calls that block MANDATORY: *"it does not wait for a better
  moment, and no coherence concern overrides it"*, with a correction retry.

The doors-sealing cluster is a **subset** of the injection turns. The Director
obeyed 7 of 12 orders while the same prompt also told it *"never restage what
already happened"*. The mandatory instruction won, correctly — it has code and a
retry behind it.

## New instruments (offline, free)

| metric | what it answers | base-r1 baseline |
|---|---|---|
| `INJ_REPEAT` | how often the CODE re-issued one order | **12x**, `act_deadline` 17 |
| `REVERT` | fact values returning to a value already held — physical contradiction made countable | **9** (`alarm`: soando → silencioso → soando → …) |
| `FACT_HEALTH` | the unbounded state channel | 54 keys / 3169 chars, 10 synonym pairs, 18 transient |
| `BEAT_LIFE` | churn from the two beat clocks | mean 2.0 turns |

`REVERT` fires only on `base-r1` across all five artifact sessions, so it
discriminates the loop rather than tracking noise. This is also the coherence
instrument round 1 lacked — and it costs nothing.

## Fixes, each proven against the old engine

**R0 — the terminal act regenerates.** A story that runs out of acts gets new
ones, via the existing `replan_roteiro(scope="act")`, which keeps the premise and
splices after the acts already played. A generation that returns no usable act
**stops the clock** rather than re-firing — otherwise one bad response trades a
repeated event for a repeated expensive call. Counterfactual: old code injected
the same world_event `3x` in a 7-turn fixture, new code `1x`.

*A fixture bug found on the way:* the pre-existing `fake_replan` clobbered
`act_started_tick` on every replan, so ordinary beat replans silently reset the
act deadline and the loop could not reproduce at all. The fake now mirrors
`replan_roteiro`, which only restarts the act clock when the act changed.

**R2 — control signals are exempt from the event contract.** `CLOCK_SKIP_INVITE`
is an instruction to the Director, not something a character can perceive, yet it
went down the `UPCOMING EVENT` channel and failed materialization on **6 of 6**
skip turns in every run (an English constant in a Portuguese scene, so no content
word can match). Cost: **~170k tokens per session, about 13%**, on a retry that
could not succeed — and the correction asked for the instruction text itself to
become the first perception event. Measured: the Director refused all 6 times, so
**nothing leaked**; this was waste plus prompt noise, not a quality defect.

**Block 3 — the laundering channel.** `confidentiality.known_tokens` and
`hidden_thought_tokens` subtract every token in `physical_facts` from the whisper
and thought secret sets, for every viewer. `perception_events` are redacted;
`scene_update` **was not** — and it is the one output with no per-viewer
projection. One whispered detail written into a fact silences the guard for
everyone, permanently, because facts are never pruned. Now redacted against a
union set covering every present viewer. Counterfactual: old code produced
`{'seal_name': 'o selo responde a vharkhalos'}` from a whisper C1 never heard.

**Block 3 — coerce, never reject.** `scene_update` demanded string-or-null and a
single boolean made the local validator discard the **entire** decision — events,
moods, zone moves — then resample with identical messages and no correction.
**5 of the 8 Director validation failures across the battery runs were exactly
this.** Values are now coerced.

**Block 3 — fact hygiene.** Cap at 24 with least-recently-written eviction,
per-character transient keys refused (`_action`/`_position`/`_stance`/…), and
near-synonym keys refused. Synonym detection compares the key's **sorted word
set**: raw, `crack_in_ceiling` vs `ceiling_crack` scores 0.48 because a
character-level ratio cannot see reordering; canonicalized it is 0.90, while
unrelated pairs move further apart (`main_doors` vs `crack_in_ceiling`: 0.31 →
0.15). The review that proposed this quoted 0.78-0.86 for that pair; measured, it
was 0.48, which is why the canonical form was needed.

## Deferred on purpose

A producer-agnostic hint-idempotence guard (R1) was planned. After R0, the only
remaining candidate repeat producer is the drive — which was pinned **off** in
every measurement taken so far. Building it now would cost a session-schema bump
to fix a hypothesis, so it is gated on the `drive` cell of the next battery.

---

# Round 2 results — controlled, and the model moved under us

## The confound that nearly ruined this

DeepSeek updated `deepseek-v4-flash` **in place on 2026-07-31**. The reference
sessions are from 07-28; everything run since is a different set of weights under
**the same model id in the log**. So "before the fixes" and "after the fixes" also
differed by a model upgrade, invisibly.

The fix is a control cell: `oldcode` runs the **pre-fix engine on today's model**
from a git worktree pinned at `2eabc81` (nothing had been committed, so `HEAD`
*is* the pre-fix engine) carrying today's tooling. Verified genuine by reading the
schema DeepSeek serializes into the system prompt — `oldcode` sends
`additionalProperties: {"type":["string","null"]}`, the current engine sends
`true`.

Now each subtraction answers one question: `base − oldcode` is the code,
`oldcode −` the 07-28 sessions is the model.

## 12 runs, 4 cells x 3 replicates, blocked and randomized. $2.52 total ($0.21/run)

Medians. 21-character cast, P1, language pinned, `alignment`/`compaction` off.

| cell | repeated world event | RSR_prop | ECHO | BOCC | cluster | NSR | SIL | GUARD | REVERT | CPA |
|---|---|---|---|---|---|---|---|---|---|---|
| `oldcode` | **4x** | 9.9% | 4 | 6 | 4x/5t | 3.92 | 0.0% | 30.8% | 0 | 38.9 |
| `base` | **1x** | **1.7%** | **0** | **3** | 3x/5t | 3.77 | 0.0% | 15.4% | 0 | 38.4 |
| `drive` | **1x** | 5.2% | 0 | 3 | 3x/5t | 3.79 | 0.0% | 13.2% | 0 | 37.0 |
| `null` | 0 | 9.4% | 0 | 0 | 4x/8t | 2.87 | 0.0% | 32.5% | 0 | 32.0 |

Per run, most-repeated world event: `oldcode` [4, 4, 4], `base` [1, 1, 1],
`drive` [1, 1, 1]. No overlap, no variance.

## Verdicts against the pre-registered rules

**Rule 1 — R0 accepted.** Repeated world-event injections: 1 in **6 of 6** fixed
runs, 4 in **3 of 3** old-engine runs. Deterministic separation, no statistics
required.

**Rule 2 — Class A confirmed dominant.** `base` `cluster_max` (3) fell *below*
the pre-fix `null` band. Interlocks held: `NSR` 3.92 → 3.77 (−3.8%, inside the
10% allowance), `SIL` 0% throughout, `CPA` flat (38.9 → 38.4). The repetition was
not bought with silence or with tokens.

**Rule 3 — the MEMORY factor is CANCELLED.** Authorization required residual
`cluster_max ≥ 4` *and* `cluster_span ≥ 10` in both `base` and `null`. Measured:
`base` 3x/5t, `null` 4x/8t. Both below the gate. Building a durable staged-event
memory now would be chasing noise, by the rule written before the data existed.

**R1 is CANCELLED by the `drive` cell.** The gate was whether the drive repeats
its own seeds once un-pinned. It does not: [1, 1, 1]. The producer-agnostic
idempotence guard — and the session-schema bump it needed — is not built, because
the hypothesis it existed for is false.

**Rule 5 could not be evaluated**: `MDR` was never run. The interlocks that were
measurable (`NSR`, `SIL`, `GUARD`) all moved the right way, and `GUARD` halving
(30.8% → 15.4%) is evidence *against* an inert-world explanation.

## Code effect vs model effect, finally separable

Same model, same day, same profile — so this column is the code alone:

| | `oldcode` | `base` |
|---|---|---|
| repeated world event | 4x | **1x** |
| `RSR_prop` | 9.9% | **1.7%** |
| `ECHO_PERSIST` | 4 | **0** |
| `BOCC` | 6 | **3** |
| `GUARD` | 30.8% | **15.4%** |

And the model: the 07-28 sessions (old model, old code) scored `RSR_prop` 31-41%;
`oldcode` on today's model scores 9.9%. **The upgrade accounts for most of the
`RSR_prop` collapse I attributed to the fixes in round 1.** That correction stands
in the record — the round-1 number was confounded, and only the control cell
makes the remainder attributable.

## A metric bug, caught before it was reported

The first pass read `max_hint_repeats = 6` for `base` and would have said R0
failed. It had not: the metric counted `CLOCK_SKIP_INVITE`, a control instruction
that legitimately recurs once per skip turn, and a 6x-repeated instruction was
hiding a 4x-repeated **event**. `INJ_REPEAT` now separates the two — only a
repeated event is a defect.

## Open risk, measured and not fixed

Relaxing the `scene_update` schema to `additionalProperties: true` raised the
Director's fact-writing rate sharply: distinct keys written over a session went
from 37 (`oldcode`) to 51-80 (`base`), and two of three `base` runs finished
pinned at the 40-key cap. Facts churn in both engines — `oldcode` loses 11-29
keys to the location wipe — and no harm is observable here (`REVERT` 0, repeated
event 1x, `cluster_max` 3). But a saturated cap means eviction runs continuously,
and evicting a load-bearing fact like `main_doors: trancadas` is exactly what
would re-enable re-staging. Worth watching; not worth churning on now.

## Reproducing

```bash
# offline metrics over any recorded session
uv run python -m tools.acceptance.repetition_metrics \
    --session 20d4cdb3 --session 15d40dfa --evidence

# the deterministic proofs
uv run pytest tests/test_audible_speech_echo.py tests/test_beat_clock.py \
              tests/test_roteiro.py tests/test_autonomous_burst.py -q

# live re-baseline, 21-character cast, language pinned to the baseline's
uv run python -m tools.acceptance.repetition_battery \
    --cell base --cell null --replicates 3
```
