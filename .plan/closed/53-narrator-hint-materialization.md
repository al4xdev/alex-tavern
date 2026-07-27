# Task 53 — Materialização confiável de `narrator_hint`

> ✅ **FECHADA em 2026-07-26** (branch `refactor/pre-1.0-cleanup`).
> A causa foi reproduzida com os payloads reais dos turnos 7 e 9, e não era a
> instrução: era o **conteúdo**. Um evento plausível materializa 4/4 com o prompt
> antigo; o dragão materializa 1/4. Correção medida e shippada; relatório no fim.

## Objetivo

Investigar por que um `narrator_hint` que chega intacto ao prompt do Director pode
desaparecer antes de virar `perception_events`, e definir evidência suficiente para
fechar o contrato de que um evento manual enviado pelo humano realmente entra na
próxima narração.

## Evidência real que abriu a task

Sessão `.data/sessions/1cad8c55`, provider `deepseek`, modelo
`deepseek-v4-flash`, em 2026-07-26:

1. Turno 7:
   - `turn_input.input.narrator_hint = "Um dragão aparece do nada"`;
   - `skip = true`;
   - `turn_input_effective` preservou o mesmo valor;
   - o request do `director` continha:
     `UPCOMING EVENT (incorporate this into your narration):`
     seguido do hint;
   - nenhum dos seis `perception_events` mencionou o dragão;
   - as duas chamadas de `prose` do beat narraram somente a figura encapuzada,
     a névoa, Maelis e o portal.
2. Turno 9:
   - `turn_input.input.narrator_hint = "Um dragão surge do nada"`;
   - `skip = true`;
   - `turn_input_effective` preservou o mesmo valor;
   - o request do `director` voltou a conter o bloco `UPCOMING EVENT`;
   - os três `perception_events` cobriram apenas a luz de Elowen, a ferida e a
     expansão do portal;
   - o `prose` não recebeu nem narrou o dragão.

O texto “das neblinas” lembrado pelo usuário não aparece nos dois payloads
persistidos; os valores acima são os textos exatos registrados.

## Localização atual da perda

O caminho observado é:

```text
mobile/API
  → turn_input
  → turn_input_effective
  → narrator_hint no prompt do Director
  → Director omite o evento de perception_events
  → validação estrutural aceita a resposta
  → Prose, deliberadamente cego, não recebe o hint
  → pending_hint é limpo após o beat
```

Pontos de código:

- `src/static/app.js`: envia `narrator_hint`;
- `src/runner.py::_resolve_beat_hint`: preserva o hint humano com precedência;
- `src/agents/narrator.py::_build_user_prompt`: escreve o bloco
  `UPCOMING EVENT`;
- `src/agents/narrator.py::narrate`: valida schema, speakers, percepção e
  confidencialidade, mas não materialização semântica do hint;
- `src/runner.py::player_turn`: limpa `pending_hint` depois do primeiro beat.

Os testes atuais comprovam transporte e presença textual no prompt
(`tests/test_integration.py`), mas não comprovam que o resultado validado contém
o evento nem que o Prose o narra.

## Não confundir com o replan do roteiro

O replan visto na mesma sessão não foi provocado pelo dragão:

- ocorreu no turno 6, antes dos hints dos turnos 7 e 9;
- foi registrado como `action="act_deadline"` e `reason="clock"`;
- as avaliações dos turnos 7 a 10 registraram `action="none"` e
  `reason="in_progress"`.

Essa distinção deve permanecer coberta na análise para não atribuir ao hint uma
mutação de roteiro que o log contradiz.

## Perguntas da investigação

- A omissão se reproduz 3–4 vezes com o payload real isolado, variando somente
  a instrução/posição do contrato do hint?
- O conflito dominante vem da prioridade dada à consequência final de
  `HISTORY`, das diretivas longas de cenário, do roteiro, do limite de seis
  eventos ou de outra parte observável do prompt?
- Um evento menos extremo que o dragão também é omitido no mesmo payload?
- Como distinguir cumprimento semântico de mera cópia lexical, preservando
  paráfrases legítimas?
