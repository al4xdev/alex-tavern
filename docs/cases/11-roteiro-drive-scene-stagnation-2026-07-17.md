# Roteiro, drive and scene stagnation: empirical results of typed beat contracts

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 11 |
| **Date** | 2026-07-17 |
| **Provider** | DeepSeek V4 Flash, real runs, blind critic |
| **Task** | 38 (delivered with reservations) |
| **Status** | Evidence feeding the stagnation program (No. 12) |

## Abstract

The Task 38 report and the investigation it unlocked: why procedural roleplay scenes stagnate and repeat. Typed beat contracts banked engine gains, but the roteiro proved coin-flip on a procedural scene (portals 2W/2L); a concrete disruptive beat broke the stall 3/3 while an abstract instruction failed 0/3 - the position-and-concreteness result that seeded the clock (Task 40) and the watcher (Task 33b).

---
Relatório da Task 38 (roteiro com contratos de beat tipados) e da investigação
que ela destravou sobre por que cenas de roleplay estagnam e repetem. Provider
de todos os runs reais: deepseek-v4-flash (endpoint local caiu; deepseek
aprovado pelo usuário). Crítico cego = subagente sem contexto de implementação,
arms embaralhados (A/B), veredito por eixo.

---

### 1. O que a Task 38 entregou

Um **roteiro hierárquico** compilado antes da primeira fala: premissa + esqueleto
de 3 atos + um **beat rolante** tipado (`intent`, `expected_actors`,
`expected_anchors`, `exit_condition`, `budget_turns`). Consumido **só pelo
Diretor** (personagem/prosa não têm o parâmetro — confidencialidade estrutural).
O **replan é decidido por CÓDIGO** (`evaluate_roteiro`): cobertura de âncoras/
atores medida na fonte autoritativa (eventos tipados do Diretor + falas/ações),
com histerese (cooldown, teto de turnos, escalada pra reescrita de ato). Zero
gatilho por auto-avaliação do modelo — toda decisão logada (`roteiro_replan`).
Feature **opt-in, OFF por padrão** (`roteiro_enabled`). Schema v7.

---

### 2. O veredito honesto (medido, não desejado)

| Cenário | Personagens | Gênero | Drive (roteiro vs controle) |
|---|---|---|---|
| Estalagem | 3-4 | ação/ameaça | roteiro vence de forma **confiável** (~5 vitórias nos loops) |
| Portais (academia) | 6 | procedural/cerimônia | **cara-ou-coroa: 2 vitórias / 2 derrotas** |

**Portais, os quatro runs A/B:** loop1 (teto) vitória · loop2 (dois fixes)
derrota (travou no sorteio) · disrupção-fix vitória decisiva · confirmação
derrota decisiva.

Conclusão: o roteiro **ajuda drive em cenas de ação apertadas** e é **instável em
cenas grandes/procedurais**. O valor de "direção" ali é anulado por (a)
topic-pinning quando o beat é procedural, (b) pile-up de disrupções desconexas
quando forçado a disromper, (c) variância alta vs um Diretor livre que às vezes
acha um conflito emergente mais limpo. **Nenhum fix único torna isso confiável** —
é realidade arquitetural + variância (cerimônia de 6 personagens é difícil pra um
sistema de beats pré-planejados rodando um modelo rápido), não um bug que um loop
fecha.

Critérios que o usuário adicionou no meio:
- **Variação lexical**: garantida por construção (backstop de narração; métrica
  < 0.8 e 0 near-dups em todo run).
- **Objetivo-por-NPC-por-cena**: melhoria **global** do prompt de personagem,
  dependente do formato do arco, **não** um diferencial garantido do roteiro.

---

### 3. A investigação de estagnação (o payoff que sobrevive à task)

O crítico apontou repetição em quase todo run (personagens reafirmando a mesma
ideia; o elenco inteiro rezando por "bons parceiros" no turno do sorteio). A
pergunta do usuário: *o deepseek recebe o histórico de falas — por que repete
tanto? já tentou via prompt?* Investigamos com a técnica de **curl-replay**:
pegar o payload REAL da chamada defeituosa (do `debug.jsonl`) e iterar só o
prompt até consertar a chamada isolada, antes de rodar qualquer bateria.

#### Tabela de intervenções (chamada real do turno travado, N runs cada)

| Intervenção | Alvo | Quebrou o loop? |
|---|---|---|
| Anti-loop no prompt do **personagem** (até proibição explícita do tópico) | personagem | ❌ 0/3 |
| Regra abstrata de autoridade/anti-estagnação no **Diretor** | Diretor | ❌ 0/3 |
| **Remover** o bloco do roteiro do prompt do Diretor | Diretor | ❌ 0/3 |
| Injetar um **evento de cena novo** no contexto | contexto | ✅ 2/3 |
| **Beat concreto disruptivo** no roteiro → Diretor | Diretor | ✅ **3/3** |

