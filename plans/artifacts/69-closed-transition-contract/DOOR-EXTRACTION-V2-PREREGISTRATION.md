# Existing-opening extraction screen V2: hall gates

Frozen as an execution rule before any provider calls on this second source case. This V2 is a local consistency screen for one already-named door aperture, not a claim about gap creation, general extraction reliability or narrative quality.

## Source and labels

The frozen source is `plans/artifacts/p1-archive/drive-P1-r1/sessions/5c994c42/debug.jsonl`, successful first-attempt Director responses T7, T8 and T10 in one archived session. T6 scene_update sets `portões: semiabertos`. T7's pre-decision spatial draft says the main gates are semiopen; the events describe a clarion, dust, a chest opening, orders and reactions; its scene_update contains no gate change. T8's draft starts semiopen; the gates then `se escancaram`, and scene_update says `portões: abertos por impacto externo`. T10's draft says the main entrance is open; the doors burst inward, the event later says `through the open doors`, and scene_update says `portões: forced open, broken`. T10 repeats a wounded-guard entrance from T8. The event still says the doors are open after the impact. One isolated model reader reviewed these three excerpts without code or extractor outputs and labeled T7 no opening, T8 ajar-to-open, and T10 no closing (one reading, no agreement estimate). These are source readings, not historical typed-state ground truth.

| Turn | Fixture current | Candidate | Expected | Source reason |
| --- | --- | --- | --- | --- |
| T7 | `ajar` | `open` | `no_change` | Neither event nor update opens the gates; only a chest opens. |
| T8 | `ajar` | `open` | `change` | The gate event and scene_update both say it opens. |
| T10 | `open` | `closed` | `no_change` | After the impact, event and update still say the entrance is open. |

The catalogue uses only the public label `main hall gates` and dimension `aperture`. The current states are manual fixtures derived from that sequence. T10 tests only whether a strong impact is mistaken for closing, not whether the already-open door sustained damage. The three turns are one session, so repeated samples are not independent narrative units.

## Frozen request and decision rule

Project only `scene_blocking.spatial_constraints`, `perception_events[].content` and `scene_update` from each accepted Director response. No character or witness ID, later narration, or historical physical-fact bag enters the request. `scene_blocking` is a pre-decision spatial draft, then event list, then scene_update. Use the first screen's system instruction, local JSON-schema validation and DeepSeek V4 Flash curl settings, adapted to a single catalogue property and its fixed candidate. Output exactly one JSON object with `aperture: change | no_change | uncertain`. `change` is legal only if the candidate differs from current and the proposal explicitly warrants the candidate. `uncertain` authorises no transition but is not counted as correct in these three source-clear cases.

Save source/script/preregistration hashes and frozen requests before execution. Verify hashes and reconstructed requests immediately before running. Four separate curl calls per turn, twelve calls total, with no retries or replacement calls. Save request, raw envelope, provider response ID, parsed output, schema result and HTTP/transport status for every call. Keep the configured secret off CLI and out of artifacts.

If fewer than twelve calls are HTTP-200 and schema-valid, the technical screen is **incomplete**, not a semantic failure; report the invalid calls without replacing them. If all are valid, advance this narrow extractor shape only when every T7 output is `no_change`, every T8 output is `change`, and every T10 output is `no_change`. Any differing valid label stops this candidate for investigation; it does not establish a population error rate or general model incapability. Even a pass permits only a later producer-to-renderer fidelity experiment; it does not authorise production integration, Task 69 closure or a claim that newly created gaps are handled.

After scoring, read the three source proposals and all outputs as fiction, and report any unscored continuity or object-identity issue separately from the fixed gate. Report the repeated guard separately as a possible continuity issue; it does not change the scored door-aperture predicate.
