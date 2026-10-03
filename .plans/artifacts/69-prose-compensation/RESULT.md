# Actual prose: occasional preservation, no validated compensation

Status: FAILED local compensation gate. The previous Director source-preservation
gate stays failed; neither candidate is admitted to production or advanced to
full fiction acceptance. This downstream diagnostic uses retained Director
outputs rather than new Director draws, and cannot rescore the previous failure.

1. MEASURED execution: four fresh actual public-renderer logical calls for the
retained omission draw and four for the retained complete draw. Eight terminal
narrations, nine curl HTTP attempts; all nine HTTP200, finish_reason stop,
distinct response IDs and emitted reasoning. Omission input: 3/4 first-attempt
JSON/schema success, 4/4 terminal after one existing client retry. Complete
input: 4/4 first-attempt and terminal. No production echo-correction request ran;
all requests matched the frozen initial payload. Initial and static correction
variants were captured from the production renderer before calls. All hashes
and actual request bodies verified after execution.

The actual Runner reconciled each retained Director's typed canon on a draft,
confirmed one public cluster, and used its real render orchestration, builder,
client, guards and normalization. No Character or semantic-admission reviewer
call; no generated narration saved over the synthetic starting sessions. Real
locks/save/load verified stored starts unchanged. No owner-play session or real
.data mutation. This tests a public renderer boundary, not full-turn commit/undo
or private per-viewer confidentiality.

2. OBSERVED complete-source reading by isolated Gemini 98e8c411d267 and verified
by the primary agent, which knows the prior investigation and is not counted
as a second blind evaluator:

| Retained Director input | Explicit lamp outcome | Inferable | Absent | Fresh final texts |
| --- | ---: | ---: | ---: | ---: |
| Lamp event omitted, submission2-3 | 2 | 1 | 1 | 4 |
| Lamp event present, submission2-2 | 4 | 0 | 0 | 4 |

The unit is a fresh draw conditioned on one fixed retained input, not a session
population. Classifications use action meaning, not mentions of 'lanterna'.
Both actual inputs retain the current action in reader history. They differ in
multiple Director details; this is not a single-variable causal ablation.
Thus neither history recovery nor an effect of Director event presence is
established. The failed all-four gate blocks a claim of validated compensation
on the omission input; occasional preservation does not reverse that gate.

3. OBSERVED absent output: omission-input repeat3 (blinded label R7) narrates
Bento removing the bar/opening the passage and then Téo crossing. Iara's lamp
is held by the doorway column, lighting walls/shadows and finally the floor.
The declared input had brought it to the bar to inspect that mechanism. This
text supplies no recoverable illumination/examination consequence at the bar;
mentioning the lamp as scenery does not satisfy the predeclared criterion.
Both readers found this absence. Opening/crossing remained in order with no
reclosure: physical aperture correctness did not prove input preservation.

Inferable output omission-repeat1 (R3) places Iara beside the vacated bar area
and points her light at exposed hardware after removal. That can convey a
bar-side inspection consequence, but does not depict the approach directly;
it remains inferable, not promoted to explicit. The two explicit outputs
illuminate the bar/fittings before or during removal. All four complete-input
texts explicitly shine light on or visually examine the bar/locking assembly.

4. OBSERVED physical and literary limits: all eight terminal texts depict blue
opening before Téo crosses, without re-closing blue or repeating wind closure,
and without authored dialogue or objective private thought. Bento's reported
caution is structurally withheld from prose and was not a missing-content gate.
This bounded read concerns the tracked aperture/crossing sequence, not every
possible physical dimension. Source2-repeat2 calls green 'selado' where source
only says closed; source1-repeat2 adds blue luminosity/pulsing/hum. The reader
permitted these as sensory expansion. Main retains them as descriptions whose
security/genre implications are not established by this aperture-only probe;
they are not proofs of general physical fidelity or newly invented gate failures.
Other phrasing oddities, such as 'o batente gira', remain observations rather
than new admission metrics.

The reader's phrase that event omission 'causes' the action dropout is not
adopted. This experiment observes a dropout under that input, and occasional
preservation under the same input. No causal mechanism or universal recovery
claim follows. There was no unresolved material classification dispute, so
no additional tie-breaking reader or resampling was used.

5. OBSERVED tooling/text defects kept separately: omission-repeat4 first response
was complete, stopped normally and included narration plus unexpected root
`type: object`. Production JSON/schema validation rejected it and the existing
client retry returned a valid single-field object; no semantic repair or
hand-edited salvage. Full initial narration/reasoning remain in the raw envelope.
Omission-repeat1 terminal text contains literal backslash-n paragraph markers
rather than actual paragraph breaks. They are present in both accepted narration
and the evaluated Runner history record; schema-valid text is not necessarily
well-formatted prose. No unescape parser or production change was added.

6. Configuration and validation: V4 Flash high, output cap16384, word floor150,
timeout180; renderer prompt sizes3,374 /3,537 characters and reported904 /951
prompt tokens. Terminal whitespace-split counts, reported only for size, were
231/253/174/222 for the omission input and187/247/205/211 for complete input.
No claim about reasoning improving counts, latency or quality follows. Scripts
passed Ruff lint/format before final freeze; production sources did not change,
so the prior 1234-test validation was not needlessly rerun. Commands:

```fish
set -lx ROLEPLAY_DATA_DIR /tmp/alex-tavern-prose-compensation
set -lx PYTHONPATH .
uv run python .plans/artifacts/69-prose-compensation/screen.py prepare
uv run python .plans/artifacts/69-prose-compensation/screen.py run
```

Executed manifests/runs refuse overwriting. Preserve the actual starts, frozen
initial/correction requests, all attempts/errors/reasoning, final narrations,
drafts, reader packet/key and classifications in ignored artifacts and isolated
storage. Credentials only curl stdin, absent from source/requests/CLI arguments.

Protocol critic c513aa3d01c9 raised useful gate/identity/causal ambiguities:
control also requires4/4; only Gemini is blind; primary has prior context;
compensation is descriptive final preservation, not established canon recovery.
Its claim that echo requests require previous generated text was checked against
the production builder and disproved: a fixed correction is appended, so both
variants can be frozen. No majority vote, causal-history experiment or metric
threshold was added merely to satisfy the critic.

Next: preregister complete-source admission tests using actual omitted/complete
Director candidates and actual absent/complete prose, plus the known injected
unsupported opening/crossing. A reviewer must detect the specified failures
and permit complete controls before it can enter the real Runner candidate.
Neither field references nor a clean schema establish meaning. All other Task69
families, dynamic subject/goal binding, full per-viewer fiction, live restaging
and remaining roadmap requirements stay open.
