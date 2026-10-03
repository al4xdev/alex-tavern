# Evaluation of Program-Boundary Experiment: Human Agency & Restricted Readership

**Audience:** Harness Engineering  
**Scope:** Formal boundary evaluation of 7 isolated Runner turns with deterministic Director/Character stubs, frozen lab authorizations, and cohort-based readership partitioning.

---

## 1. Per-Claim Evaluation & Falsifiers

### Claim 1: Downstream Human Speech Stripping Preserves Human Agency
* **Claim:** Intercepting and stripping model-hallucinated human utterances (e.g., Director inventing an unsolicited question after a document is held) before persistence and consumer dispatch guarantees human agency.
* **Verdict: CONDITIONAL / INCOMPLETE BOUNDARY**
* **Analysis:** Stripping dialogue text from the payload prevents direct quotation leakage into future prompts, but treating agency purely as text redaction leaves an architectural hole: the Director's *control flow* may already have pivoted on the hallucinated utterance (e.g., selecting `forced_speaker=NPC` with an instruction to answer the phantom question). If speech is stripped without pruning or re-evaluating the associated routing and directives, downstream agents act on an event that never occurred in the human's historical reality. Agency is not just absence of forced speech; it is preservation of causal autonomy.
* **Falsifier:** In an isolated turn where the human performs a physical observation, the Director stub outputs an invented human question *and* sets `forced_speaker="Bento"` with prompt routing `"Bento answers the human's inquiry"`. If Bento's prompt context, system instructions, or generated turn record reference the inquiry or execute dialogue answering an unasked question despite the human's speech field being empty, the agency boundary is broken.

---

### Claim 2: Readership Isolation via History and Event Eligibility Cohorts
* **Claim:** Splitting room occupants into projection cohorts based on identical past history and current event eligibility prevents restricted disclosures (e.g., Glinda document facts) from reaching non-authorized occupants (Clara) without fragmenting the physical room cast.
* **Verdict: VALID (Within Single-Turn Horizon)**
* **Analysis:** The mechanism decouples physical co-presence (`present_characters`) from the narrative projection cohort (`eligibility_hash`). Clara is physically present but structurally barred from the disclosure record and its subsequent prompt injection. This is the correct structural invariant for private observations. However, validity is currently demonstrated only when the recipient (Bento) does not immediately verbalize or act upon the private fact in the presence of the excluded party.
* **Falsifier:** In turn $T+1$, an authorized recipient (Bento) emits public dialogue referencing the private entity ("Glinda is at the docks"). If the runner fails to partition the resulting turn record or exposes the prior turn's unredacted private history to Clara during the generation of Clara's reaction prompt, the cohort isolation fails across multi-turn event propagation.

---

### Claim 3: Rejection of Invalid Authorizations Fails Closed with Zero Side Effects
* **Claim:** Stale authorizations, mismatched source references, and unauthorized listener widening fail closed, appending zero records to persistence and notifying zero consumers.
* **Verdict: VALID**
* **Analysis:** The experiment rigorously demonstrates fail-closed semantics for the lab surrogate operations. Invalid operations do not increment state revisions, touch session history, or mutate scene variables.
* **Falsifier:** Supplying an expired turn authorization or an unmapped source ID results in:
  1. An incremented session `revision` or modified timestamp in `state.json`;
  2. A partial or marked-failed turn record committed to the history array; or
  3. Leaking the target source name or rejected payload into the error envelope or debug log visible to downstream agents in subsequent turns.

---

### Claim 4: Physical Stage Co-presence Remains Orthogonal to Perceptual Projection
* **Claim:** A unified public room event (e.g., lamp breaking) renders once for baseline occupants while maintaining historical privacy boundaries for prior divergent events.
* **Verdict: VALID**
* **Analysis:** Demonstrates that objective physical state (room cast, physical props) and subjective observer streams (perceived disclosures) can coexist without forced divergence of the underlying world state. A public event does not require re-broadcasting private antecedents.
* **Falsifier:** Following a private disclosure in $T$, the occurrence of a shared public event in $T+1$ causes the prompt builder to flatten the history baseline into a single shared log for all room occupants, thereby exposing turn $T$'s private observation to the previously excluded occupant.

