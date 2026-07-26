# Task 57 — Eliminar vazamento da ontologia de jogador nos prompts LLM

> ✅ **FECHADA em 2026-07-26** (branch `refactor/pre-1.0-cleanup`). Os quatro
> vazamentos do core saíram, o Director foi revalidado por replay real e uma
> sessão ao vivo com 24 chamadas cobriu as seis famílias exigidas com **zero**
> ocorrências. Evidência completa em "Resultado" no fim do arquivo.
>
> Duas coisas ficaram **abertas de propósito** e viraram achado novo: a
> `ROUTING CONSTRAINT` do Director e o contrato de cenários do usuário. Ambas
> descritas no fim.

## Invariante violado

O contrato do kernel é mais forte que “o modelo sabe quem é o jogador, mas não
fala disso na ficção”:

- `Player.controlled_character_id` é conhecimento exclusivo do Runner;
- nenhum agente, nem mesmo Director, Prose, Character, Perspective, Historian ou
  Architect, recebe a existência de jogador, usuário ou operador externo;
- `speaker="Player"` é apenas um marcador persistido e precisa ser traduzido para
  o personagem controlado antes de qualquer prompt;
- a trava de agência ocorre deterministicamente no Runner, não por instrução ao
  modelo.

Esse contrato está documentado em `AGENTS.md` §3, `README.md:334-352` e
`src/models.py:437-447`.

## Vazamentos confirmados

### 1. Initializer de perspectiva identifica o personagem controlado

Em `src/agents/perspective.py:98-109`, `_roster_lines` acrescenta:

```text
(controlled by the player)
```

ao personagem cujo ID coincide com `controlled_id`. O texto entra no request de
`perspective:init:<viewer_id>` por `initialize_perspective` e informa à LLM:

1. que existe um jogador externo;
2. exatamente qual personagem ele controla.

O parâmetro `controlled_id` é legítimo em outras operações de perspectiva para
traduzir registros internos `speaker="Player"` na identidade percebida. Ele não
é necessário para enriquecer o roster de inicialização com um papel externo.

Risco downstream confirmado por inspeção:

- o modelo controla o campo persistido `reference`;
- `_validated_people` bloqueia nomes canônicos indevidos, mas não bloqueia
  referências como “the player-controlled character”;
- `viewer_speaker_label` e `project_text_for_viewer` reutilizam `reference` no
  contexto entregue ao Character.

Não foi observado texto literal de jogador nas respostas atuais: 32 chamadas
reais de `perspective:init:*`, distribuídas por 10 sessões, receberam o marcador,
mas nenhuma das 32 respostas contém `player`, `jogador`, `usuário`, `operador` ou
`controlled`. Isso reduz a evidência de materialização passada, mas não elimina
o vazamento no request nem prova ausência de influência semântica.

### 2. O próprio prompt do Director usa “player”

Em `src/agents/narrator.py:160-166`, a regra de roteamento diz:

```text
The player's own speech or action ...
Leaving next_speakers empty there is the world ignoring the player ...
```

Isso contradiz a docstring de `narrate` (`src/agents/narrator.py:558-561`) e o
README, que afirmam que o Director não sabe que um humano existe e nunca vê a
palavra “player”.

O comportamento protegido pela regra é válido: uma fala ou ação audível do
personagem da última entrada deve contar como evento percebido e não pode ser
ignorada pelo mundo. O defeito é expressar essa regra em termos do operador. A
variante corrigida precisa preservar a taxa de resposta medida pelo commit que
introduziu a regra.

### 3. Cenário built-in injeta “agência humana”

`src/scenarios/turma-dos-portais-pt.json:426` inclui nas
`narrator_directives`:

```text
permita que a seleção aconteça em cena e reaja à agência humana
```

As diretivas são propagadas para múltiplas famílias de chamada:

