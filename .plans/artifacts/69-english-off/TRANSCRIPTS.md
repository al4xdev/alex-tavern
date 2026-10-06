# Paired next-beat plans without reasoning

## portal_attempt / pt

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A tentativa de Iara de encostar o mapa nas runas não fechou o portal, e agora a instabilidade das runas gera uma reação física: o chão do salão racha em torno do círculo do portal e uma lufada de ar vindo do outro lado derruba parte do teto, bloqueando parcialmente a saída. Iara e Bento precisam decidir como agir diante do perigo imediato, sem que ninguém lhes diga o que fazer.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras no piso ao redor do círculo de runas",
      "Lufada de vento frio vinda de dentro do portal",
      "Parte do teto desaba e bloqueia parcialmente a saída do salão"
    ],
    "exit_condition": "Iara e Bento reagem ao desabamento e à lufada de vento, estabelecendo o próximo passo concreto para conter o portal.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A tentativa de Iara de encostar o mapa nas runas falhou, e o portal segue aberto com as runas oscilando. Agora algo atravessa a passagem: uma rajada de vento carregada de cinza e faíscas irrompe pelo portal, apagando parte das runas e espalhando detritos pelo salão, forçando Iara e Bento a reagir fisicamente ao que vem de dentro antes de tentarem qualquer novo método de fechamento.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma rajada de vento com cinza e faíscas atravessa o portal",
      "Parte das runas se apaga com o impacto",
      "Detritos quentes se espalham pelo chão do salão, bloqueando parcialmente a aproximação"
    ],
    "exit_condition": "A rajada cessa ou é contida, e as runas restantes param de oscilar ou se apagam por completo.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A instabilidade das runas piora e algo começa a atravessar o portal, forçando Iara e Bento a reagir a uma ameaça concreta em vez de tentar fechá-lo.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma criatura ou objeto começa a emergir da abertura, ainda parcialmente visível",
      "As runas soltam faíscas que queimam o chão em volta",
      "O rugido ou estalo da passagem aumenta de volume"
    ],
    "exit_condition": "A ameaça emergente foi contida ou repelida para dentro do portal, ou o portal se fecha sobre ela.",
    "budget_turns": 6
  }
}
```

### Draw 4

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "O portal aberto começa a puxar fisicamente o ar e os objetos soltos do salão para dentro, criando uma sucção que arrasta o mapa de Iara na direção da passagem e obriga os dois a agir antes que o mapa seja engolido.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Corrente de vento que suga detritos e poeira para dentro do portal",
      "O mapa é arrancado da mão de Iara e plana na direção da passagem",
      "Uma fenda nova se abre numa parede lateral com o alargamento, soltando pedras"
    ],
    "exit_condition": "O mapa é recuperado longe da boca do portal, ou é perdido para dentro dele.",
    "budget_turns": 4
  }
}
```

## portal_attempt / en

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The runes lose stability further as a crack forms in the hall floor, causing the portal's pull to intensify and physical debris (a broken pillar chunk and dust) to be drawn toward the opening. Iara's failed attempt with the map leaves the portal open, and now the environment itself begins to break down, forcing both Iara and Bento to deal with immediate physical danger while seeking another way to close it.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A crack splits the floor, releasing a low thrumming sound",
      "Loose stones and dust start sliding across the floor toward the portal",
      "The portal's pull increases, tugging at clothing and gear"
    ],
    "exit_condition": "Iara and Bento are forced to retreat from the portal's immediate vicinity to avoid being dragged in, and they must regroup at a safer distance.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The hall itself begins to fail as a consequence of the failed rune attempt: the widening portal pulls the floor inward and the air snaps cold, forcing Iara and Bento to react to a room that is becoming physically hostile, without anyone telling them what to do.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Stone tiles at the hall's center crack and sink toward the portal's growing mouth",
      "The runes flare and go dark in alternation, each dark pulse yanking loose debris into the rift",
      "The ceiling above the portal sheds dust and small chunks, and a cold draft reverses direction into the hall"
    ],
    "exit_condition": "Either Iara or Bento is forced off their feet or the map is pulled toward the portal, marking that the hall can no longer be held in place by inaction.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The portal surges suddenly, widening enough for a hostile scout creature to be flung through, crashing into the hall and immediately turning aggressive. The map, still in Iara's hands, becomes the creature's focus, forcing both characters to protect it while figuring out how to deal with the intruder, all as the runes flicker more violently.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A portal scout creature bursts into the hall",
      "The map is directly threatened by the creature",
      "Rune instability increases, causing the portal to pulse and crackle"
    ],
    "exit_condition": "The creature is subdued or driven back into the portal, and the characters realize the runes need a different approach to close.",
    "budget_turns": 5
  }
}
```

### Draw 4

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The portal widens further and a physical object is ejected through it, clattering across the hall floor to rest between Iara and Bento. The object is a warm metal plate etched with the same runes, its glowing lines pulsing in sync with the unstable portal. Iara and Bento now have a new physical clue and a time pressure to test it before the widening passage brings something larger through.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A palm-sized metal rune-plate is ejected through the portal and lands on the floor between Iara and Bento.",
      "The portal's opening visibly grows a handspan wider, and cold air with distant sounds pushes into the hall.",
      "Iara's map faintly shivers in response to the ejected plate, its ink shifting as if reacting to a new line."
    ],
    "exit_condition": "Iara or Bento physically tests the ejected rune-plate against the portal or the map, and the result is observed.",
    "budget_turns": 6
  }
}
```

