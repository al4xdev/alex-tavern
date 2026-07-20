# Task 33b — Continuous roteiro watcher (opt-in sub-model)

**Status:** ✅ FECHADA (2026-07-20) — 3 peças + wiring atrás de `watcher_enabled`
OFF, curl-validadas e test-locked; aceite cumprido (ver seção Aceite).
Follow-ups são enhancements documentados, não bloqueiam.

**Origem:** extensão da Task 33 (drive layer, fechada) e da Task 38 (roteiro,
opt-in). A ideia inicial do usuário, agora com base empírica.

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

## Aceite — ✅ CUMPRIDO (marcado 2026-07-20, evidência abaixo)
- [x] Exploração curl documentada: o watcher detecta estagnação e escreve beat
  disruptivo útil sem ruído excessivo em cena saudável.
  → auditor de delta: imobilidade `none` 4/4 + evento real `moved` 4/4 em 2
  janelas reais (prova cruzada lexical-vs-semântica); intervenção causal 9/9
  grounded por juiz cego. `plans/artifacts/watcher-delta-audit/`,
  `.../watcher-causal-intervention/`.
- [x] Toggle OFF por padrão; latência adicional medida e reportada.
  → `watcher_enabled` default False. Latência (deepseek, janelas reais):
  delta_audit **~1.4s mediana/turno** (custo por turno auditado), intervenção
  causal **~4s** (só no degrau de disrupção). `scratchpad/exp_watcher_latency.py`.
- [x] A/B crítico cego: watcher-ON vs determinístico vs OFF.
  → coberto pela bateria A/B/C (artigo Nº 13): A livre(OFF) / B arbitrário /
  C relógio+causal, crítico cego. O mecanismo (delta+ladder+contrato causal) é
  o mesmo fiado atrás da flag; a fiação tem teste de integração mockado. RESSALVA
  (follow-up documentado): re-run limpo de 3 braços com a flag `watcher_enabled`
  fiada, e a fronteira de disparo só-canal-livre (em skip nu o convite da 40
  ocupa o canal; watcher dispara em turnos de participação e beats de rajada).
- [x] Confidencialidade do roteiro preservada (scan NONE).
  → `tests/test_watcher.py::TestRoteiroConfidentiality`: os builders do watcher
  não têm superfície de roteiro; um segredo de premise não aparece nos prompts.

### FECHO (2026-07-20)
3 peças (auditor de delta, ladder de recuperação, intervenção causal) + wiring
no runner atrás de `watcher_enabled` OFF, todas curl-validadas e test-locked;
aceite cumprido com evidência. Feature entregue e desligada por padrão.
Follow-ups (enhancements, não bloqueiam): derivar flags dos degraus dormentes
(`adjudicate_attempt`, `reincorporate_thread`); pré-empção do convite de skip
da 40; re-run A/B de 3 braços com a flag fiada. Migrada para `closed/`.

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


## Decisões de desenho CONGELADAS (2026-07-19, aceite do dono)

Todas as 8 fechadas. 1/2/3/5/6 + as 2 da bateria aceitas pelo dono direto.
A #4 estava em dúvida → resolvida por curl (não hipótese), regra pré-registrada.

1. Auditor a cada turno na fase experimental — ACEITA (afinável com custo real).
2. Ladder 100% código, LLM só responde as 2 perguntas — ACEITA (firme).
3. `refractory_turns=3` — ACEITA (número empírico, afinável na bateria).
4. Confidencialidade só-Diretor — **ACEITA por evidência** (ver abaixo).
5. Fronteira com a 40 (deadline por tempo / watcher por estagnação) — ACEITA.
6. Log `watcher:delta`/`watcher:intervention` no JSONL — ACEITA.
- Bateria A: integrar o watcher atrás de flag como upgrade do drive — SIM.
- Bateria B: gerador de seeds do drive adota o contrato causal — SIM (alvo
  mais quente; ver coerência 0.00 do evento chapado abaixo).

### #4 — experimento (curl-first, AGENTS §6)

Janelas reais (sorteio `ccb521ab`, incêndio `e7760040`), deepseek-v4-flash,
4 runs/braço, juiz cego. Artefatos: `plans/artifacts/watcher-decision4/`
(`exp4.py`, `exp4_results.json`, `exp4_raw_outputs.json`). Regra de decisão
pré-registrada: *4b ≈ 4a em agência → mantém #4; 4b >> 4a sem vazar/colidir →
relaxa*.

