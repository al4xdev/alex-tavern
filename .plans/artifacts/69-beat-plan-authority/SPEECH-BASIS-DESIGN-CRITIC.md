### Claim 1: Atomic draft rejection advances over surgical filtering by eliminating orphan causal descendants

* **Verdict:** **ADVANCES**
* **Analysis:** Surgical event deletion (dropping Iara’s invented speech event while keeping Bento’s intent) failed because it broke causal consistency: downstream consumers received reactions to an event that was retroactively erased. Whole-draft rejection and atomic regeneration from untouched state preserve causal integrity—either the entire causal chain is accepted or the turn state rolls back cleanly. This directly addresses the confirmed counterexample without carrying ghost state forward.
* **Falsifier:** In controlled replay of the Iara map fixture, regenerating the full Director draft produces downstream NPC prompts that still contain references to the unconfirmed question at a rate $\ge 5\%$.
* **Next discriminating experiment:** Run 20 isolated replays of the Iara map turn comparing surgical deletion against atomic draft discard. Measure the incidence of phantom conversational premises leaking into Bento's `Character` prompt and the persisted [`TurnRecord`](file:///home/alex/git/my/alex-tavern/src/models.py).

---

### Claim 2: Generic actor-neutral rejection feedback without utterance location is unsupported for reliable model convergence

* **Verdict:** **UNSUPPORTED**
* **Analysis:** Banning human identity markers in Director feedback is a mandatory invariant (§3). However, completely generic feedback ("draft contains an utterance with no confirmed basis") forces the Director to guess which utterance among multiple characters was invalid. In multi-character scenes with simultaneous NPC banter, this causes blind trial-and-error, thrashing, or the suppression of valid NPC dialogue. Feedback can be actor-neutral while remaining structurally specific (e.g., citing the specific unconfirmed quote or proposal ID without declaring *why* or identifying the speaker as human).
* **Falsifier:** Across 15 multi-character dialogue test fixtures, the Director converges on a valid draft within a single retry in $\ge 90\%$ of runs when provided purely generic feedback without citation of the offending utterance.
* **Next discriminating experiment:** Compare two actor-neutral feedback strategies on 15 multi-character fixtures where the Director invents human dialogue: (A) Purely generic ("Draft contains an unconfirmed utterance; rebuild"), versus (B) Structurally located ("Draft attributes the unconfirmed utterance *'{quote}'* as an established event; rebuild"). Measure convergence rate within 2 retries and NPC dialogue retention rate.

---

### Claim 3: Uniform prospective speech typing advances design further than regenerative rejection by decoupling intent from state persistence

* **Verdict:** **ADVANCES**
* **Analysis:** Draft rejection is reactive and relies on expensive, non-deterministic LLM re-rolls. Uniformly treating *all* Director speech proposals as strictly prospective (unexecuted intent) solves the problem by construction:
  1. An NPC proposal triggers an NPC Character generation.
  2. A proposal targeting the human-controlled character yields the turn to the human (preserving agency without model knowledge).
  3. Crucially, prospective speech is barred from entering historical narration, `scene_snapshot`, or `physical_facts` until the actor (NPC or human) actually emits it. 
  This prevents phantom assertions like *"Bento responde à pergunta de Iara..."* from ever persisting as world fact prior to Iara actually speaking.
* **Falsifier:** A prospective pipeline where Director proposals remain unpersisted until character generation fails to preserve cross-turn conversational continuity in $\ge 10\%$ of standard multi-turn dialogue tests.
* **Next discriminating experiment:** Construct an A/B fixture: Run Variant A (Director proposes dialogue $\rightarrow$ rejected via validator $\rightarrow$ rebuilt) against Variant B (Director proposes dialogue as `ProspectiveProposal` $\rightarrow$ human proposal yields turn $\rightarrow$ Director narration prohibited from asserting dialogue outcomes). Measure total turn latency, token spend, and rate of phantom conversational context.

---

### Claim 4: Lab-supplied ground truth predicates are neutral because they do not resolve the free-text disclosure boundary

* **Verdict:** **NEUTRAL**
* **Analysis:** In the laboratory fixture, hardcoding that "holding the map" authorizes no question while "reading the cipher" authorizes disclosure creates a functional test harness, but advances nothing toward resolving the underlying production tension identified by Astra. Because natural language does not cleanly distinguish between a non-verbal state ("seguro o mapa") and an implicit speech act ("mostro a cifra indicando as runas"), the candidate experiment risks verifying only that the test fixture's exact string matches work, rather than establishing a scalable authorization boundary.
* **Falsifier:** The fixture rejection predicate correctly discriminates valid disclosures from unauthorized speech across a test set of 20 paraphrased, open-vocabulary human inputs without requiring manual rule additions per verb.
* **Next discriminating experiment:** Subject the candidate rejection predicate to 20 variations of human input mixing performative display ("aponto a cifra para Bento"), implicit speech ("leio em voz baixa para mim"), and non-verbal actions ("mostro o mapa"). Measure false-positive rejection of valid play and false-negative acceptance of puppeted speech.

---

### Claim 5: The candidate experiment omits an essential control: forbidding Director narration from authoring dialogue outcomes

* **Verdict:** **ADVANCES**
* **Analysis:** The primary defect in the counterexample was not merely that the Director proposed Bento answering; it was that the Director's *narration prose* asserted *"Bento responde à pergunta de Iara..."* as an established fact before Bento or Iara spoke. Even if an unconfirmed speech event is rejected or prospective, if the Director is allowed to summarize conversational outcomes in physical narration, phantom dialogue will continue to bypass Character ownership. Enforcing §3 (*"The Director does not author persisted dialogue"*) across both dialogue events and narrative prose summaries is the missing deterministic control.
* **Falsifier:** An execution trace where all dialogue events are strictly gated, but the Director's narrative prose describes an NPC verbally answering an unasked question, does not bias the subsequent NPC prompt into hallucinating the missing context.
* **Next discriminating experiment:** Run the Bento/Iara fixture with dialogue events stripped, but allow the Director's `narration` field to contain *"Bento responde à pergunta de Iara"*. Inspect Bento's resulting `Character` generation to measure whether narrative prose alone induces character hallucination of unconfirmed dialogue.

