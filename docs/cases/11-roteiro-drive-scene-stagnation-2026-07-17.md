# Roteiro, drive and scene stagnation: empirical results of typed beat contracts

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 11 |
| **Date** | 2026-07-17 |
| **Provider** | DeepSeek V4 Flash, real runs, blind critic |
| **Task** | 38 (delivered with reservations) |
| **Status** | Evidence feeding the stagnation program (No. 12) |

## Abstract

The Task 38 report and the investigation it unlocked: why procedural roleplay scenes stagnate and repeat. Typed beat contracts banked engine gains, but the roteiro proved coin-flip on a procedural scene (portals 2W/2L); a concrete disruptive beat broke the stall 3/3 while an abstract instruction failed 0/3 - the position-and-concreteness result that seeded the clock (Task 40) and the watcher (Task 33b).

---

The Task 38 report (a roteiro with typed beat contracts) and the investigation it
unlocked into why roleplay scenes stagnate and repeat. Provider for every real
run: deepseek-v4-flash (the local endpoint went down; deepseek approved by the
user). Blind critic = a subagent with no implementation context, arms shuffled
(A/B), a verdict per axis.

---

### 1. What Task 38 delivered

A **hierarchical roteiro** compiled before the first line of dialogue: a premise +
a 3-act skeleton + one typed **rolling beat** (`intent`, `expected_actors`,
`expected_anchors`, `exit_condition`, `budget_turns`). Consumed **by the Director
only** (character/prose agents do not get the parameter — structural
confidentiality). The **replan is decided by CODE** (`evaluate_roteiro`): anchor/
actor coverage measured at the authoritative source (the Director's typed events +
speech/actions), with hysteresis (a cooldown, a turn ceiling, escalation into an
act rewrite). Zero triggers from the model's self-assessment — every decision
logged (`roteiro_replan`). The feature is **opt-in, OFF by default**
(`roteiro_enabled`). Schema v7.

---

### 2. The honest verdict (measured, not wished for)

| Scenario | Characters | Genre | Drive (roteiro vs control) |
|---|---|---|---|
| Inn | 3-4 | action/threat | the roteiro wins **reliably** (~5 wins across the loops) |
| Portals (academy) | 6 | procedural/ceremony | **coin-flip: 2 wins / 2 losses** |

**Portals, the four A/B runs:** loop1 (ceiling) win · loop2 (two fixes) loss
(stalled on the raffle) · disruption-fix decisive win · confirmation decisive
loss.

Conclusion: the roteiro **helps drive in tight action scenes** and is **unstable
in large/procedural ones**. The value of "direction" there is cancelled out by
(a) topic-pinning when the beat is procedural, (b) a pile-up of disconnected
disruptions when it is forced to disrupt, (c) high variance against a free
Director who sometimes finds a cleaner emergent conflict. **No single fix makes
this reliable** — it is architectural reality plus variance (a 6-character
ceremony is hard for a system of pre-planned beats running a fast model), not a
bug one more loop closes.

Criteria the user added midway:
- **Lexical variation**: guaranteed by construction (the narration backstop;
  metric < 0.8 and 0 near-dups across every run).
- **A goal per NPC per scene**: a **global** improvement to the character prompt,
  dependent on the arc's shape, **not** a guaranteed differentiator of the
  roteiro.

---

### 3. The stagnation investigation (the payoff that outlives the task)

The critic flagged repetition in nearly every run (characters restating the same
idea; the entire cast praying for "good partners" on the raffle turn). The user's
question: *deepseek receives the speech history — why does it repeat so much? have
you tried through the prompt?* We investigated with the **curl-replay** technique:
take the REAL payload of the faulty call (from `debug.jsonl`) and iterate only the
prompt until the isolated call is fixed, before running any battery.

#### Intervention table (the real call from the stalled turn, N runs each)

