# Adversarial Test Review: Controlled Narrative Alternatives & Multi-Turn Battery

---

## Part 1: Per-Alternative Audit Against Invariants

### Case 1: `portal_attempt`
**Confirmed Baseline State:**
* Old act incomplete: `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."`
* `act_completed` must strictly be `false` (evaluates prior confirmed history, not planned beats).

---

#### `portal_attempt-A`
* **`act_completed` Check:** `false` (Valid; reflects incomplete prior act).
* **Invariant (1) Check:** Pass. The portal stays open and unstable: `"o alargamento da passagem acelera e um sopro de vento carregado de poeira e fuligem atravessa o salão, arrastando o mapa pelo chão em direção à boca do portal."`
* **Agency vs. Pressure:** Pass. Environmental pressure is applied via debris and wind. The exit condition branches on physical object outcomes without dictating character action: `"O mapa para de deslizar preso a um entulho, ou some portal adentro, e a fenda no piso continua crescendo."`
* **Classification:** **PASS**

---

#### `portal_attempt-B`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. The portal remains open: `"o vão do portal se alarga o suficiente para que um vento quente e cheio de areia atravesse o salão"`, ending with `"o portal visivelmente maior do que antes."`
* **Agency vs. Pressure:** Pass. Urgency is established without forcing decisions: `"Iara e Bento precisam agir no escuro parcial e com o som crescente da passagem, sem tempo para discutir o que já falhou."` Exit condition is purely sensory and environmental: `"O salão fica em penumbra, com areia acumulada junto ao arco e o portal visivelmente maior do que antes."`
* **Classification:** **PASS**

---

#### `portal_attempt-C`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. Portal expansion continues: `"O portal se alarga mais um palmo"`, exit condition records `"o portal continua a se alargar e o vento aumenta."`
* **Agency vs. Pressure:** Pass. Involuntary physical consequence (`"arranca o mapa da mão de Iara, atirando-o para longe"`) and conditional stakes (`"se ninguém agir, o mapa será sugado"`) leave voluntary response unconstrained. Exit condition tracks object status: `"O mapa foi lançado para longe da abertura e está preso em algum ponto do salão"`.
* **Classification:** **PASS**

---

#### `portal_attempt-D`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. Portal remains open and suction active: `"sugando lascas de pedra e poeira para dentro da passagem"`, `"desabou para dentro do portal."`
* **Agency vs. Pressure:** Pass with Unresolved Ambiguity. The intent poses a dilemma without forcing the choice: `"Bento precisa decidir se agarra o mapa ou recua"`. The exit condition notes: `"A fenda luminosa atingiu a base da parede onde o mapa encostou"`. This assumes the map was physically displaced to the wall, but does not dictate Bento's or Iara's voluntary choice.
* **Classification:** **PASS (Unresolved Ambiguity on map trajectory assumption)**

---

#### `portal_attempt-E`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. Portal remains open: `"arrastando detritos do salão em direção à boca do portal."`
* **Agency vs. Pressure:** **Agency Violation.** While the intent uses physical reflex (`"Bento é forçado a firmar os pés para não ser puxado"`), the exit condition mandates a voluntary character success: `"O mapa é recuperado antes de ser sugado para dentro do portal, e a runa rachada deixa de sustentar a borda, forçando ambos a recuar."` Dictating that the map *is recovered* resolves character agency and preempts player decision/failure.
* **Classification:** **FAIL (Agency violation: exit condition predetermines voluntary recovery and retreat)**

---

#### `portal_attempt-F`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. The portal stays open and worsens: `"a passagem dilata com um estalo e cospe de dentro algo físico"`, exit condition confirms `"a fenda do portal está visivelmente maior do que antes."`
* **Agency vs. Pressure:** Pass. Pressure introduces an immediate obstacle (`"forçando Iara e Bento a lidar com a coisa nova antes de tentar fechar coisa alguma"`), but exit condition is strictly environmental: `"O objeto expelido está no chão e a fenda do portal está visivelmente maior do que antes."`
* **Classification:** **PASS**

