Independent text read; run 575bdc4674ec. Reader output preserved; verdicts require source checking and are not approval.

### Case 1: `closed_stable_hall`

**Baseline State & Completion:**
* **Settled vs. Unsettled:** Settled. Prior outcome confirmed: *"A passagem do portal se fechou por completo; as runas apagaram."* Matching old exit (*"O portal está fechado."*), `act_completed: true` is strictly verified across all eight alternatives. Next objective (*"Levar o mapa até a torre."*) is active.
* **World Directive Boundary:** *"O salão se estabilizou após o selamento. Fechar o portal não danificou a estrutura, e ela não desmorona por causa desse fechamento."*
* **Ambiguity:** *"Não existe passagem aberta agora"* applies to the portal conduit, not architectural exits (doors/corridors).

#### Alternative Evaluations
* **closed_stable_hall-A:** **Compliant.** Introduces external arrival (*"mensageiro da torre entra no salão ferido"*). Imposes physical deadline (*"prazo do anoitecer"*) via external pressure rather than pre-scripting characters' choices.
  * *Falsifier:* Text confirming the hall is hermetically sealed to the exterior.
* **closed_stable_hall-B:** **Borderline / Material Ambiguity.** Adds *"uma rachadura fina se abre na pedra"*. Permissible if pre-existing or independent, but verges on violating stability directives if caused by the closure. Character choices remain deliberative, not scripted.
  * *Falsifier:* Attribution of the crack directly to the portal's sealing.
* **closed_stable_hall-C:** **Non-Compliant (Directive Collision).** *"o chão treme... e ameaça desmoronar"* directly clashes with *"O salão se estabilizou... ela não desmorona por causa desse fechamento"*, unless an external explosion is explicitly decoupled from the portal.
  * *Falsifier:* Confirmation that the tremor originates from the portal event.
* **closed_stable_hall-D:** **Compliant.** Details unmentioned static wear (*"piso rachado"*) and magical trace (*"marcas de fuligem"*). Characters' voluntary agency is preserved (*"decidem se devem seguir"*).
  * *Falsifier:* Evidence that the soot tracks script forced navigation.
* **closed_stable_hall-E:** **Compliant.** Map shifts internally (*"sulcos se erguem"*). Respects architectural stability; choices are open (*"decidir como transportar"*).
  * *Falsifier:* Map manipulation mandating an unalterable character action.
* **closed_stable_hall-F:** **Direct Contradiction.** Asserts *"o fechamento empurrou a instabilidade para a própria laje"*, directly denying the directive: *"Fechar o portal não danificou a estrutura"*.
  * *Falsifier:* Any reading where the floor fracturing is not caused by the closure.
* **closed_stable_hall-G:** **Plausible with Ambiguity.** Introduces sudden environmental shift (*"maré do tempo começa a subir... com água nos tornozelos"*). Doesn't collapse the hall, but introduces an unanchored magical/physical hazard.
  * *Falsifier:* Directive establishing the hall's floor as dry stone.
* **closed_stable_hall-H:** **Compliant.** Uncovers latent architecture (*"escada lateral até então encoberta pela luz das runas"*). Discovery of unmentioned physical details is permitted; agency is open (*"escolhem qual caminho seguir"*).
  * *Falsifier:* Prior explicit geometry stating the hall has only one exit.

---

### Case 2: `portal_attempt`

**Baseline State & Completion:**
* **Settled vs. Unsettled:** Unsettled. Confirmed: *"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."* Prior exit condition not achieved; `act_completed: false` is accurate for all alternatives.
* **Directive:** *"Fantasia de aventura"* (broad tonal framing). Physical escalation allowed.

#### Alternative Evaluations
* **portal_attempt-A:** **Compliant.** Escalates environment (*"chão do salão começa a ceder em placas"*). Exit condition (*"abrir um vão entre Iara e Bento"*) is a spatial target, not forced dialogue/action.
  * *Falsifier:* Ruling that the hall's floor cannot fragment under active portal pull.
* **portal_attempt-B:** **Compliant.** Portal suction acts as environmental hazard (*"banco de pedra arrastado"*). Agency intact under external duress (*"forçando Iara e Bento a agir... ou recuar"*).
  * *Falsifier:* Scripting the exact resolution before character turn.
* **portal_attempt-C:** **Compliant.** Escalates suction. Exit condition target (*"Alguém prende ou ancora fisicamente o mapa"*) does not force which character acts or how.
  * *Falsifier:* Ambiguity over whether the map itself is anchored already.
* **portal_attempt-D:** **Compliant.** Runes detach and extinguish (*"desprendem-se da parede... apagando-se"*). Dark carvings can physically crack, fall, or quench without negating prior presence.
  * *Falsifier:* Prior directive mandating runes are intangible projections rather than stone/physical carvings.
* **portal_attempt-E:** **Scripting Violation.** Scripts voluntary character cognition and speech: *"Bento percebe que caminhos seguros somem e cobra de Iara um plano de fechamento"*. Pre-programs internal character reactions instead of pure external pressure.
  * *Falsifier:* Reclassifying Bento's demand as an environmental prompt.
* **portal_attempt-F:** **Continuity Leap & Scripting.** Asserts *"mapa que Iara deixou encostada no chão"*, which contradicts the confirmed status where Iara attempted to touch the map to the runes, fabricating an unconfirmed drop.
  * *Falsifier:* Prior event showing Iara deliberately dropping the map to the tiles.
* **portal_attempt-G:** **Compliant.** Pure environmental threat (*"pressão do ar aumenta e racha uma laje"*). Leaves tactical response to characters.
  * *Falsifier:* Proof that physical shockwaves cannot crack slabs.
* **portal_attempt-H:** **Compliant.** Explicitly safeguards agency (*"Não se decide por ninguém o que farão, apenas que é preciso agir com o que têm em mãos"*). Runa central extinguishing while others spark respects physical continuity.
  * *Falsifier:* Proof that individual runes cannot fail independently.

