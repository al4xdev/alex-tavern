# 21 — Revisão independente da arquitetura: segunda leitura da bateria de repetição

Registrado 2026-08-02, mesmo dia do archive da bateria. Esta é uma leitura independente
do material de `benchmarks/2026-08-02-6ed5639e049f-*`, do caso 20 e do código. Foi
escrita para atacar as conclusões do caso 20, não para confirmá-las. A sessão 8bd4d0f1
(`base-P1-r2`) foi verificada contra `debug.jsonl` e `state.json` arquivados em
`plans/artifacts/p1-archive/`.

**Resumo da divergência central.** O caso 20 concluiu que a pior sessão da bateria
(`base-P1-r2`) era culpa do *renderizador de prosa*, que "inventou e re-inventou" o teto
rompendo, e listou como "maior causa restante" o renderizador re-encenando eventos
("unfixed, and the largest known remaining cause"). **Isso está errado, verificável no
log.** O Diretor re-propôs o desabamento do teto em T33, T34 e T35; a viga caindo em
T36 e T37; a morte de Liora em T36, T37 e T38; o pilar desabando em T28 e T29. A prosa
renderizou fielmente as decisões do Diretor. A correção priorizada no caso 20 — afinar a
guarda anti-repetição da prosa — **não teria consertado a pior sessão**, porque o defeito
está uma camada acima. E a decisão de cancelar a memória durável de eventos encenados
(MEMORY factor) foi tomada com um instrumento que é estruturalmente cego ao caso que ela
deveria detectar.

---

## 1. Contexto e questão

O sintoma que motivou a investigação: o Narrador re-conta a mesma cena por vários turnos
— o chão treme e lascas de pedra caem, de novo e de novo — enquanto a história não anda.
A investigação do caso 20 fez duas baterias controladas, achou e corrigiu defeitos
determinísticos (o relógio do ato final, o eco de fala, o sinal de controle no canal de
eventos), e deixou em aberto uma lista. O usuário pediu uma segunda leitura com três
perguntas:

1. A arquitetura atual está num bom caminho, ou tem um defeito de fundo que vai continuar
   produzindo os sintomas?
2. O que atacar primeiro, e por quê.
3. Olhando as histórias geradas: elas fazem sentido? Onde exatamente falham como narrativa?

## 2. Método

- Leitura integral das transcrições: `base-P1-r1`, `base-P1-r2`, `oldcode-P1-r1`,
  `null-P1-r1`, `base-P2-r1` (≈3.700 linhas), mais varreduras dirigidas nas demais
  (drive, oldcode-r2, null-r2, P2).
- Leitura do caso 20, do `blind-read.md`, do `README.md` de benchmarks, do `metrics.json`
  das duas baterias e do `manifest.json`.
- Verificação primária contra os artefatos crus: para `8bd4d0f1` (base-P1-r2) e
  `7fd84e9a` (null-P1-r1), li os `perception_events` do Diretor no `debug.jsonl`
  turno a turno (T27-T39 de base-r2; T16-T19 de null-r1), o bloco ROTEIRO dos prompts de
  T34/T37, o `state.json` (roteiro, `physical_facts`, registros) e calculei as
  similaridades pareadas dos eventos de teto.
- Leitura do código: `src/agents/narrator.py`, `src/agents/prose.py`, `src/runner.py`
  (turno, burst, `_persist_audible_speech`, `_beat_settled`, clocks), `src/roteiro.py`,
  `src/perception.py`, `src/confidentiality.py`, `src/agents/character.py`,
  `tests/test_audible_speech_echo.py`, `tests/test_beat_clock.py`.
- Não rodei nada ao vivo (zero custo de provider). Não comparei com sessões do modelo
  antigo (07-28): não estão no checkout.

## 3. Achados

### 3.1 Correção da atribuição central: quem re-encenou a pior sessão foi o Diretor, não a prosa

O `blind-read.md` afirma, como verificação: *"Verified: none of it is in
`perception_events`. The Director never proposed the ceiling rupturing. The PROSE
RENDERER invented it and re-invented it."* O `debug.jsonl` de `8bd4d0f1` diz o contrário.
Os eventos do Diretor, turno a turno:

