# Task 26 — Narrator Prose Quality and Staging Continuity

> **Status (2026-07-20): ABERTA — lane acumuladora, não fechável hoje.** Boa
> parte dissolveu na 36. Dominante atual: paráfrase semântica abaixo da barra
> (medição offline 2026-07-19: retry-guard fuzzy >0.85 não ganha nada; banda
> 0.7–0.8 ≈ 9% das sentenças). Mitigação teria que ser SEMÂNTICA (estilo
> delta-material da 33b, agora construído) ou prompt. Sem trabalho acionável
> confiável fechado.

## Goal

Remove the reader-visible style defects that make long sessions feel mechanical:
boilerplate narration, verbatim-duplicated private thoughts, staging jumps, and
person-of-address oscillation.

## Current Problem

Findings from the blind continuity review of three real sessions
(`plans/artifacts/memory_focus_xyz-avaliacao-narrativa.md`; case study
`docs/cases/07-multi-character-memory-retention-2026-07-14.md`, §3.3):

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

## Additional Evidence (2026-07-15, Task 25 acceptance runs)

Blind review of `plans/artifacts/memory_outputguard-run-v3-pos-ciclo1/` (3 sessions):

- **Memory confabulation under interrogation** (now the dominant residual): asked
  publicly about letters she never saw, Vela invents "estavam na gaveta do teu
  escritório, atrás dos mapas" while her own private thought says the opposite
  ("essa pergunta nova me cheira a armadilha") — invented memory contradicting the
  thought layer (S2 `bf5a6902` T32).
- **Impossible knowledge in the thought/narration layer**: an outsider's private
  thought asserts a whisper's CONTENT ("isso foi dito em segredo a Rook" about the
  letters) that the fiction says she never heard; speech stays clean, so only the
  reader sees it (S3 `e6d5be7b` T32). Narration also declares knowledge states
  mechanically ("Ela não ouviu Dario mencionar...").
- **Staging drift**: the shared table splits into "mesas opostas do salão" by the
  final act (S3); Rook oscillates bancos↔mesas (S1); a produced prop (embrulho de
  pano, S2 T1) is never mentioned again; a hand rests on a shoulder for 5 turns.
- **Verbatim duplication**: S3 T6 and T7 share an identical narration paragraph;
  ambient boilerplate ("um gole, um pigarro, o crepitar de uma vela") repeats ~10
  turns.
- **Surface language**: "Doublaram" (anglicism), broken commas from lost dashes,
  "prata meio enferrujada", world-inconsistent season talk (primavera + neve em 12
  dias).

## Additional Evidence (2026-07-15, interactive session `ef6b5b90`)

User-reported unnaturalness in live play (archived at
`plans/artifacts/sofia-alex-identity-leak/session-ef6b5b90/`); identity findings
routed to the 29.2 exploration, prose/flow findings belong here:

- **Direct question left unanswered**: T2, Alex asks "faz o que da vida?"; Sofia
  replies "Haha, relaxa, tô de boa! Mas a pergunta foi boa, hein?" — a
  non-sequitur that dodges the question she was routed to answer; she only
  answers one turn later after being pressed.
- **Near-duplicate private thoughts on adjacent turns** (already-tracked class,
  new instance): T2 "Ele é ousado, gostei. A Fernanda viu, mas tô nem aí." →
  T3 "Ele tá ousadinho, mas eu gosto. A Fernanda percebeu, mas tô nem aí."
- **Narration pre-empts the forced speaker's reply**: T3 and T4 narration both
  end with Sofia "responde num tom provocante" / "responde com um sorriso
  provocante" *before* her speech exists — the narration promises a reply tone
  the Character call has not produced yet.
- **Second-person narration** (already-tracked class, new instance): first
  attempt narration opened "Você entra na sala de estar..." addressing the
  player instead of third person (user undid the turn).
- **Narrator asserts a character's inner sensations as fact**: "sentindo o
  hálito de bebida quente no rosto", "a pele quente sob o tecido" — violates the
  "observable evidence only" rule from its own prompt.

## Additional Evidence (2026-07-16, live session `091b11c6`)

User-reported (archived at `plans/artifacts/session-091b11c6-live-findings/`):

- **Passive narrator / no narrative drive**: the Narrator never advances the
  story on its own; on skip turns it still waits for the player to speak. The
  user had to force events via suggestions or invent events manually because
  the game state stalled. This adds a new defect class to this task: the
  Narrator as *event generator*, not only as prose renderer.
- **Internal ID leaked into prose**: someone addressed a character as "C6" in
  reader-visible text (variable leak; also routed to the 29.2 exploration).
- **Verbatim repetition in short messages**: characters repeated text even in
  not-so-long replies.
