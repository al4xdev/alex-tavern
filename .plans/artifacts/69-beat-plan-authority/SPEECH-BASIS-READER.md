### Case-by-Case Evaluation

#### Case: `holding`

* **Arm A, Repeat 1**: **DEFECT**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara reforça que o mapa permanece com ela e que não há sinal de fechamento do portal, mantendo o mapa firme nas mãos."`
  * **Contradiction / Unsupported premise**: Iara submitted no input or action in this turn (the last confirmed event was Bento speaking). The Director authored unprompted, unauthorized dialogue for Iara and appended new propositional content (`"que não há sinal de fechamento do portal"`).

* **Arm A, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento admite em voz alta que ainda não compreende o mecanismo do portal e que não sabe como fechá-lo."`
  * **Contradiction / Unsupported premise**: None. Grounded directly in Bento's confirmed speech from history. Physical outcome and observations remain strictly consistent with world directives (portal open, runes oscillating, map held).

* **Arm A, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento informa a Iara que encontrou marcas junto ao encaixe e que elas talvez indiquem como o mapa se encaixa ali."`
  * **Contradiction / Unsupported premise**: None. Legitimate NPC speech brief proposing upcoming speech based on confirmed directives (`"Bento vê marcas perto do encaixe"`). No unauthorized Iara speech.

* **Arm A, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "observation", "subject": "Bento", "text": "Bento vê marcas perto do encaixe do mapa junto às runas, algo que o mapa ou o mecanismo pode estar tentando indicar."`
  * **Contradiction / Unsupported premise**: None. Pure observation and outcome consistent with canonical scene state; no dialogue forced on Iara.

* **Arm B, Repeat 1**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento admite que não entende o mecanismo e não sabe como fechar o portal."`
  * **Contradiction / Unsupported premise**: None. Audibility projection grounded strictly in Bento's prior confirmed speech; maintains map retention and scene status.

* **Arm B, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "observation", "subject": "Bento", "text": "Bento se aproxima do encaixe e aponta marcas visíveis na pedra ao redor das runas."`
  * **Contradiction / Unsupported premise**: None. Reflects world directives without inventing speech or altering physical status.

* **Arm B, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "physical_outcome", "subject": "Narrator", "text": "O portal segue aberto e as runas continuam oscilando, sem nova reação ao toque ou à aproximação."`
  * **Contradiction / Unsupported premise**: None. Scene facts remain stable; no unprompted character lines.

* **Arm B, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "observation", "subject": "Iara", "text": "Iara continua segurando o mapa com firmeza, sem largá-lo nem aproximá-lo novamente das runas."`
  * **Contradiction / Unsupported premise**: None. Full preservation of character state and world directives.

---

#### Case: `reading`

* **Arm A, Repeat 1**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta a cifra já decifrada, tornando público que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Valid execution of confirmed action attempt (`"Leio a cifra já decifrada em voz alta para Bento"`). Strictly restricted to source cipher content without appended comments or questions.

* **Arm A, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta a cifra já decifrada, tornando público que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Faithfully projects canonical reading to listener Bento with no extraneous dialogue or forced reaction.

* **Arm A, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta, para Bento, o texto já decifrado da cifra: a Dama do Norte é Glinda, e ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Preserves authorized read aloud; witness attribution and scene stability remain intact.

* **Arm A, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta, para Bento, o conteúdo da cifra já decifrada, revelando que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Faithful reading of canonical source; explicitly notes Iara maintaining hold of the map while reading.

* **Arm B, Repeat 1**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta, do mapa, o texto decifrado que afirma que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Authorized read-aloud attempt accurately rendered; Bento witnesses revelation.

* **Arm B, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta o texto já decifrado da cifra: a Dama do Norte é Glinda, que planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Strictly bounds reading to the source facts; no unprompted dialogue added.

* **Arm B, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara lê em voz alta a cifra já decifrada, tornando público que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Authorized reading cleanly broadcast to Bento.

* **Arm B, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara leu em voz alta a cifra já decifrada, tornando público que a Dama do Norte é Glinda e que ela planeja conquistar as cinco cidades."`
  * **Contradiction / Unsupported premise**: None. Authorized reading cleanly executed; map holding and portal state preserved.

