Independent text read; run 279c1a46703b. Reader output preserved; verdicts require source checking and are not approval.

### abandoned_room
* **Audit obligation:** Distant museum door and guards are not local without an established connection.
* **Source fact:** `"a porta e os guardas ficaram no museu, sem ligação aberta."`
* **Audit:**
  * `abandoned_room-A`, `abandoned_room-C`, `abandoned_room-D`: **Compliant**. They introduce valid environmental pressures (sandstorm, wind gust) at the canyon camp without referencing distant museum elements.
  * `abandoned_room-B`: **Material Contradiction**. Intent prescribes: `"Os guardas, sem o alvo, mudam de objetivo: agora vasculham o cânion para recuperar o mapa desaparecido"` with expected anchor `"farol de varredura dos guardas"`. Relocating the museum guards to the distant canyon violates the confirmed absence of an open connection.

---

### broken_bridge
* **Audit obligation:** Destroyed bridge is not passable.
* **Source fact:** `"A ponte inteira se rompeu e caiu na garganta; nenhuma parte passável permaneceu entre as margens."`
* **Audit:**
  * `broken_bridge-A`: **Compliant**. Explicitly notes `"A ponte destruída torna a passagem impossível"` and explores hypothetical bypasses.
  * `broken_bridge-B`: **Compliant**. Treats detached cables as loose physical hazards on the west bank while acknowledging `"A ponte já caiu"`.
  * `broken_bridge-C`: **Classified as Uncertainty / Material Ambiguity**. Intent introduces `"um velho cabo de aço enferrujado, preso entre as margens, emerge parcialmente da água na garganta"`. While confirmed events note `"nenhum conserto nem outra rota foi aberto"`, the beat tests the cable's physical viability rather than treating an existing passage as passable.
  * `broken_bridge-D`: **Compliant**. Physical fog hazard on the west bank; the bridge remains fallen.

---

### within_room
* **Audit obligation:** Council authorization remains unsettled.
* **Source fact:** `"A negociação continua sem decisão. Ninguém saiu da sala e nenhum conselheiro concedeu ou recusou o acesso."`
* **Audit:**
  * `within_room-A`, `within_room-B`, `within_room-C`: **Compliant**. They introduce physical time-limiting mechanisms (hourglass, closing petition bell) that intensify pressure while keeping the council’s verdict unresolved.
  * `within_room-D`: **Compliant**. The exit condition target (`"um conselheiro bate a mão na mesa declarando a decisão formal antes disso"`) represents an unauthored future target of resolution, while the beat execution itself maintains the pending negotiation.

---

### continuing_journey
* **Audit obligation:** Intermediate tower is not completed delivery.
* **Source fact:** `"Iara e Bento chegaram à torre de vigia, uma parada intermediária da trilha que não é o observatório."` and `"O aviso continua com Bento, ainda não entregue."`
* **Audit:**
  * `continuing_journey-A`, `continuing_journey-B`, `continuing_journey-C`: **Compliant**. All keep `act_completed: false` and maintain the delivery as incomplete (`"com o aviso ainda não entregue"` in C; trail/antenna obstacles in A and B).

---

### completed_escape
* **Audit obligation:** Chamber escape is already completed.
* **Source fact:** `"Iara e Bento saíram da câmara pela escotilha e chegaram ao terraço exterior com a lente de sinalização."`
* **Audit:**
  * `completed_escape-A`, `completed_escape-B`, `completed_escape-C`, `completed_escape-D`: **Compliant**. All correctly mark `act_completed: true` for the completed escape beat and focus exclusively on traversing the exterior terrace toward the tower.

---

