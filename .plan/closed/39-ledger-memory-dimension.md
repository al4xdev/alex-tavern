# Task 39 — Ledger Memory Dimension (replaces character_notes)

**Depends on:** 35 (done). Strengthened by 36 (perception events persisted as
the memory source). This is the 29.2 doc §8 "remove private compaction"
decision, given its own task so it does not get lost.

## Goal

Grow the perspective ledger with a durable private memory dimension
(`self.memory_summary` + bounded important-memories entries), updated
continuously from what the character actually perceived — then REMOVE
`character_notes` and the per-character compaction fan-out entirely (one
authority, no parallel memories).

## Why

- Task 35 made notes honest but poorer: they lost narration-borne outcome
  memory (recorded trade-off). The correct source for outcome memory is the
  typed perception events the character witnessed — persisted, not re-derived
  from omniscient prose.
- "What you remember: (none yet)" persists across whole sessions today (user
  evidence, session ef6b5b90): no rapport accumulates until a compaction
  happens. Continuous ledger memory closes this.
- Compaction then keeps ONLY the world summarizer (narrator-side), cutting the
  per-character call fan-out at every compaction.

## Direction (sketch, freeze in-task)

- Persist witnessed perception events (or a bounded digest) per viewer;
  batched semantic revision co-scheduled with chosen narrator calls (user's
  latency-concentration idea, see task 36 async note).
- `_build_user_prompt`'s "What you remember" reads the ledger memory.
- Remove: `GameState.character_notes`, `summarizer` private calls,
  `build_private_memory_messages`, checkpoint note fields — forward-only,
  schema bump.
- Reconcile Task 23's private-recall half (its public trim gap remains).

## Acceptance (headline)

- [x] No `character_notes` field or private summarizer call remains anywhere.
      **Verificado 2026-07-27:** a única ocorrência em `src/` é o comentário
      histórico do schema v9 em `models.py:24`; `tests/test_integration.py:2031`
      trava a assinatura de `summarize` contra o campo.
- [x] Rapport accumulates within a session without compaction (the ef6b5b90
  complaint), shown in a real run.
      **Verificado 2026-07-27:** sessão real sem nenhuma compactação +
      `TestRapportAccumulatesWithoutCompaction`, ver seção no fim.
- [ ] xfailed3 retention probes (ribbon, origin) pass via ledger memory across
  both compactions; secret family stays 0.
- [x] Undo/fork/restore preserve ledger memory exactly.
      **Verificado 2026-07-27:** undo já tinha teste; fork e restore não
      tinham. Três testes novos em `tests/test_ledger_memory.py`, ver
      "Fork e restore" no fim do arquivo.

## Design frozen (2026-07-17) — staged increments

### Increment 1 (additive, deterministic, LOW risk) — THIS increment
- `CharacterPerspective` gains a memory dimension (schema v8):
  - `recent_memory: list[str]` — deterministic, continuous capture of what the
    viewer perceived, one compact digest per witnessed turn, viewer-projected
    (no unlearned names/IDs — reuse the same projection as the identity ledger).
    Bounded (keep last N, e.g. 24).
  - `memory_summary: str = ""` — reserved for the LLM semantic revision
    (increment 2 fills it); empty in increment 1.
- Runner captures the digest when a character witnesses a turn (it already
  computes `render_events_for_viewer` per speaker; add heard speech too).
- `_build_user_prompt` "What you remember" reads the ledger memory
  (memory_summary + recent_memory), falling back to `character_notes` while both
  coexist. character_notes STAYS this increment (no removal yet).
- Undo/fork/restore already deep-copy the perspective; verify memory survives.
- Acceptance hit now: rapport accumulates WITHIN a session with no compaction
  (the ef6b5b90 complaint) — deterministic, unit-testable, no LLM.

### Increment 2 (removal, HIGHER risk) — next
- LLM semantic revision: condense `recent_memory` into `memory_summary` +
  bounded important entries, batched/co-scheduled with a narrator call.
