# Flash effort-label plans

## portal_attempt / minimal

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A instabilidade das runas se converte em algo físico: o portal Cospe uma lufada de ar quente carregada de areia e fragmentos de pedra que atravessam o salão, apagando parte das marcas no chão e deslocando o mapa das mãos de quem o segura. A pressão obriga Iara e Bento a reagir ao que entra, não apenas ao que já está aberto, enquanto o vão do portal cresce mais um palmo e uma luz pulsante começa a piscar em intervalos regulares, como se algo do outro lado estivesse batendo.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Lufada de ar quente e areia atravessando o portal",
      "Runas do chão parcialmente apagadas pela areia",
      "Mapa deslocado ou no chão entre os dois",
      "Pulsos de luz rítmicos vindos do outro lado do vão"
    ],
    "exit_condition": "Alguém decide como reagir à lufada e ao pulso (recolher o mapa, cobrir as runas, recuar, atacar a luz), e o primeiro pulso termina sem que nada mais atravesse.",
    "budget_turns": 4
  }
}
```

### Draw 2

```json
"AssertionError: HTTP/transport failure"
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A passagem continua a se alargar e agora expele algo físico para dentro do salão (uma rajada de ar carregada de fragmentos, ou uma forma ainda indistinta que empurra o limiar), enquanto parte do círculo rúnico racha e se apaga, encolhendo a área estável onde o mapa poderia funcionar. Iara e Bento têm cada um seu próprio caminho para lidar com a ameaça e com o recurso que se deteriora, sem que nada decida por eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma fenda no piso engole parte das runas ainda acesas",
      "Uma presença ou rajada atravessa o portal e avança para dentro do salão",
      "O mapa reage fisicamente ao contato com o portal (aquece, vibra ou se dobra sozinho)"
    ],
    "exit_condition": "O portal está fechado, ou a presença que atravessa assume forma plena dentro do salão.",
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
    "intent": "A tentativa de Iara falhou e as runas seguem oscilando. Agora a própria membrana do portal começa a ceder: a borda se rompe e algo tenta atravessar, enquanto o piso do salão racha em direção à passagem. Iara e Bento precisam lidar com a ameaça física imediata sem decidir por eles como reagir ou o que sacrificar.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma fenda no piso do salão que avança em direção ao portal, engolindo ladrilhos e soltando poeira",
      "Uma forma ainda incompleta pressionando a membrana do portal, deformando-a por dentro e emitindo um calor que faz o ar tremer",
      "As runas ao redor do portal apagando em sequência, da mais externa para a mais interna, reduzindo o controle sobre a passagem",
      "O mapa na mão de Iara esquentando e reagindo à proximidade da criatura, com traços se movendo sozinhos"
    ],
    "exit_condition": "O portal está fechado, por qualquer meio que os personagens escolham, ou a passagem se rompe por completo e algo atravessa.",
    "budget_turns": 5
  }
}
```

## portal_attempt / low

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "O portal aberto cobra seu preço físico: a fenda nas runas se rompe em rachaduras pelas paredes do salão e algo atravessa da passagem, forçando Iara e Bento a reagir à pressão enquanto o mapa de Iara é puxado na direção da boca do portal. A situação muda o assunto do simples teste com o mapa para uma ameaça concreta que avança sobre eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras se espalham das runas pelas paredes e pelo piso do salão",
      "Uma rajada ou vulto atravessa o portal e derruba parte do mobiliário",
      "O mapa de Iara é arrastado em direção à boca do portal"
    ],
    "exit_condition": "O vulto ou rajada é contido e o mapa é recuperado longe da boca do portal.",
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
    "intent": "A passagem se alarga visivelmente e passa a sugar o ar do salão, arrancando objetos soltos das mãos; as runas começam a se apagar uma a uma, marcando um prazo físico. Algo do outro lado empurra contra a abertura, deformando o contorno do portal. Iara e Bento ficam presos entre a sucção crescente e o mapa que reage fisicamente ao contato com a energia das runas, sem que ninguém decida por eles o que fazer.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A borda do portal se deforma com algo pressionando do outro lado",
      "As runas se apagam progressivamente, uma após a outra",
      "Sucção de ar que arrasta objetos soltos pelo salão",
      "O mapa esquenta ou chamusca numa das pontas ao se aproximar das runas"
    ],
    "exit_condition": "Algo começa a atravessar o portal ou todas as runas se apagam.",
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
    "intent": "A instabilidade das runas piora e a passagem se alarga o bastante para algo atravessar o salão vindo do outro lado, forçando Iara e Bento a lidar com uma presença física e com o avanço do próprio piso, que começa a ruir perto do portal, enquanto ainda precisam encontrar um jeito de fechar a passagem.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma rajada de ar quente e detritos atravessa o portal e apaga parte das runas",
      "Uma criatura ou vulto parcial emerge da fenda antes de ser puxado de volta",
      "O piso de pedra ao redor do portal começa a rachar e ceder em círculo",
      "O mapa esquenta e uma linha nova se desenha sozinha sobre sua superfície"
    ],
    "exit_condition": "Iara e Bento conseguem conter a criatura ou o avanço do piso e encontrar uma pista concreta de como estabilizar as runas.",
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
    "intent": "A passagem aberta avança para além das runas: o vão começa a puxar o ar e os objetos do salão para dentro, e uma pressão nova entra em cena empurrando algo físico pela fenda, obrigando Iara e Bento a reagir ao perigo imediato em vez de apenas estudar o mapa.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma rajada que suga o ar do salão e arranca papéis e poeira em direção ao portal",
      "Duas runas do chão que se apagam em sequência, deixando as demais oscilando mais rápido",
      "Um objeto sólido (pedra lascada ou algo vindo de dentro) que atravessa a fenda e cai no piso, rachando as lajes"
    ],
    "exit_condition": "Iara e Bento são forçados a recuar ou a mudar de posição quando o portal atinge um novo limiar físico, com algo sólido já atravessando a passagem.",
    "budget_turns": 4
  }
}
```