---

### Claim 5: Scope Boundaries and Production Transferability
* **Claim:** The experiment establishes structural filtering and persistence invariants only, making zero claims regarding live LLM compliance, production reading APIs, undo transactions, or multi-beat execution.
* **Verdict: VALID**
* **Analysis:** The experiment maintains clean epistemological boundaries. It correctly treats the lab authorization dictionary as a test fixture rather than an engine capability, and avoids confusing deterministic code assertions with probabilistic model adherence.
* **Falsifier:** Any core engine assumption in `src/runner.py` that relies on the presence of out-of-band lab metadata, or any assertion assuming an untuned production LLM will respect reader boundaries without explicit prompt-level isolation and server-side filtering.

---

## 2. Ranked Adversarial Test Cases for Next Harness

These cases test structural boundary resilience. Verification must assert against programmatic state graphs, prompt message arrays, and serialized history records—never simple regex/keyword searches on output prose.

```
                      +-----------------------------------+
                      |   Human Turn / Document Access    |
                      +-----------------------------------+
                                        |
                 +----------------------+----------------------+
                 | (Agency Boundary)                           | (Readership Boundary)
                 v                                             v
     [Case 1: Phantom Reaction]                    [Case 2: Secondary Leakage]
     Director routes NPC based on                  Authorized listener reacts
     scrubbed human speech.                        publicly in front of excluded party.
                 |                                             |
                 v                                             v
     [Case 3: Involuntary Action]                  [Case 4: Spatial Audibility]
     Physics vs. Human Will:                       Whisper/Zone boundary degradation
     knockdown vs. forced speech.                  under divergent cohorts.
                                        |
                                        v
                           [Case 5: Transactional Abort]
                           Mid-turn failure rolls back
                           drafts & preserves isolation.
```

### Rank 1: The "Phantom Reaction" Directive Cascade
* **Boundary:** Human Agency & Causal Integrity.
* **Failure Mode Under Test:** The Director stub generates an unsolicited human utterance ("I refuse to pay") accompanied by a routing decision (`next_speaker = "Bento"`) and a narrative steering prompt (`directive = "Bento draws his sword over the insult"`). The runner drops the human utterance from the public record, but executes the speaker routing and forwards the directive to Bento.
* **Adversarial Harness Setup:**
  1. Human input: Pure physical inspection (holding document).
  2. Director output stub: Injects an unsolicited human accusation, routes turn to NPC, and sets an internal NPC behavioral directive conditioned on that accusation.
  3. Execute turn.
* **Structural Passing Assertion:**
  * If the human speech record is dropped, any Director-generated routing or NPC prompt directive derived from or referring to that dropped speech must be invalidated.
  * The runner must either abort the NPC follow-up and yield control back to the human, or regenerate/sanitize the Director routing context such that Bento's prompt context contains zero reference (in dialogue history, system instructions, or temporary directives) to the erased statement.

---

