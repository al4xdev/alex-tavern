# An audience model for multi-character speech, validated by a bias-controlled remediation loop

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 08 |
| **Date** | 2026-07-15 |
| **Provider** | DeepSeek V4 Flash, Portuguese, real API |
| **Tasks** | 22 and 24, closed |
| **Status** | Adopted: audience-stamped records are the perception substrate |

## Abstract

Witnessed actions and a whisper/audience model for speech, validated by two-level recall assertions, blind continuity review, and a bias-controlled loop of uncontexted fixer subagents (two cycles). The pipeline closed leak-free; behavioral residuals were routed onward. The audience-stamped record introduced here later became the substrate of the acoustic zone graph (delivered later by Task 29.2 increment 2, `.plan/closed/`) and the structural-isolation benchmarks.

---

## Original report
**Date**: 2026-07-15
**Provider under test**: DeepSeek V4 Flash (`deepseek-v4-flash`), Portuguese, real API
**Scope**: Tasks 24 (fact ingestion visibility) and 22 (speech audience model), closed in
`.plan/closed/`
**Predecessor**: `07-multi-character-memory-retention-2026-07-14.md` (the investigation that
produced the defect list this work remediates)
**Artifacts**: `plans/artifacts/memory_action_fact-run1/`, `plans/artifacts/memory_audience-run-{v1,v2-pos-ciclo1,v3-pos-ciclo2}/`
**Status**: Concluded — architectural information boundary in place; residual behavioral
defects routed to open tasks

### Original abstract

The predecessor investigation established that the engine had no information boundary:
every speech record reached every present character's prompt, while the narrator's
fiction pretended otherwise. This case documents the remediation: (1) making witnessed
`action` records visible to present characters (Task 24), closing the hole where a fact
ingested through the action field was permanently unknowable; and (2) a first-class
**audience model** for speech and action records (Task 22), where a whispered record is
visible only to its listed audience and its speaker. Validation combined deterministic
tests, a two-level real-LLM recall assertion (prompt versus reply), and a blind
continuity review by a clean-context critic. Remediation of failures found during
validation followed a **bias-controlled protocol**: the implementing agent was barred
from fixing its own failures; instead, fixer subagents with no inherited context
received only the open behavioral reports (two cycles authorized, both used). After
cycle 2, no whispered content reached an outsider's prompt through any pipeline path in
9 recall checks across 3 sessions; the single residual failure was *earned knowledge* —
a character electing to say a secret aloud — which is a behavioral defect already
tracked separately.

### 1. Problem statement

From the predecessor case, two confirmed defects:

1. **Task 24** — facts entering history as `action` (e.g., an auto-suggestion submitted
   in the action field, or a shown-then-burned note) were invisible to every character
   forever, because character context selection kept only `speech` plus own `thought`.
2. **Task 22** — no audience concept existed: secrets told to one character appeared in
   every present character's prompt, and the narrator would simultaneously narrate that
   a bystander "did not seem to hear" — fiction/knowledge incoherence, deterministic in
   3/3 runs.

The project is alpha with no legacy constraints; breaking serialization compatibility
was explicitly authorized.

### 2. Design

#### 2.1 Task 24 — witnessed actions (smallest fix)

`_format_history_for_character` (`src/agents/character.py`) now includes `action`
records, labeled `TYPE=ACTION`. Narration remains narrator-only: it is omniscient,
reader-facing prose whose leakage into character context would change both economics
and epistemics. "Witnessed" initially meant "present"; the audience model below refines
it.

#### 2.2 Task 22 — the audience model

- **State**: `TurnRecord.audience: list[str] | None` (`src/models.py`). `None` means
  public (visible to everyone present — the previous behavior, preserved for existing
  records). A list of character IDs makes the record **whispered**. A single predicate,
  `record_visible_to(record, character_id)`, defines visibility: audience members plus
  the speaker.
- **Character context**: speech/action records are filtered by visibility; whispers a
  character did perceive are labeled `WHISPERED ... (confidential, ...)` so the model
  knows the information is privileged.
- **Narrator**: sees everything (it must narrate coherently), with whispered entries
  marked `[WHISPERED, perceived only by: <names>]`, plus system rules forbidding
  outsiders from reacting to whispered content and forbidding its inclusion in
  `context_for_character` for non-audience speakers.
