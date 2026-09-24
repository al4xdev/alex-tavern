# P3 actions were dispatched as skips

2026-09-14. **OBSERVED deterministic defect:** `run_one` in
`tools/acceptance/repetition_battery.py` previously dispatched speech with
`player_turn(sid, speech=text)` and every other kind with
`player_turn(sid, skip=True)`. P3 declares actions at input positions 3 and 9:
`atravessar o salão em direção à saída mais próxima` and
`seguir em frente sozinho se ninguém acompanhar`. Neither action could reach
the Runner through that dispatch. A regression test using the actual P3
profile and an observed Runner call list failed before the fix at input 3:
it received `skip=True` instead of the declared `action`. The test is
`tests/test_repetition_battery_inputs.py::test_p3_sends_actions_to_runner_instead_of_skipping`;
the failing assertion showed `At index 2 diff: call('test-session', skip=True)`
against the expected action call.

**OBSERVED archive check, two sessions:** all recorded `turn_input.input.action`
values are empty. The third recorded input is a skip in both sessions; the
ninth is present and a skip in the second session only. These are observations
of the logs, not an inference from the current code alone:

| session / log | recorded inputs | third input | ninth input |
|---|---|---|---|
| `base-P3-r1/sessions/5d60575d/debug.jsonl` | 7 | line 83, T8, `action: ""`, `skip: true` | not recorded |
| `base-P3-r2/sessions/d5a2ccf0/debug.jsonl` | 9 | line 88, T8, `action: ""`, `skip: true` | line 394, T32, `action: ""`, `skip: true` |

Paths are below `plans/artifacts/repetition-battery/`. Both logs contain the
spoken steering lines `Eu vou na frente. Abram caminho.` and
`Nao vou esperar mais. Estou entrando.` at input positions 1 and 6; their effect remains an
empirical question. The defect does **not** establish that P3 had no steering
at all. It invalidates describing these runs as the intended four content
inputs and six skips, or as a test that the engine ignored the two physical
action inputs. Neither seven nor nine recorded inputs establish completion of
the ten-input profile; this audit does not determine why the logs end there.

**Decision:** task 77's P3 section describes the profile as “four content
inputs and six skips” and calls the result for `5d60575d` evidence that “the
engine stalls regardless of who pushes.” Withdraw the four-content description
for these two archived executions and the interpretation that their physical
actions tested engine responsiveness. The broader claim cannot use the missing
actions as support; responsiveness to the actual steering speeches remains
unevaluated here. Reading the archived fiction remains legitimate when its
actual inputs are acknowledged. No new responsiveness or stall-rate estimate
is claimed here.

**Fix, deterministic validation complete:** the dispatcher now forwards `action` explicitly,
dispatches `skip` explicitly and rejects unknown kinds with `ValueError`.
Two tests exercise the complete P3 input order at the Runner boundary and
reject a misspelled kind without issuing a turn. Both pass after the fix.
The code correction is the explicit action/skip dispatch in the acceptance
tool. A fresh conclusion about response to P3's physical actions requires
verifying that those actions were actually sent.

Validation: `uv run pytest -x -q` passed 1,133 tests, with two deselected and
the existing Starlette/httpx deprecation warning. `uvx ruff check .` passed.
The changed dispatcher and new test pass formatting checks. Repository-wide
format checking still reports 44 files; the standard mypy command reports
the same three previously observed errors in `src/runner.py` at lines 873,
1291 and 1964. Neither check is reported as passing.

Two isolated report critics warned against erasing the steering speeches or
requiring a fresh run before any narrative judgment. The disposition above
is restricted to responsiveness to the missing physical actions; the literal
speeches and both incomplete recorded input counts are retained. The
unsupported claim of general exact replay readiness was removed.
