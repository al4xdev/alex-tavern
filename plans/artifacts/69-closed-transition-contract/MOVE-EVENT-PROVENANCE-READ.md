# Movement provenance is not encoded by event subject

This is a direct read of two accepted Director turns, not a corpus rate or
an LLM reliability test. It asks one narrow question: can the current
`perception_events[].subject_id` identify the event that caused each
`zone_moves` entry?

| Archived turn | Accepted event | Same-turn `zone_moves` | What the subject field carries |
| --- | --- | --- | --- |
| `d5a2ccf0` T6 | `subject_id=Narrator`: “O instrutor Garran atravessa o vão estreito e se posiciona do outro lado” | `C18` (Garran) moves to the corridor beyond the gap | The event names the mover in prose, but its subject is Narrator. There is no event with `subject_id=C18`. |
| `ea6620fb` T12 | `subject_id=C20`: “Marta puxa Link ... e avançam em direção à abertura” | `C20` (Marta) **and `C1` (Link)** move toward the narrow passage | The subject identifies Marta, but this one event also moves Link. There is no event with `subject_id=C1`. |
| `ea6620fb` T12 control within the same turn | `subject_id=C8`: “Bruna atravessa a passagem ... e chega ao outro lado” | `C8` (Bruna) moves to the new corridor | Here subject and mover coincide; that does not repair the two rows above. |

These examples prove only that an equality join from `zone_moves` actor ID
to event `subject_id` is incomplete: it misses a Narrator-subject crossing
and a second mover in a Character-subject event. No name-string rule was
used to declare a general binding algorithm; the physical actions were
read from the two accepted event sentences and compared to their same-turn
move maps. Another deterministic source of binding may exist, but it is
not present in `subject_id` alone.

The Runner applies `zone_moves` to the scene before prose rendering, while
the event `witness_ids` were clamped against the pre-move scene. In T6 that
temporal split lets the origin audience receive the crossing event while the
post-move roster excludes Garran. An implementation that tries to repair
this by joining `zone_moves` to `subject_id` would miss both counterexamples
above. An earlier whole-mover exemption on the same T6 payload preserved
the crossing but also admitted post-arrival Garran staging in two of four
selected outputs; it is a failed local turn-level candidate, not proof
against every other one. This read does not choose a schema or demonstrate
a producer. See
[`T6-TRANSIT-EXEMPTION-RESULT.md`](T6-TRANSIT-EXEMPTION-RESULT.md).

Sources: `plans/artifacts/repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl`
(Director T6), `plans/artifacts/repetition-battery/base-P1-r1/sessions/ea6620fb/debug.jsonl`
(Director T12), `src/agents/narrator.py` (`validate_perception_events` and
`zone_moves`), `src/runner.py` (`_apply_canon`, `_render_and_prepare`), and
[`T6-GARRAN-CROSSING-STRIPPED-FINDING.md`](T6-GARRAN-CROSSING-STRIPPED-FINDING.md).
