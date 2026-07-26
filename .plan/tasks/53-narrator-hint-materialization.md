# Task 53 — Materialização confiável de `narrator_hint`

> **Status (2026-07-26): ABERTA — investigação baseada em sessão real.**
> O transporte HTTP/Runner funcionou, mas o Director descartou dois hints
> consecutivos e o Prose nunca os recebeu. Ainda não há decisão de implementação:
> primeiro reproduzir o boundary real pelo método curl-first.

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

- [ ] Causa reproduzida ou delimitada com payload real e contagem de 3–4 runs
      por variante.
- [ ] Resultado separado por hint manual, hint automático e
      `skip + narrator_hint`.
- [ ] Contrato de consumo único e de visibilidade escrito sem expor o hint
      diretamente ao Prose.
- [ ] Lacuna dos testes atuais demonstrada com um teste que falha no
      comportamento observado, ainda que a implementação seja tratada depois.
- [ ] Relação com roteiro confirmada como independente, salvo nova evidência
      contrária.
- [ ] Achados registrados nesta task antes de qualquer decisão de implementação.

