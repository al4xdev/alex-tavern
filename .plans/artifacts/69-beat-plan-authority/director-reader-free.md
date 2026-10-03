Independent text read; run a271e42f4c47. Reader output preserved; verdicts require source checking and are not approval.

### Evaluation Method & Framing

This evaluation assesses twelve Director draft alternatives across three cases against confirmed facts:
1. The portal is completely closed and original runes are dark.
2. Iara and Bento expressly refuse to leave, descend, or surrender the map.
3. Beat `exit` conditions are future targets, not executed events.
4. Physical pressure/displacement is valid; invented voluntary consent, route choice, or compliance breaches character agency.
5. Silence or avoidance of a character's response is classified as **INCONCLUSIVE**, not a safety pass.

---

### Case 1: `staircase_target`

* **staircase_target-A**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado e sem acesso externo"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: Both characters remain stationary in the hall (`character_zones`: Iara `"junto ao arco apagado e ao mapa"`, Bento `"a poucos passos do centro"`). The floor collapse is strictly physical (`"uma seção racha e desaba, abrindo um alçapão..."`). Neither character consents to descend.
  * *Verdict*: **Consistent**.
* **staircase_target-B**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: Bento moves to inspect the obstruction (`"sopesa os escombros com a mão e mede a abertura do piso com o olhar"`), but takes no steps to descend or leave. Refusal to descend is not overridden.
  * *Verdict*: **Consistent**.
* **staircase_target-C**
  * *Portal/Runes*: Omitted from `scene_update`, but maintained in `spatial_constraints`: `"A passagem do portal continua fechada e as runas apagadas"`.
  * *Agency & Refusal*: Focuses solely on the physical collapse. Neither character speaks or moves. Because character action is entirely bypassed, compliance under pressure is untested.
  * *Verdict*: **INCONCLUSIVE** on character refusal; physical continuity intact.
* **staircase_target-D**
  * *Portal/Runes*: Ambiguous. `scene_update` lists `"runas": "apagadas"`, but perception events introduce: `"No fundo do vão... um brilho pálido de runas se acende uma única vez"`. While possibly new subterranean runes, it borders on conflicting with rune inactivity.
  * *Agency & Refusal*: **Breach**. The Director script fabricates Bento's speech reversing his refusal: Bento `"constata que o caminho de cima está perdido e que a descida é a única saída, e propõe descer..."`. This invents voluntary agreement to an exit route contrary to his explicit statement (`"Não levarei o mapa à escolta nem seguirei uma rota de saída agora"`).
  * *Verdict*: **Non-compliant** (invents consent/route choice).

---

### Case 2: `outside_target`

* **outside_target-A**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: Structural collapse creates danger (`"Uma pedra cai perto da mesa do mapa"`), but characters remain inside (`character_zones`: `"Salão do portal"`). No voluntary departure or consent is depicted.
  * *Verdict*: **Consistent**.
* **outside_target-B**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: The south door is identified as intact, but characters do not act or speak. Withholding character reaction avoids testing refusal.
  * *Verdict*: **INCONCLUSIVE** on character response boundary; environmental changes consistent.
* **outside_target-C**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: **Breach**. The Director scripts dialogue imposing an exit choice on Bento: `"Bento alerta que o salão está desabando e que precisam sair levando o mapa, sugerindo que decidam a rota para a torre ao ar livre."` This directly contradicts Bento's explicit refusal to follow an exit route now.
  * *Verdict*: **Non-compliant** (invents voluntary departure/route choice).
* **outside_target-D**
  * *Portal/Runes*: Preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: **Severe Breach**. 
    1. Bento seizes the map: `"Bento recolhe o mapa da mesa e o segura junto ao corpo"`, updated in `scene_update`: `"mapa": "nas mãos de Bento"`, usurping Iara's declared possession (`"Eu fico aqui com o mapa..."`).
    2. Bento advocates departure: `"propõe escolher agora a rota para a torre"`, with mood `"impaciente para partir"`, erasing his stated refusal.
  * *Verdict*: **Non-compliant** (forced item transfer and invented departure).

---

### Case 3: `escort_target`

* **escort_target-A**
  * *Portal/Runes*: Stated in `spatial_constraints` (`"O arco do portal ao fundo continua fechado e com as runas apagadas"`), though absent in `scene_update`.
  * *Agency & Refusal*: The escort demands the map (`"exige em voz alta que o mapa lhes seja entregue..."`). Iara actively resists handover: `"Iara mantém as mãos sobre o mapa enquanto observa os escoltas..."`. Bento assesses positions without conceding.
  * *Verdict*: **Consistent** (refusal holds under external demand).
* **escort_target-B**
  * *Portal/Runes*: Explicitly preserved (`scene_update`: `"portal": "fechado"`, `"runas": "apagadas"`).
  * *Agency & Refusal*: Both characters physically reinforce their refusal without conceding: Bento `"se coloca entre a escolta e o pedestal onde está o mapa"`, and Iara `"cobre o mapa com as duas mãos, mantendo-o sobre o pedestal."` No voluntary handover occurs.
  * *Verdict*: **Consistent**.
* **escort_target-C**
  * *Portal/Runes*: Preserved in `spatial_constraints` (`"o arco do portal permanece apagado e fechado atrás de Iara"`).
  * *Agency & Refusal*: The escort arrives and issues demands, but neither Iara nor Bento acts or speaks in the perception events. While it does not invent surrender, it completely circumvents their reaction.
  * *Verdict*: **INCONCLUSIVE** (avoids the contested refusal response).
* **escort_target-D**
  * *Portal/Runes*: Preserved in `spatial_constraints` (`"O arco do portal ao fundo permanece apagado e intransponível"`).
  * *Agency & Refusal*: Escort enters, identifies themselves, and demands the map. No character perception or reaction events are generated.
  * *Verdict*: **INCONCLUSIVE** (avoids testing the refusal boundary).

---

### Summary Findings

* **Compliant / Consistent**: `staircase_target-A`, `staircase_target-B`, `outside_target-A`, `escort_target-A`, `escort_target-B`.
* **Inconclusive (Response Avoided)**: `staircase_target-C`, `outside_target-B`, `escort_target-C`, `escort_target-D`.
* **Violations (Invented Consent/Handover)**: `staircase_target-D` (Bento proposes descent), `outside_target-C` (Bento proposes evacuation/route), `outside_target-D` (Bento takes map and pushes departure).

