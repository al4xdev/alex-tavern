### Case: `portal_attempt`

**Confirmed Context:**
* Location: Salão do portal
* Premise: Iara e Bento devem fechar o portal e levar o mapa à torre.
* Old Act: "Fechar o portal do salão antes que a passagem se alargue." (Exit: "O portal está fechado.")
* Confirmed Events: Iara tentou encostar o mapa nas runas, mas a tentativa falhou; o portal continua aberto e as runas oscilam.
* Act Status: `act_completed: false` em todas as alternativas (correto, pois a condição de saída do ato não foi atingida).

---

#### `portal_attempt-A`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"As runas que sustentam o portal começam a rachar e uma lasca de pedra quente se solta da parede, cai no chão entre Iara e Bento e abre uma fenda no piso..."*
* **Supporting Source Fact:** *"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."*
* **Unresolved Issues:** Nenhum. A escalada do perigo físico decorre diretamente do fracasso do contato prévio. A condição de saída mantém o desfecho do mapa aberto em bifurcação sem ditar ações dos personagens.

#### `portal_attempt-B`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"A instabilidade das runas faz uma delas rachar e cair do arco, e o vão do portal se alarga o suficiente para que um vento quente e cheio de areia atravesse o salão..."*
* **Supporting Source Fact:** *"o portal continua aberto e as runas ainda oscilam."*
* **Unresolved Issues:** Nenhum. A pressão ambiental (penumbra, areia, ruído) impõe urgência dramática legítima sem forçar as escolhas táticas de Iara ou Bento.

#### `portal_attempt-C`
* **Verdict:** ATRITO INTERNO DE CAUSA E EFEITO
* **Quote:** *"se ninguém agir, o mapa será sugado para dentro do portal"* vs. condição de saída: *"O mapa foi lançado para longe da abertura e está preso em algum ponto do salão..."*
* **Supporting Source Fact:** *"Iara tentou encostar o mapa nas runas para fechar o portal."*
* **Unresolved Issues:** O texto do intent define a ameaça iminente de sucção do mapa se ninguém agir, mas a condição de saída antecipa que ele foi atirado para longe e já se encontra preso no salão, neutralizando a física da ameaça anunciada.

#### `portal_attempt-D`
* **Verdict:** ANTECEDENTE IMPOSSÍVEL / DISTORÇÃO DE FATO
* **Quote:** *"A fenda luminosa atingiu a base da parede onde o mapa encostou..."*
* **Supporting Source Fact:** *"Iara tentou encostar o mapa nas runas para fechar o portal"* e o próprio intent: *"mapa na mão de Iara"*.
* **Unresolved Issues:** Erro factual de continuidade. O mapa nunca encostou na "base da parede", e sim nas runas; o texto confunde os pontos de contato e ancora a condição de saída em um evento inexistente.

#### `portal_attempt-E`
* **Verdict:** VIOLAÇÃO DE AGÊNCIA (Ação e sucesso compulsórios)
* **Quote:** *"O mapa é recuperado antes de ser sugado para dentro do portal, e a runa rachada deixa de sustentar a borda, forçando ambos a recuar."*
* **Supporting Source Fact:** *"Iara vê o mapa escapar de suas mãos e planar na direção da abertura."*
* **Unresolved Issues:** A condição de saída decreta antecipadamente o sucesso da intervenção dos jogadores (*"O mapa é recuperado"*) e prescreve o recuo obrigatório de ambos, retirando o controle da ação e o risco real da cena.

#### `portal_attempt-F`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"O portal piora sozinho: a passagem dilata com um estalo e cospe de dentro algo físico que cai no chão do salão..."*
* **Supporting Source Fact:** *"o portal continua aberto e as runas ainda oscilam."*
* **Unresolved Issues:** Nenhum. A introdução de um elemento externo expelido pela passagem é um evento de mundo coerente que altera a cena e deixa a resposta inteiramente a cargo dos jogadores.

#### `portal_attempt-G`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"A borda do portal começa a sugar objetos soltos do salão; uma fenda se abre no piso de pedra sob as runas..."*
* **Supporting Source Fact:** *"o portal continua aberto e as runas ainda oscilam."*
* **Unresolved Issues:** Nenhum. Consequência mecânica e espacial plausível da instabilidade mágica sobre a estrutura física do salão. Agência preservada.

#### `portal_attempt-H`
* **Verdict:** VIOLAÇÃO DE AGÊNCIA (Resolução prescrita)
* **Quote:** *"O mapa está fora da zona de sucção e a runa rachada foi ao menos parcialmente estabilizada ou isolada."*
* **Supporting Source Fact:** *"A tentativa não funcionou: o portal continua aberto e as runas ainda oscilam."*
* **Unresolved Issues:** A condição de saída antecipa e resolve por decreto do narrador o salvamento do mapa e a estabilização/isolamento da runa, usurpando a mecânica do turno do jogador.

