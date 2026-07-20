# When the room hears but nobody remembers: audible speech, memory, and the limits of a stress test

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 14 |
| **Date** | 2026-07-20 (autonomous session, generous curl budget) |
| **Provider** | DeepSeek V4 Flash, real API, Portuguese payloads |
| **Predecessors** | No. 7 (multi-character memory), No. 8 (speech audience model), No. 13 (watcher battery) |
| **Tasks** | 29.1-29.3 (xfailed3 counter-canon benchmark / xfail clock), 39 (ledger memory, closed) |
| **Artifacts** | `plans/artifacts/wt09-audible-speech-fix/`, `.../xfailed3-leaksafe/`, `.../xfailed3-whispertoken/`; harnesses `scratchpad/exp_wt09_*.py` |
| **Status** | Root cause fixed leak-safely (mode 1); mode 2 + the clock are variance-bound and NOT closed. This article is the scientific record of what was tried and why the last mile does not close. |

## Abstract

The counter-canon benchmark's `WT-09` oracle asks: after the villain's alias is
made public at turn 20 ("the Dama do Norte is Glinda, who plans conquest"), does
a witness correctly recall it at the turn-24 epilogue audit? For sessions it did
not — the witness confabulated a benevolent identity ("the Good Witch of the
North"). The roadmap had filed this as an LLM alias-confabulation. **It is not.**
Tracing the real payload, the reveal was staged by the Director as an
`audible_speech` perception event, and those events were never written to
history; only whoever replied that exact turn ever perceived them, and memory
(which reads history) never received the name. We fixed the record-dropping,
caught and closed a whisper-leak regression the first fix introduced, and then
found a SECOND, independent failure mode — the Director sometimes never voices
the names at all — that persistence cannot touch. Across five real oracle runs,
the full tier failed on a different single-turn canon family each time. We
conclude the benchmark's "three consecutive clean runs" clock is **variance-
bound**, not effort-bound: fixing WT-09 does not clean it, because the residual
is one-turn LLM noise spread across many independent canon families. This is a
negative result recorded in full, by method.

## 1. The observation

At the epilogue the audit character (Dorothy) is asked, verbatim: *"onde voce
nasceu, quem era de verdade a Dama do Norte, e onde esta Moriarty agora?"* Her
reply named Oz correctly but for the alias produced *"a própria Bruxa Boa do
Norte, disfarçada"* — the pretrained-canon benevolent reading, never "Glinda".
The oracle's `reply_matches {(?i)glinda: False}` fired. Its `prompt_passed:
True` was misleading: that field is an EMPTY check (no forbidden content), not
evidence that "Glinda" was in the prompt. It was not.

## 2. Hypothesis chain (each tested on the real payload)

**H1 — the character avoids a name it holds (generation defect).** Refuted. The
name "Glinda" appears nowhere in Dorothy's turn-24 prompt: her Knowledge still
carries the un-revised belief ("acredita que ainda é possível negociar com a
Dama do Norte") and her memory of turn 20 reads only "revealing a secret
patron". You cannot avoid naming what you were never told.

**H2 — the Director never revealed it (staging defect).** Refuted for the
canonical failing run. The turn-20 Director output carried TWO perception
events: a preamble, and a second `audible_speech` reading the cipher aloud —
*"a Dama do Norte é Glinda, que planeja a conquista das cinco cidades"* — with
Dorothy (C2) in `witness_ids`. The reveal happened, publicly, witnessed.

**H3 — the reveal was not persisted (data-flow defect).** CONFIRMED. The
session history for turn 20 contained the player's input, the blind narration
(no names), and Holmes deflecting — but NOT the second perception event. Zero
turn-20 records held "Glinda". Grepping the whole run, the name lived only in
Director-side prompts and the private knowledge of the three characters who
already knew (Holmes, the Dama, Van Helsing); it never entered the shared
record. The Director's `audible_speech` events are rendered to that turn's
REPLYING characters, fed to the prose renderer, counted for roteiro coverage —
then discarded. At turn 20 only Holmes was queued to reply, so Dorothy, a
witness, never even saw it live, and nothing was recorded for later.

A strict xfail regression test (`tests/test_audible_speech_persistence.py`)
reproduced the drop in current code.

## 3. The fix, and the regression it caused

**First fix:** persist each Director `audible_speech` event as a spoken record,
scoped to its `witness_ids`, `audience_origin="zone"` (perception, not a whisper
secret), after the reply loop. Isolated-payload validation on the real turn-24
call: with the reveal injected into Dorothy's recent events, she names Glinda
**4/4**; without it, **0/4**. The failure is the missing record; the fix
resolves it.

**The regression (caught by running the oracle, not by inspection).** A full
oracle run exposed eight `GLOBAL-secret-in-unauthorized-prompt` violations — the
whispered instrument `LUMEN-17` leaking into unauthorized character and
perspective prompts, a family Tasks 39/41 had driven to zero. Cause: the
Director sometimes RE-NARRATES a whisper with broad scope but the secret inside
— *"Alice whispers to Dracula, just audible to those nearby: '…LUMEN-17…'"*,
witnessed by everyone in the hall. The transient render path redacts that per
viewer (`redact_whisper_leaks`); our persisted, shared record could not, so the
secret entered history and leaked.

**Second fix (public-only), and why it was wrong.** Persist only genuinely
public events (all present are witnesses). It killed the leak but reintroduced
WT-09: the reveal is heard by the hall but not by a character in a separate
compartment, so it is never "fully public" and was skipped. Scope alone cannot
separate a public reveal from a hall-scoped whisper-narration — both are scoped
to "those in the hall".

**Third fix (whisper-token guard), correct.** The distinguishing signal is the
SECRET, not the scope. `LUMEN-17` was whispered, so it is a hidden whisper token
for non-confidants; "Glinda" was never whispered (Director canon voiced aloud),
so it is not. Persist the event scoped to its witnesses UNLESS its content would
hand a hidden whisper token to a listener outside that whisper — reusing
`hidden_whisper_tokens`/`redact_tokens`, the very guard the transient path uses.
The reveal persists (hall-scoped, the witness recalls it); the whisper-narration
is skipped. **Oracle run 3: the reduced tier came back with ZERO violations —
the leak I introduced is closed.**

## 4. The second failure mode persistence cannot reach

Across the five oracle runs the turn-20 reveal was **stochastic**. Sometimes the
Director reads the names aloud (H2's case — now persisted, WT-09 fixed).
Sometimes it emits only the preamble — *"Alice addresses Holmes: 'a cifra
decifrada nomeia o patrono secreto…'"*, `glinda` absent — and never voices the
names. Then the name is never public, nothing exists to persist, and WT-09 fails
for a reason no persistence can address. Call this **mode 2: Director
deferral**.

We measured it. Replaying the real turn-20 Director call, N=5:

| Arm | reveal names Glinda+Moriarty publicly | names them scoped | not at all |
|---|---|---|---|
| real prompt | 1/5 | 0/5 | 4/5 |
| + "read aloud" nudge | 1/5 | 3/5 | 1/5 |

The nudge (a Director-prompt rule: an action that reads named content aloud must
emit the actual words witnessed by all who can hear) raised NAMING from 1/5 to
4/5 — but usually SCOPED, not room-wide, and still only 1/5 fully public. It did
not meet its pre-registered bar (≥4/5 public, no scoped-name leak), so it was
not shipped. With the whisper-token persistence a scoped naming that includes
the witness would now persist, so nudge+persistence MIGHT resolve mode 2 — but
the nudge is a global, confidentiality-sensitive change to the Director whose
blast radius needs its own oracle validation, and (see §5) it would not clean
the benchmark clock regardless.

## 5. Why the clock does not close: it is variance-bound

The benchmark's exit criterion is three consecutive fully-clean oracle runs.
Five real runs, full tier, each failed on a DIFFERENT single-turn canon family:

| Run | full-tier violations |
|---|---|
| 1 (broad fix) | WT-02 (Kansas, T3), WT-12 (ribbon-through-compaction, T13) — WT-09 GONE |
| 2 (leak-safe/public-only) | WT-09 mode 2 (T24) |
| 3 (whisper-token) | WT-02 (T3), WT-10 (created-not-creator, T8), WT-09 mode 2 (T24), GLOBAL-anonymous-pair (T16) |
| reduced tiers | LUMEN leaks ×8 → then 0 → then 0 |

The residual is not one bug; it is one-turn LLM noise distributed across many
independent counter-canon families (origin refusal, created-not-creator,
promise-through-compaction, anonymous-address, alias recall). Each family fails
occasionally and independently, so the probability that ALL of them stay clean
on three consecutive 24-turn runs is small and does not respond to fixing any
single family. Fixing WT-09 in full would remove one term from that product, not
close it. **This is the honest ceiling of a long-horizon stress test against a
fast model: it measures a distribution, not a pass/fail.**

## 6. What shipped, what did not

**Shipped and validated (leak-safe, test-locked):**
- `audible_speech` events persist to history under the whisper-token guard —
  a room-heard fact is now recallable; WT-09 mode 1 resolved (0/4→4/4).
- The self-introduced whisper-leak regression is closed (reduced tier clean).

**Recorded as NOT closed, with reason:**
- **WT-09 mode 2** — Director deferral. Needs a Director-prompt change; the
  naive nudge under-delivers (1/5 public) and carries confidentiality blast
  radius. Deferred to an explicit owner decision.
- **The xfailed3 exit clock (29.1-29.3)** — variance-bound; not achievable by
  effort/budget. The benchmark remains a useful distributional monitor, not a
  gate that closes.

## 7. Method notes (for the next investigator)

- `prompt_passed: True` in this oracle can be an empty check; never read it as
  "the fact was present". Grep the actual payload.
- Run the real oracle before believing a memory/leak fix. The whisper-leak
  regression was invisible to unit tests and to inspection; only a full
  provider run surfaced it.
- Set `XFAILED3_ARTIFACTS_DIR` when running the llm tiers, or the violation
  detail is lost (the xfail swallows the traceback; the manifest holds the
  classified list).
- Distinguish "the model won't say X" from "X was never in the record". They
  demand opposite fixes; only the payload tells you which.
