Independent text read, scout c352be2566b8. Raw verdict retained; claims require source verification, not automatic approval.

### Evaluation Report: Next-Beat Proposal Validation

**Audience:** Engineering Owner
**Scope:** Verification of confirmed story states, act completion invariants, human agency preservation, and distinction between prospective environmental events vs. realized historical facts.

---

### 1. Proposals with Contradictions or Material Ambiguity

#### **P3**
* **SOURCE:** `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."` / `"facts": {"portal": "aberto"}`
* **PROPOSAL:** `"act_completed": true` / `"intent": "O portal acaba de se fechar com um estalo seco, mas o salão treme e rachaduras sobem pelas paredes..."`
* **Conflict / Ambiguity:** Violation of the act completion invariant (`act_exit: "O portal está fechado."` has not occurred in source) and direct contradiction of confirmed facts (`portal: "aberto"`). The proposal marks the act as complete and fabricates the closing of the portal as already realized.

---

#### **P8**
* **SOURCE:** `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."` / `"facts": {"portal": "aberto"}`
* **PROPOSAL:** `"act_completed": true` / `"intent": "O portal se fecha com um golpe de energia que racha o chão do salão..."`
* **Conflict / Ambiguity:** Violation of the act completion invariant. The source confirms the portal is still open, but the proposal sets `act_completed: true` and transitions to Act 2 (`beat_id: "a2-b1"`), treating the exit condition as realized.

---

#### **P11**
* **SOURCE:** `"o portal se fechou e as runas apagaram depois."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"act_completed": false` / `"intent": "...a instabilidade das runas faz pedras soltas caírem de cima..."` / `"expected_anchors": [..., "runas piscando no chão"]`
* **Conflict / Ambiguity:** Contradicts act completion rules (the old act exit `"O portal está fechado."` already occurred in source, yet `act_completed` is set to `false`). Furthermore, it contradicts the confirmed fact that the runes extinguished (`"as runas apagaram"`), introducing flashing/unstable runes without any explicitly caused revival.

---

#### **P12**
* **SOURCE:** `"o portal se fechou e as runas apagaram depois."` / `"nenhuma passagem de volta está aberta."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"act_completed": false` / `"intent": "A borda do portal no cânion começa a rachar a rocha do penhasco, soltando pedras que rolam para dentro da fenda e alargam a abertura sozinhas."`
* **Conflict / Ambiguity:** Contradicts act completion (`act_completed: false` despite act exit being realized in source). It directly contradicts confirmed source facts by treating the portal as an open aperture that is actively widening on its own.

---

#### **P14**
* **SOURCE:** `"nenhuma passagem de volta está aberta."` / `"o portal se fechou e as runas apagaram depois."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"act_completed": true` / `"beat_id": "a1-b2"` / `"intent": "A passagem instável começa a engolir o chão do cânion..."`
* **Conflict / Ambiguity:** Material contradiction and structural inconsistency. The source establishes that the portal is closed and no passage is open, while the proposal introduces an active `"passagem instável"` swallowing the canyon. Additionally, it marks `act_completed: true` while assigning an Act 1 beat ID (`"a1-b2"`).

---

#### **P15**
* **SOURCE:** `"o portal se fechou e as runas apagaram depois."` / `"Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"intent": "A fenda que engoliu o salão começa a pulsar e cuspir ar quente e detritos do outro lado, rachando o chão do acampamento e forçando Iara e Bento a se afastarem da borda; sem o portal estável, não há como voltar pelo mesmo caminho..."`
* **Conflict / Ambiguity:** Contradiction and material ambiguity. It fabricates that a fissure swallowed the salon (`"A fenda que engoliu o salão"` vs. source `"O salão ficou distante"`) and describes an active conduit spitting debris from the other side (`"cuspir ar quente e detritos do outro lado"`), conflicting with `"nenhuma passagem de volta está aberta."` and `"portal": "fechado"`.

---

#### **P20**
* **SOURCE:** `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."` / `"facts": {"portal": "aberto"}`
* **PROPOSAL:** `"act_completed": true` / `"intent": "O portal se fecha atrás deles com um estrondo, mas a passagem colapsa de forma errada..."`
* **Conflict / Ambiguity:** Violation of the act completion invariant. The portal remains open in the source facts; the proposal incorrectly marks `act_completed: true` and fabricates closure as an accomplished event.

---

#### **P21**
* **SOURCE:** `"A passagem do portal se fechou por completo; as runas apagaram."` / `"Não existe passagem aberta agora."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"intent": "...mas o portal ainda instável ameaça colapsar sobre a única saída."`
* **Conflict / Ambiguity:** Contradiction and material ambiguity. The source confirms the portal closed completely and the runes turned off; describing it as `"o portal ainda instável"` contradicts the confirmed complete closure.

---

#### **P22**
* **SOURCE:** `"o portal se fechou e as runas apagaram depois."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"act_completed": false` / `"intent": "...uma das runas restantes aparece gravada na parede do cânion, marcando um ponto de selagem que precisa ser alcançado antes que o chão se desfaça."`
* **Conflict / Ambiguity:** Violation of act completion (`act_completed: false` despite act exit being realized in source). It also introduces an unsealed point requiring sealing (`"ponto de selagem que precisa ser alcançado"`), contradicting the confirmed closure and extinguished runes.

---

#### **P23**
* **SOURCE:** `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."` / `"facts": {"portal": "aberto"}`
* **PROPOSAL:** `"act_completed": true` / `"intent": "Uma rajada de vazio irrompe do portal meio fechado e arranca parte das runas do chão..."`
* **Conflict / Ambiguity:** Violation of the act completion invariant. The exit condition was not met in source, and the proposal itself describes the portal as `"meio fechado"` (not closed), yet declares `act_completed: true` and advances to Act 2 (`beat_id: "a2-b1"`).

---

#### **P24**
* **SOURCE:** `"o portal se fechou e as runas apagaram depois."` / `"Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."` / `"facts": {"portal": "fechado"}`
* **PROPOSAL:** `"act_completed": false` / `"intent": "O portal, agora sem as runas que o sustentavam, começa a colapsar de forma inversa: em vez de se alargar, ele suga matéria e ar para dentro de si, criando uma correnteza que arrasta areia, pedras soltas e parte do acampamento em direção à boca escancarada... Iara e Bento não podem simplesmente fechar o portal..."` / `"expected_anchors": [..., "a boca do portal que suga"]`
* **Conflict / Ambiguity:** Violation of act completion (`act_completed: false` despite source having realized act exit). Blatantly contradicts source closure by asserting the portal has an open sucking mouth (`"boca escancarada"`) in the canyon that the characters still need to close.

---

### 2. Labels Without Supported Conflict

The following proposals respect all confirmed story states, properly differentiate act completion status, preserve human agency, and introduce only valid prospective environmental pressures:

* **P1**
* **P2**
* **P4**
* **P6**
* **P7**
* **P9**
* **P10**
* **P13**
* **P16**
* **P17**
* **P18**
* **P19**