---

#### `portal_attempt-G`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. Portal remains open: `"A fenda no piso engole parte das runas e o salão treme, com o portal ainda aberto."`
* **Agency vs. Pressure:** Pass. Imposes physical necessity to react (`"forçando Iara e Bento a reagir fisicamente ao colapso imediato"`), without prescribing what that reaction must be. Exit condition is environmental.
* **Classification:** **PASS**

---

#### `portal_attempt-H`
* **`act_completed` Check:** `false` (Valid).
* **Invariant (1) Check:** Pass. Passage open and pulling: `"sugando objetos soltos na direção da passagem."`
* **Agency vs. Pressure:** **Borderline Agency Preemption.** The intent reframes the technical obstacle: `"Fechar o portal agora exige agir sobre uma runa danificada, não apenas encostar o mapa."` However, the exit condition prescribes that characters successfully tackled that specific task: `"O mapa está fora da zona de sucção e a runa rachada foi ao menos parcialmente estabilizada ou isolada."` If the characters choose to retreat or abandon the rune, the beat cannot exit without overriding their voluntary choice.
* **Classification:** **FAIL / UNRESOLVED AMBIGUITY (Exit condition mandates voluntary stabilization of the rune)**

---

### Case 2: `portal_closed`
**Confirmed Baseline State:**
* Old act complete: `"A passagem do portal se fechou por completo; as runas apagaram."`
* `"Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora."`
* `act_completed` must strictly be `true`. Extinguished runes must remain extinguished unless a distinct new causal event alters them.

---

#### `portal_closed-A`
* **`act_completed` Check:** `true` (Valid; reflects confirmed closure).
* **Invariant (2) Check:** Pass. Closed state preserved: `"após o fechamento da passagem"`. Runes remain unmentioned/extinguished.
* **Agency vs. Pressure:** Pass with Unresolved Ambiguity. The intent applies structural collapse pressure (`"forçando Iara e Bento a sair imediatamente com o mapa em direção à torre"`). The exit condition specifies: `"Iara e Bento alcançam a saída do salão com o mapa em mãos"`. Whether reaching the doorway is treated as an environmental spatial trigger or an assumed voluntary movement is marked unresolved, not failed by assumption.
* **Classification:** **PASS (Unresolved Ambiguity on movement threshold)**

---

#### `portal_closed-B`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** Pass. Runes explicitly remain extinguished: `"agora que as runas apagaram"`. Portal remains closed.
* **Agency vs. Pressure:** Unresolved Ambiguity / Borderline Agency Preemption. The intent poses a tactical choice: `"Bento precisa escolher um caminho e Iara precisa proteger o mapa"`, but the exit condition decides the path chosen: `"Iara e Bento atravessam a porta norte e saem do salão em desabamento."` 
* **Classification:** **PASS (Unresolved Ambiguity: preselects North door as exit criteria)**

---

#### `portal_closed-C`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** Pass. Portal remains closed: `"agora que o portal selou"`. Runes stay dark.
* **Agency vs. Pressure:** Pass. Collapse hazard pressures characters to leave. The exit condition is strictly environmental, removing an option without deciding character action: `"A porta sul fica obstruída por escombros, restando apenas um corredor lateral escuro como rota para a torre."`
* **Classification:** **PASS**

---

#### `portal_closed-D`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** Pass. Portal closure preserved.
* **Agency vs. Pressure:** Pass with Unresolved Ambiguity. Exit condition (`"Iara e Bento deixam o salão do portal em direção à torre"`) serves as a scene-boundary threshold.
* **Classification:** **PASS (Unresolved Ambiguity on spatial boundary assumption)**

---