- Director (`src/agents/narrator.py::_build_system_prompt`);
- sugestões manuais (`_build_suggest_system_prompt`);
- sugestões de abertura (`build_opening_suggestions_messages`);
- Historian (`src/agents/summarizer.py::_build_system_prompt`);
- Architect/roteiro, limitado aos primeiros 600 caracteres
  (`src/roteiro.py::_story_context_lines`).

O cenário já possui uma formulação diegética e suficiente logo antes — não
decidir antecipadamente as escolhas de Link. A menção ao operador acrescenta
ontologia externa, não uma regra narrativa indispensável.

Também deve ser definido o contrato para `narrator_directives` de cenários do
usuário e de plugins. Uma busca ingênua pela palavra `human` não serve: “humano”
pode ser espécie ou fato legítimo do mundo, e “player” pode ter sentido
diegético. A task não deve introduzir sanitização textual silenciosa nem regex
que muta conteúdo narrativo.

### 4. Architect/roteiro recebe a identidade protegida por sinônimo

Em `src/roteiro.py:366-374`, o roster enviado a `roteiro:compile` e
`roteiro:replan` marca somente o personagem controlado como:

```text
(PROTAGONIST — never an expected actor)
```

As regras do sistema reiteram que escolhas do protagonista são “sagradas” e que
ele nunca deve entrar em `expected_actors` (`src/roteiro.py:386-403`). Mesmo sem
usar “player”, isso revela qual personagem possui proteção especial de agência.

Essa identificação no prompt é redundante para a trava real:
`_validate_beat` já remove deterministicamente o personagem controlado de
`expected_actors` em `src/roteiro.py:310-323`. O Architect pode planejar
situações e pressões sem conhecer a identidade controlada; o Runner continua
dono da filtragem.

Os logs atuais contêm 18 chamadas com o marcador explícito:

- 10 `roteiro:compile`;
- 8 `roteiro:replan`.

### 5. Cobertura existente dá falso negativo

`tests/test_integration.py:1790` verifica somente:

```python
assert "Player" not in prompt
```

Por ser case-sensitive, o teste aceita os dois usos de `player` minúsculo do
Director. O comentário adjacente, adicionado junto da regressão, também descreve
o operador em vez do personagem/ator da última entrada.

`tools/playtest_harness.py:750` possui a mesma lacuna:

```python
prompts.count("Player")
```

Não há teste direto do request produzido por `_roster_lines` /
`initialize_perspective`, nem teste que detecte a marcação semântica do
personagem controlado no roteiro.

## Evidência agregada dos logs locais

Busca case-insensitive nos `request.messages` de
`.data/sessions/*/debug.jsonl`, cobrindo as frases confirmadas e o marcador de
protagonista:

- **110 chamadas afetadas**;
- **10 sessões**;
- 50 `director`;
- 32 `perspective:init:*`;
- 10 `roteiro:compile`;
- 8 `roteiro:replan`;
- 7 `narrator_suggest`;
- 3 `opening_suggest`.

As categorias podem receber o vazamento por produtores diferentes: por exemplo,
as sugestões recebem “agência humana” pelas diretivas do cenário, enquanto o
Director recebe tanto suas regras próprias quanto as diretivas.

Essa contagem demonstra exposição no request. Ela não mede, por si só, mudança
de comportamento. Qualquer afirmação sobre efeito narrativo deve seguir o
método curl-first.

## Cronologia por commit

Idades calculadas em **2026-07-26 12:17 -03:00**.