- **Ingestion**: `player_turn(..., audience=[...])` with validation (known, present,
  non-empty; whisper requires speech or action). The API (`PlayerTurnRequest.audience`),
  the playtest harness (`turn`/`recall_check` events), and the transcript renderer all
  carry the field. **Reply inheritance**: when the narrator routes the turn to a
  character inside the whisper's audience, that character's reply keeps the same
  audience — a whispered exchange stays whispered end to end.

### 3. Validation method

Three independent evidence layers, in increasing distance from the code:

1. **Deterministic tests** — visibility, inheritance, serialization round-trip,
   validation errors, and (after cycle 2) 13 tests for the redaction guard. Full suite
   at closure: 341 passed, 2 xfailed (the two strict xfails are the open
   trim/compaction-gap specification, Task 23).
2. **Real-LLM acceptance** — the 33-turn scenario `tools/playtests/memory_focus_xyz.json`
   (secrets whispered to different characters, dense noise, four decoy codes, focus
   alternating X+Y → X+Z → X+Y), three `recall_check` events with two-level assertions:
   `prompt_patterns` (what the character's LLM call actually contained — the pipeline
   layer) versus `reply_patterns` (what it said — the model layer), plus forbidden
   variants; three repetitions per round.
3. **Blind continuity review** — transcripts rendered with whisper markers
   (`tools/render_transcript.py`) and handed to a fresh clean-context agent acting as a
   screenwriter/continuity editor, with no access to code, plans, or prior analyses.

#### 3.1 The bias-controlled remediation loop

Rule set by the project owner: when acceptance fails, the implementing agent must not
fix the failure it just diagnosed. Instead it dispatches a **fixer subagent with no
inherited context**, giving it only the open behavioral reports (and explicitly barring
it from reading `plans/`, `docs/cases/`, `.plan/`, `.claude/`); the main agent reviews
the diff, re-runs the suite, and re-runs acceptance. Two full cycles were authorized.
The rationale is straightforward: the author of a diagnosis tends to implement the fix
their diagnosis presupposes; a cold agent must rediscover the mechanism from the
symptom, which both validates the diagnosis and diversifies the fix.

### 4. Results

#### 4.1 Task 24 acceptance

Scenario `memory_action_fact.json` (a code shown on a parchment via the action field,
then burned; noise with decoys; whispered-free recall test): 3/3 repetitions passed at
both prompt and reply level; the layer localizer traced the `Player/action` record
surviving state → selection → prompt → response; the blind critic confirmed the
knowledge reads as *earned by reading* in all sessions. One methodological note: the
first acceptance round failed 3/3 purely because the reply regex was case-sensitive
("Orquídea-741" versus `ORQU[ÍI]DEA-741`) while raw evidence showed correct recall —
the criterion, not the engine, was fixed (and forbidden patterns were hardened to
case-insensitive in the same change).

#### 4.2 Task 22 acceptance across remediation rounds

| Round | Result (9 checks = 3 checks × 3 reps) | Remaining failure mode |
|---|---|---|
| v1 (audience model only) | 6/6 on the 2 completed reps (1 infra flake: provider returned truncated JSON) | replacement rep: character repeated a whispered secret in a public line one turn later |
| v2 (after cycle 1) | 8/9 | narrator leaked via `context_for_character`: "a senha ORQUÍDEA-741 é desconhecida para você" — a denial that reveals |
| v3 (after cycle 2) | 8/9 | **pipeline clean**; the failing check was earned knowledge: the character said the hideout aloud in public turns, so the other character genuinely overheard |

- **Cycle 1 fix** (uncontexted subagent): "whisper discipline" rules in the character
  system prompt — never expose whispered detail in speech audible outside the whisper;
  never quote a secret while denying it; explicit exception allowing the secret to be
  spoken back to the confidant within a whispered turn.
- **Cycle 2 fix** (uncontexted subagent): a deterministic guard,
  `redact_whisper_leaks()` (`src/agents/narrator.py`), wired at the single point where
  `context_for_character` reaches a character (`src/runner.py`). Secrets are derived
  from history itself: tokens appearing in whispered records invisible to the next
  speaker, minus everything that character legitimately knows (visible speech/action,
  own thoughts, names, scene facts). Rare tokens (≥4 chars, or containing digits) are
  replaced by a neutral marker, case-insensitively, with adjacent markers collapsed.
  Notably, the fixer found a partially written, never-wired version of this guard in
  the working tree (residue of a crashed session), wired it, and closed a whitelist
  hole: narration must never launder a whispered token into "known", since characters
  never receive narration.

#### 4.3 Blind continuity review (final round, 3 sessions)

