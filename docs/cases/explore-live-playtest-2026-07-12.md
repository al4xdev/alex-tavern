# Explore: playtest real pós-remediação

**Data:** 2026-07-12
**Escopo:** 20 turnos do roteiro Thorn/Lyra, sugestão, duas compactações com restore entre elas,
turno pós-compactação e undo
**Modelo:** Gemma 4 26B A4B QAT, servido pelo llama.cpp local
**Armazenamento isolado:** `/tmp/roleplay-report-playtest.DmyEbG`
**Sessão:** `89c21c6c`

## Artefatos

- Resultado estruturado: `/tmp/roleplay-report-playtest.DmyEbG/playtest-results.json`
- Estado final: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.json`
- Backup pré-compactação: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.kb_0.json`
- Log bruto: `/tmp/roleplay-report-playtest.DmyEbG/sessions/89c21c6c.debug.jsonl`
- Roteiro: script manual privado de playtest do projeto

## Resumo da execução

| Métrica | Resultado |
|---|---:|
| Turnos principais | 20 |
| Turnos pós-compactação | 1 |
| Registros LLM | 40 |
| Sucessos | 40 |
| Erros/retries | 0 |
| Chamadas Narrator | 21 |
| Chamadas Character/Lyra | 16 |
| Chamadas Historian | 2 |
| Chamadas Suggest | 1 |
| Maior prompt | 32.550 caracteres |
| Maior duração de chamada | 10.582 ms |
| Registros antes da compactação | 75 |
| Registros removidos/mantidos | 45 / 30 |
| Marcadores `turn_input` | 21 |

O prompt do Narrador cresceu de 4.066 caracteres no turno 1 para 32.550 no turno 20. Mesmo assim,
todas as chamadas terminaram na primeira tentativa. A maior duração, 10,6 segundos, ficou muito
abaixo tanto do timeout usado no playtest (90 s) quanto do padrão do produto (60 s). Os retries
observados do turno 14 em diante no playtest original não reapareceram.

## Bugs objetivos

### 1. `physical_facts` pode virar uma chave contendo JSON serializado

**Severidade observada:** alta para integridade do estado.

No turno 20, o Narrador retornou:

```json
{
  "location": "Watchtower Base",
  "physical_facts": "{\"atmosphere\": \"stifling, vibrating, and freezing\", \"dust\": \"falling ash-like particles\", \"scent\": \"cloying, rotting lilies\"}"
}
```

O estado persistiu literalmente:

```json
{
  "atmosphere": "stifling, vibrating, and freezing",
  "physical_facts": "{\"atmosphere\": ...}"
}
```

Assim, `dust` e `scent` não viraram fatos consultáveis no turno 20; o contêiner apareceu dentro de
si mesmo como string. No turno 21, o modelo voltou a emitir as duas chaves de forma plana, mas a
chave serializada incorreta permaneceu ao lado delas.

A forma é aceita porque `scene_update.additionalProperties` permite qualquer chave com valor
string/null (`src/agents/narrator.py:79-86`). O runner copia toda chave que não seja `location` ou
`time_of_day` diretamente para `game.scene.physical_facts` (`src/runner.py:514-520`).

### 2. Normalização de travessão provoca uma falsa troca de localização

**Severidade observada:** média; houve mutação real, sem perda neste caso.

O preset começou em `Old Mork's Tavern — main hall, dim lighting`. No turno 1, o output bruto
repetiu exatamente esse local. Antes de aplicar o estado, a normalização converteu o travessão em
vírgula (`src/agents/narrator.py:298-303` e `src/llm/client.py:32-34`).

O runner comparou a string normalizada com a string original, interpretou a diferença de
pontuação como mudança de local e executou `physical_facts.clear()`
(`src/runner.py:503-508`). Nenhum fato se perdeu porque o modelo também repetiu iluminação,
público, clima e porta naquele output. O estado, entretanto, mudou o nome do local e percorreu o
caminho de transição de cena sem que a cena tivesse mudado semanticamente.

### 3. Character executa/descreve ações físicas em todas as respostas observadas

**Severidade observada:** alta em relação ao modelo de papéis documentado.

O `AGENTS.md` define que Character pode somente falar e pensar, nunca executar ou descrever ação
física própria ou alheia. Nos 20 turnos houve 15 respostas de Lyra, e todas incluíram ação ou
descrição física própria. A resposta pós-compactação repetiu o padrão.

Exemplos:

- turno 2: `I say, leaning closer to the pulsing metal`;
- turno 8: `I mutter, frantically stuffing my scrolls into my satchel`;
- turno 14: `my fingers trembling slightly as I pull a minor illumination stone from my belt`;
- turno 19: `I stammer, my eyes wide as I stare at the vibrating wall`.

O próprio docstring do formatter confirma que só diálogo deve chegar ao Character porque apenas
o Narrador narra/descreve/age (`src/agents/character.py:47-52`). O prompt proíbe narrar ações como
fato, mas também pede apenas primeira pessoa e diálogo (`src/agents/character.py:20-36`). O output
de texto livre não aplica validação posterior para separar fala, pensamento e ação.

### 4. A localização mudou sem transição narrativa no turno 17

**Severidade observada:** média.

No turno 16, o estado estava em `Watchtower Interior`. No turno 17, Thorn declarou o plano para o
amanhecer, guardou o dispatch e procurou suprimentos no cômodo. A narração já passou a chamar o
ambiente de `tower base`, e `scene_update.location` mudou para `Watchtower Base`, sem saída,
descida ou outra transição espacial descrita.

