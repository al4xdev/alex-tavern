# Task 35 — Historian Audience Filtering (29.2 increment 3)

## Goal

Close the single confidentiality root the 29.3 comparison quantified: the
private Historian ignores `record_visible_to`, so whispered content enters
every character's private-memory prompt at compaction and cascades from there.

## Current Problem (measured, `output29/comparison-29.3.md`)

Five-stage cascade from one defect (`src/agents/summarizer.py`,
`build_private_memory_messages` filters only foreign thoughts, never audience):
whisper → 7 private-summarizer prompts at both compactions → poisoned
`character_notes` feed "What you remember" → Van Helsing (T19) and Watson
(T22) SPOKE the secret publicly → public records propagate it to everyone,
including perspective updaters. The character output guard cannot catch stage
3: it only protects secrets the speaker legitimately witnessed; a note-smuggled
secret is invisible to it. 26 classified instances in the post-29.2 full run,
all from this root.

## Direction

- `build_private_memory_messages`: include a speech/action record only when
  `record_visible_to(record, character_id)` (audience covers zone-scoped
  records too, since increment 2 computes effective audiences from zones).
- Decide (staged, not now): whether `character_notes` survive at all once the
  perspective ledger grows a memory dimension (29.2 doc §8 "remove private
  compaction"). This task does NOT remove notes; it makes them honest.
- Re-run the xfailed3 full tier: expected `GLOBAL-secret-in-unauthorized-prompt`
  26 → 0 and `SEC-01-watson-unauthorized` → 0 in one change.

## Acceptance Criteria

- [~] Unit test: a whispered record outside X's audience never appears in X's
  private-summarizer prompt; the confidant's prompt keeps it.
  **SUPERADO** — ver nota de 2026-07-27.
- [~] Unit test: zone-scoped records respect the same boundary.
  **SUPERADO** — mesma nota.
- [x] xfailed3 full tier re-run: secret family at 0; identity rules stay green;
  delta appended to `output29/comparison-29.3.md`. — refeito em 2026-07-27
  (sessão `8484d749`, 24/24 turnos, provider real): **família secret = 0**;
  ver `.plan/closed/39-ledger-memory-dimension.md`.
- [x] Existing summarizer tests stay green (world summary is narrator-side and
  keeps seeing every non-thought record — unchanged by design). — o world
  summary segue narrator-side; `tests/test_ledger_memory.py` e
  `tests/test_thought_containment.py` cobrem o limite hoje.

> **CLOSED 2026-07-16.** Three-layer fix in `build_private_memory_messages`:
> record visibility (`record_visible_to` + Player→controlled ownership),
> narration exclusion (narrator prose retold the whisper at T21), and
> world-directives exclusion (the canon bible defines the secret as WT-11).
> Benchmark cascade: 26 → 17 → 13 → **0** secret instances across three
> full-tier re-runs; final state 25 (baseline) → 2 violations, both stochastic
> semantic probes. 7 unit tests in `tests/test_historian_audience.py`. Suite:
> 433 passed. Note-quality trade-off recorded: notes lose narration-borne
> outcome memory; the proper future source is persisted perception events
> (ledger memory dimension, 29.2 §8).


---

# Nota de 2026-07-27: dois critérios foram superados, não cumpridos

Os dois primeiros testes unitários pediam prova sobre o **prompt do summarizer
privado**. Esse componente não existe mais: a task 39 substituiu as notas
privadas por memória de ledger determinística e removeu a chamada. Marcá-los como
feitos seria mentira; deixá-los abertos sugeriria trabalho pendente que não há.
Ficam como `[~] SUPERADO`.

O que resta do critério não sumiu junto — mudou de lugar e ficou mais forte:

| garantia da 35 | onde vive hoje |
|---|---|
| sussurro fora da audiência não entra no prompt de X | `tests/test_thought_containment.py` (nada além do Diretor lê pensamento) + `record_visible_to` em `_format_history_for_character` |
| limites por zona respeitados | `tests/test_zone_audibility_default.py`, `TestRunnerZoneMaterialization` |
| o componente não volta | `tests/test_integration.py:2035` trava a assinatura contra `build_private_memory_messages` |

Essa última linha é a parte que importa em revisão: quando um componente é
removido por ser a fonte de uma classe de vazamento, o teste que sobrevive não
deve ser sobre como ele filtrava — deve ser sobre ele **não existir**. É o que
está lá.

A terceira caixa era mensurável e foi medida hoje, não herdada: campanha full
tier de 24 turnos com provider real, família secret em 0.

> **Ressalva de reprodutibilidade (2026-07-27).** As sessões citadas nesta seção
> foram geradas em diretório temporário e **não estão no repositório**: os números
> não são auditáveis por terceiros nem por uma sessão futura. Foram conferidos por
> mim no momento da execução e o método está descrito acima com detalhe suficiente
> para ser refeito, mas quem reler deve tratá-los como *relato*, não como
> evidência verificável. Medições que precisem valer como prova têm de escrever
> seus artefatos em `docs/` ou `.plan/`, ou o critério deve exigir um script de
> aceitação em `tools/acceptance/` que qualquer um rode.
