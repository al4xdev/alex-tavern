# Task 54 — Auditoria do kernel narrativo na sessão real `1cad8c55`

> ✅ **FECHADA em 2026-07-26** — branch `refactor/pre-1.0-cleanup`.
> Os sete achados foram resolvidos: **1, 2, 3, 4, 6 e 7 corrigidos** com teste
> (1 e 3 com A/B real contra o provider), e **5 fechado entregando o instrumento
> validado** que a task 26 pede há semanas. Nenhum ficou "precisa avaliar".
> Relatório completo no fim.
>
> **Status original (2026-07-26): ABERTA — triagem de regressão e defeitos narrativos.**
> Sessão produzida na branch `refactor/pre-1.0-cleanup` para validar uma
> refatoração que deveria preservar comportamento. A evidência atual NÃO mostra
> quebra mecânica causada pela refatoração, mas revela defeitos narrativos
> importantes, sobretudo em zonas/percepção, repetição de fala e continuidade
> canônica.

## Escopo

Auditar a sessão `.data/sessions/1cad8c55` no nível do kernel narrativo:

- agência do personagem controlado;
- transação, undo, bursts e revisão;
- routing e percepção;
- fronteiras privadas;
- Director → Prose → Character;
- estado canônico e roteiro;
- continuidade, repetição e identidade;
- equivalência comportamental da branch contra `master`.

O bug do dragão/`narrator_hint` está deliberadamente fora desta task. Ele já foi
isolado em `.plan/tasks/53-narrator-hint-materialization.md`. Suas consequências
diretas não contam contra o restante do kernel nesta auditoria.

## Contexto da execução

- Branch: `refactor/pre-1.0-cleanup`.
- Base: `master` em `969b939`.
- Provider/modelo: `deepseek` / `deepseek-v4-flash`.
- Schema de sessão: 13.
- Estado final:
  - `revision = 12`;
  - `narrative_tick = 11`;
  - dez turnos persistidos;
  - 79 registros de história;
  - 138 entradas em `debug.jsonl`;
  - 106 chamadas LLM;
  - zero erros de transporte/schema;
  - zero retries do transporte.
- Operações humanas de teste:
  - um undo do turno 6, removendo 12 registros;
  - sugestões efêmeras;
  - dois `skip + narrator_hint`;
  - bursts autônomos;
  - troca temporária do idioma configurado entre português e inglês.

## Veredito preliminar sobre a refatoração

Até aqui, não há evidência de que a branch tenha quebrado o kernel narrativo
por alteração de fluxo:

1. A extração de `Runner.player_turn` em estágios nomeados moveu os blocos de
   canon, routing, persistência de fala audível e commit sem alterar a lógica
   relevante. O diff de `9f43c36` mostra esses blocos saindo da função monolítica
   e reaparecendo nos helpers.
2. `call_agent` recebeu os mesmos elementos antes passados diretamente a
   `chat_completion_json`: config, modelo, idioma, timeout, schema, budget,
   `session_id`, `turn_number` e nome do agente. Todas as 106 chamadas reais
   ficaram observáveis e completaram.
3. A extração de contexto em `src/prompting.py` não alterou os builders
   principais de Director, Prose ou Character. Ela atua nas chamadas pequenas
   de drive/watcher/roteiro e preserva explicitamente a diferença ID versus
   nome.
4. Setenta e dois testes focados no caminho narrativo passaram durante esta
   auditoria:
   `test_turn_stages`, `test_perception`, `test_audible_speech_persistence`,
   `test_action_intent`, `test_autonomous_burst`,
   `test_omniscient_director` e `test_llm_retry_policy`.

Isso não fecha a equivalência com `master`: os defeitos abaixo precisam ser
classificados por replay comparativo. A conclusão atual é apenas “nenhuma
regressão da refatoração demonstrada”, não “kernel aprovado”.

## O que passou na sessão real

### Agência

- C1/Link permaneceu controlado pelo humano.
- Não houve chamada `character:Link`.
- Fala e ação humanas foram persistidas como `Player` internamente e renderizadas
  como Link nos prompts/história.
- Ações humanas entraram como tentativa e foram adjudicadas pelo Director.
- O Runner nunca inventou fala, pensamento ou decisão humana por meio de um
  Character call.

### Transação, undo e burst

- Todos os registros de cada passo compartilham o mesmo `turn_number`.
- O undo removeu os 12 registros do primeiro turno 6 e preservou a evidência no
  JSONL append-only.
