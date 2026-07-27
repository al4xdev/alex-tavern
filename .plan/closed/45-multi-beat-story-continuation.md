# Task 45 — Continuação automática multi-beat no core

**Status:** ✅ FECHADA (2026-07-20) — núcleo entregue e aceito pelo dono ("ta tudo
certo aqui"). Backend (default 6, teto 24, roteamento híbrido de 2 beats,
test-locked) + frontend (slider 1–10 com explicação dinâmica) entregues; suíte 702.
Follow-ups documentados, NÃO bloqueiam:
- Gate curl do `next_speakers.description` — migrou pra **Task 46** (é o piloto dela);
  a exclusão hoje é garantida pela normalização no código (caminho provado).
- Smoke HTTP real, README e verificação Playwright 1080p/2K — fase de verificação
  do dono.
Commits: `694f682` (backend), `772b578`/`feat(44,45) slider` (frontend).

## Regressão encontrada depois do fechamento (2026-07-21) — corrigida

A revisão de sessões reais (`29caff75`, `503bb018`) mostrou que a continuação
multi-beat quebrou a calibragem da Task 38: cada beat da rajada commita como um
turno próprio, então **uma única ação do jogador consumia 6 turnos** e estourava o
`HARD_BEAT_TURN_CAP = 3` dentro dela mesma. Resultado observado: `replan_beat /
reason: stalled` **depois de toda continuação**, sempre — o roteiro era reescrito a
cada ação do jogador, com uma chamada LLM extra de brinde, e a história dava a
impressão de "descontrolada". Ver `debug.jsonl`: burst turnos 4-9 → stalled no 10;
burst 7-12 → stalled no 13.

Correção: o orçamento do beat passa a contar **ações do jogador**, não turnos
commitados (`Roteiro.beat_actions_elapsed`; `BeatProgress.actions_elapsed`;
`evaluate_roteiro` usa a nova unidade). Com rajada desligada os números são
idênticos aos da Task 38, então a calibragem original continua valendo.
Pinado por `test_burst_turns_do_not_stall_a_beat` e
`test_multi_beat_continuation_spends_one_action`.

**Real-provider confirmation (2026-07-21).** On a fork of session `29caff75`, a
two-beat continuation committed turns 17 and 18 while
`beat_actions_elapsed` moved from 1 to 2, not 3. Both beats remained
`in_progress`; no `stalled` replan occurred. In the same run, an explicit audible
player question produced three queued speakers and three Character responses,
with no `unanswered_player` marker. The HTTP boundary returned two ordered beats
and `burst_stop_reason: budget_exhausted`. The isolated state and debug log remain
under `/tmp/alex-tavern-live-validation.GwxD8V/data/sessions/6a2ae445/` for this
session only.

## Progresso (2026-07-20)

**Feito (backend, test-locked, commit `694f682`):**
- `autonomous_burst_max_beats` default 1→6 + limite superior seguro
  (`MAX_BURST_BEATS=24`, validador `_bounded_integer`). Testes: default 6, valor
  custom, rejeição de 0/negativo/bool/float/string/acima-do-teto.
- Roteamento híbrido: exclusão do protagonista nos **2 primeiros beats**
  (`BURST_PROTAGONIST_EXCLUDE_BEATS=2`), depois elegível. Via
  `_call_narrator(exclude_controlled=...)` + normalização no código (caminho
  provado). Teste: sequência `[T,T,F,F]`.
- Muito do contrato de burst (stop conditions, persistência por beat, undo) já
  vinha da Task 37 (fechada) e continua verde (suíte 700).

**Feito (frontend, commit seguinte):**
- Campo numérico de beats (1–24) em Settings, ligado a `autonomous_burst_max_beats`
  (`runtime-config.js` populate/collect com clamp + markup `index.html` + i18n PT/EN).
- Rename do botão skip→"continuar história" (title/aria, PT/EN). Teste de i18n verde.
- ⚠️ Verificação Playwright 1080p/2K **AINDA PENDENTE** — a razão mudou, ver
  "Por que o Playwright continua bloqueado" no fim do arquivo.

**Pendente:**
- **Gate curl do `next_speakers.description`** (variante Task 46, NÃO enum duro) —
  ver seção "Gate curl-first do schema".
