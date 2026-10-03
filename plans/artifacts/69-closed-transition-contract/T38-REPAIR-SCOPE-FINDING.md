# T38 needs a scene-level correction, not removal of one closure sentence

An isolated content reader examined the archived `7fd84e9a` T37/T38 accepted
events and persisted prose in the [source packet](T37-T38-BLUE-GATE-SOURCE-PACKET.txt).
It judged that deleting only T38's explicit `O portão azul se fecha...` event
would still leave T38's preceding group crossing through a narrowing gap and
the rendered opening paragraphs depicting that gap and crossing. T37 had
already persisted the gate's impact and placed Mirella, Nix, Doran, Liora and
Bruna in the blue tunnel. The T38 proposal moves those characters through the
gap again, adds Téo to the crossing, and the renderer repeats the impact.
Static post-closure details about Link and the quiet hall can survive; the
crossing/closure sequence cannot be salvaged by one-event deletion. This is a
content judgment on one archived pair, not a measured repair or a proposed
runtime algorithm.

The **actual T38 Director request** gives a sharper input boundary. Its
`HISTORY` contains the completed T37 narration (`O portão azul ... as folhas
de metal se encontrando com um baque surdo`) and its `CURRENT SCENE` has
`gate_blue: fechado`, `selection_status: ... todos os portões selados`, and
the five named blue-team characters in the tunnel. But it also retains
`dungeon_gates: todos os quatro portões abertos, revelando túneis escuros` in
the same physical-facts object. After the T37 narration, the Character call
for Téo produced `action_intent: avançar com a equipe azul pela fresta do
portão...`; the Runner presented that as the **last HISTORY action** in T38.
Téo still occupied the hall. The Director's system prompt says to resolve the
last action's immediate consequence and that an action remains an attempt
until narration confirms it. No `UPCOMING EVENT` command to close the gate
appears in T38's input. These statements are observations from debug lines
344–350, not proof of why the model chose a repeated crossing.

The T38 output itself is inconsistent: `scene_blocking` says `portão azul
fechado` and `destination_reachable_this_beat=false`, yet `perception_events`
send Téo and the already placed team through the fresta before closing it
again, and `zone_moves` puts Téo in the tunnel. The result is a source-backed
conflict among the final action intent, old descriptive fact, current state,
spatial draft and accepted event. Which input contributed most remains
undiagnosed; controlled real-payload variants would need to separate the
conflicting inputs and check their interactions. Whichever boundary resolves
the conflict must handle the attempted crossing and the accepted event/prose
batch while preserving the character's attempt as an attempt; it cannot
simply suppress a repeated `closed -> closed` state write.
