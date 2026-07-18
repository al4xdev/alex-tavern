# Task 38 — Roteiro with Typed Beat Contracts and Algorithmic Replanning

**Depends on:** Task 36 (a Director box must exist to consume the roteiro).
Task 37 benefits but is not a hard dependency.

## Goal

Give the story a DIRECTION compiled before the first word (the user's
map-reduce insight applied to narrative): a hierarchical roteiro — stable
premise + act skeleton, rolling next-beat detail — consumed by the Director
and replanned by CODE, never by model self-assessment.

## Beat contract (design frozen in exploration, 2026-07-16)

```json
{
  "beat_id": "act1-beat3",
  "intent": "Van Helsing pressiona a delegacao a abrir o corredor solar",
  "expected_actors": ["C6", "C8"],
  "expected_anchors": ["corredor solar", "venezianas"],
  "exit_condition": "a delegacao decide sobre as venezianas",
  "budget_turns": 6
}
```

## Replan signals (in preference order; hysteresis + cooldown everywhere)

1. exit condition met → advance beat (normal);
2. turn budget exhausted without anchor coverage → stalled, replan rolling beat;
3. actor/anchor/location overlap below threshold for M consecutive turns →
   drifted, replan rolling beat (fuzzy similarity as fallback signal — measured
   0.79 vs 0.23 discrimination on real pairs);
4. act-level exit broken hard → regenerate act skeleton.

Only the rolling beat is rewritten routinely; premise and act skeleton stay
stable (cache-friendly prefix, spoilers contained).

## Confidentiality rule

The roteiro reaches ONLY Director-side calls. Never a character prompt, never
the prose renderer (it contains future secrets). Assertable from debug.jsonl.

## Acceptance Criteria (headline)

- [ ] Roteiro generator produces valid typed beats from a scenario config.
- [ ] Deterministic replan triggers with unit-tested hysteresis; zero
  model-self-assessment triggers.
- [ ] Roteiro text never appears in character/prose requests (debug scan).
- [ ] Real-run A/B: same scenario with and without roteiro; blind critic
  compares narrative drive without knowing which is which.

## CLOSED 2026-07-17 (Opus session)

All headline acceptance criteria delivered and measured, plus two criteria the
user added mid-task (lexical variation; goal-per-NPC-per-scene):

- [x] Roteiro generator produces valid typed beats from a scenario config
  (premise + 3-act skeleton + rolling beat), schema v7, Director-only.
- [x] Deterministic replan with unit-tested hysteresis; ZERO model-self-
  assessment triggers. Every A/B run logged advance/coverage_complete/
  coverage_sufficient/in_progress/stalled/drifted/cooldown decisions, all from
  code signals (`roteiro_replan` debug records).
- [x] Roteiro text never in character/prose requests: confidentiality scan
  returned NONE in every A/B run (the block exists only in the Director prompt;
  character/prose builders have no roteiro parameter at all).
- [x] Real-run A/B with blind comparative critic (deepseek, shuffled A/B,
  critic blind to which arm is which), the roteiro arm must win narrative drive.

### The measurement journey (honest, n>1, fixes between rounds)

Provider note: the local llama.cpp endpoint was down; switched to the deepseek
API (user-approved) for all real runs.

1. **Round 1** (pre-fix): roteiro LOST drive (B- vs the control's... actually
   control won). Debug showed beat B3 PINNED the scene for 5 turns on one
   unmatchable anchor: coverage kept it "engaged" so drift never fired and it
   ground to a budget-stall while the Director re-staged the same stimulus and
   re-injected the same lore. Fix: **partial-coverage advance**
   (`coverage_sufficient`) - a beat with actors covered and <=1 anchor missing
   advances after a short patience window instead of dwelling.
2. **Round 2** (partial-coverage): roteiro WON drive decisively (B- vs D+); the
   pin was gone (7 beats completed, no grind).
3. User raised the bar: add **lexical variation** and **goal-per-NPC-per-scene**
   as criteria, 3 loops allowed, prompt changes expected. Direct deepseek recon
   first (per user): baseline "don't repeat a sentence" left prose echo ~0.49;
   a mandatory lexical rule ~halved it. Baseline NPCs made disconnected ambient
   remarks; an explicit "pursue a goal this turn" rule shifted them to targeted
   pursuit. Applied both + tightened the prose guard + a deterministic
   sentence-strip backstop; added a deterministic lexical metric to the harness.
4. **Loop 1**: goal-per-NPC PASSED (roteiro both NPCs pursue; control's decay),
   drive PASSED, but lexical FAILED in the roteiro arm (verbatim door sentence
   T9==T10, max_echo 1.0) because a single retry could not beat a persistent-
   state event re-narrated identically. Fix: **deterministic sentence-strip
   backstop** - strip any sentence still echoing prior narration after the
   retry (guarantee by construction).
5. **Loop 2**: lexical PASSED live (0.74/0, backstop held), goal-per-NPC PASSED
   decisively AGAIN - but drive LOST: the roteiro generated a TALKY map-lore arc
   and stalled in Act 1, NPCs "interrogating a silent chair" about backstory the
   passive player never raised. Root cause: the architect prompt never asked for
   escalation or forbade exposition. Fix: **_ARCHITECT_RULES now mandates
   escalation** (each beat a new external physical pressure; tension rises act to
   act) **and bans exposition** (no backstory/lore beats; reveal the past only
   through present physical events; anchors must physically enter the scene).
   Generation recon over 3 fresh roteiros confirmed the shift to physical arcs.
6. **Loop 3** (final): roteiro WINS BOTH AXES decisively - drive B vs D+
   (rising arc: door blown in -> pursuers -> fire -> death -> escape gambit vs
   the control's 7-turn "imoveis" door-loop), goal-per-NPC both NPCs pursue and
   act. Lexical clean (0.67/0). Confidentiality NONE. Triggers deterministic.

Final scorecard (roteiro arm): narrative drive PASS, goal-per-NPC PASS (all 3
loops), lexical variation PASS (metric <0.8, 0 near-dups; guaranteed by the
backstop), confidentiality PASS, deterministic-replan PASS.

### Residuals routed (not criterion failures; Task 26)
- Cross-turn event/action duplication (a beat active across turns re-stages the
  same action) -> candidate: generalize the burst's `repeats_event_text` dedup
  to regular turns.
- Repeated imagery below the verbatim bar (knife + dying-fireplace glow) ->
  epithet-recycling family; context-narrowing candidate.
- Object-state continuity (a medallion narrated thrown and on-the-floor at once)
  -> general engine limitation; future object-state-ledger task, not Task 26.

Suite: 547 passed. Artifacts + all three critic transcripts:
`plans/artifacts/roteiro-ab/` (critic-round{1,2}, critic-loop{1,2,3}).
Commits (Agent: claude-opus): 9761f31 impl, 35a9a2f/3f4c014 measurement fix,
bdda81f partial-coverage, 9f073e0 lexical+goal criteria, 06bb963 lexical
backstop, cedbb1a architect escalation.