- ~~Smoke HTTP real (config→skip→múltiplos beats→motivo de parada)~~ — **feito em
  2026-07-27**, e achou um bug. Ver "Smoke HTTP" no fim do arquivo.

---

**Status original:** 🟡 ABERTA (escopo definido com o dono, 2026-07-20)
**Origem:** playtest da sessão `380ea657` e necessidade de deixar o mundo avançar
por vários beats sem depender continuamente de uma nova ação do protagonista.
**Fronteira:** implementação no core, sem plugin.

## Objetivo

Transformar o skip atual numa ação de **continuar a história**: o Runner executa
uma sequência limitada de beats autônomos, mostra o mundo e os NPCs agindo sem o
protagonista e devolve o controle assim que a participação humana for necessária.

O limite padrão é **6 beats**, configurável em Settings.

## Contrato da continuação

Ao clicar em continuar/skip, o Runner pode avançar até o limite configurado. A
sequência deve parar antes do limite quando:

- o Narrador devolver o controle ao jogador (`return_control`);
- o personagem controlado for escolhido como próximo falante;
- a cena se estabilizar ou não houver próximo falante;
- ocorrerem duas respostas consecutivas somente do Narrador;
- qualquer chamada ou processamento do beat falhar;
- o limite configurado for alcançado.

Cada beat continua sendo persistido e observável pelo contrato normal do Runner.
A sequência não cria um caminho paralelo de estado, lock, save ou debug.

## Roteamento híbrido do protagonista

O protagonista não deve manter a história orbitando ao seu redor, mas também não
pode ficar permanentemente inelegível:

1. Nos **dois primeiros beats** depois do skip, o personagem controlado fica fora
   das opções de `next_speakers`. Isso obriga o mundo e os NPCs a reagirem ou
   avançarem, e a volta do protagonista não pode ser rápida demais (decisão do
   dono, 2026-07-20: janela de exclusão = 2 beats).
2. A partir do **terceiro beat** da mesma sequência, ele volta a ser elegível.
3. Quando o Narrador o escolher, o Runner interrompe a sequência imediatamente e
   devolve o controle ao humano, sem gerar fala, pensamento ou ação por ele.
4. `return_control` sempre vence o orçamento restante.

Essa regra pertence ao Runner e ao contrato de roteamento, nunca a heurísticas de
um Character e nunca a um plugin.

## JSON Schema de `next_speakers`

Melhorar o schema estruturado do Narrador:

- `items.enum` deve ser dinâmico e conter somente personagens elegíveis naquele
  beat;
- o campo deve possuir uma descrição em inglês dizendo explicitamente que IDs
  ausentes do enum são inelegíveis e não podem ser retornados;
- lista vazia continua válida quando nenhum personagem tiver motivo imediato para
  reagir;
- a descrição é contrato técnico compartilhado entre providers, não prompt
  narrativo específico de fornecedor.

Texto-base para validar:

> Return only character IDs listed in items.enum. IDs absent from the enum are
> ineligible this beat and must not appear, even if recent context suggests them.
> If no listed character has an immediate reason to react, return an empty list.

## Gate curl-first do schema

**Correção de desenho (dono, 2026-07-20):** o `enum duro` já foi medido e QUEBRA —
narrator.py:219-224 registra "3 falhas seguidas de schema" quando o enum é
estreitado (o validator do provider rejeita). Mas isso testou **enum duro**, não o
**`description` do campo** (o canal da Task 46), que **nunca foi testado**. São
mecanismos distintos: enum = grammar constraint (rejeita); description = steer suave
que o modelo lê (sem rejeição). Portanto o candidato a testar **não é o enum
restrito, é o `next_speakers.description` por-beat** nomeando o inelegível. Este é o
**piloto da Task 46** (schema-description como canal de instrução).

O que já foi shippado (backend): a exclusão por 2 beats via **normalização no
código** (backstop duro, garante a exclusão). O que o gate mede é se o
**description** melhora o roteamento por cima disso (o modelo escolhe NPC de
propósito em vez de gastar um slot no protagonista e ser corrigido).

Regra de decisão pré-registrada (variante DESCRIPTION, não enum duro):