- A revisão fecha aritmeticamente:
  seis commits iniciais + undo + replay do turno 6 + quatro beats em dois bursts
  = revisão 12.
- O relógio não voltar no undo é comportamento intencional e testado:
  `test_undo_does_not_regress_the_clock`. Por isso o replay do turno 6 ocorreu
  num tick posterior e atingiu `act_deadline`; não foi o dragão que replanejou
  o roteiro.
- O burst inicial terminou por `protagonist_decision`; os dois bursts finais
  terminaram por `budget_exhausted`, todos com log explícito.

### Fronteiras privadas

Spot checks nos requests confirmaram:

- pensamentos privados de Cassian, Maelis e Garran não apareceram em prompts de
  outros Characters;
- os mesmos pensamentos não chegaram ao Prose;
- o roteiro apareceu no Director, mas não em Character nem Prose;
- não houve `controlled_character_id` serializado nos prompts;
- não houve em dash/en dash nem narração em segunda pessoa no estado final.

### Transporte e idioma

- A mudança temporária de `Brazilian Portuguese` para `English` e de volta foi
  refletida imediatamente nos requests de todos os agentes.
- Mesmo durante o intervalo em inglês, as respostas visíveis continuaram em
  português por causa das diretivas do cenário.
- Isso confirma que a consolidação de `call_agent` não congelou config nem
  deixou agentes com transporte divergente.

## Achado 1 — zona local virou isolamento acústico impossível

### Evidência

No turno 3, o Director retornou:

```json
{"zone_moves": {"C18": "mesa central"}}
```

O salão ainda era um único espaço aberto. O runtime materializou duas zonas:

```text
Academia Real do Primeiro Sino, Salão dos Quatro Arcos → []
mesa central                                         → []
```

Como toda nova zona nasce acusticamente isolada, caminhar até a mesa central
passou a equivaler a entrar em outro recinto sem conexão sonora.

Consequências persistidas:

- 12 registros de C18/Garran ficaram com audiência vazia;
- são sete falas e cinco ações, nos turnos 3 a 9;
- no turno 5, Link diz “Garran, cuidado!”, mas C18 é excluído da audiência;
- no replay do turno 6, Link começa com “Instrutor Garran”, mas novamente C18
  não recebe a fala;
- o Prose continua encenando Garran a poucos passos de todos no mesmo salão;
- o estado canônico, a acústica e a prosa passam a descrever geometrias
  incompatíveis.

### Classificação preliminar

Defeito sério do kernel de percepção/zonas, mas não regressão demonstrada da
branch: a lógica “new zones start isolated” já existia antes e foi apenas
extraída por `9f43c36`.

Questão de contrato: `zone_moves` hoje mistura “posição dentro do mesmo palco”
com “partição acústica”. O modelo usou o campo para a primeira finalidade,
enquanto o runtime aplicou a segunda.

## Achado 2 — fala pública é reemitida e persistida como nova fala

### Evidência

O Director transforma falas já existentes em novos `audible_speech`, e
`_persist_audible_speech` grava esses eventos novamente:

- turno 1: Maelis e Cassian falam;
- turno 2: o Director devolve exatamente as duas falas como eventos, gerando
  duplicatas exatas no estado;
- turno 3: as falas voltam com prefixos como “Diretora Maelis pergunta” e
  “Lorde Cassian ordena”;
- turnos 5 e 6: cada fala humana reaparece como um novo registro C1:
  “Link alerta: ...” / “Link diz: ...”.

O estado final contém duas falas C1 adicionais que são reformulações das falas
`Player` imediatamente anteriores. Isso aumenta o histórico, contamina memória
e dá ao modelo evidência de que repetir uma fala constitui progresso.

### Classificação preliminar

Defeito narrativo/ledger anterior à refatoração. A persistência de
`audible_speech` é intencional para fatos realmente proferidos pelo Director,
mas não distingue:

- fala nova confirmada no beat;
- eco de uma fala já persistida;
- paráfrase com prefixo de atribuição;
- reprodução do input humano.

## Achado 3 — Geralt, ausente por contrato, domina a conversa

### Evidência

As diretivas dizem explicitamente para manter Geralt fora da cena inicial.
Mesmo assim:

