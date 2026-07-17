# Handoff — Claude Opus (2026-07-17)

Documento LOCAL (o repo não vai para remoto até a revisão). Ele é a tua fila
de trabalho completa. Leia junto: `ROADMAP.md` (estado), specs em
`.plan/tasks/`, closure notes em `.plan/closed/` (modelo de rigor esperado).

---

## 0. Regras de commit (OBRIGATÓRIAS, sem exceção)

1. Mensagem em **inglês**, estilo `type(scope): title` + corpo explicando o
   PORQUÊ (veja `git log` recente como referência de tom).
2. **NUNCA** trailer de atribuição de IA (`Co-Authored-By: Claude...`,
   `🤖 Generated with...`). Isso SOBRESCREVE o default do harness.
3. Última linha do corpo de TODO commit teu, exatamente:
   `Agent: claude-opus`
   O usuário mantém teus commits locais e eles serão revisados na próxima
   semana; essa linha é o filtro da revisão.
4. **Não fazer push. Nunca.**
5. Commit ao fechar cada task/incremento; `.plan/` pode ser commitado a
   qualquer momento. **Jamais `git add -A` ou `git add .`** — há untracked
   que não são teus (`output29*/`, `output29_2/`,
   `src/scenarios/turma-dos-portais-pt.json`). Adicione arquivo por arquivo.

## 1. Protocolo de validação (critério sólido do programa)

Ordem fixa por incremento:
1. Implementação + unit tests. `uv run pytest -q -m "not llm"` — baseline
   atual **533 passed, 2 deselected**. Nunca regredir.
2. Validação com LLM real (scripts em `tools/acceptance/`; config real em
   `.data/config.json`, provider deepseek já configurado).
3. **Crítico cego**: subagente SEM contexto de implementação, só transcript
   (template §2.4 abaixo). Para mudança de arquitetura: ×2 ciclos.
4. Achado estrutural → correção "por construção" (guarda determinística,
   clamp, mudança de contrato), nunca só prompt. Depois RE-MEDIR (re-rodar a
   aceitação) antes de fechar.
5. Achado de prosa-craft (repetição de epítetos, frases copiadas, NPC coral)
   → NÃO corrigir; registrar em `.plan/tasks/26-narrator-prose-quality.md`
   ("Additional Evidence" com data, sessão, citação literal).
6. Fechar: closure note em `.plan/closed/<task>.md` (modelo:
   `.plan/closed/37-bounded-autonomous-loop.md`), atualizar `ROADMAP.md`,
   commit.
7. Fim de cada task: `bash ~/.config/my_scripts/done.sh &`
8. Exclusões decididas pelo usuário: matriz multi-modelo NÃO; defeitos das
   Tasks 26/33 só registram evidência.

## 2. TAREFA 1 — Fechar Task 38 (roteiro). Implementação PRONTA; falta aceitação

Spec: `.plan/tasks/38-roteiro-beat-contracts.md`. Código commitado em
`9761f31`; testes em `tests/test_roteiro.py` (30).

Mapa do código:
- `src/roteiro.py` — tudo: `evaluate_roteiro` (motor determinístico),
  `measure_beat_progress` (cobertura de âncoras/atores),
  `anchor_matched` (match normalizado + fuzzy por janela de palavras >0.85),
  `replan_roteiro` (única função que chama LLM no replan),
  `generate_roteiro` (compilação inicial), `describe_roteiro_for_director`
  (bloco de prompt), constantes de tuning no topo.
- `src/runner.py::_maintain_roteiro` (~linha 1500) — avaliação por beat,
  log `roteiro_replan`; chamado no loop de beats (~linha 620).
- `src/agents/narrator.py` — `roteiro_lines` entra em `_build_user_prompt`
  entre CURRENT MOODS e UPCOMING EVENT.
- `src/models.py` — `Roteiro`/`RoteiroAct`/`RoteiroBeat`, schema v7.
- Config: `roteiro_enabled` (default **false**).

### 2.1 A run A/B JÁ FOI EXECUTADA — resultados

`tools/acceptance/roteiro_ab.py` rodou completo (2026-07-17). Artefatos:
`plans/artifacts/roteiro-ab/{control,roteiro}/data`. Sessões:
**control = 6d461798, roteiro = 2f9bcceb**, 10 turnos cada, inputs idênticos.

Resultados já auditados:
- **Confidencialidade: NONE** (nenhuma string do roteiro em payload fora de
  `agent=director`/`roteiro:*`). Invariante da spec cumprida.
