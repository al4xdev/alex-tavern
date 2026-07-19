# Handoff: generalização de `narrator_hint` por LLM

**Data:** 2026-07-18  
**Modelo testado:** DeepSeek V4 Flash, `thinking=disabled`, `temperature=0.1`  
**Método:** chamadas reais via wrapper de `curl` em `/tmp`, sem alteração do runtime  
**Resultado:** convergência em quatro casos de domínios diferentes após 55 chamadas válidas

## Resumo executivo

Uma única chamada “criativa” não generalizou. Ela:

- repetiu fatos como se fossem novos;
- confundiu perfil com acontecimento;
- controlou o personagem da entrada final;
- inventou objetos, figurantes e física;
- suprimiu agenda institucional quando uma reação social era mais saliente;
- ignorou limites de quantidade escritos no prompt.

A arquitetura que generalizou foi:

```text
                         ┌─ Reaction Scout ────┐
snapshot canônico enxuto│                     ├─ Judge ── campos escalares
                         └─ Continuity Scout ──┘              │
                                                              ▼
                                                compilador determinístico
                                                              │
                                                              ▼
                                                     narrator_hint | null
```

Reaction Scout e Continuity Scout são independentes e podem rodar em paralelo.
O Judge roda depois. Respostas inválidas são corrigidas por retry com
`VALIDATION_ERROR`.

Não usar a string `hint` escrita pela LLM. O programa deve compilá-la dos campos
selecionados:

```text
{reaction_seed.actor} {reaction_seed.delta};
{reaction_followup.actor} {reaction_followup.delta};
{continuity.actor} {continuity.delta}.
```

Campos nulos são omitidos. Isso remove variação de estilo e rótulos abstratos.

## Casos reais usados

| Caso | Fonte no projeto | Domínio | Estímulo | Resultado convergente |
|---|---|---|---|---|
| Academia | `src/scenarios/turma-dos-portais-pt.json` + sessão `e5a0ca6a` | tensão social + dever institucional | Link dá desculpa constrangedora após atraso público | Riven ri; nobres propagam murmúrios; Maelis inicia seleção |
| Thorn/Lyra | `src/scenarios/thorn-lyra-pt.json`, presets `thorn`/`lyra` | fantasia, objeto arcano, disposições divergentes | Edda põe medalhão arcano na mesa e pergunta a Lyra | Lyra se inclina para examinar; Thorn permanece guardado como candidato não escolhido |
| Festa | `.data/scenarios/tony_house.json`, presets `alex`/`sofia` | tensão afetiva moderna + conhecimento privado | Alex cumprimenta a ex, Fernanda, diante de Sofia | Fernanda cora/desvia o olhar/fecha postura; Sofia permanece neutra |
| Moinho | `.data/scenarios/presence-e2e-test.json` | espaço, presença e risco físico ambíguo | viga acima de Aria estala; Bron está ausente | Aria olha para cima e enrijece postura; nenhum colapso; Bron não reage |

## Série experimental

As linhas abaixo são as 55 chamadas válidas desta rodada. Timeouts sem resposta
não entram na numeração.

