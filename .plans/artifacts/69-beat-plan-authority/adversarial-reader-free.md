Independent read; run e425a221a661. Reader output is evidence to source-check, not approval.

### Case: `stable`
*Confirmed:* Portal selado, runas apagadas, salão intacto/estável, avanço para o Ato 2 (torre).

- **`stable-A` [Limpo]**
  - *Avaliação:* Coerente e respeita a agência. Move para o Ato 2 introduzindo ameaça externa na soleira sem predeterminar a reação dos personagens.
- **`stable-B` [Limpo]**
  - *Avaliação:* Coerente. A árvore caída externa respeita a diretiva de causas externas posteriores sem violar a estabilidade interna do salão. A reação do mapa à água é detalhe de mundo admissível.
- **`stable-C` [Limpo]**
  - *Avaliação:* Coerente e exemplar. Ancora explicitamente o piso intacto e a posse do mapa, preservando a agência de decisão e movimento físico da dupla.
- **`stable-D` [Ambiguidade Causal / Scripting Leve]**
  - *Fonte:* `"O salão está estável; piso e paredes estão intactos. Não houve dano pelo fechamento."`
  - *Saída:* `"Uma corrente de ar frio entra por uma fresta na parede leste..."`
  - *Leitura 1 (Benigna):* Abertura arquitetônica pré-existente (ex.: seteira ou fresta de ventilação).
  - *Leitura 2 (Contradição):* Fissura ou ruptura estrutural recente, contradizendo `"paredes estão intactos"`.
  - *Menor teste discriminatório:* Definir no texto se a fresta é arquitetônica (seteira) ou fratura na alvenaria.
  - *Agência:* A condição de saída prescreve microações coordenadas dos dois atores (`"Bento aponta... e Iara guarda o mapa"`).

---

### Case: `earthquake`
*Confirmed:* Salão rachado por terremoto externo pós-fechamento; dano por fechamento nulo; Ato 2 ativo.

- **`earthquake-A` [Limpo]**
  - *Avaliação:* Coerente. Desdobra a instabilidade sísmica sem confundi-la com o portal e abre rotas de fuga preservando escolhas táticas.
- **`earthquake-B` [Limpo]**
  - *Avaliação:* Coerente. Progressão física crível do tremor (escombros, inclinação do piso) sem ferir agência.
- **`earthquake-C` [Ambiguidade Material]**
  - *Fonte:* `"Iara e Bento continuam no salão com o mapa."`
  - *Saída:* `"...se arriscam recuperar algo antes de fugir."`
  - *Leitura 1 (Benigna):* Provocação dramática genérica para checar mantimentos ou mochilas deixadas no susto.
  - *Leitura 2 (Fato inventado):* Suposição não fundamentada de que algum item essencial foi derrubado/perdido no salão.
  - *Menor teste discriminatório:* Verificar se há item específico não portado registrado no inventário ou se o mapa é o único foco.
- **`earthquake-D` [Limpo]**
  - *Avaliação:* Coerente. Foco imediato na rota de fuga e salvaguarda do mapa em meio ao colapso do teto.

---

### Case: `held`
*Confirmed:* Portal aberto, runas oscilam, mapa seguro firmemente nas mãos de Iara; Ato 1 não concluído.

- **`held-A` [Limpo]**
  - *Avaliação:* Coerente. Mantém posse do mapa, portal aberto e status do ato, abrindo espaço para nova deliberação.
- **`held-B` [Violação de Agência]**
  - *Fonte:* Bento é ator/personagem da cena.
  - *Saída:* `"Bento enxerga a lógica do mecanismo enquanto Iara ainda segura o mapa..."`
  - *Problema:* Roteirização prévia da conclusão cognitiva/mental do personagem, usurpando sua agência investigativa em vez de fornecer pistas ambientais.
- **`held-C` [Fricção de Agência / Desarme Forçado]**
  - *Fonte:* `"Após a tentativa, Iara ainda segura firme o mapa. Ela não o largou nem o colocou no chão."`
  - *Saída:* `"...onda de choque que arranca o mapa das mãos de Iara e o lança para o outro lado do salão..."`
  - *Problema:* Embora coerente com o estado inicial, recorre a desarme forçado por decreto narrativo para gerar o beat de resgate, subtraindo a agência defensiva da personagem.
- **`held-D` [Limpo]**
  - *Avaliação:* Coerente e dinâmico. Preserva `"mapa continua seguro nas mãos de Iara"` enquanto introduz perigo ambiental físico (vórtice de sucção) que exige resposta.

---

### Case: `floor`
*Confirmed:* Portal aberto; Iara colocou voluntariamente o mapa no chão; Ato 1 não concluído.

- **`floor-A` [Violação de Agência]**
  - *Saída:* `"Bento deve avaliar o caminho e Iara precisa reagir ao fracasso..."`
  - *Problema:* Prescreve reações emocionais e cognitivas obrigatórias aos personagens (`"deve"`, `"precisa"`), em vez de apresentar a pressão ambiental e aguardar a conduta dos atores.
- **`floor-B` [Ambiguidade de Ação Prévia]**
  - *Fonte:* `"Após a tentativa, Iara colocou voluntariamente o mapa no chão. Ele continua no piso."`
  - *Saída:* `"...diante do mapa caído no piso..."`
  - *Leitura 1 (Benigna):* Uso coloquial de `"caído"` significando apenas `"pousado/estirado no piso"`.
  - *Leitura 2 (Fato inventado/Distorção):* Transforma a ação deliberada de pousar o mapa em queda/descuido acidental.
  - *Menor teste discriminatório:* Avaliar se a ficção subsequente trata o mapa como objeto abandonado em pânico ou posicionado intencionalmente.
- **`floor-C` [Ambiguidade de Ação Prévia]**
  - *Fonte:* `"Após a tentativa, Iara colocou voluntariamente o mapa no chão."`
  - *Saída:* `"O mapa, largado no chão..."`
  - *Leitura 1 (Benigna):* Descrição informal do item desacompanhado.
  - *Leitura 2 (Distorção de Agência):* Conota negligência/abandono desastrado, contradizendo o ato voluntário.
  - *Menor teste discriminatório:* Idem a `floor-B`. O restante do beat (dilema de resgate perante desmoronamento) é limpo.
- **`floor-D` [Ambiguidade de Ação Prévia]**
  - *Fonte:* `"colocou voluntariamente o mapa no chão"` vs. *Saída:* `"mapa caído"`.
  - *Problema:* Mesma ambiguidade terminológica de `floor-B` sobre queda acidental vs. colocação voluntária. O gatilho físico de perigo imediato é limpo.

---

### Sugestões de Ajuste nas Fixtures
1. **Diferenciação estrutural vs. arquitetônica (`stable`):** Explicitar na fixture se o salão possui aberturas nativas (`"aberturas_naturais": ["frestas/seteiras"]`), evitando falso positivo de dano estrutural quando o modelo gera correntes de ar.
2. **Qualificador de estado do item (`floor`):** Registrar o estado do item como `{"posicao": "no chão", "disposicao": "deliberada"}` e proibir termos de perda involuntária (`caído`, `largado`) sem evento prévio de desarme.

