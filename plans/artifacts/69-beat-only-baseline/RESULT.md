# Controlled beat baseline and bounded portal trace, 2026-10-02

Status: diagnostic evidence; experimental prompt remains outside production.
Task 69 is open. No personal owner-play session was used.

The frozen baseline used nine synthetic cases, four direct curl calls per case,
using exact production planning wire payloads. Candidate screens later transformed
those captured payloads outside production. All 36 baseline responses were
HTTP-200 and locally schema valid. In portal_attempt, all four marked the old
act complete although the confirmed attempt had failed and the portal remained
open. In portal_left, one marked it incomplete despite confirmed closure.
Applying these saved real responses through production replan_roteiro reproduced
the four premature advances and one missed advance. This is a selected controlled
observation, not a rate over roleplay sessions.

The first combined prompt variant neutralized coverage's COMPLETED wording and
added a temporal boundary. Its four attempt flags were correct, but three closure
flags and all four departure flags were wrong. Rejected. A second screen moved
only the existing confirmed-events block to the end of that variant's user
message. Its eleven valid candidate replies matched the explicit flags, but one
departure call timed out at 60 seconds. Its all-four-valid admission gate did
not pass; the timeout was preserved.

A separately preregistered replication used the exact events-last requests,
four calls per case, with at least three valid distinct provider IDs per case
required. All twelve were valid and matched the explicit act flags. No failed
slot in the earlier run was replaced.

Two isolated content readers then challenged 23 valid candidate plans from
both events-last runs. Both identified portal_closed-G, mapped to
portal-events-last-ab/portal_closed-events_last-2.result.json, whose plan says
“apagando as últimas runas” although confirmed events say the runes had already
extinguished. This is a source-supported repeated transition missed by the
boolean test. The readers disputed some other continuity and agency findings.
The automated instrument observes the applied act_index, not a beat_id prefix.
Exit conditions are read as targets, not as events already executed. Critic
claims based only on an ID prefix or the existence of a target condition are
retained as disputed, not established failures.

The bounded experiment repeated one scripted timeline four times, with different
real planner samples, and kept one roteiro per run, applied real planner replies
through production replan_roteiro, then added scripted canonical closure at T3
and short character interventions at T4/T5. All four traces retained act_index=0
after the failed attempt. They remained in_progress after T3 and T4, and at
the scheduling boundary before T6, after three committed observations including
closure, replanned with act_index=1. Each trace used two real calls. All eight
responses were schema valid. No same-turn completion was required.
World confirmations were scripted; this did not execute full Director/Character
turns, prose, persistence or full physical transitions.

The frozen bounded script is bounded_portal_run1.py, byte-identical to the
script hash in bounded-portal/manifest.json. After the run, bounded_portal.py
received import ordering and a non-None assertion for type checking only; the
run was not silently relabeled as using that later source.

Validation: the baseline harness and the maintained bounded harness pass their
explicit Ruff/type checks; repository Ruff passes, mypy checks 61 source files,
and pytest reports 1197 passed / 2 deselected. Repository format check still
fails on 44 existing files; no bulk formatting was applied.

Decision: the explicit act flags and this single bounded timeline passed in
the recorded samples. This is not evidence of delay robustness across stories.
The repeated rune transition is sufficient to reject admission; production
builder parity and broader controlled counterexamples remain unexercised.
No production prompt patch, schema change, task closure or reliability claim
follows from these experiments.
The next admission needs a strengthened content boundary, actual production
builder parity, and independent controlled counterexamples.

One later isolated reader found no portal/rune-state violation in the four
bounded traces. It distinguished newly introduced underground runes from the
extinguished portal runes. This does not erase the earlier repeated transition.
Its suggestion to require instant act advancement is not adopted: the owner
explicitly allows a plausible delay of two or three turns.

Next controlled probes: waiting after a failed attempt without declaring
success; inspecting the dark arch while refusing an offered route; and a
separately caused new portal/rune activation that must not be mistaken for
restaging the old event. These extend the test, not the production architecture.

Review operational note: report-review scout 9ccbf1f54c1c unexpectedly delegated
and invoked wl-copy against wayland-1. The local event log confirms the action;
the prior clipboard was unavailable for restoration. This action was outside
the requested text-only review and is not part of the test procedure.

Report review: the fresh text-only critic supported the recorded flag mismatch
and rune finding, and challenged generalization from four repeats of one timeline.
That limitation is explicit above. Its paraphrases 'reliably' and 'solely' were
not claims in the draft; the decision is worded to avoid either inference.