- Whisper semantics hold as *fiction*: the best session (`f85b5845`) keeps the secret
  through 28 public turns and converts the whisper into drama — the excluded character
  notices the hushed exchange, grows suspicious, and finally demands "o que tu
  cochichaste com a Vela?", which is exactly the intended behavior of a boundary the
  narrator can narrate honestly.
- The trusted-scribe character (Vela) was disciplined in 3/3 sessions: recognized all
  decoys (including plain orchids and the number 741 planted in an unrelated order) and
  produced the password only inside the whispered test.
- Residual defects concentrate in the garrulous-archetype character and in narrator
  prose: public blurting of the whispered hideout (5+ times / 2 times / one partial
  slip across the three sessions), one confabulated "vault password" promoted from a
  public decoy, narration contradicting established public facts, a whisper
  reinterpreted by the narrator as unheard by its own audience, an internal ID ("esse
  tal de C3") leaking into a character's thought, one "diesel" anachronism, and
  verbatim thought loops in long single-character stretches.

### 5. Discussion

1. **Two-level assertions carried the whole investigation.** Prompt-versus-reply
   separation localized every failure to the correct layer within minutes: character
   behavior (v1), narrator generation (v2), earned knowledge (v3). Without it, all
   three rounds would have looked like the same "leak".
2. **Prompt rules degrade under personality pressure; deterministic guards do not.**
   The cycle-1 prompt rule reduced but did not eliminate character leaks; the cycle-2
   code guard eliminated the narrator path outright. Where a boundary can be enforced
   structurally, it should be — prompts are for shaping behavior, not for guaranteeing
   invariants.
3. **The denial-that-reveals pattern recurs at every level** — characters, then the
   narrator, produced it independently. Any future secrecy feature should treat "never
   quote while denying" as a first-class rule and, where possible, a structural check.
4. **The bias-control protocol earned its cost.** The cycle-2 fixer, blind to prior
   analysis, independently rediscovered the leak mechanism, found dead code the biased
   path might have trusted as already working, and shipped it with tests the original
   never had.
5. **Boundary architecture and boundary behavior are different problems.** The audience
   model guarantees who *can* know a secret; it cannot make a talkative character keep
   one. That residual is measurable (reply-forbidden rate) and tracked as its own task.

### 6. Threats to validity

Single provider (DeepSeek V4 Flash; the local llama.cpp host remained offline);
three repetitions bound but do not eliminate sampling variance; the acceptance scenario
scripts player turns with `force_speaker`, so narrator routing under whispers is only
lightly exercised; the redaction guard is token-based and could in principle redact an
innocent rare token that coincidentally appears in a whisper (no such false positive
was observed; short tokens are exempt unless numeric); the continuity reviewer is
itself a model, spot-checked against raw artifacts.

### 7. Reproducibility

```fish
# Acceptance (whispered scenario, all three checks required)
uv run python -m tools.playtest_harness tools/playtests/memory_focus_xyz.json \
  --config-file .data/config.json --language Portuguese --llm-timeout 120 \
  --repeat 3 --output-dir <fresh-dir>
uv run python -m tools.analyze_memory_run <fresh-dir> \
  --marker "ORQU[ÍI]DEA-741" --marker "GIRASSOL-222"
uv run python -m tools.render_transcript <fresh-dir> --out <transcript.md>

# Task 24 acceptance (action-ingested fact)
uv run python -m tools.playtest_harness tools/playtests/memory_action_fact.json \
  --config-file .data/config.json --language Portuguese --repeat 3 --output-dir <dir2>

# Deterministic suite (no LLM): 341 passed, 2 xfailed at closure
uv run pytest
```

The full flow, including the blind-critic protocol, is codified in the project skill
`.claude/skills/memory-playtest/SKILL.md`.

### 8. Conclusions

1. The engine now has a real information boundary: whispered speech/action reaches only
   its audience, replies inherit whisper scope, and a deterministic guard keeps the
   narrator from leaking secrets through transient context. No pipeline path leaked in
   the final round.
2. Witnessed actions are part of character memory; facts can no longer vanish by being
   ingested through the action field.
3. Remaining defects are behavioral (a character choosing to blurt a secret,
   confabulation under interrogation → Task 25) and narrative-quality (narration
   contradicting public facts, ID leakage, anachronisms, verbatim loops → Task 26),
   with the independent trim/compaction gap still specified by strict xfails (Task 23).
4. Methodologically: two-level assertions for layer localization, blind continuity
   review for reader-level truth, and uncontexted fixer agents for bias control proved
   a repeatable remediation loop and are codified in the `memory-playtest` skill.