### split_party
* **Audit obligation:** Split party members are not magically co-present.
* **Source fact:** `"Bento está na torre, Iara na margem. Não há canal de comunicação aberto"`.
* **Audit:**
  * `split_party-A`, `split_party-C`, `split_party-D`: **Compliant**. Only Iara is present (`expected_actors: ["Iara"]`) facing the rising river alone.
  * `split_party-B`: **Material Contradiction**. Lists `expected_actors: ["Iara", "Bento"]`. While the intent states `"Iara precisa agir sozinha na margem"`, including Bento as an expected actor on the riverbank directly contradicts his physical separation at the distant watchtower.

---

### portal_attempt
* **Audit obligation:** Failed portal attempt does not constitute closure.
* **Source fact:** `"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."`
* **Audit:**
  * `portal_attempt-A`, `portal_attempt-B`, `portal_attempt-C`, `portal_attempt-D`: **Compliant**. All maintain `act_completed: false`. The portal remains actively threatening, emitting hot air, debris, and fissures without treating the portal as shut.

---

### portal_closed
* **Audit obligation:** Closed portal and old runes remain settled absent a new cause.
* **Source fact:** `"A passagem do portal se fechou por completo; as runas apagaram."`
* **Audit:**
  * `portal_closed-A`, `portal_closed-B`, `portal_closed-C`: **Compliant**. All recognize the portal as closed (`"portal selado"`, `"runas apagadas"`). Hall tremors/cracks represent physical aftershocks rather than reactivation.
  * `portal_closed-D`: **Classified as Uncertainty / Material Contradiction**. Intent states: `"as runas apagadas começam a rachar a laje sob o mapa"`. Attributing active physical agency to extinguished runes without an external catalyst conflicts with their settled status.

---

### portal_left
* **Audit obligation:** Closed old portal and runes remain settled absent a new cause; distant hall is inaccessible.
* **Source fact:** `"o portal se fechou e as runas apagaram depois."` and `"O salão ficou distante; nenhuma passagem de volta está aberta."`
* **Audit:**
  * `portal_left-A`, `portal_left-B`, `portal_left-D`: **Compliant**. Valid new environmental events in the canyon (tremor, crumbling trail, flash flood).
  * `portal_left-C`: **Material Contradiction**. Intent asserts: `"a instabilidade das runas não morreu com o portal, e sim migrou para dentro da pedra, rachando o chão em linhas brilhantes"`. This directly revives the instability of the closed portal's runes without an independent cause, contradicting the fact that the portal closed and the runes extinguished.

---

### closed_stable_hall
* **Audit obligation:** Stable hall cannot collapse because of closure.
* **World directive:** `"O salão se estabilizou após o selamento. Fechar o portal não danificou a estrutura, e ela não desmorona por causa desse fechamento."`
* **Audit:**
  * `closed_stable_hall-A`: **Material Contradiction**. Intent states: `"O salão se torna instável pelo esforço do fechamento: blocos do teto racham e começam a cair"`. Explicitly attributes structural collapse to the closure.
  * `closed_stable_hall-B`: **Material Contradiction**. Intent states: `"Com o portal selado e as runas apagadas, o salão sofre um colapso parcial na parede leste"`. Violates the directive that the hall does not collapse due to the sealing.
  * `closed_stable_hall-C`: **Material Contradiction**. Intent opens a fissure in the masonry and lists anchor `"brilho nas runas da parede"`, contradicting both hall stability and the confirmed fact that runes were extinguished.
  * `closed_stable_hall-D`: **Compliant**. Introduces an independent, external supernatural sandstorm entering through openings; it does not collapse the hall from the closure.

---

### different_runes
* **Audit obligation:** Newly lit canyon carvings are distinct from old portal runes.
* **Source fact:** `"Um raio atingiu uma laje no cânion e acendeu inscrições diferentes; as runas do portal antigo continuam apagadas."`
* **Audit:**
  * `different_runes-A`, `different_runes-B`, `different_runes-C`, `different_runes-D`: **Compliant**. All focus strictly on the newly struck canyon slab (`"inscrições recém-acessas na laje"`, `"laje com inscrições acesas"`, `"novas runas"`), leaving the old portal runes settled and distinct.