## portal_attempt / medium

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "O alargamento da passagem deixa de ser visual e passa a agir sobre o salão: uma sucção cresce no vão do portal, puxando poeira, folhas soltas e o próprio ar para dentro, enquanto a pedra-chave do arco começa a rachar e lascas caem no piso. As runas, antes oscilantes, migram de posição e se reorganizam numa sequência diferente da que Iara tentou usar, tornando o gesto anterior obsoleto. O mapa reage à proximidade da passagem: sua tinta se move sozinha, como se desenhasse algo novo. O salão deixa de ser um lugar seguro para hesitar, e Bento e Iara precisam agir sob um prazo físico que se estreita a cada instante.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Sucção crescente no vão do portal, forte o bastante para arrastar objetos leves pelo chão",
      "Lascas caindo da pedra-chave rachada do arco, marcando um tempo físico de colapso",
      "Runas que migram sozinhas para uma nova configuração, invalidando a tentativa anterior",
      "Tinta do mapa se movendo por conta própria nas proximidades da passagem"
    ],
    "exit_condition": "A sucção atinge intensidade que arrasta um dos dois na direção do vão, ou alguém consegue conter o avanço da passagem por meios físicos, quebrando o ritmo atual.",
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
    "intent": "O alargamento da passagem deixa de ser só visual e vira força física: o ar do salão começa a ser sugado para dentro do vão e detritos leves (poeira, folhas secas, lascas de pedra) deslizam pelo chão na direção do portal. Ao mesmo tempo, as runas perdem estabilidade de forma visível e progressiva: três delas se apagam em sequência, cada apagamento acompanhado de um estalo e de um solavanco na luz. A moldura de pedra range e racha, soltando fragmentos, e uma pressão vinda do outro lado empurra a abertura como se algo se apoiasse nela. O salão passa a impor um relógio físico que Iara e Bento terão de enfrentar com o que têm em mãos.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Sucção que arrasta objetos soltos em direção ao portal",
      "Três runas se apagando em sequência, com estalos e solavancos de luz",
      "Rachaduras na moldura de pedra soltando fragmentos",
      "Pressão do outro lado empurrando a abertura, deformando o vão"
    ],
    "exit_condition": "As três runas restantes se apagam por completo (ou o portal é fechado antes disso).",
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
    "intent": "A passagem aberta deixa de apenas oscilar e passa a sugar o salão: os detritos soltos do piso começam a deslizar para dentro dela, criando uma corrente de ar quente e puxão físico que ameaça arrancar o mapa das mãos e as pedras das paredes. Em vez de o grupo poder apenas observar as runas, o próprio lugar se torna ativo e hostil, obrigando a escolhas físicas imediatas (segurar, ancorar, recuar, largar algo) sem que ninguém seja forçado a decidir nada.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Sucção crescente que arrasta detritos soltos do piso em direção ao portal",
      "Uma pedra rúnica se desprende da parede e cai",
      "Fenda no piso que se alarga e range sob os pés",
      "As runas apagam em sequência, uma a uma, enquanto a pedra cai"
    ],
    "exit_condition": "A sucção para ou muda de direção, e a pedra rúnica desprendida termina recuperada ou perdida para dentro do portal.",
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
    "intent": "A passagem aberta deixa de apenas oscilar e começa a puxar o ar do salão para dentro: poeira, lascas de pedra e folhas soltas voam na direção das runas. O impacto dessa sucção arranca um bloco do lintel gravado, que despenca no chão entre Iara e Bento e trinca o piso. Enquanto o assobio do vento aumenta, algo grande se desloca devagar na escuridão do outro lado do portal, e o mapa, esteja nas mãos de quem estiver, reage ao avanço daquilo com calor ou vibração perceptível. A situação cobra movimento imediato: o salão está fisicamente mudando em volta dos dois e o tempo de hesitar diminui a cada instante.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Bloco do lintel das runas se rompe e cai, trincando o piso do salão",
      "Sucção de ar arrastando detritos e poeira para dentro do portal",
      "Forma grande e mal definida se movendo na escuridão além da passagem",
      "Reação física do mapa (calor, vibração ou brilho) quando a forma se aproxima"
    ],
    "exit_condition": "O portal está fechado, ou alguém é forçado a recuar para fora do alcance da sucção sem conseguir fechá-lo.",
    "budget_turns": 4
  }
}
```

## portal_attempt / high

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A passagem aberta deixa de ser só luz oscilante e passa a exercer força física sobre o salão: o ar é sugado na direção das runas, o piso racha em volta do círculo e algo começa a empurrar do outro lado, ainda sem forma definida. Iara e Bento precisam agir durante essa pressão crescente, cada um decidindo como quiser.",
    "expected_actors": [
      "C1",
      "Bento"
    ],
    "expected_anchors": [
      "Uma rachadura em arco que se abre no piso, acompanhando o contorno das runas",
      "O sopro contínuo que apaga duas tochas e puxa poeira e detritos para dentro do círculo",
      "Uma massa escura que pressiona a superfície do portal como tecido sendo empurrado por baixo",
      "A quarta runa, que estala e perde o brilho, deixando o restante das runas piscando mais rápido"
    ],
    "exit_condition": "Algo atravessa o portal, mesmo que só uma parte, e o salão deixa de ser um lugar de tentativa e passa a ser um lugar de confronto direto.",
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
    "intent": "O portal aberto deixa de ser só uma oscilação visual e passa a agir sobre o salão: uma rajada vinda da passagem arranca detritos e objetos leves do chão em direção à abertura, enquanto uma das runas racha e se desprende da parede, escancarando uma fresta no piso. Iara e Bento ficam presos entre conter o que atravessa, recuperar o que está sendo sugado e encontrar um jeito de aplicar o mapa na runa quebrada antes que o buraco no chão alcance a parede.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rajada contínua que arrasta detritos e objetos soltos do salão para dentro do portal",
      "Runa rachada que se desprende da parede e cai no chão",
      "Fresta aberta no piso por onde escapa a mesma luz instável das runas",
      "Mapa de Iara exposto ao vento e prestes a ser puxado para a abertura"
    ],
    "exit_condition": "O alargamento do portal cessa ou a fresta do piso é travada depois de o mapa entrar em contato direto com a runa caída, ou alguém ou algo é arrastado para dentro da passagem.",
    "budget_turns": 5
  }
}
```

