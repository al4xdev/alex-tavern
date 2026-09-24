**A primeira resposta aceita que atribui a Holt o lacramento da porta leste é o replan T7, `debug.jsonl:86`.** Ela apresenta esse lacramento como antecedente de um novo plano, sem evento anterior que o confirme. O pedido desse replan não continha o campo de estado da porta aberta; o pedido seguinte do Director continha.

Caminho-base: `plans/artifacts/77-p3-input-dispatch/live/sessions/fb62cc2f/`.

| Registro | Natureza e evidência |
|---|---|
| `debug.jsonl:40`, replan T4 aceito | **Plano anterior:** Maelis “ordena [...] que Garran Holt lacre as portas dos arcos”. Seu `expected_anchors` inclui **“porta leste entreaberta”**. As portas dos arcos e a porta leste aparecem como objetos distintos. Não há barra de ferro nem selo de cera. |
| `debug.jsonl:42`, Director T4 aceito | **Eventos:** Holt examina a fratura do arco sul e sinaliza Maelis. As ordens da diretora tratam de equipamento e descida. Não confirma o lacramento planejado. **Estado:** `scene_update.porta_leste = "entreaberta para o pátio interno, agora com alunos e Marta Ferrolume passando pela soleira"`. |
| `debug.jsonl:54`, Director T5 aceito | **Estado:** `scene_update.porta_leste = "aberta de par em par, ligando o salão ao pátio interno"`. **Fala proposta:** Holt manda os candidatos cruzarem essa porta para o pátio. |
| `debug.jsonl:74`, Director T6 aceito | **Blocking:** “A porta leste está aberta de par em par”. **Fala proposta e estado:** mantém a ordem de evacuação pela porta leste. |
| **`debug.jsonl:86`, replan T7 aceito** | **Primeiro antecedente inventado:** `beat.intent` começa “A porta leste, **que Garran Holt estava lacrando com barra de ferro e selo de cera**, cede de dentro para fora [...]”. `attempt_number = 1`, `error = null`. |
| `debug.jsonl:88`, Director T7 aceito | **Evento novo:** “A porta leste cede de dentro para fora, a madeira racha e a barra de ferro entorta [...]”. **Estado novo:** porta “arrombada de dentro para fora”. Não há evento intermediário de fechamento. |

O pedido real de `debug.jsonl:86`, `request.messages[1].content`, tem 44 linhas internas:

- Não contém `physical_facts`, `porta_leste = aberta` ou outra declaração explícita de fechamento efetivado.
- Linhas 29 e 35, em `RECENT EVENTS`, conservam falas truncadas de Holt mandando evacuar pela porta leste. A linha 35 inclui: “todo mundo para a porta leste e para o pátio, agora”.
- Linha 42 entrega o **plano anterior**: “que Garran Holt lacre as portas dos arcos”.
- Linha 44 exige uma nova perturbação externa porque o beat está marcado como estagnado. Isso é uma instrução de planejamento, não registro de fechamento.
- O sistema desse pedido, linhas 5–6, diz: “Beats plan SITUATIONS and pressures, never anyone's decisions. Every character's choices are sacred”.

Já `debug.jsonl:88`, `request.messages[1].content`, contém simultaneamente:

- Linha interna **174**, `Physical facts`: `"porta_leste": "aberta de par em par, ligando o salão ao pátio interno"`.
- Linha interna **209**, `Current beat`: “que Garran Holt estava lacrando com barra de ferro e selo de cera”.
- Linha interna **211**, elementos a introduzir: “porta leste rachada [...] barra de ferro entortada”.

Conferi as falas e intenções de Holt anteriores a T7. **Não há ação ou fala dele lacrando a porta leste.** Há duas passagens que precisam ser diferenciadas:

1. T4, `debug.jsonl:50`: “Maelis, desce ao depósito e fecha a porta atrás de você.” É uma **ordem a Maelis**, no contexto do depósito; não uma execução por Holt, não menciona barra/cera, e não consta no pedido truncado do replan T7. Está persistida em `state.json:22351`.
2. T5, `debug.jsonl:70`, `action_intent`: “empurrar a porta com o ombro para abrir a passagem aos candidatos”. T6, `:81`, `action_intent`: ficar na soleira apontando a rota ao pátio. São **intenções brutas de abertura/evacuação**, não fechamento; não devem ser promovidas automaticamente a eventos executados.

Os snapshots mantêm a porta aberta em T5 (`state.json:23873`), T6 (`:37635`) e na entrada de T7 (`:44555`). O estado final registra o arrombamento (`:454`).

Há uma tentativa rejeitada do Director entre replan e resposta aceita: `debug.jsonl:87`, `JSONDecodeError: Extra data`. O evento confirmado usado acima é o da tentativa 2, linha 88.

O rastreamento estabelece, neste caso, **um antecedente de lacramento introduzido pelo planejador e depois incorporado ao evento do Director**. Não identifica por que o planejador o inventou, nem demonstra uma causa geral. Nenhum arquivo alterado.
