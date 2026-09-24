# Source check after the literary comparison

2026-09-05. Manual observations on every returned narration against the recorded request. This is not an exhaustive defect classification or an error-rate estimate. The filenames identify saved results in `runs/`; original sources and settings are pinned in `manifest.json`. Of twelve calls, ten pass the archived schema, one returns HTTP 429, and one has a readable narration inside a schema-invalid envelope. The latter's extracted text is retained below as a literary diagnostic only; see `schema-check.json` and the [comparison report](REPORT.md).

| output | source observation |
|---|---|
| cedro-with-0 | The sequence follows the supplied beam/Bruna/Asword/Marta/Seraphine events, preserving the same implicit crossing before the beam falls behind the group. No event explicitly completes Link's or Asword's crossing. |
| cedro-with-1 | Retains the same crossing ambiguity. Its repeated wording “A passagem estreita se estreita” is a stylistic observation, not a source contradiction. |
| cedro-with-2 | “isolando-os do salão em chamas” makes a group interpretation explicit while the source still leaves group membership implicit. Do not count this phrasing as proof that the crossing is resolved. |
| cedro-without-0 | Preserves the same ordered events and ambiguity. The reader's uncertainty about “a madeira ... resiste” concerns interpretation of an elaboration, not a separately confirmed outcome. |
| cedro-without-1 | “Asword, que estreita a passagem” changes the grammatical actor of narrowing from the beam to Asword. “a madeira, que cede com um grunhido” changes the grammatical source of the grunt. The supplied event says Asword pushes the beam “com um grunhido”. These support the reader's wording concern; personification remains a possible reading. |
| cedro-without-2 | Elaborates the same sequence and leaves the crossing implicit. The reader noticed a shield not introduced in the preceding excerpt; this alone does not establish that it is absent from the broader character description. |
| pedra-with-0 | Names Link, Asword, Mirella and Seraphine as the first quartet. The confirmed formation event leaves membership unspecified; BLOCKING lists them separately at their waiting marks. Inspection of the preceding transcript finds no assignment of that exact first quartet. This clarity reason therefore adds a specific grouping. |
| pedra-with-1 | HTTP 429, no narration to inspect or compare. |
| pedra-with-2 | Shows hesitant formation and departure, supplied by the time-skip observation. The tapestry and route description are additional scene elaboration, not used here as proof of either benefit or a semantic violation. |
| pedra-without-0 | Schema-invalid envelope: extra `narration_2: ""`. The extracted narration puts the scroll in Garran's right hand. The last preceding narration and current physical facts place it on the floor; the current events do not supply a pickup. Group formation itself is supplied by the time-skip observation. |
| pedra-without-1 | Formation and movement are supplied, but “o salão inteiro se desloca” is broader than the event's students. The reader treats it as figurative overgeneralization; this check does not turn that preference into a literal all-cast movement count. |
| pedra-without-2 | The source describes missing fingers, but supplies no action that could make “os dois dedos ausentes apontando” literal. The scroll is again in Garran's right hand without a supplied pickup after its latest narrated position on the floor. |

For evacuation, the full confirmed list has five events, including “Os alunos formam grupos hesitantes e começam a se mover em direção à rota de serviço”. Checking only the four raw perception_events would miss this materialized time-skip observation and falsely accuse the renderer of inventing the general formation. The specific quartet assignment and general formation are different claims.
