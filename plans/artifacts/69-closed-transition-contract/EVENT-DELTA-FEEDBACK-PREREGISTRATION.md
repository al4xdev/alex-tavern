# T38 event-delta feedback in a full Director retry, frozen before calls

The preceding real T38 retry supplied a correct final gate state and blocked
attempt, yet all four complete drafts re-authored the already completed gate
closure as a new event. This screen tests the missing distinction directly in
the complete Director output: **final state versus a new aperture transition
in this beat**. It does not claim that a model can automatically extract the
delta. A prior draft is uncommitted in every packet.

**A** reuses the exact three-label T38 retry request from the previous frozen
screen as a fresh control: original archived T38 system/user messages,
rejected T38 assistant JSON and the physical-label feedback. **B** is the
same request except the final report adds the single field
`aperture_delta=none` after `next_aperture=closed`; every other byte of that
request is unchanged. `none` means the tracked blue gate makes no new
aperture change in T38, while the attempt remains blocked. The source T37
ending already sealed that gate and placed the team in the tunnel.

**P** is a legal-opening control. It uses the exact archived T8 Director
system/user messages and the accepted-but-uncommitted T8 Director JSON as a
proposed assistant draft. A final user message requests a complete new draft
from the same source and supplies `initial_aperture=ajar`,
`next_aperture=open`, `aperture_delta=opening`,
`attempt_outcome=not_applicable`, `actor_name=` for the main gates. It asks
the Director to preserve the other supported events, as in A and B, without
naming those events in the feedback. The archived T8 draft
contains an external impact forcing the gates open, a guard entering and
collapsing, Maelis ordering an escort and Garran raising/pushing his shield.
This control is not paired with an unconditioned P arm and has a different
source and feedback packet; it only checks whether this one legal opening and
its adjacent events survive, without attributing any loss to the delta field.

Use the original DeepSeek model/settings, adapter JSON instruction, current
Narrator schema for the 21 present IDs, thinking disabled, four fresh direct
curls per packet (**12 total**), no retries/replacements. Freeze the source,
protocol, script, schema and exact requests before calls. Save every request,
raw envelope, provider ID and parsed response. All 12 must be HTTP 200,
distinct IDs and schema-valid before aggregate content grading; otherwise
report incomplete. An independent reader sees shuffled complete drafts and
source scene summaries without packet labels. The T8 scene is recognizable,
so the blind comparison applies only to T38 A versus B. For each T38 draft judge new
blue-gate closure, re-crossing of already placed teammates, Téo's attempt,
and event/move/blocking/update agreement. For each P draft judge legal
opening, guard entry and collapse, Maelis's order, Garran's shield action,
and any unsupported replacement. Quote decisive passages. Unblind only
after the read.

**Registered local rule:** B must have 4/4 complete coherent T38 drafts with
no new blue-gate closure or re-crossing, Téo's attempt given a blocked
consequence without teleport, and no internal physical contradiction. If B fails once,
this exact event-delta feedback is stopped. If B passes while A passes at
most 1/4, it yields a local comparative signal; B passing with A at 2/4 or
more is an inconclusive comparison. P must also produce 4/4
coherent legal openings with the guard, Maelis and Garran actions retained;
otherwise the feedback bundle is not suitable even for this local pair.
Passing these selected beats would still not validate automatic delta
extraction, entity binding, persistence, renderer projection or model
reliability. No runtime producer follows directly from this screen.
