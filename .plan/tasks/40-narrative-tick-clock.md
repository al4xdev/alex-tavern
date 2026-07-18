# Task 40 — Relógio narrativo (sistema de ticks): o tempo sempre anda

**Origem:** ideia do usuário (2026-07-17), mecanização do "relógio do mundo" do
doc `docs/cases/scene-state-transition-and-human-stagnation-2026-07-17.md`.
**Relação:** primitivo fundacional consumido por Task 33 (drive) e Task 33b
(controlador de transição de cena). **Opt-in a definir.**

## O problema que resolve

A LLM está "parada no tempo": a história é estática, o modelo não tem relógio e
não percebe que *continuar* deixou de ser *progredir*. Os dois relógios
(conversa vs mundo) desacoplam e a cena procedural estagna (portais/sorteio).

> A LLM não pode parar o tempo se o tempo não pertence à LLM.

## A ideia

Um **tick narrativo monotônico, dono do CÓDIGO, que sempre avança** (nunca 0,
nunca pra trás). O roteiro, quando gerado, marca **cada ato (e opcionalmente cada
beat) com um span/deadline de tick** e o `world_event` que dispara no deadline.
Quando o clock cruza o deadline de um ato, o código **força** a transição do
mundo — enact do `world_event` + avanço do ato — independentemente do que a
conversa fez. A LLM nunca segura o relógio.

Isso é a autoridade determinística que o doc defende: **o código exige a
transição causal concreta** na hora certa; um GM humano não explode os portões,
ele simplesmente realiza o sorteio quando o sino toca.

## Perguntas de design a congelar na task

- **Unidade de tempo.** Tick abstrato ≥1 por turno commitado (base = candidato:
  reusar/derivar de `turn_number`, que já é monotônico)? Ou avanço variável, que
  permite *compressão de tempo* (o GM humano: "depois de alguns minutos, o sino
  toca" — um turno consome muitos ticks)? Tempo in-fiction (minutos/horas) pode
  ser anotação derivada; a ENFORCEMENT é no tick monotônico.
- **Anotação do roteiro.** Cada ato declara `start_tick` + `duration_ticks`
  (ou `deadline_tick`) + `world_event_on_deadline` (amarra ao "beat de
  procedimento" §6.5 do doc: `world_owner`, `next_world_event`). Beats idem,
  opcional.
- **Enforcement.** O runner avança o clock a cada turno commitado; ao cruzar um
  deadline de ato, force-advance + enact do `world_event` (mesmo mecanismo que
  quebrou o loop 3/3 no curl da Task 38, mas AGENDADO pelo relógio, não reativo a
  stall). Substitui/robustece o `budget_turns` da 38 (soft) por um deadline
  duro, e o `turns_since_injected_event` da 33 por um sinal derivado do clock.
- **Confidencialidade.** O schedule (deadlines + world_events futuros) chega SÓ
  ao Diretor (como o roteiro; nunca personagem/prosa — contém spoilers). Scan.
- **Liberdade do jogador.** O tempo passar é FATO DO MUNDO, não ditar a vontade
  do jogador — coerente com o contrato de ação livre (o Diretor tem autoridade
  sobre a resposta do mundo; devolve controle). Uma tentativa consequente do
  jogador ainda é adjudicada; o relógio só garante que o mundo não congela.
- **Compressão/skip.** O clock deve suportar um "time skip" (avançar muitos ticks
  num turno) pra implementar o modo-sumário humano (doc §4.2) — sair do modo
  dramático, avançar o relógio, voltar ao próximo momento de decisão.

## Começo (método): curl-replay primeiro

Antes de qualquer código, validar o conceito (AGENTS.md §6): pegar um payload
real de Diretor num turno procedural travado e anotar "AGORA é o tick N; o mundo
avançou para <world_event do deadline>". Medir se o Diretor encena a transição do
mundo (como o beat concreto disruptivo fez 3/3) vs instrução abstrata (0/3).
Só então desenhar o schema de tick + a anotação de ato + o enforcement.

## Aceite (rascunho, congelar ao começar)

- [ ] Clock monotônico dono do código, sempre +≥1 por turno; nunca regride;
  undo/fork/restore preservam o clock exatamente.
- [ ] Roteiro anota cada ato com deadline de tick + world_event; confidencial ao
  Diretor (scan NONE).
- [ ] No deadline, o código FORÇA o world_event/avanço de ato — cena procedural
  (portais/sorteio) alcança o próximo evento do mundo pelo relógio, SEM depender
  de disrupção arbitrária.
- [ ] Suporta time-skip (compressão) num turno.
- [ ] A/B/C (do doc §7): A livre / B disrupção arbitrária / C relógio+consequência
  causal — medir delta material, threads, re-intervenção, coerência causal cega.
  Previsão: C vence drive sustentado + coerência.
