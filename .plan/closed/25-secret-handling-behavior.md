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

---

## Closure (2026-07-15)

**Constraint honored (project owner's directive)**: no new preventive system-prompt
rules — the solution is structural. Prompt rules from Task 22's cycle 1 remain as
defense in depth only.

**Implemented**:
- Shared confidentiality module (`src/confidentiality.py`): secrets derived from
  history, never hardcoded. After cycle 1, secrets come from the **informational
  payload** of a whisper (`payload_tokens`): anchors (digit-bearing tokens,
  all-caps code words, mid-sentence proper nouns) plus rare tokens within 7 word
  positions of an anchor. Casual whispered phrasing generates no secrets; a
  whisper with no anchor is not deterministically guarded (documented trade-off).
- **Character output guard** in `act()` (`src/agents/character.py`): when a reply's
  recorded audience does not cover a known whispered secret, one CORRECTION retry
  (same pattern as the physical-action validation), then deterministic redaction
  (`[indistinct]`) as guaranteed last resort — never a failed turn (user's choice).
  Guard events logged (`whisper_output_guard`: retried/redacted + tokens).
- **Whisper-turn marker** (`_whisper_turn_note`): when the reply inherits a whisper
  audience, the turn prompt states "THIS TURN IS A WHISPER ... perceived only by
  {confidants}", anchoring the whisper-exception rule to a deterministic signal.
- Harness: `whisper_leak_records` invariant (character speech/action exposing
  whispered payload = run failure; player spending own secret is exempt) plus
  `whisper_guard_retries`/`whisper_guard_redactions` analysis counters.

**Bias-controlled iteration (2 authorized, 1 used)**: initial acceptance showed the
invariant holding (0 leaks) but 12-13 retries + 3 redactions per session garbling
innocent lines ("para de falar tão [indistinct]" for "alto"), and one case of
over-suppression (Vela describing "começa com sete e termina com um" to her own
confidant). An uncontexted fixer subagent (given only those two reports) designed
the payload derivation and the whisper-turn marker. Two acceptance-criteria
adjustments were made by the main agent with raw-evidence justification: recall
regex made separator-tolerant ("Orquídea 741" vs "-741").

**Validation**:
- Deterministic: 367 passed, 2 xfailed (payload derivation cases, guard retry/
  redaction/confidant paths, end-to-end public-record invariant, harness counters).
- Real-LLM (3 reps, DeepSeek): 9/9 recall checks green; `whisper_leak_records`
  empty 3/3; guard activity 13→1-2 retries, 3→0-1 redactions per session — the
  remaining events are REAL blocks (Vela attempting the password aloud at T4).
- Blind continuity review: password exact in the whispered test 3/3; zero secret
  quotes inside denials; the formerly leaky garrulous archetype (Rook) is now "the
  most reliable character of the three sessions"; the 2 remaining [indistinct]
  occurrences read as acceptable diegetic noise.

**Residuals routed to Task 26**: memory confabulation under interrogation (Vela
inventing "gaveta do escritório", S2 T32); impossible knowledge in the PRIVATE
THOUGHT layer (an outsider's thought asserting a whisper's content, S3 T32 —
thoughts are guard-exempt by design); staging drift (table splitting across the
hall), verbatim-duplicated narration (S3 T6=T7), orphan props, "Doublaram".
Infra note: DeepSeek returned malformed JSON killing ~1 in 3 harness runs
(`retries=0` in agent calls) — harness robustness backlog.