- Qual boundary deve possuir a garantia: validação/retry do Director,
  composição determinística de um `perception_event`, ou outro contrato que
  mantenha o Prose cego e a visibilidade correta?
- Em `skip + narrator_hint` com burst, o evento deve ser consumido exatamente
  uma vez no primeiro beat, inclusive após retry?
- Que evidência e log tornam uma omissão futura diagnosticável sem precisar
  reler o prompt inteiro?

## Protocolo de investigação

Seguir a regra curl-first de `AGENTS.md`:

1. Extrair o request real do `director` nos turnos 7 e 9.
2. Pré-registrar a regra de decisão antes das chamadas.
3. Fazer 3–4 replays por variante, alterando somente um elemento do contrato.
4. Usar a posição final real do texto no builder de produção; posição diferente
   conta como variante diferente.
5. Contar materializações e omissões, não escolher um exemplo favorável.
6. Só então comparar boundaries possíveis e registrar o custo em retries,
   visibilidade, persistência e replay.

## Critérios para encerrar a investigação

- [x] Causa reproduzida ou delimitada com payload real e contagem de 3–4 runs
      por variante.
- [x] Resultado separado por hint manual, hint automático e
      `skip + narrator_hint`.
- [x] Contrato de consumo único e de visibilidade escrito sem expor o hint
      diretamente ao Prose.
- [x] Lacuna dos testes atuais demonstrada com um teste que falha no
      comportamento observado, ainda que a implementação seja tratada depois.
- [x] Relação com roteiro confirmada como independente, salvo nova evidência
      contrária.
- [x] Achados registrados nesta task antes de qualquer decisão de implementação.



---

# Resultado (2026-07-26)

## A pergunta que decidiu tudo

A task listava várias hipóteses (posição do bloco, diretivas longas, roteiro,
limite de seis eventos). A primeira medição matou quase todas de uma vez:

**o bloco `UPCOMING EVENT` já estava a 99% do prompt** — caracteres 49.063 de
49.242 no turno 7, e 56.417 de 56.594 no turno 9, imediatamente antes da
`ROUTING CONSTRAINT`. Posição não era a variável.

Então testei a hipótese que ninguém tinha escrito: e se o problema for o
dragão?

## As três variantes (4 runs cada, nos dois payloads reais)

Regra de decisão pré-registrada antes de qualquer chamada: **V1 só é shippada se
materializar ≥ 3/4 onde V0 materializa < 2/4, nos DOIS payloads.**

| Variante | turno 7 | turno 9 |
|---|---:|---:|
| **V0** prompt atual, hint "Um dragão aparece do nada" | **1/4** | **1/4** |
| **V1** prompt atual + regra `UPCOMING EVENT IS MANDATORY` | **3/4** | **4/4** |
| **V2** prompt atual, hint trocado por "Uma lâmpada de mana estoura acima da mesa" | **4/4** | 1/1 † |

† a quarta rodada do V2 no turno 9 morreu num `JSONDecodeError` do meu script
(caractere de controle cru dentro de uma string do modelo). O caminho de
produção passa por `chat_completion_json`, que tem retry para exatamente isso —
a falha foi do harness, não do produto. Não repeti porque as três medições
anteriores já respondiam a pergunta.

## A causa

**V2 é a evidência que fecha o diagnóstico.** Com o prompt *exatamente igual* ao
que descartava o dragão, um evento que cabe na cena entra 4/4. Ou seja:

- não é transporte (já sabíamos);
- não é posição (99% do prompt);
- não é o teto de seis eventos (o turno 9 usou três);
- não é a instrução ausente — ela existia em `perception_events`
  (*"An UPCOMING EVENT, if provided, must appear here"*).

É a **prioridade de coerência do modelo**. Um dragão num salão de academia de
magia contradiz tudo que ele acabou de ler, e a instrução, sendo uma frase
dentro da descrição de um campo, perde para essa pressão. Foi por isso que a
resposta seguiu passando na validação estrutural: ela era estruturalmente
perfeita, só que sem o evento.

