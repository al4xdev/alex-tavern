# Task 55 — Readequar sugestões ao kernel Director/Prose/Character

> **Status (2026-07-26): ABERTA — gate pré-1.0.**
> O sistema de “sugerir uma jogada” antecede a separação dos papéis narrativos.
> A sessão real `1cad8c55` confirmou baixa diversidade, contexto onisciente e
> custo desproporcional. Não há evidência de regressão causada pela branch
> `refactor/pre-1.0-cleanup`.

## Sintoma observado

As sugestões para Link ficaram presas às mesmas variações:

- abrir ou preparar um microportal;
- redirecionar a névoa;
- observar o portal/ferida;
- pedir autorização a Garran ou Maelis.

Embora o prompt exija três opções distintas, as chamadas consecutivas repetem
quase a mesma jogada com pequenas trocas de formulação. Isso reduz a utilidade
do recurso justamente quando a cena já está semanticamente estagnada.

## Evidência da sessão

Em `.data/sessions/1cad8c55/debug.jsonl`:

- 7 chamadas `narrator_suggest`;
- 362.150 caracteres de prompt no total;
- 90.535 tokens estimados no total;
- máximo de 65.520 caracteres / 16.380 tokens em uma chamada;
- 35,3 segundos acumulados de latência;
- as opções dos turnos 4, 5, 6 e 10 reiteram “microportal + névoa”.

Todas as sete chamadas concluíram sem erro de provider ou schema. O defeito é
de contexto/papel/qualidade, não de transporte.

## Causa arquitetural confirmada

O recurso ainda é implementado como um Narrador onisciente:

- `src/agents/narrator.py:701-720` declara literalmente “You are the Narrator”
  e “You know EVERYTHING about the world”;
- `src/agents/narrator.py:867-917` reutiliza `_build_user_prompt`, o contexto
  completo do Narrador;
- o payload real contém todos os 20 personagens, seus segredos e os registros
  `PRIVATE THOUGHT` de personagens alheios;
- `src/runner.py:1357-1368` entrega `game.characters` e `game.history` completos;
- a chamada continua nomeada `narrator_suggest`.

Isso não corresponde ao kernel atual. A sugestão é uma ajuda efêmera para a
agência do personagem controlado: ela não precisa decidir o mundo como Director
nem conhecer segredos que o personagem não poderia usar.

O `git blame` data o prompt de 11–13 de julho. Na branch de refatoração, a
mudança relevante apenas passou a chamada pelo cliente compartilhado e pelos
hooks tipados; não alterou o contexto narrativo.

## Fronteiras que a task precisa definir

- papel próprio da sugestão, sem fingir ser Director, Prose ou Character;
- contexto limitado à `mind` do personagem controlado, nota/perspectiva própria,
  cena perceptível, falas públicas e pensamentos próprios;
- nenhuma `mind`, nota ou pensamento privado alheio;
- nenhum roteiro, estado omnisciente ou identificação do humano como Player;
- três opções materialmente diferentes, não três paráfrases da mesma tática;
- opções como rascunhos editáveis de fala/ação, sem tomar decisão pelo humano;
- coerência com as limitações físicas e o conhecimento atual do personagem;
- orçamento pequeno e estável, sem serializar o elenco inteiro.

A relação com `SUGGESTIONS_OUTPUT` precisa permanecer explícita: plugins ainda
podem filtrar/substituir o resultado, mas o contrato nativo entregue ao hook já
deve respeitar as fronteiras acima.

## Validação obrigatória

Aplicar a regra curl-first do projeto antes de escolher prompt ou contexto.

1. Pré-registrar métricas e regra de decisão.
2. Extrair uma chamada ruim real de `debug.jsonl`.
3. Comparar 3–4 runs por variante, mudando uma variável por vez.
4. Medir:
   - vazamento de conhecimento privado: alvo 0;
   - opções materialmente distintas por resposta;
   - repetição entre chamadas consecutivas;
   - fidelidade às limitações de Link;
   - tokens e latência.
5. O replay final deve usar o builder de produção exatamente como será enviado.

Cobertura mínima:

- teste de fronteira provando que pensamentos/segredos alheios não entram;
- teste de agência: nenhuma sugestão é persistida ou executada automaticamente;
- teste de schema com exatamente três itens;
- teste de lock e hook existente preservado;
- boundary HTTP real do botão de sugestão;
- inspeção do request, resposta bruta e debug log.

## Critério de fechamento

A task fecha quando o recurso tiver ownership compatível com o kernel atual,
contexto não onisciente, custo delimitado e evidência real de que entrega opções
mais diversas sem inventar conhecimento ou exercer a agência humana.
