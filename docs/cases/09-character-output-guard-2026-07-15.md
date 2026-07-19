# A deterministic output guard for whispered secrets: structure over prompt

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 09 |
| **Date** | 2026-07-15 |
| **Provider** | DeepSeek V4 Flash, Portuguese, real API |
| **Task** | 25, closed |
| **Status** | Adopted invariant: zero record-level leaks by construction |

## Abstract

Prompt rules reduced but never eliminated secret leakage under interrogation pressure. This case replaced them with a deterministic retry-then-redact guard on character output, including informational-payload secret derivation and a whisper-turn marker designed by an uncontexted fixer agent. Zero record-level leaks across all measured runs; the structure-over-prompt doctrine stated here recurs in every later case.

---
**Date**: 2026-07-15
**Provider under test**: DeepSeek V4 Flash (`deepseek-v4-flash`), Portuguese, real API
**Scope**: Task 25 (secret-handling behavior under interrogation), closed in `.plan/closed/`
**Predecessors**: `07-multi-character-memory-retention-2026-07-14.md` (investigation),
`08-speech-audience-model-2026-07-15.md` (audience model, Tasks 22/24)
**Artifacts**: `plans/artifacts/memory_outputguard-run-{v1,v2,v3-pos-ciclo1}/`,
`plans/artifacts/transcript-outputguard-v3.md`
**Status**: Concluded — leak invariant enforced by construction; one bias-controlled
fix cycle used (of two authorized)

### Abstract

After the audience model (Task 22) made whispers structurally invisible to outsiders,
one behavioral defect remained: a character who legitimately knows a whispered secret
sometimes says it aloud in public speech, or denies knowing it while quoting it. The
project owner set a binding design constraint before work began: **do not solve this
with prompt engineering** — the previous cycle had already shown prompt rules degrade
under personality pressure. We built a deterministic guard on the character's *output*:
if a reply's recorded audience does not cover a whispered secret the character knows,
the engine issues one correction retry and, failing that, redacts the secret's tokens
from the recorded speech. Initial acceptance confirmed the invariant (zero leaks in
every run) but exposed two implementation defects — vocabulary poisoning by the
whisper's casual phrasing (13 retries and 3 wrongful redactions per session) and
over-suppression (a character withholding the secret from her own confidant). Per the
project's bias-control protocol, an uncontexted fixer subagent received only those two
behavioral reports and redesigned the secret derivation around **informational
payload** (anchor tokens plus a proximity window) and added a **whisper-turn marker**.
Re-evaluation passed 9/9 recall checks with guard interference collapsing to one or two
genuine blocks per session, and a blind continuity review judged the residual redaction
noise diegetically acceptable — while the formerly leaky character became "the most
reliable of the three sessions".

### 1. Problem statement

