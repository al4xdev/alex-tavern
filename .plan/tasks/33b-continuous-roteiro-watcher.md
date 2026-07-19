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
`docs/cases/11-roteiro-drive-scene-stagnation-2026-07-17.md`) provou:
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

Ver `docs/cases/12-scene-state-transition-theory-2026-07-17.md`. A 33b
não é só um "watcher que reescreve o roteiro" — é um controlador de TRANSIÇÃO DE
ESTADO com: estado autoritativo de cena (dramatic_question, threads, pressures),
progresso por DELTA MATERIAL (não cobertura lexical), ladder de recuperação
(executar transição prometida → adjudicar tentativa → permitir silêncio →
reincorporar thread → só então disromper), contrato causal de intervenção
(source_thread/target_state/event_now/expected_delta/refractory_turns) e cobertura
de atores representativa (silêncio permitido). Consome o relógio narrativo da
**Task 40** (o tempo sempre anda). Experimento A/B/C no doc §7.

## Exploração curl EXECUTADA (2026-07-19, madrugada) — conceito validado

Método AGENTS.md §6, janelas REAIS (sorteio travado ccb521ab; incêndio e7760040).

### A) Detector de DELTA MATERIAL (auditoria por turno, call pequena)
- Janela travada: T7=[] e T8=[] com justificativas precisas ("continua a reação
  à explosão já ocorrida"; "apenas detalha o estado pós-explosão") — detectou a
  IMOBILIDADE SEMÂNTICA que âncoras lexicais não veem. T5/T6 corretamente
  creditados (marcas de espera; explosão da lâmpada).
- Janela de ação: deltas certos em 3/4 turnos com categorias corretas
  (decision_taken, attempt_got_consequence, threat_advanced); o turno inerte
  do Rui corretamente zerado.
=> O sinal de progresso do controlador FUNCIONA como classificador por turno.

### B) Contrato de intervenção CAUSAL (no ponto travado)
- 3/3 extraíram threads abertos REAIS com evidência citada por turno (carta
  lacrada, som metálico dos arcos, explosão/fumaça, ordem do pátio).
- 3/3 intervenções cresceram de um thread EXISTENTE (arco range e se abre;
  porta se escancara no caminho ao pátio; silhueta se materializa DA fumaça) —
  zero thread desconexo. refractory_turns=3 consistente.
=> O formato do contrato força causalidade — confirma a previsão do doc §7
(C bate B em coerência) no nível da geração; falta o A/B/C completo (usuário).

### Custo/latência estimados p/ produção
1 call pequena (~400 tokens out) por turno auditado (ou a cada K turnos) + 1
call de intervenção só quando a ladder chega ao degrau 5. Compatível com o
toggle OFF por padrão.

### Próximo (com o usuário)
Bateria A/B/C (doc §7) + integração: detector como gatilho da ladder
(consumindo o relógio da 40 — increment 1 já entregue), intervenção causal no
degrau final.


## Bateria A/B/C EXECUTADA (2026-07-19, autônoma — autorizada pelo dono)

Harness `tools/acceptance/watcher_abc.py`; artigo completo:
`docs/cases/13-clock-causal-watcher-battery-2026-07-19.md`. Resumo honesto:

- **C (relógio+causal): melhor taxa de delta material (6/10, T4-T9 todos
  produtivos) com o watcher NUNCA disparando** — deadlines de ato + eventos
  do roteiro sustentaram a cena sozinhos. O watcher é a camada de fallback, e
  neste run o fallback não foi necessário.
- **B (template arbitrário): re-estagnou no meio (T4/T6/T7) e a ladder
  re-disparou** — a assinatura de re-intervenção que o doc §12 previu.
- **Surpresa honesta: o crítico cego pontuou B mais alto** (drama com agência
  ganha licença narrativa do leitor). A previsão "C vence em coerência" NÃO
  se confirmou no score.
- **Mas TODA incoerência apontada pelo crítico (2 eventos em 6 críticas) veio
  da família arbitrária — seeds do DRIVE sem âncora** (vento indoor no A,
  cristal sem causa no C). Nenhum evento do relógio/roteiro/contrato causal
  foi apontado.

Decisões que isso abre (dono): (1) integrar o watcher atrás de flag como
upgrade semântico do drive; (2) o gerador de seeds do drive — a fonte de toda
incoerência apontada — adotar o contrato causal.