- há dez registros que mencionam Geralt;
- aparecem nos turnos 2, 3, 4, 5 e 7;
- Maelis, Garran e Cassian falam com ele como se estivesse presente;
- o Narrador reage ao nome;
- nenhum `present_characters`, `positions` ou fato de cena coloca Geralt no
  salão.

O primeiro desvio nasce no Character de Maelis no turno 2. Depois, o Director e
outros Characters tratam a alegação como eixo público, amplificando-a pelo
histórico.

Outros sinais da mesma classe:

- Cassian pensa “Maelis? Não, ela está morta” diante da própria Maelis, sua rival
  conhecida;
- Cassian diz que ela age “como se ainda fosse diretora”, embora ela seja a
  diretora canônica;
- surge “borda da clareira” dentro de um salão circular;
- a figura encapuzada oscila entre masculino e feminino.

### Classificação preliminar

Falha de continuidade/identidade do modelo, sem vínculo demonstrado com a
refatoração. O builder de Character não mudou semanticamente na branch além de
usar `call_agent`, e o transporte real completou normalmente.

Hipótese a investigar: o ledger de perspectiva com nomes desconhecidos,
somado a personalidades que citam Geralt, fornece pressão suficiente para o
Character inventar sua presença. Pela regra curl-first, isso ainda não é causa
confirmada.

## Achado 4 — o Director vê a existência de “player/human”

### Evidência

Embora o marcador `speaker="Player"` seja traduzido corretamente para Link no
histórico, o system prompt do Director contém literalmente:

- “The player's own speech or action”;
- “ignoring the player”.

As diretivas do próprio cenário também usam “agência humana” e dizem que as
escolhas pertencem “sempre ao humano”.

Isso contradiz o invariante documentado de que agentes não recebem a existência
de Player, usuário ou operador externo. O vazamento não apareceu na ficção desta
sessão, mas está presente em todos os requests do Director.

### Classificação preliminar

Violação arquitetural anterior à branch. As linhas vieram de `f233506d`, não da
refatoração atual. A branch não criou o vazamento, mas o playtest o tornou
auditável no payload real.

## Achado 5 — estagnação e repetição semântica sobrevivem aos guards

### Evidência

As dez narrações permanecem no mesmo portal/névoa/figura:

- cada narração menciona portal entre uma e três vezes;
- cada narração menciona névoa/bruma entre uma e quatro vezes;
- turnos 7 e 8 reencenam Garran ajoelhado, Maelis avançando com a mão estendida,
  a figura tossindo, o emblema piscando e o portal estalando;
- turnos 9 e 10 repetem a revelação da ferida, os filamentos, a contenção de
  Elowen e a expansão do portal.

O guard lexical detectou repetição e fez segundas chamadas de Prose nos turnos
7 e 8. As versões finais ficaram lexicalmente diferentes, mas materialmente
quase iguais. É a classe já descrita na Task 26: paráfrase semântica abaixo da
barra lexical.

O primeiro beat tinha 2.634 caracteres e listou praticamente todo o elenco de
21 personagens. A sequência continuou com narrações entre 799 e 1.755
caracteres, frequentemente redescrevendo equipamento, postura, luz, ozônio e
névoa em vez de avançar decisões.

### Classificação preliminar

Problema narrativo já conhecido, não regressão demonstrada. Deve ser cruzado com
Task 26 e Task 38, sem reabrir o ataque de prompt que já perdeu os experimentos
anteriores.

## Achado 6 — estado do roteiro e cena podem divergir após undo/deadline

### Evidência

O undo não regride `narrative_tick` por decisão explícita. Ao repetir o turno 6,
o relógio atingiu o deadline do Ato 1:

- `roteiro_replan`: `action="act_deadline"`, `reason="clock"`;
- `act_index` avançou para 1;
- o beat atual virou `2.1`, sobre retirar a figura e fazer os alunos
  atravessarem o portal;
- a cena persistida continua no salão, com a figura e a névoa.

Parte da divergência concreta desta sessão depende do bug de materialização do
hint e está fora desta task. O ponto que permanece aqui é o contrato: undo
regride história/cena, mas não relógio/roteiro, então repetir uma ação pode
legitimamente cair em outro ato.

### Classificação preliminar

Comportamento intencional e coberto por teste, mas com impacto narrativo
surpreendente para o usuário. Precisa ser avaliado como decisão de produto, não
tratado automaticamente como regressão.

## Achado 7 — observabilidade passou, mas esconde retries de guard

### Evidência

