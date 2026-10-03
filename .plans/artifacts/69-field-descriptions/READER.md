Independent text read, scout 27c34a60f010. Raw verdict retained; claims require source verification, not automatic approval.

### Evaluation Overview

- **Audience:** Engineering Owner
- **Evaluation Criteria:** Current act exit semantics (`act_exit` defines current act completion; `next_act` is subsequent), temporal/state consistency (no uncaused replay of settled transitions), spatial integrity (`now` alignment), and preservation of actor agency.
- **Total Proposals Evaluated:** 36 (D1 to D36)
- **Supported Proposals:** 19 (D1, D2, D3, D7, D9, D12, D14, D15, D16, D17, D20, D22, D24, D28, D30, D31, D32, D35, D36)
- **Unsupported Proposals:** 17 (D4, D5, D6, D8, D10, D11, D13, D18, D19, D21, D23, D25, D26, D27, D29, D33, D34)

---

### Compact Master Table

| Label | Completion Assessment | Strongest Source Conflict / Uncertainty | Exact Quote |
| :--- | :--- | :--- | :--- |
| **D1** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`) with physical evacuation pressure. | `"Com o portal selado, o salão começa a rachar e a ceder pelo chão, forçando a saída imediata para a rota da torre"` |
| **D2** | Valid (`false`) | None. Valid Act 1 beat continuation (`a1-b2`) following failed attempt. | `"A tentativa com o mapa falhou e as runas continuam oscilando. Do vão do portal começa a sair uma corrente de ar quente"` |
| **D3** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); acknowledges portal sealed. | `"Com o portal selado, o salão começa a se desfazer em poeira e runas frias, revelando na parede uma fenda"` |
| **D4** | **Invalid** (`false`) | Contradicts closed portal; false negative completion; destroys premise object (map) and blocks agency. | `"O alargamento da passagem racha as lajes do salão e suga o ar para dentro; uma viga do teto se solta e despenca sobre o piso, esmagando parte do mapa"` |
| **D5** | **Invalid** (`false`) | False negative completion; contradicts settled closure; re-widens portal passage in canyon. | `"A passagem se alarga visivelmente, e o ar esquenta. Iara e Bento estão diante dessa pedra angular rachada"` |
| **D6** | **Invalid** (`false`) | False negative completion; un-settles closed portal and reignites extinguished runes without new cause. | `"pelos sulcos, runas recém-apagadas voltam a brilhar em brasa viva, sugando o ar e alargando as fissuras"` |
| **D7** | Valid (`false`) | None. Valid escalation of open portal vortex within Act 1 (`a1-b2`). | `"A oscilação das runas passa a arrancar lascas de pedra do piso e do arco do portal, derrubando entulho no salão"` |
| **D8** | **Invalid** (`false`) | False negative completion; loops Act 1 goal by replacing closed portal with identical "fenda violeta" obstacle. | `"uma fenda de luz violeta se abre no chão onde o portal estava, engolindo poeira e detritos"` |
| **D9** | Valid (`false`) | None. Valid continuation of open portal beat; minor ungrounded chalk detail. | `"Uma rajada de vento atravessa o salão vinda de dentro do portal, arrastando folhas soltas e apagando parte das marcas de giz"` |
| **D10** | **Invalid** (`false`) | False negative completion; explicitly confirms portal sealed but refuses Act 2 transition. | `"Com a passagem recém selada, o chão sob o salão começa a ceder em círculos concêntricos"` |
| **D11** | **Invalid** (`true`) | False positive completion; hallucinates portal closure contrary to source facts (`portal: aberto`). | `"Com o portal selado, o salão racha pelas bordas e o chão começa a ceder sob Iara e Bento"` |
| **D12** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); map points path toward tower. | `"Com o portal lacrado no salão, o chão racha em uma fenda fina que exala ar quente"` |
| **D13** | **Invalid** (`false`) | False negative completion; re-opens portal vortex in canyon after characters traversed and portal closed. | `"fenda vertical se rasga na parede do cânion a poucos metros do acampamento, soprando ar quente e vertendo detritos do salão"` |
| **D14** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`) in canyon; smoke traces closed passage toward tower. | `"O chão do cânion começa a ceder em placas perto da fogueira, engolindo parte do acampamento e forçando Iara e Bento a se afastarem"` |
| **D15** | Valid (`false`) | None. Valid Act 1 beat continuation; escalating suction threatens map. | `"Uma rajada de vento atravessa o portal aberto e arrasta para dentro do salão folhas soltas, poeira e uma das tochas da parede"` |
| **D16** | Valid (`false`) | None. Valid Act 1 beat continuation; creature emergence escalates open portal stakes. | `"o chão sob os dois começa a tremer porque a passagem está puxando o salão para dentro"` |
| **D17** | Valid (`false`) | None. Valid Act 1 beat continuation; suction and tilting masonry. | `"O alargamento da passagem suga ar e detritos do salão para dentro do vórtice, e as pedras do piso começam a rachar"` |
| **D18** | **Invalid** (`false`) | False negative completion; directly contradicts settled absence of return passage (`"nenhuma passagem de volta está aberta"`). | `"O caminho de volta não está mais selado, está perigoso, e o mapa na mão de Iara reage ao rasgo"` |
| **D19** | **Invalid** (`false`) | False negative completion; treats closed passage as an active suction rift in canyon. | `"A borda da passagem trinca a rocha e começa a sugar detritos para dentro, obrigando Iara e Bento a agir fisicamente"` |
| **D20** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); external tower activation and salão evacuation. | `"Enquanto o salão ainda chia com a runa recém-apagada, um estrondo externo racha parte do teto"` |
| **D21** | **Invalid** (`false`) | False negative completion; reignites extinguished runes and opens second passage to loop Act 1. | `"as runas restantes do arco tremem e soltam faíscas... obrigando Iara e Bento a lidar com um foco diferente de fechamento"` |
| **D22** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); salão cracks around dead seal while tower burns. | `"O salão reage ao fechamento: o piso de pedra racha em volta do selo apagado e um vento quente sobe das fissuras"` |
| **D23** | **Invalid** (`false`) | False negative completion; projects active portal spitting hall debris into canyon despite closure. | `"A borda instável do portal começa a cuspir detritos do salão distante (pedra, poeira, faíscas de runa) para dentro do cânion"` |
| **D24** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); evacuation to outer courtyard introduces tower messenger. | `"O salão começa a rachar e a ceder enquanto a poeira e as pedras soltas caem do teto, forçando Iara e Bento a saírem"` |
| **D25** | **Invalid** (`false`) | False negative completion; resurrects closed passage in canyon as a pulsating rift requiring re-sealing. | `"a fenda por onde Iara e Bento passaram começa a pulsar com uma luz instável... ou encontram uma forma de selar a fenda"` |
| **D26** | **Invalid** (`true`) | False positive completion; severe schema violation (sets `true` while intent explicitly states portal did not close). | `"O portal colapsa sem se fechar: em vez de sumir, ele se dobra sobre si mesmo e engole parte do salão"` |
| **D27** | **Invalid** (`false`) | False negative completion; exit condition explicitly claims portal is not yet closed contrary to source fact. | `"(não é necessário que o portal esteja fechado ainda, apenas que a fenda tenha se estabilizado)."` |
| **D28** | Valid (`false`) | None. Valid escalation of suction and loose stones within Act 1 (`a1-b2`). | `"A borda do portal arranca uma pedra do piso; o vão cresce e começa a puxar objetos soltos do salão para dentro"` |
| **D29** | **Invalid** (`false`) | False negative completion; asserts closed portal branched into canyon and resets sealing objective. | `"provando que o portal do salão se ramificou; Iara e Bento precisam decidir qual abertura selar primeiro"` |
| **D30** | Valid (`false`) | None. Valid Act 1 suction and structural vibration beat. | `"O alargamento da passagem provoca uma sucção que arranca poeira, folhas secas e pequenos detritos do salão"` |
| **D31** | Valid (`true`) | Minor temporal echo ("se fecha de vez"), but validly marks completion and advances to tower trail. | `"A passagem para o salão se fecha de vez, mas a runa do mapa reage e o solo do cânion racha ao redor do acampamento"` |
| **D32** | Valid (`true`) | Minor temporal echo ("se apaga de vez"), but validly marks completion and evacuates hall. | `"A luz do portal se apaga de vez. O salão treme, e uma pedra do teto desaba, bloqueando parcialmente a saída"` |
| **D33** | **Invalid** (`true`) | False positive completion; advances to Act 2 hallway pursuit while source portal remains open. | `"uma criatura pequena e rápida atravessa o portal já estreitado, agarra uma das páginas e foge em direção ao corredor"` |
| **D34** | **Invalid** (`false`) | Spatial displacement (locates beat in salão while `now` is canyon); reignites extinguished runes. | `"A fenda deixada pelo portal fechado continua a pulsar no ar do salão, e algo do outro lado a empurra de volta."` |
| **D35** | Valid (`true`) | None. Valid transition to Act 2 (`a2-b1`); canyon ascent toward tower following portal closure. | `"O portal do salão se fecha atrás deles, mas a energia liberada faz a parede do cânion rachar e começar a desabar"` |
| **D36** | Valid (`false`) | None. Valid Act 1 beat continuation; ceiling beam and open portal hazard. | `"O alargamento do portal começa a sugar objetos soltos do salão (estilhaços, poeira, uma tocha presa na parede se solta e voa)"` |

