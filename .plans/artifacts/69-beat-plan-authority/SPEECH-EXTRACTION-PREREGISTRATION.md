# Separate speech extraction and authorization, before calls

Previous goal turn made progress: both final-audit prompts failed their frozen
falsification sets; whole Runner silent replay preserved an unrealized verbal
report. Whole-beat gate remains unvalidated. Astra recommends locating whether
claim coverage or authorization is failing, rather than changing one binary
verdict prompt again.

Use the six frozen V2 fixture contents unchanged, plus an exact contrast around
the original real clause: Bento only points at marks (no speech act) vs explicitly
describes them verbally (completed speech claim, no actual words). Preserve the
ambiguous original real wording as its own case. Current stronger experimental
contract requires reported completed verbal acts to have actually authored words
or the explicit canonical-source reading exception. This is not a claim that
current task-65 policy already implements that contract.

Eight cases, four repeats. Existing V2 whole-draft outputs remain a historical
baseline on the six original cases. Two independent stages: (1) extraction sees
ONLY full candidate, no authorization evidence or expected labels, emits exact
spans/field paths/actor/act/status/content, splitting read + extra question and
implied question + answer; (2) authorization sees each extracted act and uniform
actual speech/action/source evidence, classifies support and cites exact fields.
Compare automatic extraction with manually COMPLETE extraction receiving the
same independent judgment. Manual arm diagnoses the bottleneck and is never a
production producer. Manual spans are whole source clauses with context retained.
All actors have identical fields and canonical names, no human/AI or control
markers, internal actor IDs, named exclusions or test labels in model prompts.

Freeze all initial actual-wire requests, schemas, sources, manual acts, labels,
provider identity and script/protocol hashes before calls. 64 initial calls plus
32 dependent automatic-judgment calls, randomized bounded concurrent scheduling.
No retries/replacement; invalid extraction halts only that chain and is preserved.
Dependent requests are built using the preregistered builder and exact saved
extraction; save each payload before calling. Log agent/session_id/turn_number as
artifact metadata without adding them to prompts. Config read-only, curl key via
stdin, no personal play session, no runtime mutation. Original results never rerun.

Mechanical checks precede any aggregate disposition: all calls parse/validate;
extracted nonempty spans reference actual candidate fields; judgment indices are
complete/unique and citations exist in evidence (not the candidate's own claims).
These verify syntax/provenance presence only, NOT coverage or semantic support.
Empty extraction is not proof that speech is absent. Citation presence is not
proof that a claim is authorized. Code derives revision from unsupported completed
acts; a mislabeled completed act as prospective can still evade it and must be
checked against the manual arm and source.

Expected revision labels on original six remain T,T,F,F,T,F; pointing F, explicit
verbal description T. All known violating cases must reject and positives remain
for admission; label agreement alone is not semantic proof. Diagnostic decisions:
- Automatic misses observation/question while complete manual extraction judges
  correctly: coverage remains unresolved, no adoption.
- Manual complete extraction still accepts unsupported acts or rejects actual NPC
  words/source reading: authorization judgment remains unvalidated, no adoption.
- Both stages survive all fixtures: only then isolated text critic challenges
  content/reasons and proposes fresh harder cases, followed by fresh production
  drafts and real whole-Runner rejection/save/load/next-turn checks.

Incomplete mechanical gates prohibit aggregate admission, but individual retained
responses can still locate a specific failure. No effect/reliability percentage,
production safeguard, session field, source UI/repository or Task69 closure follows.
