# Task 43 — Substrato de disposição dos personagens (estado que deriva)

**Status:** 🟡 ABERTA (roadmap novo, 2026-07-20) — track independente, não bloqueia
nem depende das tasks abertas (26/26b, 16, 38, xfailed3). Fase 0 (definição +
artigo) concluída; Fases 1–5 abertas.
**Artigo da fronteira:** `docs/cases/15-character-disposition-substrate-2026-07-20.md`.
**Origem:** conversa de desenho com o dono (2026-07-20), a partir de uma sugestão
externa (o "sistema de memória/fé" citado de Sword Art Online) e da nota
`.plan/backlog/player-persona-public-vs-real.md`.

## Ideia

Personagens deixam de ser **ficha estática** (personalidade + `current_mood` texto
livre) e ganham **disposições que DERIVAM ao longo da história**: confiança que
erode, afeto que vira, compostura que quebra e volta devagar. Semeado na criação
do personagem (no preset), mensurável e persistido, e — o ponto — legível na prosa.

## A disciplina central (o que torna isto embarcável)

**O escalar 0–1 é do CÓDIGO; só a BANDA qualitativa chega ao modelo.** Resolve a
contradição aparente ("o modelo não honra um campo de credence numérico" — verdade)
com "queremos valores 0–1" (também verdade): número e modelo vivem em lados opostos
de uma parede.
- Escalar (0–1): determinístico, persistido, testável **sem gastar modelo**. Dá o
  lado mensurável (seed no preset, deriva, limiares, antes/depois).
