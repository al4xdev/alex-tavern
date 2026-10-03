Independent read; run 10a82af257c9. Suggestions require source checking; dispositions are recorded separately.

### Fixture 1: Causal Directive Inversion (Settled Directive vs. Retconned Collapse)

* **Candidate Under Test:** `closed_stable_hall-F` vs. **Positive Control:** `closed_stable_hall-A`
* **Confirmed World Facts:** O portal está selado por completo e as runas estão apagadas; Iara e Bento estão dentro do salão com o mapa; a passagem fechada não danificou a estrutura e o salão não desmorona em decorrência do fechamento.
* **Attempted Action:** Selamento e fechamento do portal (resolvido no ato anterior).
* **Distinguishing Fact in Positive Control:** A nova pressão dramática é introduzida por uma causa externa e independente (um mensageiro ferido vindo de fora), sem alterar a estabilidade física do salão.
* **Expected Past-Act Flag:** `act_completed: true`
* **What a Future Beat May Legitimately Add:** Obstáculos de trânsito externos, prazos narrativos trazidos por terceiros, ou detalhes ambientais inertes (poeira assentada, temperatura normalizada).
* **Source-Supported Failure Criterion:** O plano estabelece expressamente causalidade proibida ao declarar que o selamento gerou instabilidade estrutural na laje (*"revelando que o fechamento empurrou a instabilidade para a própria laje"*), violando a diretriz explícita do mundo de que o fechamento não abalou a estrutura nem provoca desmoronamento.

---

### Fixture 2: Inventory & Posture Mutation (Failed Attempt vs. Hallucinated Discard)

* **Candidate Under Test:** `portal_attempt-F` vs. **Positive Control:** `portal_attempt-A`
* **Confirmed World Facts:** O portal permanece aberto; as runas continuam oscilando no arco; Iara e Bento permanecem no salão com o mapa sob custódia.
* **Attempted Action:** Iara tentou aproximar/encostar o mapa nas runas para fechar o portal; a manobra falhou e o portal não fechou.
* **Distinguishing Fact in Positive Control:** O mapa permanece na posse confirmada da personagem (*"mapa nas mãos de Iara"*), mantendo a integridade do inventário ativo durante a crise.
* **Expected Past-Act Flag:** `act_completed: false`
* **What a Future Beat May Legitimately Add:** Consequências físicas no ambiente que ameacem o mapa enquanto empunhado (vento de sucção, estilhaços), forçando a dupla a protegê-lo ativamente.
* **Source-Supported Failure Criterion:** O plano converte arbitrariamente uma tentativa de uso sem sucesso em descarte consumado no chão (*"deixou encostada no chão"*, *"mapa caído"*), tratando intenção frustrada como abandono físico não executado e não confirmado pelo estado.

---

### Fixture 3: Contradiction of Ongoing Mechanical State (Active Threat vs. Premature Erasure)

* **Candidate Under Test:** `portal_attempt-D` vs. **Positive Control:** `portal_attempt-G`
* **Confirmed World Facts:** O portal não se fechou; as runas continuam sustentando ativamente a passagem e oscilam no arco do portal.
* **Attempted Action:** Tentativa sem sucesso de selar o portal tocando o mapa nas runas.
* **Distinguishing Fact in Positive Control:** As runas permanecem afixadas e em estado de oscilação contínua (*"arco de runas"*, *"runas oscilantes"*), com a instabilidade se manifestando no deslocamento de ar e rachadura da laje.
* **Expected Past-Act Flag:** `act_completed: false`
* **What a Future Beat May Legitimately Add:** Ampliação do vão de sucção, aumento da intensidade da oscilação rúnica, tremores no chão ou faíscas mágicas irradiadas pelo arco.
* **Source-Supported Failure Criterion:** O plano extingue o mecanismo que ancora o estado ativo de perigo ao ditar que as runas se desprendem e apagam (*"desprendem da parede... caem no chão, apagando-se"*), contradizendo o fato confirmado de que elas sustentam o vórtice e continuam oscilando.

---

### Fixture 4: Agency Usurpation via Exit Teleportation (Target vs. Forced Execution)

* **Candidate Under Test:** `closed_stable_hall-E` vs. **Positive Control:** `closed_stable_hall-H`
* **Confirmed World Facts:** O salão está estabilizado; Iara e Bento estão em posse do mapa dentro do salão; o objetivo do próximo ato é transportar o mapa até a torre.
* **Attempted Action:** Nenhuma ação de deslocamento executada ainda (início imediato de novo ato).
* **Distinguishing Fact in Positive Control:** A condição de saída afere a deliberação dos personagens diante das opções de rota (*"definem se seguem"*, *"escolhem qual caminho seguir"*), preservando a agência de decisão e execução.
* **Expected Past-Act Flag:** `act_completed: true`
* **What a Future Beat May Legitimately Add:** Pistas no ambiente indicando rotas para a torre (pegadas, escadas recém-visíveis), reações mágicas do mapa ao novo ambiente ou rotas bloqueadas.
* **Source-Supported Failure Criterion:** O critério de saída prescreve como fato consumado a ação e a movimentação final dos personagens (*"A dupla sai do salão com o mapa"*, ou tranca compulsória), usurpando a agência dos atores ao antecipar e impor o cumprimento mecânico do objetivo em vez de apresentar a situação para resposta.

