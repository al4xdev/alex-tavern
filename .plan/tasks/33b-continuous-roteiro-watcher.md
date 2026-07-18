# Task 33b — Continuous roteiro watcher (opt-in sub-model)

**Quando:** DEPOIS de todas as pendentes (39, xfail §15). Extensão da Task 33
(drive layer, fechada) e da Task 38 (roteiro, fechada, opt-in). A ideia inicial
do usuário, agora com base empírica.

## Ideia

Um **sub-modelo "watcher" que roda o tempo todo**: a cada turno ele olha a cena,
**detecta mudanças/estagnação** e **reescreve o roteiro** (o próximo beat) em
tempo real. Em vez do replan ser disparado por sinais determinísticos de código
(o que a Task 38 faz), um agente contínuo vigia e reage.

**Toggle obrigatório, OFF por padrão** — custo de latência: uma chamada extra por
turno. É opcional exatamente por isso.

## Por que faz sentido (evidência da Task 38)

A investigação da Task 38 (relatório:
`docs/cases/roteiro-drive-and-scene-stagnation-2026-07-17.md`) provou:
- Estagnação de cena é o problema-raiz; o lever é o Diretor encenar um **evento
  concreto novo** (um beat disruptivo quebrou o loop 3/3 no curl).
- O replan determinístico da Task 38 é reativo e por vezes tardio (o teto força
  virada a cada 3 turnos, mas a detecção é grosseira).

Um watcher contínuo poderia detectar a estagnação mais cedo/melhor e reescrever
o roteiro pró-ativamente — ao custo de latência.

Relação com o gatilho de estagnação já roteado pro drive layer (Task 33, nota de
extensão 2026-07-17): 33b é a variante "sub-modelo olhando sempre", o gatilho no
drive layer é a variante "hazard determinístico". 33b explora se o agente
contínuo bate o determinístico.

## Começo/critério: EXPLORAR VIA CURL PRIMEIRO (antes de construir)

Método curl-replay do `AGENTS.md` §6. Validar o CONCEITO antes de qualquer código:
1. Pegar payloads reais de turnos de cena real (`debug.jsonl` das sessões em
   `plans/artifacts/roteiro-ab*/`).
2. Montar um prompt de "watcher": recebe o estado da cena + histórico recente,
   retorna (a) detectou mudança/estagnação? (b) o novo beat/roteiro.
3. Rodar via curl em sequências de turnos: **o disparo-sempre do detector-que-
   reescreve realmente funciona?** Mede: ele detecta estagnação quando existe?
   escreve um beat disruptivo útil (como o que quebrou 3/3)? gera ruído quando a
   cena está saudável (falso positivo → reescrita desnecessária)?
4. Só se o conceito se sustentar no curl → desenhar o agente + o toggle + o custo
   de latência medido, e comparar (A/B) watcher-ON vs replan-determinístico vs
   OFF, com o crítico cego.

## Escopo

- Toggle de config (ex.: `roteiro_watcher_enabled`, default false).
- Um agente watcher (Director-side, recebe o roteiro; confidencialidade da Task
  38: nunca chega a personagem/prosa).
- Medir latência adicional por turno e reportar (custo do opt-in).
- NÃO substitui o replan determinístico da Task 38; é uma camada alternativa
  sob toggle.

## Aceite (rascunho, congelar na task quando começar)
- [ ] Exploração curl documentada: o watcher detecta estagnação e escreve beat
  disruptivo útil sem ruído excessivo em cena saudável.
- [ ] Toggle OFF por padrão; latência adicional medida e reportada.
- [ ] A/B crítico cego: watcher-ON vs determinístico vs OFF em cena procedural
  (portais) e de ação (estalagem).
- [ ] Confidencialidade do roteiro preservada (scan NONE).

## Reenquadramento (2026-07-17): controlador de transição de estado de cena

Ver `docs/cases/scene-state-transition-and-human-stagnation-2026-07-17.md`. A 33b
não é só um "watcher que reescreve o roteiro" — é um controlador de TRANSIÇÃO DE
ESTADO com: estado autoritativo de cena (dramatic_question, threads, pressures),
progresso por DELTA MATERIAL (não cobertura lexical), ladder de recuperação
(executar transição prometida → adjudicar tentativa → permitir silêncio →
reincorporar thread → só então disromper), contrato causal de intervenção
(source_thread/target_state/event_now/expected_delta/refractory_turns) e cobertura
de atores representativa (silêncio permitido). Consome o relógio narrativo da
**Task 40** (o tempo sempre anda). Experimento A/B/C no doc §7.
