# Scene stagnation as absent state transition: the world as a clock, and what the human literature teaches

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 12 |
| **Date** | 2026-07-17 |
| **Type** | Research synthesis + design program (owner-authored findings preserved) |
| **Status** | ACTIVE program: feeds Tasks 33b and 40 (clock delivered; watcher validated by exploration) |

## Abstract

Research synthesis defining stagnation as the absence of narrative state transition: two decoupled clocks (conversation vs world), a material-delta definition of progress, a causal intervention contract, a recovery ladder, and the player-attempt contract - grounded in the dialogue, turn-taking, improv and RPG literatures (Pickering & Garrod; Sacks, Schegloff & Jefferson; Magerko; FIREBALL). Its predictions were later validated by curl exploration and the delivered narrative clock; the A/B/C battery it specifies in section 7 is executed as case No. 13.

---
Documento de pesquisa + design, alimentando a **Task 33b**. Sintetiza o achado
empírico da Task 38 (relatório: `11-roteiro-drive-scene-stagnation-2026-07-17.md`)
com literatura sobre diálogo, turn-taking, improviso e RPG, e mapeia como esses
temas ajudam — e o que já fizemos similar no kernel.

Origem: dois achados do usuário (2026-07-17). Este doc os registra fielmente e
adiciona o mapeamento pro nosso código.

---

### 1. A tese

> **Estagnação não é repetição de texto; é ausência de transição de estado
> narrativo.**

Os guards que implementamos (backstop lexical, guard de personagem, teto de
beat, disrupção-no-stall) eliminam sintomas reais — eco, near-dup, beat infinito
— mas **uma cena pode produzir frases completamente diferentes e permanecer
semanticamente imóvel**. "Todos comentam o sorteio de maneiras variadas" ainda é
o mesmo estado.

O limite que batemos na Task 38 não é o limite do roleplay com LLM. É o limite
de **usar geração autoregressiva como motor de progressão dramática**. O modelo
é excelente em *continuar* uma cena; não é naturalmente confiável em *decidir que
a cena esgotou sua função e deve mudar de estado*.

---

### 2. O mecanismo: dois relógios desacoplados

A cena do sorteio (portais) estagnou porque **o relógio da conversa continuou
avançando, mas o relógio do mundo parou**:

```
Cena de AÇÃO (estalagem)          Cena PROCEDURAL (portais)
personagem tenta                   personagem espera
  → mundo responde                   → personagem comenta
    → estado muda                      → mundo continua esperando
```

Na estalagem, ameaça/movimento/tentativa exigem adjudicação — cada ação chama
uma resposta do mundo. Nos portais, os personagens esperavam uma *instituição*
realizar um procedimento. Como o mundo não tem relógio autônomo, ele ficou
esperando o Diretor; e o Diretor continuou servindo reações do elenco.

> **O sistema confundiu participação do elenco com progressão da cena.**

O histórico funciona como um **campo gravitacional / atrator**: quanto mais
personagens reafirmam um enquadramento, mais provável fica que a próxima geração
(1) reconheça o enquadramento como "a cena", (2) preserve a coerência local, (3)
dê voz ao próximo personagem dentro dele, (4) reforce ainda mais o enquadramento.
Em elenco grande piora: "cada NPC precisa reagir", então seis reações viram seis
votos para manter o tópico vivo.

O beat disruptivo funcionou (3/3 no curl) não porque "disrupção" seja a solução
correta, mas porque foi a **primeira mutação autoritativa de estado** — reacoplou
os dois relógios: `evento concreto → mundo muda → personagens têm algo novo a
responder`. Mas disrupções sucessivas produzem **pile-up** porque *novidade
sozinha não equivale a causalidade* (confirmado no run de confirmação do portais).

---

### 3. A literatura: humanos também alinham, repetem e travam

O erro seria concluir "LLMs repetem e humanos não". A conclusão melhor:

> Humanos também alinham, repetem, reafirmam e deixam cenas morrer. Mas uma mesa
> humana tem **silêncio, metajogo, compressão temporal, sinais sociais e um GM
> responsável por manter o mundo em movimento**. Nosso sistema removeu quase
> todas essas saídas e manteve a obrigação de gerar.