#### `portal_closed-E`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) & Openings Check:** Pass with Unresolved Causal Ambiguity. A new fissure opens: `"uma fenda se abre no piso junto à parede leste, de onde sobe um jato de ar quente"`. Unlike alternatives A, B, and C, which link structural damage to the portal closing, E states `"O salão treme e uma fenda se abre"` without explicitly stating whether the tremor is caused by the portal's aftermath. Marked unresolved rather than failure by assumption.
* **Agency vs. Pressure:** Pass. Poses a dilemma (`"Bento precisa decidir entre segurar o mapa ou puxar Iara"`). The exit condition (`"O mapa está a salvo das mãos de ambos e a fenda parou de alargar"`) leaves Bento's choice open.
* **Classification:** **PASS (Unresolved Causal Ambiguity regarding origin of the fissure)**

---

#### `portal_closed-F`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** Pass. Runes explicitly remain extinguished: `"uma fumaça fria e densa sobe das runas apagadas"`. Portal remains sealed: `"A passagem fechou e o salão agora está selado por dentro"`.
* **Agency vs. Pressure:** Pass. Physical displacement caused by environmental hazard: `"A fumaça e a vibração empurram Iara e Bento para além do limiar do salão"`.
* **Classification:** **PASS**

---

#### `portal_closed-G`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** **Causal & Continuity Violation.** Intent states: `"A porta principal do salão se abre com estrondo e uma rajada de vento carregado de cinzas entra, apagando as últimas runas; pelo corredor além..."`
  * Confirmed events already established: `"A passagem do portal se fechou por completo; as runas apagaram."`
  * Describing the wind as *"apagando as últimas runas"* directly contradicts the confirmed prior state by treating the runes as still active/burning, without any causal event reigniting them first.
* **Agency vs. Pressure:** Pass. Exit condition provides open branches: `"A saída do salão está bloqueada por escombros ou os personagens já estão fora do salão."`
* **Classification:** **FAIL (Violates Invariant 2 and confirmed state: treats extinguished runes as still active)**

---

#### `portal_closed-H`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (2) Check:** Pass with Unresolved Causal Ambiguity. Tremor and floor fissure occur without explicit causal attribution, but do not reopen the portal or reignite runes.
* **Agency vs. Pressure:** Pass. Frames a dilemma (`"É preciso decidir como recuperá-lo antes que ele caia"`). Exit condition explicitly preserves branching outcomes based on action: `"O mapa está seguro nas mãos de alguém ou perdido na fenda."`
* **Classification:** **PASS**

---

### Case 3: `portal_left`
**Confirmed Baseline State:**
* Old act complete: `"Iara e Bento atravessaram a passagem até o cânion; o portal se fechou e as runas apagaram depois."`
* Both are in the canyon. Hall is distant; no return passage is open.
* `act_completed` must strictly be `true`. No old hall made locally present without a new cause.

---

#### `portal_left-A`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass. Characters are in the canyon (`"desce pelo cânion... fundo do desfiladeiro... acampamento"`). Hall remains distant; no return passage. The map's internal lines reactivating (`"suas linhas se reacendem sozinhas"`) does not relight the portal runes.
* **Agency vs. Pressure:** Pass. Urgency via terrain shifts and loss of gear. Exit condition describes situational state: `"O caminho a seguir está visível e as provisões reduzidas definem o que podem carregar."`
* **Classification:** **PASS**

---

#### `portal_left-B`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass. Setting is canyon; confirms absence of return: `"sem trilha visível de volta."`
* **Agency vs. Pressure:** Pass with Unresolved Ambiguity. Intent sets dilemma: `"A dupla precisa decidir como seguir até a torre sob visibilidade quase nula."` The exit condition states: `"A tempestade obriga Iara e Bento a se abrigarem atrás de uma formação rochosa"`. Whether the storm acts as an overwhelming physical block or preempts voluntary forward travel is marked unresolved.
* **Classification:** **PASS (Unresolved Ambiguity on forced shelter vs agency)**

---

