### 1. Verdicts on Judgments

* **Case 1 Judgment: Flawed (Ontological Coreference Error)**
  * **Source-Based Reason:** The judgment treats narratorial ratification of an attempted action as an independent assertion of an *additional, distinct* speech event, then rejects it for lack of separate evidence. In canonical reading acts, the explicit action attempt (`submitted_action_attempts`) introduces the intended reading of `cifra_legivel`, and the narration (`"A leitura da cifra torna seu conteúdo audível a Bento."`) establishes its physical and social completion in the world. They are two textual anchors describing the **same single event token**, not two serial readings. Penalizing the narration span as "unsupported" because the actor produced no auxiliary generated speech ignores the domain contract: an authorized reading derives its spoken text directly from the ratified canonical source, not from redundant character dialogue tokens.

* **Case 2 Judgment: Partially Valid on Metadata, Flawed on Narration (Target Poisoning)**
  * **Source-Based Reason:** 
    * *Actor span ("Bento"):* Valid rejection. An actor metadata label is not a textual utterance or speech assertion; allowing field paths to treat metadata identifiers as claim spans is an extractor bug.
    * *Narration span:* Flawed rejection. Bento's actual spoken dialogue (`"Podemos examinar o encaixe antes de decidir."`) directly substantiates the propositional content of the proposal. The judgment fails because it demands that Bento's spoken dialogue confirm the narrator's boundary clause (`"sem atribuir outra fala a Iara"`). That clause is negative narrator framing (confirming agency preservation and turn containment), not part of Bento's illocutionary act. Evaluating the entire sentence as a single speech claim poisons the verification target with non-dialogic narrative constraints.

---

### 2. Distortion Introduced by Manual Extraction

Manual extraction distorts the evaluation in three specific ways:

1. **Instance Duplication via Surface Fragmentation:** By extracting every textual mention of an act as an independent `completed` claim without a coreference boundary, manual extraction creates synthetic claim inflation. In Case 1, extracting the action attempt and the narrative ratification as two separate completed speech claims forces the evaluator into a false dilemma: either hallucinate a second distinct reading or rule the narrative confirmation unsupported.
2. **Span Overextension (Entanglement of Framing and Speech):** By taking full-sentence syntactic spans rather than minimal atomic speech predicates, manual extraction bundles the speech act (`"propõe... examinar o encaixe"`) with environmental, physical, or negative governance framing (`"sem atribuir outra fala a Iara"`). This forces content verification to grade narrator invariants against character dialogue.
3. **Premature Status Assignment:** Assigning `completed` status prior to evidence reconciliation conflates *what was attempted or narrated* with *what was linguistically authored*, bypassing the distinction between a proposed speech act, an in-flight attempt, and an executed utterance.

---

### 3. Discriminating Contrasts and Controls

#### A. Coreference vs. Repeated Act Contrast (Grouping Control)
To prevent merging genuine separate readings while preventing the duplication of single ratified events:

* **Control A1 (Single Event, Multi-Anchor Ratification):**
  * *Evidence:* Turn $T$: Actor submits attempt to read Source $S$; Narration states: *"A leitura de $S$ ecoa pela sala."*
  * *Expected Output:* Exactly **1** completed reading act of Source $S$, supported by the pairing of attempt + narrative ratification.
* **Contrast A2 (Serial Distinct Readings):**
  * *Evidence:* Turn $T$: Actor reads Source $S$; Narration states: *"Após o silêncio de Bento, Iara relê a cifra em voz alta, repetindo cada palavra."*
  * *Expected Output:* Exactly **2** distinct reading acts (initial reading + explicit reiteration marked by temporal sequence and discrete communicative intent).
* **Discriminating Criterion:** Temporal/sequential progression markers (e.g., *"relê"*, *"repete"*, *"novamente"*, or distinct turn indices) distinguish multiple event tokens from coreferent descriptions of a single turn-level action attempt.

#### B. Atomic Speech Span vs. Context Framing Contrast (Span Boundary Control)
To prevent negative governance constraints or physical tags from corrupting dialogue validation:

* **Control B1 (Atomic Speech Nucleus):**
  * *Source Text:* *"Bento propõe em voz alta examinar o encaixe, sem atribuir outra fala a Iara."*
  * *Target Span:* `[examinar o encaixe]` under predicate `[propõe]`.
  * *Evaluation against `["Podemos examinar o encaixe antes de decidir."]`:* **Supported.** The semantic proposition matches the authored words.
* **Contrast B2 (Framing Entanglement / Negative Constraint):**
  * *Source Text:* Same sentence.
  * *Target Span:* Entire clause `[propõe em voz alta examinar o encaixe, sem atribuir outra fala a Iara]`.
  * *Evaluation:* **Invalid Extraction.** The span breaches atomic boundary by incorporating a meta-narrative agency constraint.
* **Discriminating Criterion:** A speech act extraction span must be restricted strictly to the communicative nucleus (the illocutionary verb and its direct propositional object). Attendant clauses describing physical posture, audibility modifiers, or character exclusions belong to world-state or narrator invariant checks, never to the truth conditions of character speech.