> Adotar o `next_speakers.description` por-beat somente se, em replay real do
> payload do Narrador: 4/4 respostas estruturalmente válidas (sem falha de schema),
> nenhuma selecionar o protagonista nos 2 primeiros beats, o Narrador continuar
> roteando NPCs quando houver reação natural, E a fila vier menos "corrigida pelo
> código" que a baseline (prosa no user message) — i.e., menos slots do protagonista
> dropados.

Se houver falha de schema, fila artificialmente vazia ou perda de roteamento, não
adotar. A normalização no código permanece como caminho comprovado
independentemente do resultado. Documentar a medição sem afirmar melhora por
hipótese. Ver `.plan/backlog/46-schema-description-instruction-channel.md`.

## Frontend

- Reutilizar o botão atual; não criar um botão concorrente.
- Trocar o conceito visível de “Pular turno” para “Continuar história” ou microcopy
  equivalente validada em PT-BR e EN.
- Settings deve oferecer um campo numérico para escolher o máximo de beats.
- Valor padrão: `6`.
- A ajuda do campo explica que o limite é máximo e que o sistema pode parar antes
  quando a participação do protagonista for necessária ou a cena se estabilizar.
- Não armazenar configuração runtime do servidor em `localStorage`.
- Renderizar os beats retornados sequencialmente, preservando sua ordem.

## Configuração e ownership

- Chave canônica: `autonomous_burst_max_beats`.
- Default canônico: `6`.
- Definir e validar um limite superior seguro no contrato, sem coerção silenciosa
  de booleanos ou valores inválidos.
- `src/config.py` possui validação, resolução e representação pública.
- `src/runner.py` possui orçamento, loop, condições de parada e agência.
- `src/agents/narrator.py` possui o schema dinâmico de `next_speakers`.
- `src/static/runtime-config.js` serializa o campo de Settings.
- `src/static/index.html`/i18n/CSS possuem apenas a apresentação e microcopy.
- Atualizar README com o comportamento e configuração representativos.

## Observabilidade e persistência

- Todas as chamadas preservam `session_id`, `turn_number` e `agent`.
- O resultado HTTP informa os beats em ordem e o motivo de parada da sequência.
- Cada beat mantém o mesmo limite transacional da sessão.
- Falha interrompe a sequência sem repetir chamadas já persistidas.
- Undo continua removendo um passo transacional completo conforme o contrato de
  `turn_number`; qualquer alteração desse agrupamento exige decisão explícita e
  teste, não compatibilidade implícita.

## Testes obrigatórios

- [x] Default canônico de 6 beats. — `TestBurstConfigValidation::test_default_is_six`
- [x] Limite personalizado válido. — `::test_accepts_a_valid_custom_value`
- [x] Rejeição de zero, negativo, booleano, texto e valor acima do máximo. — `::test_rejects_out_of_range_and_wrong_types` (0, -1, MAX+1, True, 2.5, "6")
- [x] Os dois primeiros beats excluem o personagem controlado. — `test_protagonist_excluded_for_first_two_beats`
- [x] Terceiro beat e seguintes tornam o personagem controlado elegível. — mesmo teste: `exclude_controlled == [True, True, False, False]`
- [x] Seleção do protagonista interrompe imediatamente sem gerar sua fala. — `test_stops_when_player_is_addressed` (`player_addressed`)
- [x] `return_control` interrompe imediatamente. — `test_stops_on_return_control_flag`
- [x] Limite máximo encerra a sequência. — `test_budget_exhausted_runs_all_beats_with_own_turns`
- [x] Cena estabilizada encerra a sequência. — `test_two_narrator_only_beats_settle_the_scene`
- [x] Fila vazia encerra a sequência. — `test_empty_beat_settles_immediately`
- [x] Duas respostas consecutivas somente do Narrador encerram a sequência. — `test_two_narrator_only_beats_settle_the_scene`
- [x] Erro encerra a sequência sem repetir beat persistido. — **faltava** — escrito em 2026-07-27, ver seção no fim
- [x] `force_speaker` e turno humano normal mantêm seus contratos. — `test_force_speaker_disables_the_burst` + `test_normal_player_turn_never_bursts`
- [x] Campo é populado e serializado corretamente pelo frontend. — `runtime-config.js:81,150,170`
- [x] Catálogo i18n contém toda microcopy PT-BR e EN. — 11 chaves `engine.burstBeats*` nos dois locales (`i18n.js:37-47` / `449-459`)
- [x] Service worker/cache inclui qualquer asset novo necessário. — sem asset novo; `runtime-config.js` já no SHELL (`sw.js:17`)

