# Exact-request replication, before calls

The events-last A/B produced correct explicit act_completed values in its
11 valid candidate outputs (4 attempt, 4 closure, 3 departure). One departure
call timed out at 60 seconds, so its all-four-valid gate did not pass. The
failed call remains failed and is not replaced. No production patch follows.

Run a separate replication with the exact frozen events_last request for all
three cases, four calls each, 12 total. No prompt, model, sampling or timeout
change. Preserve the previous run and all replication outcomes. This is not
a continuation that fills its missing slot.

Technical rule fixed now: at least three HTTP-200 schema-valid responses with
distinct nonempty provider IDs in each case. Any fewer makes this replication
incomplete. Content rule: every valid response must match the exact known
act_completed value (attempt false, closure true, departure true). No aggregate
or population reliability claim. Neither a previous valid reply nor a later
retry counts toward this run. No retries. A pass permits independent content
criticism of every valid candidate from both runs and adversarial test design.
Plan semantics, production parity and multi-turn execution remain unproven.