### Draw 3

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A passagem deixa de apenas oscilar e começa a engolir o ar do salão, puxando poeira, cacos e tecido na direção das runas. Do outro lado algo material se prensa contra a borda da abertura e força passagem, enquanto a primeira runa se apaga e uma rachadura corre pelo assoalho de pedra, aproximando-se do mapa. O salão deixa de ser um lugar seguro de observação: o chão se abre em fenda crescente, a sucção arrasta objetos soltos e a criatura ou coisa presa na borda ganha cada vez mais espaço para atravessar. Iara e Bento ficam livres para decidir como reagir a essa pressão física e ao tempo que se encurta a cada runa que se apaga.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Algo material prensado na borda do portal, ganhando espaço para atravessar",
      "A primeira runa se apaga, e uma rachadura no assoalho avança em direção ao mapa",
      "Sucção que arrasta poeira, cacos e tecido solto para dentro da passagem"
    ],
    "exit_condition": "A coisa prensada na borda é impedida de atravessar por completo ou consegue atravessar, e a rachadura no assoalho alcança ou não o mapa.",
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
    "intent": "A tentativa de Iara de encostar o mapa nas runas falhou e o portal segue aberto, com as runas oscilando. Agora a passagem deixa de ser uma fenda estável: o vão se alarga de verdade e passa a sugar o ar do salão, arrancando uma laje do piso e fazendo uma das runas rachar. Pelo rasgo começa a atravessar algo físico (uma garra, um peso, uma corrente de ar que arrasta detritos), e o salão deixa de ser um lugar seguro para se pensar. A situação pressiona Iara e Bento a agir no presente, sem decidir por eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A fenda do portal se alarga visivelmente e suga o ar do salão",
      "Uma laje do piso se solta e é arrastada em direção à passagem",
      "Uma das runas racha e sua luz muda de cor e ritmo",
      "Algo físico começa a atravessar a passagem, agarrando ou forçando a borda do vão"
    ],
    "exit_condition": "Algo atravessa a passagem o suficiente para tocar o chão do salão, alterando o espaço de forma irreversível e obrigando Iara e Bento a mudar de posição.",
    "budget_turns": 5
  }
}
```

## portal_closed / minimal

### Draw 1

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal fechado, o salão reage: as runas apagadas voltam a brilhar em vermelho e formam uma contagem regressiva, enquanto o chão racha e engole pedaços do piso, criando uma pressão física que empurra Iara e Bento para fora com o mapa.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Runas reacesas em contagem regressiva",
      "Fenda no chão que engole o piso",
      "Tremor crescente no salão"
    ],
    "exit_condition": "A contagem regressiva chega a zero ou Iara e Bento atravessam a saída do salão.",
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
    "intent": "Após o fechamento do portal, o salão começa a desmoronar, abrindo uma fenda no chão que separa Iara e Bento da única saída em direção à torre.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "fenda no chão",
      "abismo",
      "porta de saída do outro lado"
    ],
    "exit_condition": "Iara e Bento conseguem atravessar o abismo ou encontrar uma rota alternativa para deixar o salão.",
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
    "intent": "Com o portal selado, o salão responde ao fechamento: as paredes começam a ceder e o piso racha, tornando a permanência insustentável. O mapa, ainda nas mãos de Iara e Bento, reage ao selo e revela uma rota que só faz sentido se seguida agora, enquanto a estrutura ao redor se desfaz. A pressão é externa e física: o lugar onde estão deixa de ser seguro e o caminho até a torre passa a ser uma escolha forçada pelo colapso, não por conversa.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras que se alargam no piso e nas paredes do salão",
      "O mapa esquentando e marcando uma linha de rota que antes não aparecia",
      "Um estrondo vindo de além do portal selado, empurrando poeira pelas frestas",
      "A única saída visível do salão parcialmente obstruída por escombros"
    ],
    "exit_condition": "Iara e Bento deixam o salão por uma rota decidida no mapa, ou o salão se torna intransitável e eles precisam abrir caminho na força.",
    "budget_turns": 5
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão deixa de ser passagem e vira armadilha: o mapa de Iara reage ao fechamento, aquecendo e acendendo uma marca nova que aponta para a torre, enquanto a única porta de pedra do salão começa a descer sozinha e um ruído de algo pesado se arrasta do lado de fora. A pressão agora é sair com o mapa antes que o salão se tranque por completo.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "O mapa esquenta e revela uma marca luminosa que aponta na direção da torre",
      "A porta de pedra do salão começa a descer lentamente sobre o vão",
      "Um arrasto pesado e regular se aproxima do lado de fora da porta",
      "Uma rachadura nova se abre no chão onde as runas apagadas estavam"
    ],
    "exit_condition": "Iara e Bento atravessam ou escancaram a porta do salão levando o mapa consigo.",
    "budget_turns": 5
  }
}
```