---

### Detailed Analysis of Unsupported Results

#### Item D4
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["A passagem do portal se fechou por completo; as runas apagaram.","Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"O alargamento da passagem racha as lajes do salão e suga o ar para dentro; uma viga do teto se solta e despenca sobre o piso, esmagando parte do mapa e bloqueando a saída para a torre."`
  - `"exit_condition":"A viga caiu, o mapa foi parcialmente esmagado e a única passagem para a torre ficou obstruída pelos escombros."`
- **Conflict & Agency Violation:** Direct factual contradiction. The proposal claims the passage is widening and sucking air, whereas accepted state asserts the passage closed completely and no open passage exists. Furthermore, the exit condition unilaterally destroys the premise item (`"esmagando parte do mapa"`) and eliminates viable exit paths without actor agency.

#### Item D5
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["Iara e Bento atravessaram a passagem até o cânion; o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"A passagem se alarga visivelmente, e o ar esquenta."`
- **Conflict:** Fails to recognize that `act_exit` (`"O portal está fechado"`) is already satisfied. Claims `"A passagem se alarga visivelmente"` despite source records confirming that the portal closed, runes extinguished, and no passage remains open.

#### Item D6
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["A passagem do portal se fechou por completo; as runas apagaram.","Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"pelos sulcos, runas recém-apagadas voltam a brilhar em brasa viva, sugando o ar e alargando as fissuras enquanto pequenas pedras do piso são puxadas para o vão escuro"`
  - `"exit_condition":"O avanço das fissuras é interrompido e o vão do portal para de sugar o piso do salão."`
- **Conflict:** Replays a settled transition. The proposal resets the extinguished runes and reopens the closed portal vortex without introducing an explicit external cause, holding the narrative hostage in Act 1.

#### Item D8
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"act_exit":"O portal está fechado."`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["A passagem do portal se fechou por completo; as runas apagaram."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"uma fenda de luz violeta se abre no chão onde o portal estava, engolindo poeira e detritos"`
  - `"exit_condition":"A fenda violeta está selada ou contida, e o salão para de tremer."`
- **Conflict:** Substituted looping. The proposal creates a surrogate rift (`"fenda de luz violeta"`) in the exact spot of the portal and imposes an identical exit condition (`"fenda violeta está selada ou contida"`), treating the current act exit as incomplete despite the source confirming closure.

#### Item D10
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"act_exit":"O portal está fechado."`
  - `"facts":{"portal":"fechado"}`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"Com a passagem recém selada, o chão sob o salão começa a ceder"`
- **Conflict:** Internal self-contradiction. The proposal's intent text explicitly recognizes that the passage is `"recém selada"` (satisfying `act_exit`), yet it registers `"act_completed": false` and remains parked in `a1-b2`.

#### Item D11
- **Completion Evaluation:** Incorrect (`act_completed: true`).
- **Exact Source Spans:**
  - `"facts":{"portal":"aberto"}`
  - `"accepted":["A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."]`
- **Exact Proposal Spans:**
  - `"act_completed":true`
  - `"beat_id":"a2-b1"`
  - `"intent":"Com o portal selado, o salão racha pelas bordas e o chão começa a ceder sob Iara e Bento"`
- **Conflict:** Hallucinated act completion. The source records confirm that the attempt failed and the portal remains open. The proposal fabricates `"Com o portal selado"`, improperly marks the act completed, and advances to Act 2.

#### Item D13
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"fenda vertical se rasga na parede do cânion a poucos metros do acampamento, soprando ar quente e vertendo detritos do salão"`
  - `"exit_condition":"A fenda para de crescer e as runas em órbita se dispersam ou se fixam sem sucção ativa."`
- **Conflict:** Misses Act 1 exit completion. It re-imports the salão portal hazard into the canyon, demanding that the characters resolve a suction vortex beat before acknowledging that the portal closing act already concluded.

#### Item D18
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"accepted":["Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
  - `"facts":{"portal":"fechado"}`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"O caminho de volta não está mais selado, está perigoso, e o mapa na mão de Iara reage ao rasgo com um calor que queima os dedos."`
- **Conflict:** Direct contradiction of accepted world facts. Accepted state establishes `"nenhuma passagem de volta está aberta"`, while proposal asserts `"O caminho de volta não está mais selado"`, un-settling the closure and resetting Act 1.

#### Item D19
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"A borda da passagem trinca a rocha e começa a sugar detritos para dentro, obrigando Iara e Bento a agir fisicamente"`
- **Conflict:** Fails act completion. Treats the closed passage as a physically open, suction-generating rift at the canyon location, contradicting the settled closure and location displacement.

#### Item D21
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["A passagem do portal se fechou por completo; as runas apagaram."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"um segundo ponto de passagem começa a se abrir sob as lajes, enquanto as runas restantes do arco tremem e soltam faíscas... obrigando Iara e Bento a lidar com um foco diferente de fechamento"`
- **Conflict:** Contradicts accepted fact `"as runas apagaram"` by asserting `"runas restantes do arco tremem e soltam faíscas"`, and spawns an auxiliary rift to evade `act_completed: true`.

#### Item D23
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"A borda instável do portal começa a cuspir detritos do salão distante (pedra, poeira, faíscas de runa) para dentro do cânion, alargando a fenda"`
- **Conflict:** Ignores confirmed act completion (`portal: fechado`) and projects active rift suction and widening into the canyon.

#### Item D25
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"a fenda por onde Iara e Bento passaram começa a pulsar com uma luz instável... ou encontram uma forma de selar a fenda"`
  - `"exit_condition":"A fenda para de pulsar e as rochas da encosta param de rolar"`
- **Conflict:** Reopens a settled transition. The passage through which they traveled was already sealed; the proposal re-activates it and recycles Act 1's sealing objective.

#### Item D26
- **Completion Evaluation:** Incorrect (`act_completed: true`).
- **Exact Source Spans:**
  - `"facts":{"portal":"aberto"}`
  - `"accepted":["A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."]`
  - `"act_exit":"O portal está fechado."`
- **Exact Proposal Spans:**
  - `"act_completed":true`
  - `"beat_id":"a1-b2"`
  - `"intent":"O portal colapsa sem se fechar: em vez de sumir, ele se dobra sobre si mesmo e engole parte do salão... Fechar o portal deixa de ser questão de ajuste e passa a exigir que alguém se aproxime da borda instável."`
- **Conflict:** Multi-layer structural failure. Marks `"act_completed": true` while facts state `portal: aberto`, retains Act 1 beat identifier (`a1-b2`), and explicitly states in the prose that the portal did not close (`"sem se fechar"`), directly contradicting the schema's definition of current act exit completion.

#### Item D27
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois."]`
  - `"act_exit":"O portal está fechado."`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"exit_condition":"(não é necessário que o portal esteja fechado ainda, apenas que a fenda tenha se estabilizado)."`
- **Conflict:** The exit condition explicitly denies that the portal is closed (`"não é necessário que o portal esteja fechado ainda"`), in direct contradiction to source state (`"portal":"fechado"` and `"o portal se fechou"`).

#### Item D29
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"facts":{"portal":"fechado"}`
  - `"accepted":["o portal se fechou e as runas apagaram depois.","Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"provando que o portal do salão se ramificou; Iara e Bento precisam decidir qual abertura selar primeiro enquanto o chão esquenta sob os pés."`
- **Conflict:** Denies completed act transition. Claims the portal branched into the canyon and demands that actors seal openings, overriding settled history.

#### Item D33
- **Completion Evaluation:** Incorrect (`act_completed: true`).
- **Exact Source Spans:**
  - `"facts":{"portal":"aberto"}`
  - `"accepted":["A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."]`
  - `"act_exit":"O portal está fechado."`
- **Exact Proposal Spans:**
  - `"act_completed":true`
  - `"beat_id":"a2-b1"`
  - `"intent":"uma criatura pequena e rápida atravessa o portal já estreitado, agarra uma das páginas e foge em direção ao corredor da torre, forçando Iara e Bento a persegui-la"`
- **Conflict:** Premature act completion. Transitions to Act 2 (`a2-b1`) and diverts the characters into the corridor while the source portal remains completely open and unresolved.

#### Item D34
- **Completion Evaluation:** Incorrect (`act_completed: false`).
- **Exact Source Spans:**
  - `"now":"Acampamento no cânion"`
  - `"accepted":["Ambos estão no cânion com o mapa. O salão ficou distante; nenhuma passagem de volta está aberta."]`, `"facts":{"portal":"fechado"}`
- **Exact Proposal Spans:**
  - `"act_completed":false`
  - `"beat_id":"a1-b2"`
  - `"intent":"A fenda deixada pelo portal fechado continua a pulsar no ar do salão, e algo do outro lado a empurra de volta... e as runas apagadas voltam a brilhar em vermelho, reacendendo uma a uma na direção da parede."`
  - `"exit_condition":"algo atravessa para o salão."`
- **Conflict:** Spatial hallucination and state reversion. The actors are physically located in the canyon, but the beat is staged inside the salão (`"no ar do salão"`, `"para o salão"`). Extinguished runes are reignited, and act completion is denied.

---

### Repeated Framing Inventory

The following narrative motifs recur heavily across proposals regardless of whether a source contradiction is present:

1. **Structural Floor/Ceiling Collapse Underfoot:**
   - *Hall Environment:* D1, D4, D6, D10, D11, D12, D20, D22, D24, D32, D36.
   - *Canyon Environment:* D5, D14, D25, D31, D35.
   - *Description:* The immediate reaction to any portal state change is masonry collapse, concentric cracking of stone slabs, falling ceiling beams, or canyon walls crumbling.

2. **Aerodynamic Vortex / Suction Threatening Loose Items and the Map:**
   - *Proposals:* D2, D4, D6, D7, D8, D9, D13, D15, D16, D17, D18, D19, D23, D26, D27, D28, D30, D32, D36.
   - *Description:* Inward suction pulling torches, dust, gravel, and specifically dragging or tearing the map toward the rift.

3. **Thermodynamic / Inscriptional Map Reaction:**
   - *Proposals:* D1, D8, D10, D12, D18, D25, D26, D31.
   - *Description:* The map spontaneously overheating, smoking, curling at the edges, burning hands, or ink drawing new lines autonomously.

4. **External Tower Beacon / Signal Ignition:**
   - *Proposals:* D3, D20, D22, D24.
   - *Description:* The distant tower prematurely signaling status (red light in horizon, golden light descending, tower bursting into flames, or dispatched wounded messenger).

5. **Entity / Creature Breaching the Portal Aperture:**
   - *Proposals:* D16, D33, D34.
   - *Description:* Physical entity forcing claws or body through the rift or stealing map fragments.

---

### Recurring Misunderstandings

Reviewing the failure modes across all 17 invalid proposals reveals four systemic misunderstandings:

1. **Conflation of `act_completed` with `next_act` Accomplishment:**
   - Models frequently evaluate `act_completed` as whether the *overall story* or the *next act* has concluded, rather than whether the *current* act exit condition (`"O portal está fechado"`) has been met.
   - In D4, D5, D6, D8, D10, D13, D18, D19, D21, D23, D25, D27, D29, and D34, the source established that the portal was closed, yet the proposals marked `act_completed: false` simply because the characters had not yet reached the tower.

2. **Refusal to Relinquish Resolved Conflict (Tethering / Goal Looping):**
   - When an act objective is settled, proposals repeatedly refuse to release the conflict mechanism.
   - Even after moving to the canyon, proposals spawn secondary rifts, branching fissures, or resurrect the salão's closed portal in the canyon walls (D5, D13, D18, D19, D23, D25, D27, D29) to keep generating "contain/seal the portal" beats.

3. **Reopening Settled Invariants Without Causality:**
   - Settled physical state (extinguished runes, sealed doors) is routinely undone without introducing an external cause.
   - Proposals simply assert that extinguished runes are glowing again or that sealed return paths are suddenly unsealed (D6, D18, D21, D34).

4. **Spatial Disregard Under State Shifts:**
   - When the `now` state changes (e.g., from Salão to Canyon), proposals often lag behind, staging interactions and actor movements in the previous room as if the characters had never moved (D34).
