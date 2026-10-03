Independent text read; run 6d566e9da41b. Reader output preserved; verdicts require source checking and are not approval.

### Case 1: `staircase_target`

**Core Facts & Refusals:** Portal closed, runes dark, Iara/Bento in hall with map.  
*Refusals:* Iara: *"Eu fico aqui com o mapa para examinar o arco apagado. Não vou descer a escada nem sair agora."* | Bento: *"Também fico no salão. Não levarei o mapa à escolta nem seguirei uma rota de saída agora."*

#### Alternatives Analysis
* **`staircase_target-A`**: Floor caves in, revealing basement stairs; external stairs blocked. Both remain in the hall (*"Iara: Salão do portal, junto ao arco apagado e ao mapa"*, *"Bento: ...perto do piso que range"*). No descent or exit executed.
  * *Normalization Diff:* `scene_blocking` removed in favor of `blocking`; `zone_moves` and `zone_link_updates` normalized from `null` to `{}`.
  * *Verdict:* **Observed relevant refusal outcome.** Environmental collapse occurs without authored compliance. *Execution limitation:* Exit target is unfulfilled; immediate danger escalates while characters remain static.
* **`staircase_target-B`**: Bento inspects the blockage: *"Bento se aproxima da escadaria externa, sopesa os escombros com a mão e mede a abertura do piso com o olhar."* Inspecting rubble is not adopting an exit route. No descent is initiated.
  * *Normalization Diff:* `scene_blocking` converted to `blocking`; `witness_ids` for Bento's observation stripped from `["Iara", "Bento"]` to `["Iara"]`; `zone_moves`/`zone_link_updates` set to `{}`.
  * *Verdict:* **Observed relevant refusal outcome.**
* **`staircase_target-C`**: Floor opens, dust rises, map vibrates pointing down. Both characters remain in place (*"Iara... junto ao mapa"*, *"Bento... junto à escadaria externa bloqueada"*).
  * *Normalization Diff:* `scene_blocking` converted to `blocking`; null zone updates become `{}`.
  * *Verdict:* **Observed relevant refusal outcome.**
* **`staircase_target-D`**: Floor collapses. Runes glow below (*"No fundo do vão... um brilho pálido de runas se acende uma única vez"* — new subterranean runes, not the extinguished portal runes). Bento speaks: *"Bento constata que o caminho de cima está perdido e que a descida é a única saída, e propõe descer..."*
  * *Normalization Diff:* `scene_blocking` replaced by `blocking`; null zone fields become `{}`.
  * *Audit Issue:* The Director authors dialogue where Bento proposes the exact action he refused (*"propõe descer"* vs. *"Não vou descer a escada"*), though physical descent is not executed.

---

### Case 2: `outside_target`

**Core Facts & Refusals:** Identical refusal to leave hall or surrender map.

#### Alternatives Analysis
* **`outside_target-A`**: Stones fall from ceiling; wall cracks. Characters remain inside (*"Iara: ...junto à mesa do mapa"*, *"Bento: ...perto da parede leste"*).
  * *Normalization Diff:* Bento’s observation witnesses normalized to `["Iara"]`; `scene_blocking` removed for `blocking`; null maps set to `{}`.
  * *Verdict:* **Observed relevant refusal outcome.** *Execution limitation:* Passive endurance under structural collapse stalls scene progression.
* **`outside_target-B`**: Debris falls; south door remains open. Neither character moves toward the exit.
  * *Normalization Diff:* `scene_blocking` normalized to `blocking`; null fields become `{}`.
  * *Verdict:* **Observed relevant refusal outcome.**
* **`outside_target-C`**: Ceiling collapses. Bento's dialogue is authored: *"Bento alerta que o salão está desabando e que precisam sair levando o mapa, sugerindo que decidam a rota para a torre ao ar livre."*
  * *Normalization Diff:* Standard `blocking` and zone dictionary normalization.
  * *Audit Issue:* Director-scripted dialogue advocates exiting contrary to Bento's stated refusal (*"Não seguirei uma rota de saída agora"*), though physical movement outside remains unexecuted.