## portal_closed / low

### Draw 1

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão deixa de ser seguro: o mapa reage ao contato de Iara e Bento (esquenta, marca um traço novo que aponta para a torre) enquanto batidas pesadas surgem do outro lado da parede onde ficava a passagem, forçando os dois a decidir como e quando sair do salão levando o mapa.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "O mapa esquenta e revela um traço/rota nova apontando para a torre",
      "Batidas pesadas do outro lado da parede selada, algo tentando reabrir a passagem",
      "Uma rachadura fina que volta a brilhar na pedra onde as runas apagaram"
    ],
    "exit_condition": "Iara e Bento cruzam a saída do salão levando o mapa, deixando o portal selado para trás.",
    "budget_turns": 5
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado, a energia represada rebate pelo salão: as runas apagadas racham o piso de pedra e o selo central começa a ceder, abrindo uma fenda que exala ar quente e um brilho âmbar vindo de baixo. O mapa nas mãos de Iara esquenta e puxa para o lado da parede leste, como se algo embaixo do salão o chamasse. A situação pressiona a dupla a decidir como sair do salão em ruína sem perder o mapa, e o que fazer com a nova abertura no chão.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Piso de pedra rachado em volta do selo central",
      "Fenda no chão exalando ar quente e brilho âmbar",
      "Mapa esquentando e puxando a mão de Iara para a parede leste",
      "Poeira e detritos caindo do teto do salão"
    ],
    "exit_condition": "A dupla deixa o salão (pela fenda, pela parede leste ou por outra saída) levando o mapa consigo, ou a fenda central se alarga a ponto de tornar a permanência impossível.",
    "budget_turns": 6
  }
}
```

### Draw 3

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão perde sustentação: o piso de pedra racha em volta do antigo círculo e parte do teto desmorona, forçando a saída. Em meio ao desabamento, o mapa reage ao calor e à poeira, revelando uma linha nova que não existia antes e que aponta para a torre por um caminho mais curto, mas visivelmente perigoso. Iara e Bento precisam decidir, sob pressão física imediata, como e por onde sair com o mapa intacto.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras se abrem no piso ao redor do círculo de runas apagadas, com blocos do teto caindo",
      "O mapa esquenta e uma linha nova se desenha sozinha sobre ele, marcando uma rota alternativa até a torre",
      "A porta lateral do salão emperra com o deslocamento das pedras, deixando só uma saída parcialmente livre"
    ],
    "exit_condition": "Iara e Bento atravessam a saída do salão levando o mapa, e a nova rota traçada nele permanece visível do lado de fora.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado, a energia recua e o salão sofre as consequências físicas do fechamento: o piso racha, as runas queimadas não voltam a acender e algo pressiona do outro lado da pedra selada. Ao mesmo tempo, o mapa reage ao calor residual e expõe uma rota até a torre, impondo uma decisão imediata sobre partir antes que o selo ceda ou o salão desabe.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras que se abrem no piso do salão",
      "Mapa que esquenta e revela uma rota até a torre",
      "Batidas abafadas do outro lado da pedra selada",
      "Runas queimadas que já não respondem"
    ],
    "exit_condition": "A rota até a torre está traçada e os dois se movem para a saída do salão.",
    "budget_turns": 4
  }
}
```

## portal_closed / medium

