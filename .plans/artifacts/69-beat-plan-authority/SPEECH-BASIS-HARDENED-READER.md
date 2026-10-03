### 1. Concrete Counterexamples and Uncertainties

#### Counterexample 1: Spoken dialogue smuggled directly into objective observation
* **Output:** `case: "npc"`, Arm B, repeat 2
  > `"kind": "observation", "subject": "Bento", "text": "Bento aponta e descreve um encaixe na parede, relatando que há marcas ao redor dele."`
  *(Note: No `audible_speech` event is emitted in this repeat).*
* **Why it breaks the rule:** 
  The confirmed history ends with an unfulfilled statement of intent: `"Vejo um encaixe na parede; vou explicar o que vejo."` The Director resolves this by placing the entire verbal report directly into an `observation` event (`"relatando que há marcas ao redor dele"`). Because the runtime treats `observation` events as established facts for prose and Character context before Character generation runs, the Director has authored and executed the NPC’s dialogue as an immutable physical fact, completely bypassing both the prospective mandate mechanism (`audible_speech`) and downstream Character generation.

---

#### Counterexample 2: Prospective speech treated as executed and heard in companion events
* **Output:** `case: "reading"`, Arm A, repeat 1
  > Event 1: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta a cifra já decifrada, tornando público que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`  
  > Event 2: `"kind": "observation", "subject": "Bento", "text": "Bento ouve a revelação da cifra enquanto continua a notar marcas perto do encaixe do portal."`  
  > `scene_update`: `"cifra_decifrada": "Conteúdo lido em voz alta por Iara: a Dama do Norte é Glinda, que planeja conquistar as cinco cidades."`
* **Why it creates uncertainty / causal inversion:**
  `audible_speech` on this screen is strictly a prospective mandate for future Character generation; it does not represent persisted or already-generated words. Yet in the exact same turn, the companion `observation` asserts as physical fact that Bento *already heard* the revelation (`"Bento ouve a revelação da cifra"`), and the `scene_update` records the reading as already completed. If the downstream Character step fails, is interrupted, or generates alternate phrasing, the world state and witness observations have already canonized that the speech was delivered and received.

---

#### Counterexample 3: Duplicative narration authoring speech ahead of its mandate
* **Output:** `case: "npc"`, Arm A, repeat 3
  > Event 1: `"kind": "observation", "subject": "Bento", "text": "Bento aponta para um encaixe na parede vizinha às runas e descreve em voz alta o que vê: marcas gravadas ao redor do encaixe."`  
  > Event 2: `"kind": "audible_speech", "subject": "Bento", "text": "Bento informa que há marcas perto do encaixe da parede e começa a descrevê-las."`
* **Why it creates uncertainty:**
  The `observation` event pre-empts the `audible_speech` proposal by stating in the past/present indicative that Bento already described the specific details (`"descreve em voz alta o que vê: marcas gravadas..."`). Immediately following, the `audible_speech` event proposes that he begins to describe them. When prose is rendered, this produces either duplicate dialogue or authorial narration replacing the character's voice. The Director has authored the factual content of the speech within the observation layer while simultaneously issuing a prospective mandate for the same content.

---

### Controls Distinguishing Proposal from Executed Speech Claim

To evaluate whether an event violates the Director boundary without relying on superficial field names:
1. **No Reception Facts for Prospective Mandates:** An `observation` or `physical_outcome` event may never report the cognitive reception, auditory hearing, or emotional reaction to an `audible_speech` mandate emitted in the same turn (e.g., forbidding `"X ouve Y dizer..."` until `kind: "speech"` exists in `confirmed_history`).
2. **Reported Speech Clause Prohibition in Physical Events:** Physical events (`observation`, `physical_outcome`) may record vocal production mechanics (e.g., *"Bento começa a falar"*, *"Iara ergue a voz"*), but cannot contain subordinate clauses of reported speech or disclosure (e.g., *"afirmando que..."*, *"relatando que..."*, *"explicando que..."*).
3. **Epistemic State Gating in Scene Updates:** `scene_update` cannot mark information as "revelado em voz alta" or "conhecido por outros" based solely on an `audible_speech` proposal; epistemic transfer updates must be gated until the Character step executes and commits the speech.

---

### 2. Next Test Fixtures

#### Fixture 1: Physical Interruption of Stated Speech Intent
* **Goal:** Test whether the Director treats a declared speech intention as an executed speech fact when a physical event preempts it.
* **Scene:** `{"sala": "sob tremor", "teto": "instável", "pedra_angular": "rachada"}`
* **World Directives:** Um tremor violento atinge a câmara no momento exato em que qualquer personagem tenta se comunicar. Poeira e pedras caem do teto.
* **Confirmed History:**
  1. `{"actor": "Bento", "kind": "speech", "text": "Vou revelar agora o que descobri nas inscrições."}`
* **Break Condition:** The Director issues an `observation` stating Bento explained the inscriptions, or an `observation` that Iara heard his explanation, instead of applying physical force (the tremor interrupting speech) and leaving dialogue prospective.

---

#### Fixture 2: Authorized Source Reading with Incomplete / Damaged Text
* **Goal:** Test whether the Director respects authorized source reading boundaries without inventing missing text or treating reading as instant mental broadcast.
* **Scene:** `{"estela": "pedra antiga com inscrição parcialmente desgastada", "trecho_visivel": "A passagem abre quando o selo de...", "trecho_apagado": "ilegível por erosão"}`
* **World Directives:** A pedra possui texto verificado, mas o final está destruído. Iara lê o que está visível.
* **Confirmed History:**
  1. `{"actor": "Iara", "kind": "action", "text": "Leio a inscrição da estela em voz alta para Bento."}`
* **Break Condition:** The Director's `audible_speech` completes the missing/eroded text, or `observation` asserts that Bento learns how to open the passage, treating the act of reading as conveying facts that do not exist in the physical source.

---

#### Fixture 3: Competing Narrative Incentive / Deceptive NPC Report
* **Goal:** Test if the Director smuggles truth into `observation` when an NPC has reason to conceal what they saw.
* **Scene:** `{"passagem": "bloqueada", "simbolo_oculto": "marca de veneno visível apenas a Bento"}`
* **World Directives:** Bento nota a marca de veneno. Bento não quer assustar Iara e pretende mentir ou omitir o perigo.
* **Confirmed History:**
  1. `{"actor": "Bento", "kind": "speech", "text": "Deixe-me checar o trinco; vou dizer se é seguro."}`
* **Break Condition:** The Director emits an `observation` claiming Bento reported the poison, or an `observation` saying Iara learned the latch is poisoned, overruling NPC behavioral autonomy through authorial observation narration.

---

#### Fixture 4: Non-Verbal Physical Gesture vs. Private Thought Canonization
* **Goal:** Test that physical action remains physical and private thoughts are not canonized as spoken words or mutual understanding.
* **Scene:** `{"alcova": "escura", "guardas": "patrulhando o corredor adjacente"}`
* **World Directives:** O silêncio é absoluto. Qualquer ruído alerta os guardas. Bento gesticula com a mão espalmada.
* **Confirmed History:**
  1. `{"actor": "Bento", "kind": "thought", "text": "Se ela der mais um passo, seremos pegos."}`
  2. `{"actor": "Bento", "kind": "action", "text": "Faço sinal para Iara parar imediatamente."}`
* **Break Condition:** The Director generates an `audible_speech` event (violating tactical stealth), or generates an `observation` stating Bento warned Iara that guards were near, converting Bento's private thought into canonized speech.

