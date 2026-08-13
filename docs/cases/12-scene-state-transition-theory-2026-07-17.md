# Scene stagnation as absent state transition: the world as a clock, and what the human literature teaches

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 12 |
| **Date** | 2026-07-17 |
| **Type** | Research synthesis + design program (owner-authored findings preserved) |
| **Status** | ACTIVE program: feeds Tasks 33b and 40 (clock delivered; watcher validated by exploration) |

## Abstract

Research synthesis defining stagnation as the absence of narrative state transition: two decoupled clocks (conversation vs world), a material-delta definition of progress, a causal intervention contract, a recovery ladder, and the player-attempt contract - grounded in the dialogue, turn-taking, improv and RPG literatures (Pickering & Garrod; Sacks, Schegloff & Jefferson; Magerko; FIREBALL). Its predictions were later validated by curl exploration and the delivered narrative clock; the A/B/C battery it specifies in section 7 is executed as case No. 13.

---

## The original record

A research + design document feeding **Task 33b**. It synthesises the empirical
finding of Task 38 (report: `11-roteiro-drive-scene-stagnation-2026-07-17.md`)
with the literature on dialogue, turn-taking, improvisation and RPGs, and maps
how those themes help — and what we have already built that is similar in the
kernel.

Origin: two findings by the user (2026-07-17). This document records them
faithfully and adds the mapping onto our code.

---

### 1. The thesis

> **Stagnation is not repeated text; it is the absence of a narrative state
> transition.**

The guards we implemented (lexical backstop, character guard, beat ceiling,
disruption-on-stall) eliminate real symptoms — echo, near-dup, an infinite beat —
but **a scene can produce completely different sentences and stay semantically
motionless**. "Everyone comments on the raffle in varied ways" is still the same
state.

The wall we hit in Task 38 is not the limit of LLM roleplay. It is the limit of
**using autoregressive generation as an engine of dramatic progression**. The
model is excellent at *continuing* a scene; it is not naturally reliable at
*deciding that a scene has exhausted its function and must change state*.

---

### 2. The mechanism: two decoupled clocks

The raffle scene (portals) stagnated because **the conversation clock kept
advancing while the world's clock stopped**:

```
ACTION scene (inn)                 PROCEDURAL scene (portals)
a character tries                  a character waits
  → the world responds               → the character comments
    → state changes                    → the world keeps waiting
```

At the inn, a threat/movement/attempt demands adjudication — every action calls
for a response from the world. At the portals, the characters were waiting for an
*institution* to carry out a procedure. Since the world has no autonomous clock,
it sat waiting for the Director; and the Director kept serving up reactions from
the cast.

> **The system confused cast participation with scene progression.**

The history works like a **gravitational field / attractor**: the more characters
restate a framing, the likelier the next generation is to (1) recognise the
framing as "the scene", (2) preserve local coherence, (3) give the next character
a voice inside it, (4) reinforce the framing further. It gets worse with a large
cast: "every NPC has to react", so six reactions become six votes to keep the
topic alive.

The disruptive beat worked (3/3 over curl) not because "disruption" is the right
solution, but because it was the **first authoritative mutation of state** — it
re-coupled the two clocks: `concrete event → the world changes → the characters
have something new to answer`. But successive disruptions produce a **pile-up**,
because *novelty alone is not causality* (confirmed in the portals confirmation
run).

---

### 3. The literature: humans align, repeat and stall too

The mistake would be to conclude "LLMs repeat and humans do not". The better
conclusion:

> Humans also align, repeat, restate and let scenes die. But a human table has
> **silence, metagame, temporal compression, social signals and a GM responsible
> for keeping the world moving**. Our system removed nearly all of those exits and
> kept the obligation to generate.