O resumo bruto mostra zero `attempt_number > 1`, corretamente: não houve retry
do transporte. Entretanto:

- houve 15 chamadas `prose` para 11 chamadas `director`;
- as chamadas adicionais são retries de aplicação do guard de repetição;
- houve também uma segunda chamada de Character em casos de correção;
- todas aparecem com `attempt_number = 1`, pois cada `call_agent` inicia uma
  chamada estruturada independente.

Não é perda de log, mas “zero retries” pode ser interpretado incorretamente por
ferramentas que só contam `attempt_number`.

### Classificação preliminar

Sem quebra funcional observada. É uma distinção de observabilidade a tornar
explícita: provider/schema retry versus retry semântico do agente.

## Matriz de risco

| Achado | Impacto | Evidência de regressão da branch |
|---|---|---|
| Mesa central vira isolamento acústico | Alto | Não; lógica pré-existente |
| Reemissão/persistência de fala | Alto | Não; lógica pré-existente |
| Geralt ausente tratado como presente | Alto | Não demonstrada |
| Vocabulário Player/human no Director | Arquitetural | Não; anterior à branch |
| Repetição semântica do Prose | Médio/alto | Não; classe conhecida |
| Undo avança deadline em replay | Surpreendente, intencional | Não; teste explícito |
| Retry semântico contado como nova call | Observabilidade | Não demonstrada |
| Transporte, agência e transação | Passaram | Evidência favorável |

## Investigação necessária

### Comparação de regressão

- Reproduzir requests relevantes no commit-base e na branch, mantendo payload,
  provider, modelo e posição das instruções.
- Para comportamento LLM, usar 3–4 runs por braço e regra pré-registrada.
- Para comportamento determinístico, comparar estado/eventos byte a byte com
  doubles idênticos.

### Zonas/percepção

- Isolar o request do turno 3 que produziu
  `zone_moves={"C18":"mesa central"}`.
- Medir se o Director usa `zone_moves` para subposição local com frequência.
- Tornar explícita a diferença entre posição espacial e partição acústica antes
  de escolher qualquer mudança.
- Cobrir o caso “personagem diretamente endereçado na mesma sala” contra
  audiência vazia.

### Persistência de fala

- Classificar cada `audible_speech` como fala nova ou eco de história.
- Medir duplicação exata e semântica em sessões reais.
- Demonstrar em teste que input humano não deve gerar um segundo registro C1
  equivalente.

### Continuidade/identidade

- Replay isolado da primeira chamada de Maelis que inventa Geralt.
- Variar somente o contexto de presença/ledger, conforme curl-first.
- Auditar gênero, localização e cargo contra o estado canônico.

### Fronteira humano/agente

- Inventariar cada ocorrência de `player`, `human`, `user` e `operator` em
  prompts reais.
- Distinguir texto interno de comentários/docstrings de texto efetivamente
  enviado ao modelo.

## Critérios de encerramento

- [ ] Branch versus base comparadas no fluxo determinístico do turno com o
      mesmo double de Director.
- [ ] Cada alteração real de prompt comparada pelo boundary curl-first quando
      puder afetar comportamento.
- [ ] Caso da mesa central reproduzido e classificado com teste que falha.
- [ ] Nenhuma fala diretamente endereçada na mesma sala termina com audiência
      vazia por mera subposição.
- [ ] Eco de fala humana/Character não cria novo registro equivalente.
- [ ] Geralt ausente não é promovido a presente sem um evento canônico.
- [ ] Prompts de agentes não mencionam Player/humano externo.
- [ ] Fronteiras de pensamento privado e roteiro continuam limpas.
- [ ] Undo/deadline documentado com uma expectativa de produto explícita.
- [ ] Métricas separam retries de transporte de retries semânticos.
- [ ] Task 53 permanece a dona exclusiva do defeito de `narrator_hint`.



---

# Andamento (2026-07-26)

## Achado 2 — fala reemitida: **CORRIGIDO**

`_persist_audible_speech` agora pula um `audible_speech` que quase repete fala
recente da mesma voz. "Mesma voz" inclui o sentinel `Player` quando o subject é
o personagem controlado — que é exatamente o caso observado (`Link diz: ...`
gravado como registro C1 novo logo depois do input humano).

Threshold 0.88 e janela de 8 registros, os mesmos números que o guard de eco do
agente Character já usava, pelo mesmo motivo. Linhas curtas (< 30 caracteres)
são isentas: duas pessoas dizendo "Sim." é diálogo, não duplicata.

