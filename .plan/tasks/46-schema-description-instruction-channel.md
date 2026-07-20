# Task 46 — Schema `description` as the primary instruction channel (structured output)

**Status:** 🔵 GUARDADA (backlog / design note, 2026-07-20). Re-trabalho grande e
transversal, **gated atrás de re-validação curl**. NÃO iniciar em partes (meia
migração = estado não-validado).
**Origem:** observação do dono (eng de GenAI), 2026-07-20.

## A ideia

O canal mais confiável pra dirigir **saída estruturada** não é o system nem o user,
e sim os campos `description` do **JSON Schema** passado no request (por-propriedade,
e o description de nível de schema). Instrução colada ao slot exato que o modelo vai
preencher é seguida mais fielmente do que a mesma regra enterrada em prosa no system,
e fica **local** ao campo que governa.

## Por que importa aqui

- Hoje a instrução de *shape de saída* vive no system: a taxonomia de delta do
  watcher, a regra de atribuição da appraisal, os constraints de saída do Character,
  a elegibilidade de `next_speakers`. Muito disso é guidance **por-campo** que
  pertence ao campo.
- **Rastreabilidade ("rastrear todos"):** com a regra no schema, todo constraint é
  enumerável num único lugar estruturado — dá pra auditar/rastrear o que governa cada
  campo de saída, em vez de prosa espalhada por N system prompts.
- O projeto **já faz isso** num ponto: o `next_speakers` da Task 45 carrega
  "Return only character IDs listed in items.enum..." como description do campo — o
  padrão que esta task generaliza.

## Nuance (escopo honesto — é re-balancear, não apagar system)

- **Schema-description GANHA** pra: constraints/formato de campo, semântica de enum,
  do/don't por-slot, forma da saída. (delta categories; appraisal
  direction/attribution; next_speakers eligibility; speech/thought split.)
- **System ainda carrega**: persona/papel global, enquadramento de tarefa,
  invariantes de confidencialidade, e raciocínio não atado a um único slot.

## O custo que torna isto backlog, não agora

- Mover carga de instrução muda o prompt efetivo de **todo** agente estruturado. A
  regra da casa é **"a variante validada É a shippada"** — então isto quebra o estado
  curl-validado de cada um: watcher delta (4/4), appraisal (4/5), guard de saída do
  Character, beat do roteiro, prose, narrator, banda de disposição.
- Cada schema migrada precisa **re-rodar seu gate curl** provando que a variante-
  schema ≥ a variante-system naquela métrica. É campanha de re-validação, não refactor.
- Portanto: **nada de migração piecemeal.** Ou é uma campanha deliberada e orçada com
  A/B por-agente (variante system vs variante schema, gate cego), ou não é.

## Piloto barato proposto (primeiro passo de baixo risco)

A schema de **disposição/appraisal** (`build_appraisal_schema`) é nova, tem
`description` vazio por campo, e o gate dela custa ~20 chamadas curl
(`scratchpad/exp_disposition_appraisal.py`). Migrar a regra de atribuição e a
disciplina "most turns shift nothing" do system pro `description` dos campos ali, e
re-rodar o gate (≥4/5, mesmo limiar), **prova ou mata o lift** sem tocar em nenhum
outro agente. Se o piloto mostrar ganho, aí sim decidir a campanha.

## Aceite (rascunho — congela ao iniciar)

- [ ] Inventário de toda schema de saída estruturada; classificar cada instrução do
  system como **field-local (movível)** vs **global (fica)**.
- [ ] Por agente, gate curl A/B: variante-schema vs atual, pré-registrado; a
  variante-schema precisa ser ≥ a atual na métrica existente daquele agente.
- [ ] Saída de rastreabilidade: um registro que lista, por campo de saída, a
  description que o governa (o ganho "rastrear todos").
- [ ] Sem regressão de confidencialidade (mover texto pra schema não pode vazar
  roteiro/segredo numa chamada estruturada de um viewer).
- [ ] README/AGENTS documenta schema-description como o canal canônico de guidance
  field-local.

## Fora de escopo

- Mover persona/enquadramento global ou invariante de confidencialidade pra schema.
- Qualquer migração sem o gate de re-validação por-agente daquele prompt.
- Reescrever prompts já shippados "por elegância" sem provar o lift por curl.
