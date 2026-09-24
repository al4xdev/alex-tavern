# Blue-gate closing-action extraction: frozen rule before provider calls

The prior [blue-gate transition screen](BLUE-GATE-EXTRACTION-RESULT.md) failed to identify the repeated T38 closure consistently while asking the model to combine event reading with the current-state transition rule. This second local **smoke test** asks only whether the accepted proposal narrates a **new completed closing action**, leaving the comparison to durable state for deterministic code. Its four selected phrases may permit shallow lexical matching; even a pass cannot establish semantic understanding, extractor reliability or readiness for repair. A failure can reject this exact shape on the local source fixture.

## Four source labels, one session

Use the same successful first-attempt Director responses from `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl`: T36 line 334, T37 line 344, T38 line 350, T39 line 352. Project only `perception_events[].content` and `time_skip_summary`, ordered as the Runner supplies them to prose. No `scene_update`, `scene_blocking`, current aperture, candidate state, later narration, character IDs or witness IDs enters the model request. The public target label is `blue dungeon gate`. This removes the state dictionary shortcut; the later state comparison is outside the measured model task.

| Turn | Expected `closing_action` | Source-grounded reason |
| --- | --- | --- |
| T36 | `false` | Gate narrows to a still usable gap; warning says five seconds remain. No completed closure. |
| T37 | `true` | Accepted `time_skip_summary` says the blue team disappears into the blue tunnel and then `o portão se fecha com um baque surdo`; the referent is that blue gate. |
| T38 | `true` | Accepted `perception_events[].content` for a `physical_outcome` says `O portão azul se fecha com um baque surdo`. This is a proposed action even though prior state was already closed; the model is **not** asked to judge whether it is legal. |
| T39 | `false` | Gates are observed already sealed; no new closing action occurs. |

An isolated text-only reader of the complete T37/T38 packet established the duplicate closure, and the T36/T39 source events were checked directly. These labels describe what each proposal **asserts**, not a physically legal state change or a population truth rate.

## Frozen output and decision rule

Use DeepSeek V4 Flash through direct curl with the configured model/max-token settings, `json_object`, thinking disabled, and no temperature/top-p/seed override. The system message defines `closing_action: boolean` as true only when an event or time-skip summary says the target gate **finishes closing during this beat**; narrowing, warning that closure is imminent, and observing an already sealed gate are false. It instructs the model to judge the action independent of whether the gate could already be closed. Output exactly one JSON object with `closing_action` and a nonempty `evidence_quote` copied **verbatim from one supplied event or time-skip summary**. Local validation checks schema, boolean type and that quote's literal occurrence in the source event text. On false cases, the quote only anchors what the model looked at; a quotation cannot prove the absence of an event elsewhere in the proposal. The independent reader judges the verdict against the whole supplied event list, not the quote alone.

Freeze source/script/preregistration hashes and four exact requests in a manifest before provider calls; verify all hashes and reconstructed requests immediately before dispatch. Run four independent curl calls per turn, sixteen total, with no retry or replacement. Save requests, raw envelopes, provider response IDs, parsed outputs, schema and quote validation, HTTP and transport statuses. Keep configured secrets off CLI arguments and out of artifacts.

If fewer than sixteen calls return HTTP 200, schema-valid JSON and a literal event quote, mark the technical screen **incomplete**, without scoring semantic success. If all are valid, this local smoke test passes only if all four `closing_action` labels on each turn match the table and an independent text-only reader finds no verdict contradicted by the full supplied events. Any differing valid label or contradicted verdict stops this candidate. A pass would permit only a **new adversarial source contrast** with different wording and other physical objects before any proposal-repair experiment. It would not estimate reliability, prove semantic extraction, validate a model producer, authorize runtime integration or close Task 69.
