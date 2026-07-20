# Task 45 — Continuação automática multi-beat no core

**Status:** 🟡 ABERTA — backend do núcleo ENTREGUE (2026-07-20), frontend + gates de
navegador/curl pendentes.

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

**Pendente:**
- **Frontend:** campo numérico de beats em Settings (espelho de
  `compaction_keep_recent_turns` em `runtime-config.js` + markup no `index.html` +
  i18n PT/EN) e o rename skip→"continuar história". Precisa de verificação
  Playwright 1080p/2K (boundary de navegador — não dá pra confirmar sem browser).
- **Gate curl do `next_speakers.description`** (variante Task 46, NÃO enum duro) —
  ver seção "Gate curl-first do schema".
- Smoke HTTP real (config→skip→múltiplos beats→motivo de parada) e README.

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
hipótese. Ver `.plan/tasks/46-schema-description-instruction-channel.md`.

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

- [ ] Default canônico de 6 beats.
- [ ] Limite personalizado válido.
- [ ] Rejeição de zero, negativo, booleano, texto e valor acima do máximo.
- [ ] Os dois primeiros beats excluem o personagem controlado.
- [ ] Terceiro beat e seguintes tornam o personagem controlado elegível.
- [ ] Seleção do protagonista interrompe imediatamente sem gerar sua fala.
- [ ] `return_control` interrompe imediatamente.
- [ ] Limite máximo encerra a sequência.
- [ ] Cena estabilizada encerra a sequência.
- [ ] Fila vazia encerra a sequência.
- [ ] Duas respostas consecutivas somente do Narrador encerram a sequência.
- [ ] Erro encerra a sequência sem repetir beat persistido.
- [ ] `force_speaker` e turno humano normal mantêm seus contratos.
- [ ] Campo é populado e serializado corretamente pelo frontend.
- [ ] Catálogo i18n contém toda microcopy PT-BR e EN.
- [ ] Service worker/cache inclui qualquer asset novo necessário.

## Boundaries de entrega

- [ ] Replay real `curl` 4/4 conforme a regra pré-registrada.
- [ ] Testes Python, frontend modules, adapters e parsing de HTML.
- [ ] Smoke HTTP real: config → skip → múltiplos beats → motivo de parada.
- [ ] Playwright em 1080p e 2K para Settings, ajuda do campo e botão de continuar.
- [ ] Inspeção do estado persistido e `debug.jsonl` após um burst real.
- [ ] README atualizado.
- [ ] Task movida para `.plan/closed/` somente após todos os gates aplicáveis.

## Fora de escopo

- Plugins ou plugin de self-healing.
- Reescrita retroativa de narração já persistida.
- Gerar qualquer decisão, fala, pensamento ou ação para o personagem controlado.
- Criar um segundo botão de “auto” que concorra com o skip/continuar.
- Usar o roteiro como requisito para o burst: a continuação deve funcionar com ou
  sem roteiro, respeitando as condições de parada do estado disponível.
