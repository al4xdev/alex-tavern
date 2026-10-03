# Physical-only T38 draft-presence screen: local pass

The [frozen protocol](PHYSICS-ONLY-DRAFT-AB-PREREGISTRATION.md) isolated one
blue-gate aperture decision and one tracked attempt from the earlier failed
whole-transaction screen. F-A used the archived T38 Director context and
manually anchored committed facts with no proposed draft. F-B added the
archived, uncommitted T38 draft to the otherwise identical packet. P used the
archived T8 context and its proposed, physically supported gate opening as a
positive control. Exact requests, source/script hashes and schema are in
`physics-only-draft-ab-manifest.json`; all curl requests, raw provider
envelopes, IDs and parsed outputs are in `physics-only-draft-ab-runs/`.

All **12 independent direct curls** returned HTTP 200, a distinct response ID
and a schema-valid three-field JSON object. The pre-registered exact local
rule passed in every packet:

| Packet | Exact expected physical labels | Matches |
| --- | --- | ---: |
| F-A, no proposed draft | `closed`, `blocked`, `Téo Ventobravo` | 4/4 |
| F-B, with proposed draft | `closed`, `blocked`, `Téo Ventobravo` | 4/4 |
| P, legal opening | `open`, `not_applicable`, empty actor | 4/4 |

An independent content-only reader checked the source scene semantics: T37
had already closed and sealed the four gates; the subsequent T38 action was
Téo's attempted advance, with no intervening reopening. T8 explicitly opens
the previously ajar main gates by an external impact. The reader judged the
F and P labels consistent with those texts. This is a source reading, not an
additional model-call success count.

F-A and F-B each returned the same tuple in all four calls. That does not
show that uncommitted drafts are harmless in
general, nor identify why the earlier whole-transaction candidate failed:
its interface also required ordered operations and non-gate content. The
manual starting state, public gate identity, tracked actor and single attempt
were supplied in this screen. It tested neither target binding, dynamic entity
creation, whole-event fidelity, prose generation, nor persistence. Four calls
per packet on one beat per case are a local gate, not a reliability estimate.

The registered consequence is to test prose conditioned on these physical
labels separately. No runtime producer or renderer is admitted from this
result, and no production code or persisted session contract changed.