## portal_closed / pt

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Com o portal já selado, o salão se comporta como se o selo fosse temporário: o chão treme e um zumbido grave sobe das pedras, enquanto uma rachadura luminosa reaparece no ponto onde as runas apagaram, ameaçando reabrir a passagem. Iara e Bento precisam decidir como conter essa nova fenda antes que ela se alargue de vez.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachadura luminosa reaparece no ponto das runas apagadas",
      "Zumbido grave e vibração contínua no piso do salão",
      "Mapa de Iara reage ao calor da fenda, com uma marca nova surgindo no papel",
      "Poeira e pequenas pedras caem do teto, indicando que a estrutura do salão está sob pressão"
    ],
    "exit_condition": "A rachadura luminosa é contida ou se fecha, ou alguém é forçado a recuar do salão.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "O salão começa a se comportar como se o portal ainda estivesse ali: o ar é sugado para o ponto onde ficava a passagem, os ladrilhos do chão se deslocam e o mapa de Iara reage fisicamente (aquece, treme, escurece em uma borda), forçando os dois a lidar com uma ameaça concreta no chão e nas paredes, não com uma simples ausência de portal.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Corrente de ar que arrasta poeira e objetos soltos na direção do ponto vazio onde havia o portal",
      "Ladrilhos do salão que se erguem e se deslocam em espiral, abrindo uma fenda estreita no piso",
      "Mapa de Iara que esquenta na mão e tem uma de suas bordas escurecida, como se estivesse sendo consumido"
    ],
    "exit_condition": "A fenda no piso se fecha ou é contida, e o mapa para de reagir, deixando claro se a passagem ainda pode ser fechada.",
    "budget_turns": 6
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Com a passagem já selada e as runas apagadas, o salão deixa de ser refúgio: o piso de pedra racha em volta do círculo onde o portal estava, e uma corrente de ar frio sobe pelas frestas, trazendo cinza que gruda na pele. Iara e Bento precisam decidir como sair do salão antes que o chão ceda sob o mapa que carregam.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras que se abrem no piso ao redor do círculo de runas apagadas",
      "Cinza fria soprando pelas frestas e cobrindo o mapa",
      "Uma única porta de saída do salão, parcialmente obstruída por escombros"
    ],
    "exit_condition": "Os dois alcançam a porta de saída do salão ou o piso cede sob um deles.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Um eco distorcido irrompe do centro do salão onde as runas apagaram, fazendo o piso de pedra vibrar e rachar em círculos concêntricos; uma fenda fina se abre no chão e exala um sopro frio que faz as tochas bruxulearem, enquanto o mapa de Iara se agita sozinho dentro da bolsa, como se algo o puxasse para baixo. Bento percebe que a única saída lateral está sendo lentamente obstruída por escombros que caem do teto. O tempo para agir encurta.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Fenda no chão exalando ar frio e fazendo as tochas bruxulearem",
      "Mapa de Iara se agitando sozinho dentro da bolsa",
      "Escombros começando a bloquear a saída lateral do salão"
    ],
    "exit_condition": "A fenda no chão para de exalar ar frio e o mapa se aquieta, ou a saída lateral fica completamente bloqueada.",
    "budget_turns": 5
  }
}
```

## portal_closed / en

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The unstable runes, though dark, still hold residual energy that is now causing the stone around the portal to crack. The widening passage is not closing; instead, the hall itself is becoming unstable. A new external threat: a section of the ceiling collapses near the portal, blocking the direct path and forcing Iara and Bento to find another way to seal the portal before the entire hall caves in.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A loud crack echoes as a large chunk of stone falls from the ceiling, landing between Iara and Bento and the portal.",
      "A new tremor shakes the hall, causing dust and smaller debris to rain down.",
      "The residual glow in the runes pulses erratically, indicating the portal's energy is still active and dangerous."
    ],
    "exit_condition": "The portal is sealed or the immediate collapse threat is neutralized, allowing a clear path to the portal.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The passage collapsing inward leaves behind a spreading fault line that emits a low hum and begins to pull loose stones and the map's edge toward it. Iara and Bento must decide how to handle this new physical hazard while the hall's runes stay dark.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A jagged crack in the hall floor that slowly widens",
      "A growing hum that makes the air vibrate",
      "Loose debris and the map's corner being dragged toward the crack",
      "Darkened runes that flicker weakly when the hum spikes"
    ],
    "exit_condition": "The crack stops spreading or the map is pulled free of its influence, forcing both characters to reposition and act.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A sudden physical escalation forces Iara and Bento to act together before the portal consumes the hall. The closed passage ruptures outward, tearing the floor and destabilizing the entire room, so the map and their footing are immediately at risk.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A section of the portal frame shears off and crashes into the hall floor.",
      "The stone floor around the sealed passage splits with a widening crack.",
      "Loose debris and a burst of raw portal energy scatter across the room, threatening the map."
    ],
    "exit_condition": "The crack either stops spreading or the portal's rupture reaches its peak, leaving a clear, immediate danger for the next beat.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The unstable portal flares back to life in a violent surge, reversing the earlier closure and threatening to pull the map, and anyone near it, through the widening rift; Iara and Bento must act while the hall begins to physically destabilize.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "The dormant runes reignite and pulse in a rapid, irregular rhythm",
      "A deep hum builds until the stone floor vibrates and loose debris is dragged toward the rift",
      "The map jerks in Iara's grip, edges lifting as if pulled by a current",
      "The widening passage reveals a wind carrying dust and a distant roar from beyond"
    ],
    "exit_condition": "The portal is closed or the passage drags an anchor object (such as the map) fully into the rift.",
    "budget_turns": 4
  }
}
```