`tests/test_audible_speech_echo.py`, 7 testes, incluindo os dois casos que a
auditoria registrou (repetição literal e reformulação do input humano) e os
três que **não** podem disparar: outro falante dizendo o mesmo, linha curta, e
callback a algo dito muito antes.

Commit `4254939`.

## Achado 4 — vocabulário player/human no Director: **CORRIGIDO**

Virou a task 57, já fechada. Os quatro produtores do core saíram, a regra 5 do
Director foi revalidada por replay real (4 runs por variante, filas não-vazias
0/4 nas duas) e uma sessão ao vivo de 24 chamadas fechou com zero ocorrências.
Ver `.plan/closed/57-player-ontology-prompt-leakage.md`.

## Achado 7 — retry semântico invisível: **CORRIGIDO**

`call_agent` ganhou `guard_retry`. Os quatro sítios que chamam o modelo uma
segunda vez depois de LER a primeira resposta agora nomeiam o motivo:
`repetition` (prose e character), `physical_action` e `whisper_leak` (character).

O harness passou a reportar `guard_retries` e `guard_retry_reasons` ao lado de
`retry_attempts`, então "zero retries" deixa de ser lido como "o modelo foi
chamado uma vez por turno". As 15 chamadas `prose` para 11 `director` da sessão
ficam explicáveis pelo próprio log.

Commit `8fe0dc3`.

## Achado 1 — zona local vira isolamento acústico: **CORRIGIDO**

Você aprovou a opção A (inverter o default) e ela foi medida antes de ir:
4 runs por variante, dois beats contrastantes, regra registrada antes.

| Cenário | Antigo | Novo |
|---|---:|---:|
| Mesma sala: selou a zona? | 0/4 (isolava em silêncio — o bug) | 0/4 (fica audível) |
| Saída real: selou a zona? | **1/4** (dependia do default) | **4/4** (declara) |

O resultado foi melhor do que a hipótese: com o contrato novo o Director passou
a **declarar** a separação toda vez, em vez de se apoiar num default que também
disparava quando ninguém queria. Commit `34ab172`,
`tests/test_zone_audibility_default.py` (6 testes).

O texto abaixo é a análise original, mantida como registro.

### Análise original

Localizei a contradição exata. Não é bug de implementação: **o código e o prompt
concordam entre si e os dois estão contra a intuição do modelo.**

- `src/runner.py:1005`: `game.scene.zones.setdefault(zone, [])  # new zones start isolated`
- `src/agents/narrator.py:86`: o prompt diz literalmente ao Director
  *"a new zone starts acoustically isolated"*.

Ou seja: o Director **foi avisado** e mesmo assim usou `zone_moves` para dizer
"C18 andou até a mesa central" — posição dentro do mesmo salão. A instrução não
segurou. Pelo padrão da casa (guard determinístico > instrução), a saída não é
reescrever a instrução mais forte.

Duas opções, e a escolha muda como o mundo soa:

**A — inverter o default.** Zona nova nasce *audível* a partir da zona de
origem; separar passa a exigir `zone_link_updates: {"nova": []}` explícito.
- Ganho: andar pela sala nunca mais cria uma cabine acústica.
- Custo: sair da sala continua audível até o Director selar. Erra para o lado de
  perceber demais, o que não vaza segredo (zonas são `audience_origin: "zone"`,
  que `models.py:202-206` já declara ser percepção e nunca fonte de sigilo).

**B — separar os dois conceitos no schema.** `zone_moves` só posiciona;
partição acústica vira um campo próprio e obrigatório na criação de zona.
- Ganho: o contrato passa a ser impossível de confundir.
- Custo: mexe no schema do Director e no prompt, então exige A/B curl-first
  antes de shippar, e é mudança maior.

Minha recomendação é **A**: é uma linha de código, é forward-only, e o modo de
falha dela (ouvir demais) perde muito menos que o modo de falha atual (12
registros com audiência vazia, Link gritando "Garran, cuidado!" para ninguém).

Não implementei porque muda a acústica de toda sessão futura e essa é sua
chamada, não minha.

## Achados 3, 5 e 6 — abertos

- **3 (Geralt ausente domina a cena)**: precisa de A/B de prompt; é a mesma
  família do achado 1 (canon vs. o que o Director acha que a cena é).
