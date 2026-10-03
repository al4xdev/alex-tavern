# Roteiro actor references, 2026-10-03

The saved portal_attempt-coverage-3 response emits expected_actors ['Iara','Bento'].
Its source roster gives IDs C1/C2. The old string-array output schema accepts
those names; the actual normalizer returns [] and loses the intended Bento hint.
A previous compiler screen exposed the same reference problem. Downstream story
effects were not measured.

Delivered correction: build_roteiro_schema and build_next_beat_schema now receive
the roster IDs explicitly, and constrain expected_actors.items by enum in both
first_beat and next beat. All live source callers and the direct schema test were
updated. Rewritten future acts use the same roster parameter. The full roster,
including the controlled character, is represented equally; there is no human
marker. Standard shared-client schema validation rejects names/unknown IDs
before normalization and uses its existing retry. This resends the same request;
it does not inject error feedback or guarantee a live provider will recover. Valid IDs still pass through
the Runner's controlled-character exclusion. No name-to-ID fallback, persisted
field or session-schema bump was introduced.

Two real shared-client mocked HTTP tests cover compiler and replanner. Each feeds
a name reply, then valid C1/C2. Both make exactly two requests and retain C2 after
normalization, whereas the invalid first reply cannot be silently accepted.
The embedded DeepSeek schema contains all C1/C2/C3 equally. These tests verify
the standard call path, not wrappers that bypass shared-client validation.

Eight fresh direct curls use frozen delivered builder/schema/client/adapter
requests, high thinking and effective max_tokens8192: four compiler, four
next-beat. No retries or replacement in the screen. All eight HTTP200 replies
pass the enum schema, have distinct IDs per cell, finish_reason stop and
nonempty returned reasoning. Every actor array is ['C1','C2']; next-beat flags
are all false for the confirmed failed portal attempt. This is local boundary
evidence, not proof that enum makes provider output universally valid.

Narrative issues remain: compile-2 assigns 'Iara compara ... enquanto Bento sonda'
and compile-4 similarly scripts comparing/testing. Replan-3 presupposes a
lantern belonging to Bento although no lantern was confirmed. These are
observed planning premises, not measured downstream actions. References being
valid does not establish source/agency compliance or close Task69.

Validation: 122 focused tests passed, including operator-ontology and prompt-ID
checks. Full suite 1229 passed, two deselected, one Starlette deprecation warning.
Ruff lint passes, five changed/new Python files pass format checks, mypy passes
61 source files, and git diff whitespace check passes. README records the
reference contract. The rejected coverage-label wording remains unchanged in
production. No remote operation or new commit was performed in this work block.

Frozen historical experiment scripts target their capture-time API and requests.
They are not mutated to erase original schema behavior; newly executed screen.py
in this directory uses the new explicit roster signatures. Source producers/
consumers were checked by repository search separately from those historical
artifacts.

The previously saved real name response was also fed to the delivered enum
schema directly: validation rejects $.beat.expected_actors[0] as outside C1/C2.
Fiction reader c191885e37c8 independently identified voluntary action scripting
in compile-2, compile-3 and compile-4, and the lantern premise in replan-3.
Compile-4 also assumes ropes, a lamp and powder in hand. Those defects remain
open; no fiction-admission claim accompanies the reference fix. Its replan-4
exit-target objection remains a boundary interpretation rather than a proven
choice violation, because prospective exit targets were explicitly allowed.

Report critic eb9bbe43ec1d supports the structural boundary and local eight-call
observation. Its 'live retry reliably recovers' claim is not in this report and
is not adopted: recovery was demonstrated only with controlled mock responses.
If a live model repeats invalid references, the existing bounded retry can
exhaust and raise its validation failure. That is explicit rejection, not silent
acceptance with lost actor hints. No quality gain or universal first-pass success
is inferred from the eight calls.
