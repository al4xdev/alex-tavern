# Task 69: scoped historical cohort comparison

1. This is a descriptive follow-up to the proposed comparison of 18 sessions
that never reach 40 physical-fact keys with 15 that do. It does not estimate the
causal effect of eviction. Input inspection found two of the latter exceed 40
(oldcode sessions 45dac069 and 976e9d42 peak at 58 and 70); reaching a threshold is not proof a cap
operated. Narrative density, session length, engine revision and accumulated
context may differ between groups.

2. Pin the original 33 distinct session IDs: sorted state-path deduplication
under plans/artifacts, excluding the two known post-79 additions ea6620fb and
bb72dc94. Record chosen debug paths and hashes. Read Physical facts as JSON from
each recorded Director request. Define each session's cohort by whether any
recorded request has at least 40 keys. Report missing/invalid requests, and
do not silently replace them with state snapshots. Include every session in the
inventory, including short sessions without measurable recurrence opportunity.

Abort the comparison on a missing/unparseable Physical facts block rather than
classifying incomplete request coverage as below threshold. For recurrence use
the last parseable Director response per turn in file order, report earlier
duplicate responses discarded, and report failed response parses separately.
Parseability does not certify runtime schema acceptance or persistence.

3. Before scanning, fix the comparison: reuse the archived task-69 detector
(Unicode normalization, SequenceMatcher threshold 0.6, prior three turns) only
as a report instrument. For each physical_outcome or observation event, search
prior events of those same two kinds. Exclude audible_speech and other kinds
from both numerator and denominator. An observation label can still describe
speech or an order, so this is an event-kind filter, not a semantic guarantee.
Count one flag at most per event. Drop turns 1-3 from the denominator as a fixed
turn-index convention, not proof that every retained turn has three complete
predecessors or equal event opportunities. Report failed response parses.

4. Report flags/events and per-session rate for all measurable sessions, then
each cohort's pooled count plus unweighted session median, population sd and
range. For a position-restricted descriptive contrast also report rates using
only turn indices represented by both cohorts; list that intersection. No
pooled p-values, no causal or equivalence claim. A similar or smaller frequency
in the threshold cohort does not establish that capacity is irrelevant.

5. Read the earliest flagged physical-kind pair in each below-threshold session
(tie-break by repeated turn, source turn, event text), alongside both event
texts, their source subject IDs, and the repeating prompt's full facts bag and
relevant transcript. Preserve records for adjudication. Determine whether it
is the same completed event re-staged, a progression/continuation, a different
entity, speech/order, or indeterminate. Report one reading per session, with
its ambiguity; no automatic flag becomes a genuine-repeat count without this
read. This positive-only read cannot estimate detector precision/recall for the
full corpus; automatic frequencies remain diagnostic regardless.

6. Decision before scanning: one clear physical repeat in a session whose
recorded prompts never reach 40 shows that reaching this input threshold is
not necessary for that example. It does not establish that eviction never
happened in unrecorded processing or that storage/salience interventions cannot
help. Zero confirmed cases leaves this question unresolved, not falsified.
Neither result authorizes production changes or resolves task 69's storage
design. Report the group comparison and counterexamples without rewriting the
historical 703/5064 figure: the denominator and event-kind scope differ.
