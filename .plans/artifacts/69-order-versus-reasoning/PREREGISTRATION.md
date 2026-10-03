# Order/name correction versus high reasoning, before calls

Owner requested applying plan-before-confirmed-events order, an unambiguous
plan label, and a parallel simple test of the unchanged ambiguous case with
reasoning high. Scope is one existing synthetic closed-portal case. No owner
sessions, persisted JSON fields, schema versions or active provider changes.

Three arms, four fresh direct curl calls each, 12 total: unchanged ambiguous
messages with thinking disabled; applied production-builder messages with old
guidance renamed PREVIOUS BEAT PLAN and RECENT EVENTS last, thinking disabled;
unchanged ambiguous messages with thinking enabled and reasoning_effort high.
The revised arm combines order and label; it does not isolate their effects.
The high arm tests the thinking mode/effort package, not just effort alone.

Use canonical deepseek-flash in all arms; previous response metadata and official
docs established that the frozen request's deepseek-v4-flash alias already served
this model. Increase max_tokens uniformly to 8192 for all arms so high reasoning
is not artificially truncated by the old 1024-token ceiling; set curl timeout180
uniformly for this screen only. No runtime configuration change. Except these
common settings, verify original/high messages and structural schema are exact;
high differs from control only in thinking toggle and reasoning_effort. Reordered
request uses actual production builder/schema via adapter. Preserve old facts,
plan intent, act skeleton, STATUS, schema, text policy and sampling options.

Freeze protocol/script/source and exact requests before calls. Shuffle jobs with
max four concurrent; ensure a high job begins in the first batch alongside other
arms. Secret via curl stdin, preserve raw output/IDs/finish_reason/usage including
reasoning_content; no retries/replacement. Four schema-valid HTTP200 replies
with distinct nonempty IDs required per cell for complete comparison. Expected
act_completed=true. Retain valid counterexamples even if another call fails.
High arm also requires nonempty reasoning_content to verify the mode actually ran.

Read all plans against confirmed portal closed/runas extinguished/people in hall.
Flag mismatches, revived unresolved old closure without a distinct new cause,
invented prior voluntary actions and material uncertainty. Allow independent
new events, genuinely new caused reversals and prospective exit targets.
An isolated reader sees source and outputs, blind arm labels. Manually verify
reader claims. A clean local cell is not general quality, roadmap closure or
proof of mechanism. Summarize returned reasoning as the model's expressed
explanation, not definitive evidence of internal causation. Preserve applied
user-requested order change and disclose remaining failures.
