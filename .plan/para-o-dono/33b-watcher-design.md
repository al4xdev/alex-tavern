# 33b — Watcher design for scene transition (for your approval/veto)

> ## ✅ RESOLUTION (2026-07-19, night — approved by you before sleeping)
>
> You agreed with **1, 2, 3, 5, 6** and with the **2 test suite decisions**
> (integrate watcher behind flag = YES; drive adopts causal contract = YES).
> **#4** was your doubt → resolved by **curl in real window**, not by
> hypothesis (pre-registered decision rule). Verdict: **#4 ACCEPTED as is
> (Director-only).** All 8 decisions closed. Evidence below and in
> `plans/artifacts/watcher-decision4/` (local, gitignored).
>
> **Experiment #4** (2 real windows: lottery `ccb521ab`, fire `e7760040`;
> deepseek-v4-flash; 4 runs/arm; blind judge):
>
> | Level | Metric | 4a (blind/shipped) | 4b (character sees diffuse pressure) |
> |---|---|---|---|
> | Character | initiative (0-2) | **1.88** | **2.00** |
> | Character | invents external event (collision risk) | 0/8 | 0/8 |
> | Character | meta/immersion break | 0/8 | 0/8 |
> | Character | leaks Director's event | — | **no (0)** |
>
> | EVENT Level | causal coherence (0-2, blind judge, average of 3) |
> |---|---|
> | causal (anchored in thread) | **1.83** (fire 2.0 / lottery 1.67) |
> | flat/arbitrary | **0.00** (both windows, all runs) |
>
> **Reading:** routing the watcher signal to the character (relaxing #4) yields
> ~0.12 of initiative on a ceiling that the base prompt already saturates (1.88) — noise. And the
> stall is NOT due to a lack of character initiative: in 4a they ALREADY take
> initiative (1.88) and even so the turn does not produce a material delta — what is missing is the
> **new external consequence**, which only the Director's concrete event delivers and
> which the character must not fabricate (this is the collision that #4 prevents). The value of the
> watcher lives entirely at the Director/event level — exactly where #4 puts it.
> Bonus: the event level shows the target — causal 1.83 vs flat **0.00** of
> coherence — which **reinforces Decision B of the test suite** (drive seeds adopt
> the causal contract: the flat is the "cause-less crystal").


Everything below has already been validated by curl exploration in real payloads
(2026-07-19, see task 33b). None of this touches the canonical turn without the
toggle; OFF by default.

## The three pieces

```text
committed turn
      │
      ▼
[1] MATERIAL DELTA AUDITOR (1 small call, ~400 tokens out)
    "Did this turn produce a material delta? Which category?"
    categories: decision_taken, information_revealed,
    position_or_access_changed, attempt_got_consequence,
    relationship_changed, threat_advanced,
    possibility_opened_or_closed, none
      │  (validated: detected semantic immobility in the
      │   stalled lottery turns that lexical anchoring doesn't see)
      ▼
[2] ESCALATION LADDER (deterministic, code — doc §6)
    turn counter without delta consumes the CLOCK from 40
    steps 1-4: light pressures already existing (drive,
    pressure hint, force_speaker, beat replan)
      │  only at the final step:
      ▼
[3] CAUSAL INTERVENTION (1 call, only when the ladder is exhausted)
    contract: source_thread (evidence cited per turn) →
    event_now → expected_delta → refractory_turns
    (validated 3/3: every intervention grew from an existing thread,
     zero "hooded figure out of nowhere")
      │
      ▼
    becomes narrator_hint (UPCOMING EVENT channel — the same as
    drive/33, disruption/38 and the clock deadline/40)
```

## Design decisions (my proposals — veto what you don't like)

1. **Auditor runs every turn** when the toggle is ON (cost: 1 small call/turn).
   Cheaper alternative: only when `narrative_tick - last_delta > 1`. I start with the
   run-every-turn version in the experimental phase (better data), and decide later with real cost numbers.
2. **The ladder is 100% code** — the LLM never decides "when to intervene", it only
   answers the two questions (was there a delta? what is the causal intervention?).
   Same doctrine as the clock: time/pressure does not belong to the LLM.
3. **Refractory period respected**: after intervention, `refractory_turns` (the model
   asked for 3 in 3/3 runs) without new intervention, counting by the tick from 40.
4. **Confidentiality**: threads/intervention only reach the Director (as a
   screenplay/schedule). The Character and prose never see them.
5. **Boundary with 40**: the act deadline triggers BY THE CLOCK (time);
   the watcher triggers BY STAGNATION (lack of delta). Two triggers, same delivery
   channel, never in the same turn (deadline takes precedence; watcher
   enters refractory period when the deadline queued an event).
6. **Log**: each audit and intervention is logged in debug JSONL
   (`watcher:delta`, `watcher:intervention`) for the harness to measure.

## What the A/B/C battery will measure (with you awake)

A = free (no watcher) / B = arbitrary disruption / C = causal watcher.
Metrics from doc §7: sustained material delta rate, open-vs-resolved threads,
need for re-intervention, causal coherence by blind critic. Registered prediction:
C wins in sustained drive + coherence.

## Estimated cost

Auditor: ~1 small call/turn (only with toggle ON). Intervention: rare (only
final step). Experimental phase: harness/replay first, integration to the
runner only after your acceptance of the design + battery.