### Draw 1

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão deixa de ser um lugar neutro: a energia represada no outro lado empurra a pedra e abre uma rachadura que avança pela parede onde ficava a passagem, enquanto o chão range sob os pés e cede num degrau que não existia antes, revelando uma descida. Ao mesmo tempo, o mapa de Iara reage fisicamente, aquecendo e puxando na direção da torre, expondo um traço de rota que não estava desenhado antes. A pressão é a de sair antes que o salão se mova mais do que eles podem acompanhar, com a criatura ou a força do outro lado batendo do lado de dentro do selo e o assoalho instável fechando as opções de ficar.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachadura luminosa que se espalha pela parede do portal selado, com batidas do outro lado do selo",
      "Degrau e alçapão de pedra que se abrem no piso do salão, levando a uma escada descendente",
      "Mapa esquentando e exibindo uma linha de rota nova apontando para a torre",
      "Poeira e escombros caindo do teto a cada impacto contra o selo"
    ],
    "exit_condition": "A rota concreta para fora do salão está estabelecida (escada descoberta, mapa indicando direção) e o salão se torna ativamente perigoso demais para permanecer.",
    "budget_turns": 5
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal fechado e as runas apagadas, o salão deixa de ser um lugar neutro: o piso em volta do pedestal começa a rachar e ceder, poeira fina sobe pelas frestas e um vento frio desce de algum lugar acima, trazendo um badalar metálico distante vindo da direção da torre. O mapa reage ao movimento do ar e do chão, expondo uma rota que antes não aparecia. A pressão é física e imediata: o chão sob os dois está mudando, e o único caminho seguro aponta para fora do salão, na direção do som. Nada decide por Iara nem por Bento; o que se planeja é o que o lugar faz com eles e o que o mapa passa a mostrar enquanto isso acontece.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras que se abrem no piso ao redor do pedestal, com poeira e estalos de pedra",
      "Badalar metálico distante vindo da direção da torre, audível pelas frestas",
      "O mapa que revela uma linha de rota nova ao ser atingido pelo vento frio",
      "Corrente de ar descendente que apaga vestígios e arrasta fragmentos pelo salão"
    ],
    "exit_condition": "O piso em torno do portal cede o suficiente para tornar o salão insustentável e a rota marcada no mapa aponta claramente para fora, na direção do badalar da torre.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão cobra seu preço: o piso de pedra onde a passagem ficava se abre numa fenda reta que expõe um degrau descendente, enquanto a tinta do mapa começa a desaparecer a partir de uma das bordas, impondo um prazo físico a Iara e Bento. Ao mesmo tempo, sons de fora do salão anunciam que o complexo deixou de estar vazio, forçando os dois a escolher entre descer pelo degrau revelado, sair pela rota conhecida ou tentar preservar o mapa antes que ele se apague.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Fenda reta no piso de pedra onde ficava o portal, expondo um degrau descendente",
      "Tinta do mapa começando a sumir a partir de uma borda, apagando trechos do traçado",
      "Três batidas pesadas do portão externo do complexo, seguidas de silêncio",
      "Fragmento de pedra do umbral que se esfarela e cai no chão com marcas de runas esfriando"
    ],
    "exit_condition": "Iara e Bento deixam o salão por uma das rotas (degrau, saída conhecida ou outra abertura) ou ficam retidos nele com o mapa já parcialmente apagado, definindo o próximo movimento rumo à torre.",
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
    "intent": "Com o portal já selado e as runas apagadas, o salão deixa de ser refúgio: a energia que sustentava a passagem volta-se contra a própria pedra, e o mapa que Iara e Bento precisam levar à torre começa a se degradar fisicamente diante deles. O fechamento tem um preço imediato e material (estrutura cedendo e tinta sumindo), empurrando os dois para fora do salão por uma saída estreita e perigosa, sem que ninguém decida por eles como agir.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Rachaduras que se abrem no piso e detritos que desabam bloqueando a porta principal do salão",
      "A tinta do mapa se apagando de fora para dentro, deixando visível apenas o traçado que leva à torre",
      "Um arrastar de pedra pesada vindo do corredor lateral, aproximando-se no escuro",
      "Uma escada lateral estreita, antes oculta sob as runas apagadas, que agora se revela como única saída"
    ],
    "exit_condition": "Os dois deixam o salão pela escada lateral carregando o mapa com a rota da torre ainda legível, ou o mapa perde essa rota por completo antes que consigam sair.",
    "budget_turns": 5
  }
}
```

## portal_closed / high

### Draw 1

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado e as runas apagadas, o salão deixa de ser lugar seguro: o mecanismo da porta de pedra na única saída começa a descer e o chão racha onde as runas queimaram. Enquanto isso, uma nova linha escura surge sozinha no mapa, apontando para a torre, e sons de passos e vozes alheias se aproximam pelo corredor externo. Iara e Bento precisam reagir ao cerco fechando, escolhendo o que fazer com o mapa e como escapar, sem que nenhuma decisão seja tomada por eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "O portão de pedra da única saída do salão começa a descer lentamente, encurtando o vão a cada instante",
      "Uma linha escura nova se desenha sozinha no mapa, apontando para a torre, como se o papel tivesse reagido ao portal selado",
      "Passos e vozes não identificadas se aproximam pelo corredor além do portão, trazendo alguém ou algo em direção ao salão",
      "Rachaduras se abrem no piso exatamente onde as runas apagadas estavam, soltando poeira e calor"
    ],
    "exit_condition": "Iara e Bento cruzam o vão do portão de pedra antes que ele se feche, ou o portão se fecha de vez e a saída pelo corredor fica bloqueada, restando outra rota a definir.",
    "budget_turns": 5
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "O salão reage ao portal fechado: impactos pesados do lado de fora racham a parede leste e parte do teto cede; o mapa esquenta e uma linha luminosa se desenha sobre ele apontando na direção da torre; a porta lateral, antes selada, começa a destrancar. Iara e Bento ficam entre a instabilidade do salão e a rota que se revela.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "parede leste rachada",
      "mapa aquecido com linha luminosa apontando para a torre",
      "porta lateral destrancando",
      "impactos pesados do lado de fora"
    ],
    "exit_condition": "A porta lateral se abre o bastante para expor o corredor externo, enquanto os impactos aumentam.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "O portal está selado, as runas apagaram e o salão ficou sem passagem. Iara e Bento precisam sair dali e levar o mapa até a torre, mas o selamento cobrou um preço físico: a energia que fechou a passagem está sendo sugada de tudo o que restou no salão, e o próprio mapa começa a se apagar diante dos olhos. As saídas do salão reagem ao rompimento mágico: parte do teto desaba perto de uma delas e uma poeira fria enche o ar, deixando apenas um corredor viável. Ao longe, o sino da torre badala de forma errada, num repique contínuo que funciona como prazo, alguém ou algo já está na torre e o mapa precisa chegar antes que ele fique em branco. O mundo não espera: a degradação do mapa e o desmoronamento avançam por conta própria.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "As linhas e os símbolos do mapa começam a desaparecer progressivamente, a partir das margens e das rotas menos marcadas",
      "Parte do teto do salão desaba sobre uma das saídas, deixando apenas um corredor viável para fora",
      "Uma poeira fria e carregada de estática mágica ocupa o ar, tornando visível que o selamento drenou energia de tudo no recinto",
      "O sino da torre badala em repique contínuo e anômalo, marcando um prazo externo que se aproxima"
    ],
    "exit_condition": "Iara e Bento cruzam a saída restante do salão com o mapa em mãos e o apagamento do mapa está detido ou desacelerado, com os dois já no corredor que leva à torre.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal selado, o salão deixa de ser um lugar neutro: o resíduo do fechamento suga o ar e faz as runas do piso esfriarem e racharem. Do outro lado da pedra selada vêm batidas ritmadas, e cada batida faz a poeira do chão subir e voltar a cair. O selo é recente e fino, e as paredes do salão reagem a ele: a única porta lateral range, empurrada por dentro, e o mapa nas mãos de Iara queima uma rota nova em direção à torre, enquanto as bordas desse traçado escurecem como papel pegando fogo. A situação exige que os dois leiam o que o mapa está mostrando e escolham como sair antes que o salão deixe de ser habitável.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Batidas ritmadas do outro lado da pedra selada, cada vez mais próximas do ritmo de um coração",
      "Mapa de Iara marcando uma rota nova até a torre, com as bordas do traçado escurecendo e se consumindo",
      "Porta lateral do salão rangendo, forçada por dentro, com o ar do salão ficando pesado e rarefeito"
    ],
    "exit_condition": "Os dois cruzarem a soleira do salão (pela porta lateral ou por outro vão que se abra) ou o mapa consumir a rota antes que a atravessem.",
    "budget_turns": 6
  }
}
```

