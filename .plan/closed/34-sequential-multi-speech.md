# Task 34 — Sequential Multi-Character Speech (no Narrator between speakers)

## Goal

Let one narrated turn route SEVERAL characters speaking in sequence, without a
Narrator call between them. First concrete increment of the Decision-layer
direction in `.plan/reference/explore-29.2-architecture-map.md`: the Narrator's
routing output becomes an ordered queue, and later speakers react having heard
the earlier ones. Requested by the user 2026-07-16 ("pode deixar nessa update
múltiplos personagens falarem em sequência sem o narrador").

## Design

- Narrator contract (forward-only, no compatibility path): `next_speaker: str`
  is replaced by `next_speakers: array` (1..3, enum of present IDs +
  "Narrator"). JSON-schema-first per the model guidance: deepseek-v4-flash
  fills typed contracts better than free text.
- Normalization in `narrator.act`: drop unknown/absent entries, dedupe
  preserving order, truncate at "Narrator" (nothing speaks after "no one
  reacts"), cap at 3, empty -> ["Narrator"]. `force_speaker` -> [forced].
- Runner executes the queue sequentially: each response is appended to history
  BEFORE the next character call, so speaker N+1 perceives speaker N's speech
  through the normal visibility filter. The queue stops at the controlled
  character (human agency preserved). `context_for_character` goes to the
  FIRST speaker only; later speakers rely on the fresh history (prevents the
  Narrator from pre-scripting replies it has not seen, a Task 26 defect).
- Turn result contract: `character_responses: [{character_id, speech,
  thought}]` + `next_speakers: [...]` replace `character_response` +
  `next_speaker`. Frontend renders the list.
- Whisper semantics per speaker: reply-audience inheritance applies to each
  queued speaker independently (same formula as before).

## Acceptance Criteria

- [x] Narrator schema/prompt emit and document `next_speakers`. —
  `build_narrator_json_schema`; `TestValidSpeakers` in `test_integration.py`
- [x] Normalization unit tests (unknown/dup/Narrator-terminator/cap/forced). —
  `test_valid_speakers_accepts_custom_id`, `test_valid_speakers_fallback_invalid`,
  `test_forced_narrator_collapses_queue`, `test_forced_speaker_constrains_schema_and_context_target`
- [x] Runner test: queue of two characters produces two responses in order and
  the second character's prompt contains the first one's fresh speech. —
  **also confirmed live on 2026-07-27**, see the section at the end
- [x] Runner test: queue stops at the controlled character without generating
  their speech. — `test_autonomous_burst.py::test_stops_when_player_is_addressed`
  (`player_addressed`, no speech generated for the controlled character)
- [x] Existing agency/presence/whisper guards unchanged (suite green). — suite
  at 918 tests; `test_absent_next_speaker_never_receives_a_character_call`
- [x] Real-LLM smoke run showing a multi-speaker exchange in one turn. —
  the xfailed3 campaign of 2026-07-27 (cast of 9), see the section at the end

> **CLOSED 2026-07-16** (commit ae0e001). Delivered: next_speakers queue (1-3,
> ordered), sequential execution with fresh-history perception between
> speakers, agency stop at the controlled character, force collapse under
> plugin filters. Real-run evidence: narrator routed [C3,C2,C4] in one turn
> with genuine interplay (plans/artifacts/task34-smoke). Residual test-fake
> updates delegated to the test-fixing model.


---

# Verified live (2026-07-27, xfailed3 campaign `8484d749`)

The two real-run criteria were blank. I ran the 24-turn campaign with the real
provider and a cast of **9 characters** — the right scenario for this, unlike the
2-character sessions of the other measurements.

**The sequential proof.** Two turns fired two character calls in a queue, and in
both the second character received the first one's **fresh** speech in their own
prompt:

| turn | queue | first speaker's fresh speech in the second's prompt |
|---|---|---|
| 19 | Dorothy → Dama do Norte | yes |
| 23 | Watson → Dama do Norte | yes |

## The measurement error this corrected

My first metric counted *turns with 2+ distinct speakers in the history*. It gave
20 of 24 turns — a flattering number, and **wrong**. Turn 5 has four speech records
(Player, Van Helsing, Alice, Dama do Norte) and **one single** character call: the
other three are `audible_speech` written by the Director and persisted as speech.

Those are two different mechanisms with the same appearance in the history. Task
34's criterion is about the call queue, not about how many names appear speaking.
Measured by mechanism, the real number is 4 turns with 2+ calls, of which 2 are a
genuine queue — the other two are the same character called twice, which is a
**guard retry**, not a queue.

Third time tonight that a surface metric disagreed with the mechanism (the others:
mentions vs vocatives in 54, and the agent-name filter in 38). The pattern is
consistent enough to become a rule: when the criterion speaks about a mechanism,
count the mechanism in `debug.jsonl`, never its effect on the state.

> **Reproducibility caveat (2026-07-27).** The sessions cited in this section were
> generated in a temporary directory and **are not in the repository**: the numbers
> are not auditable by a third party or by a future session. I checked them at the
> time of execution and the method is described above in enough detail to be
> redone, but whoever re-reads this should treat them as an *account*, not as
> verifiable evidence. Measurements that need to count as proof have to write their
> artifacts into `docs/` or `.plan/`, or the criterion must require an acceptance
> script in `tools/acceptance/` that anyone can run.
