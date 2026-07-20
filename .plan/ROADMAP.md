# Roadmap — estado atual e sequência (atualizado 2026-07-16)

Fonte única de "onde estamos e o que vem". Atualize este arquivo a cada task
fechada ou mudança de sequência. Este arquivo é a fonte única da fila.
Referência de arquitetura:
`reference/explore-29.2-architecture-map.md`. Artefatos de benchmark: `output29/`.

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
| 19 | Security hardening (fronteira de origem + alvos de provider) | token por-servidor + guarda de origem em toda mutação; política de `api_base` no contrato do adapter (deepseek HTTPS/host fixo; llama_cpp loopback/rede privada); token nunca persistido, rotação em 403. **Smoke tests 3/3 verdes** (desktop/Docker/Android) — outcome 6 fechado pelo dono |
| 40 | Relógio narrativo (tick sempre anda) | inc.1 (tick code-owned +1/turno; deadline de ato força world_event + avança) + inc.2 (time-skip: cena viva nunca pula 6/6, clamp 0..8) + bateria A/B/C (braço C sustentou 6 turnos sem watcher). Aceite completo test-locked; tick sempre-on, deadline gated por `roteiro_enabled` |

## 🔶 Em andamento

| Task | O que falta |
|---|---|
| 38 — Roteiro (opt-in, OFF) | ressalva de disrupção-desconexa ENDEREÇADA (2026-07-20) pela camada 33b (intervenção causal 9/9), não pelo prompt do roteiro (rewrite causal do beat `stalled` deu empate 5/6 no A/B → revertido); demais ressalvas **o dono fecha pessoalmente** na fase de testes dele |
| 26b — re-descrição de ambiência via prompt | ⏸️ **PARQUEADA (fallback do dono)**: 24 calls, 3 variantes em 2 iterações — TODAS pioraram a banda (16.4%→21-23%); linha sobre cenário vira ímã de atenção. Direção futura: nível dos eventos (delta-material da 33b), não prompt. Resultado completo na task |
| Relógio de saída do xfail (29.3 §15) | 3 runs completas limpas consecutivas com o oráculo calibrado; run pré-39/41 = 0 violações (primeira XPASS). **Run pós-39/41 (2026-07-19, madrugada): NÃO limpo — relógio segue em 0.** SP-01 T7 RESOLVIDA por calibração (decisão do dono + amostragem cega 3/3: leitura intra-turno é a mais natural — o som alcança o delegado no momento em que a divisória abre; regra agora isenta registros do turno-limite posteriores à ação de abertura; **tier reduzida retroativamente LIMPA, completa cai pra 1**). Resta WT-09 T24. **RAIZ DIAGNOSTICADA (2026-07-20, curl-first no payload real): NÃO é confabulação de LLM — é um buraco de data-flow.** No T20 o Diretor revelou "a Dama do Norte é Glinda, que planeja a conquista" como um `audible_speech` perception event (witness_ids inclui C2), mas eventos `audible_speech` do Diretor NUNCA são persistidos em `game.history` (só input do jogador, narração cega e falas de personagem entram). No T20 só C4 (Holmes) estava na fila de resposta, então C2 nem viu ao vivo, e nada foi gravado → a memória (que lê o history) nunca recebeu o nome → no T24 o modelo preenche o buraco com o prior pré-treinado ("Bruxa Boa do Norte"). **WT-09 tem DOIS modos (diagnosticado 2026-07-20 rodando o oráculo 4×):**
(1) **record-dropping** — a revelação É lida em voz alta no T20 mas eventos
`audible_speech` do Diretor não eram persistidos → memória nunca recebe.
**CORRIGIDO + leak-safe:** o runner grava audible_speech do Diretor SÓ quando
GENUINAMENTE PÚBLICO (todos os presentes ouvem; fala pública não tem segredo).
Curl no payload real do T24: BEFORE 0/4 vs AFTER 4/4 naming "Glinda"; oráculo
full-tier confirmou WT-09 sumido no run com revelação pública.
(2) **Diretor difere a nomeação** — às vezes o Diretor só emite o preâmbulo no
T20 ("a cifra nomeia o patrono...") e NUNCA lê os nomes; aí "Glinda" nunca vira
público e nenhuma persistência resolve. Modo estocástico, Director-side.
**Regressão de vazamento pega e fechada:** o 1º corte persistia audible_speech
parcial (o Diretor re-narra um WHISPER com escopo "audível aos próximos" mas
conteúdo secreto) → vazou LUMEN-17 em 8 prompts (`GLOBAL-secret-in-unauthorized`,
família zerada). Regra público-apenas eliminou (reduced tier: 8 vazamentos → 0).
**Fix final (whisper-token guard):** persiste audible_speech escopado por quem
ouviu, EXCETO se o conteúdo entregaria um token de whisper a um ouvinte fora do
sussurro (reusa `hidden_whisper_tokens`/`redact_tokens`). A revelação do alias
(nunca sussurrada, cânon do Diretor) persiste; a re-narração de whisper
(LUMEN-17) é pulada. **Run 3 confirmou: reduced tier LIMPO (0 violações — a
regressão de vazamento que EU introduzi está fechada).**
**Relógio do xfail = VARIANCE-BOUND:** 5 runs, cada um com slips estocásticos
diferentes (LUMEN leaks → WT-10 → WT-02 Kansas → WT-12 ribbon → GLOBAL-anonymous-
pair → WT-09 modo 2). As "3 runs limpas consecutivas" NÃO são alcançáveis por
esforço/budget — é ruído de LLM de 1 turno entre MUITAS famílias de cânon, não
regressão. Fixar só o WT-09 não zera o relógio (a sopa estocástica persiste). O
fix de persistência é strictly better (resolve modo 1, zero regressão de leak).
Modo 2 (Diretor difere a nomeação) pediria mudança no prompt do Diretor (nudge
testado: naming 1/5→4/5 mas frequentemente escopado; blast radius exige validar
no oráculo) — baixo valor marginal pro relógio já que não zera de todo jeito.
Artefatos: `plans/artifacts/wt09-audible-speech-fix/`, `.../xfailed3-leaksafe/`,
`.../xfailed3-whispertoken/` (reduced tier limpo). Falso positivo do allowlist (`perspective:memory:*` novo) corrigido no oráculo. Artefatos: `plans/artifacts/xfailed3-post-39-41/` (sessões das 2 tiers + violations.txt) |