From the Task 22 closure, measured across its final acceptance round: the garrulous
character (Rook), whispered a hideout location with "só tu sabes", spoke
"GIRASSOL-222" aloud in public turns 5+/2/1 times across three sessions; a character
denied knowing a password while quoting it in full ("só conheço as que me contaste
hoje: ORQUÍDEA-741"). The audience model guarantees who *can* know a secret; it cannot
make a character keep one.

**Design constraint (set by the project owner, verbatim intent)**: the tempting fix is
another prompt rule, and it must not be used — "a solução mais simples é provavelmente
a mais frágil". Empirical basis: Task 22's cycle-1 prompt rule reduced the leak
frequency but never eliminated it.

**Target invariant**: no whispered-secret token enters a history record whose audience
does not cover that secret — by construction, not by instruction.

**Last-resort policy** (owner's decision via explicit option review): redact the
leaking tokens in the recorded speech (`[indistinct]`, reading as diegetic mumbling),
never silently narrow the audience, never fail the turn.

### 2. Design

#### 2.1 Shared confidentiality primitives (`src/confidentiality.py`)

Extracted from the Task 22 narrator guard so both guards share one semantics:
`tokens`, `known_tokens` (everything a viewer legitimately knows: visible
speech/action, own thoughts, names, scene facts — narration deliberately excluded so a
narration leak can never launder a secret), `redact_tokens`, and the two secret
derivations: `hidden_whisper_tokens` (narrator side: whispers the viewer did NOT
perceive) and `secret_tokens_exposed_to` (output side: whispers the speaker DID
perceive whose audience does not cover every exposed listener, minus what all exposed
listeners already know — "earned knowledge" via prior public mention stops being a
secret). The internal "Player" speaker marker counts as the controlled character for
audience-coverage purposes.

#### 2.2 The output guard (`src/agents/character.py`)

Inside `act()`'s existing two-attempt loop (previously used only for the
physical-action validation): after a syntactically valid reply, compute the leaked
set = secrets exposed by this reply's audience ∩ tokens of the speech. If non-empty on
attempt one, retry once with a pointed CORRECTION (reactive, post-violation — the same
established mechanism as the action validator, not a new preventive rule). If still
non-empty, record the speech with the leaking tokens redacted. Private thoughts are
exempt by design. Every guard event is logged (`whisper_output_guard`,
retried/redacted, tokens) for measurement.

#### 2.3 Measurement (playtest harness)

- `whisper_leak_records(game)`: post-run invariant — any character speech/action
  record exposing whispered payload fails the run. Player-typed records are exempt
  (the player may spend their own secret).
- Analysis counters `whisper_guard_retries` / `whisper_guard_redactions` separate "how
  often the model tries to leak" (quality signal) from "how often anything leaks"
  (invariant, must be zero).

### 3. First acceptance round: invariant holds, implementation over-fires

Three repetitions (one lost to a provider JSON flake): `whisper_leak_records` empty in
every completed session — **the invariant held from day one**. But:

1. **Vocabulary poisoning**: 12-13 retries and 3 redactions per session, most of them
   false positives. Mechanism: every rare token of a whispered record counted as
   secret — including the character's *own casual phrasing* in their whispered reply.
   After one whispered exchange, innocent public lines got garbled: "para de falar tão
   **[indistinct]**!" (the word was "alto"), "cê **[indistinct]**" ("sabe"), "aquele
   **[indistinct]** que você cochichou" ("negócio"). Cost: ~40% extra character-call
   volume and reader-visible prose damage.
2. **Over-suppression**: in one session the scribe, asked *in a whispered turn* by her
   own confidant to recite the password, answered "foi orquídea, seguida do número que
   começa com sete e termina com um" — perfect recall, deliberately incomplete
   utterance. Charming fiction, but it violates the task's own acceptance criterion:
   discretion must not suppress recall toward the rightful confidant.

One acceptance-criterion artifact was also found and fixed by the main agent (with raw
evidence): the recall regex required a hyphen while the model answered "Orquídea 741";
patterns were made separator-tolerant.

### 4. Bias-controlled remediation (cycle 1 of 2)

Per the project's protocol, the implementing agent did not fix its own guard. An
uncontexted fixer subagent — barred from reading plans, case studies, or prior
analyses — received only the two behavioral reports above and produced:

1. **Payload derivation** (`payload_tokens`): a secret is the *informational payload*
   of a whisper, not its phrasing. Anchors = digit-bearing tokens, all-caps code
   words, and mid-sentence capitalized proper nouns (a colon deliberately does not
   reset sentence stance, so "o código é: Girassol" still anchors). Payload = anchors
   plus rare tokens within seven word positions of an anchor. A whisper with no anchor
   contributes no guardable secret (documented trade-off: an anchor-less secret falls
   back to prompt-side discipline only).
2. **Whisper-turn marker** (`_whisper_turn_note`): when a reply inherits a whisper's
   audience, the turn prompt states "THIS TURN IS A WHISPER: … perceived only by
   {confidant names} … speak shared secrets openly and completely", and the system
   whisper-exception rule now anchors to that deterministic marker instead of a
   heuristic "latest event" reading. This is a structural signal derived from runner
   state, not a new preventive behavior rule.

### 5. Re-evaluation results

Three repetitions, all green (exit 0):

| Metric | Before cycle 1 | After cycle 1 |
|---|---|---|
| Recall checks | 8/9 (one over-suppression) | **9/9** |
| `whisper_leak_records` | 0 (invariant held) | **0** |
| Guard retries / session | 12-13 | **1-2** (and now mostly *real* blocks — e.g. the scribe attempting the password aloud in a public turn) |
| Wrongful redactions / session | 3 | **0-1** (residual: "está" adjacent to an anchor) |

**Blind continuity review** (clean-context critic, transcript only): password exact in
the whispered test in 3/3 sessions; zero secrets quoted inside denials; the previously
leaky garrulous character is now "o personagem mais confiável das três sessões",
deflecting the final interrogation three different correct ways ("você nunca me deu
senha nenhuma", "se leva para o túmulo", "já teria esvaziado seus cofres e comprado uma
ilha"). The two remaining `[indistinct]` occurrences across ~99 turns read as
"acceptable diegetic noise", with the sharp observation that their *repetition pattern*
(both at turn 4) is what betrays an artifact — a calibration note, not a defect
verdict.

### 6. Discussion

1. **The constraint was right.** The structural guard achieved in one round what two
   generations of prompt rules could not: a leak rate of literally zero, measured at
   the record level, robust to personality pressure. The prompt layer's proper role is
   shaping *how* a character deflects; the engine's role is guaranteeing *that*
   nothing leaks.
2. **Deterministic guards need a theory of what a secret is.** "Every rare word of the
   whisper" was the wrong theory and taxed both cost and prose. "Informational payload
   around anchors" is a better one, and it came from an agent that had never seen our
   prior reasoning — the bias-control protocol again produced a design its
   originators had not considered.
3. **Retry-then-redact is a good escalation shape.** The retry gives the model a
   chance to stay eloquent (most events end there); redaction guarantees the
   invariant; neither ever blocks a turn.
4. **Residual defects moved up a layer.** With speech sealed, the failures the blind
   critic still found live in the thought/narration layer (an outsider's private
   thought asserting a whisper's content; confabulated memories under interrogation)
   and in staging/prose quality — all routed to Task 26 with turn-level citations.

### 7. Threats to validity

Single provider (DeepSeek V4 Flash); three repetitions per round bound but do not
eliminate sampling variance; the payload window (7) and anchor heuristics were
calibrated on Portuguese transcripts of this scenario family; anchor-less secrets are
knowingly outside the deterministic guarantee; recurrent provider JSON flakes killed
roughly one run in three (agent calls use `retries=0` — harness robustness noted as
backlog); the continuity reviewer is itself a model, spot-checked against raw
artifacts.

### 8. Reproducibility

```fish
uv run python -m tools.playtest_harness tools/playtests/memory_focus_xyz.json \
  --config-file .data/config.json --language Portuguese --llm-timeout 120 \
  --repeat 3 --output-dir <fresh-dir>
# whisper_leak_records must be [] in every run; recall checks 9/9
uv run python -m tools.render_transcript <fresh-dir> --out <transcript.md>
uv run pytest   # 367 passed, 2 xfailed at closure
```

Full flow, including the blind-critic protocol, in `.claude/skills/memory-playtest/SKILL.md`.

### 9. Conclusions

1. Whispered secrets are now protected end to end by construction: selection filter
   (Task 22), narrator context guard (Task 22 cycle 2), and character output guard
   with retry-then-redact escalation (this task) — zero leaks at the record level
   across every measured run.
2. Secret derivation must target informational payload, not phrasing; anchors plus a
   proximity window eliminated vocabulary poisoning while keeping every real block.
3. A deterministic turn-level signal ("this turn is a whisper") resolved the
   confidant-recall ambiguity that a system-prompt rule alone could not.
4. The bias-control loop (uncontexted fixer, evidence-only briefs) delivered the key
   design insight for the second time in two tasks and is now standard practice for
   this project's behavioral fixes.