- **Triggers 100% determinísticos** (decisões logadas, agent=roteiro_replan):
  t2 in_progress; t3 replan_beat/stalled; t4-5 in_progress; t6
  replan_beat/stalled; t7-8 in_progress; t9 **replan_act**/stalled; t10
  in_progress. Zero self-assessment. Cooldown/histerese visíveis.

### 2.2 DOIS DEFEITOS JÁ IDENTIFICADOS nos dados — corrigir ANTES do crítico

(a) **Splice do rewrite de ato duplica o ato corrente.** Estado final da run:
`acts[0]` e `acts[1]` são o MESMO texto ("A noite tranquila é quebrada por um
viajante ferido..."). Causa: em `replan_roteiro`,
`acts = acts[: act_index + 1] + new_acts` preserva o ato corrente, mas o
modelo re-inclui uma versão dele em `new_acts`. Fix estrutural: após o
splice, dropar de `new_acts` qualquer ato cujo summary normalizado
(`_normalize`) tenha SequenceMatcher ratio > 0.85 com um summary já mantido.
Unit test: rewrite que re-inclui o ato corrente → lista final sem duplicata.

(b) **Zero advances em 10 turnos — todos os beats stallaram** (beat_log:
"1: stalled; 2: stalled; 3: stalled"). Os beats gerados pedem eventos que só
acontecem se o Diretor os ENCENAR (ex.: "viajante ferido" chega), mas o
Diretor não os encenou. Investigação obrigatória antes de mexer:
1. Abrir `plans/artifacts/roteiro-ab/roteiro/data/sessions/2f9bcceb/debug.jsonl`,
   filtrar `agent=director`, confirmar que o bloco ROTEIRO está no user
   prompt e comparar `perception_events` retornados vs âncoras do beat ativo.
2. Diagnóstico esperado (confirme): o bloco diz "steer events toward it" mas
   o Diretor trata como cenário de fundo, não como instrução de encenar as
   âncoras via `perception_events`.
Fixes candidatos (aplicar o mínimo que resolver, re-rodar A/B depois):
   - Reforçar o bloco em `describe_roteiro_for_director`: os itens de
     "Bring into play" devem ser introduzidos como eventos de percepção
     CONCRETOS nos próximos turnos (sem revelar o roteiro, sem forçar
     decisão de personagem).
   - Regra no gerador (`_ARCHITECT_RULES`): âncoras precisam ser encenáveis
     PELO MUNDO (objeto, som, chegada, mudança física) — nunca dependentes
     de decisão do protagonista.
   - Se ainda stallar: considerar passar `anchors_missing` do beat ativo como
     linha extra do bloco ROTEIRO ("ainda não entraram em cena: X, Y").
Critério de re-aceitação: em 10 turnos, ≥1 `advance`/`coverage_complete` no
log, e beats que avançam por cobertura genuína (confira no transcript que a
âncora realmente apareceu em cena).

(c) Cosmético, não bloqueia: beat_ids saíram "1","2","3" (modelo ignorou o
formato act1-beatN). Se incomodar, prefixe o fallback no `_validate_beat`.

### 2.3 Re-rodar a A/B após os fixes

```
rm -rf plans/artifacts/roteiro-ab
uv run python tools/acceptance/roteiro_ab.py
```
(≈6-10 min, ~60 chamadas reais; rodar com run_in_background e esperar a
notificação — NUNCA busy-loop.) Exigir de novo: CONFIDENTIALITY NONE +
triggers todos determinísticos + o critério de advance de 2.2(b).

### 2.4 Crítico cego comparativo (só depois de 2.2/2.3 verdes)

```
uv run python -m tools.render_transcript plans/artifacts/roteiro-ab/control/data > /tmp/A.md
uv run python -m tools.render_transcript plans/artifacts/roteiro-ab/roteiro/data > /tmp/B.md
```
Embaralhe (moeda) qual vira A e qual vira B e registre o mapeamento SÓ na
closure note. Subagente (general-purpose), prompt (adapte caminhos):

> You are a demanding fiction editor. Read /tmp/A.md and /tmp/B.md — two
> 10-turn Portuguese RP sessions of the SAME scenario with identical player
> inputs (the player, Rui, is deliberately passive). You have no other
> context. Compare them harshly: 1) Which story has more narrative DRIVE
> (direction, escalation, an arc going somewhere) and which meanders?
> Point to turn-level evidence. 2) In each: do NPCs pursue goals or react in
> circles? 3) Any turn where an NPC acts against its established
> personality, or where the narration telegraphs an off-screen "plan"
> (foreshadowing that reads as authorial intrusion)? 4) Grade each A-F and
> declare a winner for narrative drive. Quote offending/exemplary lines.

