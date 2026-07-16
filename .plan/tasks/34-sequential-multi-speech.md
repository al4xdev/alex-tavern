# Task 34 — Sequential Multi-Character Speech (no Narrator between speakers)

## Goal

Let one narrated turn route SEVERAL characters speaking in sequence, without a
Narrator call between them. First concrete increment of the Decision-layer
direction in `.plan/tasks/explore-29.2-architecture-map.md`: the Narrator's
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

- [ ] Narrator schema/prompt emit and document `next_speakers`.
- [ ] Normalization unit tests (unknown/dup/Narrator-terminator/cap/forced).
- [ ] Runner test: queue of two characters produces two responses in order and
  the second character's prompt contains the first one's fresh speech.
- [ ] Runner test: queue stops at the controlled character without generating
  their speech.
- [ ] Existing agency/presence/whisper guards unchanged (suite green).
- [ ] Real-LLM smoke run showing a multi-speaker exchange in one turn.
