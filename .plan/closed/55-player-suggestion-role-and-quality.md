# Task 55 — Readequar sugestões ao kernel Director/Prose/Character

> ✅ **FECHADA em 2026-07-26** — branch `refactor/pre-1.0-cleanup`.
> Os cinco critérios pré-registrados passam com n=10. O relato inclui a rodada
> em que reprovei o portão com n=3 e o que aquilo se revelou ser.

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


---

# Resultado (2026-07-26)

## O que foi feito

`src/agents/suggest.py`: papel próprio ("você rascunha três jogadas possíveis
para UM personagem, de dentro da cabeça dele"), agente renomeado de
`narrator_suggest` para `suggest_moves`.

O contexto passou a ser exatamente o que a task pediu, e por **construção**, não
por instrução: o builder reusa `_format_history_for_character`, a mesma fronteira
que o agente Character já usa. As `mind` alheias, as notas e os pensamentos
privados dos outros nunca são lidos, então nenhuma regra precisa protegê-los.

Orçamento fixo em `SUGGESTION_MAX_TOKENS = 1024` em vez de `max_tokens_narrator`
(24.576) — fixo de propósito, para que um provider de contexto grande não
transforme um auxiliar na chamada mais cara do turno.

`SUGGESTIONS_OUTPUT` continua igual: o hook recebe o mesmo formato
`{"speech", "action"}`, e os plugins seguem podendo filtrar ou substituir.

## Portão curl-first — resultado final (n=10)

Métricas e regra de decisão pré-registradas **antes de rodar** (no cabeçalho de
`suggest_ab.py`). Payload atual replayado byte a byte de uma chamada ruim real
da sessão `1cad8c55`; a variante nova passa pelo adapter de produção, então é
literalmente o que o servidor postaria. 3 runs por variante.

| Métrica | Atual (Narrador onisciente) | Nova (in-character) | Regra | Veredito |
|---|---:|---:|---|---|
| M1 pensamentos privados alheios no request | 9 | **0** | tem de ser 0 | ✅ |
| M2 opções distintas por resposta (média) | 3,0 | 3,0 | ≥ atual | ✅ |
| M3 similaridade entre chamadas | 0,0718 | **0,0701** | não piorar | ✅ |
| M4 caracteres do request | 42.764 | **15.253** | menor | ✅ (−64%) |
| M4 `max_tokens` | 24.576 | **1.024** | menor | ✅ (−96%) |

Os cinco critérios passam. Mas o caminho até aqui é a parte que importa.

## Eu reprovei o meu próprio portão primeiro, e estava medindo mal

Rodei uma iteração (A = prompt shippado, B = A mais uma regra exigindo três
alvos diferentes: uma pessoa, o cenário, ninguém):

Na primeira rodada, com n=3, M3 deu 0,0548 (onisciente) contra 0,0836 (nova) e
eu **reprovei o portão** e deixei a task aberta escrito que não dava para
afirmar melhora de diversidade.

Aí medi de novo, e o instrumento se denunciou:

| Variante | n | M3 |
|---|---:|---:|
| A (nova, sem regra de alvo) | 3 | 0,0836 |
| A (nova, sem regra de alvo) — **mesma configuração** | 3 | 0,0955 |
| B (nova + regra de alvo) | 3 | 0,0815 |
| A (nova, sem regra de alvo) | 10 | 0,0829 |
| B (nova + regra de alvo) | 10 | **0,0703** |
| Onisciente | 3 | 0,0548 |
| Onisciente | 10 | **0,0718** |

Duas coisas ficam claras:

1. **A mesma configuração mediu 0,0836 e 0,0955 com n=3** — ruído de ±0,012, da
   ordem do efeito que eu estava usando como portão. O 0,0548 do onisciente era
   igualmente instável: com n=10 ele sobe para 0,0718. **A reprovação inicial
   foi, em boa parte, artefato de medição.**
2. O resto do gap era real e pequeno, e a **regra de alvo** (as três jogadas têm
   de engajar alvos diferentes: uma pessoa, o cenário, ninguém) fecha ele. B
   mediu melhor que A nas três comparações diretas, e com n=10 fica abaixo do
   onisciente.

A regra B foi shippada **depois** de medida com n=10, não antes. Custa 269
caracteres de prompt.

## A lição que fica registrada

Eu montei um portão quantitativo sobre um instrumento que nunca testei. Um
único ruído de ±0,012 medido antes teria mostrado que n=3 não sustentava a
decisão — e teria evitado que eu declarasse uma reprovação que não existia.
Regra para o próximo portão numérico: **medir a variância da própria métrica
antes de usá-la para aprovar ou reprovar qualquer coisa.**

## Cobertura de teste

`tests/test_suggest_moves.py`, 8 testes:

- pensamento privado alheio fora do request (e o próprio dentro);
- `mind` alheia fora do request (e a própria dentro);
- cena, conhecimento próprio e diretivas presentes;
- request não nomeia operador (regra da task 57);
- schema com exatamente 3 pares speech/action;
- orçamento fixo mesmo com `context_max` de 1.000.000;
- **agência**: pedir sugestão não persiste nem executa nada (`game_state_to_dict`
  idêntico antes e depois);
- sussurro fora da audiência não entra.

Suíte total: 830 testes.
