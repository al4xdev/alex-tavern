### CLAIM 1: Baseline payloads mark failed portal attempts complete (4/4) and confirmed closure incomplete (1/4).
- **VERDICT**: ADVANCES
- **STATUS**: MEASURED
- **STATUS AS WRITTEN**: MEASURED
- **WHAT A READER CAN NOW DO**: Reproduce baseline failure modes using archived wire payloads without re-deriving failure conditions from scratch.
- **FALSIFIER**: Replaying the baseline payloads through `replan_roteiro` yielding `act_index=0` on attempt or `act_index=1` on closure.
- **STRONGEST CASE AGAINST**: Nine synthetic cases from one scenario cannot establish failure frequency in live roleplay sessions.
- **WORSE IF DELETED?** yes
- **METRIC**: Exact act-flag matching over frozen wire payloads (n=36 across 9 cases, 4 curls each).

---

### CLAIM 2: Moving the confirmed-events block to the end produces 12/12 explicit act flag matches across three cases.
- **VERDICT**: ADVANCES
- **STATUS**: MEASURED
- **STATUS AS WRITTEN**: MEASURED
- **WHAT A READER CAN NOW DO**: Test the events-last prompt variant on new cases knowing it clears the local boolean flag gate on these three fixtures.
- **FALSIFIER**: Any valid response on these three cases misclassifying the target act status.
- **STRONGEST CASE AGAINST**: Three cases with identical prompt envelopes cannot distinguish structural prompt efficacy from fixture-specific token sensitivity.
- **WORSE IF DELETED?** yes
- **METRIC**: Pre-registered explicit act-flag classification (n=12 across 3 cases, 4 curls each).

---

### CLAIM 3: Plan `portal_closed-G` re-narrates the extinguishing of runes already confirmed extinguished.
- **VERDICT**: ADVANCES
- **STATUS**: OBSERVED
- **STATUS AS WRITTEN**: OBSERVED
- **WHAT A READER CAN NOW DO**: Block admission of this prompt variant specifically on repeated state transition without disputing the boolean act flag.
- **FALSIFIER**: Textual proof in the prompt context that "últimas runas" refers to a separate, unextinguished rune set.
- **STRONGEST CASE AGAINST**: The phrase can be read as descriptive atmospheric detail rather than an authoritative state transition.
- **WORSE IF DELETED?** yes
- **METRIC**: Two-reader qualitative audit of 23 candidate outputs against source event history.

---

### CLAIM 4: Four bounded traces demonstrate the planner reliably manages a 2-turn delay before act progression.
- **VERDICT**: NEUTRAL
- **STATUS**: OBSERVED
- **STATUS AS WRITTEN**: MEASURED
- **REWORD**: In four runs of a single scripted timeline, the planner advanced the act after two intermediate turns.
- **FALSIFIER**: A run on this scripted timeline advancing at T3 or failing to advance at T6.
- **STRONGEST CASE AGAINST**: Unit-of-analysis error: four runs of a single scripted timeline test stochastic sampling on one sequence, not delay robustness across narrative variations.
- **WORSE IF DELETED?** no
- **METRIC**: Scripted step counter (n=4 runs of 1 timeline, 2 calls per run).

---

### CLAIM 5: The candidate is blocked from production admission solely by the repeated rune transition.
- **VERDICT**: WORSE THAN ABSENT
- **STATUS**: THEORY
- **STATUS AS WRITTEN**: MEASURED
- **REWORD**: The repeated rune transition was sufficient to reject the candidate; other production prerequisites remain unexercised.
- **FALSIFIER**: Remediating the rune transition text results in immediate production admission.
- **STRONGEST CASE AGAINST**: Conflates a fatal local finding with overall readiness; missing builder parity and lack of diverse counterexamples would block admission regardless.
- **WORSE IF DELETED?** no
- **METRIC**: None — this claim is not empirical.

---

- **DELETE**: 4, 5
- **DEMOTE**: 4 (MEASURED → OBSERVED), 5 (MEASURED → THEORY)
- **PROMOTE**: None
- **THE ONE THING**: Treating four repetitions of a single scripted timeline as evidence of temporal robustness mistakes repeated sampling of one fixed sequence for general delay tolerance.

