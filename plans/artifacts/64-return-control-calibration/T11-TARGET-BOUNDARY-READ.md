# T11 return-control target is not represented

The archived `base-P1-r2` session `54bcdace` controls **Link (C1)**.
At T11, the accepted Director response has `return_control: true` and
`next_speakers: [C17, C2, C3]` (Maelis, Asword and Mirella). Its own
events have the creature fix its eyes on Asword, Asword offer to lead a
team, and Mirella request Maelis's authorization. Link appears only in
the broad witness lists. The exact logged Director instruction says to
set `return_control` only when a decision, danger or question is aimed at
**one named person** who alone can answer. It does not ask for the target's
identity. The Runner executes the queued Character calls, then uses the
boolean alone to stop the burst and return the next turn to the human's
controlled character. This is a deterministic **interface ambiguity**:
the prompt's named-person criterion cannot be compared with the actual
handoff recipient from the boolean alone. The model may have treated
Maelis or Asword as the target, or it may have set `true` for a general
pause despite the narrower instruction. This one response cannot tell
which happened or prove that giving Link an opportunity to act harms the
fiction.

The [T10–T11 fiction packet](reader-54b-t10-t11.md) contains persisted
narration, speech and action with public names, without the boolean,
controlled-character field or expected label. Two independent content
readers saw the passage. [Reader A](reader-54b-a.md), asked whether a
Link handoff fits, judged it displaced: the last direct petition is to
Maelis and Link is not named. [Reader B](reader-54b-b.md), asked only for
the natural continuation, independently identified Maelis's answer,
Riven's possible response or the creature's attack; it saw no concrete
invitation for another named person. Reader B did not judge a Link handoff
directly. Both saw that the general order to form teams permits initiative
from any student. Thus the final scene has an **open initiative option**,
but not a source-explicit question or decision for Link alone.

The Director selected its boolean **before** the actual Character speech
was generated. The final Mirella line asking Maelis is therefore evidence
about the scene presented to the human, not evidence that this later line
caused the boolean. The accepted Director events already contain Mirella's
petition and no Link-specific request, so the target ambiguity is
visible at the decision boundary too. The subsequent Character speech
preserves rather than creates that asymmetry.

This one source read makes `54bcdace` T11 unsuitable as an
**unambiguous named-person positive control** in another wording trial.
It also leaves the task's claim that all ten handoffs choose the right
dramatic moment open to a fuller fiction read; Reader A disputes this
one, while Reader B only predicts another continuation. The earlier
five-payload screen already
stopped at 37/40 valid outputs and its T11 A baseline reproduced `true`
only 1/4 fresh calls; these results are not re-scored here. One literary
judgment does not establish a false-positive rate, and an open pause for
human initiative may still be a good product choice.

The next design decision is whether this boolean means a pause for an
**open human initiative** or a pause for a **specific named person's** next
action. The existing instruction expresses the latter; the Runner's
consumer implements the former. Neither a new target field nor new prompt
wording is validated by this case. No runtime code or prompt changed in
this source audit.
