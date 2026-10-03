Independent read; run 2dd5abd0158e. Suggestions require source checking; dispositions are recorded separately.

### 1. Contradiction: Mechanical Gate Threshold vs. Absolute Failure Clause
* **Exact Quote:** `"each fixture has at least three schema-valid HTTP-200 replies with distinct nonempty IDs, and every valid reply matches its exact past-act flag. Failures keep their evidence and stop admission; no replacement calls."`
* **Issue:** Direct contradiction. Requiring "at least three" out of four curls implies tolerance for a single transport/HTTP drop. However, `"Failures keep their evidence and stop admission"` can be read as treating *any* failed curl out of four as an immediate disqualification. Evaluators cannot objectively determine whether a 3-of-4 run with one provider timeout passes or fails.
* **Correction:** Replace with: `"At least three schema-valid HTTP-200 replies are required per fixture; flag mismatches or fewer than three valid replies stop admission. Transport drops within the allowance do not stop admission."`

---

### 2. Ambiguity & False-Positive Risk: In-Beat Character Agency vs. State Hallucination (Pair 2)
* **Exact Quote:** `"Fail an invented already-performed voluntary drop in held, or treating the attempt as successful. A future target to pick up, retain, or move the map is not an executed action."`
* **Issue:** Legitimate character choice risks false failure. The distinction between an "invented already-performed drop" (retconning prior history) and an *active, present-beat voluntary drop* (e.g., Iara deliberately dropping the map to free her hands under pressure) is blurred. Additionally, by only clarifying that a "future target" is not an executed action, it leaves ambiguous whether Iara *actually executing* the action of picking up the map in `floor` is permitted or considered a contradiction of the static baseline.
* **Correction:** Replace with: `"Fail framing the map as having been dropped prior to the beat in held, or treating the attempt as successful. Active in-beat decisions (e.g., Iara voluntarily letting go of the map now, or picking it up from the floor) are valid choices, not baseline violations."`

---

### 3. Ambiguity: Unattributed Hazards vs. Closure Damage (Pair 1)
* **Exact Quote:** `"The next beat may introduce a new fitting cause in either fixture; stable is not a ban on future danger. Fail explicit attribution of damage to closure, or treatment of successful closure as an unfinished past action."`
* **Issue:** Unjudgeable edge case. If the model introduces immediate environmental damage without explicitly articulating a new external cause (e.g., *"Dust falls as cracks split the flagstones"*), readers will disagree on whether the damage was implicitly caused by the portal closure or by an unelaborated new fitting cause.
* **Correction:** Replace with: `"Fail only if the text explicitly states the damage resulted from the portal or its closure. Unattributed emerging hazards or ambient cave-ins are treated as new fitting causes, not closure damage."`

---

### 4. Unsupported Expectation: Unbounded Gate Criterion ("Unresolved Material Concern")
* **Exact Quote:** `"A source-supported failure or unresolved material concern blocks this candidate."`
* **Issue:** Unsupported and subjective. In an adversarial protocol intended to rely on exact source-grounded state discrepancies, introducing an undefined `"unresolved material concern"` allows an isolated reader to block a candidate on subjective prose style, roleplay pacing, or aesthetic distaste.
* **Correction:** Replace with: `"A source-supported factual contradiction blocks this candidate; narrative or stylistic reservations must be recorded as non-blocking observations."`

---

### 5. Unjudgeable Requirement: Undefined Past-Act Flag Schema Mapping
* **Exact Quote:** `"every valid reply matches its exact past-act flag."`
* **Issue:** Unsupported expectation. The protocol requires matching an `"exact past-act flag"`, but fails to specify the target JSON key or required boolean/enum value expected from the model response envelope, making mechanical compliance unjudgeable by an independent evaluator.
* **Correction:** Replace with: `"every valid reply matches the fixture's expected past-act boolean in its designated schema field."`