| Data de introdução | Idade | Commit | Evento |
|---|---:|---|---|
| 2026-07-11 14:11 | 14d 22h | `9a56500` | adicionou o teste case-sensitive `assert "Player" not in prompt` |
| 2026-07-11 16:58 | 14d 19h | `4bbca41` | documentou no README que nenhum agente conhece o humano e que o Director nunca vê “player” |
| 2026-07-12 18:29 | 13d 17h | `8850d2e` | adicionou `player_prompt_occurrences = prompts.count("Player")` ao harness |
| **2026-07-16 04:07** | **10d 8h** | **`93a5d69`** | introduziu `(controlled by the player)` no novo perspective ledger — primeiro vazamento confirmado |
| 2026-07-17 10:35 | 9d 1h | `2565993` | marcou o controlado como `PROTAGONIST — never an expected actor` no roteiro |
| 2026-07-17 10:47 | 9d 1h | `c7f3d36` | adicionou “agência humana” ao cenário `turma-dos-portais-pt` |
| 2026-07-21 14:55 | 4d 21h | `f233506` | adicionou “The player's own...” e “ignoring the player” ao Director |

Portanto, a violação literal mais antiga conhecida está presente há pouco mais
de **10 dias**. A garantia e seus testes já existiam quando ela entrou, mas
testavam apenas o sentinel com capitalização exata e não o contrato semântico.

## Resultado esperado

Restaurar a fronteira:

```text
estado completo + controlled_character_id
                    │
                    ▼
                  Runner
     traduz sentinel, filtra routing/actors,
     interrompe geração no personagem controlado
                    │
                    ▼
       prompts recebem somente personagens,
       eventos e regras diegéticas do mundo
```

Nenhum agente deve conseguir inferir de um rótulo fornecido pelo sistema qual
personagem é controlado ou que existe um operador externo. Isso não impede que
cenários tenham protagonistas narrativos; impede que o core equipare esse papel
à identidade protegida pelo Runner.

## Requisitos da correção

- Remover do roster de perspectiva o papel `(controlled by the player)` e
  eliminar parâmetros que fiquem realmente sem uso nesse builder.
- Reformular a regra de resposta audível do Director em termos da entrada final,
  do ator da ação e de testemunhas, sem `player`, humano, usuário ou operador.
- Preservar o comportamento que motivou `f233506`: fala/ação audível não pode
  voltar a produzir fila vazia quando alguém naturalmente pode responder.
- Tornar diegética a diretiva built-in de `turma-dos-portais-pt`, sem enfraquecer
  a proibição de decidir escolhas de Link.
- Remover do prompt de roteiro a associação entre o ID controlado e o papel
  especial de protagonista. A filtragem de `expected_actors` continua
  determinística em `_validate_beat`.
- Auditar os builders finais de todas as famílias LLM, diferenciando comentários
  e docstrings de texto realmente emitido.
- Não resolver com filtro regex silencioso, substituição global ou camada de
  compatibilidade. Produtores core e conteúdo built-in devem emitir o contrato
  correto.
- Manter `controlled_character_id` interno onde ele é necessário para traduzir
  `speaker="Player"` e aplicar travas determinísticas.
- Não alterar schema de sessão: esta correção muda prompts e testes, não estado
  persistido.

## Validação obrigatória

### Testes estruturais

- Testar os `messages` finais, não apenas helpers parciais.
- Cobrir case-insensitive as frases externas controladas pelo core:
  `player`, `jogador`, `usuário`, `operador`, `human-controlled`,
  `controlled by`.
- Ter teste específico de `perspective:init` demonstrando que alternar
  `controlled_id` não marca nem textual nem estruturalmente uma pessoa no
  roster.
- Ter teste de roteiro demonstrando que o prompt não distingue o personagem
  controlado, enquanto `_validate_beat` ainda o remove de `expected_actors`.
- Corrigir a métrica do playtest harness para não produzir falso zero por
  capitalização e incluir marcadores semânticos mantidos pelo core.
- Cobrir Director, Perspective, Historian, opening suggestions, manual
  suggestions e roteiro com cenário built-in.
- Evitar falso positivo para usos diegéticos legítimos de “humano” ou
  “protagonista”; os fixtures devem procurar ontologia operacional, não palavras
  isoladas sem contexto.

### Boundary real e curl-first

Antes de escolher a formulação substituta do Director:

