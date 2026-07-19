# Roadmap — estado atual e sequência (atualizado 2026-07-16)

Fonte única de "onde estamos e o que vem". Atualize este arquivo a cada task
fechada ou mudança de sequência. Este arquivo é a fonte única da fila.
Referência de arquitetura:
`tasks/explore-29.2-architecture-map.md`. Artefatos de benchmark: `output29/`.

## ✅ Fechadas (todas com evidência medida e commit)

| Task | Entrega | Evidência-chave |
|---|---|---|
| 31 | Política única de retry no cliente LLM | zero runs perdidas por flake desde então |
| 34 | Fila multi-falante (`next_speakers`) | [C3,C2,C4] num turno, interação genuína |
| 29.1 | Baseline xfailed3 (fixture + ledger + 3 tiers) | 8/25 violações registradas |
| 29.2 inc.1 | Ledger de perspectiva + projeção viewer-relative | identidade 7/13 → 0/13 |
| 29.2 inc.2 | Eventos de percepção tipados + grafo de zonas | divisória estrutural 2/2 |
| 29.3 r.1 | Comparação baseline→pós-29.2, oráculo com proveniência | identidade → 0; cascata do Historian quantificada |
| 35 | Historiador privado com fronteira de percepção (3 camadas) | segredo 26 → 0; benchmark completo 25 → 2 |
| 33 | Drive: hazard scheduler + eventos externos em skip | A/B: cena travada anda; controle fica circular |
| 36.1 | Split Decisão/Prosa + renderizador cego | diálogo-em-narração 6+ → 0/4 por construção |
| 36.2 | `action_intent` + `zone_moves` + arestas dinâmicas | arco físico completo 2/2 (divisória que abre) |
| 32 | `routing_check` natural + custo por check no harness | 6/6 sondas; warm-up de cache visível |
| 28 | Force speaker (bug real: skip descartava a força) | aceitação real 6 rodadas, zero chamadas de personagem |
| 30 | Whisper UI no composer | payload/render/i18n; 9 testes de fronteira |
| **36** | **Split Diretor/Prosa + intents + zonas dinâmicas + audience_origin (v6)** | benchmark 25 -> 0 determinístico; diálogo-em-narração impossível; staging correto |
| 23 | Gap trim/compactação | pinning de âncoras de código + retenção adaptativa; os 2 xfails-spec verdes; suíte sem nenhum xfail |
| 37 | Loop autônomo limitado (rajada com paradas tipadas, undo por beat) | 3 runs ao vivo ×4 beats; parada `protagonist_decision` via `return_control`; crítico cego ×2 — classes estruturais zeradas por construção |
| 21 | Namespace de storage privado por plugin | `.data/plugins/storage/<id>/` + `context.storage` (path-safe: rejeita abs/`..`/symlink escape); contrato + permission + 16 testes + `docs/plugin-storage.md`; cached/ é concern separado (sem migração) |
| 39 | Memória do ledger (dimensão + revisão semântica + character_notes removidos, schema v9/v10) | revisão replay-validada em digests reais (1ª pessoa, segredos verbatim, sem fusão de referências); never-fail-the-turn; xfailed3 pós-39: **zero violações atribuíveis à memória** (o hit `perspective:memory:C5` era allowlist desatualizado — C5 é o confidente); contrato verbatim test-locked |
| 41 | Diretor onisciente + reconciliação de canon (emergencial) | replay produção 3/3 no caso real c2e5107b; 9 testes; guard determinístico `hidden_thought_tokens`; zonas dinâmicas + canon-antes-da-prosa; ressalva RESOLVIDA: xfailed3 completo pós-41 com **zero** violações das famílias de vazamento |
| 42 | Narrador fala pouco (emergencial) | puro curl em payloads reais: piso de 1 linha no FIM do PROSE_SYSTEM; mediana 118→1247 / 271→568 chars, 3/3 em 2 cenas; piso, nunca cap |
| 29.2 | Estado subjetivo (supertask) | concluída pelos incrementos: inc.1/inc.2 + Tasks 35, 36, 39, 41 (todas fechadas); medição continua no relógio 29.3 |
| 27 | SDK isolado + pipeline de curadoria (exploração) | topologia ACEITA pelo dono (2026-07-19); implementação vira trabalho novo quando priorizado |

## 🔶 Em andamento

| Task | O que falta |
|---|---|
| 38 — Roteiro (opt-in, OFF) | ressalvas devem ser resolvidas por 40+33b (decisão do dono 2026-07-19); **o dono fecha pessoalmente** todas as abertas na fase de testes dele, criando tasks menores |
| 19 — Security hardening | falta só o outcome 6 com o dono: roteiro pronto em **`.plan/19-smoke-tests-para-o-dono.md`** (3 ambientes, ~10 min cada); 3/3 verdes → fecho |
| 40 v2 — time-skip do relógio | ✅ **ENTREGUE** (2026-07-19): Diretor PEDE (schema 0-8 + regra no fim, validada 12 calls: cena viva 6/6 nunca pula, mesmo convidada), CÓDIGO convida no turno de passe e aplica clampado; sumário vira observation testemunhada; suíte 627. Falta só A/B/C unificada com 33b (dono) |
| 26b — re-descrição de ambiência via prompt | task experimental criada por decisão do dono ("via prompt; se não der, parquear"): `tasks/26b-ambience-redescription-prompt-experiment.md`; alvo 9%→<4% na banda 0.7–0.8 sem quebrar o piso da 42 |
| Relógio de saída do xfail (29.3 §15) | 3 runs completas limpas consecutivas com o oráculo calibrado; run pré-39/41 = 0 violações (primeira XPASS). **Run pós-39/41 (2026-07-19, madrugada): NÃO limpo — relógio segue em 0.** SP-01 T7 RESOLVIDA por calibração (decisão do dono + amostragem cega 3/3: leitura intra-turno é a mais natural — o som alcança o delegado no momento em que a divisória abre; regra agora isenta registros do turno-limite posteriores à ação de abertura; **tier reduzida retroativamente LIMPA, completa cai pra 1**). Resta WT-09 T24 (família conhecida: confabulação de alias — C2 recorda a revelação mas com enquadramento benevolente de cânon familiar, evita "Glinda"). Famílias da 41 (pensamento/segredo): **zero**. Falso positivo do allowlist (`perspective:memory:*` novo) corrigido no oráculo. Artefatos: scratchpad `xfailed3_run1_artifacts/` |