| Intervention | Target | Broke the loop? |
|---|---|---|
| Anti-loop in the **character** prompt (up to an explicit ban on the topic) | character | ❌ 0/3 |
| An abstract authority/anti-stagnation rule in the **Director** | Director | ❌ 0/3 |
| **Removing** the roteiro block from the Director's prompt | Director | ❌ 0/3 |
| Injecting a **new scene event** into the context | context | ✅ 2/3 |
| A **concrete disruptive beat** in the roteiro → Director | Director | ✅ **3/3** |

#### What that proves

1. **It is not a character problem.** No rule in the character prompt — not even a
   direct ban on the topic — breaks the loop. The fast model follows the
   established scene (a saturated history) hard.
2. **It is not (only) the roteiro.** Removing the roteiro block did not help: the
   accumulated history alone already pins the topic.
3. **The lever is a new concrete event.** Injecting an event broke it 2/3; a
   **concrete disruptive beat** handed to the Director broke it 3/3 (it staged the
   crash at the gates + the hooded figure, dropping the raffle).
4. **The Director has the authority** to break the scene — but only exercises it
   given a **concrete "this happens NOW"** instruction. An abstract instruction
   loses to the pull of the history; a concrete event wins.

#### The fix that came out of it

`evaluate_roteiro` → when a beat **stagnates**, the replan generates a **concrete
disruptive beat** that changes the subject (an arrival/interruption/breakage
happening this turn), never a continuation of the stuck topic. Validated 3/3 in
the replan generator and 3/3 in the Director. It closed the drive gap on one
portals run (a decisive win) — but the next run showed the new failure mode (a
disconnected pile-up), keeping portals at a coin-flip.

---

### 4. Banked engine gains (they hold for both arms)

These do not depend on the roteiro being on — they improve the whole kernel:

- **A hard per-beat turn ceiling** (`6d6e9b8`): no beat pins the scene into static
  repetition; `min(budget, 3)`.
- **A character anti-repetition guard** (`5c40276`): a character's verbatim echo of
  itself / parroting another is eliminated deterministically (0/0); retry, then
  drop the echoed field if the other survives (it never goes mute).
- **A lexical narration backstop** (`06bb963`): a sentence still echoing after the
  retry is removed; lexical variation guaranteed.
- **Coverage at the authoritative source** (`35a9a2f`) + **partial-coverage
  advance** (`bdda81f`) + **the architect: escalate, without exposure**
  (`cedbb1a`).
- **Disruption-on-stall** (`490f1d5`).
- **The curl-replay method documented** in `AGENTS.md` §6.

---

### 5. Routed to other tasks

- **Task 33 (drive layer)** — the natural home for the GENERAL stagnation fix: give
  the hazard function a **topic-stagnation** signal (no new entity/anchor for K
  turns, or low lexical novelty) so it injects a new event in BOTH arms, not only
  in the roteiro.
- **Future roteiro** — the pile-up of disconnected disruptions + weakness in
  procedural arcs: make the disruption **advance the planned arc**, not interrupt
  loose.
- **Task 26** — a whole beat re-narrated (cross-turn `perception_event` dedupe,
  generalising the burst dedup), semantic character echo, a repeated
  `action_intent`.
- **Task 29.2** — `initialize_perspective` blows the fixed 1024-token budget with
  20+ characters present (large-cast scaling).
- **A new follow-up** — adjudicating the player's attempt (the portal example): the
  Director resolves the player's consequential action as a **world-response** +
  `return_control` ("you have not crossed yet; what do you do?"), never dictating
  their will. The same Director authority, with the freedom lock.

---

### 6. The design principle that remains

> **The Director has authority over the WORLD'S RESPONSE, never over the WILL of
> whoever acts.** Every action (NPC or player) is an attempt; the Director decides
> how the world responds (it may resist, complicate, reveal) and, for the player,
> always hands control back. It is the same mechanism that breaks stagnation (a
> new concrete event) and that preserves the player's freedom (never narrating
> their decision).

The canonical example (in Portuguese, as played):
> Player: *"Eu abro o portal e atravesso."*
> Narrator: *"Sua mão alcança o selo, mas ele não responde como você esperava. A
> superfície se abre por um instante e revela alguém do outro lado. Você ainda
> não atravessou. O que faz?"*