## portal_left / minimal

### Draw 1

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal recém-selado, a água represada do salão desce pelo cânion em uma tromba que sobe rápido; Iara e Bento precisam ganhar as paredes para não serem arrastados. Ao mesmo tempo, o mapa exposto reage à luz da tarde e traça uma rota viva até a torre, mas acrescenta uma marca nova que pulsa como se tivesse prazo. A situação é de fuga vertical e leitura do mapa sob pressão, sem decidir por nenhum dos dois.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A água do cânion subindo e estreitando o chão de pedra",
      "O mapa com uma linha pulsante apontando para a torre e uma marca nova que lateja",
      "Uma fenda na parede com degraus antigos esculpidos, alcançável acima da linha da água",
      "Um som de sino distante vindo da direção da torre"
    ],
    "exit_condition": "Iara e Bento alcançam a fenda elevada e o mapa estabiliza a rota até a torre sob seus olhos.",
    "budget_turns": 6
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal fechado, o próprio cânion reage ao fechamento: o calor e o zumbido presos na fissura começam a escapar e o fundo do desfiladeiro responde com um estrondo de água em movimento. Ao mesmo tempo, o mapa que Iara carrega muda fisicamente diante dos olhos dela, desenhando uma linha nova que aponta para a torre. A dupla precisa se afastar da área do portal antes que a primeira onda alcance o acampamento, já com uma rota inédita nas mãos.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "a fissura lacrada pelo portal esquenta e solta um zumbido crescente",
      "um estrondo de água corrente cresce no fundo do cânion e se aproxima",
      "ao ser aberto, o mapa desenha sozinho uma linha nova apontando para a torre"
    ],
    "exit_condition": "A primeira onda de água e detritos alcança o acampamento e obriga Iara e Bento a deixar a área às pressas, com o mapa já exibindo a rota nova para a torre.",
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
    "intent": "A fenda do portal se alarga de repente e começa a sugar ar, poeira e pedras soltas do cânion; as runas racham e soltam faíscas. Iara percebe que o mapa reage à proximidade da fenda, aquecendo-se e projetando linhas de luz que apontam para pontos instáveis na parede de rocha, enquanto Bento precisa decidir como manter os dois longe da sucção e ainda assim agir sobre o que o mapa revela.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A fenda se alarga e suga detritos do chão",
      "As runas racham e soltam faíscas",
      "O mapa aquece e projeta linhas de luz na parede de rocha",
      "Um desmoronamento parcial bloqueia parte do caminho de volta ao salão"
    ],
    "exit_condition": "Iara e Bento identificam um ponto físico concreto na parede (indicado pelo mapa) que pode estabilizar ou fechar a fenda, e se posicionam para agir sobre ele.",
    "budget_turns": 4
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal já fechado e sem passagem de volta, Iara e Bento precisam partir do acampamento no leito do cânion rumo à torre, mas o cânion deixa de ser passivo: um estrondo distante cresce e a água represada lá em cima começa a descer pelo leito seco, obrigando os dois a decidir o que carregar e para onde subir antes que o caminho baixo desapareça.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A torre visível no alto da parede do cânion, ainda longe",
      "O leito seco que começa a encher com água barrenta e detritos",
      "O mapa nas mãos de Iara, com uma linha nova que parece apontar para cima",
      "O acampamento montado no ponto mais baixo do leito"
    ],
    "exit_condition": "Iara e Bento abandonam o acampamento e alcançam uma cornija acima da linha da água, com o caminho baixo já submerso.",
    "budget_turns": 6
  }
}
```

## portal_left / low

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "A instabilidade das runas não para de crescer: a passagem começa a sugar o ar, a poeira e as pedras soltas do cânion para dentro de si, criando um redemoinho que arrasta tudo na direção do salão distante. Bento precisa decidir como atravessar o terreno que se desfaz, enquanto Iara percebe que o mapa reage ao fenômeno e pode conter a chave do selamento. A pressão física aumenta a cada instante e o tempo urge antes que algo maior seja arrastado.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "O redemoinho de sucção que puxa detritos e o ar do cânion para dentro da passagem",
      "As runas que perdem estabilidade e racham sob a pressão",
      "O mapa que reage ao fenômeno (linhas ou símbolos se acendendo/movendo)",
      "Uma formação rochosa do cânion que cede e desaba parcialmente por causa da sucção"
    ],
    "exit_condition": "Iara e Bento identificam no mapa o mecanismo capaz de interromper a sucção e iniciar o fechamento da passagem.",
    "budget_turns": 6
  }
}
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal fechado e as runas apagadas, Iara e Bento ficam presos no fundo do cânion sem rota de volta e precisam definir como levar o mapa até a torre. Um tremor faz desmoronar a parede norte do cânion, selando a saída óbvia e revelando uma fenda estreita sob os escombros, por onde sobe ar quente com cheiro de enxofre. Ao mesmo tempo, o mapa nas mãos de Iara esquenta e suas linhas se movem, apontando para longe, na direção oposta à fenda, e algo grande se desloca nas pedras acima, jogando terra solta sobre eles.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Desmoronamento que sela a saída norte do cânion",
      "Fenda estreita aberta nos escombros, com ar quente e cheiro de enxofre",
      "O mapa esquentando e redesenhando suas próprias linhas"
    ],
    "exit_condition": "Os dois escolhem por onde seguir (a fenda ou a direção indicada pelo mapa) e dão os primeiros passos nessa rota.",
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
    "intent": "Com o portal já selado e o salão inalcançável, Iara e Bento precisam achar uma rota de saída do cânion para chegar à torre. Enquanto avaliam o terreno, o desmoronamento de uma das paredes de arenito soterrou parcialmente a única trilha visível e abriu uma fenda estreita na rocha, forçando os dois a escolher entre desenterrar o caminho antigo ou arriscar a fenda nova, sem certeza de qual leva a algum lugar. A decisão é deles; a pressão é que o sol está baixando e o desmoronamento pode continuar.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A trilha principal do cânion soterrada por pedras do desmoronamento",
      "Uma fenda estreita recém-aberta na parede de arenito",
      "O mapa de Iara reagindo com uma linha que antes não existia",
      "A sombra da parede avançando sobre o acampamento conforme a tarde cai"
    ],
    "exit_condition": "Iara e Bento escolhem uma rota e começam a se mover por ela, ou o desmoronamento avança de novo forçando uma saída imediata.",
    "budget_turns": 5
  }
}
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal já selado e a única passagem de volta perdida, o deslocamento pelo cânion expõe Iara e Bento a uma pressão externa nova: o próprio terreno reage à presença do mapa. Uma corrente de ar quente sobe do fundo do desfiladeiro carregando poeira e um tremor que desprende blocos das paredes altas, enquanto a linha desenhada no mapa se move sozinha sob a pele de couro, apontando para uma direção que não existe no relevo visível. Algo grande se arrasta na penumbra entre as pedras, invisível mas audível, e o caminho se estreita atrás deles à medida que avançam.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "A rota marcada no mapa muda de posição sozinha, indicando um trajeto que o cânion não mostra",
      "Uma corrente de ar quente e um tremor que solta blocos das paredes do desfiladeiro",
      "Um som de arrasto pesado vindo da penumbra entre as rochas, sem origem visível",
      "O caminho já percorrido se fecha ou desmorona atrás deles, impedindo recuo imediato"
    ],
    "exit_condition": "Iara e Bento encontram um ponto seguro e elevado no cânion onde consigam parar, orientar-se pelo mapa alterado e decidir a rota antes que os desmoronamentos atinjam sua posição.",
    "budget_turns": 5
  }
}
```