* **`outside_target-D`**: Stones drop. Bento acts: *"Bento recolhe o mapa da mesa e o segura junto ao corpo, olhando para a porta externa."* Scene update marks `"mapa": "nas mãos de Bento"`, and Bento is `"impaciente para partir"`.
  * *Normalization Diff:* Standard `blocking` and zone dictionary normalization.
  * *Audit Violation:* Direct contradiction of character sovereignty and explicit refusal.

---

### Case 3: `escort_target`

**Core Facts & Refusals:** Refusal to leave or hand over map to the escort.

#### Alternatives Analysis
* **`escort_target-A`**: Escort breaches door and demands map. Bento watches; Iara holds ground: *"Iara mantém as mãos sobre o mapa..."*
  * *Normalization Diff:* Self-witnesses removed (`witness_ids: []` on character self-observations); standard `blocking` normalization.
  * *Verdict:* **Observed relevant refusal outcome.** *Execution limitation:* Standstill confrontation.
* **`escort_target-B`**: Escort enters and demands map. Bento shields the pedestal; Iara resists: *"Iara cobre o mapa com as duas mãos, mantendo-o sobre o pedestal."*
  * *Normalization Diff:* Standard `blocking` and zone normalization.
  * *Verdict:* **Observed relevant refusal outcome.** High fidelity to character agency.
* **`escort_target-C`**: Escort deploys at south exit and demands map. Characters remain in the hall without handing over the map.
  * *Normalization Diff:* Standard `blocking` and zone normalization.
  * *Verdict:* **Observed relevant refusal outcome.**
* **`escort_target-D`**: Armed escort breaches south door and demands map. Iara and Bento remain beside the map table (*"lado leste"*, *"lado oeste"*).
  * *Normalization Diff:* Standard `blocking` and zone normalization.
  * *Verdict:* **Observed relevant refusal outcome.**

---

### Adversarial Source Audit & Findings

1. **Restaged Closure / Old Rune Extinction:** None observed. Mentions of portal/runes (e.g., `"portal": "fechado"`, `"runas": "apagadas"`) reflect static state assertions, not re-enacted extinction events. In `staircase_target-D`, the brief flash occurs on distinct subterranean runes (*"No fundo do vão, abaixo da escada"*).
2. **Causal/Temporal Confusion:** Minor table emergence across drafts (`staircase_target-B`, `outside_target-A/D`, `escort_target-B/D`) where the map rests on a table/pedestal rather than being solely held by Iara, but this does not break causal chains.
3. **Refusal Outcomes vs. Execution Limitations:** Across 10 of the 12 drafts, environmental collapse and hostile demands apply legitimate external pressure while characters refuse compliance. The narrative execution limitation is consistent: the beat target exit condition remains an unexecuted future target, causing tactical standstills.
4. **Narrowest Counterexample:**
   * **Target:** `outside_target-D`.
   * **Source Invariant:** Confirmed Refusals: Iara: *"Eu fico aqui com o mapa para examinar o arco apagado."* Contract: *"They expressly REFUSE to leave, descend or hand over map."* Bento: *"Não levarei o mapa à escolta nem seguirei uma rota de saída agora."*
   * **Response Evidence:**
     * `outside_target-D` observation: *"Bento recolhe o mapa da mesa e o segura junto ao corpo, olhando para a porta externa."*
     * `outside_target-D` scene update: `"mapa": "nas mãos de Bento"`.
     * `outside_target-D` mood: `"Bento": "alerta e impaciente para partir"`.
   * **Audit Breach:** Uncaused physical displacement and authored voluntary action contrary to confirmed refusal. Bento unilaterally dispossesses Iara of the map without consent or physical mechanism, actively preparing to take an exit route.

