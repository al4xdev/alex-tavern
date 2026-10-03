# T38 stale-fact-only repair fails its local screen

The [frozen paired replay](T38-STALE-FACT-AB-PREREGISTRATION.md) used the
archived T38 Director request verbatim in A and changed only one
`CURRENT SCENE` value in B: `dungeon_gates` from `todos os quatro portões
abertos...` to `todos os quatro portões selados`. Eight fresh direct curl
calls returned HTTP 200, distinct provider IDs and parseable JSON objects
with `perception_events` lists, meeting the **registered technical
prerequisite (8/8)**. No call was replaced. This prerequisite was intentionally
weaker than production Narrator schema validation; a blind reader later
noticed outputs with character-name zone keys and mismatched subject IDs.
A **post-hoc diagnostic**, outside the registered gate, ran the current
`build_narrator_json_schema` and local validator against all eight responses;
all eight passed. That schema permits arbitrary string keys in
`character_zones` and cannot determine whether an event's `subject_id`
matches its prose. The replay remains a content diagnostic, not a validated
runtime continuation or a model reliability estimate.

The blind content reader received T37's completed closure, Téo's pending
crossing attempt, and eight shuffled output packets without arm labels. It
read new blue-gate closure in **A: 1/4** and **B: 4/4**. It distinguished
`O último baque ... se dissipa` and a character reporting that gates *had*
closed from a new impact. No A event replayed the blue team's crossing. One B
output did not narrate a crossing but moved Téo **and the already placed team**
into the tunnel again through `zone_moves`; the reader marked crossing
`unclear` across the event and zone channels. Another B output silently
placed Téo beyond the closed gate. The four B outputs all repeat the closing
impact, including two that explicitly say the gate is already closed in their
own blocking draft.

The registered sufficient-repair rule required B to avoid **both** repeated
crossing and repeated closure in 4/4, with A showing both defects in at least
3/4. Neither condition holds. The preregistration separately says any B
repeat makes the single correction insufficient; B repeats closure in 4/4,
so it is **insufficient on this T38 payload**. The
observed A/B direction does not prove that the correction caused more
repetition; the baseline varied and only one payload was sampled. The
unresolved action intent, scene state, history and lengthy directives remained
unchanged. No runtime fact patch or producer follows.

The blind read also exposed a **schema-blind semantic limit**: interpretable
events sometimes used character names rather than IDs in spatial maps or
attributed an event to the wrong subject. The post-hoc schema pass does not
approve those outputs as coherent Director decisions. A future replay aiming
to validate a candidate fix needs both current-schema local validation and a
content read of the whole event/zone/prose path. The actual T38 defect remains
a multi-boundary continuity problem, with causal weights undiagnosed.
