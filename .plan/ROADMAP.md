# Roadmap — estado atual e sequência (atualizado 2026-07-16)

Fonte única de "onde estamos e o que vem". Atualize este arquivo a cada task
fechada ou mudança de sequência. **Handoff ativo: `HANDOFF-OPUS.md`** (fila
detalhada + regras de commit para o Opus; Task 38 implementada, falta
aceitação A/B). Referência de arquitetura:
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
| 38 | Roteiro com contratos de beat tipados + replan algorítmico | A/B deepseek ao vivo, crítico cego ×5 (embaralhado); arm roteiro vence drive + objetivo-por-NPC; variação lexical garantida por construção (backstop); confidencialidade NONE; gatilhos 100% determinísticos |

## 🔶 Em andamento

| Task | O que falta |
|---|---|
| Relógio de saída do xfail (29.3 §15) | 3 runs completas limpas consecutivas com o oráculo calibrado; run 1 = 0 violações (primeira XPASS do programa); variância semântica restante: cumprimento de promessa, discrição vs auditoria, confabulação de alias |

## 📋 Sequência principal (após 28/30)

| Ordem | Task | Depende de |
|---|---|---|
| 1 | 39 — Dimensão de memória do ledger (remove `character_notes`) | 35 ✅; melhor pós-36 |
| 2 | Rodadas de saída 29.3 (xfail estrito sai com 3 runs completas limpas — §15) | cada incremento |
| — | Render progressivo da rajada (SSE por beat) — lane de UI; arquitetura já suporta | 37 ✅ |

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