## portal_left / medium

### Draw 1

```json
{
  "act_completed": false,
  "beat": {
    "beat_id": "a1-b2",
    "intent": "Ainda no cânion com a passagem de volta selada, o alargamento que ameaçava o salão agora se manifesta do lado de fora: o chão do acampamento racha e uma segunda boca de portal começa a abrir, obrigando Iara e Bento a lidar com a ameaça se expandindo no próprio terreno onde estão, longe de qualquer rota de fuga.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma segunda boca de portal se abre no chão do cânion, engolindo parte do acampamento e materiais de Bento",
      "As runas que haviam apagado voltam a pulsar, agora em vermelho, na pedra acima da fenda",
      "O mapa de Iara esquenta e suas linhas se movem sozinhas, marcando a fenda aberta",
      "O ar fica denso e quente, e bordas de rocha começam a se soltar ao redor da fenda"
    ],
    "exit_condition": "A segunda boca tem sua expansão interrompida ou seu ponto de alimentação fica exposto, mostrando o que precisa ser selado.",
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
    "intent": "A parede do cânion racha sob a pressão da passagem que se alarga, derrubando pedras e sugando poeira e vento para dentro; o mapa nas mãos de Iara reage ao calor e ao zumbido, e ambos precisam lidar com o desmoronamento físico enquanto a boca da passagem segue crescendo.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Uma fissura nova rasga a parede do cânion e solta uma chuva de pedras sobre o acampamento",
      "Um rugido grave sobe do fundo da passagem e faz o chão vibrar",
      "O mapa esquenta e brilha nas mãos de Iara, marcando um ponto que pisca",
      "A poeira e o vento são sugados para dentro da passagem, arrastando equipamento solto"
    ],
    "exit_condition": "A boca da passagem para de se alargar e as pedras param de cair, revelando se o portal se fechou ou se rompeu de vez.",
    "budget_turns": 5
  }
}
```