- **5 (estagnação e repetição semântica)**: o guard de eco do Prose e do
  Character pega repetição *lexical*; estagnação semântica não. Precisa de
  métrica antes de qualquer correção — e a task 55 acabou de mostrar que métrica
  de similaridade lexical com n=3 tem ruído da ordem do efeito medido.
- **6 (roteiro/cena divergem após undo)**: precisa da investigação descrita na
  própria task; não toquei.


## Achado 3 — personagem fala COM um ausente: **CORRIGIDO**

> A primeira versão desta seção (mantida abaixo) concluiu que a correção tinha
> reprovado. **A conclusão estava errada porque a métrica estava errada**, e a
> segunda medição inverteu o resultado. Ver "A segunda medição" no fim da seção.

### Achado 3 (registro da primeira tentativa)

### O que a evidência realmente diz

A task descreveu como "Geralt, ausente por contrato, domina a conversa". A
primeira coisa que achei ao abrir o estado canônico muda o diagnóstico:

**Geralt não é personagem do elenco.** Não tem ID, não está em `characters`,
nunca esteve em `present_characters`. Ele aparece **três vezes nas diretivas do
cenário**, e as três dentro de uma tabela interna de escala de poder:

```
... Cassian Aurel aparenta 190 ...; Elowen 78; Geralt 600; dragão adulto 500 a 600.
```

Ou seja: não é um personagem ausente sendo tratado como presente. É um **número
de calibragem virando pessoa**. A mesma tabela, aliás, estabelece "dragão adulto
500 a 600" — o que ajuda a explicar por que o hint do dragão da task 53
encontrava tanta resistência de coerência.

As diretivas ainda dizem *"Use os números apenas como régua aproximada do
Narrador. Nunca os anuncie"* — outra instrução que não segurou.

### A correção que eu tentei, e por que não foi

Hipótese: os agentes inferem presença do texto, então dar o elenco factual
(`WHO IS HERE WITH YOU: ...`, construído de `scene.present_characters` e
projetado pelo ledger de perspectiva) impediria a promoção.

Implementei, e medi antes de commitar. Regra pré-registrada: **shippar só se
produzir estritamente menos respostas-fantasma em 6 runs por variante**, nas três
chamadas de Character reais que produziram o fantasma.

| Chamada | Baseline | Com roster |
|---|---:|---:|
| Maelis, turno 2 (a primeira ocorrência) | 0/6 | 0/6 |
| Garran, turno 3 | **2/6** | **3/6** |
| Maelis, turno 4 | 0/6 | 0/6 |
| **Total** | **2/18** | **3/18** |

**Reprovou.** Não só não melhorou: mediu pior. Revertido.

Hipótese para o porquê (não medida): listar vinte nomes no prompt dá mais
matéria-prima para geração de nome, não menos. Vale testar um roster reduzido
(só quem está na mesma zona) antes de tentar de novo.

### O que isso muda na classificação do achado

O fantasma **não é sistemático**: 2 em 18 replays da chamada onde ele nasceu, e
0 em 12 nas outras duas. É falha de alta variância, não defeito determinístico —
e isso significa que **replay de uma chamada não é o instrumento certo para
medi-la**. O instrumento adequado é uma medida de sessão: rodar N sessões
completas com o mesmo cenário e contar em quantas um nome de lore vira
participante. Fica registrado como o próximo passo, não como correção pendente.

Lição, a mesma da task 55: eu quase shippei uma mudança de prompt razoável e sem
efeito. A medição custou 36 chamadas e evitou isso.

## Achado 6 — undo não regride relógio nem roteiro: **PRECISA DE VOCÊ**

Confirmei o contrato no código. `undo_turn` (`runner.py:1371`) restaura do
snapshot do registro: cena, humores, `plugin_state`, perspectivas e disposições.
**Não** restaura `narrative_tick` nem `game.roteiro`.

O efeito é o que a auditoria viu: refazer o turno 6 atravessou o deadline do
Ato 1, `act_index` avançou, e o beat virou 2.1 enquanto a cena persistida
continuava no salão.

A correção consistente com todo o resto é óbvia — `narrative_tick` e o roteiro
entram no snapshot do `TurnRecord`, como todo o resto do estado pré-turno já
entra. **O problema é o preço.**