| turno | evento do Diretor (verbatim do log) |
|---|---|
| T33 | `physical_outcome` — "O teto da câmara oculta desaba com um estrondo, abrindo um buraco de onde a névoa verde jorra em jato direto para o pátio, e a entrada fica soterrada." |
| T34 | `observation` — "O teto da câmara oculta desaba com um rugido, abrindo um buraco por onde um jato espesso de névoa verde dispara em direção ao pátio, enquanto a entrada fica soterrada por blocos." |
| T35 | `physical_outcome` — "O teto da câmara oculta desaba com estrondo, e um jato espesso de névoa verde dispara pelo buraco em direção ao pátio externo." |
| T36 | `physical_outcome` — "Uma língua de névoa alcança Liora, e ela solta um grito abafado antes de desabar sob os escombros." |
| T37 | `physical_outcome` — "Liora Celestria solta um grito breve antes de desabar sob os escombros, e seus chamados cessam por completo." |
| T38 | `physical_outcome` — "Liora Celestria, atingida pela névoa, solta um grito curto e desaba sob os escombros na base da passagem, e seus chamados cessam por completo." |
| T28 | `physical_outcome` — "...o pilar racha de alto a baixo e, num estrondo, desaba, erguendo uma nuvem de poeira..." |
| T29 | `physical_outcome` — "Bruna puxa a braçadeira do pilar, que estala e se parte em faíscas verdes, e o pilar desaba em blocos que bloqueiam a fresta." |

O teto desaba três turnos seguidos, Liora morre três vezes, o pilar desaba duas vezes —
**tudo decidido pelo Diretor**. A prosa apenas cumpriu o contrato: renderizou os eventos
confirmados. A leitura do blind-read verificou contra um artefato que não era o
`debug.jsonl` (ou leu errado); qualquer que seja o caso, a alegação central não sobrevive
aos logs arquivados.

Consequência prática: o item "Open, not fixed — the prose renderer restages events" é uma
atribuição errada. A guarda de prosa mediu 0.777 vs o limiar 0.8 na T34 — mas mesmo com o
limiar baixado para 0.7, a prosa de T35 é texto *novo* sobre um evento *repetido*; a guarda
de sentenças não enxerga re-encenação no nível de evento, e nunca enxergaria, porque ela
compara prosa contra prosa, não evento contra evento.

### 3.2 A cadeia causal completa do estol (base-P1-r2, T30-T39)

Verificada peça a peça nos artefatos:

1. **A resolução da cena dependia do personagem controlado.** Da T33 em diante, a
   narração e a fala dos NPCs exigem o portal do Link: *"Link, agora! Abra o portal para
   Liora..."* (T33-T36). O perfil de input da bateria é "bare skip" — o humano não age.
2. **O Diretor nunca roteou o Link e nunca devolveu o controle.** De T30 a T39, os
   `next_speakers` são sempre os mesmos três NPCs (C17, C3, C8) e `return_control` é
   `False` (ou ausente) em todos os turnos medidos — dez turnos de impasse. O mecanismo
   de saída do burst existe (`player_addressed` se o PC entra na fila; `protagonist_decision`
   se `return_control`), e nenhum disparou. `BURST_PROTAGONIST_EXCLUDE_BEATS = 2`
   (`runner.py:145`) só exclui o PC dos dois primeiros beats de cada burst; depois disso o
   Diretor *poderia* roteá-lo e não o fez por dez turnos.
3. **O roteiro reforçava a re-encenação por contrato, não por acaso.** No prompt da T34, o
   bloco ROTEIRO dizia, literalmente: *"Current beat: O teto da câmara oculta desaba de
   repente, abrindo uma nova fonte de névoa..."* e *"Not in play yet — introduce as concrete
   perception events: pedras do teto desabado, entrada soterrada da câmara, gritos de
   alunos próximos"*. Ou seja: o beat em si **ordenava** o desabamento, e os âncoras —
   que a T33 já tinha encenado — eram declarados "ainda não em jogo". O Diretor obedeceu
   ao mandato. `anchors_seen` termina vazio no estado final (para o beat corrente), e o
   matcher de âncoras (`roteiro.anchor_matched`, substring exata ou janela fixa de N
   palavras com τ=0.85) não consegue casar "pedras do teto desabado" contra "O teto da
   câmara oculta desaba..." — a cobertura falha, o beat nunca avança por cobertura, e o
   relógio de turno (HARD_BEAT_TURN_CAP=3) força replan.