## O que foi shippado

**1. A regra medida, verbatim como testada** (`_build_system_prompt`, no bloco
`RULES`, não enterrada na descrição de um campo):

```
- UPCOMING EVENT IS MANDATORY. When an UPCOMING EVENT block is present,
  the FIRST entry of perception_events IS that event, written
  as a witness would perceive it, with witness_ids covering everyone who
  could sense it. It happens: it is not a suggestion, it does not wait for
  a better moment, and no coherence concern overrides it. Resolve the final
  HISTORY action in the events that follow it.
```

Uma nota: a primeira redação dizia *"When the user prompt carries..."* e o guard
da task 57 reprovou na hora — "the user" é ontologia de operador. O teste pegou
antes de eu commitar.

**2. Um guard retry determinístico**, no formato que a casa já usa para
repetição do Prose e vazamento de sussurro no Character: se o hint não aparece,
uma correção e nova chamada, registrada como `guard_retry="hint_omitted"` (a
observabilidade que a task 54, achado 7 acabou de criar). Nunca duas: um
Director que insiste não custa o turno.

**3. A detecção é lexical de propósito.** Compara palavras de 4+ caracteres do
hint contra os eventos, ignorando acento. Isso significa que uma paráfrase pura
— *"uma criatura escamosa de porte médio, com asas retorcidas"*, que foi
literalmente o que o V1 devolveu numa das runs — lê como omissão e custa um
retry. **Medi esse custo: 1 run em 4.** É mais barato que deixar um evento
enfileirado pelo humano sumir em silêncio, e a alternativa (julgar equivalência
semântica) exige outro modelo no caminho quente do turno.

## Respostas às perguntas da investigação

- **A omissão se reproduz?** Sim: 1/4 nos dois payloads, com a variante de
  controle mostrando 4/4 no mesmo prompt.
- **De onde vem o conflito dominante?** Da coerência da cena contra o conteúdo
  do evento — não das diretivas, do roteiro nem do teto de eventos.
- **Um evento menos extremo também é omitido?** Não. 4/4.
- **Como distinguir cumprimento semântico de cópia lexical?** Não distingo, e
  está declarado: a detecção é lexical, o falso negativo custa um retry, e o
  número (1/4) está medido em vez de suposto.
- **Qual boundary tem a garantia?** Os dois: a regra no prompt (medida) e o
  retry determinístico. O Prose continua cego — ele recebe `perception_events`,
  nunca o hint.
- **Consumo único em `skip + narrator_hint` com burst?** Sim, inalterado:
  `pending_hint` é limpo após o primeiro beat e o retry acontece dentro da mesma
  chamada de `narrate()`, antes do beat existir.
- **Que log torna uma omissão futura diagnosticável?** `guard_retry="hint_omitted"`
  no `debug.jsonl`, mais o contador `guard_retries` do harness.

## A lacuna de teste, agora fechada

Os testes antigos provavam que o hint chegava ao prompt e paravam ali — que é
exatamente o que a sessão real também provava, enquanto o evento sumia.
`tests/test_narrator_hint_materialization.py` (10 testes) cobre o outro lado:
a forma literal da omissão observada no turno 7, o retry com correção, o custo
zero quando o hint entra, e o caso da paráfrase que reprova de propósito.

## Relação com o roteiro: confirmada independente

O `roteiro_replan` daquela sessão foi `action="act_deadline"`, `reason="clock"`,
no turno **6** — antes dos dois hints. Os turnos 7 a 10 registraram
`action="none"`, `reason="in_progress"`. Nada aqui mudou o roteiro.

> **Caixas espelhadas em 2026-07-27.** As 6 caixas do cabeçalho ficaram em branco enquanto a seção de fechamento deste mesmo arquivo já
> registrava as entregas. Marcá-las é sincronizar cabeçalho e corpo, não
> declarar trabalho novo: a evidência de cada uma está na seção de
> fechamento abaixo. Onde a varredura de 2026-07-27 encontrou lacuna real,
> ela está descrita em seção própria com o teste que a cobre.
