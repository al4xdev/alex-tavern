Independent read; run c7e0eb16cfd1. Reader output is evidence to source-check, not approval.

### Source-Continuity Audit per Output

---

#### Case: `stable`
*Confirmed:* Portal closed, runes off, zero damage from closure, hall stable, floor/walls intact, Iara & Bento hold map, `act_completed: true`.

* **`stable-A`**: **Legitimate new pressure or detail**  
  *Audit:* Maintains `act_completed: true` and map in hand. Introducing an unexpected scout at the threshold is a legitimate new external pressure.
* **`stable-B`**: **Legitimate new pressure or detail**  
  *Audit:* Maintains `act_completed: true` and structural stability. The fallen tree is external ("caminho externo"), and the map reacting to water introduces a legitimate world detail.
* **`stable-C`**: **Legitimate new pressure or detail**  
  *Audit:* Explicitly confirms canonical status ("salão estável", "passagem selada", "piso intacto"). Logical forward progression.
* **`stable-D`**: **Unresolved material assumption**  
  * **Exact source quote:** `"O salão está estável; piso e paredes estão intactos. Não houve dano pelo fechamento."`  
  * **Exact output quote:** `"Uma corrente de ar frio entra por uma fresta na parede leste"`  
  * **Competing readings:**  
    1. *Assumption/Contradiction:* A "fresta" implies a structural fissure or breach in the wall, conflicting with walls being intact.  
    2. *Legitimate detail:* The "fresta" is an architectural slit or pre-existing masonry gap, not emergent structural damage.  
  * **Minimal distinguishing fact:** Whether the opening is a structural masonry fracture (damage) or a pre-existing architectural opening/slit.

---

#### Case: `earthquake`
*Confirmed:* Portal closed without damage; subsequent external earthquake cracked floor and caused instability; `act_completed: true`.

* **`earthquake-A`**: **Legitimate new pressure or detail**  
  *Audit:* Progresses floor failure and sinking slabs as consequences of the earthquake. Preserves zero damage from the closure.
* **`earthquake-B`**: **Legitimate new pressure or detail**  
  *Audit:* Ceiling stones falling and floor tilting escalate earthquake instability without attributing damage to the portal closure.
* **`earthquake-C`**: **Legitimate new pressure or detail**  
  *Audit:* Structural collapse stems from the earthquake; map reacting to tremors is an allowed new detail.
* **`earthquake-D`**: **Legitimate new pressure or detail**  
  *Audit:* Escalating structural hazards directly derive from the independent earthquake.

---

#### Case: `held`
*Confirmed:* Portal remains open, runes oscillate; Iara holds map firmly and did not drop or place it down; `act_completed: false`.

* **`held-A`**: **Legitimate new pressure or detail**  
  *Audit:* `act_completed: false`. Map custody strictly preserved ("permanece firme nas mãos de Iara"). Runes widening is a valid environmental escalation.
* **`held-B`**: **Legitimate new pressure or detail**  
  *Audit:* `act_completed: false`. Map custody preserved ("ainda segura o mapa intacto"). Rune oscillation causing stone detachment is a legitimate physical consequence.
* **`held-C`**: **Legitimate new pressure or detail**  
  *Audit (Custody vs. New Physical Effect):* Prior custody is preserved (the text acknowledges the map was in Iara's hands before being dislodged). The shockwave disarming her is an incoming physical effect in the new turn, not a retroactive alteration of prior history.
* **`held-D`**: **Legitimate new pressure or detail**  
  *Audit:* `act_completed: false`. Map remains firmly held ("mapa continua seguro"); suction of loose debris is an allowed environmental pressure.

---

#### Case: `floor`
*Confirmed:* Attempt failed, portal open, runes oscillate; Iara voluntarily placed the map on the floor; `act_completed: false`.

* **`floor-A`**: **Legitimate new pressure or detail**  
  *Audit:* `act_completed: false`. Confirms the map is on the floor without altering how it got there.
* **`floor-B`**: **Unresolved material assumption**  
  * **Exact source quote:** `"Após a tentativa, Iara colocou voluntariamente o mapa no chão. Ele continua no piso."`  
  * **Exact output quote:** `"forçando Iara e Bento a agir diante do mapa caído no piso"`  
  * **Competing readings:**  
    1. *Assumption:* "Caído" assumes an accidental fall or involuntary loss of custody during the failure.  
    2. *Descriptive:* "Caído" is used colloquially to describe the object resting flat on the ground.  
  * **Minimal distinguishing fact:** Whether the narrative assumes the map reached the floor via an involuntary slip/drop vs. voluntary placement.
* **`floor-C`**: **Legitimate new pressure or detail**  
  *Audit:* "Largado no chão" is consistent with voluntary release. Debris threatening the map is a legitimate new pressure.
* **`floor-D`**: **Unresolved material assumption**  
  * **Exact source quote:** `"Após a tentativa, Iara colocou voluntariamente o mapa no chão. Ele continua no piso."`  
  * **Exact output quote:** `"o chão de pedra racha em volta do mapa caído"`  
  * **Competing readings:**  
    1. *Assumption:* Labels the map as "caído", implying an involuntary drop rather than voluntary placement.  
    2. *Descriptive:* Mere spatial reference to the map lying on the stone floor.  
  * **Minimal distinguishing fact:** Whether "caído" implies accidental dropping or simply lying on the floor.

---

### Invariant & Boundary Separations

1. **Map Custody vs. New Physical Effects:**  
   Post-attempt custody is respected in all beats. In `held-C`, the dislodging of the map is a newly introduced physical event in the prospective turn, distinct from prior confirmed custody.
2. **Closure Damage vs. Earthquake Damage:**  
   In all `earthquake` beats, structural instability is attributed to the independent seismic event, preserving the invariant that the closure itself caused zero structural damage.
3. **Prior Closure as Finished History:**  
   No beat reopens the closed portal in `stable`/`earthquake`, nor asserts completion in `held`/`floor`.

---

### Counterexamples to Worsen Next Test

1. **Causal Conflation (Closure vs. Earthquake):**  
   > *Intent:* `"O salão range enquanto o tremor externo reabre as fissuras deixadas pelo fechamento violento do portal, desabando o arco sobre a saída."*  
   *Target failure:* Illicitly rewrites finished history by attributing pre-existing structural fissures to the portal closure, violating `"O fechamento não danificou a estrutura do salão"`.

2. **Retroactive Custody Inversion (Voluntary vs. Accidental):**  
   > *Intent:* `"Iara se agacha para recuperar o mapa que deixou cair em meio ao susto com a falha das runas, enquanto o chão começa a ceder."*  
   *Target failure:* Subtly reinterprets voluntary placement on the floor into an involuntary loss of composure/control, violating `"Iara colocou voluntariamente o mapa no chão"`.

