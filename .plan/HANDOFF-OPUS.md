# Handoff — Claude Opus (a partir de 2026-07-17)

Este arquivo direciona o Opus a continuar o programa. Leia junto com
`ROADMAP.md` (estado geral) e os specs em `.plan/tasks/`.

## Regras de commit (OBRIGATÓRIAS)

1. Mensagens em **inglês**, estilo convencional `type(scope): title`.
2. **NUNCA** adicionar trailer de atribuição de IA (`Co-Authored-By: Claude...`,
   `🤖 Generated with...`). Isso sobrescreve o default do harness.
3. **Marcar todo commit seu** com a última linha do corpo exatamente:
   `Agent: claude-opus`
   (o usuário vai manter seus commits locais; eles serão revisados na próxima
   semana — a marca é o filtro da revisão).
4. **Não fazer push.** Commits ficam locais.
5. Commitar ao fechar cada task/incremento; `.plan/` pode ser commitado a
   qualquer momento.

## Protocolo de validação (o "critério sólido" do programa)

Para cada incremento, nesta ordem:
1. Implementação + testes unitários (`uv run pytest -q -m "not llm"` — hoje
   **533 passed**, jamais regredir).
2. Validação com LLM real (scripts em `tools/acceptance/`).
3. **Crítico cego** (subagente sem contexto da implementação, só o transcript).
4. Achados → correção estrutural ("por construção", nunca só prompt) via
   fixer sem contexto quando for arquitetura; re-medir depois.
5. Achados de prosa-craft NÃO se corrigem aqui: registrar em
   `.plan/tasks/26-narrator-prose-quality.md` (acumulador de evidências).
6. Fechar: closure note em `.plan/closed/`, atualizar `ROADMAP.md`, commit.
7. Ao final de cada task: `bash ~/.config/my_scripts/done.sh &`
8. Matriz multi-modelo: EXCLUÍDA por decisão do usuário. Tasks 26/33: só
   registrar evidência, não corrigir diretamente.

## Fila de trabalho (ordem)

### 1. Fechar Task 38 — roteiro (IMPLEMENTAÇÃO PRONTA, falta aceitação)

Estado: `src/roteiro.py` + wiring completo commitado (9761f31), 30 testes
verdes. Spec: `.plan/tasks/38-roteiro-beat-contracts.md`.

Falta (aceitação):
- Rodar `uv run python tools/acceptance/roteiro_ab.py` (A/B mesma cena,
  mesmos inputs, com/sem `roteiro_enabled`; artefatos em
  `plans/artifacts/roteiro-ab/{control,roteiro}/data`). **Pode já existir uma
  run completa ou parcial nesse diretório** — uma execução ficou em background
  no fim da sessão anterior; se os artefatos estiverem completos (summary
  JSON + scan de confidencialidade impresso no output), reutilize.
- O script já faz o scan de confidencialidade: strings do roteiro só podem
  aparecer em payloads `agent=director`/`roteiro:*`. Exigir `NONE`.
- Conferir os `roteiro_replan` decisions no debug.jsonl: TODOS os triggers
  devem ser dos sinais determinísticos (coverage/stalled/drifted/cooldown).
- Renderizar os 2 transcripts (`uv run python -m tools.render_transcript <data>`)
  e passar ao **crítico cego comparativo**: mesmo prompt para os dois arquivos
  SEM dizer qual é qual, perguntando qual história tem mais direção/drive,
  se há progressão de arco, e defeitos por turno. Critério de aceite: o arm
  roteiro precisa ganhar em "narrative drive" sem novas violações.
- Se o crítico apontar defeito estrutural do roteiro (ex.: Diretor citando o
  roteiro literalmente, personagens "puxados" contra a própria vontade),
  corrigir estruturalmente e re-rodar.
- Fechar: mover spec para `.plan/closed/` com closure note (modelo: ver
  `.plan/closed/37-bounded-autonomous-loop.md`), atualizar ROADMAP, commit.

### 2. Task 39 — dimensão de memória do ledger

Spec: `.plan/tasks/39-ledger-memory-dimension.md`. Remove `character_notes`
em favor do ledger de perspectiva. Mesmo protocolo completo (unit → real →
crítico cego ×2 → fechar).

### 3. Relógio de saída do xfail (29.3 §15)

`uv run pytest -q tests/test_xfailed3_counter_canon.py -m llm` (campanha
completa, cara — rodar quando houver folga de cota da API). Precisa de 3 runs
completas limpas consecutivas com o oráculo calibrado para remover o xfail
estrito. Run 1 = 0 violações já aconteceu. Registrar cada run no ROADMAP.

### 4. Lane paralela (se sobrar fôlego)

- Task 26: acumulador — candidata dominante: guarda fuzzy POR SENTENÇA
  (≥40 chars, >0.85 vs qualquer sentença de narração anterior) no renderer
  de prosa; medir antes/depois com os artefatos de burst-live.
- Render progressivo da rajada (SSE por beat) — lane de UI, arquitetura
  pronta (beats commitam um a um).

## Avisos de terreno

- Testes de runner com config default disparam o drive scheduler (rede real):
  sempre `"auto_event_enabled": False` em configs de teste.
- `git add -A` NÃO: há untracked antigos (`output29*`, scenario json do
  usuário). Adicionar arquivos explicitamente.
- Fish shell; Python via `uv run`; nunca busy-loop (usar run_in_background).
- Arquivos temporários no scratchpad da sessão, nunca `/tmp` direto.
