# Identity and aspect screen: frozen before provider calls

The preceding two-stage screen was technically valid but admitted generic T37
closure prose for a named blue gate. This screen tests an **offline, manually
bound reader**, not a producer or runtime change. It separates two distinct
questions about offered passages: did a closure finish, and does the closing
gate identify the named subject? The model sees no prior state, complete source,
later narration or expected label.

The response has `completed_closure: boolean`, `identity: named|resolved|
ambiguous|other|absent`, and literal `action_quote`/`identity_quote` strings.
`named` means the closing clause explicitly names the target; `resolved` means
the clause uses an unnamed gate whose target is unambiguous in the offered
discourse; `ambiguous` means the closing action's referent is not uniquely
identified; `other` means it identifies a different gate; `absent` means no
closing action is mentioned. These are separate fields with a logical
constraint: `absent` requires `completed_closure=false`. A future warning may
identify the blue gate while still having `completed_closure=false`.
Present-tense narrative `se fecha com um baque` counts as completion; a clause
that explicitly stops before closure does not. `action_quote` is a literal
excerpt of the closing-action phrase, including a future or interrupted
action, or `""` if no closing action is mentioned. `identity_quote` is a
literal excerpt naming the target or a different gate, or identifying the
unique antecedent when `resolved`; for `ambiguous` and `absent`, it is `""`.
The quotes may come from separate passages. Literal quotation validates
provenance, not semantic correctness.

Nine fixed packets, four fresh calls each:

| Packet | Offered evidence | Frozen expected `(completed, identity)` |
| --- | --- | --- |
| `t38_explicit` | archived blue closing clause | `(true, named)` |
| `t37_bare` | archived bare `o portão se fecha` quote | `(true, ambiguous)` |
| `t37_context` | archived blue-gate fresta mention plus full time-skip summary | `(true, ambiguous)` |
| `t36_future` | archived warning that blue gate closes in five seconds | `(false, named)` |
| `t38_static_green` | archived already-sealed green-gate observation | `(false, absent)` |
| `wrong_target` | archived blue closing clause, subject green | `(true, other)` |
| `synthetic_resolved` | "O salão tem um único portão, pintado de azul. O grupo atravessa sua abertura. Atrás deles, o portão se fecha com um baque." | `(true, resolved)` |
| `synthetic_competitors` | blue and green gates move, then `o portão` closes | `(true, ambiguous)` |
| `synthetic_aborted` | named blue gate begins closing but stops short of fully closing | `(false, named)` |

Independent pre-call content reading judged the archived T37 summary ambiguous
because it says the closing seals all groups and then mentions plural gates.
The synthetic resolved case states a unique gate as a scene fact, not as a
checker instruction. The synthetic competitor and interrupted-action cases
test whether lexical mention alone triggers target identity or completion.
These frozen labels are admission decisions for these passages, not a population
truth set. A later blind content read examines disputed outputs against exact
input without moving labels or replacing calls.

Freeze source/script/preregistration hashes, schema, prompt and nine request
bodies before execution. Use configured DeepSeek V4 Flash through direct curl,
`json_object`, thinking disabled, no sampling override. Four calls per body,
**36 total**, no retry or replacement. Save request, raw envelope, provider ID,
HTTP/transport status, parsed response and grade; secret passes via curl-config
stdin, never a command argument or artifact. No internal character ID enters a
prompt.

Technical prerequisite: 36 HTTP-200 calls with distinct response IDs,
schema-valid JSON and quotes with these exact rules: a mentioned closing action
requires nonempty literal `action_quote`; otherwise it requires `""`; named,
resolved or other identity requires nonempty literal `identity_quote`;
ambiguous or absent requires `""`. If any call fails, mark the screen incomplete and do not score an
aggregate semantic pass. If technically valid, every packet must match both
frozen fields 4/4. Any mismatch stops this exact reader contract. A local pass
still validates only offered-evidence reading on selected passages; it does
not authorize automatic target binding, durable state writes or renderer repair.