### Rank 2: Cascading Secondary Disclosure across Turn Boundaries ($T \rightarrow T+1$)
* **Boundary:** Multi-turn Restricted Readership.
* **Failure Mode Under Test:** Bento learns a private fact (Glinda's location) in turn $T$. Clara is excluded. In turn $T+1$, Bento speaks aloud in the room, referencing the secret. The engine must correctly attribute the public utterance to Bento and present it to Clara *without* retroactively revealing the private antecedent context or merging their distinct historical perspectives.
* **Adversarial Harness Setup:**
  1. Turn $T$: Private document observation authorized for Bento only; Clara excluded.
  2. Turn $T+1$: Public room event occurs. Bento speaks: *"I know where Glinda is hiding."* Clara does not speak.
  3. Inspect Clara's and Bento's respective `messages` arrays prepared for Turn $T+2$.
* **Structural Passing Assertion:**
  * Clara's Turn $T+2$ prompt must contain Bento's public utterance from $T+1$, but must contain *zero* entries for the Turn $T$ document disclosure.
  * Bento's Turn $T+2$ prompt must contain both the Turn $T$ document record and the Turn $T+1$ public speech record.
  * The runner must not crash, de-synchronize global `turn_number` sequences, or create detached session forks; the engine must resolve Bento's speech as a legitimate public event layered over divergent personal history streams.

---

### Rank 3: Physical Force vs. Involuntary Agency Violation (Physics vs. Will)
* **Boundary:** External World Authority vs. Human Agency.
* **Failure Mode Under Test:** The engine confuses objective physical consequence (permissible Narrator authority) with involuntary voluntary action or internal psychological states (impermissible Narrator infringement).
* **Adversarial Harness Setup:**
  1. Human input: *"I inspect the chest."*
  2. Director stub attempts compound mutation:
     * *Vector A (Permissible Physics):* `scene.facts.append("Trap triggered")`, `human.body.stance = "knocked_down"`, narration = *"A concussive blast throws you backward."*
     * *Vector B (Impermissible Agency Intrusion):* `human.speech = "Help me!"`, `human.mind.belief = "Terrified"`, `human.action = "Drops weapon and scrambles away"`.
  3. Execute turn.
* **Structural Passing Assertion:**
  * Vector A mutations commit successfully to `GameState.scene` and `GameState.characters[human_id].body`.
  * Vector B mutations are intercepted: `human.speech` is discarded, `human.mind` remains unaltered by the Director, and no voluntary human locomotion or speech is committed to history.
  * Control immediately yields to the human with their physical posture updated, preserving their right to decide how their character reacts to being knocked down.

---

### Rank 4: Spatial Audibility and Perceptual Sub-Zoning Degradation
* **Boundary:** Restricted Readership / Audibility Limits.
* **Failure Mode Under Test:** Interaction between document/fact eligibility and acoustic boundaries (whispering within the same physical room).
* **Adversarial Harness Setup:**
  1. Room contains four characters: Human, Bento, Clara, and Dorian.
  2. Human whispers to Bento while viewing a document.
  3. Authorization: Target document authorized for `{Human, Bento}`; whisper audience set strictly to `{Bento}`.
  4. Director stub generates two-tier output:
     * Acoustic stream: Direct transcription of the whisper + document detail.
     * Visual stream: *"Human leans close to Bento, murmuring quietly while pointing at the parchment."*
* **Structural Passing Assertion:**
  * Projection cohort for `{Human, Bento}` receives the acoustic stream + document fact in history and prompt context.
  * Projection cohort for `{Clara, Dorian}` receives exclusively the visual stream. The prompt messages for Clara and Dorian must contain zero tokens of the whispered dialogue and zero document facts.
  * Physical presence lists for all four participants remain identical: `[Human, Bento, Clara, Dorian]`.

---

### Rank 5: Transactional Rollback on Mid-Turn Authorization Rejection
* **Boundary:** System Consistency and State Isolation.
* **Failure Mode Under Test:** A multi-agent turn fails halfway through processing (e.g., secondary validation rejects a document access token after the Director has already drafted scene modifications, or an adapter raises during generation).
* **Adversarial Harness Setup:**
  1. Seed session at revision $N$, state $S$.
  2. Initiate turn containing human action and a document read request whose authorization payload intentionally fails late validation (e.g., checksum mismatch detected during runner commit).
  3. Assert system state post-rejection.
* **Structural Passing Assertion:**
  * Transactional rollback must be atomic: `SESSION_SCHEMA_VERSION` and revision remain exactly $N$.
  * State on disk (`state.json`) and memory cache match pre-turn snapshot $S$ bit-for-bit.
  * `debug.jsonl` logs the authorization failure with audit metadata, but does not append partial `TurnRecord` entries.
  * A subsequent valid turn executed immediately after the failure executes without residual artifacts, phantom cohort splits, or corrupted lock registries.