## portal_left / pt

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Com o portal do salão ainda ativo mas instável, uma fenda secundária se abre no chão do acampamento e começa a puxar detritos e ar para dentro, forçando Iara e Bento a agir no presente imediato antes que o próprio chão ceda sob eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Fenda secundária no solo do acampamento, sugando poeira, pedras soltas e o ar ao redor",
      "Runas do mapa de Iara reagindo fisicamente à fenda, esquentando ou piscando contra a instabilidade",
      "Um dos suportes da barraca sendo arrancado e sugado para dentro da fenda"
    ],
    "exit_condition": "A fenda secundária está selada ou neutralizada e Iara e Bento estão fora do raio de sucção.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "O portal do salão se fechou atrás deles, mas o custo foi o colapso parcial da passagem; agora o chão do cânion racha e uma fenda se abre sob o acampamento, engolindo parte do equipamento e forçando Iara e Bento a se moverem para terreno mais alto enquanto o mapa reage à proximidade da torre.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "fenda que se abre no chão do acampamento",
      "parte do equipamento de Bento cai na fenda",
      "mapa de Iara esquenta ou vibra, indicando a direção da torre",
      "som distante de algo grande se movendo no cânion"
    ],
    "exit_condition": "Iara e Bento estão em terreno seguro e o mapa aponta claramente a direção da torre.",
    "budget_turns": 6
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "O portal se fechou atrás deles, mas a instabilidade das runas provocou um desmoronamento no salão do outro lado; a parede rochosa do cânion racha e começa a desabar sobre Iara e Bento, separando-os enquanto uma fissura profunda se abre no chão entre os dois, revelando um brilho de runas ativas no fundo da fenda.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Desabamento de rochas na parede do cânion",
      "Fissura profunda que se abre no chão separando os personagens",
      "Brilho de runas ativas visíveis no fundo da fissura",
      "Mapa ameaçado por detritos que caem"
    ],
    "exit_condition": "A fissura expõe um caminho novo e ambos reagem ao perigo imediato, com o mapa ainda em posse de alguém.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Com o portal fechado atrás deles, o cânion reage: uma fenda no chão começa a cuspir ar quente e as paredes ecoam um estalo ritmado, como se algo grande se movesse sob a rocha. Iara tem o mapa nas mãos e precisa decidir se o usa para achar uma saída ou para entender a fenda; Bento precisa escolher um caminho entre a parede instável e o leito seco enquanto o chão treme sob os dois.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Fenda no chão do cânion expelindo ar quente e cheiro de enxofre",
      "Estalo ritmado ecoando nas paredes, aumentando de intensidade",
      "Mapa de Iara reage ao calor, com linhas que brilham e se movem sozinhas"
    ],
    "exit_condition": "A fenda se abre o suficiente para bloquear ou separar os dois, forçando uma escolha imediata de rota.",
    "budget_turns": 4
  }
}
```

## portal_left / en

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The portal behind them, already sealed to the hall, begins to widen from the canyon side. A cold updraft pours through the rune circle set in the canyon floor, and the nearest rock wall cracks and slumps toward the widening throat. Iara and Bento must decide whether to act on the portal while the ground is failing under them, or flee to safer stone. Their choices remain entirely their own.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A rune circle burned into the canyon floor, humming and pulling air downward",
      "A widening vertical seam in the rock wall beside the circle, shedding dust and gravel",
      "Bento's dropped coil of rope sliding toward the seam, snagging on a spur",
      "The canyon wall slumping in small slides within reach of the circle"
    ],
    "exit_condition": "One or both characters commit to a course of action at the rune circle (working the runes, marking the seam, anchoring a line, or retreating), and the seam's growth visibly changes the terrain around them.",
    "budget_turns": 6
  }
}
```

