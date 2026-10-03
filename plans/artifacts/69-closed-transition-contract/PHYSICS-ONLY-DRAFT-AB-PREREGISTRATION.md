# Physical-only T38 draft-presence A/B, frozen before calls

The prior real-source transaction screen bundled physical decisions,
non-gate event prose and a rejected Director draft. Its blue T38 outputs
failed, but that bundle does not tell whether the model copied the bad draft
or could not resolve the committed gate state. This screen asks only for the
physical decision of one named gate and one tracked attempt. It produces no
story text and makes no runtime change.

Source **F** is the archived `7fd84e9a` T38 Director user context. The
manually anchored committed facts are: blue gate aperture `closed`; Téo
Ventobravo is in the hall, has attempted to advance through its former
fresta; Mirella, Nix, Doran, Liora and Bruna are already in the blue tunnel.
The last action is still an attempt, not a successful crossing. Source **P**
is archived `5c994c42` T8: main gates begin `ajar`, and the accepted draft
explicitly has an external impact force them open. The T8 opening is the
legal positive control, not an invented target outcome.

Three packets, four fresh independent direct curls each, no retry or
replacement (**12 calls**):

* **F-A:** exact archived T38 Director user context plus the committed typed
  gate/position facts and last attempted action; **no accepted T38 draft**.
* **F-B:** identical F-A packet with the accepted but uncommitted T38 Director
  draft attached as proposed material. This is the only F arm difference.
* **P:** exact archived T8 Director user context plus initial `ajar` and its
  accepted but uncommitted proposed draft, to test whether a legal opening
  is preserved. There is no tracked character crossing in P.

The JSON contract has `next_aperture` (`closed|ajar|open`),
`attempt_outcome` (`blocked|crossed|not_applicable`) and `actor_name`
(canonical public Téo name or empty). It asks for **no free-text event,
explanation or quotation**. Generic instructions state that an action is an
attempt until confirmed; a new aperture state requires a physically supported
change in the supplied context/proposal; a pre-existing closed gate does not
close again; a character already in the tunnel is not crossed again. No
case-specific `Téo is blocked` answer is supplied. Use the DeepSeek adapter's
JSON instruction and the shared client's Portuguese/no-dash instructions.
Freeze source, protocol, script, schema and exact request bodies before
dispatch. Save all HTTP requests, raw envelopes, provider IDs and outputs.

Technical prerequisite: all 12 calls HTTP 200, distinct response IDs and
schema-valid output; otherwise the screen is incomplete, with valid
individual outputs still readable. Registered local content rule: F-A and
F-B each pass only if all four outputs are `closed`, `blocked`, `Téo
Ventobravo`; P passes only if all four are `open`, `not_applicable`, empty
actor. If all three packets pass, the narrow physical selector merits a
separate conditioned-prose test. If F-A passes but F-B fails, the archived
draft is a local candidate contributor to the failure; the exact JSON
contract still fails when used for source-draft repair. If F-A fails, removing
the draft alone did not resolve the source conflict. If P fails, the selector
cannot preserve the legal positive even in this sparse output contract.
No comparison here estimates a model failure rate or proves which input
caused a difference across one stochastic beat. A content reader may audit
source semantics and any surprising output; numeric labels alone are not
fictional-quality evidence.
