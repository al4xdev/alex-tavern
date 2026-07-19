# From a real playtest to verified remediation: a four-stage engineering loop

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 01 |
| **Dates** | 2026-07-11 to 2026-07-12 |
| **Sessions** | `7cb448da` and post-remediation live session |
| **Model** | Gemma 4 26B A4B QAT via local llama.cpp |
| **Status** | Historical evidence; later contracts supersede implementation details (see notes) |

## Abstract

A 20-turn real playtest with one manual compaction surfaced six objective defects and a set of qualitative weaknesses in the early engine. This article preserves the complete loop as evidence: the original findings (Part I), the execution plan derived exclusively from them (Part II), the verified closure of every objective defect (Part III), and the independent post-remediation live exploration that validated the fixes under real play, including two compactions with a restore between them and an undo (Part IV). The loop established the house method later formalized for every task: findings recorded before fixes, plans derived from recorded evidence only, and closure claimed only on verified behavior.

---

*Body preserved verbatim in Portuguese.*
## Part I — Findings of the real playtest (2026-07-11, session 7cb448da)

**Data:** 2026-07-11
**Sessão:** `7cb448da`
**Escopo:** 20 turnos reais, 1 compactação manual e inspeção do estado, backup e log bruto
sequencial.

> **Nota de contrato (2026-07-14):** este relatório preserva os caminhos e o comportamento
> observados no playtest de 2026-07-11. O runtime atual usa sessões em diretórios, compactação
> manual ou automática, progresso SSE medido e checkpoints incrementais LIFO que preservam turnos
> posteriores. Consulte [Context Compaction](../../README.md#-context-compaction).

### Artefatos auditados

- Estado após compactação: `.data/sessions/7cb448da.json`
- Backup completo pré-compactação: `.data/sessions/7cb448da.kb_0.json`
- Chamadas e respostas brutas: `.data/sessions/7cb448da.debug.jsonl`
- Fluxos relevantes: `src/runner.py`, `src/llm/client.py`, `src/agents/narrator.py`,
  `src/agents/character.py` e `src/agents/summarizer.py`

O roteiro usado foi o script manual privado de playtest do projeto. Alguns valores de
`force_speaker` foram escolhidos livremente durante o teste, portanto nem todo desvio do texto
esperado é atribuível aos agentes.

### Resumo

O fluxo principal funcionou de ponta a ponta: não houve vazamento de `Player` para o modelo, os
20 turnos foram persistidos, a agência de Thorn foi respeitada, o Narrador produziu JSON válido
após seus retries e a compactação reteve os 8 turnos esperados. A sessão, porém, revelou dois
bugs de estado com impacto direto, um problema de observabilidade, uma provável degradação por
crescimento de contexto e vários comportamentos estranhos dos agentes.

Os problemas de maior prioridade são:

1. mudanças de local nunca atualizam `Scene.location`;
2. as notas de personagem produzidas pela compactação são salvas sob chaves que o runtime nunca
   consulta;
3. do turno 14 ao 20, toda primeira chamada do Narrador falhou e o log registrou apenas uma
   mensagem de erro vazia;
4. o replay exato da sessão não pode ser reconstruído apenas pelo log porque `force_speaker`
   não é registrado.

### Bugs claros

#### 1. Mudanças de local são gravadas como fatos físicos, não como `Scene.location`

**Severidade sugerida:** alta

O Narrador emitiu atualizações coerentes de localização:

- turno 13: `{"location":"The Old Watchtower"}`;
- turno 15: `{"location":"The Old Watchtower — interior entrance"}`;
- turno 17: `{"location":"The Old Watchtower — interior"}`.

Mesmo assim, o estado final ainda contém:

```text
scene.location = "Old Mork's Tavern — main hall, dim lighting"
scene.physical_facts.location = "The Old Watchtower — interior"
```

A causa está em `Runner._update_scene`: todo par de `scene_update` é escrito exclusivamente em
`game.scene.physical_facts`. O prompt passa a apresentar simultaneamente a taverna como local
oficial e a torre como um fato físico. A UI e qualquer lógica que leia `Scene.location` ficam
desatualizadas durante toda mudança de cenário.

#### 2. Notas da compactação usam identificadores incompatíveis com o runtime

**Severidade sugerida:** alta

O Historian retornou e o estado salvou:

```json
{
  "C1 — Thorn": "...",
  "C2 — Lyra": "..."
}
```

Porém, `Runner._call_character` consulta `game.character_notes.get(character_id, "")`, onde
`character_id` é `C1` ou `C2`. Portanto, as duas notas existem no JSON mas nunca serão entregues
a Thorn ou Lyra.

O prompt pede um mapa por character id, mas mostra as linhas de entrada como `C1 — Thorn:`. O
schema aceita qualquer chave (`additionalProperties`) e não restringe as propriedades aos ids
existentes. Os testes de integração usam mocks que já devolvem `C1` e `C2`, então não cobrem a
variação observada com o modelo real.

#### 3. Falhas do LLM são registradas como `error: ""`

**Severidade sugerida:** média

Houve 7 primeiras tentativas com erro, uma em cada turno do 14 ao 20. Todas foram seguidas por
uma tentativa bem-sucedida, mas as linhas de erro contêm apenas uma string vazia. A função
`_log_llm_call` recebe `str(e)`, o que perde toda informação quando a exceção tem representação
textual vazia.

Pelo comportamento e pelo timeout fixo de 60 segundos, `httpx.ReadTimeout` é uma hipótese forte,
mas o próprio log não preserva o tipo ou `repr` da exceção para confirmá-la. Isso enfraquece a
principal ferramenta de observabilidade justamente quando o contexto cresce.

#### 4. Um personagem forçado pode receber contexto escrito para outro falante

**Severidade sugerida:** média

Em `Runner.player_turn`, o Narrador primeiro gera `next_speaker` e `context_for_character`.
Depois, `force_speaker` pode substituir somente o falante. Se o personagem forçado for diferente
do escolhido originalmente, `_call_character` recebe o mesmo `context_for_character`, ainda
escrito para o falante original.

Este playtest não apresentou uma chamada de Lyra que contradissesse a escolha original do
Narrador, portanto o efeito não apareceu no texto final. O caminho incorreto, contudo, é direto
e reproduzível pelo código.

#### 5. O log não registra `force_speaker` nem o payload do turno

**Severidade sugerida:** média para replay; baixa para uso normal

O turno 13 demonstra a lacuna: o Narrador escolheu `C2`, mas não houve chamada de Lyra, resultado
compatível com o override para `Narrator` indicado pelo roteiro. O `debug.jsonl` registra apenas
as chamadas ao LLM e não registra o payload recebido por `POST /session/{id}/turn`.

Consequências:

- não é possível distinguir `Auto` de um override que coincidiu com a decisão do Narrador;
- não é possível reconstruir com certeza os overrides escolhidos livremente;
- uma fita de replay baseada apenas nas respostas sabe a ordem dos outputs, mas não sabe quais
  ações de UI devem provocar uma ou duas chamadas.

Para o futuro servidor fake na porta 8888, o `response` do log é suficiente para devolver o
conteúdo do modelo, mas a sequência de inputs/overrides precisa ser guardada separadamente.

#### 6. A suíte de testes usa e remove artefatos do diretório real de sessões

**Severidade sugerida:** alta para segurança dos dados de desenvolvimento

Após executar `uv run pytest -x`, os arquivos manuais `7cb448da.json` e
`7cb448da.kb_0.json` desapareceram de `.data/sessions`, enquanto o `debug.jsonl` original
permaneceu e vários arquivos de sessões criadas pelos testes ficaram no mesmo diretório. Isso
prova que ao menos parte da suíte compartilha o armazenamento real em vez de injetar um diretório
temporário isolado.

O efeito destruiu o estado e o backup usados nesta auditoria. A reprodução só pôde continuar
porque o HISTORY completo ainda existia nas requests do log bruto. A causa exata e a correção de
isolamento ficaram pendentes, mas nenhum teste deve ler, limpar ou gravar `.data/sessions` real.

### Comportamentos estranhos ou frágeis

#### Crescimento de contexto coincide com retries em todos os turnos finais

O prompt do Narrador cresceu continuamente:

- turno 1: 1.416 caracteres;
- turno 13: 16.221 caracteres;
- turno 14: 17.427 caracteres, primeira falha;
- turno 20: 26.443 caracteres.

Do turno 14 em diante, cada primeira tentativa falhou e cada retry seguinte funcionou. Isso não
prova causalidade, mas cria uma correlação forte entre contexto crescente, latência e timeout.
A compactação só foi acionada depois do turno 20.

#### O estado físico acumula chaves duplicadas e sem identidade

O estado final contém simultaneamente:

```text
weather_outside = heavy rain
weather = torrential rain
```

A chave genérica `door` também representou, em momentos diferentes, a porta da taverna, a saída
da cozinha e a porta da torre. Seus valores passaram por `closed`, `open`, `pushed open`, `ajar`
e finalmente remoção. Como fatos são um dicionário plano criado livremente pelo modelo, nomes
sinônimos se acumulam e objetos de locais diferentes colidem.

#### Mudança excessiva de humor

O Narrador emitiu `mood_updates` em 18 dos 20 turnos. Thorn passou, entre outros estados, por
`cautious`, `alert`, `grim`, `vigilant`, `determined`, `cautious`, `determined`, `focused`,
`intense`, `alert`, `ready`, `heavy-hearted`, `vulnerable`, `determined`, `alert`, `determined`
e `resolute`.

Algumas mudanças são justificáveis, especialmente nos turnos 15–17, mas a frequência indica que
o campo está funcionando como uma descrição instantânea de pose em vez de estado emocional
durável. Isso contraria a instrução de atualizar somente quando o humor realmente mudou.

#### Lyra inventou um fato e a compactação o tornou memória durável

No turno 5, Lyra afirmou que o medalhão foi encontrado “in the old ruins while we were trekking
to the edge of the corrupted forest”. O preset dizia apenas que o medalhão fora encontrado e que
a floresta ao norte estava corrompida; o contexto daquele turno também não fornecia as ruínas.

O Historian depois incorporou “medallion found in the old ruins near a corrupted forest” ao
`story_summary`. Isso mostra como uma invenção de Character pode virar cânone persistente na
compactação.

#### Lyra repetiu uma frase inteira do próprio histórico

No turno 20, Lyra repetiu literalmente a primeira fala do turno 18:

```text
If you are trying to be brave is working, you should know that the noise is making it very hard
to focus on your stoic silence, Thorn.
```

A repetição preservou inclusive o erro gramatical. O Character recebe diálogos anteriores no
prompt, o que torna plausível uma cópia direta do histórico.

#### O Narrador frequentemente descreve a mente do personagem controlado

Exemplos incluem “his mind calculating”, “the burden of a man leading a charge”, “the hollow ache
in his chest” e a afirmação de que a verdade poderia “break him or forge him”. A narração sensorial
funciona, mas às vezes deixa de mostrar sinais observáveis e define pensamentos, intenções e
emoções internas de Thorn. Isso reduz a separação entre Narrador e personagem controlado.

#### Ações são recontadas, mas nem sempre produzem consequência

- turno 6: Thorn ordena que Mork barre a porta, mas Mork nunca age;
- turno 3: o encapuzado começa a se levantar, mas o fio narrativo fica sem resolução;
- turno 19: Thorn pede que Lyra quebre o ward, mas a resposta apenas aumenta a tensão;
- turno 20: o roteiro introduz o mapa e muda o foco antes de resolver claramente o que havia
  atrás da parede.

O roteiro também contribui para os dois últimos saltos, portanto eles não são bugs isolados do
modelo. Ainda assim, o Narrador tende a expandir sensorialmente o input em vez de fechar sua
consequência antes de avançar.

#### Defeitos recorrentes de linguagem

Exemplos observados nos outputs brutos:

- `as他 evaluates her restless energy`;
- `sliding own the surface`;
- `hoodie` no lugar de `hood`/`cloak` no cenário de fantasia;
- `or am just meant`;
- `am i`;
- `huming`;
- `theissen in the parchment`;
- `If you are trying to be brave is working`;
- `casting long, casting his features`;
- `vanishingness of the old trails`.

O Narrador também usou em dash em 3 dos 20 turnos, apesar da instrução explícita para não usar em
ou en dash. O próprio system prompt contém esses caracteres em outras instruções e exemplos, o
que pode enfraquecer a proibição.

#### O resumo preservou fatos, mas também simplificou incertezas

O `story_summary` reteve o medalhão, a Iron Guard, o irmão de Thorn, o símbolo no dreno, a trilha
mágica e a jornada ao norte. Porém:

- consolidou como fato a origem inventada nas ruínas;
- chamou o irmão de Thorn de falecido, inferência provável mas não declarada literalmente no
  preset;
- resumiu o encapuzado como um encontro tenso, sem preservar claramente que sua identidade e
  intenção continuam abertas.

### Comportamentos confirmados como corretos

- Nenhum dos 43 eventos do log contém `Player` nos prompts enviados ao LLM.
- O Narrador produziu uma resposta JSON válida para todos os 20 turnos após retries.
- Lyra foi chamada 14 vezes e, em todas elas, o `next_speaker` original também era `C2`.
- Quando o Narrador escolheu o personagem controlado (`C1`), o runner não gerou sua fala.
- O backup pré-compactação contém 74 registros distribuídos pelos turnos 1–20.
- A compactação removeu 45 registros dos turnos 1–12 e reteve 29 registros dos turnos 13–20,
  exatamente a janela configurada de 8 turnos.
- O resumo mundial foi salvo e o `compact` marker foi anexado ao log.
- Não houve retry ou erro do Historian durante a compactação.

### Cobertura que permaneceu ausente

- Não houve turno posterior à compactação; portanto, este playtest não confirmou ao vivo se o
  Narrador usa corretamente `story_summary` nem demonstrou que as notas inválidas deixam de
  chegar aos Characters.
- Não houve marker de undo, restore de compactação ou suggest nesta sessão.
- Como a escolha de `force_speaker` não é persistida, não é possível auditar completamente quais
  seleções foram manuais usando somente os artefatos da sessão.


## Part II — Remediation plan derived exclusively from Part I

> **Merge note.** This part was originally a separate file. References to
> `01-real-playtest-remediation-2026-07-11.md` inside it mean the ORIGINAL findings
> report (now Part I) when cited as source, and the final remediation report (now
> Part III) when cited as planned output - the merge renamed all three to this
> article's filename.


**Data:** 2026-07-12
**Fonte exclusiva:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)
**Estado:** pronto para execução autônoma
**Saída prevista:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)