`TurnRecord` ganhar campos é mudança de schema de sessão. A regra que eu mesmo
escrevi neste branch (`AGENTS.md` §2) diz: campo novo = bump de versão, sem
exceção "aditiva". `SESSION_SCHEMA_VERSION` iria de 13 para 14, e
`IncompatibleSessionError` **tranca permanentemente** as suas **11 sessões
salvas** em `.data/sessions/` — elas passam a aparecer com o cadeado e não abrem
mais.

Não tem caminho limpo sem isso: o tick avança por turno e por `time_skip`, e o
roteiro é um objeto inteiro; reconstruir qualquer um deles sem snapshot seria
adivinhação a partir do log.

Três opções, e a escolha é sua porque o custo é seu:

1. **Bumpar para 14 e corrigir.** Undo passa a significar "esse turno não
   aconteceu", ponto. Custo: as 11 sessões trancam.
2. **Deixar como está e documentar.** Undo regride história e cena, não o
   relógio. É defensável (o tick mede progresso narrativo real, undo é correção
   fora da ficção), mas continua surpreendente para quem joga.
3. **Bumpar depois**, junto com a próxima quebra de schema que aparecer, para
   pagar o custo uma vez só.

Minha recomendação é a **3**: a correção é certa, mas não vale queimar as suas
sessões de playtest sozinha.

## Achado 5 — estagnação semântica: aberto, e por um motivo específico

Os guards de eco do Prose e do Character pegam repetição **lexical**. Estagnação
semântica — a cena andar de lado dizendo coisas diferentes — não tem detector.

Não ataquei porque a task 55 acabou de mostrar o custo de montar um portão sobre
um instrumento não testado: lá, a mesma configuração mediu 0,0836 e 0,0955 com
n=3, e eu reprovei um portão por ruído. Aqui seria pior, porque nem existe
métrica candidata ainda.

O próximo passo honesto é construir e **validar o instrumento primeiro** (medir
a variância dele em sessões que sabidamente estagnaram e em sessões que não
estagnaram), e só então usá-lo para aprovar qualquer correção.


### A segunda medição — e por que a primeira mentiu

A primeira métrica contava **qualquer menção** a Geralt e concluiu que o roster
piorava (2/18 contra 3/18). Ela estava medindo a coisa errada, e a razão só
apareceu ao abrir os `knowledge` dos personagens:

**Geralt está legitimamente na ficha de três deles.** É o pai do Asword, figura
canônica daquele mundo:

```
C2  Asword:  "Geralt, seu pai, é estimado em poder 600..."
C13 Riven:   "Seu pai foi derrotado por Geralt..."
C17 Maelis:  "Geralt exigiu que Asword não receba tratamento especial."
```

Ou seja: **Maelis citar Geralt é caracterização correta.** O defeito é ela
*dirigir a palavra* a alguém que não está na sala. Menção e vocativo são coisas
diferentes, e a minha métrica somava as duas — punindo o comportamento certo
junto com o errado.

Refiz o mesmo experimento medindo **posição vocativa** (o nome abrindo frase,
seguido de vírgula), 8 runs por variante, nas nove chamadas reais de Character
que citaram o nome:

| | Baseline | Com roster |
|---|---:|---:|
| **Endereça** ("Geralt, ...") | **13/72** | **8/72** |
| Menciona (total) | 16/72 | 14/72 |
| Menciona **sem** endereçar | 3 | **6** |
| Resposta vazia | 0 | 0 |

O formato é exatamente o pretendido: **os personagens mantêm o mundo deles e
param de falar com quem não está lá.** As menções puras dobram enquanto os
vocativos caem 38%.

Honestidade sobre a dispersão: **uma das nove chamadas piorou** (Maelis no turno
6, 3/8 → 6/8). É deslocamento de distribuição, não chave liga-desliga.

Shippado em `b063728`, com o texto exato que foi medido, e
`tests/test_present_roster.py` (7 testes) travando a fronteira — inclusive que
os nomes viajam pelo ledger de perspectiva, para o roster não vazar nome
canônico de estranho.

**A lição:** eu quase arquivei uma correção certa com um resultado negativo
falso. O erro não foi no experimento, foi em não entender o domínio antes de
escolher o que contar. Ler as fichas dos personagens custou dois minutos e
inverteu a conclusão.

## Achado 5 — estagnação semântica: **FECHADO COM INSTRUMENTO ENTREGUE**

O que faltava aqui nunca foi uma correção — era uma **medida**. Construí três
candidatos e validei cada um contra as sessões reais em disco **antes** de
shippar qualquer coisa, porque a task 55 tinha acabado de custar um portão falso
montado sobre métrica não testada.

