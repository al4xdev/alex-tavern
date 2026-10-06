# Local textual-description variant, frozen before provider calls

Control: 69-local-chain, three chains stopped on their first submission. Each
Director produced syntactically valid JSON with a failed crossing, but invalid
physical_steps fields; all three persisted states remained unchanged. Two used
aperture_change with closed to closed and actor/result, one used attempt_result
with nonempty from_state/to_state/cause. No narrative was generated in that control.

Hypothesis, not established cause: native schema grammar constrains individual
values without exposing description semantics to the model's text input. The
requests contain field descriptions only in response_format, not in messages.

Single variant: also put the exact existing physical_steps schema and descriptions
in Director extra_context, keeping native grammar and all validation unchanged.
No changed schemas, manual response repair, expected-state insertion, model/server
changes, reasoning changes, or semantic retries. Inherit the control's config,
inputs, saved/reloaded sequential-turn method, explicit review test mock, and
text-reader rubric. Three new separately persisted chains, four submissions each,
halt each chain at its first error; retain every failed draw. Do not rescore control.

Gate: all three first submissions produce legal blocked attempts, and all three
chains commit all four submissions with the predefined state and reload checks.
If first-turn contract violations persist, this variant does not resolve them.
If later failures appear, isolate the first faulty call before further tests.
Passing is bounded to these fixtures, with 600-word prose floor, this local model,
server reasoning off, and mock semantic admission. No production activation or
Task69 closure. Text judgments remain separate from mechanical gate.

Frozen text review: cite new unsupported reopening/crossing/closure, contradicting
final aperture/position, missing currently resolved cause from entitled prose,
or technical state/beat/tooling language in the story. Distinguish recollection
from a new event, and style oddity from contradiction. No universal quality claim.

Inherited precritic bd6090111e26 considered before control freeze: clarified Iara
input versus world cause injection, actual forced Bento speech, mock semantics,
sampling and text rubric. This variant tests only description visibility; no
claim it separates every possible cause of failure or shows reasoning effects.
