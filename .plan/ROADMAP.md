# Roadmap — estado atual e sequência (atualizado 2026-07-16)

Fonte única de "onde estamos e o que vem". Atualize este arquivo a cada task
fechada ou mudança de sequência. Referência de arquitetura:
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

## 🔶 Em andamento

| Task | O que falta |
|---|---|
| **36 (fechamento)** | (a) crítico cego subjetivo dos transcripts pós-fix (API dos subagentes em 529, 4 tentativas — rodar quando voltar); (b) rodada 29.3 com fixture ZONADO (re-autoria de beats: divisória abre no T8 via `zone_link_updates`; ~meio dia) |
| **28 — Force speaker** | EM EXECUÇÃO — investigação evidence-first (sessão 091b11c6) |
| **30 — Whisper UI** | EM EXECUÇÃO — seletor de audiência no composer + render de sussurros + i18n |
| **README principal** | EM EXECUÇÃO — refletir a arquitetura pós-split |

## 📋 Sequência principal (após 28/30)

| Ordem | Task | Depende de |
|---|---|---|
| 1 | 37 — Loop autônomo limitado (paradas, undo de rajada, render progressivo) | 36 |
| 2 | 38 — Roteiro com contratos de beat tipados + replan algorítmico | 36 |
| 3 | 39 — Dimensão de memória do ledger (remove `character_notes`) | 35 ✅; melhor pós-36 |
| 4 | Rodadas de saída 29.3 (xfail estrito sai com 3 runs completas limpas — §15) | cada incremento |

## 🧺 Lane paralela (independentes)

- 23 — Gap trim/compactação (2 xfails estritos como spec)
- 26 — Prosa do narrador (acumulador de evidências; boa parte dissolveu na 36;
  dominante atual: re-descrição de ambiência em cena estática — mitigação
  candidata: retry-guard fuzzy >0.85)
- Fakes antigos de `tests/test_integration.py` (6) — lane do modelo menor
  (padrão: `action_intent` no payload + monkeypatch de `_render_narration`)

## 📌 Decisões diferidas (com dono)

- K-falantes core vs plugin → fechamento da 36
- Undo através de rajada autônoma → 37
- Roteiro nunca chega a personagem/prosa (spoilers) → 38 (regra já escrita)
- Matriz multi-modelo → EXCLUÍDA (decisão do usuário, 2026-07-15)