1. extrair um payload real em que uma fala/ação audível recebeu resposta;
2. pré-registrar a regra de decisão;
3. comparar 3–4 runs do prompt atual e da variante cega, mudando somente essa
   regra;
4. medir fila vazia versus resposta válida e inspecionar `next_speakers`;
5. shippar exatamente a variante validada, na mesma posição do builder.

Depois, executar ao menos uma sessão real que produza:

- `perspective:init:*`;
- `director`;
- `roteiro:compile` ou `roteiro:replan`;
- `narrator_suggest`;
- `opening_suggest`;
- `summarizer`, forçando compactação.

Inspecionar os requests completos no `debug.jsonl`. O alvo é zero exposição
core/built-in da ontologia operacional e preservação das travas de agência em
código.

## Critério de fechamento

- [ ] Nenhum prompt produzido pelo core ou cenário built-in identifica jogador,
      humano operador ou personagem controlado.
- [ ] O sentinel `Player` continua sempre traduzido antes de chamadas LLM.
- [ ] Perspective e roteiro não recebem marcação especial do ID controlado.
- [ ] O Director continua respondendo corretamente a fala/ação audível segundo
      replay real de 3–4 runs.
- [ ] Testes deixam de depender de capitalização exata.
- [ ] Harness reporta ontologia operacional por uma regra explícita e testada.
- [ ] Boundary real cobre todas as famílias listadas, inclusive Historian.
- [ ] Requests, respostas brutas e contagens ficam registrados nesta task.
- [ ] README permanece verdadeiro sem precisar enfraquecer a garantia.



---

# Resultado (2026-07-26)

## O que mudou

| # | Vazamento | Correção |
|---|---|---|
| 1 | `(controlled by the player)` em `perspective._roster_lines` | Marcador removido; o parâmetro `controlled_id` ficou sem uso e saiu de `_roster_lines` **e** de `initialize_perspective` (`runner.py:2081` acompanhou) |
| 2 | "The player's own..." / "ignoring the player" na regra 5 do Director | Reescrita em termos da última entrada de HISTORY e do zone daquele falante — **validada por replay**, ver abaixo |
| 3 | "reaja à agência humana" em `turma-dos-portais-pt.json` | Virou "reaja ao que ele fizer ali"; o resto da diretiva (não decidir escolhas de Link) ficou intacto |
| 4 | `(PROTAGONIST — never an expected actor)` no roteiro | Marcador removido do roster, e `_ARCHITECT_RULES` deixou de citar "protagonist" nas 3 posições. `_validate_beat` continua removendo o controlado de `expected_actors` deterministicamente |
| 5 | `assert "Player" not in prompt` e `prompts.count("Player")` | Substituídos pela regra compartilhada `src/prompt_contract.py` |

## A regra, agora explícita e testada

`src/prompt_contract.py` define `operator_ontology_hits` / `leaks_operator_ontology`
sobre **frases operacionais**, nunca palavras soltas — o requisito da própria task.
Dois consumidores compartilham a mesma definição: `tests/test_prompt_operator_ontology.py`
e a métrica `operator_ontology_hits` do `tools/playtest_harness.py` (que também
passou a reportar `operator_ontology_phrases`).

Os testes cobrem as duas direções, que é o que faltava antes:

- `test_the_rule_catches_the_four_shapes_that_actually_shipped` — fixtures com as
  strings exatas que estavam em produção, inclusive as minúsculas que o assert
  case-sensitive aceitava;
- `test_the_rule_leaves_diegetic_language_alone` — "a única humana entre os elfos",
  "um player de alaúde", "as escolhas de cada personagem são sagradas" não podem
  disparar.

## Boundary real — o A/B do Director (curl-first, AGENTS.md §6)

Regra de decisão **pré-registrada antes de rodar**: shippar a variante cega só se,
em 4 runs por variante sobre o mesmo payload gravado, ela produzir `next_speakers`
não-vazio pelo menos tanto quanto a atual, e sem escolher o personagem controlado.

