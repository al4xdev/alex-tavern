# Hand-bound closed-event realizer feasibility, before construction

This is a **deterministic architecture feasibility** screen, not a model
producer experiment. Its question is whether a single closed event grammar
and controlled realizer can preserve selected source events as readable RPG
prose when a human has supplied the best possible event program. It cannot
show that a model can propose that program. No runtime code or session data
will be changed.

Freeze the four selected source beats and their scene obligations before
writing the realizer:

1. `7fd84e9a` T37→T38: already sealed blue gate, team already tunnel,
   Téo's attempted advance; no new closure or unexplained crossing.
2. `5c994c42` T8: main gates ajar→open under external impact, guard enters
   and collapses, Maelis orders evacuation, Garran moves and handles a shield,
   smoke and bells. Director speech is intent; the archived Character words
   are a separate source layer and may differ in wording.
3. `d5a2ccf0` T6: Garran crosses the narrow gap, Elowen tends Cael and
   begins a prayer, reports that Cael needs the infirmary, then a second
   tremor drops a block that rolls several metres. Origin viewers see the
   crossing, not later offstage actions. Elowen's speech intent and her
   separately authored Character words are both part of the source.
4. `05e0dffc` T23: Noa waits to begin; Bruna and Liora pressure her in
   distinct voices, Maelis intervenes and taps her cane. It tests a
   conversational beat with no required durable physical transition.

The source files are pinned by SHA-256 (`debug.jsonl`, then `state.json`):

| Beat | Local source directory | Debug hash | State hash |
| --- | --- | --- | --- |
| T38 | `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a` | `03aef5776ce1565352f1c526ee4c7b17909b3f873ac57cda06704c2f68f1f187` | `c66b438dfb62452153ea9b9c0c841baae366424245b07c7d85eb513caab06302` |
| T8 | `plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42` | `f958df9f12b6926344fbbddf9b1d57d6088442d0da71e35d555a33569fb561fd` | `872ecab6dfd3ad324c15acaaa0a67adfc7d1087c7296f5ffdbcbc82b2488a187` |
| T6 | `plans/artifacts/repetition-battery/base-P3-r2/sessions/d5a2ccf0` | `01cc4b84dd3f4b049e00e2fe3481630cc711a45de3b4ef2c9a69a2ce5873e931` | `94727049f62ebb156ee7a5ffa7a55b9f4088a7b12e4b069da821f7f93fabc669` |
| T23 | `plans/artifacts/p1-archive/null-P1-r2/sessions/05e0dffc` | `ea49f397cff98c81ac391d4e2d056b50bcdd795f3c114d1b874ef8602b84217c` | `daf2afc504c9cd7262d0a7fa16e5bcaa5a7ca39c6cc6ccf62ca0f0e941bb3deb` |

The hand-bound program may name canonical participants, objects and places
from a fixed source glossary. It may use closed action/result and sensory
vocabularies, temporal grouping and event-time audience sets. It may **not**
carry arbitrary source sentence fragments, an `other` action, or a free
`content`/`cause`/style field that could assert an extra event. The one
realizer must use the same action templates and composition rules across all
four beats, with no branch on case ID or source turn. It must keep Character
speech outside its narration; for the T8, T6 and T23 assembled-reader packet,
append exactly the **first `content_type=speech` history record for each
routed Character**, in the Director's `next_speakers` order, as a separate
fixed layer. Later Director-authored echo records are excluded. Those
archived words are not a claim about how a new Character call would respond.

Before looking at any rendered text, freeze the schema, source-to-program
mapping and renderer. Run it once and archive its exact output before reading.
The frozen artifact is `semantic_program_feasibility.py`, SHA-256
`2e51f67cb524b28b1599ad7772cd16683eade981d9192da0559cc44159957529`.
If a required event cannot be
represented in the closed vocabulary, record **coverage failure** and do
not add an ad-hoc free-text escape after seeing that output. There are no
provider curls in this screen; the project's curl-first rule still applies
to later claims about a model proposing or obeying this grammar.

Two independent readers receive source obligations and the four assembled
reader texts, without implementation notes. One judges factual continuity
and event-time perception; one reads as an RPG fiction reader and judges
whether the text can be published as scene prose rather than an incident
list. Each must quote every missing, added or misleading event and any
passage they find flat or incoherent. **Local pass requires all four** to
retain the listed material, add no physical transition or spoken words,
respect audience/agency, and satisfy both readers as finished prose.
One failure stops this exact grammar/realizer pair; split verdicts are
reported, never averaged. This selected set is not a representative sample
or a reliability estimate. A pass would permit a separate real-payload
model-program screen, not Runner integration.
