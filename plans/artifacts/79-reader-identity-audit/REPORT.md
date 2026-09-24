# Reader identity audit, 2026-09-05

## 1. Decision: the old 35/40 is not a canonical-name baseline

OBSERVED by inspecting all 40 saved rows: `character == cid` in every row of
`plans/artifacts/79-positional-audit/blind_read/results.json`. For example, the
first row is session `c76037ff`, T16, `cid: C11`, `character: C11`.
The saved state's `characters["C11"]["mind"]["name"]` is `Bram Muralha`.
The archived collector reads `c.get("name") or cid`; its judge inserts that
value into `PERSONAGEM`. The script therefore reconstructed character labels
from the wrong level of the schema.

The old result remains a historical count of 35 undeterminable judgments among
40 ID-addressed cases. It does not support the published method description
that a reader received a canonical name. Retire its use as task 79's acceptance
baseline and task 80's measured omission evidence, independently of the replay
outcome. This identifies a defect in the instrument, not proof that the prose
is clear or that IDs caused every old unknown answer. Original artifacts stay
unchanged.

## 2. Contemporary paired reconstruction: 240 successful calls, 20 sessions

Pre-registered in `PREREGISTRATION.md`, before calls. The manifest pins all 40
original case identities from 20 sessions, chosen state paths/hashes, the old
script/hash and exact prompts. Three calls per arm per case; A uses the old ID,
B uses `mind.name`; no other prompt difference. Original narration collection
is preserved, including joining audiences and the 4000-character cap (none of
these 40 cases reached that cap). Calls used curl and `deepseek-v4-flash`, with
seed 790905 interleaving and six concurrent requests. All 240 returned HTTP 200
and a parseable answer with an allowed verdict and string evidence; none were
replaced. Requests, envelopes and audit metadata are under `runs/`.

This is reconstruction: the original judge did not save its request envelopes,
so historical byte identity and historical provider behavior cannot be verified.
It is not a post-blocking production A/B and not a player's single-view read.

The registered rule was to report the stochastic arm difference without a
significance or causal claim, and to withhold baseline promotion if reading
exposed material judge failures. Baseline retirement was fixed independently
of the new outputs. The automatic counts below preserve the experiment's
outcomes; none becomes an acceptance threshold.

## 3. Reading the answers prevents another false baseline

OBSERVED manual review, not blinded: read every determinate answer (52 answers
over 19 distinct cases) against its full submitted narration. Also read five
systematically spaced cases with six undeterminable answers each: indices
0, 7, 20, 27 and 37. For example, case 37 targets Ysara Lua-Parda, while its
text describes a fissure, a chamber, a mural and unidentified observers; it
does not identify Ysara's movement. This is not a measured
precision/recall estimate; manual answers do not overwrite automatic labels.

Concrete failures and limits:

- **Wrong subject in the old task-81 example.** Case 30, `00997daa` T16,
  target C1 = Link: the passage is `Asword é o primeiro a se mover. Ele recua
  da beira da rachadura`. The old judge's quoted retreat belongs to Asword.
  One fresh ID answer repeats that attribution; one fresh name answer instead
  infers Link from unspecified students. Neither supplies explicit movement
  evidence about Link. Retire task 81's claim that both readings described
  the same character correctly; this example does not establish a contradiction
  between Link's state change and his narrated action.
- **Correct names do not validate the movement categories.** Case 6,
  `5d60575d` T3, one of three name answers calls Asword's `permanece de pé`
  a reposition. Case 19, `09aabf25` T22, all three name answers call Link's
  short step toward the north gate a room change; no threshold crossing is
  asserted in the text. These answers cannot validate the room-versus-position
  distinction.
- **Wrong actor despite a canonical target.** Case 34, `75d9f36f` T19,
  one of three Asword-name answers cites an unnamed hooded figure leaving;
  the narration does not identify that figure as Asword.
- **An unchanged endpoint can hide a corrected attribution.** Case 35,
  `834f91e5` T8, target Nix: all three ID answers cite Cael climbing stairs;
  all three name answers cite Nix positioning herself at the threshold.
  Both arms are determinate, but only the name answer cites the focal actor.