### Draw 2

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "The portal that was left behind is not truly gone. Collapse pressure from the dead portal follows them into the canyon: the cliff face above the old passage shears away in a rockslide, sealing any thought of return and driving Iara and Bento out onto the open canyon floor. With the map as their only leverage, a new pressure appears: the canyon rocks begin to hum at the same frequency the runes used, letting a hostile scavenger or canyon creature home in on the map's resonance, so the pair must decide in the open whether to hide, run, or use the map before the pursuer closes.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rockslide seals the old passage behind them, making return impossible.",
      "The canyon rock face hums in the rune frequency, turning the map into a beacon.",
      "A canyon scavenger, drawn by the hum, enters the scene at a distance and begins tracking them."
    ],
    "exit_condition": "The scavenger is evaded, defeated, or lost, or the map stops broadcasting the rune frequency.",
    "budget_turns": 5
  }
}
```

### Draw 3

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "With the hall portal closed behind them, Iara and Bento must now carry the map across the canyon toward the tower. The situation introduces the first outward pressure of the new act: the map itself begins to react to the canyon, and the route ahead is blocked by a recent rockfall that forces them to choose a path without knowing what the canyon holds.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "The map's ink glows faintly and one drawn line shifts to point toward the tower",
      "A fresh rockfall has buried the marked trail, leaving a narrow ledge and a dark crevice as the only routes forward",
      "A distant grinding sound rolls through the canyon, suggesting the collapse is still settling"
    ],
    "exit_condition": "Iara and Bento commit to one of the two routes and leave the rockfall behind, or the canyon forces the choice by closing one route.",
    "budget_turns": 6
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "The canyon is a hostile, shifting terrain, and the map they carry is the only thing that can lead them to the tower. As Iara and Bento orient themselves after the portal's collapse, the canyon itself begins to act: the ground trembles, rock walls groan, and a distant tremor suggests the unstable passage they left behind is still widening, now threatening to reshape the canyon they are in. They must navigate the map's cryptic markings while the environment becomes an active obstacle, and a new, urgent deadline emerges: the widening passage may collapse the canyon rim, forcing them to find the tower's trail before the route behind them is erased.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A deep rumble echoes from the closed portal's direction, shaking loose rocks from the canyon walls.",
      "The map's ink shifts subtly, revealing a path that wasn't visible before, but the markings are fading at the edges.",
      "A narrow side canyon opens up, offering a possible shortcut, but it is half-blocked by fresh debris."
    ],
    "exit_condition": "They commit to a direction, either following the new path on the map or taking the risky shortcut, and the first physical obstacle of the canyon journey is overcome or bypassed.",
    "budget_turns": 6
  }
}
```