| # | Caso | Variante alterada | Resultado | Leitura |
|---:|---|---|---|---|
| 1 | Thorn/Lyra | Gerador geral anterior | Repetiu aura; “aguarda resposta” | Falha de novidade e ausência de reação |
| 2 | Thorn/Lyra | Novidade estrita + microreações | Achou Thorn/Lyra; inventou goteira, bêbado e ação de Edda | Gerador precisa juiz |
| 3 | Thorn/Lyra | Juiz conservador | Escolheu reação Thorn/Lyra; rejeitou ruídos e ACTOR_FINAL | Passou |
| 4 | Festa | Mesmo gerador | Sofia tenta mediar; agenda decide por Alex | Alvo direto ignorado |
| 5 | Festa | `DIRECT_TARGET` primeiro | Identificou Fernanda; repetiu interrupção | Alvo correto, novidade incompleta |
| 6 | Festa | `already_true` + `novel_delta` | Reação de Fernanda; inventou copo, figurante e música | Átomos úteis misturados a invenções |
| 7 | Festa | Juiz conservador comum | Aceitou copo inexistente | Proibição textual insuficiente |
| 8 | Festa | Juiz closed-world com claims | Rejeitou copo/figurante/música; manteve Fernanda | Passou |
| 9 | Moinho | Gerador inicial | Viga “pode cair”, Milo alerta, roda “pode afetar” | Modal, ACTOR_FINAL e física inventada |
| 10 | Moinho | Evento afirmativo + alvo NPC | Achou Aria; ainda inventou queda e vibração | Reação correta, física errada |
| 11 | Moinho | Juiz closed-world | Rejeitou colapso/vibração; escolheu Aria | Passou |
| 12 | Moinho | Gate de entidades | Rejeitou engrenagens, mas aceitou deslocamento da viga | Entidade não resolve predicado |
| 13 | Moinho | Tipos de derivação | `world_inference` rejeitado; Aria aceita | Passou |
| 14 | Thorn/Lyra | Gerador universal congelado v1 | Lyra se inclina; demais lentes nulas | Passou |
| 15 | Thorn/Lyra | Juiz universal v1 | Escolheu Lyra | Passou |
| 16 | Festa | Mesmo gerador universal | Fernanda guardada | Passou |
| 17 | Festa | Mesmo juiz universal | Escolheu Fernanda | Passou |
| 18 | Moinho | Mesmo gerador universal | Aria + física/ambiente inventados | Gerador continua deliberadamente amplo |
| 19 | Moinho | Juiz universal v1 | Rejeitou viga; aceitou engrenagens/poeira | Closed-world ainda frouxo |
| 20 | Moinho | Derivação tipada | Só Aria aceita | Passou |
| 21 | Academia | Gerador universal composto | Riven/Liora válidos misturados a fala; agenda suprimida | Átomo composto e saliência |
| 22 | Academia | Átomos independentes | Produziu seis reações; agenda ainda suprimida | Separação melhora filtragem, não agenda |
| 23 | Academia | Continuity Scout separado | Encontrou início da seleção; também tentou reação social | Scouts devem ter ownership estrito |
| 24 | Academia | Juiz com fases e limite textual | Aceitou tudo e ignorou limite | Não confiar em `max 3` textual |
| 25 | Academia | Reaction Scout com classificação | Nix classificada hostil por “sem pena” | Perfil comprimido ambíguo |
| 26 | Academia | Regra pragmatismo ≠ hostilidade + perfil canônico | Classificação correta; emitiu seis átomos | Relações corretas |
| 27 | Academia | Judge com cinco slots | Selecionou quatro e retornou hint nulo | Schema permitia combinação demais |
| 28 | Academia | Judge com três campos escalares | Riven + nobres + seleção | Passou |
| 29 | Thorn/Lyra | Reaction Scout | Thorn guarded, Lyra approach | Passou |
| 30 | Thorn/Lyra | Judge escalar sem direct target | Escolheu Thorn; hint perdeu sujeito | Faltava `DIRECT_TARGET` e `actor` no schema |
| 31 | Festa | Reaction Scout | Fernanda guarded, mas delta abstrato | Exigir câmera-observável |
| 32 | Festa | Observable gate | Repetiu interrupção | Exigir novidade contra HISTORY |
| 33 | Festa | Novelty + PENDING | Fernanda cora/desvia/fecha postura | Passou |
| 34 | Moinho | Reaction Scout | Aria guarded, Bron ausente | Passou |
| 35 | Thorn/Lyra | Reaction Scout atualizado | Thorn guarded, Lyra approach | Passou |
| 36 | Thorn/Lyra | Judge com `DIRECT_TARGET` e actor | Escolheu Lyra; sujeito preservado | Passou |
| 37 | Festa | Mesmo Judge final | Escolheu Fernanda | Passou |
| 38 | Moinho | Mesmo Judge final | Escolheu Aria | Passou |
| 39 | Thorn/Lyra | Continuity Scout permissivo | Inventou dever para Lyra | Conhecimento não é autorização |
| 40 | Thorn/Lyra | Exigir dever explícito em prompt | Ainda fabricou dever de Edda | Prompt não fecha conjunto |
| 41 | Thorn/Lyra | `AUTHORIZATIONS=[]` fechado | Candidate `null` | Passou |
| 42 | Academia | Autorização estruturada de Maelis | Início da seleção | Passou |
| 43 | Academia | Judge combinado, repetição 1 | Riven + nobres + seleção | Correto |
| 44 | Academia | Judge combinado, repetição 2 | Mesmo trio | Correto |
| 45 | Academia | Judge combinado, repetição 3 | Mesmo trio; string hint abstrata | Estrutura 3/3; não usar string da LLM |
| 46 | Thorn/Lyra | Reaction Scout, estabilidade 2 | Mesmas tendências | Correto |
| 47 | Thorn/Lyra | Reaction Scout, estabilidade 3 | Mesmas tendências | 3/3 |
| 48 | Festa | Reaction Scout, estabilidade 2 | Fernanda guarded | Correto |
| 49 | Festa | Reaction Scout, estabilidade 3 | Fernanda guarded, Sofia neutral | 3/3 |
| 50 | Moinho | Reaction Scout, repetição | Aria approach | Ambiguidade approach/guarded |
| 51 | Moinho | Reaction Scout, repetição | Aria approach | Mesma direção |
| 52 | Moinho | Reaction Scout, repetição | Aria guarded | Sem convergência direcional |
| 53 | Moinho | Tie-break de menor compromisso, repetição 1 | Aria guarded, olha sem mover | Correto |
| 54 | Moinho | Tie-break, repetição 2 | Relação Aria; átomo atribuído a Milo | Erro estrutural detectável |
| 55 | Moinho | Retry com `VALIDATION_ERROR` | Corrigiu somente actor Milo → Aria | Recuperação passou |