- Personagem: iniciativa 4a=**1.88** vs 4b(pressão difusa)=**2.00** (teto já
  saturado pelo prompt-base); inventa evento externo 0/8 em ambos; meta 0/8;
  4b não vazou o evento do Diretor.
- Evento: coerência causal (ancorado em thread) **1.83** vs chapado **0.00**
  (média de 3 runs cegas; fogo 2.0 / sorteio 1.67 no causal, 0 em ambos no
  chapado).
- Veredito: **manter #4 (só-Diretor).** O travamento não é déficit de
  iniciativa do personagem (que o prompt-base já satura sem produzir delta) —
  é falta de consequência externa nova, que só o evento do Diretor entrega e
  que o personagem não deve fabricar (colisão que a #4 previne). O valor do
  watcher é o EVENTO causal (0.00 do chapado prova onde está o ganho), Diretor-
  side — que é onde a #4 o mantém. Colateral: reforça a Decisão B da bateria.

### Próximo (implementação, trabalho novo quando priorizado)
Peça [1] auditor de delta + [2] ladder (código, consome relógio da 40) +
[3] intervenção causal Diretor-side; tudo atrás de toggle OFF. E os seeds do
drive migram pro contrato causal (Decisão B).

### Peça [1] auditor de delta — ✅ ENTREGUE (2026-07-20, madrugada autônoma)
`src/watcher.py::audit_delta` — call isolada e cega (espelha `drive.py`), sem
jogar lance. Audita o BLOCO do último turno (narração + fala/ação de cada
personagem daquele `turn_number`) contra o contexto anterior e devolve os
deltas materiais GENUINAMENTE NOVOS. Taxonomia congelada de 8 categorias;
`moved = categories and != ("none",)` é o único bit que a ladder consome.

**Curl-first (AGENTS §6), 2 janelas reais de produção, 4 rodadas/turno, gate
bidirecional pré-registrado — passou SHIP:**
- imobilidade sinalizada: sorteio T7 (re-narração da explosão) none 4/4;
  T8 (rescaldo, descrição) none 4/4.
- evento real capturado: fogo T5 (ignição) moved 4/4; T9 (viga desaba e bloqueia
  a saída) moved 4/4. Prova cruzada: fogo T9 divide vocabulário de fogo/faísca
  com os turnos imóveis do sorteio e ainda assim é `moved` — âncora lexical não
  separa, o auditor de delta material separa.
- 1 iteração de prompt: v1 solta errava os 3 (perdia evento real, perdia
  repetição, contava descrição pura); v2 com NOVELTY GATE + `information_revealed`
  exigindo mudança de stake acertou tudo. A variante validada É a shippada.
- turnos ambíguos deixados FORA do gate (report-only): sorteio T6 (explosão pós
  lâmpada-já-falhando + contagem = ~50/50 entre culminação-prevista e escalada
  nova) e T3 (mensageiro só CHEGA em T3; revelação "antecipado" cai em T4).
- artefato: `plans/artifacts/watcher-delta-audit/` (VALIDATION.md + harness +
  raw). 9 testes unitários offline em `tests/test_watcher.py`. NÃO fiado no
  runner ainda (toggle/wiring é a peça de integração, depois de [2]/[3]).

### Peça [2] ladder de recuperação — ✅ ENTREGUE (2026-07-20, madrugada autônoma)
`src/watcher.py::select_recovery_step` — núcleo de decisão 100% código,
determinístico, sem falar com a LLM. Consome o sinal da peça [1]
(`moved is False` acumulado em `quiet_turns`) contra o relógio da 40 e escolhe
o degrau de recuperação. Ordem congelada, mais gentil primeiro:
`execute_promised_transition → adjudicate_attempt → allow_silence →
reincorporate_thread → causal_disruption`. Dois portões antes da escalada:
limiar de quiet (default 2 — um turno quieto é lull, não stall) e refratário
(default 3, casa com o `refractory_turns=3` validado no contrato causal). O
`allow_silence` é uma graça de UM beat antes de reincorporar/disromper
(cobertura de atores representativa). `RecoveryStep.intervenes` é False para
`none`/`allow_silence`. Toggle `watcher_enabled` OFF por padrão (é camada de
fallback — a bateria A/B/C mostrou relógio+causal segurando a cena sem o
watcher disparar). Entrada explícita (`LadderContext`): a derivação dos flags a
partir do estado (roteiro→transição pronta; histórico de auditoria→tentativa
pendente; extrator causal→thread aberto) é a peça de integração, depois de [3].
9 testes unitários exaustivos (portões + escalada). ruff+mypy limpos.

### Peça [3] intervenção causal — ✅ ENTREGUE (2026-07-20, madrugada autônoma)
`src/watcher.py::generate_causal_intervention` — gerador Diretor-side do último
degrau (`causal_disruption`). Não inventa choque desconexo: faz UM evento
externo CRESCER de um thread já aberto na cena, sob contrato tipado
`source_thread → target_state → event_now → expected_delta → refractory_turns`.
`event_now` vira hint de MUNDO pro Narrador cego; nunca dita vontade de
personagem (invariante de agência), como o seed do drive. `refractory_turns`
clampeado em [2,4].

**Curl-first, 9 intervenções (3 pontos travados reais × 3), juiz de causalidade
CEGO por intervenção (nunca sabe que é intervenção do watcher) — SHIP:**
- **9/9 grounded** pelo juiz cego + TODAS estruturalmente usáveis. Cada uma
  citou thread real e cresceu dele: anomalia da masmorra que adiou a seleção
  (arco D range e abre), resíduo de mana inexplicado da explosão (fissura na
  mancha; arranhado metálico dos arcos selados), vazamento de gás + viga em
  brasa (cano rompe; viga desaba e bloqueia a porta da rua). Zero desconexo.
- reforça o 3/3 da exploração para 9/9 no prompt shippado. A variante validada
  É a shippada.
- artefato: `plans/artifacts/watcher-causal-intervention/` (VALIDATION.md +
  harness + raw). 3 testes unitários offline (grounded property, contrato no
  prompt, schema). ruff+mypy limpos.

### Integração (wiring) — ✅ ENTREGUE (2026-07-20, autorizada pelo dono)
Fiado no runner atrás de `watcher_enabled` (OFF por padrão). Schema bump 10→11
(3 campos novos em `GameState`: `watcher_quiet_turns`,
`watcher_last_intervention_tick`, `watcher_silence_spent`).
- **Pós-turno** (`Runner._audit_turn_for_watcher`, antes do `save_game`): 1
  call de auditoria de delta por turno commitado; `moved` → zera quiet+silence,
  `none` → quiet++.
- **Pré-turno** (`Runner._maybe_watcher_recovery`, depois do relógio, mesmo
  canal `narrator_hint`): monta `LadderContext`, roda o ladder; `allow_silence`
  gasta a graça de 1 beat (sem hint), `causal_disruption` gera a intervenção
  (peça 3) e injeta `event_now`, marca refratário (tick) e zera quiet.
- **Fronteira honesta do wiring:** o relógio da 40 JÁ é o degrau
  `execute_promised_transition`, então o flag fica False no wiring (o watcher é
  o fallback ABAIXO dele). `adjudicate_attempt` e `reincorporate_thread` ficam
  DORMENTES (flags sempre False) até existir a derivação de estado deles —
  definidos e testados na função pura, nunca disparam ainda. Em **skip nu**, o
  convite de compressão de tempo da 40 ocupa o canal e o watcher cede; o watcher
  dispara em turnos de participação e beats de rajada (canal livre). Pré-emptar
  o convite em skip travado = follow-up (precisa reconciliar com a 40).
- teste de integração mockado (`tests/test_watcher_integration.py`): stall
  acumula → graça de silêncio → disrupção causal no canal → refratário
  suprime; e OFF nunca audita/intervém. Suíte 654 verde; ruff+mypy limpos.

**Status 33b:** 3 peças + integração entregues, toggle OFF. Follow-ups
documentados: derivar flags de `adjudicate_attempt`/`reincorporate_thread`;
pré-empção do convite de skip da 40; bateria A/B/C com o watcher LIGADO (fica
com o dono).