### Draw 3

```json
"AssertionError: HTTP/transport failure"
```

### Draw 4

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "O portal já se fechou atrás deles, deixando Iara e Bento presos no cânion com o mapa e sem rota de volta. O acampamento é atingido por um desmoronamento da borda do cânion que soterra o poço e a linha de água, força os dois a se mover, e a queda expõe uma escada de pedra entalhada descendo pela parede. Ao mesmo tempo, o mapa reage ao desmoronamento: um dos selos queima e apaga uma rota inteira na superfície, reduzindo as opções. Um som distante de chifre vindo da direção da torre responde ao estrondo, deixando claro que algo lá fora registrou o acontecimento. A pressão é externa: água perdida, terreno alterado, mapa danificado e um sinal de que não estão sozinhos.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "desmoronamento da borda que soterra o poço do acampamento",
      "escada de pedra entalhada exposta na parede do cânion pela queda",
      "selo do mapa que queima e apaga uma rota inteira",
      "som de chifre distante vindo da direção da torre"
    ],
    "exit_condition": "Iara e Bento abandonam o acampamento soterrado e se comprometem com um caminho concreto, seja a escada exposta ou outra rota que decidirem buscar.",
    "budget_turns": 6
  }
}
```

## portal_left / high

### Draw 1

```json
"JSONDecodeError: Invalid control character at: line 1 column 568 (char 567)"
```

### Draw 2

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "O chão do leito do cânion cede atrás deles num desmoronamento que sela a rota de volta e ergue uma nuvem de poeira; presos no fundo, o mapa de Iara esquenta e desenha uma linha de luz trêmula apontando para uma fenda estreita na parede, enquanto pedras soltas rolam de cima e um arrasto pesado se move fora de vista entre as sombras do cânion.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Desmoronamento que bloqueia o leito do cânion atrás dos dois",
      "Linha de luz instável surgindo do mapa e apontando para uma fenda",
      "Pedras rolando das paredes e um arrasto pesado nas sombras acima"
    ],
    "exit_condition": "A poeira baixa, a linha do mapa para de tremer e a origem do arrasto nas sombras se revela ou se afasta, deixando um caminho definido no fundo do cânion.",
    "budget_turns": 4
  }
}
```

### Draw 3

```json
{
  "act_completed": true,
  "beat": {
    "beat_id": "a2-b1",
    "intent": "Com o portal fechado, Iara e Bento estão presos no acampamento do cânion e precisam achar um caminho para a torre. Enquanto reavaliam o mapa, a encosta acima do acampamento desmorona: pedras selam a rampa por onde chegaram, soterram parte da tralha e expõem, sob o barro, uma laje antiga com a marca de uma torre em relevo. O estrondo atrai algo grande que se arrasta pelo leito seco lá embaixo, subindo na direção do acampamento. O mapa no colo de Iara reage ao entalhe da laje por conta própria. Cada um decide o que fazer com o pouco tempo que resta antes de a criatura chegar.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Desmoronamento da encosta sela a rampa de saída do acampamento e soterra parte dos suprimentos",
      "Laje de pedra exposta com o entalhe em relevo de uma torre",
      "Mapa de Iara reage sozinho perto da laje (traço, calor ou tinta se movendo)",
      "Rastejo pesado subindo pelo leito seco do cânion em direção ao acampamento"
    ],
    "exit_condition": "A criatura chega ao acampamento ou Iara e Bento já estão em movimento por uma rota nova, com o acampamento abandonado para trás.",
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
    "intent": "A passagem que engoliu o salão não ficou atrás: uma fissura vertical se abre na parede do cânion, runas reacesas subindo pela rocha, e a abertura cresce a cada respiração. O bloco de pedra que desaba da borda represa o riacho raso do acampamento, e a água começa a subir pelas botas enquanto o mapa esquenta nas mãos de quem o segura, a tinta escorrendo e apontando sozinha para a fissura. Iara e Bento precisam decidir, sob água subindo e pedra caindo, o que fazer com a abertura antes que algo saia dela ou o acampamento vire leito de rio.",
    "expected_actors": [
      "C1",
      "C2"
    ],
    "expected_anchors": [
      "Fissura vertical na parede do cânion, alargando a cada instante, com runas reacesas subindo pela pedra",
      "Desabamento de um bloco da borda que represa o riacho; a água sobe pelo acampamento",
      "Mapa esquentando e tinta correndo sozinha na direção da fissura",
      "Sopro de ar frio vindo da fissura, trazendo detritos e um ruído ritmado de dentro"
    ],
    "exit_condition": "A fissura para de alargar (selada, bloqueada ou colapsada) após ação direta de Iara ou Bento sobre ela.",
    "budget_turns": 6
  }
}
```