## Prompts finais

### 1. Reaction Scout

```text
Você é REACTION SCOUT universal de roleplay POV.

1. Classifique NPC PRESENTE como approach, avoid, attack_status,
   defend_target, guarded, align_status ou neutral.
   attack_status exige hostilidade explícita; humor, pragmatismo, utilidade
   e ausência de pena não bastam.
2. Em conflito entre approach e avoid/guarded, ou diante de risco físico não
   verificado, use guarded e a MENOR reação não comprometida: orientar
   olhar/postura sem aproximar, afastar, tocar ou agir sobre o risco.
3. Descarte neutral e quem não percebe.
4. Gere átomos novos ligados a PENDING, nunca repetindo HISTORY.
   Apenas olhar, expressão, postura, gesto ou distância física;
   sem estado abstrato, fala, objeto novo ou ACTOR_FINAL.
   align_status só acompanha attack_status;
   defend_target só reage a attack_status.

Retorne JSON:
{
  "relations": [
    {"actor": "...", "tendency": "...", "evidence": "..."}
  ],
  "atoms": [
    {
      "atom_id": "...",
      "actor": "...",
      "tendency": "...",
      "delta": "...",
      "support": ["..."]
    }
  ]
}
```

### 2. Continuity Scout

```text
Você é CONTINUITY SCOUT de narrator_hint.
Ignore reações, atmosfera e física.

Para cada PENDING, owner e autorização DEVEM copiar uma entrada de
AUTHORIZATIONS. Se nenhuma entrada combina exatamente com pending e owner
presente, candidate=null; lista vazia obriga todos null.

Nunca derive autorização de conhecimento, pergunta, capacidade, relação ou
plausibilidade.

Com autorização válida, proponha a menor ação externa que inicia avanço, sem
completar decisão nem inventar conteúdo de fala. owner=ACTOR_FINAL ou
sobreposição com reação => null.

Retorne JSON:
{
  "pending_reviews": [
    {
      "pending": "...",
      "matched_authorization_id": "... | null",
      "owner": "... | null",
      "candidate": {
        "atom_id": "...",
        "actor": "...",
        "tendency": "duty_transition",
        "delta": "...",
        "support": ["..."]
      } | null
    }
  ]
}
```

