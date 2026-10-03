# Manual world changes through the planner

Authorized scope: replace the manual narrator_hint input with event. The event
is consumed once by the planner before the Director runs. Rewrite the unplayed
future, preserve confirmed history and completed acts, and reset the replacement
act's clock. Keep the Director's autonomous event channel. No dual API or replay
read. Existing Roteiro and undo snapshots persist the result without new fields.

Manual events start session planning on demand even when automatic planning is
not enabled. Once a session has a roteiro, maintain it so progression survives
later turns. Event rewrites bypass cooldown, old deadlines and ordinary maintenance
in their first beat. Subsequent beats/turns use normal maintenance. An event is
never stored as spoken dialogue, a thought, or a confirmed fact before execution.

Preserve the owner's uncommitted README and roteiro schema descriptions. Test in
isolated temporary data. No commits or remote operations in this task.

The following provider experiment was planned but not run. The owner requested
only breakage checks, so no additional LLM battery will be performed and no
measured claim about narrative quality is made.

Before any real provider calls: use a frozen current-schema session state, one
single-turn scene change and one progressive corruption instruction, three repeats
per case. Use final production builders and curl transport; preserve schema,
language adaptation and actual logging. Follow each progressive case with normal
turns to inspect continuation. Keep source state byte-identical. No shared port.

Decision rule: all six planner calls must produce a first_beat with the requested
initial manifestation and acts carrying the future consequences (including explicit
progression/duration when supplied); the Director must materialize the initial effect
on the very next turn in all six. No original event may be injected again as a
Director hint. Read prompts, raw output, state and logs. If the new plan contradicts
the directive or the effect is absent, reject that candidate, isolate the call and
register a revised variant before repeating. These small checks do not establish
exact arbitrary natural-language duration enforcement, which remains model-authored.

Implemented: event input replaces manual narrator_hint across API, UI, debug log
and replay. Planner rewrites the future before the Director; automatic events keep
their existing channel. Undo restores the scene and plan from before the turn.
Validation: existing full suite completed with 1211 passed and 2 deselected;
HTTP event acceptance and old-field rejection are covered. Provider behavior was
not measured. Unrelated existing formatting failures were left untouched.