- REMOVE `character_notes`, the private summarizer calls
  (`build_private_memory_messages`, summarize's notes path), checkpoint note
  fields. Forward-only. Reconcile Task 23's private-recall half.
- Re-validate xfailed3 retention probes (ribbon, origin) via ledger memory
  across both compactions; secret family stays 0.

## FECHADA COM CONFIANÇA (2026-07-19, madrugada)

Increment 2 completo: (a) revisão semântica (`revise_memory`, agente
`perspective:memory:<id>`, replay-validada em digests reais — 2 iterações de
regra até 1ª pessoa + zero fusão de referências; never-fail-the-turn);
(b) character_notes removido em todo lugar (summarizer world-only, schema
bump); (c) pinning de âncoras mantido + segredos-verbatim test-locked.

Validação final (xfailed3 pós-39, 2 tiers): ZERO violações atribuíveis à
memória. O único hit (`perspective:memory:C5` com o instrumento) era allowlist
desatualizado do oráculo: C5 é o CONFIDENTE do sussurro — memória legítima.
Allowlist corrigido (perspective:memory:C1/C5). As 2 violações reais do run
(SP-01 intra-turno, WT-09 alias) são de famílias pré-existentes registradas na
linha do relógio no ROADMAP.

> **Correção (2026-07-20):** a nota original dizia que WT-09 era "sem relação
> com memória". Errado — a raiz É de propagação de memória, só que UPSTREAM do
> digest: a revelação do alias no T20 foi um `audible_speech` do Diretor, e
> eventos `audible_speech` do Diretor não são persistidos no history, então a
> memória nunca teve o nome pra reter/revisar. Não é defeito do digest da 39
> (esse funciona: retém o que recebe); é o record que nunca chegou. Fix é de
> código (persistir audible_speech), não do prompt de memória. Ver ROADMAP e
> `tests/test_audible_speech_persistence.py`.


---

# Fork e restore verificados (2026-07-27)

O critério dizia "undo/fork/restore preservam a memória do ledger exatamente".
**Só o undo tinha teste** (`test_undo_rolls_ledger_memory_back`). Fork e restore
estavam afirmados e não verificados — e o undo tinha acabado de mudar no bump
para o schema 14, o que tornava a lacuna mais relevante, não menos.

Três testes novos, todos verdes na primeira execução (o comportamento estava
certo; o que faltava era a prova):

1. **`test_fork_carries_the_ledger_memory_to_the_copy`** — para cada personagem,
   a cópia mantém `recent_memory`, `memory_through_turn`, `memory_summary` e os
   nomes conhecidos em `people`. Um fork que perdesse o ledger reiniciaria a
   memória privada de todo mundo em silêncio: a cópia simplesmente começaria
   amnésica, sem nada acusando.
2. **`test_a_fork_is_a_copy_not_a_shared_reference`** — jogar na cópia não
   escreve no original.
3. **`test_restoring_a_compaction_keeps_the_ledger_memory`** — a compactação
   evicta histórico, e o ledger não é histórico: a memória é idêntica antes da
   compactação, depois dela e depois do restore.

Detalhe de método no terceiro: a primeira versão usava `pytest.skip` quando a
compactação não disparava, o que deixaria o teste passar sem testar nada. Trocado
por asserção dura de que a compactação aconteceu e evictou registros.


---

# Rapport sem compactação (2026-07-27)

O critério pedia "mostrado em run real". Está mostrado, e ganhou rede.

**Run real.** Das 15 sessões da medição da task 55, uma fechou sem nenhuma
compactação — `B_noalign/d9bdae22`, 10 turnos, `compaction_stack` vazio. O ledger
de C2 tem **8 linhas** e o cursor `memory_through_turn=10`. É exatamente a
reclamação do ef6b5b90 respondida: a memória privada andou até o último turno
sem que nenhuma eviction tivesse acontecido. Nas outras 14 (20 turnos, 1
compactação cada) o cursor também chega a 20, ou seja, continua andando depois
da compactação em vez de só nela.

**Por que isso precisava de teste mesmo com o run real.** A correção do ef6b5b90
é *uma linha de fiação*: `capture_memory` roda dentro de `_ensure_perspective`
(`runner.py:2263`), que o runner chama uma vez por falante por turno. Toda a
classe `TestCaptureMemory` chama a função diretamente — prova a função, não a
fiação. Mover a chamada de volta para o caminho da compactação deixa **todos**
aqueles testes verdes e ressuscita o bug inteiro.

`TestRapportAccumulatesWithoutCompaction::test_the_ledger_grows_every_turn_with_no_compaction`
percorre 6 turnos numa sessão real (sem provider) e verifica três coisas
distintas: o ledger cresce monotonicamente, o cursor avança junto, e o conteúdo
do **último** turno está lá — a terceira separa "acumula continuamente" de
"despejou um backlog de uma vez", que os dois primeiros sozinhos confundiriam.

Nota de método: o helper de sessão estava preso como método de
`TestUndoPreservesMemory`. Herdar a classe para reusá-lo fazia os 4 testes do pai
rodarem duas vezes; virou `_scripted_session` no nível do módulo.