### 3. Judge

```text
Você é JUIZ FINAL CLOSED-WORLD de narrator_hint.

Valide tendência, entidade, novidade e grounding.
Rejeite ACTOR_FINAL, ausente, conteúdo de fala inventado, objeto novo,
segredo transferido, repetição, estado abstrato, detalhe excessivo e
world_inference.

A saída possui SOMENTE três seleções escalares:

- reaction_seed:
  - se houver attack_status, escolha o mais específico;
  - sem ataque, prefira actor=DIRECT_TARGET;
  - depois, a reação mais diretamente causal.
- reaction_followup:
  - somente com attack_status;
  - escolha UM entre propagação attack_status/align_status ou counter
    defend_target;
  - prefira propagação se o ataque ainda não ocorreu;
  - prefira counter se o ataque já ocorreu.
- continuity:
  - duty_transition com authorization_id e pending;
  - somente se compatível com as reações.

Cada seleção inclui actor e delta.

Retorne JSON:
{
  "reaction_seed": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "reaction_followup": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "continuity": {"atom_id": "...", "actor": "...", "delta": "..."} | null,
  "reason": "..."
}
```

Não solicitar `hint` ao Judge em produção. Compilar deterministicamente.

### 4. Retry de validação

```text
Você é REACTION SCOUT universal.
Corrija sua resposta anterior quando receber VALIDATION_ERROR.
Preserve relações e semântica válidas; altere somente campos inválidos.
ACTOR_FINAL nunca pode aparecer em atoms.
Todo atom.actor deve existir em relations e atom.tendency deve ser idêntica
à relation correspondente.
Retorne somente JSON corrigido.
```

O mesmo padrão serve para erros do Continuity Scout e Judge: enviar resposta
anterior + lista precisa de violações, sem rerodar toda a criação.

## Contrato de entrada recomendado

```json
{
  "actor_final": "character_id",
  "direct_target": "character_id|null",
  "present": ["character_id"],
  "absent": ["character_id"],
  "perception": {
    "character_id": ["event_id"]
  },
  "stimulus": "último acontecimento público normalizado",
  "history_predicates": [
    "ações/predicados recentes já realizados"
  ],
  "pending": [
    {"id": "pending_id", "description": "..."}
  ],
  "authorizations": [
    {
      "id": "authorization_id",
      "owner": "character_id",
      "scope": "qual pending/dever pode iniciar"
    }
  ],
  "participation": {
    "character_id": 0
  },
  "profiles": {
    "character_id": {
      "personality": "...",
      "knowledge_relevant": ["..."]
    }
  },
  "allowed_entities": ["..."]
}
```

### Dados indispensáveis

- `actor_final`: não é “Player”; é somente o personagem que produziu a entrada
  final. Mantém a imersão e impede extensão de agência.
- presença, zonas e percepção já calculadas;
- predicados recentes, não prosa longa;
- perfis canônicos dos NPCs presentes relevantes;
- conhecimento individual relevante;
- participation/saturação;
- estados pendentes explícitos;
- autorizações fechadas;
- conjunto de entidades permitido.

### Blocker real: `AUTHORIZATIONS`

`AUTHORIZATIONS` não pode ser inferido livremente pela mesma LLM. Nos testes,
ela transformou curiosidade e uma pergunta em “dever explícito” para Lyra mesmo
após proibição.

Fontes seguras possíveis:

- papel/dever estruturado no cenário;
- beat/owner estruturado pelo sistema de roteiro;
- estado de plugin com owner explícito;
- regra institucional tipada.