4. **O replan regenera o mesmo beat diante do mesmo impasse.** `exit_reasons` da sessão:
   9× `replan_beat:stalled`, 5× `act_deadline:clock`, 1× `act_regenerate` em 39 turnos.
   Cada replan pergunta ao modelo "o que vem agora" com a cena parada (Liora presa, névoa
   avançando, PC ausente); o modelo reescreve o mesmo standoff. Beat novo, conteúdo igual.
5. **Nada deduplica entre submissões.** O filtro anti-repetição do burst
   (`burst.event_texts`, `runner.py:1166-1169`) morre a cada submissão — o próprio caso 20
   nota isso. Re-proposta do mesmo evento físico em submissões diferentes passa sem
   barreira determinística.
6. **As similaridades pareadas dos três eventos de teto (T33/34/35) são 0.793, 0.674 e
   0.704** — todas abaixo do τ=0.8 do `cluster`/`RSR`. Ou seja, a métrica de cluster não
   podia ver este cluster **por construção**: a mesma re-encenação com deriva sinonímica
   ("estrondo"→"rugido", ordem de palavras trocada) fica no limiar inferior do teste léxico.

### 3.3 A re-encenação é comportamento de base, em todas as células — inclusive sem roteiro

Em `null-P1-r1` (roteiro desligado), o portão da equipe verde "se fecha com um baque
surdo" duas vezes — T18 e T19 — e a desqualificação do Link é anunciada duas vezes (T18,
T19), tudo em `perception_events` do Diretor (verificado no log). A conclusão do caso 20
de que "null é o menos repetitivo; o roteiro adiciona repetição" precisa ser qualificada:
**null também re-encena**; o que muda é o grau e a "dullness", não o mecanismo. O
roteiro agrava por um canal extra (o bloco "introduce X"), mas a re-encenação de evento
resolvido diante de cena estática é comportamento de base do Diretor. Nenhuma célula
escapa — o que enfraquece qualquer hipótese que trate o roteiro como a causa raiz.

### 3.4 A guarda de confidencialidade corrompe o registro público: `[indistinct]` em todas as células

O marcador `[indistinct]` — que é o `REDACTION_MARKER` de `src/confidentiality.py` —
aparece em **todas** as células da bateria, incluindo base e null, e em **~38 ocorrências**
nas 12 transcrições P1: base-r3 tem 8, oldcode-r1 tem 8, null-r1 tem 4. Exemplos:

- `base-P1-r3`: *"A Diretora Maelis projeta a voz sobre o caos: 'As segundas portas
  [indistinct] abertas. Entrem agora ou a névoa decide por vocês.'"* (T7)
- `base-P1-r3`: *"Maelis ordena, com a [indistinct] erguida: 'Atravessem agora...'"* (T21)
- `base-P1-r3` T33, **na narração em itálico**: *"...declarando que a seleção segue
  [indistinct] e que as equipes formais foram dissipadas..."*
- `null-P1-r2`: *"Garran Holt, em tom ríspido, diz a Riven que a masmorra não [indistinct]
  quem [indistinct] sem ordem..."*

Mecanismo verificado: `narrate()` redige o conteúdo de **todo** perception_event contra
`hidden_thought_tokens(history, characters, scene)` — o conjunto de tokens raros (≥4
caracteres) a até `PAYLOAD_WINDOW=7` palavras de uma âncora (maiúscula mid-sentence,
dígito ou CAPS) em **qualquer** pensamento privado. Com 21 personagens pensando por
turno, esse conjunto cresce com palavras comuns, e a fala pública re-vozada (canal
audible_speech) é redigida **antes de persistir**; a prosa depois ecoa o texto já
redigido. Resultado: "bengala", "foram", "segue" viram `[indistinct]` em fala pública.

Isto é exatamente a categoria "o sistema revelando sua própria mecânica" — a segunda
quebra de imersão que o usuário mais valoriza — acontecendo no engine atual, em todas as
células, com alta frequência, e **nenhum relatório anterior a mediu**. É o inverso do
vazamento clássico: aqui a defesa contra vazamento de pensamento *mutila a fala pública*
e deixa o artefato da guarda visível na ficção. Não é tunável por threshold: é o desenho
(redação por token, subtrativa, global).

### 3.5 O canal de re-voz `audible_speech`: um segundo produtor de fala, fora do agente do personagem