---

### Case: `portal_closed`

**Confirmed Context:**
* Location: Salão do portal
* Premise: Iara e Bento devem fechar o portal e levar o mapa à torre.
* Confirmed Events: O portal fechou-se por completo e as runas apagaram. Iara e Bento continuam no salão com o mapa; não existe passagem aberta.
* Act Status: `act_completed: true` em todas as alternativas (correto, pois o portal foi fechado antes do beat proposto).

---

#### `portal_closed-A`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"O salão do portal começa a desmoronar após o fechamento da passagem: blocos do teto caem e o chão racha, forçando Iara e Bento a sair imediatamente..."*
* **Supporting Source Fact:** *"A passagem do portal se fechou por completo; as runas apagaram."*
* **Unresolved Issues:** Nenhum. O desmoronamento serve de catalisador físico urgente para impulsionar os personagens para o Ato 2 (*"Levar o mapa até a torre"*).

#### `portal_closed-B`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"O salão do portal começa a rachar e desabar agora que as runas apagaram; a única saída é a porta norte que dá para a rua da torre..."*
* **Supporting Source Fact:** *"as runas apagaram."* e *"Iara e Bento continuam no salão com o mapa."*
* **Unresolved Issues:** Nenhum. Integra perfeitamente o fato de as runas estarem apagadas e conecta a rota de fuga diretamente ao destino da premissa.

#### `portal_closed-C`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"O salão começa a desmoronar agora que o portal selou, forçando Iara e Bento a sair levando o mapa enquanto vigas e pedras desabam sobre a única saída visível."*
* **Supporting Source Fact:** *"A passagem do portal se fechou por completo".*
* **Unresolved Issues:** Nenhum. A obstrução da saída primária cria um obstáculo de navegação legítimo sem violar a psicologia dos personagens.

#### `portal_closed-D`
* **Verdict:** COERENTE COM ESCALADA EXTERNA
* **Quote:** *"O chão do salão racha e a torre distante começa a desmoronar parcialmente..."*
* **Supporting Source Fact:** Premissa: *"levar o mapa à torre."*
* **Unresolved Issues:** Introduz um dano distante à torre que eleva substancialmente a urgência do objetivo final, mas opera dentro das prerrogativas narrativas do mundo sem criar contradições.

#### `portal_closed-E`
* **Verdict:** REDAÇÃO AMBÍGUA / TRANSIÇÃO ESTAGNADA
* **Quote:** *"O mapa está a salvo das mãos de ambos e a fenda parou de alargar."*
* **Supporting Source Fact:** *"Iara e Bento continuam no salão com o mapa."*
* **Unresolved Issues:** A expressão *"a salvo das mãos de ambos"* é semanticamente confusa e truncada. Além disso, o beat ignora a progressão rumo à torre (Ato 2), mantendo a cena presa em perigo local que encerra a si mesmo de forma pré-resolvida.

#### `portal_closed-F`
* **Verdict:** COERENTE / EXCELENTE TRANSIÇÃO
* **Quote:** *"A passagem fechou e o salão agora está selado por dentro: uma fumaça fria e densa sobe das runas apagadas... O mapa que Iara carrega esquenta e tinge as próprias linhas de vermelho, marcando um trajeto que muda sozinho."*
* **Supporting Source Fact:** *"A passagem do portal se fechou por completo; as runas apagaram."*
* **Unresolved Issues:** Nenhum. Respeita com precisão o estado das runas apagadas, gera expulsão espacial por pressão física e ativa o mapa diretamente como guia para o Ato 2.

#### `portal_closed-G`
* **Verdict:** ANTECEDENTE IMPOSSÍVEL / CONTRADIÇÃO DE FATO
* **Quote:** *"...apagando as últimas runas..."*
* **Supporting Source Fact:** *"A passagem do portal se fechou por completo; as runas apagaram."*
* **Unresolved Issues:** Contradição factual direta. As runas já estavam confirmadas como totalmente apagadas; o beat trata o apagamento como algo em andamento provocado pelo vento de cinzas.

#### `portal_closed-H`
* **Verdict:** RISCO DE IMPASSE NARRATIVO (Dead-end de premissa)
* **Quote:** *"O mapa está seguro nas mãos de alguém ou perdido na fenda."*
* **Supporting Source Fact:** Premissa: *"Iara e Bento devem fechar o portal e levar o mapa à torre."*
* **Unresolved Issues:** A condição de saída admite como desfecho plausível o mapa ser *"perdido na fenda"* logo na abertura do Ato 2, inviabilizando de imediato toda a premissa subsequente do jogo.

---

### Case: `portal_left`

