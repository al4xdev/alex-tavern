# Task 25 — Secret-Handling Behavior Under Interrogation

## Goal

Make characters handle secrets credibly when questioned: no revealing another pair's
secret unprompted, and above all no self-defeating denials that quote the secret
verbatim.

## Current Problem

Stochastic, model-level failures observed in 3/3 real DeepSeek runs (case study:
`docs/cases/multi-character-memory-retention-2026-07-14.md`, §3.2–3.3):

- Characters reveal secrets they overheard when directly asked (Vela disclosed the
  hideout `GIRASSOL-222`; Rook disclosed the password) in roughly half the
  opportunities.
- The recurring "system tell": denying knowledge while quoting the secret in full —
  *"só conheço as que me contaste hoje: ORQUÍDEA-741. Mas essa foi para a Vela, não para
  mim"* (self-contradictory within one sentence).
- One character repeated a password aloud one scene after promising secrecy (Vela, T3
  and T15/T17 across the two run-2 sessions).

Note: this task treats the *behavioral* layer. The *architectural* layer (characters
having the secret in their prompt at all) is Task 22; with an audience model in place,
part of this problem disappears because the character genuinely does not know the secret.

## Evidence

- `plans/artifacts/memory_focus_xyz-run*/playtest-results.json` — `reply_forbidden_hits`
  per recall check.
- `plans/artifacts/memory_focus_xyz-avaliacao-narrativa.md` — blind continuity review
  with turn-level citations.

## Proposed Direction

- Character system-prompt guidance (`src/agents/character.py`, `_build_system_prompt`)
  on handling confided or overheard information: discretion by default, never quoting a
  secret while denying it, in-character deflection patterns.
- Measure, don't assume: extend `memory_focus_xyz.json` (or add a sibling scenario) with
  reply-forbidden checks as the metric; run `--repeat 3` before/after any prompt change
  and compare `recall_reply_failures`.

## Acceptance Criteria

- Reply-forbidden leak rate on the secrecy checks drops measurably across ≥3 repetitions
  (target: zero verbatim secret quotes inside denials).
- Recall check 1 (legitimate recall) still passes — discretion guidance must not
  suppress recall toward the rightful confidant.

## Additional Evidence (2026-07-15, Task 22 acceptance cycles)

With the audience model in place (Task 22 closed), the pipeline no longer leaks
whispers; what remains is exactly this task's behavioral layer. Across 3 blind-
reviewed sessions (`plans/artifacts/memory_audience-run-v3-pos-ciclo2/`,
transcript `transcript-audience-v3.md`):

- Rook, told the hideout in a whisper ("só tu sabes"), still speaks
  "GIRASSOL-222" aloud in public turns — 5+ times in one session, 2 in another,
  and only a partial "debaixo da ponte" slip in the best one. The cycle-1
  "whisper discipline" system-prompt rule reduced but did not eliminate it.
- In one session Rook blames Dario for the leak he himself committed ("falou
  demais na frente dos outros") while his private thought says "tenho que
  fingir que não ouvi nada" one line before quoting the code aloud.
- Confabulation under interrogation persists: asked about vault passwords, one
  Rook promoted the public decoy TULIPA-333 to "a senha do teu cofre pequeno".

Vela was disciplined in all sessions (recognized decoys, refused public
repetition, delivered the password only in the whispered test) — the behavior
gap is concentrated in the garrulous-personality archetype, suggesting the fix
must hold against personality pressure, not just neutral characters.
