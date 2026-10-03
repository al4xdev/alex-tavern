# Character-based move suggestions

Objective: compare existing speech/action drafts with three alternatives produced by
Character.act, preserving its perception, memory, relationships and output guards.
The implementation is isolated in the character-suggestions worktree.

Candidate: three concurrent calls using the unchanged Character system prompt and
schema, with a dialogue, physical-attempt, or reflective possible-next-move suffix.
Return speech/thought/action drafts. Nothing executes or changes session state.
No Director speech mandate or screenplay impulse is imposed on the human's draft.
Raw canonical scene facts are excluded; Character's perceived history supplies events.

Before any provider call: select two current-schema real sessions with at least
five records, one shorter and one longer. Snapshot them read-only once. Compare
baseline (checkpoint's exact suggest_moves) and final production candidate three
times per session. Use curl as the transport for the actual production client so
language, provider schema adaptation and guard retries are exercised unchanged.
Credentials enter curl through stdin, never argv or recorded artifacts.
All logs/output are isolated here; source session files must remain byte-identical.

Decision rule: retain only if all six candidate groups return three nonempty,
editable alternatives, with no operator/ID/private-other-thought leakage in requests,
no invented outcomes or forbidden secrets in drafts on human reading, and the
candidate is preferable in at least four of six paired groups for in-character
specificity, scene relevance and meaningful choice. A blinded independent reader
judges A/B without code or this implementation rationale. A tie is not a win.
This small pilot establishes usefulness in these snapshots, not universal superiority.

Technical checks: full Python checks and pytest; frontend module parsing, registry
and HTML checks; execute suggestion selection and verify all three fields fill,
including a thought-only option, without sending a turn.

## Candidate V2, registered after reading V1 and before new calls

V1 completed six groups but failed the useful-choice condition: independent calls
repeated the same question or protective promise. Reading also found that omitting
all current surroundings lost the shaking floor in the flat-scene case. V1 is not
accepted; outputs remain in private/results.json. The independent review is pending.

V2 returns to the original planned architecture: extract the EXACT Character
message builder, leave ordinary Character.act unchanged, and request all three
alternatives together so the model can coordinate distinct intentions. The helper
uses Character's schema for each item and its existing movement/repetition/secrecy
validation functions, with one correction and deterministic fallbacks. Use the
old helper's physical surroundings only in flat scenes; split-scene facts have no
witness metadata and remain excluded. No new schema field or session mutation.

Repeat the same six pairs against the same frozen snapshots (not new scene inputs).
Use the same decision rule. Thought presence is not a quality win by itself.
V1 transport initially lacked gzip decoding; no valid outputs from that failed
transport were counted. The corrected transport uses curl --compressed.

## Recorded Character call: input-order probe (user requested)

Before calls: replay the final recorded Character request from session 274679ed,
turn 1, character Asword. Keep every system rule, fact, event and final instruction
unchanged; permute whole user-context blocks only. Preserve chronology within
RECENT EVENTS. Test original order and three local RNG seeds (11, 22, 33), three
runs each, through curl on the currently configured DeepSeek model. The historical
request originally used llama_cpp; this is a controlled rerun of its messages on
the current provider, not a reproduction of its original sampling environment.

Decision rule: an unsupported asserted backstory/current fact in any raw output
is a witnessed Character generation failure on this payload; report the exact
example and per-order rate after reading against ALL supplied context. An order
is not better merely for different prose. A consistent difference of at least
2/3 bad outputs versus 0/3 motivates a follow-up, not shipping random ordering.
No code changes to the Character prompt or runtime order during this experiment.
This is input RNG, not LLM sampling seed. No seed parameter is passed to DeepSeek.