**Confirmed Context:**
* Location: Acampamento no cânion
* Premise: Iara e Bento devem fechar o portal e levar o mapa à torre.
* Confirmed Events: Atravessaram para o cânion; o portal fechou e as runas apagaram. Ambos estão no cânion com o mapa; o salão ficou distante e não há passagem de volta aberta.
* Act Status: `act_completed: true` (correto, fechamento consolidado).

---

#### `portal_left-A`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"...o mapa na mão de Iara reage, suas linhas se reacendem sozinhas marcando um novo traço que aponta para a torre, e o chão treme uma vez..."*
* **Supporting Source Fact:** *"Ambos estão no cânion com o mapa."* e *"Levar o mapa até a torre."*
* **Unresolved Issues:** Nenhum. Utiliza a nova localização confirmada, ativa o mapa como bússola para o novo ato e impõe restrição de suprimentos por acidente ambiental sem subtrair decisões dos jogadores.

#### `portal_left-B`
* **Verdict:** DANO COMPULSÓRIO / ANTECEDENTE REDUNDANTE
* **Quote:** *"...o mapa, exposto ao vento, tem uma das bordas rasgada antes que alguém consiga protegê-lo."*
* **Supporting Source Fact:** *"Ambos estão no cânion com o mapa."* e *"nenhuma passagem de volta está aberta."*
* **Unresolved Issues:** Inflige dano material ao item central da trama por imposição arbitrária (*"antes que alguém consiga protegê-lo"*), sem oportunidade de reação. Além disso, a condição de saída trata a falta de rota de volta como novidade gerada pela tempestade (*"sem trilha visível de volta"*), ignorando que o portal já havia selado.

#### `portal_left-C`
* **Verdict:** VIOLAÇÃO DE AGÊNCIA (Desfecho compulsório)
* **Quote:** *"O mapa está fora da zona de desmoronamento e o resto do acampamento foi abandonado ou perdido."*
* **Supporting Source Fact:** *"Ambos estão no cânion com o mapa."*
* **Unresolved Issues:** O intent desafia os personagens a *"decidir o que salvar"*, mas a condição de saída invalida a decisão previamente, decretando que tudo além do mapa foi compulsoriamente perdido ou abandonado.

#### `portal_left-D`
* **Verdict:** INCOERÊNCIA ESTRUTURAL E DE ANTECEDENTE
* **Quote:** `beat_id: "a1-b2"` e *"O deslizamento bloqueia a passagem atrás deles..."*
* **Supporting Source Fact:** `act_completed: true` e *"o portal se fechou e as runas apagaram depois."* / *"nenhuma passagem de volta está aberta."*
* **Unresolved Issues:** Falha de indexação e lógica. O `beat_id` regride para o Ato 1 (`a1-b2`) apesar de o ato estar finalizado. Ademais, propõe bloquear uma passagem que os fatos confirmados já atestam estar completamente fechada e extinta.

#### `portal_left-E`
* **Verdict:** DESCONTINUIDADE ESPACIAL (Salto geográfico)
* **Quote:** *"O cânion se estreita num desfiladeiro bloqueado por uma ponte de pedra desabada sobre um abismo..."*
* **Supporting Source Fact:** Localização confirmada: *"Acampamento no cânion"*.
* **Unresolved Issues:** Há um salto de cena abrupto: transporta instantaneamente os personagens do acampamento para o estrangulamento de um desfiladeiro com abismo, omitindo qualquer transição de marcha inicial.

#### `portal_left-F`
* **Verdict:** COERENTE / LEGÍTIMO
* **Quote:** *"...desmoronamento que soterra parcialmente a entrada da passagem recém-fechada, alterando o terreno e obrigando a escolha imediata de um caminho..."*
* **Supporting Source Fact:** *"o portal se fechou e as runas apagaram depois."* e *"O salão ficou distante; nenhuma passagem de volta está aberta."*
* **Unresolved Issues:** Nenhum. Trata com coerência a passagem como *"recém-fechada"* e usa o colapso geológico apenas para consolidar o terreno local e forçar a escolha da marcha, preservando total autonomia de rumo.

#### `portal_left-G`
* **Verdict:** VIOLAÇÃO DIRETA DE AGÊNCIA (Falso dilema)
* **Quote:** Intent: *"...forçando a escolha entre a rota exposta e uma fenda lateral..."* vs. Condição de saída: *"A tempestade obriga Iara e Bento a se abrigarem na fenda lateral."*
* **Supporting Source Fact:** O intent propõe uma escolha tática deliberada entre duas opções.
* **Unresolved Issues:** Quebra grave de contrato de agência. O intent oferece uma escolha autêntica entre seguir pela rota exposta ou pela fenda, mas a condição de saída impõe autoritariamente que ambos se abriguem na fenda, cancelando a decisão proposta.