- **Alinhamento interativo — Pickering & Garrod.** Humanos naturalmente alinham
  vocabulário, estrutura e representação da situação durante uma conversa. Parte
  da repetição que observamos é uma versão *exagerada* de um mecanismo humano
  real de coordenação — não é falha cognitiva; a função é reduzir ansiedade e
  criar afiliação. (["Toward a mechanistic psychology of dialogue"](https://www.pure.ed.ac.uk/ws/files/11823730/Toward_a_mechanistic_psychology_of_dialogue.pdf))
- **Turn-taking — Sacks, Schegloff & Jefferson.** A organização de turnos não é
  round-robin: o falante atual pode selecionar alguém, outro pode se
  autosselecionar, e os demais podem ficar em silêncio. Turno é local e
  distribuído. → **presença na cena não implica direito nem obrigação de emitir
  reação** — exatamente o que nosso `expected_actors` viola. ([o estudo clássico](https://pure.mpg.de/rest/items/item_2376846_3/component/file_2376845/content))
- **Improviso e `wimping` — Magerko et al.** Cenas progridem quando alguém faz
  uma *oferta* destinada a alterar o estado narrativo e os outros a aceitam.
  `wimping` = aceitar a oferta anterior sem construir nada a partir dela. Os NPCs
  fizeram wimping em escala (todos "aceitam" que estão ansiosos pelo sorteio,
  ninguém acrescenta uma operação que transforme a situação). ([estudo empírico](https://www.academia.edu/4105381/An_empirical_study_of_cognition_and_theatrical_improvisation))
- **Metajogo — Corbitt 2024.** Numa campanha de 6 semanas, a fala de metajogo
  negociava conhecimento, justiça, relações e *ritmo narrativo*. A saída humana
  pra estagnação frequentemente **abandona momentaneamente o roleplay** ("já
  entendemos que todo mundo tá nervoso, pula pro resultado?"). ([Corbitt, 2024](https://www.sciencedirect.com/science/article/abs/pii/S0898589824000263))
- **Frames de diálogo em RPG — Mäyrä.** Três frames intercalados: conversa social
  fora do jogo; negociação de regras/estado; fala dentro da ficção. O GM tem
  poder especial de transformar uma declaração em fato do mundo (jogadores ainda
  negociam/contestam). ([Dialogue in RPGs](https://homepages.tuni.fi/frans.mayra/Dialogue-in-RPGs.pdf))
- **FIREBALL — ACL 2023.** ~25k sessões reais de D&D no Discord, 8M utterances,
  2,1M comandos, 1,2M estados estruturados. Modelos **com estado real do jogo
  produziram turnos melhores que os baseados só em histórico de diálogo**. Não
  mede estagnação diretamente, mas confirma: roleplay humano real **não é só uma
  corrente de falas** — intercala linguagem, comandos executáveis e mudanças
  verificáveis de estado. ([FIREBALL](https://aclanthology.org/2023.acl-long.229.pdf))

**Sinais fora do texto:** o GM humano detecta "esta cena acabou" por silêncio
desconfortável, respostas encurtando, olhares, piadas fora de personagem, perda
de energia — *antes* de haver repetição textual suficiente pra um detector. Num
log só-texto, boa parte dessa informação some. (Implicação: nosso detector é
cego a metade dos sinais que um humano usa.)

---

### 4. As saídas humanas que removemos

1. **O jogador/personagem pode não produzir conteúdo.** "O meu só espera" é um
   turno válido de 2 segundos. Nós pressionamos cada personagem convocado a
   produzir uma contribuição apresentável. → silêncio deve ser permitido.
2. **O GM comprime tempo.** "Depois de alguns minutos de especulação, o sino toca
   e o primeiro par é anunciado." Isso **não é disrupção** — é a *conclusão da
   transição já prometida pela cena*. O humano alterna modo dramático ↔ sumário.
3. **Oferta com intenção ativa.** "Vou até o responsável perguntar por que
   demora", "tento ver a lista antes", "desisto de esperar e me aproximo do
   portal" — uma tentativa que exige resposta do mundo.
4. **Sair da ficção (metajogo).** Um canal que os personagens não têm.
5. **Ler sinais fora do texto** (acima).

---

### 5. O que já fizemos similar aqui (mapeamento pro kernel)

Já temos **implementações parciais** de vários mecanismos humanos:

| Mecanismo humano | O que já existe no kernel |
|---|---|
| GM transforma declaração em fato do mundo (Mäyrä) | Split Diretor/Prosa (36); `action_intent` = TENTATIVA que o Diretor adjudica |
| Oferta que muda estado | `perception_events` tipados do Diretor; disrupção-no-stall (38) |
| Mundo com estímulos próprios | Drive hazard scheduler (33): injeta evento externo em cena quieta |
| Devolver controle ao jogador | `return_control` (37) → para a fila no protagonista |
| Direção pré-compilada | Roteiro (38, opt-in) |
| Anti-repetição de superfície | backstop lexical + guard de personagem + teto de beat |

**O que FALTA** (a lacuna que explica a estagnação):

- **Estado autoritativo de cena** (dramatic_question, threads, pressures) — hoje
  o "estado" é só o histórico + scene.physical_facts + o beat do roteiro. Não há
  representação de *o que está dramaticamente em jogo*.
- **Definição de progresso por DELTA MATERIAL** — hoje medimos cobertura de
  âncoras (entidade/lexical), que o próprio usuário aponta como sinal errado: uma
  figura encapuzada nova pode aparecer sem nada avançar; uma porta simplesmente
  fechar pode transformar a cena.
- **Relógio do mundo** — procedimentos pertencentes ao mundo (o sorteio) não
  avançam sozinhos; ficam reféns da geração de reações do elenco.
- **Cobertura de atores representativa, não exaustiva** — `expected_actors` +
  o roteamento tratam presença como obrigação de falar.
- **Contrato causal de intervenção** — a disrupção-no-stall introduz novidade,
  mas não amarra a um thread existente (→ pile-up).

---

### 6. O design proposto (Task 33b reenquadrada)

Task 33b deixa de ser "watcher que reescreve o roteiro" e vira um **controlador
de transição de estado de cena** — tira da LLM a responsabilidade de perceber
sozinha quando continuar deixou de ser progredir, e dá ao código autoridade pra
exigir uma transição causal concreta.

#### 6.1 Estado autoritativo mínimo
```
scene_phase          dramatic_question     active_pressure
unresolved_threads   actor_commitments     last_material_change
intervention_level
```

#### 6.2 Progresso = DELTA MATERIAL verificável
Um turno só conta como avanço se produzir ≥1 delta: uma decisão foi tomada;
informação antes desconhecida virou conhecida; posição/posse/acesso mudou; uma
tentativa recebeu consequência; uma relação/compromisso mudou; uma ameaça
avançou; uma possibilidade foi aberta/fechada; a pergunta dramática mudou.
Entidade nova e novidade lexical *participam* do sinal, mas **não são o sinal
principal**.

#### 6.3 Recuperação em ladder (ANTES de disromper)
```
1. Há transição do mundo já prometida?  → EXECUTE-A.
2. Há tentativa pendente?                → ADJUDIQUE-A.
3. Há personagens sem contribuição material? → permita SILÊNCIO ou agregue reações.
4. Ainda sem mudança possível?           → reincorpore um thread existente como pressão.
5. Só então:                             → introduza uma disrupção nova.
```
A disrupção é o ÚLTIMO recurso, não o primeiro. Um GM humano não explodiria os
portões — ele simplesmente **realizaria o sorteio**.

#### 6.4 Contrato causal de intervenção (o antídoto pro pile-up)
```yaml
source_thread:   "o portal reage de forma anômala ao jogador"
target_state:    "o sorteio deixa de ser a questão dominante"
event_now:       "o portal atribuído a outro aluno se abre para o jogador"
expected_delta:  "a cerimônia é interrompida e a seleção é contestada"
closes_or_advances: "mistério dos portais incompatíveis"
refractory_turns: 3
```
Muito diferente de `event_now: "um estrondo e uma figura encapuzada"` — o segundo
**quebra** a cena; o primeiro a **transforma**. Após uma intervenção, proibir
outra disrupção por `refractory_turns`; nesse período o Diretor só: materializa a
consequência → permite reação → consolida o novo estado → devolve controle. Se
ainda estagnar, a próxima intervenção **escala o mesmo thread** (`lembrar →
pressionar → tornar inevitável → resolver com custo`), nunca abre outro fio.

#### 6.5 Beat de PROCEDIMENTO (o relógio do mundo)
```yaml
beat_kind: procedure
world_owner: mestre_da_cerimonia
next_world_event: anunciar_primeiro_par
max_reaction_turns: 2
on_budget_exhausted: enact_next_world_event
actor_coverage: representative_not_exhaustive
```
> Cenas procedurais não precisam primordialmente de mais drive dos personagens.
> Precisam de **um mundo que continue funcionando** enquanto os personagens
> existem dentro dele.

#### 6.6 Liberdade do jogador — contrato refinado
```
player_intent:       preservado integralmente
attempted_action:    pode ser narrada
world_response:      autoridade do Diretor
player_followthrough: nunca presumido após mudança material
return_control:      obrigatório após complicação ou revelação
```
Refino sobre "toda ação é uma tentativa": ações **triviais e já estabelecidas**
não sofrem resistência artificial. O Diretor só interpõe resposta relevante
quando há incerteza, oposição, custo ou consequência dramática — senão vira GM
adversarial (transformar abrir uma gaveta em disputa = falsa agência). "Atravesso
o portal" pode ser interrompido porque o mundo mudou antes da consumação; mas se
o portal está aberto, seguro e sem incerteza relevante, impedir seria falsa
adjudicação.

---

### 7. O experimento que fecharia a hipótese

Três braços no cenário Portais:

| Braço | Intervenção |
|---|---|
| A | Diretor livre |
| B | disrupção concreta arbitrária (o que fizemos na 38) |
| C | consequência concreta ligada a um thread existente (§6.4) |

Medir, além de "quebrou o tópico": **delta material em 1–2 turnos**; thread
anterior avançado/fechado; nº de novos threads abertos; necessidade de nova
intervenção em ≤3 turnos; retorno efetivo de controle ao jogador; **coerência
causal julgada às cegas**.

Previsão (usuário): **B vence em quebra imediata; C vence em drive sustentado e
coerência.** Essa é a diferença entre um *mecanismo anti-loop* e um *motor
dramático de verdade*.

Método de exploração: curl-replay primeiro (AGENTS.md §6) — validar o contrato
causal numa chamada real de Diretor antes de qualquer bateria; depois o A/B/C.

---

### 8. Relação com o que está roteado

- **Task 33 (drive layer)** já foi roteada (2026-07-17) pra ganhar um gatilho de
  estagnação. Este doc a refina: o gatilho não deve ser "hora de acontecer algo"
  (hazard) e sim um **controlador de transição** com estado autoritativo + delta
  material + ladder de recuperação. A disrupção arbitrária é o piso, não o teto.
- **Task 33b** herda este design (controlador de cena + contrato causal + beat de
  procedimento + cobertura representativa).
- **FIREBALL** sugere um caminho de validação futuro: modelos com estado
  estruturado > histórico de diálogo. Nosso `perception_events` + o estado de
  cena proposto são o análogo; um dataset como FIREBALL permitiria medir
  quantitativamente (embora enviesado a interações com comandos do Avrae).

---

### 9. Mecanização: o relógio narrativo (Task 40)

Ideia do usuário que fecha o "relógio do mundo" (§2) de forma concreta: a LLM
está parada no tempo porque a história não tem relógio. Introduzir um **tick
monotônico, dono do código, que sempre avança**, com **cada ato do roteiro
amarrado a um deadline de tick + o `world_event` que dispara nele**. No deadline,
o código FORÇA a transição do mundo — a LLM não pode parar o tempo porque o tempo
não pertence a ela. Isso torna determinístico o "beat de procedimento" (§6.5): o
sorteio acontece quando o sino toca (tick), não quando o elenco para de comentar.
Especificado em `.plan/tasks/40-narrative-tick-clock.md`; começa por curl-replay.
