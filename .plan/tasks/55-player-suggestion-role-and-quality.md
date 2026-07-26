# Task 55 — Readequar sugestões ao kernel Director/Prose/Character

> 🟡 **ENTREGUE COM RESSALVA (2026-07-26)** — branch `refactor/pre-1.0-cleanup`.
>
> O papel próprio existe (`src/agents/suggest.py`), o contexto deixou de ser
> onisciente e o custo caiu. **Mas o critério de fechamento pede evidência de
> "opções mais diversas", e essa parte do meu portão pré-registrado REPROVOU.**
> A task fica aberta por causa disso; medições no fim do arquivo.

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

## Portão curl-first: o que passou e o que não passou

Métricas e regra de decisão pré-registradas **antes de rodar** (no cabeçalho de
`suggest_ab.py`). Payload atual replayado byte a byte de uma chamada ruim real
da sessão `1cad8c55`; a variante nova passa pelo adapter de produção, então é
literalmente o que o servidor postaria. 3 runs por variante.

| Métrica | Atual (Narrador onisciente) | Nova (in-character) | Regra | Veredito |
|---|---:|---:|---|---|
| M1 pensamentos privados alheios no request | 9 | **0** | tem de ser 0 | ✅ |
| M2 opções distintas por resposta (média) | 3,0 | 3,0 | ≥ atual | ✅ |
| M3 similaridade entre chamadas | **0,0548** | 0,0836 | não piorar | ❌ **REPROVOU** |
| M4 caracteres do request | 42.764 | **14.978** | menor | ✅ (−65%) |
| M4 `max_tokens` | 24.576 | **1.024** | menor | ✅ (−96%) |

**M3 reprovou e eu não vou fingir o contrário.** A variante nova repete mais
entre chamadas consecutivas — que é justamente o sintoma que abriu esta task.

## O que a segunda rodada mostrou sobre a própria métrica

Rodei uma iteração (A = prompt shippado, B = A mais uma regra exigindo três
alvos diferentes: uma pessoa, o cenário, ninguém):

| Variante | M3 |
|---|---:|
| A (shippado), 1ª medição | 0,0836 |
| A (shippado), 2ª medição | 0,0955 |
| B (+regra de alvo) | 0,0815 |

**A mesma configuração mediu 0,0836 e 0,0955 — ruído de ±0,012 entre execuções
idênticas.** A diferença que eu estava usando como portão (0,0548 → 0,0836 =
0,029) é só o dobro do ruído, com n=3. Ou seja: M3 com 3 runs não sustenta uma
decisão de ship/no-ship com confiança, e eu montei o portão em cima de um
instrumento fraco demais para ele.

B mediu melhor que as duas medições de A, mas com uma amostra só. **Não shippei
a regra B**: uma amostra dentro da banda de ruído não é evidência.

Em termos absolutos todos os valores são baixos (< 0,10 de Jaccard). O que dá
para afirmar com honestidade: a variante nova **não é pior em diversidade dentro
de uma resposta** (M2 = 3/3 nas 6 execuções) e **é dramaticamente melhor em
vazamento e custo**. O que **não** dá para afirmar é que ela entrega opções mais
diversas entre chamadas — que é o que o critério de fechamento pede.

## Por que shippei mesmo assim

O que foi para o código são os itens que passaram: fronteira de contexto, papel,
orçamento. Nada do que reprovou virou justificativa para mudar o prompt.

Se M3 fosse um portão de segurança eu teria revertido. Ele é um portão de
qualidade, e a alternativa de mantê-lo era continuar mandando 9 pensamentos
privados alheios e 24.576 tokens de budget por três linhas — uma troca ruim.

## O que falta para fechar

1. **Um instrumento decente para M3.** n=3 não serve. Precisa de ~10 runs por
   variante, ou de uma métrica menos sensível a ruído lexical (por exemplo
   distância entre as *intenções*, julgada por um avaliador, não por Jaccard).
2. **Decidir sobre a regra B** com amostra suficiente.
3. Uma sessão real longa medindo repetição de sugestões ao vivo, não em replay.

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
