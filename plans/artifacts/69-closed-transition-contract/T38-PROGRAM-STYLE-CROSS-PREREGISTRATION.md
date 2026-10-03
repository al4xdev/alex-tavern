# T38 event-program authority × archived style reference, before calls

This is a **local realizer feasibility** screen, not a model event producer,
runtime design approval, or reliability estimate. It isolates one archived
T38 setting before any four-beat battery. The question is whether a prose
model follows a closed physical event program when a stylistic reference
depicts a conflicting gate state. A nice rewrite of the reference alone
would fail this question.

## Frozen source and packets

The source is `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/`,
whose `debug.jsonl` SHA-256 is
`03aef5776ce1565352f1c526ee4c7b17909b3f873ac57cda06704c2f68f1f187`
and `state.json` SHA-256 is
`c66b438dfb62452153ea9b9c0c841baae366424245b07c7d85eb513caab06302`.
The **static program S** is source-grounded T37→T38 repair: blue gate already
closed, blue team already in its tunnel, Téo still in the hall, attempts the
former gap and is blocked. No new closure or crossing is authorized. This
program is manually bound; no model selected the state, entity or outcome.

The **legal control program L** is an explicit counterfactual on the same
scene and actors: the blue gate starts ajar, the blue team is already in the
tunnel, Téo crosses from hall to tunnel, and only then the gate closes.
That is coherent but **not** the historical T38 state or a real-world
validation case. It tests whether the output can change when the program
changes, not whether a model could infer L from the archived request.

Two archived Narrator passages from the same session are style references:
T38's persisted narration depicts a fresh closure and crossing; T39's
persisted narration opens on the residual sound of the *previous* closure
and a settled hall. The realizer is told explicitly that both references
carry **zero event authority**, even where their prose sounds causal. The
four cells are S×T38, S×T39, L×T38 and L×T39, four independent direct curls
per cell (16 total). Request order and content are frozen in a manifest
before any curl. Each request has the same system instruction, JSON schema,
Brazilian-Portuguese/no-dash policy, model/settings, names, static scene
glossary and output budget. Only the program and reference differ. The
program is placed **after** the reference in the user message, so a result
cannot be credited to an unrecorded prompt-order change.

The program is a closed list of operations with public names, aperture
before/after, actor position before/after and temporal order. It contains no
source sentence fragments, generic `other`, free cause or event-bearing
content field. The model writes one JSON `narration` string, no dialogue.
There is no retry, correction or post-render event filter. The archived
Character words are **not** appended in this isolated physical screen;
fiction quality of final assembled turns remains untested. T6 and its
conflicting partial-visibility/zone-graph source packet are deliberately
outside this isolated T38 test.

## Frozen decision rule

Technical prerequisite: all 16 HTTP 200 outputs have distinct response IDs,
parse as JSON, pass the current local prose schema, and have nonempty
Brazilian-Portuguese narration. If any fails, report individual outputs but
do not claim an aggregate semantic pass. All requests and raw envelopes are
retained.

Two independent readers receive the scene obligations and shuffled,
unlabelled narration texts, with no code, prompts or conclusion. The
continuity reader must identify every new closure, crossing, move, sonic
impression of fresh closure, or imported reference event. The fiction
reader must judge whether each text works as finished RPG narration and
identify checklist cadence, mere paraphrase, unclear pronouns and any
imagery that makes the wrong physical outcome feel true. A source reader
checks their factual labels against the source/program and separates the
T39 *residual* sound from a fresh closing sound. Reader disagreement is
reported, not averaged.

Local advance to a broader realizer battery requires **all 16** outputs to
obey their own program and audience, add no unsupported physical event or
spoken words, and pass the fiction reader as finished prose. For S, every
output must leave Téo in the hall and the gate already closed, without a
new closure; for L, every output must convey Téo's crossing before a new
closure and leave him in the tunnel. Both outcomes must hold under both
style references. A single material failure stops this exact prompt and
program format. Passing would support only local realizer feasibility under
manually supplied programs; it would **not** validate program production,
source coverage outside this gate, speech assembly, perception across zones
or runtime transaction enforcement. No significance test or population rate
will be inferred from four stochastic calls per selected cell.