> **Convenção (2026-07-17):** só migra pra `.plan/closed/` a tarefa fechada COM CONFIANÇA. Tarefa entregue com ressalvas / sem fecho confiante fica em `.plan/tasks/` com as ressalvas no topo.

## 🌙 FILA DA MADRUGADA (2026-07-18, decisões do usuário já resolvidas)

Ordem de execução autônoma. Regras permanentes: commits em inglês sem trailer
de IA; método curl-first (AGENTS.md §6 — a variante validada É a shippada);
convenção closed/ = só fecho confiante; 529 storm → pular pra item zero-API e
voltar; `done.sh` ao fim de cada task.

| # | Task | Custo API | Decisões já tomadas |
|---|---|---|---|
| 0 | 42 — Narrador fala pouco | ✅ **ENTREGUE**: piso de 1 linha no FIM do PROSE_SYSTEM ("at least 150 words..."), medido 118→1247 / 271→568 chars medianos, 3/3 em 2 cenas; sem cap (regra AGENTS) |
| 1 | 39 inc2(a) — revisão semântica da memória | ✅ **ENTREGUE** (replay-validada em digests reais, 2 iterações de regra; never-fail-the-turn) |
| 2 | 39 inc2(b) — remover character_notes + checkpoint | ✅ **ENTREGUE** (summarizer world-only; schema bump autorizado) |
| 3 | 39 inc2(c) — reconciliar recall task 23 | ✅ **ENTREGUE** (pinning fica; segredos-verbatim test-locked) |
| 4 | xfailed3 run 1 | ✅ **RODADO, não limpo → sem runs extras** (decisão). Veredito na linha do relógio: 39/41 validadas (zero violações das famílias novas); 2 reais pré-existentes (SP-01 intra-turno, WT-09 alias) |
| 5 | 40 — relógio narrativo | ✅ **increment 1 ENTREGUE** (tick code-owned +1/beat; deadline de ato → world_event como UPCOMING EVENT; avanço de ato é do código; replay 2/3). Pendente: time-skip v2, A/B/C |
| 6 | 33b — exploração curl | ✅ **ENTREGUE** (delta material: detecta imobilidade semântica nas janelas travadas; contrato causal 3/3 amarrado a threads existentes; ver task 33b). Bateria A/B/C fica com o usuário |
| F | Fillers | MCP curl ✅ **ENTREGUE** (`replay_extract_call`/`replay_llm_call` no MCP de debug, só tools/, 17 testes). Restam: medição offline da guarda-por-sentença (26); fakes antigos do test_integration |

Pendências que precisam do dono: smoke tests da 19 (roteiro em
`.plan/19-smoke-tests-para-o-dono.md`); aceite do desenho da 33b
(`.plan/33b-desenho-para-o-dono.md`); bateria A/B/C unificada (33b + 40).


## 🧺 Lane paralela (independentes)

- 26 — Prosa do narrador (acumulador de evidências; boa parte dissolveu na 36;
  dominante atual: re-descrição de ambiência em cena estática).
  **Medição offline 2026-07-19** (4 sessões reais, 549 sentenças de narração
  vs narrações anteriores): eco residual ≥0.8 = 2 casos, ambos PÓS-compactação
  (a guarda por sentença não enxerga história compactada); banda 0.7–0.8
  (a re-descrição parafraseada: "estojo continua lacrado" → "jaz esquecido,
  lacre intacto") = 50/549 ≈ 9%; ≥0.85 praticamente nunca ocorre. Conclusão:
  o candidato retry-guard fuzzy >0.85 NÃO ganha nada; a família dominante é
  paráfrase abaixo da barra — mitigação teria que ser semântica (estilo
  delta-material da 33b) ou prompt. Script: scratchpad `measure26.py`.
- **Auto narrator_hint (estudo 2026-07-18)** — arquitetura validada em 55
  calls reais (4 domínios): Reaction Scout + Continuity Scout em paralelo →
  Judge closed-world escalar → compilador determinístico (nunca usar a string
  da LLM); `AUTHORIZATIONS` só de fonte estruturada (candidata natural:
  beat/owner do roteiro 38/40) ou lista vazia. Entra no MESMO canal
  narrator_hint do drive/relógio. Handoff completo:
  `.plan/narrator-hint-generalization-handoff.md`. Próximo passo (a decidir
  com o dono): harness experimental atrás de flag, fora do turno canônico.
- Fakes antigos de `tests/test_integration.py` (6) — lane do modelo menor
  (padrão: `action_intent` no payload + monkeypatch de `_render_narration`)

## 📌 Decisões diferidas (com dono)

- K-falantes core vs plugin → fechamento da 36
- ~~Undo através de rajada autônoma~~ → DECIDIDA na 37: undo = 1 beat (cada beat é um turno commitado)
- Roteiro nunca chega a personagem/prosa (spoilers) → 38 (regra já escrita)
- Matriz multi-modelo → EXCLUÍDA (decisão do usuário, 2026-07-15)
