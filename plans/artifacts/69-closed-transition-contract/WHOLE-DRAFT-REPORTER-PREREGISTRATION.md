# Whole-draft contradiction reporter: frozen source/control screen

The [manual T38 retry](T38-MANUAL-RETRY-RESULT.md) generated coherent
replacement drafts only when a human supplied the contradiction report. This
screen tests the preceding **reporter** boundary, offline. The reporter sees a
public-name physical projection of committed evidence, the pending attempt
(when present), and the candidate Director draft's blocking, events, moves
and update. It does not see the source case's frozen label, an accepted
replacement, the previous reporter experiments, or internal character IDs.
The two archived positive cases are selected excerpts, not byte-complete raw
Director payloads; this screen cannot validate full-prompt or runtime behavior.

Freeze the seven exact packets in
[the case file](WHOLE-DRAFT-REPORTER-CASES.json) and their labels before calls:

| Case | Expected status | Required reading |
| --- | --- | --- |
| archived T38 blue gate | `contradiction` | Gate closure and already completed group crossing recur; Téo's attempt is not success, and the draft's own reachability conflicts with its move. |
| archived kennel T34 | `contradiction` | T33 persisted prose already closes the kennel gate; no confirmed reopening precedes T34's repeated closure. `trancado` alone is not aperture evidence. |
| synthetic ajar closure | `consistent` | Passable gap, crossing, then closure is legal. |
| synthetic reopening | `consistent` | A closed gate can reopen through a narrated cause and admit Téo. |
| synthetic open crossing | `consistent` | Crossing an open gate is legal. |
| synthetic ambiguous gate | `uncertain` | Generic `o portão` with blue closed and green open cannot be bound to blue for rejection. |
| synthetic static aftermath | `consistent` | `permanece fechado` and old impact echo do not assert a new closure. |

The content-only pre-call reader agreed with these seven classifications on
the original packet. It flagged two construction weaknesses: an invented
pending attempt in the kennel packet and a blue-gate update that seemed to
resolve the ambiguous control. Before freezing, the kennel pending attempt
was set to `null` and the ambiguous control's update was set to empty. The
positive kennel evidence remains T33 **persisted prose**, not a claim that
`trancado` means closed.

Output JSON: `status: contradiction|consistent|uncertain`, `conflicts: []`
of objects with `committed_quote`, `draft_quote`, `reason`, and
`uncertainty_quote`. For `contradiction`, at least one conflict, each quote
literal within the corresponding input side, and empty `uncertainty_quote`.
For `consistent`, no conflicts and empty uncertainty quote. For `uncertain`,
no conflicts and a nonempty literal quote of the ambiguous draft phrase.
The technical quote check verifies provenance only; a content reader judges
whether the quotes actually support the reasoning. The reporter must not
turn a future attempt, legal reopening or unspecified `o portão` into a
completed named transition by inference.

Use configured DeepSeek V4 Flash with direct curl, `json_object`, thinking
disabled, no sampling override. Freeze script, case file, preregistration,
schema and exact seven request bodies before calling. Four fresh calls per
body (**28 total**), no retry/replacement. Save request, raw envelope, provider
ID, HTTP/transport status, parsed output and grade. Secret passes through
curl-config stdin. No internal ID enters a reporter prompt.

Technical prerequisite: all 28 calls HTTP 200, distinct IDs, locally
schema-valid JSON and literal quote conditions. If any fails, mark the screen
incomplete and do not score an aggregate semantic pass. If technically valid,
all seven bundles must match their frozen status 4/4. An independent content
reader, blind to labels and source provenance, then judges each report: T38
must identify both repeated closure and already completed crossing/failed
reachability, kennel must cite persisted T33 closure versus T34 new closure,
legal controls must remain unflagged, and ambiguous identity must remain
unbound. Any content miss stops this exact reporter. A pass would validate
only these projections; it would not validate automatic runtime detection,
full prompts, recovery success when fed to the Director, or the transactional
retry boundary.
