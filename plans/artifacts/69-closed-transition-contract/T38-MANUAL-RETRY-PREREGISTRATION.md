# T38 whole-draft retry with a manually grounded contradiction

The archived T38 Director draft closes the already closed blue gate and moves
characters through a gap after T37 placed them in the tunnel. Its own spatial
draft says the destination is unreachable. A content read found that removing
one sentence leaves the rest of the crossing incoherent. This isolated replay
tests whether a **complete replacement draft** can recover when the
contradiction is supplied manually. It does not test automatic detection or
authorize runtime retries.

Use archived `7fd84e9a` T38 Director request and response at debug line 350.
Both arms contain the exact original system/user messages, followed by the
same assistant message containing that rejected JSON draft and a final user
message asking for a full replacement from the committed T37 state. The two
final messages share the same wrapper and differ only in the text under
`CONSISTENCY REPORT`:

- **A, generic:** `The previous draft conflicts with committed scene continuity. Review the committed state and the final attempted action, then regenerate every field as a new draft.`
- **B, grounded:** `At T37 the blue gate completed closure; gate_blue is fechado. Mirella, Nix, Doran, Liora and Bruna are already in the blue tunnel; Téo is in the hall. Téo's final advance through the fresta is an attempt, not a completed crossing. The rejected draft says destination_reachable_this_beat=false but moves Téo and the already placed team through that fresta and closes the blue gate again. Reconcile those statements against the committed state and regenerate every field. A new causal reopening is possible if you actually establish it; do not assume this attempt succeeded.`

The generic and grounded text are different treatment content, not a
one-variable test of one word. The rejected draft and its position are
identical; the screen isolates whether **specific grounded feedback** helps
relative to a generic retry request. The original contradictory
`dungeon_gates` fact remains in both arms. No rejected-draft events or state
effects are committed in this offline test.

Freeze the script, source, preregistration, exact request bodies and current
Narrator schema before calls. Direct DeepSeek V4 Flash curl, `json_object`,
thinking disabled, no sampling override, four fresh calls per arm (**eight
total**), no retry or replacement. Secret via curl-config stdin. Save every
request, raw envelope, provider ID, HTTP/transport status and validation.

Technical prerequisite: all eight HTTP 200, distinct IDs, JSON objects valid
against the current Narrator JSON schema built for the 21 present character
IDs. A schema pass is necessary, not evidence of coherent IDs or narrative.
If any call fails, mark the screen incomplete without an aggregate semantic
pass. A blind content reader receives shuffled complete response drafts with
no arm label, plus the common committed T37 ending and Téo's final attempt.
For each response, judge: repeated blue-gate closure; repeated crossing of
already placed team; whether Téo's attempted crossing receives a coherent
consequence without unexplained teleport; and whether blocking, events,
zones and scene update agree. Quote the exact failing or resolving passages.

**Registered local rule:** B must produce 4/4 whole-draft coherent responses
with no repeated closure or re-crossing, Téo's attempt resolved or carried as
unresolved without teleport, and no draft-internal physical contradiction.
If B misses any, this exact retry contract fails. If B meets it while A does
so in at most 1/4, there is a local comparative signal for grounded feedback;
otherwise the comparison is inconclusive. Even a local pass does not validate
automatic conflict detection, other physical entities, legitimate reopening,
legal crossing or durable-state integration; those require independent
controls before code changes.