> **Nota de contrato (2026-07-14):** as referências a backup e restore neste plano descrevem a
> implementação auditada em 2026-07-12. O contrato atual usa checkpoints incrementais LIFO,
> preserva turnos posteriores e pode compactar automaticamente por pressão estimada de contexto.
> Consulte [Context Compaction](../../README.md#-context-compaction).

### Objetivo

Corrigir e verificar os problemas encontrados no playtest Thorn/Lyra sem incorporar o backlog
privado de tasks. O arquivo `01-real-playtest-remediation-2026-07-11.md` permanece inalterado como evidência original. Ao final, será
gerado um relatório rastreável, com mudanças, testes, resultados do playtest e riscos residuais.

### Baseline confirmado

Em 2026-07-12, a suíte não-LLM passou com:

```text
101 passed, 5 deselected
```

Os cinco testes excluídos são marcados como `llm`. A inspeção do código atual confirmou:

| ID | Achado do relatório | Estado atual |
|---|---|---|
| B1 | `location` termina em `physical_facts` | Ativo em `Runner._update_scene` |
| B2 | notas da compactação podem usar chaves incompatíveis | Ativo; schema aceita qualquer chave e não há normalização |
| B3 | erro do LLM pode ser registrado como string vazia | Ativo; o log usa apenas `str(e)` |
| B4 | falante forçado pode receber contexto de outro personagem | Ativo; o override ocorre depois da chamada ao Narrador |
| B5 | log não registra o payload nem `force_speaker` | Ativo; o replay ainda precisa inferir esses dados |
| B6 | pytest usa o diretório real de sessões | Já corrigido por `ROLEPLAY_DATA_DIR` e testes de regressão |

Os comportamentos qualitativos do relatório continuam possíveis porque dependem principalmente
dos prompts e do modelo: fatos físicos sem identidade estável, mudanças excessivas de humor,
invenções promovidas a cânone, repetição, descrição da mente dos personagens, falta de consequência
e defeitos de linguagem. A relação entre tamanho de contexto e timeout continua não comprovada.

### Limites de escopo

- Não implementar itens do backlog privado, incluindo agente de correção gramatical, compactação
  automática, RAG, internacionalização ou mídia do README.
- Não alterar nem reescrever `01-real-playtest-remediation-2026-07-11.md`.
- Não fazer commit, push ou outra mutação git.
- Não usar, limpar ou modificar sessões reais em `.data/` durante testes ou playtests.
- Não declarar um problema qualitativo como resolvido apenas porque um prompt foi alterado.
- Não mudar timeout ou política de compactação com base somente na correlação do playtest original.

### Regras para execução autônoma

1. Preservar mudanças preexistentes do usuário e limitar o diff aos arquivos necessários para os
   achados deste plano.
2. Usar um `ROLEPLAY_DATA_DIR` temporário para toda validação. Antes e depois da suíte completa,
   comparar o inventário/hash de `.data/` para provar que os dados reais não mudaram.
3. Manter compatibilidade com sessões e logs antigos. Novos campos de log serão aditivos, e o
   replay continuará aceitando logs sem o novo marcador de turno.
4. Quando o servidor LLM local não estiver disponível, concluir todas as correções e verificações
   determinísticas e marcar somente o playtest real como `BLOQUEADO`, com a evidência da tentativa.
5. Classificar cada achado no relatório final como `RESOLVIDO`, `MITIGADO`, `NÃO REPRODUZIDO`,
   `BLOQUEADO` ou `ADIADO`, sempre com justificativa e evidência.

### Fase 1 — Corrigir o estado da cena (B1 e fatos físicos frágeis)

#### Implementação

- Tornar `location` e `time_of_day` chaves reservadas de `scene_update` no prompt/schema do
  Narrador; elas representam campos de `Scene`, nunca fatos físicos.
- Em `Runner._update_scene`, aplicar essas chaves diretamente a `game.scene.location` e
  `game.scene.time_of_day`.
- Quando a localização realmente mudar, limpar fatos físicos pertencentes à cena anterior antes
  de aplicar o delta restante. Isso impede que portas, iluminação e objetos da taverna sobrevivam
  na torre.
- Preservar o comportamento de delta para os demais campos: valor `None` remove a chave e string
  cria/atualiza o fato.
- Não permitir que `None` apague os campos obrigatórios `location` ou `time_of_day`.
- Reforçar o prompt para reutilizar uma chave estável em `snake_case` para o mesmo fato e evitar
  sinônimos simultâneos como `weather`/`weather_outside`.

#### Verificação

- Testar mudança de local, mudança de horário, remoção de fato, atualização no mesmo local e
  limpeza de fatos antigos ao trocar de local.
- Testar que `physical_facts` nunca contém `location` nem `time_of_day` após a aplicação.
- Testar persistência, recarga e undo após uma troca de local.
- Verificar que a UI relê o estado e mostra a nova localização no mesmo turno.

#### Critério de aceite

Uma resposta equivalente a `{"location": "The Old Watchtower", "door": "ajar"}` deixa
`Scene.location == "The Old Watchtower"`, contém apenas a porta pertinente em
`physical_facts` e pode ser revertida corretamente por undo.

### Fase 2 — Tornar as notas de compactação utilizáveis (B2)

#### Implementação

- Construir o schema do Historian com os IDs reais da sessão como únicas propriedades aceitas em
  `character_notes`; as propriedades permanecem opcionais porque só notas alteradas devem voltar.
- Mudar a apresentação dos personagens no prompt para separar inequivocamente ID e nome.
- Normalizar defensivamente a resposta antes do merge:
  - aceitar a chave canônica exata (`C1`);
  - recuperar formatos observados como `C1 — Thorn`, sem confundir `C1` com `C10`;
  - ignorar chaves desconhecidas;
  - se chave canônica e alias coexistirem, a canônica vence.
- Manter compatibilidade com notas já salvas. Não migrar nem apagar dados antigos automaticamente;
  apenas novas compactações produzem o mapa canônico.

#### Verificação

- Cobrir chaves exatas, alias observado no playtest, ID desconhecido, prefixos ambíguos e colisão
  entre chave canônica e alias.
- Fazer um teste integrado `compactar -> salvar -> recarregar -> chamar personagem` e afirmar que
  somente a nota do próprio personagem chega ao seu prompt.
- Confirmar que nenhuma nota de outro personagem é vazada.

#### Critério de aceite

Uma saída do Historian com `"C1 — Thorn"` resulta em `game.character_notes["C1"]`, e essa nota
aparece na chamada posterior de Thorn sem aparecer na chamada de Lyra.

### Fase 3 — Corrigir roteamento e replay exato (B4 e B5)

#### Implementação do falante forçado

- Validar `force_speaker` logo após carregar a sessão, antes de chamar o Narrador.
- Passar o override válido ao Narrador como uma restrição de roteamento interna, sem mencionar
  jogador ou interface.
- Quando um personagem for forçado, restringir `next_speaker` a esse ID e exigir que
  `context_for_character` seja filtrado especificamente para ele.
- Quando `Narrator` for forçado, exigir contexto vazio e não chamar Character.
- Overrides inválidos continuam equivalentes a `Auto`.

#### Implementação do log de turno

- Adicionar um marcador append-only `turn_input` antes da primeira chamada LLM do turno, contendo
  `turn_number`, `speech`, `action`, valor solicitado de `force_speaker` e valor efetivo validado.
- Manter esse marcador fora dos prompts e do estado ficcional; ele existe somente no debug log.
- Fazer o driver de replay preferir `turn_input` para reconstrução exata, mantendo a inferência
  atual como fallback de logs legados.
- Garantir que loaders de fita ignorem o marcador como resposta LLM.

#### Verificação

- Simular Narrador escolhendo C1 enquanto C2 é forçado e provar que o contexto recebido por C2 foi
  criado para C2.
- Cobrir override para personagem controlado, NPC, `Narrator`, inválido e ausente.
- Cobrir ordem do log, falha da primeira chamada e repetição de tentativa sem consumir marcadores
  como outputs de replay.
- Reconstruir uma pequena sessão usando apenas o novo log, sem backup auxiliar nem heurística de
  `HISTORY`.

#### Critério de aceite

Nenhum Character recebe contexto destinado a outro ID, e o log sozinho contém dados suficientes
para repetir exatamente cada chamada de turno e seu override.

### Fase 4 — Melhorar observabilidade e investigar os retries finais (B3)

#### Implementação

- Preservar o campo textual `error` para compatibilidade, mas usar `str(e) or repr(e)` para nunca
  gravar uma mensagem vazia.
- Acrescentar campos estruturados: tipo da exceção, `repr`, duração da tentativa, número da
  tentativa e tamanho aproximado do prompt.
- Registrar os mesmos campos de duração/tamanho nas chamadas bem-sucedidas para permitir
  comparação.
- Adicionar uma opção de timeout na configuração somente para torná-lo explícito e ajustável;
  manter o comportamento padrão atual até existir medição que justifique outro valor.

#### Verificação

- Forçar `httpx.ReadTimeout` com representação textual vazia e verificar que tipo e `repr` ficam
  disponíveis no JSONL.
- Cobrir HTTP status error, JSON inválido seguido de retry e sucesso na segunda tentativa.
- Confirmar que os novos campos não quebram UI, MCP, loader de replay nem logs antigos.

#### Decisão baseada em evidência

Depois da instrumentação, repetir o roteiro de 20 turnos em armazenamento temporário:

- se `ReadTimeout` for confirmado, registrar latência e tamanho do prompt e ajustar apenas a
  configuração de timeout necessária para o ambiente testado;
- se a falha for de schema/JSON ou transporte, corrigir a causa observada e adicionar regressão;
- se não houver reprodução, não inventar uma correção de performance; classificar como
  `NÃO REPRODUZIDO` e conservar a nova telemetria.

Compactação automática continua fora de escopo porque o relatório não provou que ela é a solução.

### Fase 5 — Reduzir fragilidades dos agentes

Esses itens terão correções de prompt/validação e avaliação comparativa. Eles só serão marcados
como `MITIGADOS` sem uma taxa de falha mensurável igual a zero em amostra suficiente.

#### Narrador

- Exigir consequência concreta para a última ação antes de acrescentar ambientação ou abrir outro
  fio narrativo.
- Proibir afirmar pensamentos, intenções ou emoções internas como fato; usar apenas sinais
  observáveis, percepção explicitamente fornecida ou fala/pensamento já presente no histórico.
- Tratar humor como estado persistente: emitir `mood_updates` apenas após mudança emocional
  significativa, não para sinônimos de pose ou disposição momentânea.
- Tornar explícita a diferença entre fato canônico, alegação de personagem e tentativa de ação.

#### Character

- Reforçar que conhecimento, notas e contexto são as únicas fontes de fatos; informação ausente
  deve ser omitida ou apresentada como dúvida, nunca como passado inventado.
- Pedir revisão breve antes da resposta e proibir repetição literal de uma frase recente do próprio
  personagem.

#### Historian

- Incluir `content_type` junto de cada evento entregue à compactação.
- Tratar diálogo como alegação atribuída e ação do personagem como tentativa até confirmação do
  Narrador; preservar incerteza no resumo em vez de promovê-la a cânone.
- Preservar explicitamente fios abertos, identidades desconhecidas e fatos não confirmados.

#### Linguagem e pontuação

- Remover os próprios caracteres U+2014/U+2013 das instruções e separadores dos prompts, usando
  nomes/códigos ou separadores ASCII.
- Manter o log bruto com a resposta real do modelo, mas normalizar esses dois caracteres na saída
  persistida/mostrada para garantir a regra já declarada pelo produto.
- Não criar o agente de correção gramatical opcional. Outros erros de linguagem serão medidos no
  playtest e reportados como risco residual se persistirem.

#### Verificação

- Testes de prompt comprovam a presença das regras e a marcação de proveniência dos eventos.
- Testes determinísticos comprovam a normalização de pontuação sem alterar o log bruto.
- Uma avaliação do mesmo roteiro conta: atualizações de humor, repetição literal, afirmações de
  mente, fatos não sustentados, ações sem consequência e defeitos de linguagem.

### Fase 6 — Fechar as lacunas de cobertura do playtest original

- Executar ao menos um turno após a compactação e verificar uso de `story_summary` e da nota
  canônica do Character.
- Exercitar deliberadamente um override diferente da escolha livre do Narrador.
- Exercitar `undo`, `restore_compaction` e `suggest` em armazenamento temporário.
- Confirmar que nenhum prompt contém o marcador interno `Player`.
- Confirmar contagens da janela de compactação e que backups/restauração continuam íntegros.
- Se o LLM real estiver indisponível, executar equivalentes determinísticos/replay e separar essa
  evidência da validação ao vivo no relatório final.

### Fase 7 — Validação técnica final

Executar, nessa ordem:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy .
uvx pytest
```

Depois:

- executar os testes `llm` somente se o endpoint local estiver saudável;
- repetir o playtest isolado descrito acima;
- comparar hashes/inventário de `.data/` antes e depois;
- revisar o diff por escopo, compatibilidade, locks, atomicidade e caminhos de erro;
- conferir cada ID B1-B6 e cada comportamento qualitativo contra evidência concreta.

### Relatório final obrigatório

Criar `01-real-playtest-remediation-2026-07-11.md` com:

1. resumo executivo;
2. hash/commit-base analisado e escopo do diff;
3. matriz de todos os achados de `01-real-playtest-remediation-2026-07-11.md`, com status, arquivos alterados, testes e evidência;
4. resultados completos de Ruff, format check, mypy e pytest;
5. resultado do playtest real ou motivo verificável do bloqueio;
6. comparação quantitativa do playtest original versus o novo;
7. prova de que `.data/` real não foi alterado;
8. riscos residuais, itens mitigados e itens que exigem decisão humana;
9. lista explícita de qualquer etapa deste plano que não tenha sido concluída.

O relatório não deve chamar mudanças de prompt de “resolução” sem avaliação e não deve esconder
falhas, skips ou validações indisponíveis.

### Definição de concluído

O trabalho estará concluído quando:

- B1-B5 tiverem regressões automatizadas e comportamento corrigido;
- B6 tiver sido revalidado sem qualquer modificação dos dados reais;
- todas as fragilidades qualitativas tiverem evidência de mitigação ou risco residual declarado;
- a suíte determinística estiver verde;
- o playtest real estiver concluído ou formalmente marcado como bloqueado por indisponibilidade do
  endpoint, sem impedir as demais entregas;
- `01-real-playtest-remediation-2026-07-11.md` permitir auditoria achado por achado.


## Part III — Verified closure of the six objective defects

> **Merge note.** This part was originally a separate file. References to
> `01-real-playtest-remediation-2026-07-11.md` inside it mean the ORIGINAL findings
> report (now Part I) when cited as source, and the final remediation report (now
> Part III) when cited as planned output - the merge renamed all three to this
> article's filename.


**Data:** 2026-07-12

**Fonte exclusiva:** [`01-real-playtest-remediation-2026-07-11.md`](./01-real-playtest-remediation-2026-07-11.md)

**Resultado:** os seis bugs objetivos foram corrigidos e verificados; os problemas qualitativos
foram mitigados, mas continuam dependentes do modelo.

> **Nota de contrato (2026-07-14):** os resultados abaixo continuam sendo evidência histórica do
> runtime de 2026-07-12. Compactação hoje usa progresso SSE medido, gatilho automático opt-in e
> checkpoints incrementais LIFO que preservam turnos posteriores. Consulte
> [Context Compaction](../../README.md#-context-compaction).

### Resultado por achado

| ID | Achado original | Estado | Evidência |
|---|---|---|---|
| B1 | `location` gravada em `physical_facts` | **RESOLVIDO** | `Runner._update_scene` trata `location` e `time_of_day` como campos reservados, limpa fatos da localização anterior e preserva undo. Testes cobrem troca, permanência, remoção e restauração. No playtest final, abrir a porta mudou o local para `Outside Old Mork's Tavern, alleyway`. |
| B2 | notas de compactação com IDs inutilizáveis | **RESOLVIDO** | O schema aceita apenas IDs da sessão, a resposta é filtrada por IDs canônicos e o prompt separa ID/nome. O playtest produziu notas `C1` e `C2`; a nota de Lyra apareceu no prompt do turno pós-compactação. |
| B3 | erros LLM registrados como string vazia | **RESOLVIDO** | O JSONL agora registra `str(e) or repr(e)`, `error_type`, `error_repr`, duração, tentativa e tamanho do prompt. Erros de JSON estruturado também são registrados e excluídos da fita. O timeout é configurável, com padrão de 60 s. |
| B4 | `force_speaker` podia reutilizar contexto de outro personagem | **RESOLVIDO** | O override é validado antes do Narrador e restringe schema/prompt ao ID efetivo; `Narrator` força contexto vazio. Testes e playtest cobriram `C2`, `Narrator`, inválido e automático. |
| B5 | log sem payload/override, impedindo replay exato | **RESOLVIDO (formato atual)** | Cada turno grava `turn_input` antes da primeira chamada, com fala, pensamento (thought), ação, override solicitado e efetivo. O replay exige esses marcadores e não tenta inferir logs antigos. Essa decisão segue a orientação de não criar uma camada de compatibilidade legada. |
| B6 | testes alteravam `.data` real | **RESOLVIDO** | `tests/conftest.py` define um `ROLEPLAY_DATA_DIR` temporário antes dos imports e recusa o diretório real ou descendentes. O hash e a contagem de `.data` permaneceram idênticos durante a validação final. |

### Mitigações qualitativas

- O Narrador recebeu regras para resolver primeiro a consequência imediata, evitar leitura de
  mente, preservar incerteza, estabilizar humores e reutilizar chaves físicas.
- Character limita fontes de fatos, proíbe repetição integral de frases recentes e pede revisão
  gramatical curta.
- Historian recebe `TYPE`, diferencia alegação/tentativa de fato confirmado e usa schema fechado.
- Respostas geradas normalizam U+2014/U+2013 somente depois do log bruto. No playtest final, houve
  1 travessão na resposta bruta e 0 no conteúdo persistido.

Esses itens são **MITIGADOS**, não declarados como eliminados: invenção, repetição, gramática,
mudança de humor e qualidade narrativa continuam probabilísticos. O playtest curto não substitui
uma avaliação estatística nem repete os 20 turnos originais.

### Validação executada

- `uvx ruff check .`: passou.
- `uvx ruff format --check .`: passou, 26 arquivos já formatados.
- `uvx mypy src/`: passou, 14 módulos sem erros.
- `uv run pytest -x`: **116 passed, 5 deselected**.
- `uv run pytest -m llm -x`: **5 passed, 116 deselected**, usando Gemma 4 local.
- `node --check src/static/app.js` e `src/static/api.js`: passaram.
- Playtest real isolado em `/tmp/roleplay-report-live-ayqs4vpq`: 5 turnos, 10 tentativas LLM,
  0 erros, 3 sugestões, compactação, turno pós-compactação, undo, recusa segura de restore com
  turno novo e restore bem-sucedido após undo.
- Nenhum prompt do playtest continha `SPEAKER=Player`.
- `.data`: 38 arquivos e hash agregado
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f` antes e depois.

Os sete timeouts/retries dos turnos 14–20 do relatório original não reapareceram nos cinco testes
LLM nem no playtest final. Portanto, a observabilidade foi corrigida, mas não há evidência para
alterar o timeout padrão ou introduzir compactação automática.

### Correções adicionais encontradas ao retomar

Após atualizar para o novo `HEAD`, a revisão encontrou três regressões fora dos achados originais,
mas impeditivas para a saúde do projeto:

- sintaxe de múltiplas exceções incompatível com MyPy em `src/store/presets.py` e
  `src/store/sessions.py`;
- importação local desordenada, comentário longo e ausência de tipo no endpoint de bootstrap em
  `src/main.py`.

Elas foram corrigidas e estão incluídas nas validações acima.

### Fora de escopo e riscos residuais

- `01-real-playtest-remediation-2026-07-11.md` permaneceu inalterado como evidência original.
- O trabalho Android/Docker não foi alterado. Há uma incompatibilidade potencial a acompanhar no
  APK: o Gradle fixa Python 3.11, FastAPI 0.99 e Pydantic 1, enquanto o projeto declara Python
  3.14+ e FastAPI 0.115+.
- O diretório de playtest em `/tmp` foi preservado para inspeção.
- Nenhum commit, push ou outra mutação Git foi executada por esta remediação.


## Part IV — Post-remediation live exploration (20 turns, compaction, restore, undo)

**Data:** 2026-07-12
**Escopo:** 20 turnos do roteiro Thorn/Lyra, sugestão, duas compactações com restore entre elas,
turno pós-compactação e undo
**Modelo:** Gemma 4 26B A4B QAT, servido pelo llama.cpp local
**Armazenamento isolado:** `/tmp/roleplay-report-playtest.DmyEbG`
**Sessão:** `89c21c6c`

> **Nota de contrato (2026-07-14):** este playtest registra o backup/restore existente na data da
> execução. O runtime atual substituiu esse formato por checkpoints incrementais LIFO, mantém os
> checkpoints até a exclusão da sessão e preserva turnos posteriores durante o undo. Consulte
> [Context Compaction](../../README.md#-context-compaction).

### Artefatos

- Resultado estruturado: `/tmp/roleplay-report-playtest.DmyEbG/playtest-results.json`
- Estado final: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.json`
- Backup pré-compactação: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.kb_0.json`
- Log bruto: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.debug.jsonl`
- Roteiro: script manual privado de playtest do projeto

### Resumo da execução

| Métrica | Resultado |
|---|---:|
| Turnos principais | 20 |
| Turnos pós-compactação | 1 |
| Registros LLM | 40 |
| Sucessos | 40 |
| Erros/retries | 0 |
| Chamadas Narrator | 21 |
| Chamadas Character/Lyra | 16 |
| Chamadas Historian | 2 |
| Chamadas Suggest | 1 |
| Maior prompt | 32.550 caracteres |
| Maior duração de chamada | 10.582 ms |
| Registros antes da compactação | 75 |
| Registros removidos/mantidos | 45 / 30 |
| Marcadores `turn_input` | 21 |

O prompt do Narrador cresceu de 4.066 caracteres no turno 1 para 32.550 no turno 20. Mesmo assim,
todas as chamadas terminaram na primeira tentativa. A maior duração, 10,6 segundos, ficou muito
abaixo tanto do timeout usado no playtest (90 s) quanto do padrão do produto (60 s). Os retries
observados do turno 14 em diante no playtest original não reapareceram.

### Bugs objetivos

#### 1. `physical_facts` pode virar uma chave contendo JSON serializado

**Severidade observada:** alta para integridade do estado.

No turno 20, o Narrador retornou:

```json
{
  "location": "Watchtower Base",
  "physical_facts": "{\"atmosphere\": \"stifling, vibrating, and freezing\", \"dust\": \"falling ash-like particles\", \"scent\": \"cloying, rotting lilies\"}"
}
```

O estado persistiu literalmente:

```json
{
  "atmosphere": "stifling, vibrating, and freezing",
  "physical_facts": "{\"atmosphere\": ...}"
}
```

Assim, `dust` e `scent` não viraram fatos consultáveis no turno 20; o contêiner apareceu dentro de
si mesmo como string. No turno 21, o modelo voltou a emitir as duas chaves de forma plana, mas a
chave serializada incorreta permaneceu ao lado delas.

A forma é aceita porque `scene_update.additionalProperties` permite qualquer chave com valor
string/null (`src/agents/narrator.py:79-86`). O runner copia toda chave que não seja `location` ou
`time_of_day` diretamente para `game.scene.physical_facts` (`src/runner.py:514-520`).

#### 2. Normalização de travessão provoca uma falsa troca de localização

**Severidade observada:** média; houve mutação real, sem perda neste caso.

O preset começou em `Old Mork's Tavern — main hall, dim lighting`. No turno 1, o output bruto
repetiu exatamente esse local. Antes de aplicar o estado, a normalização converteu o travessão em
vírgula (`src/agents/narrator.py:298-303` e `src/llm/client.py:32-34`).

O runner comparou a string normalizada com a string original, interpretou a diferença de
pontuação como mudança de local e executou `physical_facts.clear()`
(`src/runner.py:503-508`). Nenhum fato se perdeu porque o modelo também repetiu iluminação,
público, clima e porta naquele output. O estado, entretanto, mudou o nome do local e percorreu o
caminho de transição de cena sem que a cena tivesse mudado semanticamente.

#### 3. Character executa/descreve ações físicas em todas as respostas observadas

**Severidade observada:** alta em relação ao modelo de papéis documentado.

O `AGENTS.md` define que Character pode somente falar e pensar, nunca executar ou descrever ação
física própria ou alheia. Nos 20 turnos houve 15 respostas de Lyra, e todas incluíram ação ou
descrição física própria. A resposta pós-compactação repetiu o padrão.

Exemplos:

- turno 2: `I say, leaning closer to the pulsing metal`;
- turno 8: `I mutter, frantically stuffing my scrolls into my satchel`;
- turno 14: `my fingers trembling slightly as I pull a minor illumination stone from my belt`;
- turno 19: `I stammer, my eyes wide as I stare at the vibrating wall`.

O próprio docstring do formatter confirma que só diálogo deve chegar ao Character porque apenas
o Narrador narra/descreve/age (`src/agents/character.py:47-52`). O prompt proíbe narrar ações como
fato, mas também pede apenas primeira pessoa e diálogo (`src/agents/character.py:20-36`). O output
de texto livre não aplica validação posterior para separar fala, pensamento e ação.

#### 4. A localização mudou sem transição narrativa no turno 17

**Severidade observada:** média.

No turno 16, o estado estava em `Watchtower Interior`. No turno 17, Thorn declarou o plano para o
amanhecer, guardou o dispatch e procurou suprimentos no cômodo. A narração já passou a chamar o
ambiente de `tower base`, e `scene_update.location` mudou para `Watchtower Base`, sem saída,
descida ou outra transição espacial descrita.

A alteração também limpou `light_level`, pois toda troca de localização descarta os fatos da cena
anterior. O novo estado reteve apenas `atmosphere`.

### Fragilidades qualitativas reproduzidas

#### Ponto de vista em segunda pessoa troca implicitamente para Lyra

Nove das 21 narrações contêm `you`/`your` enquanto Thorn é descrito em terceira pessoa. Em vários
casos, a segunda pessoa só pode ser Lyra:

- turno 18: `The illumination stone in your hand ... as your hands shake`, enquanto Thorn está
  com o ouvido contra a parede e a pedra pertence a Lyra;
- turno 19: `your pale blue light`;
- turno 20: `your illumination stone`;
- turno 21: `your fingers ... around the staff`.

Não houve vazamento da palavra `Player`, mas a narração exibida ao humano que controla Thorn muda
o foco para o corpo e os objetos de Lyra sem marcar a troca de ponto de vista.

#### Consequências imediatas continuam podendo ser adiadas

- turno 6: Thorn ordena que Mork barre a porta. Mork pausa com o pano na mão, mas não barra a
  porta; `door` continua `closed` apenas por já estar assim no preset;
- turno 19: Thorn conta regressivamente e ordena que Lyra quebre o ward. A narração troca o som de
  arranhado por batidas e Lyra diz que está pronta, mas o ward não é quebrado;
- turno 20 muda para o mapa sem resolver o ward ou o que existe atrás da parede.

A regra de resolver a consequência antes de ampliar a atmosfera existe no prompt do Narrador,
mas os dois padrões do relatório original reapareceram.

#### Character ainda inventa origem ausente

No turno 5, Lyra responde `We found it tucked away in a ruin`. Seu conhecimento contém apenas que
o medalhão foi encontrado e emite uma aura fraca; roteiro, estado e contexto do turno não fornecem
uma ruína. É o mesmo tipo de invenção observado no playtest original.

As duas compactações não promoveram a ruína para o resumo, sinal de que as regras de proveniência
do Historian funcionaram melhor do que no relatório original.

#### Narrator ainda afirma estados internos

Exemplos observados:

- turno 5: `desperate, piercing intensity`;
- turno 17: `grim, mechanical purpose` e `his focus remaining on the task`;
- turno 20: `Thorn ignores it, his focus entirely consumed by the paper`.

Esses trechos atribuem emoção, propósito ou foco interno, apesar da regra de descrever apenas
evidência observável.

#### Mood updates redundantes

O Narrador emitiu oito objetos de atualização de humor. Três não mudaram o valor persistido:

- turno 10: C2 `anxious` para `anxious`;
- turno 14: C2 `anxious` para `anxious`;
- turno 19: C2 `terrified` para `terrified`.

Houve cinco transições reais: C1 para `determined`, C2 para `anxious`, C1 para `devastated`, C1
de volta para `determined` e C2 para `terrified`. A frequência é muito menor que as 18
atualizações em 20 turnos do relatório original, mas a instrução de omitir personagens sem
mudança ainda não é obedecida de forma consistente.

### Comportamentos confirmados como corretos

- Nenhum prompt contém `Player` ou `SPEAKER=Player`.
- Todos os 21 overrides solicitados foram registrados e validados corretamente em `turn_input`.
- Todas as 40 chamadas possuem métricas e `attempt_number=1`; não houve erro vazio ou retry.
- As mudanças reais de local limparam fatos da cena anterior: taverna, corredor, beco, ruas e
  torre não vazaram portas/clima/iluminação entre si.
- As notas de compactação usaram somente `C1` e `C2`.
- O turno 21 recebeu `STORY SO FAR`, a nota canônica de Lyra e somente sua própria nota.
- Lyra conseguiu listar medalhão, dispatch e floresta após a compactação.
- A primeira compactação removeu 45 registros e manteve 30, correspondentes exatamente aos oito
  turnos 13-20 desta execução.
- Restore recuperou os 75 registros anteriores; uma nova compactação voltou a 30.
- Undo do turno 21 restaurou história, cena e humores do estado pós-compactação.
- Não houve frase completa repetida literalmente entre narrações nem entre respostas de Lyra.
- O log bruto contém um travessão (na localização do turno 1); o conteúdo gerado persistido foi
  normalizado sem travessão/en dash.
- O diretório real `.data` permaneceu com 38 arquivos e hash agregado
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f`.

### Observações sem classificação de bug

Compactar, restaurar e compactar novamente o mesmo estado produziu dois resumos semanticamente
próximos, mas não idênticos. As notas também mudaram de redação. O comportamento é compatível com
geração em temperatura 1.0, mas demonstra que compactação repetida não é semanticamente
idempotente mesmo quando o estado de entrada é idêntico.

Nenhum dos cinco turnos com roteamento automático escolheu C1, o personagem controlado. A trava
de agência desse ramo continua coberta por testes e playtests anteriores, mas não foi exercitada
ao vivo nesta execução específica.

### Open Questions

- A narração deve manter sempre terceira pessoa ou existe intenção de permitir segunda pessoa
  direcionada a um personagem que não é o controlado?
- `physical_facts` deve ser tratado como nome reservado de contêiner no schema/delta ou seu uso
  literal como fato é considerado válido?
- A variação entre duas compactações do mesmo estado é aceitável para o fluxo de restore/retry ou
  deve ser tratada apenas como característica observável do modelo?
