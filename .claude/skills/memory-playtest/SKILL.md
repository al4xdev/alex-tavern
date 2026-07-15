---
name: memory-playtest
description: Roda o playtest de memória multi-personagem (foco narrativo alternado X/Y/Z) contra um LLM real, localiza perdas camada a camada e avalia a narrativa com um subagente limpo no papel de roteirista. Use quando o usuário pedir para testar retenção de memória, recall de fatos, vazamento entre personagens ou continuidade narrativa em sessões longas.
---

# Memory playtest — fluxo completo

Fluxo em quatro etapas: rodar o cenário contra o LLM real → localizar perdas por camada → renderizar o roteiro → avaliação narrativa por subagente **sem contexto herdado**. Os artefatos de cada run são a evidência; nunca os apague.

## 1. Rodar o playtest

```fish
uv run python -m tools.playtest_harness tools/playtests/memory_focus_xyz.json \
  --config-file .data/config.json --language Portuguese --llm-timeout 120 \
  --model-label memoria-xyz --repeat 1 --output-dir <RUN_DIR>
```

Cenários disponíveis:
- `tools/playtests/memory_focus_xyz.json` — retenção com foco alternado + checks de isolamento (os checks 2/3 falham até a Task 22 existir; é o esperado).
- `tools/playtests/memory_action_fact.json` — fato que entra só pelo campo `action` (pergaminho mostrado e queimado); aceite da Task 24.

- `<RUN_DIR>` deve ser um diretório novo (o harness recusa diretórios existentes e qualquer coisa dentro de `.data/`). Use o scratchpad da sessão ou `plans/artifacts/<nome>-runN`.
- Rodadas longas: execute em background e aguarde a notificação de conclusão.
- Exit ≠ 0 é esperado quando um `recall_check` obrigatório falha — isso É o resultado, não um defeito do harness.
- Interprete `runs[].events[].recall` em `playtest-results.json`: `prompt_passed` falso = perda antes do provider (estado/seleção/prompt); `prompt_passed` verdadeiro com `reply_passed` falso = falha de recall do modelo.
- `invariant_violations` deve estar vazio — prova que não houve compactação, edição de presença nem troca de participantes no meio da sessão.
- Recall de modelo é estocástico: para afirmar "reproduziu/não reproduziu", use `--repeat 2..3` e compare os checks entre repetições.

## 2. Localizar perdas camada a camada

```fish
uv run python -m tools.analyze_memory_run <RUN_DIR> \
  --marker "ORQU[ÍI]DEA-741" --marker "GIRASSOL-222"
```

Camadas: 1 ESTADO (histórico persistido) → 2 SELEÇÃO (filtro content_type + trim recomputados offline) → 3 PROMPT (requests reais em `debug.jsonl`) → 4 RESPOSTA (o que o personagem disse). A primeira camada onde o marcador some é a localização da perda; a correção pertence só a essa camada.

## 3. Renderizar o roteiro

```fish
uv run python -m tools.render_transcript <RUN_DIR> --out <TRANSCRIPT.md>
```

Gera um roteiro legível (narração, diálogo, ações e pensamentos privados marcados) sem nenhum vazamento de código, prompt ou config — é o único material que o subagente da etapa 4 pode receber.

## 4. Avaliação narrativa por subagente limpo

Lance um subagente `general-purpose` **novo** (nunca `SendMessage` para um agente existente — o avaliador não pode ter contexto herdado). Regras invioláveis do prompt:

- Entregue APENAS: o caminho do transcript e uma descrição curta do cenário esperado (ex.: "três personagens numa taverna; Dario confia uma senha a Vela no início, a conversa desvia longamente para Rook com vários códigos, e no fim Dario testa a memória dos dois").
- PROIBIDO: inspecionar código, testes, planos, análises anteriores, configs ou qualquer arquivo além do transcript; modificar arquivos; propor implementação ou correção técnica.
- Papel: roteirista / editor de continuidade narrativa lendo a cena como um leitor comum.
- O relatório escrito deve responder:
  1. Os personagens lembram eventos anteriores de forma natural?
  2. O comportamento de cada um permanece consistente?
  3. Algum personagem demonstra saber algo que não deveria saber?
  4. Fatos, nomes, códigos, relações ou motivações se confundem em algum ponto?
  5. A conversa soa contínua depois das trocas de foco narrativo?
  6. Há alguma descontinuidade estranha que um leitor normal notaria?

## 5. Consolidar

Relate ao usuário em um único resumo: resultado dos `recall_checks` (com a distinção prompt×reply), a tabela de camadas por marcador, os invariantes, e o relatório do subagente. Falha de isolamento (segredo de um par no prompt do outro personagem presente) é comportamento atual por design — todo `speech` é público entre presentes; registre como questão de produto, não como regressão.