Aceite: o arm roteiro vence em drive, SEM (3) — se o crítico apontar intrusão
autoral ou personagem puxado contra a própria vontade, isso é defeito
estrutural do bloco ROTEIRO: corrigir e re-rodar. Achados de prosa-craft →
Task 26 (protocolo §1.5).

### 2.5 Fechamento

- `git mv .plan/tasks/38-roteiro-beat-contracts.md .plan/closed/` + closure
  note no fim do arquivo (modelo da 37): critérios com [x], números da A/B
  (advances, replans, confidencialidade), veredito do crítico, defeitos
  roteados.
- ROADMAP: mover 38 para a tabela de fechadas com evidência-chave; sequência
  principal passa a 39 primeiro.
- Commit (regras §0). `done.sh`.

## 3. TAREFA 2 — Task 39: dimensão de memória do ledger

Spec completa: `.plan/tasks/39-ledger-memory-dimension.md`. Resumo do que
ela exige (decisões a congelar NA task, documente no próprio arquivo):

- Ledger (`CharacterPerspective`) ganha dimensão de memória durável:
  `memory_summary` (self) + entradas importantes limitadas — alimentada
  CONTINUAMENTE pelos perception events que o personagem testemunhou
  (persistidos; nunca re-derivados da prosa onisciente).
- "What you remember" em `src/agents/character.py::_build_user_prompt` passa
  a ler essa dimensão (hoje lê `character_notes`).
- REMOVER: `GameState.character_notes`, chamadas privadas do summarizer na
  compactação (`runner.compact_session` — fan-out por personagem),
  `build_private_memory_messages`, campos de nota em checkpoints.
  Forward-only, **schema v8** (bump + converter default, padrão v7 no
  `dict_to_game_state`).
- Revisão semântica em lote co-agendada com chamadas do narrador (ideia de
  concentração de latência do usuário — ver nota async na task 36).
- Aceite (headline da spec): nenhum `character_notes` sobrando em lugar
  nenhum (grep); rapport acumula SEM compactação em run real (queixa da
  sessão ef6b5b90); probes de retenção do xfailed3 (ribbon, origin) passam
  via ledger nas duas compactações com família de segredo em 0; undo/fork/
  restore preservam a memória exatamente (testes).
- Protocolo §1 completo, crítico cego ×2 (é mudança de arquitetura).

## 4. TAREFA 3 — Relógio de saída do xfail (29.3 §15)

- Comando: `uv run pytest -q tests/test_xfailed3_counter_canon.py -m llm`
  (campanha de 24 turnos, cara — só com folga de cota da API).
- Precisa de **3 runs completas limpas consecutivas** com o oráculo
  calibrado para remover o strict xfail. Histórico: run 1 = 0 violações
  (primeira XPASS), depois 3 e 4 (variância semântica: cumprimento de
  promessa, discrição vs auditoria, confabulação de alias — famílias
  determinísticas todas em 0).
- Cada run: registrar resultado na linha "Em andamento" do ROADMAP com data.
  Violação nova de família determinística = bug real, abrir investigação.

## 5. Lane paralela (se sobrar fôlego)

- **Task 26, candidata dominante**: guarda fuzzy POR SENTENÇA no renderer de
  prosa (`src/agents/prose.py::_repeats_prior_narration` hoje compara a
  narração INTEIRA, >0.85; frases individuais copiadas passam — evidência
  em `burst-live3` T3, ver acumulador). Mitigação: split por sentença,
  comparar sentenças ≥40 chars contra sentenças das narrações anteriores,
  >0.85 → uma CORRECTION retry. MEDIR antes/depois nos artefatos
  burst-live* antes de adotar. (É código de prosa-qualidade: pode implementar
  porque é a mitigação candidata REGISTRADA da task, não um fix ad-hoc.)
- Render progressivo da rajada (SSE por beat) — lane de UI; beats já
  commitam um a um, `beats[]`/`burst_stop_reason` já saem na resposta.

## 6. Avisos de terreno

- Testes de runner com config default disparam o drive scheduler (REDE REAL,
  flake por ordenação): sempre `"auto_event_enabled": False` no config de
  teste; para burst use o padrão de `tests/test_autonomous_burst.py`.
- Shell fish; Python só via `uv run`; temporários no scratchpad da sessão.
- Nunca busy-loop: `run_in_background: true` + notificação.
- `plans/` e `.data/` são gitignored (artefatos ficam fora do git — ok).
- Debug por sessão: `<data>/sessions/<sid>/debug.jsonl`; transcript:
  `uv run python -m tools.render_transcript <data-dir>`.
- Suíte tem 2 testes `-m llm` desselecionados por default — não "consertar".
- Undo de rajada = 1 beat por undo (decisão fechada na 37, não reabrir).