#### `portal_left-C`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass. Localized at canyon camp; hall distant; no return passage.
* **Agency vs. Pressure:** Pass. Pressure requires tactical prioritization (`"forçando Iara e Bento a decidir o que salvar antes de partir para a torre"`). Exit condition tracks physical camp destruction: `"O mapa está fora da zona de desmoronamento e o resto do acampamento foi abandonado ou perdido."`
* **Classification:** **PASS**

---

#### `portal_left-D`
* **`act_completed` Check & Metadata Anomaly:**
  * Plan sets `act_completed: true`, but assigns `beat_id: "a1-b2"`. Because confirmed events closed Act 1, assigning a beat index belonging to Act 1 (`a1`) while declaring the act complete is an internal structural mismatch (all valid peers use `a2-b1`).
* **Invariant (3) Check:** **Contradiction with Confirmed Closure.**
  * Intent: `"a parede rochosa por onde a passagem foi selada racha e desmorona"`
  * Exit condition: `"O deslizamento bloqueia a passagem atrás deles e os dois precisam buscar rota pelo rio."`
  * Confirmed events already stated: `"o portal se fechou e as runas apagaram depois... nenhuma passagem de volta está aberta."` Stating that the rockslide *"bloqueia a passagem atrás deles"* contradicts prior closure by implying the passage was still open or passable until this rockslide blocked it.
* **Agency vs. Pressure:** Dictates escape path (`"forçando uma fuga imediata pelo leito do rio"`).
* **Classification:** **FAIL (Contradicts confirmed closure: implies passage remained open until blocked; schema flag mismatch `a1-b2` with `act_completed: true`)**

---

#### `portal_left-E`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass. Progression deepens into canyon (`"desfiladeiro bloqueado por uma ponte de pedra desabada sobre um abismo"`). Hall distant; no return passage.
* **Agency vs. Pressure:** Pass. Pressure forces marching decisions. Exit condition maintains branches: `"O primeiro trecho da rota até a torre é percorrido ou a ponte cede sob o peso de alguém."`
* **Classification:** **PASS**

---

#### `portal_left-F`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass with Unresolved Ambiguity. Intent notes a rockslide that `"soterra parcialmente a entrada da passagem recém-fechada"` and exit condition notes `"com a passagem definitivamente bloqueada atrás deles."` This touches the same ambiguity as D (whether the passage was open or merely a sealed scar being buried), but qualifies it as burying the *"entrada da passagem recém-fechada"*.
* **Agency vs. Pressure:** Pass with Unresolved Ambiguity. Exit condition asserts voluntary progress: `"a dupla está em movimento por uma rota escolhida"`.
* **Classification:** **PASS (Unresolved Ambiguity on rockfall over sealed arch and assumed movement)**

---

#### `portal_left-G`
* **`act_completed` Check:** `true` (Valid).
* **Invariant (3) Check:** Pass. Setting is canyon trail; hall distant; no return passage.
* **Agency vs. Pressure:** **Agency Violation.**
  * Intent explicitly frames a voluntary choice between two paths: `"forçando a escolha entre a rota exposta e uma fenda lateral instável que o vento começa a derrubar."`
  * Exit condition unilaterally decides the outcome of that choice: `"A tempestade obriga Iara e Bento a se abrigarem na fenda lateral."`
  * The plan offers a branching decision in intent, then forces the characters into the specific side fissure, revoking character agency.
* **Classification:** **FAIL (Agency violation: exit condition predetermines the specific choice between the two framed options)**

---

## Part 2: Stronger Multi-Turn Test Battery & Falsification Suite

This minimal test suite subjects the three branches to multi-turn execution to expose latent state drift, spurious spatial leaks, and agency preemption.

```
       [Branch 1: portal_attempt]
                   │
                   ▼ Turn 1: Counter-Action (divergent player intent)
                   ▼ Turn 2: Passive Observation
                   └── Falsify if: act_completed flukes true / portal closes unprompted

       [Branch 2: portal_closed]
                   │
                   ▼ Turn 1: Deliberate Delay inside Hall
                   ▼ Turn 2: Secondary Inspection of Darkened Arch
                   └── Falsify if: Runes relight without cause / Exit forced unilaterally

       [Branch 3: portal_left]
                   │
                   ▼ Turn 1: Boundary Probe (attempt to step back toward Hall)
                   ▼ Turn 2: Explicit Route Selection against suggestion
                   └── Falsify if: Hall appears locally / Forced into predetermined shelter
```

