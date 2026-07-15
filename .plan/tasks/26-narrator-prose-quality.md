# Task 26 — Narrator Prose Quality and Staging Continuity

## Goal

Remove the reader-visible style defects that make long sessions feel mechanical:
boilerplate narration, verbatim-duplicated private thoughts, staging jumps, and
person-of-address oscillation.

## Current Problem

Findings from the blind continuity review of three real sessions
(`plans/artifacts/memory_focus_xyz-avaliacao-narrativa.md`; case study
`docs/cases/multi-character-memory-retention-2026-07-14.md`, §3.3):

- **Boilerplate narration**: near-identical sensory sentences recycled across turns
  ("sente o couro do colete esticar", "alguém arrasta um banco"); one character kept a
  hand in a pocket for ~29 consecutive turns.
- **Verbatim-duplicated thoughts**: private thoughts identical word-for-word across
  adjacent turns (session `ff8b7dd6`, T6/T7 and T21/T22) — the thought also lagged the
  topic (still ruminating a previous subject).
- **Staging jumps**: a character walks toward the door and reappears seated at the table
  with no transition (session `50bb264a`, T14→T15); standing/sitting flips without
  narration; scenario says one shared table but narration stages separate spots.
- **Person oscillation**: narration alternates between second person ("você, Vela") and
  third person within one session.
- **Costume transfer**: narration dressed one character in another's signature garment
  (session `ff8b7dd6`, T19).

## Evidence and Measurement

- The harness already counts `exact_narration_sentence_duplicates` and
  `exact_character_sentence_duplicates` (`tools/playtest_harness.py`,
  `analyze_debug_records`); extend with a thought-duplication counter (same speaker,
  adjacent turns, normalized equality) and use `memory_focus_xyz.json --repeat 3` as the
  benchmark.
- Transcripts via `tools/render_transcript.py` + the clean-reviewer protocol from
  `.claude/skills/memory-playtest/SKILL.md` for qualitative before/after comparison.

## Proposed Direction

- Narrator prompt (`src/agents/narrator.py`): explicit anti-boilerplate and staging
  continuity rules (track posture/position; a character who moved must be moved back on
  screen; fix person of address).
- Character prompt: forbid repeating one's own previous thought verbatim (the existing
  duplicate-sentence rule covers speech but evidently not thoughts).

## Acceptance Criteria

- Duplicate-sentence and (new) duplicate-thought counters drop across ≥3 repetitions of
  the benchmark scenario, with no increase in `character_action_heuristic_hits` or
  schema retries.
- A fresh blind continuity review reports no staging jump of the door/table kind and no
  verbatim-duplicated thoughts.

## Additional Evidence (2026-07-15, Task 24 acceptance runs)

Blind continuity review of `plans/artifacts/memory_action_fact-run1/` (3 sessions):

- **Fact invention by the narrator despite "never invent facts" directives**: session
  `6f75a83e` injects an unresolved supernatural subplot (an ice-cold blade appearing on
  Rook's vest, a scratched message under a cup); session `7b363465` invents a backstory
  ("templo de Salim", "rota sul") that all characters then treat as established.
- **Verbatim-duplicated private thoughts** across adjacent turns (session `7b363465`,
  turns 1–2), and dialogue leaking inside italic narration then duplicated as speech
  (turns 3–4).
- **Staging teleport**: Rook moves from "across the room" to the table with no
  transition (session `7b363465`), contradicting the scenario's fixed seating.
- **Scripted blindness**: in all 3 sessions, Dario's turn-2 "not a word aloud" request
  ignores that Vela already vocalized the code in turn 1 — the narrator/character do not
  acknowledge the immediately preceding event.

## Additional Evidence (2026-07-15, Task 22 acceptance cycles)

Blind continuity review of `plans/artifacts/memory_audience-run-v3-pos-ciclo2/`
(3 sessions, whisper markers rendered in transcripts):

- **Narration contradicting established public facts**: one session narrates
  that Vela "não ouviu" a location Rook had shouted publicly at the same table
  turns earlier; another narrates a whispered line as *not* heard by its own
  audience ("as palavras se perdem no burburinho") and then lets the character
  know the exact code one turn later — the narrator reinterprets whisper
  semantics instead of following the marker.
- **Internal ID leaking into fiction**: a private thought references "esse tal
  de C3" — a system identifier, fourth-wall break.
- **World-breaking lexicon**: "diesel" in a candle-lit tavern; minor modern
  terms ("Xerife", "15%", "plano B").
- **Verbatim loops persist**: identical ambient sentences across ~12 turns,
  identical private thoughts repeated up to 10 times in long single-character
  blocks; scene frozen (same three laughs at the door all night) in the worst
  session, while the best session shows real ambient progression (tavern
  emptying, candles going out) — proving the model can do it.
- **POV mixing** inside one narration paragraph (opens in Rook's eyes, ends on
  Vela's skin).