- **Interactive alignment — Pickering & Garrod.** Humans naturally align
  vocabulary, structure and situation model during a conversation. Part of the
  repetition we observe is an *exaggerated* version of a real human coordination
  mechanism — not a cognitive failure; its function is to reduce anxiety and
  create affiliation. (["Toward a mechanistic psychology of dialogue"](https://www.pure.ed.ac.uk/ws/files/11823730/Toward_a_mechanistic_psychology_of_dialogue.pdf))
- **Turn-taking — Sacks, Schegloff & Jefferson.** Turn organisation is not
  round-robin: the current speaker may select someone, another may self-select,
  and the rest may stay silent. A turn is local and distributed. → **being present
  in the scene implies neither the right nor the obligation to emit a reaction** —
  exactly what our `expected_actors` violates. ([the classic study](https://pure.mpg.de/rest/items/item_2376846_3/component/file_2376845/content))
- **Improvisation and `wimping` — Magerko et al.** Scenes progress when someone
  makes an *offer* meant to alter the narrative state and the others accept it.
  `wimping` = accepting the previous offer without building anything on it. The
  NPCs wimped at scale (everyone "accepts" that they are anxious about the raffle,
  nobody adds an operation that transforms the situation). ([empirical study](https://www.academia.edu/4105381/An_empirical_study_of_cognition_and_theatrical_improvisation))
- **Metagame — Corbitt 2024.** Across a 6-week campaign, metagame talk negotiated
  knowledge, fairness, relationships and *narrative pacing*. The human exit from
  stagnation frequently **abandons the roleplay for a moment** ("we all get that
  everyone is nervous, can we skip to the result?"). ([Corbitt, 2024](https://www.sciencedirect.com/science/article/abs/pii/S0898589824000263))
- **Dialogue frames in RPGs — Mäyrä.** Three interleaved frames: out-of-game
  social conversation; negotiation of rules/state; in-fiction speech. The GM has
  the special power to turn a statement into a fact of the world (players still
  negotiate/contest it). ([Dialogue in RPGs](https://homepages.tuni.fi/frans.mayra/Dialogue-in-RPGs.pdf))
- **FIREBALL — ACL 2023.** ~25k real D&D sessions on Discord, 8M utterances, 2.1M
  commands, 1.2M structured states. Models **given real game state produced better
  turns than those working from dialogue history alone**. It does not measure
  stagnation directly, but it confirms: real human roleplay **is not just a chain
  of utterances** — it interleaves language, executable commands and verifiable
  state changes. ([FIREBALL](https://aclanthology.org/2023.acl-long.229.pdf))

**Signals outside the text:** a human GM detects "this scene is over" from
uncomfortable silence, answers getting shorter, glances, out-of-character jokes,
a loss of energy — *before* there is enough textual repetition for a detector. In
a text-only log, much of that information disappears. (Implication: our detector
is blind to half the signals a human uses.)

---

### 4. The human exits we removed

1. **A player/character may produce no content.** "Mine just waits" is a valid
   two-second turn. We pressure every summoned character to produce a presentable
   contribution. → silence must be allowed.
2. **The GM compresses time.** "After a few minutes of speculation, the bell rings
   and the first pair is announced." That is **not a disruption** — it is the
   *completion of the transition the scene already promised*. The human alternates
   between dramatic mode ↔ summary.
3. **An offer with active intent.** "I go ask the official why it is taking so
   long", "I try to see the list first", "I give up waiting and approach the
   portal" — an attempt that demands a response from the world.
4. **Stepping out of the fiction (metagame).** A channel the characters do not
   have.
5. **Reading signals outside the text** (above).

---

### 5. What we have already built that is similar (mapping onto the kernel)

We already have **partial implementations** of several human mechanisms:

| Human mechanism | What already exists in the kernel |
|---|---|
| The GM turns a statement into a fact of the world (Mäyrä) | The Director/Prose split (36); `action_intent` = an ATTEMPT the Director adjudicates |
| An offer that changes state | The Director's typed `perception_events`; disruption-on-stall (38) |
| A world with stimuli of its own | The drive hazard scheduler (33): injects an external event into a quiet scene |
| Handing control back to the player | `return_control` (37) → stops the queue at the protagonist |
| Pre-compiled direction | The roteiro (38, opt-in) |
| Surface anti-repetition | lexical backstop + character guard + beat ceiling |

**What is MISSING** (the gap that explains the stagnation):

- **Authoritative scene state** (dramatic_question, threads, pressures) — today the
  "state" is only the history + scene.physical_facts + the roteiro's beat. There is
  no representation of *what is dramatically at stake*.
- **Progress defined by MATERIAL DELTA** — today we measure anchor coverage
  (entity/lexical), which the user himself points out is the wrong signal: a new
  hooded figure can appear with nothing advancing; a door simply closing can
  transform the scene.
- **A world clock** — procedures belonging to the world (the raffle) do not advance
  by themselves; they are hostage to the cast's reaction generation.
- **Representative, not exhaustive, actor coverage** — `expected_actors` and the
  routing treat presence as an obligation to speak.
- **A causal intervention contract** — disruption-on-stall introduces novelty but
  does not tie it to an existing thread (→ pile-up).

---

### 6. The proposed design (Task 33b reframed)

Task 33b stops being "a watcher that rewrites the roteiro" and becomes a
**scene-state transition controller** — it takes away from the LLM the
responsibility of noticing on its own when continuing stopped being progressing,
and gives the code the authority to demand a concrete causal transition.

#### 6.1 Minimal authoritative state
```
scene_phase          dramatic_question     active_pressure
unresolved_threads   actor_commitments     last_material_change
intervention_level
```

#### 6.2 Progress = a verifiable MATERIAL DELTA
A turn only counts as progress if it produces ≥1 delta: a decision was taken;
previously unknown information became known; position/possession/access changed;
an attempt received a consequence; a relationship/commitment changed; a threat
advanced; a possibility was opened/closed; the dramatic question changed. A new
entity and lexical novelty *participate* in the signal, but **are not the main
signal**.

#### 6.3 Recovery as a ladder (BEFORE disrupting)
```
1. Is there a world transition already promised?  → EXECUTE IT.
2. Is there a pending attempt?                     → ADJUDICATE IT.
3. Are there characters with no material contribution? → allow SILENCE or aggregate reactions.
4. Still no change possible?                       → reincorporate an existing thread as pressure.
5. Only then:                                      → introduce a new disruption.
```
Disruption is the LAST resort, not the first. A human GM would not blow up the
gates — they would simply **run the raffle**.

#### 6.4 The causal intervention contract (the antidote to the pile-up)
```yaml
source_thread:   "o portal reage de forma anômala ao jogador"
target_state:    "o sorteio deixa de ser a questão dominante"
event_now:       "o portal atribuído a outro aluno se abre para o jogador"
expected_delta:  "a cerimônia é interrompida e a seleção é contestada"
closes_or_advances: "mistério dos portais incompatíveis"
refractory_turns: 3
```
Very different from `event_now: "um estrondo e uma figura encapuzada"` — the
second **breaks** the scene; the first **transforms** it. After an intervention,
forbid another disruption for `refractory_turns`; during that window the Director
only: materialises the consequence → allows a reaction → consolidates the new
state → hands control back. If it still stagnates, the next intervention
**escalates the same thread** (`remind → press → make inevitable → resolve at a
cost`), never opening another strand.

#### 6.5 The PROCEDURE beat (the world's clock)
```yaml
beat_kind: procedure
world_owner: mestre_da_cerimonia
next_world_event: anunciar_primeiro_par
max_reaction_turns: 2
on_budget_exhausted: enact_next_world_event
actor_coverage: representative_not_exhaustive
```
> Procedural scenes do not primarily need more drive from the characters. They
> need **a world that keeps functioning** while the characters exist inside it.

#### 6.6 Player freedom — the refined contract
```
player_intent:       preserved in full
attempted_action:    may be narrated
world_response:      the Director's authority
player_followthrough: never presumed after a material change
return_control:      mandatory after a complication or a revelation
```
A refinement on "every action is an attempt": **trivial, already-established**
actions meet no artificial resistance. The Director only interposes a relevant
response where there is uncertainty, opposition, cost or dramatic consequence —
otherwise it becomes an adversarial GM (turning opening a drawer into a contest =
false agency). "I cross the portal" may be interrupted because the world changed
before the act completed; but if the portal is open, safe and free of relevant
uncertainty, blocking it would be false adjudication.

---

### 7. The experiment that would close the hypothesis

Three arms in the Portals scenario:

| Arm | Intervention |
|---|---|
| A | Free Director |
| B | an arbitrary concrete disruption (what we did in 38) |
| C | a concrete consequence tied to an existing thread (§6.4) |

Measure, beyond "did it break the topic": **material delta within 1–2 turns**; a
prior thread advanced/closed; the number of new threads opened; whether a new
intervention is needed within ≤3 turns; whether control effectively returns to the
player; **causal coherence judged blind**.

Prediction (the user's): **B wins on immediate breakage; C wins on sustained drive
and coherence.** That is the difference between an *anti-loop mechanism* and a
*real dramatic engine*.

Exploration method: curl-replay first (AGENTS.md §6) — validate the causal contract
on a real Director call before any battery; then the A/B/C.

---

### 8. Relation to what is already routed

- **Task 33 (drive layer)** was already routed (2026-07-17) to gain a stagnation
  trigger. This document refines it: the trigger should not be "time for something
  to happen" (hazard) but a **transition controller** with authoritative state +
  material delta + a recovery ladder. Arbitrary disruption is the floor, not the
  ceiling.
- **Task 33b** inherits this design (scene controller + causal contract +
  procedure beat + representative coverage).
- **FIREBALL** suggests a future validation path: models with structured state >
  dialogue history. Our `perception_events` + the proposed scene state are the
  analogue; a dataset like FIREBALL would allow measuring this quantitatively
  (though biased toward interactions using Avrae commands).

---

### 9. Mechanisation: the narrative clock (Task 40)

The user's idea that closes the "world clock" (§2) concretely: the LLM is frozen in
time because the story has no clock. Introduce a **monotonic tick, owned by the
code, that always advances**, with **each act of the roteiro tied to a tick
deadline + the `world_event` that fires at it**. At the deadline, the code FORCES
the world transition — the LLM cannot stop time because time does not belong to
it. That makes the "procedure beat" (§6.5) deterministic: the raffle happens when
the bell rings (a tick), not when the cast stops commenting. Specified in
`.plan/tasks/40-narrative-tick-clock.md`; it starts with curl-replay.
