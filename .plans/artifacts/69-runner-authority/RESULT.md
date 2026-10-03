# Physical authority at actual Runner boundaries

Status: deterministic candidate boundary exercised; NOT runtime admission,
NOT evidence of LLM fidelity, NOT Task 69 closure. No real provider calls in this
stage. App construction still uses the ordinary Runner. Candidate sources and tests are
in `.plans/artifacts/69-runner-authority/`; run with `uv run python -m pytest -x
.plans/artifacts/69-runner-authority/test_candidate.py`.

1. OBSERVED in two synthetic baseline turns: free event text can register a
physical-looking anchor without changing durable aperture or actor position.
The ordinary Runner covered `azul aberto` and `Téo no túnel` from:
`O portal azul aberto deixa Téo no túnel, do outro lado. Iara ajusta a lanterna.`
Blue stayed closed and Téo stayed in the hall. The initial wording, `O portal
azul está aberto. Téo está no túnel. Iara ajusta a lanterna.`, covered neither
physical anchor. That failed the initial expected lexical precondition; it is
retained as a distinct negative control, not called a successful bypass draw.
This demonstrates a deterministic text-coverage boundary and wording dependence,
not a measured cause of any previously generated restaging cluster.

2. OBSERVED at both real coverage consumers: `_commit_beat` reads event content,
Character replies and descriptive keys; `measure_beat_progress`, called by
planning, additionally reads history text. Protecting only the commit collector
would still allow prose to prove a physical anchor on the next evaluation.
The candidate overrides coverage collection and requests explicitly authoritative
anchors during planning evaluation. Existing actor coverage and pacing remain.
The ordinary application still uses the previous default coverage semantics.

3. MEASURED by deterministic assertions: 21 candidate/control test cases passed,
including the two ordinary-Runner wording controls, false event/prose claims,
hidden claims in a cause, five contradictory parallel field cases, four invalid
typed transactions, one four-turn reload/undo chain, two semantic-refusal stages,
one restricted-audience case, one omitted declared attempt and three schema
failures that exhausted the existing three-attempt client policy. Model replies and reviewer decisions are test
doubles; Director requests use the production builder, schema and shared client.
The renderer is a deterministic projection double inside the real per-viewer
Runner orchestration, not production prose generation. A forced clean reviewer
could not make untyped claims mutate aperture/position or cover the two bound
goals. Contradictory parallel fields and refusals left the full persisted
GameState unchanged, including history, revision and goal coverage.
The omitted-attempt and schema controls were added after the first content
review; all four passed and left the complete saved state untouched. These
counts describe test cases, not independent model samples or a population
reliability estimate. Assertions establish only their particular inputs.

4. OBSERVED in one synthetic four-turn chain: persisted aperture states were
closed, closed, open, open and Téo's positions hall, hall, tunnel, tunnel.
Actual hard-cap planning ran before turn 3; a planner double returned another
beat with the same goals, resetting current-beat coverage. Each subsequent
Director request reflected reloaded physical state and accepted typed steps;
turn 3 also reflected that legitimate coverage reset. Turn 4 no longer listed
these beat elements as awaiting coverage. The lamp fact survived unrelated
updates. Two undo calls restored state, position, accepted-step history and
coverage to the end of turn 2. Added context contained no private entity IDs
or lexical operator ontology hits. This does not test automatic extraction of
physical goals, actual Character calls, dynamic registrations, other dimensions,
or scene relocation: goals, routes and attempts are explicit fixture metadata.

5. OBSERVED negative narrative control: with a reviewer forced to accept every
candidate, the false opening/crossing prose WAS persisted. The physical state
and bound goal coverage stayed unchanged; planner evaluation still reported the
physical goals missing. Therefore this candidate separates state authority from
language admission but does not guarantee narrative fidelity. A real reviewer
and actual per-viewer renderer still require complete-source checks and fresh
provider evaluation; field references or schema-validity cannot prove meaning.

6. Validation: 209 selected production regression tests passed; full suite
1234 passed, 2 deselected, one existing Starlette warning. Ruff lint passed;
mypy passed for 61 source files. Both the project-locked formatter and latest
formatter accept changed Python files. Repository-wide latest format check is
NOT green: 35 files would be reformatted. No unrelated formatting was applied.
The two Runner method extractions preserve default behaviour; the optional
`authoritative_anchors` argument is used only by this isolated candidate and its
unit tests. No persisted domain field or schema version changed.

Protocol reader `6380503877aa` found ambiguous abort/prune language and an
underspecified future provider stage. The protocol now states whole-turn abort
with no pruning and requires a separate preregistration of provider counts and
stop conditions. The initial setup also rejected the absent internal presence
sentinel, an obsolete fixture `narration` key and a non-schema `Narrator` queue;
fixes conform the synthetic replies to the real contract, not runtime fallbacks.
A normalized-null roster proposal initially raised TypeError; the candidate now
rejects it as a whole-turn failure. Initial and final isolated test data remain
under /tmp; no owner session was used or modified.

Next action: freeze and replay the actual Director and per-viewer renderer
requests with real high-reasoning responses and audits, starting with explicit
causal targets and including known contradictions in event/cause/final prose.
Require complete ancillary fiction in every accepted transaction. The implemented candidate already aborts detected structural mismatches and
explicit reviewer refusals as whole turns: new outputs and input remain
uncommitted, and the caller receives an exception. Undetected semantic
contradictions can still persist, as claim 5 demonstrates. The upcoming provider
evaluation must check whether actual reviews detect omissions and contradictions.
There is no semantic retry or partial-event salvage; only the existing client
JSON/schema retry policy applies. Failed admission must
not be described as successful preservation of the rejected fiction. A local pass would authorize further controlled fiction evaluation,
not close the remaining Task 69 and roadmap gates.

Content review `5bec34fcf02b` retained the six numbered claims with their bounded
statuses, questioned whole-turn abort versus preserving ancillary fiction, and
requested clearer failure handling. The final text now distinguishes complete
accepted transactions from wholly uncommitted rejected ones, with caller-visible
exceptions. Its objection that contradictory history will *reliably* cause later
hallucinations is an unmeasured causal theory, not adopted here: the negative
control demonstrates contradiction persistence, not its frequency or downstream
effect. The reviewer likewise does not authorize runtime admission.

Final content review `8bf891372043` also retained the six bounded claims, but
flagged wording that could imply every semantic contradiction aborts. The final
next-action text now explicitly limits existing aborts to detected structural
mismatches and reviewer refusals. Its asserted `.plans` path error is not
adopted: the owner requires `.plans/`, and the exact command above executed
successfully. No reviewer consensus is used as proof of implementation or model
behaviour.
