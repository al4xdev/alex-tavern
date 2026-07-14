# Relatório do playtest real: Thorn e Lyra

**Data:** 2026-07-11
**Sessão:** `7cb448da`
**Escopo:** 20 turnos reais, 1 compactação manual e inspeção do estado, backup e log bruto
sequencial.

> **Nota de contrato (2026-07-14):** este relatório preserva os caminhos e o comportamento
> observados no playtest de 2026-07-11. O runtime atual usa sessões em diretórios, compactação
> manual ou automática, progresso SSE medido e checkpoints incrementais LIFO que preservam turnos
> posteriores. Consulte [Context Compaction](../../README.md#-context-compaction).

## Artefatos auditados

- Estado após compactação: `.data/sessions/7cb448da.json`
- Backup completo pré-compactação: `.data/sessions/7cb448da.kb_0.json`
- Chamadas e respostas brutas: `.data/sessions/7cb448da.debug.jsonl`
- Fluxos relevantes: `src/runner.py`, `src/llm/client.py`, `src/agents/narrator.py`,
  `src/agents/character.py` e `src/agents/summarizer.py`

O roteiro usado foi o script manual privado de playtest do projeto. Alguns valores de
`force_speaker` foram escolhidos livremente durante o teste, portanto nem todo desvio do texto
esperado é atribuível aos agentes.

## Resumo

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

## Bugs claros

### 1. Mudanças de local são gravadas como fatos físicos, não como `Scene.location`

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

### 2. Notas da compactação usam identificadores incompatíveis com o runtime

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

### 3. Falhas do LLM são registradas como `error: ""`

**Severidade sugerida:** média

Houve 7 primeiras tentativas com erro, uma em cada turno do 14 ao 20. Todas foram seguidas por
uma tentativa bem-sucedida, mas as linhas de erro contêm apenas uma string vazia. A função
`_log_llm_call` recebe `str(e)`, o que perde toda informação quando a exceção tem representação
textual vazia.

Pelo comportamento e pelo timeout fixo de 60 segundos, `httpx.ReadTimeout` é uma hipótese forte,
mas o próprio log não preserva o tipo ou `repr` da exceção para confirmá-la. Isso enfraquece a
principal ferramenta de observabilidade justamente quando o contexto cresce.

### 4. Um personagem forçado pode receber contexto escrito para outro falante

**Severidade sugerida:** média

Em `Runner.player_turn`, o Narrador primeiro gera `next_speaker` e `context_for_character`.
Depois, `force_speaker` pode substituir somente o falante. Se o personagem forçado for diferente
do escolhido originalmente, `_call_character` recebe o mesmo `context_for_character`, ainda
escrito para o falante original.

Este playtest não apresentou uma chamada de Lyra que contradissesse a escolha original do
Narrador, portanto o efeito não apareceu no texto final. O caminho incorreto, contudo, é direto
e reproduzível pelo código.

### 5. O log não registra `force_speaker` nem o payload do turno

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

### 6. A suíte de testes usa e remove artefatos do diretório real de sessões

**Severidade sugerida:** alta para segurança dos dados de desenvolvimento

Após executar `uv run pytest -x`, os arquivos manuais `7cb448da.json` e
`7cb448da.kb_0.json` desapareceram de `.data/sessions`, enquanto o `debug.jsonl` original
permaneceu e vários arquivos de sessões criadas pelos testes ficaram no mesmo diretório. Isso
prova que ao menos parte da suíte compartilha o armazenamento real em vez de injetar um diretório
temporário isolado.

O efeito destruiu o estado e o backup usados nesta auditoria. A reprodução só pôde continuar
porque o HISTORY completo ainda existia nas requests do log bruto. A causa exata e a correção de
isolamento ficaram pendentes, mas nenhum teste deve ler, limpar ou gravar `.data/sessions` real.

## Comportamentos estranhos ou frágeis

### Crescimento de contexto coincide com retries em todos os turnos finais

O prompt do Narrador cresceu continuamente:

- turno 1: 1.416 caracteres;
- turno 13: 16.221 caracteres;
- turno 14: 17.427 caracteres, primeira falha;
- turno 20: 26.443 caracteres.

Do turno 14 em diante, cada primeira tentativa falhou e cada retry seguinte funcionou. Isso não
prova causalidade, mas cria uma correlação forte entre contexto crescente, latência e timeout.
A compactação só foi acionada depois do turno 20.

### O estado físico acumula chaves duplicadas e sem identidade

O estado final contém simultaneamente:

```text
weather_outside = heavy rain
weather = torrential rain
```

A chave genérica `door` também representou, em momentos diferentes, a porta da taverna, a saída
da cozinha e a porta da torre. Seus valores passaram por `closed`, `open`, `pushed open`, `ajar`
e finalmente remoção. Como fatos são um dicionário plano criado livremente pelo modelo, nomes
sinônimos se acumulam e objetos de locais diferentes colidem.

### Mudança excessiva de humor

O Narrador emitiu `mood_updates` em 18 dos 20 turnos. Thorn passou, entre outros estados, por
`cautious`, `alert`, `grim`, `vigilant`, `determined`, `cautious`, `determined`, `focused`,
`intense`, `alert`, `ready`, `heavy-hearted`, `vulnerable`, `determined`, `alert`, `determined`
e `resolute`.

Algumas mudanças são justificáveis, especialmente nos turnos 15–17, mas a frequência indica que
o campo está funcionando como uma descrição instantânea de pose em vez de estado emocional
durável. Isso contraria a instrução de atualizar somente quando o humor realmente mudou.

### Lyra inventou um fato e a compactação o tornou memória durável

No turno 5, Lyra afirmou que o medalhão foi encontrado “in the old ruins while we were trekking
to the edge of the corrupted forest”. O preset dizia apenas que o medalhão fora encontrado e que
a floresta ao norte estava corrompida; o contexto daquele turno também não fornecia as ruínas.

O Historian depois incorporou “medallion found in the old ruins near a corrupted forest” ao
`story_summary`. Isso mostra como uma invenção de Character pode virar cânone persistente na
compactação.

### Lyra repetiu uma frase inteira do próprio histórico

No turno 20, Lyra repetiu literalmente a primeira fala do turno 18:

```text
If you are trying to be brave is working, you should know that the noise is making it very hard
to focus on your stoic silence, Thorn.
```

A repetição preservou inclusive o erro gramatical. O Character recebe diálogos anteriores no
prompt, o que torna plausível uma cópia direta do histórico.

### O Narrador frequentemente descreve a mente do personagem controlado

Exemplos incluem “his mind calculating”, “the burden of a man leading a charge”, “the hollow ache
in his chest” e a afirmação de que a verdade poderia “break him or forge him”. A narração sensorial
funciona, mas às vezes deixa de mostrar sinais observáveis e define pensamentos, intenções e
emoções internas de Thorn. Isso reduz a separação entre Narrador e personagem controlado.

### Ações são recontadas, mas nem sempre produzem consequência

- turno 6: Thorn ordena que Mork barre a porta, mas Mork nunca age;
- turno 3: o encapuzado começa a se levantar, mas o fio narrativo fica sem resolução;
- turno 19: Thorn pede que Lyra quebre o ward, mas a resposta apenas aumenta a tensão;
- turno 20: o roteiro introduz o mapa e muda o foco antes de resolver claramente o que havia
  atrás da parede.

O roteiro também contribui para os dois últimos saltos, portanto eles não são bugs isolados do
modelo. Ainda assim, o Narrador tende a expandir sensorialmente o input em vez de fechar sua
consequência antes de avançar.

### Defeitos recorrentes de linguagem

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

### O resumo preservou fatos, mas também simplificou incertezas

O `story_summary` reteve o medalhão, a Iron Guard, o irmão de Thorn, o símbolo no dreno, a trilha
mágica e a jornada ao norte. Porém:

- consolidou como fato a origem inventada nas ruínas;
- chamou o irmão de Thorn de falecido, inferência provável mas não declarada literalmente no
  preset;
- resumiu o encapuzado como um encontro tenso, sem preservar claramente que sua identidade e
  intenção continuam abertas.

## Comportamentos confirmados como corretos

- Nenhum dos 43 eventos do log contém `Player` nos prompts enviados ao LLM.
- O Narrador produziu uma resposta JSON válida para todos os 20 turnos após retries.
- Lyra foi chamada 14 vezes e, em todas elas, o `next_speaker` original também era `C2`.
- Quando o Narrador escolheu o personagem controlado (`C1`), o runner não gerou sua fala.
- O backup pré-compactação contém 74 registros distribuídos pelos turnos 1–20.
- A compactação removeu 45 registros dos turnos 1–12 e reteve 29 registros dos turnos 13–20,
  exatamente a janela configurada de 8 turnos.
- O resumo mundial foi salvo e o `compact` marker foi anexado ao log.
- Não houve retry ou erro do Historian durante a compactação.

## Cobertura que permaneceu ausente

- Não houve turno posterior à compactação; portanto, este playtest não confirmou ao vivo se o
  Narrador usa corretamente `story_summary` nem demonstrou que as notas inválidas deixam de
  chegar aos Characters.
- Não houve marker de undo, restore de compactação ou suggest nesta sessão.
- Como a escolha de `force_speaker` não é persistida, não é possível auditar completamente quais
  seleções foram manuais usando somente os artefatos da sessão.
