# Manually guided whole-draft retry passes the isolated T38 screen

The [frozen retry experiment](T38-MANUAL-RETRY-PREREGISTRATION.md) sent the
same archived T38 request and the same rejected Director draft to both arms.
The last user message requested a full replacement: A received a generic
consistency report; B received a manually source-grounded report naming the
closed blue gate, current positions, Téo's attempted crossing, and the
rejected draft's contradictory crossing and closure. All **8/8** direct curl
calls returned HTTP 200, distinct provider IDs and JSON valid against the
current Narrator schema built for the 21 present character IDs. No call was
replaced. The old `dungeon_gates: todos os quatro portões abertos` fact stayed
in both arms.

An independent fiction reader saw eight shuffled **complete drafts** without
arm labels, alongside T37's committed ending and Téo's final attempt. After
unblinding, the registered whole-draft gate yielded **A: 0/4 coherent; B:
4/4 coherent**. All four generic retries again completed the blue-gate
closure and narrated Téo crossing the already sealed gap; two also restaged
the already placed blue team crossing. One generic draft declared
`destination_reachable_this_beat=false` yet moved Téo and teammates into
the tunnel. The four grounded retries instead treated Téo's action as an
attempt blocked by metal already closed: e.g. `Téo avança até o ponto onde
estava a fresta do portão azul e encontra metal sólido, sem passagem alguma`.
They kept him in the hall, left the team in the tunnel and described the gate
as already closed, without a new impact. The blind reader found their event,
blocking, move and update channels mutually coherent for this source case.

This meets the **registered local comparative rule**: B 4/4 complete and
consistent; A no more than 1/4. It supports a narrowly defined recovery
operation **when a human has already identified the contradiction**. The B
report explicitly supplies the blocked-gate interpretation, so this is
steerability under a correct manual constraint, not autonomous discovery. It does
not validate the automatic extractor/checker, the fidelity of future
contradiction reports, legitimate reopening, other gates or characters, or
what a persisted renderer would write. All four B responses chose to deny the
attempt; the experiment does not prove that another legal resolution would be
preserved. One archived request, a manually written report and four stochastic
calls per arm do not estimate reliability or prove a general mechanism.

The next boundary is not a prompt tweak on T38. First, an independent detector
must produce a **whole-draft** contradiction report grounded against committed
state, abstain on ambiguous target identity, and accept legal
reopening/crossing controls. Only after that works should runtime retry be
considered. A rejected draft must leave no state,
history, Character call or renderer effect; the accepted replacement must be
checked again before commit. This screen establishes only that a complete
retry with a correct report is worth testing at those boundaries.
