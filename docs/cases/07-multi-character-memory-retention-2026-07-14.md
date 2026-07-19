# Multi-character memory retention under alternating narrative focus: a failed reproduction with a real finding

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 07 |
| **Date** | 2026-07-14 |
| **Provider** | DeepSeek V4 Flash, Portuguese, real API |
| **Runs** | 3 independent sessions, 33 turns each (artifact dirs `-run1/` and `-run2/`; run2 holds two repetitions, numbered Runs 2 and 3 in the tables) |
| **Status** | Reported defect did not reproduce; latent findings routed to Tasks 22-26 |

## Abstract

A controlled attempt to reproduce a reported multi-character recall loss. The reported defect did not reproduce in three independent 33-turn runs; the experiment instead demonstrated the absence of an information boundary between characters (any character could answer with another's private facts) and a latent trim/compaction gap. Both findings became tasks and later structural fixes (audience model, output guard, perception ledger).

---

## Original report
**Date**: 2026-07-14
**Provider under test**: DeepSeek V4 Flash (`deepseek-v4-flash`), Portuguese, real API
**Runs**: 3 independent sessions of the same 33-turn scenario
**Artifacts**: `plans/artifacts/memory_focus_xyz-run1/`, `plans/artifacts/memory_focus_xyz-run2/`
**Status**: Concluded — reported defect not reproduced; two distinct defects confirmed

### Original abstract

A user-reported anomaly claimed that in a three-character session (X, Y, Z all present
throughout, no compaction, no presence edits, under ~30k tokens), character Y could not
recall a fact that X had confided early in the session after the narrative focus had
alternated X+Y → X+Z → X+Y. We built a deterministic reproduction harness (a scripted
33-turn scenario with unique per-pair facts, decoy codes, and dense noise), a two-level
recall assertion that separates pipeline loss from model recall failure, a four-layer
loss localizer, and a blind narrative evaluation protocol. Across three real-LLM runs the
reported defect **did not reproduce**: the planted fact survived every pipeline layer and
the target character recalled it verbatim in 3/3 runs. The experiment instead confirmed
two different defects: (1) a deterministic absence of any information boundary — every
speech record reaches every present character's prompt, even when the narrator's own
fiction asserts a character did not hear it; and (2) an independent, latent
trim/compaction gap that silently drops the oldest history from character context in
long sessions with no summary fallback.

### 1. Problem statement

Reported behavior (original session data lost; scenario reconstructed from the report):

1. **Phase A** (focus X+Y): X reveals a unique fact to Y ("my vault password is …").
2. **Phase B** (focus X+Z): many turns of unrelated conversation; Y remains in the scene
   but out of narrative focus.
3. **Phase C** (return to X+Y): X asks Y for the fact; Y does not recall it.

Constraints asserted by the reporter: no compaction occurred, no character was removed
(`set_presence` never used), the session stayed under ~30k tokens, provider was DeepSeek.

#### 1.1 Prior static analysis

Code inspection before the experiment established (verified against the tree at the time):

- A character's prompt is built from the **full** session history
  (`src/runner.py` → `character_act`); the only filter is by `content_type`
  (`src/agents/character.py`): every `speech` from every speaker is kept, plus the
  character's own `thought` records; `narration` and `action` records never reach any
  character.
- There is **no** filter by presence, focus, addressee, or recency window in the
  character path; `present_characters` only gates who may be selected as next speaker.
- `trim_history_by_tokens` (`src/models.py`) drops oldest records beyond a budget of
  `0.7 × context_max − max_tokens_character`. With the DeepSeek defaults
  (`context_max = 524288`, `max_tokens_character = 2048`) the budget ≈ 367k tokens, so a
  <30k-token session cannot trigger trimming.
- Automatic compaction defaults to disabled; when enabled, its threshold (80%) sits
  **above** the trim point (70%), and `compaction_keep_recent_turns = 200` blocks any
  session shorter than 200 turns.

These facts predicted the reported loss should be impossible under the stated
conditions — motivating a controlled reproduction attempt rather than a speculative fix.

### 2. Method

#### 2.1 Instrumentation

Four pieces were added to the toolchain (all merged with deterministic unit tests):

1. **Two-level recall assertions** — a new `recall_check` playtest event
   (`tools/playtest_harness.py`) that runs a normal turn and then matches regex patterns
   against (a) the exact prompt the character's LLM call received and (b) the reply it
   produced, including forbidden-pattern variants. `prompt` failures localize a loss
   before the provider (state, selection, or prompt assembly); `prompt` success with
   `reply` failure isolates model recall failure. A check with zero character calls
   fails by construction, so routing failures cannot masquerade as success.
2. **Session invariants** — after any scenario containing recall checks, the harness
   asserts: empty `compaction_stack`, empty `story_summary`, empty
   `presence_edit_stack`, and identical `present_characters` across every history
   snapshot. This mechanically proves the "no compaction / no removal / no reload"
   preconditions of the report.
3. **Four-layer loss localizer** (`tools/analyze_memory_run.py`) — given a run
   directory and a marker regex, reports the marker's survival per layer:
   **STATE** (persisted history) → **SELECTION** (the content-type filter plus token
   trim, recomputed offline) → **PROMPT** (actual request messages in `debug.jsonl`) →
   **RESPONSE** (what the character said). The first layer where the marker disappears
   is the locus of the defect.
4. **Blind narrative evaluation** — `tools/render_transcript.py` renders a session as a
   screenplay (narration, dialogue, actions, marked private thoughts; no prompts, code,
   or configuration). A fresh reviewer agent with **no inherited context** receives only
   the transcript and a short description of the intended scenario, and reports as a
   screenwriter/continuity editor on memory naturalness, behavioral consistency,
   impossible knowledge, fact confusion, focus-switch continuity, and reader-visible
   discontinuities.

#### 2.2 Scenario design

`tools/playtests/memory_focus_xyz.json`: three characters — Dario (X, player-controlled),
Vela (Y), Rook (Z) — all present at the same tavern table for the entire session; focus is
alternated purely by `force_speaker`, never by presence edits.

- **Phase A1** (X+Y, 4 turns): X plants the pair-exclusive fact
  `ORQUÍDEA-741` (vault password) with an explicit secrecy request.
- **Phase B1** (X+Z, 10 turns): X plants a second pair-exclusive fact
  `GIRASSOL-222` (hideout location) plus decoy codes `LÓTUS-999`, `TULIPA-333` inside
  dense, 300–400-character logistics chatter.
- **Phase A2** (X+Y, 6 turns): unrelated conversation engineered for interference —
  plain orchids as flowers, and the number 741 recurring in an unrelated candle order.
- **Phase B2** (X+Z, 10 turns): more noise plus fresh decoys `JASMIM-108`, `DÁLIA-654`.
- **Phase C** (3 recall checks): (1) Y must reproduce `ORQUÍDEA-741` and must not emit
  any decoy; (2) Y must not know `GIRASSOL-222` at either prompt or reply level;
  (3) Z must not know `ORQUÍDEA-741` at either level.

Checks 2 and 3 encode the *desired* information-boundary behavior and were expected to
fail under the current architecture; they are kept `required: true` deliberately, as the
playtest-level equivalent of a strict `xfail`.

#### 2.3 Execution

Three runs against the live DeepSeek API (one run, then `--repeat 2`), 66 LLM calls per
run, zero LLM errors, full artifacts retained (session state, `debug.jsonl`, manifests,
markdown reports, transcripts).

### 3. Results

#### 3.1 Recall of the planted fact (the reported defect)

| Run | Session | Prompt contains fact | Reply contains fact | Verdict |
|---|---|---|---|---|
| 1 | `8bcccf1d` | yes | yes ("ORQUÍDEA-741 … como uma flor que não murcha na minha memória") | recall OK |
| 2 | `50bb264a` | yes | yes | recall OK |
| 3 | `ff8b7dd6` | yes | yes | recall OK |

The layer localizer confirms no loss anywhere: the marker is persisted as `speech`,
survives the selection filter and trim, appears in Y's actual request at the test turn,
and appears in Y's reply — in all three runs. No decoy code was ever substituted for the
real one; hard facts (codes, quantities, deadlines) never corrupted in any session.

**The reported defect did not reproduce.**

#### 3.2 Information boundary (checks 2 and 3)

Deterministic failure at the **prompt layer in 3/3 runs**: `GIRASSOL-222` was always
present in Y's prompt and `ORQUÍDEA-741` always present in Z's prompt, because the
selection layer forwards every speech record to every present character by design.

Reply-level leakage was **stochastic**: in run 1 both characters revealed the other
pair's secret when asked; in run 2 rep 1 only Y leaked; in run 2 rep 2 only Z leaked —
including the self-defeating pattern of denying knowledge while quoting the secret
("só conheço as que me contaste hoje: ORQUÍDEA-741. Mas essa foi para a Vela").

Session invariants were clean in 3/3 runs (no compaction, no presence edits, stable
participant set), mechanically satisfying the report's preconditions.

#### 3.3 Blind narrative evaluation

The clean-context reviewer (three sessions, transcript-only) converged on the same
diagnosis from the fiction side: *"the recurring problem is not memory, it is
information boundary and staging coherence."* Key observations:

- **Fiction/knowledge incoherence (run 1)**: the narrator asserts Rook "does not seem to
  hear" the whispered password (T1) and later narrates Rook mentally listing
  `ORQUÍDEA-741` among codes he heard (T9); Rook then references it in dialogue (T6).
  The narrator's fiction promises a boundary the pipeline does not implement.
- **Self-inflicted secrecy violations (run 2)**: Y repeats the password aloud in front
  of Z (T15/T17 in `50bb264a`; T3 in `ff8b7dd6`) one scene after promising secrecy, and
  in `ff8b7dd6` later denies having overheard a conversation the narration shows her
  attentively watching (T32 vs T6).
- **Reader-visible style defects**: verbatim-duplicated private thoughts (T6/T7 and
  T21/T22 in `ff8b7dd6`), formulaic narration reused across turns, staging jumps (a
  character walks to the door and reappears seated), second/third-person oscillation,
  and one costume transfer between characters (T19, `ff8b7dd6`).

#### 3.4 Independent finding: the trim/compaction gap

Unrelated to this scenario (trimming never fired at DeepSeek's budget), static analysis
plus targeted tests confirmed a latent defect for long sessions or small-context
providers: `trim_history_by_tokens` silently drops the oldest speech at ~70% of
`context_max` with no summary fallback, while automatic compaction (the mechanism that
would preserve evicted content in `story_summary`/`character_notes`) is disabled by
default, thresholded *after* the trim point (80% > 70%), and blocked below 200 turns.
This gap will manifest exactly as the reported symptom once a session outgrows the trim
budget. It is documented as two `xfail(strict=True)` specification tests in
`tests/test_memory_retention.py`, which double as acceptance criteria for a future fix.

### 4. Discussion

#### 4.1 Explaining the original report

With the pipeline exonerated under the stated conditions, two hypotheses remain for the
lost original session, both actionable:

1. **Wrong content type at ingestion**: a fact recorded as `action` or `narration`
   (e.g., an auto-suggestion submitted in the action field) is invisible to every
   character forever — behavior pinned by
   `test_action_and_narration_facts_are_invisible_to_characters`. This failure mode is
   consistent with the reporter driving the session through narrator auto-suggestions.
2. **Stochastic model recall failure** on that particular run — indistinguishable in
   hindsight without the session's `debug.jsonl`.

Should the symptom recur, the `/memory-playtest` skill localizes the losing layer from
the affected session's own artifacts in minutes.

#### 4.2 Design implication

The confirmed boundary defect is architectural, not a bug in any single function: the
engine has no representation of speech audience. The narrator already *narrates* selective
hearing; the state model cannot express it. A fix requires an audience/whisper model on
speech records (narrator, character prompt assembly, and history schema), which is a
product decision rather than a minimal correction — and was deliberately not attempted
in this pass (one cause per fix, evidence first).

### 5. Threats to validity

- **Single provider**: all runs used DeepSeek V4 Flash; the local llama.cpp host was
  offline. Cross-model consistency remains untested.
- **Stochasticity**: three runs bound but do not eliminate sampling variance; the recall
  result is 3/3, not a proof.
- **Synthetic scenario**: scripted player turns with `force_speaker`; narrator routing
  quality was not exercised.
- **LLM-based narrative evaluation**: the continuity reviewer is itself a model; its
  transcript citations were spot-checked against the artifacts.

### 6. Reproducibility

```fish
# Full pipeline (see .claude/skills/memory-playtest/SKILL.md)
uv run python -m tools.playtest_harness tools/playtests/memory_focus_xyz.json \
  --config-file .data/config.json --language Portuguese --llm-timeout 120 \
  --repeat 3 --output-dir <fresh-dir>
uv run python -m tools.analyze_memory_run <fresh-dir> \
  --marker "ORQU[ÍI]DEA-741" --marker "GIRASSOL-222"
uv run python -m tools.render_transcript <fresh-dir> --out <transcript.md>

# Deterministic suite (no LLM): 316 passed, 2 xfailed at time of writing
uv run pytest
```

Supporting documents: `plans/artifacts/memory_focus_xyz-relatorio.md` (decision log,
Portuguese), `plans/artifacts/memory_focus_xyz-avaliacao-narrativa.md` (full narrative
evaluation, Portuguese), raw run artifacts under `plans/artifacts/memory_focus_xyz-run*/`.

### 7. Conclusions

1. The memory pipeline is healthy for the reported conditions: append-only state, no
   focus/presence filtering, no trimming at DeepSeek budgets, verbatim recall in 3/3
   real runs under aggressive interference.
2. The engine's dominant defect is the **absence of an information boundary** — every
   present character receives every speech, while the narrator's fiction pretends
   otherwise (deterministic, product-level).
3. A latent **trim/compaction gap** will reproduce the reported symptom in long
   sessions; it is specified by strict xfail tests awaiting a dedicated fix.
4. Secondary quality issues (characters revealing secrets while denying them, boilerplate
   narration, duplicated thoughts, staging jumps) are reader-visible and partially
   downstream of (2).