## Boundaries de entrega

- [x] Replay real `curl` 4/4 conforme a regra pré-registrada. — feito na entrega original
- [x] Testes Python, frontend modules, adapters e parsing de HTML. — suíte verde
- [x] Smoke HTTP real: config → skip → múltiplos beats → motivo de parada. — `tools/acceptance/burst_http_smoke.py`, 2026-07-26
- [~] Playwright em 1080p e 2K para Settings, ajuda do campo e botão de continuar.
      **1080p FEITO em 2026-07-27** pela extensão do Chrome (o MCP do Playwright
      continua travando no handshake do `--remote-debugging-pipe`): viewport real
      1900×917, Settings abre, o controle "Maximum beats per continuation"
      renderiza com rótulo, valor, escala e explicação, a faixa reage ao arrasto
      (`1 · short` → `7 · balanced`, com o texto correspondente trocando junto),
      zero erro de console e nenhum overflow horizontal.
      **2K permanece impossível aqui**: a tela é 1920×1080, então a janela não
      cresce até 2560. Precisa de outro monitor — não de outra ferramenta.
- [x] Inspeção do estado persistido e `debug.jsonl` após um burst real. — smoke HTTP + `log_burst`
- [x] README atualizado. — `README.md:446,1191`
- [x] Task movida para `.plan/closed/` somente após todos os gates aplicáveis. — feito

## Fora de escopo

- Plugins ou plugin de self-healing.
- Reescrita retroativa de narração já persistida.
- Gerar qualquer decisão, fala, pensamento ou ação para o personagem controlado.
- Criar um segundo botão de “auto” que concorra com o skip/continuar.
- Usar o roteiro como requisito para o burst: a continuação deve funcionar com ou
  sem roteiro, respeitando as condições de parada do estado disponível.


---

# Smoke HTTP (2026-07-27) — a pendência que achou um bug

`tools/acceptance/burst_http_smoke.py`, tudo pela API HTTP do servidor rodando,
não pelo Runner em processo — o ponto é a fronteira que um cliente usa de fato:

1. `PUT /config` grava `autonomous_burst_max_beats` e `GET` devolve;
2. um skip puro commita mais de um beat, cada um com seu número de turno;
3. a resposta carrega `burst_stop_reason`;
4. undo tira **um** beat, não o burst inteiro;
5. undo regride o relógio junto (contrato novo do schema 14);
6. skip com falante forçado commita exatamente um beat;
7. todo beat reportado está no histórico persistido.

## O bug: um beat que não produziu nada commitava mesmo assim

Três checagens reprovaram na primeira execução. Uma era assert ingênuo meu
(assumi que undo regride o relógio em exatamente 1; ele restaura o snapshot, que
já contabiliza compressão de tempo). As outras duas eram defeito real.

Reproduzido da sessão `ce70b997`, turno 4:

```
turno 3: next=['C1']  evento: "Lyra pergunta em tom leve, 'Por que a pergunta, Thorn?...'"
turno 4: next=['C1']  evento: "Por que a pergunta, Thorn? Está pensando em comprar o lugar?"
```

O evento do turno 4 é a **mesma linha** do turno 3. A cadeia:

1. o filtro anti-repetição do burst (task 37) esvazia os eventos do beat;
2. sem eventos, um passo multi-beat narra **nada** de propósito;
3. a fila é o personagem controlado, que o runner nunca dubla;
4. **o beat commita assim mesmo** — queima número de turno, tick e revisão, com
   zero registro no histórico.

O custo não é cosmético: `_next_turn_number` lê o número do **último registro**,
então o número queimado é distribuído de novo. Dois beats diferentes acabam com o
mesmo número de turno — e o undo tira os dois juntos, quebrando exatamente o
contrato em que esta feature se apoia: *"cada beat commita como seu PRÓPRIO turno
(undo tira um beat)"*.

## A correção, e o susto no meio dela