- Banda qualitativa: é o que o agente-personagem **lê** (`"desconfiado"`, nunca
  `0.72`) e o delta direcional é o que ele **escreve** ("esse turno quebrou minha
  confiança"); o **código** integra o delta no escalar.
- É a MESMA divisão de trabalho já provada no auditor de delta do watcher (33b /
  artigo Nº 13): modelo classifica evento qualitativo, código faz a aritmética.

## A navalha anti-complexidade (aceite de cada eixo)

> **Um eixo só ganha lugar se um leitor CEGO, olhando só a fala/ação, souber dizer
> em que ponta do eixo o personagem está.** Se não muda comportamento observável,
> é decoração — corta.

Isto é teste curl (crítico cego adivinha a banda pela prosa; se não bate o acaso, o
eixo morre). É como "complexidade com razão" vira falsificável, não aspiração.

## Decisões de desenho CONGELADAS (aceite do dono, 2026-07-20)

1. **Parede escalar-código / banda-modelo** — firme (a fundação; §"disciplina").
2. **Conjunto de 3 eixos** de partida:
   - **Confiança** (generaliza a "fé") — por-par — age na palavra do outro, baixa
     a guarda, compartilha segredo.
   - **Afeto** (calor ↔ hostilidade) — por-par — tom, disposição a ajudar, agressão.
   - **Compostura** (calmo ↔ abalado) — global — ritmo da fala, impulsividade; é
     literalmente "o tom da fala". Disciplina um slice do `current_mood` já existente.
3. **4º eixo (Ousadia: cauteloso ↔ temerário, global) NÃO entra por desenho — é
   decidido por CURL** (Fase 3.5). Desenha-se pra 3; o 4º prova que se paga (muda
   comportamento que um cego nomeia, acima dos 3) ou fica de fora. — aceite do dono.
4. **Escopo por-par desde a Fase 1** (aceite do dono): Confiança/Afeto já nascem
   dyadic (`A→B`), mas **materializados PREGUIÇOSAMENTE** — entrada só onde há
   divergência viva. Compostura é global. Essa distinção mata a explosão O(N²).
5. **Preset semeia, história deriva, gravidade volta.** Cada eixo carrega
   `baseline` (semeado no preset), `valor` (movido por delta) e `gravidade` (relaxa
   pro baseline em turnos calmos).
6. **Reusar a taxonomia de delta do watcher** (`relationship_changed` já existe)
   pra mover o escalar — reaproveitar máquina provada, não construir subsistema.

## Fronteiras (o que isto NÃO é)

- NÃO é um novo store de memória. A "fé" é um **carimbo de crença** em cima de
  percepção/memória já existentes, não um terceiro banco. (Ver artigo Nº 15 §2 e o
  turno de desenho: "matar a palavra 'três memórias'".)
- NÃO substitui os ledgers de perspectiva (29.2). Isto governa DISPOSIÇÃO que deriva;
  os ledgers governam PERCEPÇÃO/conhecimento subjetivo. Complementares.
- Construído pra correção de longo prazo, validado empiricamente — não otimizado pra
  custo por chamada agora (postura do dono: modelo de fronteira barato = gastar em
  validação, desenhar pro arco).

## Roadmap (cada fase barata e testável isolada; gate curl-first onde há modelo)

### Fase 0 — Definição + artigo da fronteira — ✅ CONCLUÍDA (2026-07-20)
`docs/cases/15-character-disposition-substrate-2026-07-20.md`. Eixos, a parede
escalar/banda, a navalha, o unificador (persona pública/real), as reivindicações
falsificáveis (§9). Esta task é o roadmap-companheiro do artigo.

### Fase 1 — O substrato (PURO CÓDIGO, zero modelo) — ⬜ ABERTA
Modelo de dados por personagem: `{axis: (baseline, value, gravity)}` para os eixos
globais + `{(observer, target): {axis: (baseline, value, gravity)}}` dyadic-lazy.
Seed a partir do preset. Deriva/gravidade determinística por turno/tick (consome o
relógio da 40). Projeção `escalar → banda` (função pura). Bump de schema. Testável
de graça (aritmética + projeção).
- **Aceite:** seed do preset popula baselines; N turnos calmos relaxam o valor pro
  baseline dentro de uma tolerância; projeção mapeia faixas → bandas estáveis;
  dyadic materializa preguiçosamente (sem entrada = sem custo); ruff+mypy limpos;
  unit tests offline. **Nenhuma chamada de modelo nesta fase.**

### Fase 2 — Projeção na voz (o modelo LÊ a banda) — 🟢 GATE CUMPRIDO (2/3 SHIP)
Injeta a banda no prompt do agente-personagem (`_build_disposition_note` →
"CURRENT PRIVATE STATE"; o número NUNCA entra). 3 testes de unidade (banda aparece,
escalar não vaza, dyad ocioso silencioso). Suíte 686 verde.
- **Gate curl-first EXECUTADO** (deepseek real, crítico cego, regra pré-registrada
  ≥8/10 por eixo + ≥2/3 pra ship; limiar nunca movido; v1/v2/v3 todos registrados).
  Evidência: `plans/artifacts/disposition-voice/VALIDATION.md`.
  - **Warmth: PASS 3× (8/9/9)** — banda honrada e legível por cego.
  - **Trust: PASS 10/10** (v3, juiz 5/5 equilibrado) quando o estímulo dá espaço aos
    dois polos ("guarde este embrulho até amanhã").
  - **Composure: FAIL nas 3 (5/5/7)** — não separa no nível de UMA fala. Diagnóstico:
    é "clima" interno que colore a ENTREGA; uma linha de um profissional competente
    lê como composto independente da banda, e qualquer estímulo forte o bastante pra
    abalar satura o polo calmo. Parece stance de CENA/prosódia, não sinal de fala
    única. **Decisão do dono pendente:** rebaixar / tratar em nível de cena / cortar
    (a navalha pode estar rejeitando composure no nível de utterance).
- **Aceite:** ✅ banda legível por cego em 2/3 eixos (gate); ✅ número nunca no prompt
  (teste + scan). RESSALVA aberta: composure (ver decisão do dono).

### Fase 3 — A malha de retorno (modelo ESCREVE delta, código integra) — 🟢 GATE CUMPRIDO (4/5) + FIADO
Auditor de appraisal blind/Director-side (`appraise_relationships` em
`src/disposition.py`): lê o bloco do último turno e emite deltas DIRECIONAIS por par
(`observer→target`, axis trust|warmth, direction up|down, intensity slight|strong).
Código integra (`integrate_appraisal` → `ensure_dyad` + `nudge`), depois 1 passo de
gravidade. Escopo trust+warmth (composure estacionado). Fiado em
`Runner._apply_disposition_feedback` atrás de `disposition_feedback_enabled` (OFF por
padrão). 10 testes de unidade + 2 de integração; suíte 696 verde.
- **Gate curl-first EXECUTADO** (deepseek real, 5 cenários × 4 runs, regra
  pré-registrada ≥3/4 por cenário + ≥4/5 pra ship; v1/v2 registrados).
  Evidência: `plans/artifacts/disposition-appraisal/VALIDATION.md`.
  - **Direção + par confiáveis** (sempre C1→C2, sinal certo). **Falso-positivo
    zero** (neutral silencioso 4/4 nas duas rodadas).
  - **Regra de atribuição** ("quando B age sobre A, é A→B que muda") consertou o
    caso-assinatura: **betrayal 2/4→4/4**.
  - **Soft spot honesto:** o split trust/warmth é mole pra atos que movem os dois
    (rescue lê como warmth, não trust) — não prejudica: ambos empurram o dyad no
    mesmo sinal e mostram a mesma banda mais quente. Shipped = prompt v2.
- **Aceite:** ✅ delta rastreia provocação (4/5) + gravidade restaura (unit) + teste
  de integração mockado (provoca→escalar move→banda vira→OFF fica estático).

### Fase 3.5 — Experimento do 4º eixo (Ousadia) — ⬜ ABERTA
Decisão #3 por curl, não por hipótese. A banda de Ousadia muda comportamento que
um cego nomeia, ACIMA dos 3? Regra pré-registrada antes de rodar. Entra ou fica
fora por evidência.

### Fase 4 — Unificação com persona pública/real — ⬜ ABERTA
Realiza `player-persona-public-vs-real.md`: persona pública = **prior padrão**;
entrada dyadic = **posterior** de um observador que desvia do prior; valor do eixo
= força do desvio. Uma contradição testemunhada revisa o posterior (caminho de
revisão de ledger 29.2/39).
- **Aceite:** herda os aceites da nota de persona (prior público semeia; posterior
  dyadic desvia; testemunho revisa) expressos sobre o substrato.

### Fase 5 — Artigo de registro (COM medição) — ⬜ ABERTA
O artigo de evidência (não o de definição): o que o modelo honrou, onde foi
variance-bound (honesto, como o relógio do roteiro), custo/latência real. Fecha a
task com evidência ou com negativo documentado por método.

## Aceite GERAL (rascunho — congela ao iniciar cada fase)
- [ ] Substrato escalar por-personagem (global) + dyadic-lazy, semeado no preset,
  com deriva/gravidade determinística e projeção escalar→banda. (F1)
- [ ] A banda é legível na prosa por crítico cego em ≥2/3 eixos. (F2, navalha)
- [ ] Delta direcional rastreia provocação e a gravidade restaura. (F3)
- [ ] O número (0–1) nunca aparece em prompt de personagem/prosa (scan NONE). (F1/F2)
- [ ] 4º eixo decidido por curl (entra/fora com regra pré-registrada). (F3.5)
- [ ] Persona pública=prior / dyadic=posterior realizada; testemunho revisa. (F4)
- [ ] Artigo de evidência (Nº do caso a seguir) com medição e ressalvas. (F5)

## Invariante de projeto (a razão da complexidade)
Cada eixo/feature adicionado passa pela navalha (cego nomeia a ponta pela prosa) OU
é cortado. Complexidade sem observabilidade é decoração. É o que separa este
substrato de um "vetor de personalidade" que incha até ninguém medir.