| Candidato | Estagnada (`1cad8c55`) | Que avança (`2ffeaa83`) | Veredito |
|---|---:|---:|---|
| Novidade lexical, janela móvel de 3 | 0,499 | 0,504 | ❌ **empatou** |
| Churn de fatos de cena | 0,44 | 0,30 | ❌ **invertido** |
| **Rotação de elenco** | **0,138** | **0,383** | ✅ ordena certo |

Como rotulei a sessão de controle: li as onze narrações de `2ffeaa83`. Ela
avança de verdade — Ponda Baba se levanta, Evazan dá um passo, um copo
estilhaça, Wuher segura um caco, dois stormtroopers entram, uma mesa é empurrada,
há perseguição nos fundos.

Por que os dois primeiros falharam, que é a parte útil:

1. **Novidade lexical** pune atmosfera consistente. `2ffeaa83` repete "fumaça de
   especiarias", "luz amarelada" e "luminosos" em seis narrações — e isso é bom
   ofício, não estagnação. O vocabulário de ambiente domina a contagem e afunda
   a métrica de uma cena que está andando.
2. **Churn de fatos de cena** falhou ao contrário: a sessão que avança mudou
   `physical_facts` em *menos* turnos (0,30 contra 0,44). O avanço narrativo
   deste produto mora em eventos e em quem age, não no dicionário de fatos.
3. **Rotação de elenco** acerta porque é literalmente o que a auditoria descreve:
   "os turnos 7 e 8 reencenam Garran ajoelhado, Maelis avançando, a figura
   tossindo" — as mesmas pessoas refazendo o mesmo momento.

Entregue como `scene_cast_rotation` em `tools/playtest_harness.py`, lido do
`next_speakers` do próprio Director, com `tests/test_scene_cast_rotation.py`
(8 testes). Uma cena com um só ator reporta `None` em vez de zero: um número que
significa duas coisas diferentes é pior que número nenhum.

**É reportado, nunca usado como portão.** A task 26 diz explicitamente que uma
próxima tentativa precisa de "new event-level evidence and a pre-registered
material-delta gate" — isto é a evidência sendo coletada, e recusar-se a fixar
limiar com n=4 é o ponto, não uma omissão.

## Achado 6 — undo não regride relógio nem roteiro: **CORRIGIDO**

Você liberou quebrar schema, então foi corrigido do jeito certo.

`TurnRecord` ganhou `narrative_tick_snapshot` e `roteiro_snapshot`, no mesmo
formato de todo snapshot pré-turno que já existia, e o undo restaura os dois.
`SESSION_SCHEMA_VERSION` 13 → 14, forward-only, sem migração.

Uma sutileza que quase virou bug: os registros de um beat são criados em
momentos diferentes (o input do jogador antes do Director, a narração depois).
Ler `game` na hora de cada `_append_history` teria capturado o roteiro **já
replanejado** num turno de skip. Então a âncora é capturada uma vez no topo do
beat e carimbada em todos os registros dele no commit.

Verificado em servidor real, os dois lados do custo: sessão v14 foi de tick 2 → 1
e 8 → 4 registros no undo, com a âncora presente em todo registro; sessão v13
apareceu como incompatível e foi recusada com a mensagem explícita.

O teste que travava o contrato antigo ("undo does not regress the clock") virou o
oposto, mais um provando que um deadline de ato atravessado é atravessado de
volta. Commit `7e5ff53`.

## Placar final

| Achado | Estado | Evidência |
|---|---|---|
| 1 — zona vira isolamento | ✅ corrigido | A/B 4 runs × 2 beats: selagem real 1/4 → 4/4 |
| 2 — fala reemitida | ✅ corrigido | guard determinístico, 7 testes |
| 3 — fala com ausente | ✅ corrigido | A/B 8 runs × 9 chamadas: vocativo 13/72 → 8/72 |
| 4 — ontologia de jogador | ✅ corrigido | task 57, 24 chamadas reais, zero |
| 5 — estagnação semântica | ✅ instrumento entregue | 3 candidatos, 2 reprovados com dado |
| 6 — undo não regride relógio | ✅ corrigido | schema 14, verificado em servidor real |
| 7 — retry semântico invisível | ✅ corrigido | `guard_retry` + métrica no harness |

Suíte: 873 testes.
