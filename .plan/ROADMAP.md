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

## 🔶 Em andamento

| Task | O que falta |
|---|---|
| 39 — Memória do ledger | increment 1 FEITO (dimensão de memória, schema v8, 560 testes). **increment 2 (risco: compactação)**, guia em `HANDOFF-FABLE.md` |
| 27 — SDK isolado + pipeline de curadoria | **exploração DELIVERED** (`docs/plugin-ecosystem-topology-exploration-2026-07-17.md`); aguarda aceite do dono + verificação com checkout do hub |
| 38 — Roteiro (opt-in, OFF) | **ENTREGUE COM RESSALVAS, mantida aberta** (não migra pra closed/): ganhos de engine banked, mas o roteiro é cara-ou-coroa em cena procedural (portais 2W/2L). Ver banner na task + relatório em `docs/cases/`. Fixes futuros: disrupção avança o arco; watcher 33b |
| 41 — Diretor onisciente + reconciliação de canon (EMERGENCIAL) | **ENTREGUE** (replay produção 3/3 no caso real c2e5107b; 9 testes; guard determinístico de thought; zonas dinâmicas; canon-antes-da-prosa); ressalva: revalidar famílias de vazamento no relógio do xfail |
| 19 — Security hardening | **ENTREGUE COM RESSALVAS**: boundary origem+token + política de alvo de provider implementados e revisados (buraco do origin `null` fechado; same-origin LAN liberado; token nunca persistido; 403-retry pós-restart); falta só o outcome 6 (smoke tests desktop/Docker/Android) |
| Relógio de saída do xfail (29.3 §15) | 3 runs completas limpas consecutivas com o oráculo calibrado; run 1 = 0 violações (primeira XPASS do programa); variância semântica restante: cumprimento de promessa, discrição vs auditoria, confabulação de alias |

> **Convenção (2026-07-17):** só migra pra `.plan/closed/` a tarefa fechada COM CONFIANÇA. Tarefa entregue com ressalvas / sem fecho confiante fica em `.plan/tasks/` com as ressalvas no topo.

## 🌙 FILA DA MADRUGADA (2026-07-18, decisões do usuário já resolvidas)

Ordem de execução autônoma. Regras permanentes: commits em inglês sem trailer
de IA; método curl-first (AGENTS.md §6 — a variante validada É a shippada);
convenção closed/ = só fecho confiante; 529 storm → pular pra item zero-API e
voltar; `done.sh` ao fim de cada task.

| # | Task | Custo API | Decisões já tomadas |
|---|---|---|---|
| 0 | **42 — Narrador fala pouco (EMERGENCIAL)**: prosa curta demais; não é max_tokens, é prompt. Achar FRASE PEQUENA que destrave o deepseek (prompts já estão grandes). Puro curl em payloads reais; suspeito nº 1: "vivid but economical" no PROSE_SYSTEM | baixo | frase mínima, posição no FIM (lição 41); nunca CAP de frases (regra AGENTS) — só piso/riqueza |
| 1 | 39 inc2(a) — revisão semântica da memória (builder → replay → wire) | baixo | never-fail-the-turn no LLM da revisão |
| 2 | 39 inc2(b) — remover character_notes + checkpoint | zero | **schema v9 AUTORIZADO** (sessões existentes quebram, ok) |
| 3 | 39 inc2(c) — reconciliar recall task 23 | zero | pinning de âncora fica |
| 4 | xfailed3 run 1 (valida 39d + famílias de vazamento da 41) | alto | **1 run; +2 só se limpo; cap 3** |
| 5 | 40 — relógio narrativo | ✅ **increment 1 ENTREGUE** (tick code-owned +1/beat; deadline de ato → world_event como UPCOMING EVENT; avanço de ato é do código; replay 2/3). Pendente: time-skip v2, A/B/C |
| 6 | 33b — exploração curl (delta material + contrato causal em payloads reais) | médio (~20 calls) | **bateria A/B/C só com o usuário acordado** |
| F | Fillers (quando bloqueado): MCP curl simples SÓ em tools/ (**autorizado**); medição offline da guarda-por-sentença (26); fakes antigos do test_integration | zero | — |

Pendências que precisam do usuário (NÃO tocar de madrugada): smoke tests da 19
(desktop/Docker/Android); aceite da exploração 27; bateria A/B/C da 33b.


## 🧺 Lane paralela (independentes)

- 26 — Prosa do narrador (acumulador de evidências; boa parte dissolveu na 36;
  dominante atual: re-descrição de ambiência em cena estática — mitigação
  candidata: retry-guard fuzzy >0.85)
- Fakes antigos de `tests/test_integration.py` (6) — lane do modelo menor
  (padrão: `action_intent` no payload + monkeypatch de `_render_narration`)

## 📌 Decisões diferidas (com dono)

- K-falantes core vs plugin → fechamento da 36
- ~~Undo através de rajada autônoma~~ → DECIDIDA na 37: undo = 1 beat (cada beat é um turno commitado)
- Roteiro nunca chega a personagem/prosa (spoilers) → 38 (regra já escrita)
- Matriz multi-modelo → EXCLUÍDA (decisão do usuário, 2026-07-15)
