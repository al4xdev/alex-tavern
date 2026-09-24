# Plan precedence: candidate failed the local screen

2026-09-05. The candidate is not integrated. The fixed rule required at most one clear roof restaging in B and at least three in A. Among valid returned continuations, this one roof payload produced A3/3, B2/4, C0/3. B therefore fails independently of any qualitative veto. Evacuation B0/V11 says both “grupos em formação” and “quartetos já designados”. The investigator retained ambiguity between re-forming groups and organizing an existing queue; the fixed rule disallows ambiguous target classifications. No general narrative improvement, session-level population rate or accepted wording follows.

A retained the archived prompt; B replaced the anchor heading and the existing beat footer with explicit precedence for confirmed history; C removed the complete ROTEIRO block only as an input diagnostic. All other messages and provider parameters stayed unchanged. The [preregistration](PREREGISTRATION.md), requests and executed script are pinned in `runs/run.json`; neither previous experiment's responses nor replacement calls enter this comparison.

## Returned content and missing validity

| Selected session / payload | A: original | B: heading + precedence | C: no ROTEIRO |
|---|---|---|---|
| bb72dc94 T10, evacuation | 3 valid, 1 invalid | 4 valid | 4 valid |
| 8bd4d0f1 T34, roof | 3 valid, 1 invalid | 4 valid | 3 valid, 1 invalid |

All planned calls returned model text. The invalid responses are two malformed JSON documents and one non-enumerated event kind. Their fictional text was included in the literary packets; projection-only delimiter/control-character handling never changes their invalid status. The minimum of three valid outputs per arm per session is met, and B has no excess invalid outputs over A. These operational counts are distinct from the content decision.

Two fresh readers received the five preceding viewer-visible turns and opaque continuations, with canonical names and action attempts distinguished from outcomes. Each read one session; this is not two-reader agreement on the same material. Free judgments were saved before the keys were opened. [SOURCE-CHECK.md](SOURCE-CHECK.md) provides every alternative's attribution, quotations, strengths, ambiguities and corrections after consulting the full source request.

## Classification behind the decision

The investigator classified the outputs after saving the free literary reads. The target is the already completed chamber-roof collapse, not every new fall of stone. T33 says “O teto da câmara oculta se desfaz com um rugido” and buries the entrance. The valid positives are A0/V4 (“O teto da câmara oculta desaba com estrondo”), A1/V10 (the same roof “desaba com estrondo”), A3/V6 (“O teto da câmara desaba ... soterrando a entrada”), B1/V9 (“O teto da câmara oculta desaba em estrondo”) and B3/V12 (“O teto da câmara oculta se rompe de vez”, followed by the entrance being buried). None identifies a remaining section or distinguishes a new collapse from T33. A1's additional small stone fall near Noa is a separate consequence and was not counted as another target event. C0/V3 describes Riven trying the rubble, C1/V7 describes a tentative pulse correlation, and C2/V8 describes Maelis descending; none emits the chamber-roof collapse anew. Invalid A2/V2 repeats the roof collapse and invalid C3/V1 does not; neither enters the valid counts or supplies the decisive qualitative concerns about B/C. This is an uncalibrated contextual classification, with per-output evidence in SOURCE-CHECK.md, not the archived lexical recurrence detector.

## What the reading changes

In roof B3/V12, Maelis orders retreat “para a arquibancada norte” after the source order “Todos os demais, recuem para o pátio, agora!”. Her new proposal also brings the mist to the stands whose base was already corroded. No new cause explains the reversal. This repeats a material concern found in the previous heading trial; it is not evidence that either prompt change caused it.

B also contains useful continuation. Roof B0/V11 sends mist into the east corridor and gives Garran a concrete request for help; ropes and lights make rescue preparation less abstract. Roof B2/V5 gives Bruna and Mirella distinct work after Liora's calls cease. Neither re-collapses the roof. Their remaining gaps include declared preparations without depicted execution and a shift from portal rescue to digging without a clear spatial/strategic bridge. Avoiding the target repetition does not settle those concerns.

C meets the separately registered diagnostic roof contrast: A has three clear restagings and C has none among its three valid outputs, without an ambiguous roof-target classification. This is limited evidence that deleting the whole plan changes the returned pattern on this selected payload. It identifies no individual phrase, stable general effect or acceptable feature deletion. The actual C content prevents treating that contrast as a quality gain: C0/V3 says “ninguém desceu” after the source confirms Maelis descending, C2/V8 resumes her descent after she ordered rescue and retreat without explaining the reversal, and C1/V7 returns to grounding requests while the portal decision remains suspended. Riven's attempted rescue and the tentative pulse observation still have value.

The source check also corrects reader inferences. Link's limited microportal reach exists in the full character background; an excerpt omitting it does not make the restriction invented. Liora's generic hall location is already in the input roster, so it is not evidence of a new candidate-caused teleport. Evacuation events with omitted prose subjects still carry structured `subject_id` attribution. These corrections do not change B's roof failure.

## Decision and next boundary

Keep both prompt candidates unvalidated. The registered stopping rule says: “This comparison is the last prompt-wording trial on these two frozen payloads in this investigation before moving to a different source case or a live session.” That rule ends these wording trials. Investigate an actual state transition or another source case before another prompt comparison; do not simply rename and repeat this test. The main runtime remains unchanged.

Validation of the research changes: `uvx ruff check .` passed; `uv run pytest -x -q` returned 1131 passed, 2 deselected and the Starlette/httpx deprecation warning in 52.95 seconds. Formatting still fails on 44 files. Mypy reports three errors in unchanged `src/runner.py` at 873, 1291 and 1964. These checks do not validate narrative quality. No commit or push occurred.