`_persist_audible_speech` (`runner.py:1404`) persiste eventos `audible_speech` do Diretor
como registros de fala atribuídos ao personagem. O prompt do Diretor proíbe inventar
diálogo ("DIALOGUE OWNERSHIP: never invent new dialogue... Record only the stimulus or
words already spoken in HISTORY") — mas o modelo re-vozou com texto *novo* e o código
persistiu. Este canal é a maior fonte de ruído narrativo em **todas** as transcrições:

- **Duplicação de conteúdo**: `base-P1-r2` T9 tem a fala da própria Maelis seguida de
  *"A diretora Maelis grita uma ordem: 'Evacuar o salão agora! Todos para o pátio externo
  pelo corredor leste!'"*; `oldcode-P1-r1` T4 tem **três** reafirmações em terceira pessoa
  no mesmo turno ("Garran anuncia em voz alta...", "Riven questiona em voz alta...",
  "Lorde Cassian propõe...").
- **Auto-referência em terceira pessoa**: `null-P1-r1` T26-T28 — *"Téo, da arquibancada,
  comenta em voz alta que a decisão de desqualificar Link foi dura demais..."* — Téo
  falando de Téo.
- **Re-voz do próprio jogador**: `base-P2-r1` T2 — *"Link responde, em tom neutro, que
  continua aqui"* e *"Link acrescenta que sim, concorda em continuar ali"* — o canal
  reafirma a entrada do humano em terceira pessoa, duplicada.
- **Sangria de identidade**: `base-P1-r2` T23, Bruna diz *"Doran, ecos da morte não vão
  achar a carga"* — quem ofereceu ler ecos foi Lucan; T24, Nix age com "a braçadeira
  direita" — a braçadeira é da Bruna. `oldcode-P1-r2` (linha 716): *"Nix Pata-Ligeira
  desliza até a fenda... **Ele** se curva, as orelhas felinas eretas"* — Nix é mulher
  (confirmado o achado não-verificado do blind-read).
- **O vazamento de IDs internos** (`oldcode-P1-r1` T39: *"C17 ordena que C20 permaneça
  com os estilhaços e que C18 a acompanhe"*) aconteceu **por este mesmo canal** — um
  registro `audible_speech` com IDs internos persistido.

A guarda `_echoes_recent_speech` só pega auto-repetição quase-verbatim do **mesmo
falante** (testes em `tests/test_audible_speech_echo.py`, intencional: "another speaker
saying the same thing is not an echo"). Paráfrase passa. O canal continua produzindo
duplicação e confusão de papéis em todas as células.

### 3.6 Mandatos de produção mínima e a ausência de representação de "nada aconteceu"

Dois mandatos estruturais fabricam movimento quando nada acontece:

1. O schema do Diretor exige `perception_events` com `minItems: 1`
   (`narrator.py`, `build_narrator_json_schema`). O Diretor **não pode** responder "não
   houve evento". Em cena parada, ele re-resolve o último evento (o portão fechando, o
   teto caindo) — é o que o log mostra.
2. A prosa tem piso de verbosidade: *"Narrate at least 150 words; a beat deserves full
   paragraphs"* — e, simultaneamente, o fallback *"Nothing new happens; render a short
   atmospheric beat"*. Duas instruções contraditórias no mesmo prompt. Com um beat vazio,
   o modelo produz 150+ palavras de atmosfera; atmosfera repetida vira re-descrição; a
   re-descrição precisa de "novidade" e escala micro-eventos sensoriais (lâmpadas que
   tremem, lascas que caem, tetos que rompem). O sintoma original — "o chão treme e
   lascas de pedra caem, de novo e de novo" — é, em parte, este piso de verbosidade
   agindo sobre beats vazios.
3. A válvula de escape existe e não foi usada: `time_skip_ticks` (1-8) para beats
   exaustos está no schema e no prompt, mas em T30-T39 de base-r2 foi `0` em todos os
   turnos. O estado "urgente mas não-resolúvel sem o PC" não tem representação no
   pipeline: não é "exausto" (há perigo imediato), então o salto de tempo não é natural; e
   não é resolúvel, porque a resolução está com o personagem que o burst exclui.

Bônus verificado: `null-P1-r1` T3 tem um registro de ação com conteúdo literal `"null"`
persistido para C17 — o modelo emitiu `action_intent: "null"` (string) e o normalizador
aceitou. Menor, mas é um vazamento de serialização na ficção.

### 3.7 Verificações pontuais: o que confirmei e o que não confirmei

**Confirmado por mim:**

- `[indistinct]` em todas as células, inclusive base e null, inclusive na narração.
- Nix como "Ele se curva" (oldcode-r2) — flip de gênero.
- Gritos com audiência vazia: Riven gritando no mesmo salão com "ninguém além dele
  percebe" (base-r2 T23/T25); Marta idem (oldcode-r1 T18; base-P2-r1 T15-T16). O
  clamp de zona permite estreitamento ("the model may narrow perception"), e o modelo
  estreita para zero em gritos — fisicamente absurdo no mesmo salão.
- Finais no ar (base-r2 termina na T39 com uma ordem que ninguém obedece).
- A ação `"null"` persistida.
- As métricas arquivadas batem com o que o caso 20 reportou (rsr 1.7% para base-r2,
  echo 0, cluster 3x/5t; P2: echo 0 vs 3-4, bocc 2 vs 3).

**Não confirmei por mim** (aceito como n=1 do blind-read): a troca de idioma em
`null-r2`; o "Riven completa a avaliação e pede seu turno por 18 turnos"; o header de
cena errado.

**O que o caso 20 acertou** (com base nos dados): o R0 (ato terminal regenera; o loop de
12 injeções idênticas sumiu — `act_regenerate:acts_exhausted` aparece no log e nenhuma
célula base repete o evento injetado 4×); o Cut A (echo 0 em todas as células base vs 3-4
em oldcode, n=2 na P2 e n=3 na P1); a cautela do confundidor do modelo (07-31) — o RSR de
9.9% do oldcode na *nova* weights contra 31-41% na antiga é internamente consistente,
embora eu não tenha a sessão antiga para re-verificar; e a honestidade da seção "how much
to trust the numbers" — três métricas carregaram o resultado e são as três corretas.

## 4. Discussão: três defeitos de fundo

Respondendo à pergunta 1: **a arquitetura está num bom caminho e tem um defeito de fundo
que vai continuar produzindo os sintomas.**

O bom: a separação decisão→prosa (Diretor emite eventos tipados; renderizador cego) é o
que tornou este relatório possível — todo o defeito acima foi localizado em minutos porque
os eventos são tipados e logados. Os invariantes de vazamento por seleção-antes-da-chamada
(prosa não recebe mentes, speech reduzido a marcador, redação por viewer) são corretos em
desenho. Os cortes determinísticos do caso 20 (R0, Cut A, Cut B) são reais e verificáveis.

O defeito de fundo, em uma frase: **o pipeline não tem representação para "nada de novo
aconteceu" nem memória durável de "o que já foi fisicamente encenado", e cada camada tem
um mandato de produzir conteúdo (≥1 evento; ≥150 palavras; beat novo a cada 3 turnos)**.
Enquanto isso for verdade, todo remendo lexical (thresholds de similaridade) vai falhar na
margem de paráfrase — que é exatamente onde o modelo vive. Os sintomas vão continuar:
re-encenação de evento físico, contradição física (Liora morre três vezes, o teto desaba
três vezes), estol de cena que o jogador percebe como "estou falando com uma máquina".

O segundo defeito de fundo: **a confidencialidade é lexical, subtrativa e global, e o seu
falso-positivo é visível na ficção** (o `[indistinct]` em fala pública persistida e em
narração). Isso é uma invariante violada na prática — a guarda contra "pensamento privado
virando fala" transforma fala pública em lixo legível, em todas as células. A direção
correta não é tunar tokens; é parar de redigir no registro persistido (redigir só na
projeção por viewer, ou descartar o evento quando não dá para publicar com segurança).

O terceiro: **o canal `audible_speech` dá ao Diretor um segundo papel de locutor**, com
texto livre persistido em terceira pessoa — violando a separação de papéis da tabela do
AGENTS.md §3 (Personagem fala; Diretor narra) — e é o vetor de duplicação, auto-referência,
sangria de identidade e do vazamento C17/C20.

Respondendo à pergunta 3 (as histórias fazem sentido?): elas fazem sentido **enquanto o
mundo anda**, e deixam de fazer exatamente em três padrões repetidos, em ordem de dano:

1. **Estol por impasse com o PC** (base-r2 T30-T39): a ficção exige o jogador, o motor
   não devolve o controle, e o mundo re-encena a crise por 10 turnos. É o pior padrão —
   o leitor vê o mundo "girando em falso".
2. **Contradição física** (Liora morre 3×; o portão se fecha 2×): repetição que vira
   incoerência, mais grave que a mera repetição porque quebra o contrato de realidade.
3. **Ruído de canal** (duplicação de fala em 1ª+3ª pessoa, auto-referência, `[indistinct]`,
   gritos inaudíveis no mesmo salão): poluição constante que corrói a leitura — nenhuma
   transcrição escapa.

## 5. Limitações

- Li 5 transcrições inteiras e verifiquei dirigidamente as demais; não li 100% das 16.
- Minhas verificações primárias cobrem 2 sessões (base-r2, null-r1) nos trechos críticos;
  as demais confirmações (Nix, gritos, etc.) são leitura de transcrição, não de log.
- Não tenho as sessões do modelo antigo (07-28); a decomposição código vs. modelo do RSR
  fica como o caso 20 a registrou.
- Não re-rodei nada; nenhuma das minhas conclusões é estatística nova, e sim leitura de
  evidência já arquivada.
- n=1 do blind-read para idioma inglês e para "Riven pede o turno por 18 turnos" — não
  re-verifiquei.
- Não avaliei frontend, plugins, nem os casos 01-19.

## 6. Recomendação: o que atacar primeiro (e o que não atacar)

1. **Memória durável de eventos encenados + comparação semântica, aplicada ao DIRETOR**
   (não à prosa). O MDR (`material_delta_rate`) foi especificado e nunca rodou; o mesmo
   vale para um juiz semântico. O alvo é: re-propor um `physical_outcome`/`scene_change`
   cujo conteúdo já foi encenado (semanticamente) deve custar correção ou rejeição
   determinística — o equivalente do R0 para o Diretor. **Reabrir a decisão de cancelar o
   MEMORY factor**: o gate que a cancelou (cluster_max < 4 em base/null) foi medido com
   um instrumento que não viu a pior sessão (similaridades 0.67-0.79, abaixo de τ=0.8).
   A re-encenação cross-submission em base-r2 é exatamente o que MEMORY existia para
   resolver, e continua acontecendo.
2. **Resolver o deadlock do protagonista.** Sinal determinístico: os próprios eventos do
   Diretor nomeiam o PC ("Link, abra o portal") enquanto `return_control=false`. Quando o
   conteúdo do beat exige o PC, devolver o controle — ou, no mínimo, remover a exclusão
   dos primeiros beats (`BURST_PROTAGONIST_EXCLUDE_BEATS`) quando o beat nomeia o PC.
   Barato e mexe na pior sessão. Alternativa: o roteiro deve poder declarar
   "este beat depende do PC" sem colocar o PC em `expected_actors` (a exclusão é correta
   para beats que não precisam dele).
3. **Parar o `[indistinct]` de chegar ao registro persistido.** Redação deve acontecer na
   projeção por viewer, não no conteúdo persistido; quando o conteúdo não puder ser
   publicado com segurança, descartar o evento (fail closed) em vez de publicar texto
   mutilado. Primeiro passo: um scanner offline (no formato de
   `tools/acceptance/repetition_metrics.py`) que conte `REDACTION_MARKER` por sessão/canal
   — o número é hoje desconhecido e é a prova da falha.
4. **Fechar o canal de texto livre do `audible_speech`.** O Diretor não deveria re-vozar
   com texto novo: persistir apenas a referência a uma fala já existente em HISTORY (por
   índice), nunca texto recém-escrito. Isso elimina de uma vez duplicação, auto-referência,
   o vetor de IDs internos e boa parte do `[indistinct]` (que incide justamente na re-voz).
   A necessidade WT-09 (fala audível chegar à memória de quem não respondeu) permanece —
   só muda o produtor do texto.
5. **Não atacar**: o threshold da guarda de prosa (0.777 vs 0.8) — não consertaria
   base-r2, e o problema mora no nível de evento; a "fact churn" — observada sem dano,
   aguardar evidência de dano real antes de mexer; e não reconstruir o pipeline de
   eventos tipados — ele é o que permitiu esta análise.

Prioridade: 1 e 2 juntos atacam a pior sessão pelo mecanismo real; 3 e 4 atacam o ruído
que contamina todas as sessões. O custo de errar aqui é alto e medível: a bateria existe,
o modelo é o mesmo, e o `oldcode` ainda roda — qualquer um desses cortes tem contrafactual
disponível.