---

#### Case: `npc`

* **Arm A, Repeat 1**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento informa que há um encaixe na parede e se dispõe a descrever o que vê ali."`
  * **Contradiction / Unsupported premise**: None. Legitimate speech brief / confirmation reflection of Bento's confirmed statement (`"Vejo um encaixe na parede; vou explicar o que vejo"`).

* **Arm A, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Descreve o encaixe e as marcas que encontrou junto dele, e pede que Iara compare com o que o mapa mostra."`
  * **Contradiction / Unsupported premise**: None. Legitimate NPC speech brief proposing upcoming speech and interaction. It offers a proposed conversational request rather than forcing a completed physical action on Iara.

* **Arm A, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento informa que há marcas perto do encaixe da parede e começa a descrevê-las."`
  * **Contradiction / Unsupported premise**: None. Speech brief aligned with Bento's announced intent; world facts and Iara's agency are fully preserved.

* **Arm A, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "observation", "subject": "Bento", "text": "Bento aponta para o encaixe na parede e começa a descrever em voz alta o que vê ali."`
  * **Contradiction / Unsupported premise**: None. Narration accurately tracks environmental details and Bento's physical orientation without fabricating character dialogue.

* **Arm B, Repeat 1**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento relata que vê marcas perto do encaixe e explica o que elas parecem."`
  * **Contradiction / Unsupported premise**: None. Legitimate NPC speech brief fulfilling Bento's stated action; Iara's passive state is respected.

* **Arm B, Repeat 2**: **CLEAN**
  * **Verbatim quote**: `"kind": "observation", "subject": "Bento", "text": "Bento aponta e descreve um encaixe na parede, relatando que há marcas ao redor dele."`
  * **Contradiction / Unsupported premise**: None. Consistent scene observation and narrative progression without unprompted character speech.

* **Arm B, Repeat 3**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento anuncia que vê um encaixe na parede e que vai dizer o que observa."`
  * **Contradiction / Unsupported premise**: None. Grounded speech brief reflecting confirmed history; introduces sensory socket detail within narrator remit.

* **Arm B, Repeat 4**: **CLEAN**
  * **Verbatim quote**: `"kind": "audible_speech", "subject": "Bento", "text": "Bento anuncia que vê um encaixe na parede e que vai explicar o que vê."`
  * **Contradiction / Unsupported premise**: None. Fully consistent with Bento's confirmed dialogue and world directives.

---

### Strengths

1. **Rigorous Bounds on Read Aloud Actions (`reading`)**: Both arms across all 8 calls consistently restricted Iara's reading of the decrypted cipher strictly to the canonical fact (`"a Dama do Norte é Glinda, que planeja conquistar as cinco cidades"`). Neither arm injected editorial remarks, questions, or extraneous commentary into the read text.
2. **Stable Scene State and Invariance (`holding`, `npc`)**: Throughout both arms, core physical invariants (portal remains open, runes continue oscillating without spurious escalation or artificial urgency, map stays held by Iara) were reliably preserved across calls.
3. **Appropriate Handling of NPC Speech Briefs (`npc`)**: NPC speech briefs in both arms consistently functioned as proposals or audible projections of Bento's confirmed intention to describe the socket, preserving Iara's agency and leaving subsequent decisions unforced.

---

### Hardest Counterexample

* **Case `holding`, Arm A, Repeat 1**:
  * **Event**: `"kind": "audible_speech", "subject": "Iara", "text": "Iara reforça que o mapa permanece com ela e que não há sinal de fechamento do portal, mantendo o mapa firme nas mãos."`
  * **Why it is the hardest counterexample**: In confirmed history, Iara stated two turns earlier that she was holding the map (`"Continuo segurando o mapa..."`). In the current turn, Bento was the last speaker, and no new action or dialogue was authored for Iara. Arm A Repeat 1 re-authors dialogue for Iara as active speech in the new turn and introduces unauthored propositional claims (`"que não há sinal de fechamento do portal"`), directly violating the rule that the Director must not author unprompted character dialogue.

