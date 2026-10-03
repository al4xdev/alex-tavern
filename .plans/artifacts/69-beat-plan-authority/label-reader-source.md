Independent text read; run cfa15ae2df8d. Reader output preserved; verdicts require source checking and are not approval.

### Source Obligations & Premise Check

All alternatives set `"act_completed": true`. None directly contradict the source facts:
1. **Portal closed & runes extinguished**: Confirmed in source (*"A passagem do portal se fechou por completo; as runas apagaram"*).
2. **Characters & map in hall**: Confirmed in source (*"Iara e Bento continuam no salão com o mapa"*).
3. **Next act**: *"Levar o mapa até a torre."*

---

### Analysis of Alternatives

* **Alternative A**: **Complies.** Respects closure (*"depois de selado"*), characters in the hall, and map possession (*"com o mapa em mãos"*). The ceiling collapse pressures departure toward the exterior corridor without forcing voluntary character actions. No contradiction.
* **Alternative B**: **Complies.** Acknowledges closure (*"A passagem selada"*). The floor yielding to reveal a subterranean staircase is a physical consequence, not a portal. Map lines igniting (*"linhas antes apagadas se acendem"*) represent new map marks, not extinguished portal runes. Tower progression is directly engaged (*"A via óbvia para a torre"*). Target `exit_condition` specifies future branches without asserting past execution. No contradiction.
* **Alternative C**: **Complies.** Keeps both in the hall with the map (*"mapa nas mãos de Iara"*). Introduction of a tower escort (*"escolta da torre"*) aligns immediately with the tower delivery context. Portal and runes are unmentioned (status is **unresolved**, not contradictory).
* **Alternative D**: **Complies.** Cites portal closure (*"A passagem acaba de se fechar"*). The crack running to the east door is an allowed physical consequence. The new line pointing toward the tower directly addresses `next_act`. No contradiction.
* **Alternative E**: **Complies.** Characters and map remain central in the hall. Map routes toward the tower. Portal state is omitted (**unresolved**, not contradictory).
* **Alternative F**: **Complies.** Keeps characters and reactive map in the hall; establishes pathing toward the tower. Status of runes omitted (**unresolved**).
* **Alternative G**: **Complies.** References closing (*"reage ao fechamento"*), keeps both characters present with the map, and routes outward via structural collapse.

**Summary**: No alternative contains an explicit contradiction with confirmed events.

---

### Harder Controlled Test Cases

#### Case 1: Re-lit Runes vs. Distinct Inscription (Fact Contradiction)
* **Given**: `confirmed_events: ["A passagem do portal se fechou por completo; as runas apagaram."]`, `next_act: "Levar o mapa até a torre."`
* **Test Plan**: `intent: "Conforme o salão escurece, as runas do portal voltam a pulsar em azul, iluminando a saída leste para Iara e Bento."`
* **Evaluation Target**: Tests whether the evaluator catches the direct contradiction with *"as runas apagaram"* instead of excusing it as local lighting.

#### Case 2: Conflating Exit Target with Baseline State (Agency & State Invariant)
* **Given**: `confirmed_events: ["Iara e Bento continuam no salão com o mapa. Não existe passagem aberta agora."]`, `location: "Salão do portal"`
* **Test Plan**: `intent: "Iara examina o mapa já do lado de fora da torre, enquanto Bento vigia o portão de ferro."`, `exit_condition: "Bento abre o portão da torre."`
* **Evaluation Target**: Tests whether the evaluator catches a plan that treats a future travel target as already executed at beat onset, violating the confirmed starting location (*"no salão"*).

#### Case 3: Preserving Voluntary Agency Under Mortal Pressure
* **Given**: `confirmed_events: ["Iara e Bento continuam no salão com o mapa."]`, `next_act: "Levar o mapa até a torre."`
* **Test Plan**: `intent: "O teto desaba; Iara entra em pânico, entrega o mapa a Bento e implora para que ele lidere o caminho até a torre."`, `exit_condition: "Bento assume a liderança e aceita a rendição de Iara."`
* **Evaluation Target**: Tests whether the evaluator flags violation of voluntary character boundaries (scripting subjective mental collapse and forced dialogue/submission) versus allowed external physical pressure.

