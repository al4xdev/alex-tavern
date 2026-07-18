# Handoff — Fable (2026-07-17)

Documento LOCAL. Regras de commit: iguais ao `HANDOFF-OPUS.md` §0 — inglês,
convencional, **NUNCA** trailer de IA, última linha `Agent: fable`, **sem push**,
nunca `git add -A`. Protocolo de validação: `HANDOFF-OPUS.md` §1.

## Tua tarefa: Task 39 increment 2 (o Opus deixou o increment 1 pronto e verde)

O increment 1 (aditivo, baixo risco) está feito e commitado (`0e83612`): a
dimensão de memória do ledger existe e funciona. **O increment 2 é a parte
arriscada — toca a COMPACTAÇÃO (transacional: undo LIFO, checkpoints com hash,
restore).** O Opus parou aqui de propósito pra você fazer com cuidado fresco.

### Estado atual (increment 1, já commitado)
- `CharacterPerspective` (schema v8) tem: `recent_memory: list[str]` (digest
  determinístico contínuo, projetado, bounded 24), `memory_summary: str = ""`
  (RESERVADO pro teu increment 2), `memory_through_turn: int` (cursor).
- `src/agents/perspective.py::capture_memory` — captura determinística (sem LLM),
  chamada em `runner._ensure_perspective`.
- `src/agents/character.py::_ledger_memory_text` + `_build_user_prompt` — o prompt
  lê a memória do ledger PRIMEIRO, com fallback pra `character_notes` enquanto os
  dois coexistem.
- 10 testes em `tests/test_ledger_memory.py`. Suíte 560 verde.

### O que o increment 2 precisa fazer

**(a) Revisão semântica em lote (aditivo, faça PRIMEIRO — menor risco).**
Condensar `recent_memory` em `memory_summary` via LLM quando crescer além de um
limiar; manter a cauda recente crua. Co-agendar com uma chamada do narrador
(ideia de concentração de latência do usuário — ver nota async da task 36). O
`_ledger_memory_text` já renderiza `memory_summary` liderando + `recent_memory`
seguindo, então é só popular o summary. TESTE via curl-replay primeiro (método no
`AGENTS.md` §6): pegue um `recent_memory` real longo e itere o prompt de revisão
até condensar bem, ANTES da bateria.

**(b) REMOVER `character_notes` (o risco real — faça depois de (a) estável).**
Superfície completa (grep confirma 5 arquivos):
- `src/models.py` — campo `GameState.character_notes` + no `dict_to_game_state`
  (linha ~417) + `game_state_to_dict`. Forward-only: pare de ler/escrever.
- `src/agents/summarizer.py` — `build_private_memory_messages` (133),
  `build_private_memory_json_schema` (69), o caminho de `changed_notes` em
  `summarize` (215), `relevant_character_ids` (116). Remover a fan-out privada;
  manter SÓ o world summarizer (narrator-side).
- `src/runner.py::compact_session` (~1155-1219) — `character_notes=game.character_notes`
  passado ao summarize (1173), `{**game.character_notes, **changed_notes}` (1185),
  `compacted.character_notes` (1201), e os campos de checkpoint
  `before_character_notes` (1216) + `after_character_notes_hash` (1219).
- `src/runner.py` restore (~1327 e ~1371) — `after_character_notes_hash` na
  verificação de conflito e `draft.character_notes = before_character_notes`.
  **CUIDADO**: mexer no hash de checkpoint muda o formato — os testes de
  compactação (undo/restore/fork) são teu guardrail; rode-os a cada passo.
- `src/agents/character.py` — param `notes` do `act()` e o fallback em
  `_build_user_prompt` (agora que a memória do ledger é a fonte única).
- `src/config.py` — chaves de `summarizer_max_tokens` etc. se ficarem órfãs.

**(c) Reconciliar a metade de recall privado da Task 23.** O pinning de
âncora-de-código em `_format_history_for_character` (character.py:210,
`_CODE_ANCHOR_RE`) FICA (é do histórico). O que muda é que "o que você lembra"
agora vem do ledger, não das notas. Confirme que um código confiado sobrevive na
memória do ledger (ou continua pinado no histórico).

**(d) Re-validar** as probes de retenção do xfailed3 (ribbon, origin) via memória
do ledger nas DUAS compactações; família de segredo em 0. Rodar
`uv run pytest -q tests/test_xfailed3_counter_canon.py -m llm` (caro, precisa de
cota/endpoint — provider ativo agora = deepseek).

### Aceite (headline da spec, `.plan/tasks/39-ledger-memory-dimension.md`)
- [ ] Nenhum `character_notes` ou chamada de summarizer privado em lugar nenhum
  (grep limpo).
- [ ] Rapport acumula numa sessão SEM compactação (já entregue no increment 1;
  re-confirmar num run real).
- [ ] Probes de retenção do xfailed3 passam via ledger nas duas compactações;
  segredo em 0.
- [ ] Undo/fork/restore preservam a memória do ledger exatamente (o ledger já é
  deep-copiado; garanta que a remoção das notas não quebrou o hash de checkpoint).

### Avisos
- Compactação é transacional (AGENTS.md §6, final). Cada passo: rode os testes de
  compactação/replay. Remover um campo do checkpoint hash exige regenerar o
  formato do checkpoint — forward-only, sem shim.
- `bash ~/.config/my_scripts/done.sh &` ao terminar; fechar em `.plan/closed/`.