A alteração também limpou `light_level`, pois toda troca de localização descarta os fatos da cena
anterior. O novo estado reteve apenas `atmosphere`.

## Fragilidades qualitativas reproduzidas

### Ponto de vista em segunda pessoa troca implicitamente para Lyra

Nove das 21 narrações contêm `you`/`your` enquanto Thorn é descrito em terceira pessoa. Em vários
casos, a segunda pessoa só pode ser Lyra:

- turno 18: `The illumination stone in your hand ... as your hands shake`, enquanto Thorn está
  com o ouvido contra a parede e a pedra pertence a Lyra;
- turno 19: `your pale blue light`;
- turno 20: `your illumination stone`;
- turno 21: `your fingers ... around the staff`.

Não houve vazamento da palavra `Player`, mas a narração exibida ao humano que controla Thorn muda
o foco para o corpo e os objetos de Lyra sem marcar a troca de ponto de vista.

### Consequências imediatas continuam podendo ser adiadas

- turno 6: Thorn ordena que Mork barre a porta. Mork pausa com o pano na mão, mas não barra a
  porta; `door` continua `closed` apenas por já estar assim no preset;
- turno 19: Thorn conta regressivamente e ordena que Lyra quebre o ward. A narração troca o som de
  arranhado por batidas e Lyra diz que está pronta, mas o ward não é quebrado;
- turno 20 muda para o mapa sem resolver o ward ou o que existe atrás da parede.

A regra de resolver a consequência antes de ampliar a atmosfera existe no prompt do Narrador,
mas os dois padrões do relatório original reapareceram.

### Character ainda inventa origem ausente

No turno 5, Lyra responde `We found it tucked away in a ruin`. Seu conhecimento contém apenas que
o medalhão foi encontrado e emite uma aura fraca; roteiro, estado e contexto do turno não fornecem
uma ruína. É o mesmo tipo de invenção observado no playtest original.

As duas compactações não promoveram a ruína para o resumo, sinal de que as regras de proveniência
do Historian funcionaram melhor do que no relatório original.

### Narrator ainda afirma estados internos

Exemplos observados:

- turno 5: `desperate, piercing intensity`;
- turno 17: `grim, mechanical purpose` e `his focus remaining on the task`;
- turno 20: `Thorn ignores it, his focus entirely consumed by the paper`.

Esses trechos atribuem emoção, propósito ou foco interno, apesar da regra de descrever apenas
evidência observável.

### Mood updates redundantes

O Narrador emitiu oito objetos de atualização de humor. Três não mudaram o valor persistido:

- turno 10: C2 `anxious` para `anxious`;
- turno 14: C2 `anxious` para `anxious`;
- turno 19: C2 `terrified` para `terrified`.

Houve cinco transições reais: C1 para `determined`, C2 para `anxious`, C1 para `devastated`, C1
de volta para `determined` e C2 para `terrified`. A frequência é muito menor que as 18
atualizações em 20 turnos do relatório original, mas a instrução de omitir personagens sem
mudança ainda não é obedecida de forma consistente.

## Comportamentos confirmados como corretos

- Nenhum prompt contém `Player` ou `SPEAKER=Player`.
- Todos os 21 overrides solicitados foram registrados e validados corretamente em `turn_input`.
- Todas as 40 chamadas possuem métricas e `attempt_number=1`; não houve erro vazio ou retry.
- As mudanças reais de local limparam fatos da cena anterior: taverna, corredor, beco, ruas e
  torre não vazaram portas/clima/iluminação entre si.
- As notas de compactação usaram somente `C1` e `C2`.
- O turno 21 recebeu `STORY SO FAR`, a nota canônica de Lyra e somente sua própria nota.
- Lyra conseguiu listar medalhão, dispatch e floresta após a compactação.
- A primeira compactação removeu 45 registros e manteve 30, correspondentes exatamente aos oito
  turnos 13-20 desta execução.
- Restore recuperou os 75 registros anteriores; uma nova compactação voltou a 30.
- Undo do turno 21 restaurou história, cena e humores do estado pós-compactação.
- Não houve frase completa repetida literalmente entre narrações nem entre respostas de Lyra.
- O log bruto contém um travessão (na localização do turno 1); o conteúdo gerado persistido foi
  normalizado sem travessão/en dash.
- O diretório real `.data` permaneceu com 38 arquivos e hash agregado
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f`.

## Observações sem classificação de bug

Compactar, restaurar e compactar novamente o mesmo estado produziu dois resumos semanticamente
próximos, mas não idênticos. As notas também mudaram de redação. O comportamento é compatível com
geração em temperatura 1.0, mas demonstra que compactação repetida não é semanticamente
idempotente mesmo quando o estado de entrada é idêntico.

Nenhum dos cinco turnos com roteamento automático escolheu C1, o personagem controlado. A trava
de agência desse ramo continua coberta por testes e playtests anteriores, mas não foi exercitada
ao vivo nesta execução específica.

## Open Questions

- A narração deve manter sempre terceira pessoa ou existe intenção de permitir segunda pessoa
  direcionada a um personagem que não é o controlado?
- `physical_facts` deve ser tratado como nome reservado de contêiner no schema/delta ou seu uso
  literal como fato é considerado válido?
- A variação entre duas compactações do mesmo estado é aceitável para o fluxo de restore/retry ou
  deve ser tratada apenas como característica observável do modelo?