#### O que isso prova

1. **Não é problema do personagem.** Nenhuma regra no prompt do personagem — nem
   uma proibição direta do tópico — quebra o loop. O modelo rápido segue a cena
   estabelecida (histórico saturado) com força.
2. **Não é (só) o roteiro.** Remover o bloco do roteiro não ajudou: o histórico
   acumulado sozinho já pina o tópico.
3. **O lever é um evento concreto novo.** Injetar um evento quebrou 2/3; um
   **beat concreto disruptivo** entregue ao Diretor quebrou 3/3 (ele encenou o
   estrondo nos portões + a figura encapuzada, largando o sorteio).
4. **O Diretor tem autoridade** pra quebrar a cena — mas só a exerce com uma
   instrução **concreta "isto acontece AGORA"**. Instrução abstrata perde pro
   puxão do histórico; evento concreto ganha.

#### O fix que saiu disso

`evaluate_roteiro` → quando um beat **estagna**, o replan gera um **beat concreto
disruptivo** que muda o assunto (chegada/interrupção/quebra acontecendo neste
turno), nunca uma continuação do tópico travado. Validado 3/3 no gerador de
replan e 3/3 no Diretor. Fechou o gap de drive numa run do portais (vitória
decisiva) — mas a run seguinte mostrou o modo de falha novo (pile-up desconexo),
mantendo o portais em cara-ou-coroa.

---

### 4. Ganhos de engine banked (valem para os dois braços)

Independem do roteiro estar ligado — melhoram o kernel inteiro:

- **Teto rígido de turnos por beat** (`6d6e9b8`): nenhum beat pina a cena em
  repetição estática; `min(budget, 3)`.
- **Guard anti-repetição de personagem** (`5c40276`): echo verbatim do próprio
  personagem / papagaiar outro eliminado deterministicamente (0/0); retry, depois
  drop do campo ecoado se o outro sobrevive (nunca emudece).
- **Backstop lexical de narração** (`06bb963`): sentença que ainda ecoa após o
  retry é removida; variação lexical garantida.
- **Cobertura na fonte autoritativa** (`35a9a2f`) + **partial-coverage advance**
  (`bdda81f`) + **arquiteto: escalar, sem exposição** (`cedbb1a`).
- **Disrupção-no-stall** (`490f1d5`).
- **Método curl-replay documentado** no `AGENTS.md` §6.

---

### 5. Roteado para outras tasks

- **Task 33 (drive layer)** — a casa natural do fix GERAL de estagnação: dar à
  hazard function um sinal de **estagnação de tópico** (nenhuma entidade/âncora
  nova por K turnos, ou baixa novidade lexical) pra injetar evento novo nos DOIS
  braços, não só no roteiro.
- **Roteiro futuro** — pile-up de disrupções desconexas + fraqueza em arcos
  procedurais: fazer a disrupção **avançar o arco planejado**, não interromper
  solto.
- **Task 26** — beat inteiro re-narrado (dedupe de `perception_event` cross-turn,
  generalizando o dedup da rajada), echo semântico de personagem, `action_intent`
  repetido.
- **Task 29.2** — `initialize_perspective` estoura o budget fixo de 1024 tokens
  com 20+ personagens presentes (escala de elenco grande).
- **Novo follow-up** — adjudicação da tentativa do jogador (o exemplo do portal):
  o Diretor resolve a ação consequente do jogador como **resposta-do-mundo** +
  `return_control` ("você ainda não atravessou; o que faz?"), nunca ditando a
  vontade dele. Mesma autoridade do Diretor, com a trava de liberdade.

---

### 6. Princípio de design que fica

> **O Diretor tem autoridade sobre a RESPOSTA DO MUNDO, nunca sobre a VONTADE de
> quem age.** Toda ação (NPC ou jogador) é uma tentativa; o Diretor decide como o
> mundo responde (pode resistir, complicar, revelar) e, para o jogador, sempre
> devolve o controle. É o mesmo mecanismo que quebra estagnação (evento concreto
> novo) e que preserva a liberdade do jogador (nunca narrar a decisão dele).

Exemplo canônico:
> Jogador: *"Eu abro o portal e atravesso."*
> Narrador: *"Sua mão alcança o selo, mas ele não responde como você esperava. A
> superfície se abre por um instante e revela alguém do outro lado. Você ainda
> não atravessou. O que faz?"*
