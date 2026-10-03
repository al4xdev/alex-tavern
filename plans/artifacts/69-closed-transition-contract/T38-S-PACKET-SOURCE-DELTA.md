# T38 S packet: source delta, not a cause of the prose failure

This is a direct comparison of one archived T37→T38 pair with the later
manually constructed S packet. It neither changes Task 69's runtime nor
explains why one generated S paragraph sounded like a report.

| Source at T37 | Archived content | In constructed S packet? |
| --- | --- | --- |
| `scene_update` | `gate_blue=fechado`; selection status says the blue team entered, Link was disqualified and all gates were sealed | Blue gate closed and team in tunnel: yes. Link's status: no. |
| `time_skip_summary` | Blue team enters; gate closes with a dull impact; hall falls silent; officials disperse | Team in tunnel and closed gate: yes. Silence, impact and dispersal: no. |
| Existing scene `physical_facts` | Mana lamps and rank banners D/C/B/A | Lamps: yes. Banners: no. |
| Persisted narration | Lamp flicker, still banners, echoed footsteps and other phrasing | Not included as a prose reference. This row is *history*, not an additional state update. |

The Director requested three skip ticks in T37. The Runner's
`_apply_time_skip` appends a nonempty `time_skip_summary` to
`perception_events` as an observation for the present cast before rendering.
That makes the summary part of the accepted **perception-event channel** for
this turn. It does **not** make every clause a typed durable physical-state
transition. The scene also retains a conflicting older `dungeon_gates` free
fact saying all four gates are open; this comparison does not reconcile it.

The S packet's sole current-beat operation is `attempt_cross` with outcome
`blocked`, no gate change and Téo still in the hall. It does not specify
contact, stopping distance or recoil. The archive likewise does not say those
interactions occurred in T38. Adding one to this *historical* fixture as if
it were recovered evidence would be fabrication; authoring one as a new
counterfactual event would be a different test.

The S author and fiction reader each ran once. Their report-like S result is
about that exact sparse packet and output; this source delta does not assign
causality to any omitted field or select the next Task 69 design.

Sources: `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/debug.jsonl`
(Director T37/T38); corresponding `state.json` (scene facts, T37 narration);
`plans/artifacts/69-closed-transition-contract/t38-constructive-author-packet.json`;
`src/runner.py` (`_apply_time_skip`); and
`T38-CONSTRUCTIVE-PACKET-RESULT.md`.