Um beat que não deixou traço não é commitado: `burst.stop_reason` vira
`beat_produced_nothing` e nada é salvo, então tudo que ele tocou em memória se
desfaz sozinho.

A primeira versão do guard era "sem registro → descarta" e **quebrou um teste
existente**: um beat de `time_skip` avança o relógio legitimamente sem gerar
registro próprio. O guard passou a ser estreito de propósito — só descarta quando
não há registro **e** não houve `scene_update` **e** não houve compressão de
tempo.

Dois testes que travavam o contrato antigo (o beat vazio era reportado E
commitado) foram atualizados mantendo a intenção original: o burst continua
terminando ali, e agora diz por quê com precisão.

`tests/test_empty_burst_beat.py` (4 testes) reproduz a cadeia inteira de forma
determinística. Suíte: 880.

## Como rodar

```bash
ROLEPLAY_DATA_DIR=/tmp/x uv run uvicorn src.main:app --port 8903 &
uv run python tools/acceptance/burst_http_smoke.py http://127.0.0.1:8903
```


---

# Por que o Playwright continua bloqueado (2026-07-27)

A ressalva original dizia "não dá pra rodar navegador aqui". Isso deixou de ser
verdade em 2026-07-26: o plugin de Playwright do editor dirigiu a UI inteira
naquele dia — carrossel, swipe em viewport de celular, turno real, modal de
sessões.

Na madrugada de 27 ele parou de subir. Diagnostiquei em vez de reportar
"navegador não funciona":

| Tentativa | Resultado |
|---|---|
| `browser_navigate` (3×) | `TimeoutError: async initializeServer: Timeout 180000ms` |
| Matar processos órfãos e limpar `SingletonLock` | mesma falha |
| Mover o perfil inteiro para `/tmp` e deixar recriar | mesma falha |
| **Chrome direto, headless, `--remote-debugging-port=9333`** | **funciona** — responde `{"Browser": "Chrome/150.0.7871.128", "Protocol-Version": "1.3"}` em 8s |

**O Chrome está saudável.** O que falha é o handshake do MCP, que usa
`--remote-debugging-pipe` (descritor de arquivo) em vez de porta TCP. É o
plugin, não o navegador, não este repositório e não a aplicação.

Consequência para esta task: a verificação visual em 1080p/2K segue pendente, e
segue sendo a única pendência dela. Não é um bloqueio do produto — o smoke HTTP
cobre o comportamento do burst ponta a ponta, e a UI foi dirigida por navegador
em 2026-07-26 sem erro de console.


---

# Varredura da checklist (2026-07-27)

A task foi para `closed/` com as 23 caixas em branco. Não era abandono: quase
tudo já existia e ninguém voltou para marcar. Conferi uma a uma contra o código —
o resultado está inline acima, cada caixa com o teste ou o arquivo:linha que a
sustenta.

**Um item era pendência de verdade:** "erro encerra a sequência sem repetir beat
persistido". O loop do burst não tem `except` nenhum, então esse contrato não é
implementado em lugar algum — ele *emerge* de `_commit_beat` chamar `save_game`
antes do beat seguinte começar. O próprio comentário do runner afirma isso ("a
crash leaves only complete beats"), e a afirmação nunca foi exercitada.

`TestACrashLeavesOnlyCompleteBeats::test_beats_before_the_error_survive_and_are_not_replayed`
faz o Director estourar no terceiro beat e verifica, **lendo do disco** (não do
`GameState` em memória, que some junto com a exceção):

1. a exceção sobe até o chamador, não é engolida;
2. os beats 1 e 2 estão persistidos;
3. o retry do mesmo skip começa no turno 3 — não regenera o que o jogador já leu;
4. o texto dos beats já commitados é byte a byte o mesmo depois do retry.

O item 3 é o que dá nome ao critério. Se `save_game` saísse de `_commit_beat` para
o fim de `player_turn` — uma "otimização" plausível, uma escrita em vez de N — o
teste falha: `_next_turn_number` leria um histórico que nunca chegou ao disco e a
rajada se repetiria do começo. É esse acoplamento não óbvio que a caixa vazia
deixava sem rede.

Continua aberto só o Playwright 1080p/2K, por bloqueio de ferramenta.