Correctly copied words can still describe the wrong person. On the registered
rule quoted above, these material reading failures prevent promotion of B to a
validated acceptance baseline. Exact-substring evidence flags remain in the raw
summary for audit, without being treated as semantic error rates.

## 4. Consequence for the roadmap

Task 79's already shipped, viewer-filtered blocking path stays in place; this
audit neither evaluates nor reverts it. Its quality acceptance remains open,
requiring a correctly named, per-viewer read that separates useful staging from
invented movement. Task 80 stays a backlog hypothesis without the old quantitative
support. Task 81 stays a backlog hypothesis with its cited subject attribution
withdrawn. No schema, graph, priority or production-code change follows.

This audit invalidates the cited 88% hurdle; it does not establish the next task
or alter the deferred blocking persistence decision.

## 5. Review decisions and reproducibility

Critic framings split on presentation: the deletion review rejected prominent
diagnostic percentages as a potential replacement headline; the demotion and
arithmetic reviews retained them as measured instrument output, not quality.
The counts are retained below as an appendix so the experiment remains recorded.
The preregistration review rejected calling a nonzero stochastic contrast
"name sensitivity"; that phrase was removed before calls. These reviews are
method checks, not independent evidence of the narrative conclusions.

Reproduction commands are `audit_reader_identity.py prepare`, `run` and
`analyze`; the latter recomputes the automatic summary. The generation-time
script is preserved at
`runs/executed-script.py`; the tracked copy differs only in wrapping its prepare
status message to satisfy lint. Source hashes in the manifest preserve the old
script and saved-result identities. Raw state files and replay outputs remain
local, as in the existing archive policy; this report preserves the reviewed
conclusions and the method when those large artifacts are not available.

## Diagnostic appendix: automatic output frequencies

MEASURED automatic labels on the pinned sample, not a quality score:

| arm | undeterminable / calls | pooled share | session mean | session median | session population sd | session range |
|---|---|---|---|---|---|---|
| ID | 104/120 | 86.7% | 82.6% | 100% | 27.7 points | 0-100% |
| canonical name | 84/120 | 70.0% | 66.9% | 81.7% | 35.5 points | 0-100% |

Each session's rate averages repeats within a case, then its cases equally.
The paired name-minus-ID difference has mean **-15.8 points**, median **-3.3**,
population sd **35.2**, range **-100 to +66.7**. Ten sessions decrease, two
increase, eight tie. This is an observed stochastic contrast on the pinned
sample; no p-value, causal effect or population claim. The new 70% is not a
replacement validated baseline.


Per-session automatic rates (repeats are averaged before cases):

| session | original cases | ID unknown | name unknown | name minus ID |
|---|---|---|---|---|
| 00997daa | 3 | 77.8% | 55.6% | -22.2 points |
| 09aabf25 | 2 | 50.0% | 0.0% | -50.0 points |
| 11028536 | 2 | 100.0% | 50.0% | -50.0 points |
| 17ec48d5 | 1 | 66.7% | 100.0% | +33.3 points |
| 21f7c4e1 | 1 | 100.0% | 100.0% | +0.0 points |
| 22b27d6e | 1 | 100.0% | 100.0% | +0.0 points |
| 34390b86 | 1 | 100.0% | 33.3% | -66.7 points |
| 377582f0 | 1 | 33.3% | 100.0% | +66.7 points |
| 45dac069 | 2 | 100.0% | 100.0% | +0.0 points |
| 54bcdace | 2 | 100.0% | 83.3% | -16.7 points |
| 5d60575d | 5 | 100.0% | 93.3% | -6.7 points |
| 63deac61 | 2 | 50.0% | 50.0% | +0.0 points |
| 75d9f36f | 4 | 91.7% | 91.7% | +0.0 points |
| 834f91e5 | 1 | 0.0% | 0.0% | +0.0 points |
| 87157fa1 | 2 | 83.3% | 50.0% | -33.3 points |
| 8bd4d0f1 | 1 | 100.0% | 0.0% | -100.0 points |
| a3e1ceda | 2 | 100.0% | 50.0% | -50.0 points |
| c76037ff | 5 | 100.0% | 80.0% | -20.0 points |
| d0cc98e5 | 1 | 100.0% | 100.0% | +0.0 points |
| d5a2ccf0 | 1 | 100.0% | 100.0% | +0.0 points |
