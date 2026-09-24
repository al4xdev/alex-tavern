**O prompt já exigia movimento efetivo e proibia teleporte em T21. A lacuna é a ausência de um vínculo explícito e verificável entre cada `zone_moves` e o evento que sustenta aquela transição.** Não cabe atribuir o caso apenas a uma instrução esquecida.

No payload arquivado, `debug.jsonl:242`, `request.messages[0].content`:

| Linhas internas | Trecho literal |
|---|---|
| 52–53 | `"zone_moves": null OR an object mapping character_id to the zone they physically moved to THIS beat (an attempted movement succeeds).` |
| 26–29 | `"perception_events": the typed record of what happens THIS beat, resolving the last HISTORY event (an attempted action succeeds, fails, or twists; a speech lands; the environment moves). This is the ONLY substrate the renderer and the characters receive, so cover everything that matters.` |
| 12–13 | `This is factual blocking, not narration or hidden motives. Every later decision must agree with it.` |
| 79–80 | `A character's action is an attempt until narration confirms its outcome. Preserve uncertainty.` |
| 140–143 | `Meaningful travel takes multiple beats when the fiction requires it and ends only after a later explicit arrival. Never teleport someone, invent a convenient connection, or skip the journey just to bring characters together.` |

Essas regras permanecem no builder atual: `src/agents/narrator.py:81–87`, `101–104`, `129–136`, `167–168` e `219–225`.

Há também uma tensão textual já existente e preservada: `CANON RECONCILIATION` manda reconciliar uma autodeclaração incompatível com o estado por `zone_moves` (arquivo atual, linhas 205–212; payload, 122–129). Assim, o campo também serve à correção da representação espacial, embora sua definição diga “physically moved [...] THIS beat”. **Isso não justifica T21:** a última ação de Liora identificada no rastreamento a mantinha no corredor; não fornecia uma autodeclaração de saída.

Comparei o builder executado isoladamente com os mesmos IDs e as mesmas diretivas do cenário arquivado. As diferenças no texto produzido pelo builder tratam de `audible_speech` e autoria do diálogo. **Não houve mudança nos trechos de movimento, reconciliação ou viagem acima.** Idioma, pontuação e instrução técnica de JSON aparecem acrescentados no payload por outras camadas, ainda presentes em `src/llm/client.py:79–96` e `src/llm/adapters/deepseek.py:62–66`.

Em T21, a resposta manda `zone_moves.C7 = "Academia Real do Primeiro Sino, Salão dos Quatro Arcos"`. Os quatro eventos descrevem parede rompida, brilho apagado, névoa e teto desabando atrás de Riven. **Nenhum descreve Liora saindo, sendo retirada ou chegando ao salão.** O evento “forçando todos a recuarem” ocorre no salão e não explica atravessar a passagem bloqueada desde o corredor.

O validador permite essa combinação porque:

- O schema aceita `zone_moves` como objeto de strings (`narrator.py:384–387`), sem referência a um evento.
- A sanitização verifica personagem existente/presente e destino textual de até 60 caracteres (`:818–834`).
- `validate_perception_events` verifica forma, sujeitos e testemunhas (`perception.py:117–141`), sem relacionar seus eventos aos movimentos.
- O Runner grava o destino aceito diretamente (`runner.py:1396–1397`).

Portanto, **“personagem e destino válidos” só estabelece que o comando pode ser representado**, não que a passagem foi possível ou ocorreu. Não existe exigência literal “cada movimento deve citar um evento de saída/chegada”, nem estrutura para registrar essa ligação. Já a exigência geral de movimento ocorrido, continuidade espacial e cobertura dos acontecimentos existia e foi descumprida.

Consultei as specs ativas. A tarefa **69** conserva o escopo de transições físicas e decisão de armazenamento (`.plan/tasks/69-physical-state-as-closed-transition.md:251–272`). A **79** distingue blocking de posição canônica: percepção não pode consumir blocking, e persistência continua adiada (`.plan/tasks/79-blocking-as-durable-state.md:445–454`). Logo, este achado não autoriza promover automaticamente blocking a posição, nem escolher uma implementação de validação. Também não demonstra que acrescentar uma frase ao prompt resolveria o problema.

Nenhum arquivo alterado; nenhuma chamada LLM realizada.
