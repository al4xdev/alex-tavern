**A mudança canônica nasce numa proposta contraditória do Director em T21 e é aplicada pelo Runner.** T34 perpetua essa posição; não é o primeiro ponto da divergência.

Todos os caminhos de evidência abaixo são relativos a `plans/artifacts/repetition-battery/base-P1-r2/sessions/8bd4d0f1/`.

| Etapa | Evidência |
|---|---|
| T19: entrada válida | `debug.jsonl:211`, resposta aceita: evento “Liora [...] cruza a luz âmbar e entra na passagem”; `zone_moves.C7 = "corredor interno da passagem secreta"`. Snapshot de T19 em `state.json:197155` registra exatamente esse destino. |
| T20: permanece presa | `debug.jsonl:227`, tentativa 2 aceita: o clarão derruba Liora, a entrada desmorona e Riven anuncia “Liora está presa!”. `zone_moves` move somente C13 para junto dos escombros. Snapshot T20 em `state.json:214267`: C7 no corredor. |
| T21: entrada ainda correta | `debug.jsonl:242`, `request.messages[1].content`, linha interna 283: corredor com `occupants: Liora Celestria`. Linha 284: Riven junto aos escombros. Portanto a posição correta chegou ao Director. |
| **T21: proposta divergente** | Na mesma linha JSONL 242, `response.scene_blocking.character_zones.C7` passa para `"Salão dos Quatro Arcos, junto aos escombros da passagem"` e **`response.zone_moves.C7` determina `"Academia Real do Primeiro Sino, Salão dos Quatro Arcos"`**. Nenhum dos quatro `perception_events` narra saída ou resgate de Liora; eles descrevem névoa e colapsos. |
| Aplicação | Primeiro registro persistido de T21, `history[187]`, tem C7 no salão em `state.json:231322`. O pedido T22, `debug.jsonl:252`, linhas internas 290–292 de `messages[1].content`, já mostra Liora no salão e corredor vazio. |
| Persistência até T34 | Depois de T21 não há outra `zone_moves.C7` até o pedido T34. `debug.jsonl:395`, pedido, linhas internas 411–413: Liora no salão, corredor vazio. |

Há uma armadilha relevante: **T20 possui outra resposta em `debug.jsonl:226`**, que narra Liora saindo e propõe movê-la ao salão. Essa resposta tem `error_type = "JSONDecodeError"` e `attempt_number = 1`. A resposta aplicada é a tentativa 2, linha 227, que mantém Liora presa. A saída da tentativa rejeitada não pode ser tratada como ficção confirmada.

O caminho determinístico atual é:

- `src/agents/narrator.py:818–834` sanitiza `zone_moves`: personagem existente e presente, destino não vazio, até 60 caracteres. O destino de T21 tem 54 caracteres e satisfaz esses critérios.
- `src/runner.py:1371–1380` remove apenas a alteração global de `scene_update.location` quando o movimento é parcial.
- `src/runner.py:1396–1397` executa diretamente `game.scene.positions[moved_id] = zone`.
- `src/perception.py:171–184` constrói os ocupantes do pedido seguinte a partir de `scene.positions`. Assim o salão de T34 é consequência do valor persistido, sem inferência da prosa.

**O blocking posterior acrescenta uma segunda divergência, mas não explica a origem.** T25 (`debug.jsonl:288`), T26 (`:300`), T31 (`:358`) e T33 (`:382`) colocam C7 no corredor em `scene_blocking.character_zones`, sem `zone_moves.C7`. T33 ainda confirma em `perception_events`: “Liora permanece presa dentro do corredor bloqueado”. Isso não modifica a posição canônica. O snapshot T33 continua no salão (`state.json:450690`).

Limites: o checkout atual é posterior à sessão. Consultei também `git show 2eabc81`, último commit anterior ao início registrado do run: `narrator.py:729–745` tem a mesma sanitização; `:758–760` descarta `scene_blocking`; `runner.py:1107–1108` aplica diretamente os movimentos. Isso corrobora o caminho, mas não certifica a árvore exata executada. O código atual conserva blocking apenas para o renderer daquele turno. Os registros demonstram a proposta T21 e sua persistência; não demonstram por que o modelo a produziu, nem a frequência desse comportamento. Não houve replay ou alteração de arquivos.
