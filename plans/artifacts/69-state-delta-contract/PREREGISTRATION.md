# State-delta contract screen

Planned 2026-09-14 before calls. Selected case: fb62cc2f T4, accepted Director
request at debug line 42. Prior state says `plataforma_de_comando = diretora em
posto, mensageiro retido por Elowen na porta leste`. The recorded delta adds
`feridos_no_portao_leste = um mensageiro ferido ... chegou à plataforma de
comando`, without updating or removing the earlier statement. A deterministic
replay of Runner._update_scene retained both statements and matched the full
T4 physical-facts snapshot. This is a reported implementation observation,
not a cause of later fiction.

THEORY: the existing instruction to reuse keys and remove nonexistent items
may not elicit updates of a compound fact when only one of its assertions
changes. Test one replacement of that instruction, keeping the caller, schema,
input and placement fixed. No additional runtime model call or storage is proposed.

A: exact recorded request. B: replace only the scene_update paragraph with
the candidate in replay_delta.py. It says to update/remove older assertions
invalidated by this turn's resolved events, preserve still-true parts of a
compound value, and treat orders/attempts/plans as not yet executed. The exact
candidate and both complete payloads are frozen and hashed before dispatch.
Four calls per arm, order shuffled with seed 694204, concurrency four. One connection retry only
with no HTTP response; retain malformed and absent responses without replacement.

Read before counting. A fresh literary reader gets the preceding visible story
and opaque proposed Director events with resulting physical state. A separate
source reader gets the same alternatives, the prior state and full prior
accepted source. Both remain blind to arms until their judgments are saved.
The state projection must use the actual current Runner._update_scene;
preserve raw delta and any discarded values separately so model and program
are not conflated. Invalid output is not an enacted continuation.

For each alternative classify the messenger transition and resulting state,
in this order: CONFLICT if an explicit resulting claim contradicts the resolved
events/prior source (including unsupported release, movement or arrival), or
simultaneously retains incompatible current locations; AMBIGUOUS if the source
read cannot resolve a material uncertainty; NO TRANSITION only if no release,
movement or arrival resolves and the consistent resulting state keeps him
retained; otherwise SUPPORTED only when a release, movement or arrival actually
resolves in the events, is compatible with the prior source, and agrees with
every retained current-state assertion. A proposed new event need not have
already happened in history; an order or attempt alone is not its execution.
Allow release, ongoing travel and arrival as distinct outcomes. Do not force
arrival to count as success. Read all other events and facts for material
continuity, loss of still-true facts or agency defects; quote each concern.
Material means changing an actor's available action, position, access, knowledge
or an event's outcome, not mere wording preference. Source checking adjudicates
both readers' concerns before revealing arms; unresolved disagreement about a
material concern remains AMBIGUOUS, not a vote. Projection failure is ineligible
even if the JSON schema accepted the output, and is retained as such.

Absolute exploratory follow-up rule, not a comparative quality score: require
at least three schema-valid outputs in each arm; at least two A outputs must
reproduce CONFLICT; all valid B outputs must be SUPPORTED or NO TRANSITION,
with at least three SUPPORTED transitions and no source-checked material
continuity/agency defect or unresolved material ambiguity. This only qualifies
the exact variant for production-builder verification and a live continuation;
it never establishes a general benefit or authorizes deployment by itself.
Any unmet condition stops this candidate on this frozen request, including
insufficient eligible responses, non-reproduction and ambiguity. A transport
failure or invalid output remains in the record but does not by itself stop
the screen if each arm still has at least three eligible responses. No
seed/synonym tuning.

The preregistration critic identified overlapping SUPPORTED/NO TRANSITION
definitions and an unspecified resolution of reader disagreement. The definitions
above were corrected before any dispatch. The exact replacement paragraph is:

```text
- "scene_update": object with changes to the current scene (e.g.,
  {"location": "Old Watchtower", "door": "open"}). "location" and
  "time_of_day" are reserved Scene fields. Every other key is a physical
  fact for the current location. Reuse the existing snake_case key for the
  same fact; do not add a synonym alongside it. Use null if nothing changed.
  After resolving this turn's events, update every existing fact they make
  false. If a value combines several assertions, rewrite it to preserve the
  still-true parts while replacing the changed part. Set a key to null only
  when none of that fact remains current. A new key does not retire an old
  assertion. Orders, plans and attempted actions are not completed events.
```