- **Role violations**: the Narrator spoke for characters ("furou várias vezes
  narrando fala de personagem"). User assessment: "o narrador é o elo mais
  fraco de todos".
- Larger response budgets (24k narrator / 12k character) measurably improved
  output quality; defaults were raised accordingly (adapters, 2026-07-16).

## Additional Evidence (2026-07-16, blind critic on perspective-smoke runs)

Blind continuity review of 3 takes (`plans/artifacts/perspective-smoke/`,
grades A-/B-/C+). Identity boundary (Task 29.2 inc. 1) passed 3/3; every
finding below is narrator-prose territory:

- **Dialogue leaking into narration (systemic, most reader-visible)**: the
  narration quotes a full character reply inside the italic prose, then the
  character's actual line answers AGAIN differently — double answers, near-
  duplicate phrasing, one soft contradiction (Dona Maria vs. avó do Tom).
  Same class as the "narration pre-empts the forced speaker" finding from
  session ef6b5b90; in the target architecture this dissolves when prose
  renders only confirmed facts (Decision/Prose split).
- **Character re-introduces herself two beats after introducing herself**, and
  re-asks a question the other person just answered ("Então você é amigo
  dele?" right after "eu sou o Rafa, amigo do Tom!").
- **Boilerplate across independent takes**: "Tom é um querido/um amor" in 3/3
  runs; "brincos balançando" as stock gesture (fuzzy-similarity metric would
  catch both).
- **Thought contradicting narration**: Nina's thought claims "Ele me viu.
  Desviou o olhar" while the narration shows only HER looking away.
- **Silent character**: Nina (with a live secret) never routed to speak in any
  take — reads as an inactive agent, not performed indifference (Drive-layer
  evidence, Task 33).

## Additional Evidence (2026-07-16, blind critic on partition-smoke2 runs)

Partition scenario (zones), 2 takes, grades A-/C+ (information partition held
in both; findings below are narrator/character prose):

- **Character invents a stimulus under forced routing with empty perception**
  (pre-fix take): isolated Vitor greeted a nonexistent visitor. The engine now
  fills the perception void with a deterministic statement; residual pressure
  (why route to an isolated character at all) is Drive-layer/Task 33 territory.
- **Narration duplicating dialogue verbatim inside prose** (recurring class,
  new instance: Alice's T3 line quoted twice in one turn).
- **Malapropism**: "delegacia" where "delegação" is meant.
- Praise worth preserving as the target register: "O som não ultrapassa o
  espaço entre eles, dissipando-se no ar do salão antes de alcançar qualquer
  outro ouvido" — narration committing to the acoustic isolation.

## Additional Evidence (2026-07-16, post Decision/Prose split 36.1)

Deterministic measurement on 4 fresh runs: dialogue-in-narration = 0/4
(structurally eliminated — spoken words no longer exist in any prose input).
NEW dominant defect class: near-duplicate narration SENTENCES across turns in
static scenes (6 and 15 instances in the party takes; 0 and 2 in the embassy
takes). The renderer, seeing its own prior prose and a content-free transcript,
re-describes the same tableau. Candidate mitigations for THIS task: fuzzy
retry-guard on generated narration (>0.85 similarity to prior narration →
one correction retry), and/or passing only the last 1-2 narrations as context.
Measure before choosing.

## Additional Evidence (2026-07-17, Task 37 burst live runs)

Three autonomous-burst live runs (4 beats each, `plans/artifacts/burst-live*/`).
The whole-narration fuzzy guard (>0.85, Task 36 closure) plus the burst event
dedupe eliminated the *re-told event* class — but SENTENCE-level verbatim
copying survives both: in run 3 (`burst-live3`), the T3 narration reproduced
two full sentences of T2's narration verbatim ("O som distante de cascos de
cavalo ecoa...", "Os cães começam a latir no quintal.") inside an otherwise
novel paragraph — the whole-text ratio stays under 0.85, so no retry fires,
and the event dedupe cannot help because the copied text comes from the prose
model reading the transcript, not from a duplicated event. Also recurring:
epithet recycling across beats ("lareira quase apagada" 3x, "barba rala" 3x in
run 2) — template-like set-dressing tags in static scenes. Refined mitigation
candidate: apply the fuzzy guard per SENTENCE (>=40 chars, >0.85 vs any prior
narration sentence) instead of per narration; epithet recycling likely needs
the context-narrowing option (pass only the last 1-2 narrations).

## Additional Evidence (2026-07-17, Task 38 portais/estalagem A/B — reopened)

Cross-turn WHOLE-BEAT re-narration is the dominant residual once single-sentence
lexical echo is backstopped: the portais roteiro arm narrated the smoke-statue
forming into 16 shards twice (T6==T8, paraphrased under the 0.8 sentence bar),
and the messenger arrival twice (T3==T4). The narration lexical backstop only
catches per-sentence >=0.8; a paraphrased re-run of a whole beat slips under.
Concrete candidate: generalize the burst's `repeats_event_text` dedup
(perception.py) to regular turns — drop a perception_event that near-matches one
narrated in the last K turns. Also: semantic character-line echo (Nix's
"Senhor Veludo" line T3~T4; Mirella's "geada noturna" x6) and repeated
`action_intent` ("observar discretamente" x3) escape the verbatim character
guard (>=0.88) — harder, needs semantic dedup or an action_intent-aware guard.