> **Convenção (2026-07-17):** só migra pra `.plan/closed/` a tarefa fechada COM CONFIANÇA. Tarefa entregue com ressalvas / sem fecho confiante fica em `.plan/tasks/` com as ressalvas no topo.

## 🌙 FILA DA MADRUGADA (2026-07-18) — ✅ CONCLUÍDA INTEGRALMENTE (2026-07-19)

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
| F | Fillers | ✅ TODOS ENTREGUES: MCP curl (tools/, 17 testes); medição offline da guarda (26, ver lane); fakes antigos do test_integration modernizados (22 payloads pré-split limpos, 627 verdes) |

Pendências que precisam do dono: smoke tests da 19 (roteiro em
`.plan/para-o-dono/19-smoke-tests.md`) — **única aberta**. Desenho da 33b:
✅ ACEITO (2026-07-19 noite) — 8/8 decisões fechadas; #4 (confidencialidade)
resolvida por curl em janela real (mantém só-Diretor; ver
`.plan/para-o-dono/33b-desenho-watcher.md` e `plans/artifacts/watcher-decision4/`),
as 2 decisões da bateria = SIM/SIM. **Implementação 33b (2026-07-20, madrugada
autônoma): as 3 peças construídas, curl-validadas e commitadas** —
[1] auditor de delta (`src/watcher.py`, 2 janelas reais, gate bidirecional:
imobilidade none 4/4 + evento real moved 4/4), [2] ladder de recuperação
(código puro, escalada congelada, 9 testes), [3] intervenção causal (9/9
grounded por juiz cego). **Integração (wiring) ENTREGUE (2026-07-20, autorizada
pelo dono):** fiado no runner atrás de `watcher_enabled` OFF (schema 10→11;
auditoria pós-turno acumula `quiet_turns`; ladder pré-turno → disrupção causal
no canal `narrator_hint`; relógio da 40 = degrau execute-transition, watcher é o
fallback abaixo; teste de integração mockado). Follow-ups: derivar flags dos
degraus dormentes (adjudicate/reincorporate), pré-empção do convite de skip da
40, bateria A/B/C com watcher ON (fica com o dono). Artefatos:
`plans/artifacts/watcher-delta-audit/` e
`plans/artifacts/watcher-causal-intervention/`. Purge do refs/original:
✅ FEITO (verificado 2026-07-19 — `refs/original` vazio, reflog expirado; git
local e GitHub limpos).


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
  `.plan/reference/narrator-hint-study-part2-handoff.md`. Próximo passo (a decidir
  com o dono): harness experimental atrás de flag, fora do turno canônico.
- ~~Fakes antigos de `tests/test_integration.py`~~ — FEITO 2026-07-19 (22
  payloads pré-split modernizados pro contrato atual; suíte 627)

## 📌 Decisões diferidas (com dono)

- K-falantes core vs plugin → fechamento da 36
- ~~Undo através de rajada autônoma~~ → DECIDIDA na 37: undo = 1 beat (cada beat é um turno commitado)
- Roteiro nunca chega a personagem/prosa (spoilers) → 38 (regra já escrita)
- Matriz multi-modelo → EXCLUÍDA (decisão do usuário, 2026-07-15)