Payload: chamada `director` real do turno 1 da sessão `34f16498` (fala audível do
personagem controlado na última entrada de HISTORY). Só a regra 5 mudou entre as
variantes; o resto é byte a byte o que o servidor mandou.

| Variante | Filas vazias | `next_speakers` por run | Média de falantes |
|---|---:|---|---:|
| atual (com "player") | **0/4** | `[C2]`, `[C2,C3]`, `[C2]`, `[C2]` | 1,25 |
| cega (shippada) | **0/4** | `[C2,C3]`, `[C2]`, `[C2]`, `[C2,C3,C4]` | 1,75 |

Nenhuma das 8 runs escolheu C1 (o controlado). A regra pré-registrada passou e a
variante cega foi shippada exatamente como testada. **Observação honesta:** a
variante cega escolheu em média mais falantes (1,75 vs 1,25). Não é reprovação
pela regra registrada, mas se bursts ficarem mais longos que o esperado, este é o
primeiro lugar para olhar.

## Sessão real — as seis famílias

Servidor com a config real (DeepSeek), cenário built-in `turma-dos-portais-pt`,
jogado pelo frontend em viewport mobile (390×844) com swipe no carrossel.
**24 requests LLM auditados, 0 ocorrências:**

| Família | Chamadas |
|---|---:|
| `director` | 3 |
| `prose` | 4 |
| `alignment:impulse` | 4 |
| `character:*` | 4 |
| `roteiro:compile` + `roteiro_replan` | 3 |
| `perspective:init:*` + `perspective:update:*` | 4 |
| `narrator_suggest` | 2 |
| `opening_suggest` | 1 |
| `summarizer:world` (Historian, compactação forçada) | 1 |

Auditoria estática dos builders shippados, no mesmo estado real: **17 builders,
0 vazando**. Os três cenários built-in também: 0.

## Achado novo #1 — a `ROUTING CONSTRAINT` identifica o controlado

`narrator.py:451-456` emite `Do not include C1 in next_speakers this turn; they
just spoke or passed.` e `runner.py:2019` mostra que `exclude_speaker` é
**sempre** `game.player.controlled_character_id`. Ou seja: toda chamada do
Director com essa linha aponta qual personagem tem proteção especial.

Não corrigi de propósito. Duas razões:

1. na maior parte dos turnos a linha não acrescenta informação — que C1 acabou de
   agir já está visível no HISTORY;
2. mas durante um burst multi-beat (`beat_index < BURST_PROTAGONIST_EXCLUDE_BEATS`)
   ela reaparece em beats onde C1 **não** agiu, e aí marca C1 de graça.

Mexer nisso é mudar política de roteamento, o que exige o mesmo A/B da regra 5.
Fica como próximo passo, não como resto.

## Achado novo #2 — cenários do usuário não têm contrato

O cenário `star-wars-cantina-pt` (de usuário, em `.data/scenarios/`) tem uma
seção inteira:

```
AGÊNCIA DO JOGADOR
O jogador controla Dax Vanguard (C1). NENHUM agente escolhe falas, pensamentos,
decisões ou ações morais por Dax.
...as decisões do personagem controlado pelo humano (Dax Vanguard)...
```

Isso propaga para Director, Historian, sugestões e roteiro — 4 dos 17 builders
acusaram, e a origem é 100% conteúdo do dono. A task proíbe sanitização
silenciosa, e com razão: reescrever texto narrativo de alguém sem avisar é pior
que o vazamento.

O core está limpo; o que falta é **decidir o contrato**. Recomendação: avisar na
carga do cenário (a regra já existe e é barata de rodar), nunca mutar. Precisa da
sua decisão, então não implementei.

## Estado da suíte

815 testes passam (eram 805), `ruff` limpo, `mypy` limpo em 57 arquivos.
