# Fresh P3 prefix, current engine, 2026-09-14

Run one new session of `turma-dos-portais-pt-full` through the corrected
`repetition_battery.run_one`, base cell, P3, first three inputs only. These are
the speech `Eu vou na frente. Abram caminho.`, one skip and the action `atravessar o salão em direção à saída mais
próxima`. Preserve a fresh isolated data directory, canonical config path
without copying secrets, source hashes, resolved nonsecret settings, actual
debug log and persisted state. The existing base-cell controls apply: roteiro
on, drive and character alignment off, automatic compaction off, Portuguese,
burst limit six. Output/provider limits otherwise come from resolved config.

This is a real Runner/provider boundary check and a new fiction sample, not
an A/B or a completed P3 profile. It cannot estimate whether action-responsive
fiction improved. Do not run a recurrence score or substitute this short
session for the archived long ones.

The deterministic completion condition is that the third actual turn_input
contains the exact action with skip=false, and that the persisted state
contains that input as the controlled character's attempted action. Also verify
that the Director's actual provider request for that turn contains the action
and that an accepted response is recorded. Receipt without a provider response
is partial boundary coverage, not a completed provider check; a provider error
does not by itself implicate dispatch. A failure
before the third input is incomplete, not proof of an input-dispatch failure.
Preserve transport/model errors and do not replace the whole session with a
favorable rerun. Inspect any retry records to distinguish individual attempts;
do not assume their existence proves complete observability.

Read the complete visible fiction afterwards with a fresh isolated literary
critic, without the bug description, input-dispatch condition, metrics or
expected result. Save its observations and source-check any claimed physical
contradiction against the actual requests and accepted events before deciding
where investigation continues. No implementation of narrative mechanisms or
closure of task 69/77 follows from merely completing this boundary check.
