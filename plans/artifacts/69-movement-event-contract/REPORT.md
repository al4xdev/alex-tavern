# Movement contract: no local benefit established

2026-09-14. One archived Director request, 8bd4d0f1 T21. A retains the original
request; B changes only the opening instruction for `zone_moves`, requiring
a resolved movement before recording its destination. No production prompt
change is proposed from this result.

1. **OBSERVED execution:** A returned four schema-valid outputs. B returned
two schema-valid outputs; its other two planned calls each exhausted the
allowed connection retry without an HTTP response (`curl` exit 28, status
000, about 30 seconds per attempt, with `Connection timed out after 30003
milliseconds`). These are missing responses, not malformed model output.
The final result also records `FileNotFoundError`; use the individual attempt
records above to identify the observed transport failure.
There were eight planned calls and ten attempts, with six returned responses.

2. **OBSERVED source check:** every returned output keeps Liora's blocking in
`corredor interno da passagem secreta`. A0 and A3 omit a Liora move; A1 and
A2 redundantly write that same current corridor into `zone_moves.C7`.
Both returned B outputs have `zone_moves: null`. None places her outside the
blocked corridor. The registered target therefore has no supported occurrence
in the four returned A outputs or the two returned B outputs. The archived
contradiction was not reproduced in this round; its historical existence is
not thereby refuted. A redundant same-zone assignment is not the target.

3. **Decision under the [preregistration](PREREGISTRATION.md):** at least three
valid responses per arm and at least two supported A target failures were
required for follow-up. Both requirements fail. The comparison is unresolved;
it does not show that the candidate prevents the historical move. Wording
trials on this T21 payload stop here, including new seeds and minor rewrites.
The target counts describe one repeated request, not a defect rate across
sessions or an accepted quality metric.

4. **OBSERVED literary and source findings:** the fresh reader distinguished
actual consequences for Riven from repeated disaster setup. B0/V1 has him
trying to dig and Oriana singing to steady the line; A3/V5 forces him back
from the rubble. These are different gains in different arms, not a winner
score. B2/V6 leaves his attempt unresolved and repeats the collapse. Its
blocking also calls the passage both blocked and the only immediate escape
route, while its resulting state says both ends are sealed and no safe route
is defined. This unresolved concern fails the registered follow-up veto:
“Any material concern in B suffices for the veto regardless of whether A also
has it; this does not establish that the candidate caused the concern.”
That is a conservative selection rule, not a finding that B2's overall
literary quality must be worse. One could read “only route” as the only
conceivable option once reopened, but “immediate” and the absent reopening
leave that interpretation unresolved.

## Individual checks after the opaque reading

The [reader verdict](reading-movement/READER-VERDICT.md) was saved before the
arm key was opened. It contains only the visible preceding fiction and event
continuations, not the structured positions. The investigator then inspected
all returned events, blocking, moves, state updates and time summaries.
No returned time summary supplies an alternative escape account. The typed fields below are quoted
directly from the individual `runs/movement-*.result.json` files.

| Slot / call | Liora blocking / move | Source check |
|---|---|---|
| V1 / B0 | inner corridor / null | No target. Riven “erguendo o sabre para escavar pedra com as próprias mãos” leaves the physical gesture unclear; Oriana starts a song. `fuga_rota_principal = norte do salão, única via viável` is asserted while the input has `teto_norte = novas fissuras e uma laje caída sobre bancos`; the reader's concern about the line's destination is not resolved by a stated safe path. |
| V2 / B1 | no response | Two connection timeouts, no returned fiction or target classification. |
| V3 / A0 | inner corridor / null | No target. Repeats Liora's engulfing flash, collapse, Maelis's order and Riven's rescue demand; Bruna is still trying to map the mist. The input T20 narration already says “um clarão verde engole Liora Celestria” and “bloqueando a entrada com um monte de entulho”. |
| V4 / A2 | inner corridor / same corridor | No target. Riven advances and stops before the stones. “Liora ... desapareceu ... quando o teto desabou” is retrospective; it does not establish an exit. The repeated C7 destination equals her input zone. |
| V5 / A3 | inner corridor / no C7 move | No target. `zone_moves.C13` moves Riven from the rubble zone to the hall, supported by “é forçado a recuar ... dos escombros”. The reader recognized a consequence to his attempted approach. Repeated collapse and an unexplained northern refuge remain concerns. |
| V6 / B2 | inner corridor / null | No target. Blocking says “A entrada ... está bloqueada por escombros e não permite retorno” and “a passagem secreta é a única rota de fuga imediata”. No opening/traversal event follows; `corredor_interno = desabado em toda a extensão conhecida, acesso selado para ambos os lados` and `evacuação_em_andamento = true, sem rota segura definida`. This is a separate route contradiction, not a Liora move. |
| V7 / B3 | no response | Two connection timeouts, no returned fiction or target classification. |
| V8 / A1 | inner corridor / same corridor | No target. Repeats flash, mist, collapse, order and Riven's approach. The reader's uncertainty about Liora's precise location is understandable from prose, but CURRENT SCENE already assigns her the inner corridor; preserving that zone is not inventing a new destination. |

The reader wrote that Oriana's and Elowen's locations were missing from the
excerpt. The source places Elowen in `corredor leste` and Oriana in the hall;
that supplies their locations, not a route for the evacuation. B0's cracked
plate is not a clean output-only contradiction: the input narration says it
broke into fragments, while physical facts still describe `selo_improvisado`
as a cracked plate pressed against the gap. Both sources reach the Director;
the mixed input must remain visible in the diagnosis.

## Reproduction and limits

`replay_movement.py prepare` pins debug line 242 and its source hash;
`replay_movement.py run` records actual curl requests and attempts.
`prepare_reader.py movement` builds the opaque fiction projection, filters
events by the preceding viewer's witness ID, resolves canonical names and
stores its own executed snapshot. Neither absent response was repaired or
replaced. Source, manifest, executed-script and preregistration hashes were
checked after the run. The original and candidate have identical non-message
parameters and identical messages after the system message; the only system
substitution is the one registered.

The original prompt says “physically moved to THIS beat (an attempted movement
succeeds)” and “Never teleport someone, invent a convenient connection, or
skip the journey just to bring characters together.”
The [contract trace](CONTRACT-TRACE.md) also identifies its separate canon
reconciliation use of `zone_moves`; this experiment does not validate that
use or a general replacement contract. No schema or graph decision follows.

Two isolated report critics challenged treating a route concern as proof of
inferior overall quality. The wording above now distinguishes the actual
registered veto from such a quality claim and retains the contrary reading.