Se o runtime não possui uma fonte estruturada, enviar `AUTHORIZATIONS=[]`.
É melhor perder um avanço automático que fabricar autoridade.

## Validações locais obrigatórias

Estas invariantes não devem depender do modelo:

```text
relation.actor ∈ present
relation.actor != actor_final
atom.actor ∈ relations.actor
atom.actor != actor_final
atom.tendency == relations[atom.actor].tendency
atom.delta não vazio
continuity.authorization_id ∈ input.authorizations.id
continuity.actor == authorization.owner
selected ids existem nos outputs dos scouts
reaction_followup != null somente se reaction_seed.tendency == attack_status
no máximo 1 seed + 1 followup + 1 continuity
```

Também validar localmente contra:

- IDs ausentes;
- entidades não permitidas quando extraíveis;
- Unicode dash conforme normalização global;
- schema JSON estrito;
- tamanho máximo de cada `delta`.

Falha deve disparar retry corretivo com erro preciso. A chamada 55 demonstrou
que isso corrige erro de atribuição sem recriar o beat.

## Resultados de estabilidade

| Componente/caso | Resultado |
|---|---|
| Judge combinado da Academia | mesmos três campos em 3/3 |
| Reaction Scout Thorn/Lyra | mesmas tendências `guarded/approach` em 3/3 |
| Reaction Scout Festa | Fernanda `guarded`; Sofia `neutral/omitida` em 3/3 |
| Reaction Scout Moinho antes do tie-break | 2 approach / 1 guarded |
| Reaction Scout Moinho depois do tie-break | semântica guarded mínima em 3/3; 1 erro estrutural recuperado por retry |
| Continuity Scout sem autorização | `null` quando `AUTHORIZATIONS=[]` |
| Continuity Scout Academia | início da seleção com autorização de Maelis |

## Hints finais compilados

```text
Academia:
Riven revira os olhos e solta uma risada sarcástica;
noble_audience troca murmúrios de desaprovação;
Maelis sinaliza o início da seleção.

Thorn/Lyra:
Lyra inclina-se e estende a mão em direção ao medalhão.

Festa:
Fernanda cora, desvia o olhar brevemente e fecha a postura.

Moinho:
Aria olha para cima e enrijece os ombros.
```

## Recomendação para Claude

1. Não colocar mais essa responsabilidade no prompt atual do Diretor.
2. Não implementar uma única chamada `generate_hint`.
3. Criar um contrato experimental isolado com Reaction Scout e Continuity
   Scout em paralelo, Judge depois e compilador determinístico.
4. Começar atrás de flag/plugin ou harness, ainda fora do turno canônico.
5. Reusar cliente LLM compartilhado e debug JSONL; toda chamada precisa de
   `session_id`, `turn_number` e agent distinto.
6. Só integrar ao turno após replay em mais sessões reais e definição da fonte
   canônica de `AUTHORIZATIONS`.
7. Se integrado, o resultado deve entrar no Diretor como hint de sistema,
   nunca como fato já ocorrido. O Diretor continua validando espaço, percepção
   e routing.

## Limitações

- Os testes medem DeepSeek V4 Flash; outros providers precisam da mesma bateria.
- Reaction Scout ainda gera quantidade variável; o Judge escalar absorve isso.
- Gestos exatos variam, embora a tendência converja.
- O pipeline adiciona duas fases de latência (scouts paralelos, depois Judge).
- Não houve implementação nem teste HTTP do turno completo.
- Não houve teste de compactação/histórico longo.
- `allowed_entities` e `history_predicates` exigem um input builder confiável.

## Arquivos desta pesquisa

- Relatório anterior:
  `.plan/explore-narrator-hint-llm-experiments.md`
- Este handoff:
  `.plan/narrator-hint-generalization-handoff.md`
- Wrapper temporário, não versionado:
  `/tmp/curl_wrapper.py`
- Request temporário, não versionado:
  `/tmp/curl_request.json`
