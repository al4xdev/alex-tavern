# Three physical labels do not repair the complete T38 draft

The [frozen screen](T38-LABEL-CONDITIONED-RETRY-PREREGISTRATION.md) replayed
the exact archived T38 Director request and rejected draft. A received generic
consistency feedback; B received only the three labels that the preceding
physical-only F-B packet produced in 4/4 calls: blue gate `closed`, Téo's
attempt `blocked`, actor `Téo Ventobravo`. The exact request bodies, source
and script hashes are frozen in `t38-label-conditioned-retry-manifest.json`.
Every curl request, raw provider envelope, response ID and parsed output is
preserved in `t38-label-conditioned-retry-runs/`.

All **8 direct curls** returned HTTP 200, distinct provider IDs and JSON
valid against the current full Narrator schema. An independent fiction reader
received eight shuffled complete drafts, the committed T37 ending and Téo's
last action, without arm labels. Its read was unblinded only after the
per-draft verdicts. The registered whole-draft gate failed in both arms:

| Arm | Whole drafts coherent | Téo blocked and kept in hall | New blue-gate closure event |
| --- | ---: | ---: | ---: |
| A, generic | 0/4 | 0/4 | 4/4 |
| B, three physical labels | 0/4 | 4/4 | 4/4 |

Each B response gives Téo an unsuccessful encounter with the metal and has no
`zone_moves` for him; each A response narrates him crossing. One A response
then leaves him in the hall with no move despite that prose. These are the
eight observed outputs on one archived beat, not a general improvement rate.

The unchanged failure is visible in the B event channel itself. B-1 says
`As folhas metálicas do portão azul se encontram com um baque surdo,
selando a passagem`; B-2 says `O portão azul termina de se fechar com um
baque surdo`; B-3 says `O portão azul se fecha com um baque surdo`; B-4
says `O portão azul termina de se fechar com um baque surdo`. All are new
`physical_outcome` events in the proposed T38 draft. The source T37 prose
had already said the metal leaves met with a dull slam and all four gates
remained sealed. No intervening opening was supplied. A reader cannot treat
these B events as merely reporting the existing state: they stage the same
closure as the current beat. B-2 through B-4 additionally say the gate was
*already* closed when Téo met it, then make it finish closing afterward.

The reader also flagged witness lists and some scene-update content. Those
observations remain unadjudicated: the supplied source packet did not include
all background events, and the screen did not establish a rule requiring an
actor to appear in their own event's `witness_ids`. Each draft independently
violates the registered no-repeat-closure criterion; removing that closure
alone has not been tested and might leave other failures. In this local
comparison, B's four drafts block Téo while all eight still re-author the
prior gate closure. It does not show why that
transition recurred, that richer automatic feedback would work, or that
model-produced labels can be wired safely into the Runner. Gate identity and
actor were manually bound, the feedback was manually inserted, and no legal
opening control, renderer, state commit or runtime retry was exercised. No
production code or persisted schema changed.
