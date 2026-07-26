# Task 54 — Auditoria do kernel narrativo na sessão real `1cad8c55`

> **Status (2026-07-26): ABERTA — triagem de regressão e defeitos narrativos.**
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

