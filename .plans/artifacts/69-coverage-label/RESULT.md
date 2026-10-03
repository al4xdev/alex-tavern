# Coverage wording diagnostic, 2026-10-03

32 fresh curls, four repetitions per fixture per arm. Both arms used actual
production thinking enabled/high and effective max_tokens8192. Candidate changed
only the coverage_complete STATUS sentence to 'Previous beat coverage: its expected
actors and anchors were observed.' All messages, schemas and facts otherwise match.
No source runtime change was applied; no retries or replacements.

| Fixture / expected act_completed | Control valid/correct | Candidate valid/correct |
| --- | --- | --- |
| Failed portal attempt / false | 4/4, 4/4 | 4/4, 4/4 |
| Portal closed after canyon departure / true | 4/4, 4/4 | 4/4, 4/4 |
| Gate closed then blown open, exit requires current blockage / false | 4/4, 4/4 | 4/4, 4/4 |
| Antidote obtained but not administered / true | 4/4, 4/4 | 4/4, 4/4 |

Every reply HTTP200, schema-valid, distinct IDs per cell, nonempty reasoning.
These local observations do not show an accuracy gain from wording or a
population reliability rate. The preregistered admission rule explicitly required 'no candidate contradicting
confirmed source or assuming a prior voluntary action not established by it';
future exit targets were permitted, and did not count as prior actions.
Correct flags do not satisfy that source/agency gate: candidate portal_left-coverage-3 invents 'a saída por onde
planejavam seguir'; no such route plan was established. Candidate
portal_left-coverage-1 assumes Bento already recognized a trail. The former
alone is enough to reject admission. Control portal_left-control-4 likewise
invented 'Enquanto arrumam o que sobrou'; this problem is not specific to the
candidate. Candidate wording is not shipped. Task69 stays open.

Blind reader d2b724226261 saw all 32 source/output pairs, with randomized labels.
Confirmed mappings: R03=portal_left-control-4; R16=portal_left-coverage-3;
R28=portal_left-coverage-1. Its R19=antidote_secured-control-2 also puts the vial
simultaneously in Iara's hand and in a box slot on the table, an internal
staging conflict. Its R14=gate_reversed-coverage-3 treats 'fora dos trilhos' as
proving zero residual attachment and any metal across the threshold as a full
blockage. Those stronger physical conclusions are not required by the source;
retain ambiguous staging, not a proven contradiction or an additional gate
failure. New physical events and prospective exit targets were explicitly allowed.

Candidate portal_attempt-coverage-3 returned expected_actors ['Iara','Bento']
although its roster supplied C1/C2. The saved response passes today's string-array
schema. Replaying through the actual _validate_beat with that fixture yields []:
both names are dropped as unknown references, including the intended Bento hint.
This is a deterministic local semantic-contract loss, not measured downstream
story degradation. It repeats the preceding compiler's name-versus-ID failure
on the next-beat path. A roster-scoped enum in the output schema is the next
structural boundary to exercise, rather than another prose-only warning.

The text critic's new fixtures were adapted with explicit exits. An unspecified
'neutralize beacon' case was excluded because an ongoing heat hazard does not
by itself prove that extinguishing a guidance beam failed its intended goal.
The gate case explicitly requires current blockage; the antidote case ends at
possession, not administration. Before requests were frozen, preparation caught
that literal anchor wording in the new antidote history did not count as complete
coverage; the fixture names were made explicit ('frasco de antídoto', 'veneno').
No network calls occurred during those preparation failures. No trimming occurred.

Preregistration, frozen manifest and all raw responses remain local artifacts.
The script passes Ruff lint/format; no production source change or full-turn test
follows from this rejected wording screen. Owner play sessions were not used.

Report critic 7486b03e4aa3 requested quoting the admission criterion; included
above. Reject its claim that improvement over control was required: preregistration
required correctness and source/agency compliance, not a positive delta. Its
claim5 merges R14/R19, but the report rejects only R14's stronger physical
conclusions; R19's simultaneous vial placement remains a concrete conflict.
The comparable control defect is preserved, not used to excuse the candidate.
The screen does not diagnose a causal effect of the coverage label.