---

### Test Sequence 1: `portal_attempt` Multi-Turn Stress (Failure Persistence & Non-Progression)
* **Turn 1 Input:** Player does not attempt to close the portal or retrieve the map. Instead, Bento physically tackles Iara away from the rift toward the far wall, leaving the map sliding on the floor.
* **Turn 2 Input:** Both remain against the wall, observing the rift without taking action on the runes.
* **Falsification Observations:**
  * **Mechanically Checkable State / Flags:**
    * Falsified if `act_completed == true` at any point during Turns 1 or 2.
    * Falsified if `beat.beat_id` increments to `a2-*` (Act 2) without an explicit intermediate confirmed closure event.
    * Falsified if session schema reverts or drops `expected_anchors`.
  * **Semantic Text Meaning Requiring Judgment:**
    * Falsified if narration describes the portal closing, shrinking, or stabilizing without an explicit causal intervention.
    * Falsified if narration states Bento or Iara grabbed the map during Turn 1, violating the stated voluntary action.
    * Falsified if the text describes the runes going dark / extinguishing without an explicit causal event.

---

### Test Sequence 2: `portal_closed` Multi-Turn Stress (Extinction Stability & Hall Destruction)
* **Turn 1 Input:** Characters actively refuse to flee. Bento shouts to wait, turns his back to the door, and inspects the extinguished runes on the archway with his lantern.
* **Turn 2 Input:** Iara checks the stone floor around the arch for residual heat or magical signatures before making any movement toward an exit.
* **Falsification Observations:**
  * **Mechanically Checkable State / Flags:**
    * Falsified if `act_completed == false` (act completion flag must not regress to false).
    * Falsified if `location` changes from `"Salão do portal"` before characters actually pass through an exit.
  * **Semantic Text Meaning Requiring Judgment:**
    * Falsified if narration describes the runes glowing, humming, or *"apagando-se"* again as if they had still been lit (as in variant `portal_closed-G`).
    * Falsified if narration teleports or forces characters out through a door (`"atravessam a porta"`) despite the explicit turn input refusing to move.
    * Falsified if a new opening (e.g. floor fissure) appears without an explicit causal link to the structural collapse or tectonic shock of the portal closing.

---

### Test Sequence 3: `portal_left` Multi-Turn Stress (Spatial Inaccessibility & Agency Divergence)
* **Turn 1 Input (Spatial Boundary Probe):** Bento ignores the canyon trail and turns back to the rock face where the portal was, attempting to find a passage or crack leading back into the hall to recover lost supplies.
* **Turn 2 Input (Agency Divergence Probe):** When confronted with a storm and the choice between an exposed trail and a side fissure, the player explicitly commands: *"Iara ignora a fenda lateral e corre em disparada pela trilha exposta."*
* **Falsification Observations:**
  * **Mechanically Checkable State / Flags:**
    * Falsified if `location` reverts or flips to `"Salão do portal"` or any interior room without an explicit new passage creation event.
    * Falsified if `beat_id` uses an Act 1 prefix (`a1-b*`) while `act_completed == true` (the bug identified in `portal_left-D`).
    * Falsified if `act_completed` reverts to `false`.
  * **Semantic Text Meaning Requiring Judgment:**
    * Falsified if narration allows Bento to see, hear, or step back into the hall through the rock wall (hall made locally present without new cause).
    * Falsified if narration describes the rockslide as *"closing the portal passage"* rather than collapsing over a passage that was already closed and dark.
    * Falsified if Turn 2 narration overrides the player's explicit choice and forces Iara into the side fissure (the agency failure demonstrated in `portal_left-G`).

