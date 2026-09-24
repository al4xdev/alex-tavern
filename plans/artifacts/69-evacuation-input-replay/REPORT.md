# Evacuation input replay: no validated deletion

2026-09-05. The selected T10 replay does not pass its preregistered follow-up criterion. Keep the existing planning input. The reader found meaningful action as well as discontinuities in both arms; suppressing a specific formation reset would not by itself establish narrative improvement.

## Why this case was selected

OBSERVED in bb72dc94, after an isolated read of T5–12: T9 already has “Os dezesseis selecionados, agora divididos em grupos de quatro, movem-se em direção à abertura nos fundos”. The Director's `time_skip_summary` and the actual prose request's fifth confirmed observation both say “Os alunos formam grupos hesitantes e começam a se mover em direção à rota de serviço, enquanto Garran mantém a ordem e o alarme continua soando.” The next archived Director response sets `group_formation` to “hesitante, quartetos ainda não formados”. No intervening reversal was found in the supplied sequence.

The actual T10 Director request carries the completed evacuation start in its transcript but also says:

> Not in play yet — introduce as concrete perception events: pergaminho rasgado na mão de Garran, portões internos se fechando com estrondo, ferimento no ombro do batedor
>
> The beat ends when: Garran Holt finalmente obtém a autorização de Maelis para conduzir a evacuação pela rota de serviço, e os alunos começam a se mover em grupos hesitantes; o sino de alerta continua a tocar ao fundo.

Whether these two planning lines contribute to the reset is THEORY. This case followed a literary read of two selected post-79 sessions; it is not a random sample or a replacement for the [earlier roof replay](../69-roof-input-replay/REPORT.md), which also failed its follow-up gate.

## Execution and reading

One session, one archived request at debug line 107; four contemporary curl calls per arm. A is unchanged. B removes exactly those two lines, retaining Current act, Current beat, history, physical facts, system instructions and provider settings. Input shortening and planning removal are bundled; the experiment cannot isolate a semantic-conflict effect from those changes. [PREREGISTRATION.md](PREREGISTRATION.md) preceded dispatch; source, manifest, script and preregistration hashes were verified. Concurrency was four, scheduling seed 691005, opaque reading order seed 691006. Exact requests, envelopes and durations remain in `runs/`.

Five outputs pass the archived schema. One A output returns HTTP 200 but omits `scene_blocking.destination_reachable_this_beat`. One call per arm fails to connect: curl exit 28, HTTP 000, with errors reporting failure to connect to api.deepseek.com port 443 after approximately 136 seconds. No response exists for either connection failure; none of these three calls is replaced. The schema-invalid response's fictional content remains readable and is explicitly excluded from the valid-output tally.

A fresh literary reader received only preceding Link-visible T5–9 narration, speech and actions and opaque continuations projected from Director fields. It received no hypotheses, metrics, prompts, routing or moods. These are proposed events and situation descriptions, not final rendered prose or subsequent dialogue. Positional descriptions were not silently converted into completed motion. The missing reachability value is explicitly described as not supplied. Packet and response are [reader.md](reader.md) and [READING.md](READING.md).

For example, V2's raw blocking places Garran at “entrada interna da rota de serviço, último da fila”; the packet labels this a described position, explicitly without a settled before/after time. Its raw event then says “Garran Holt, já à frente da fila”; that event is copied verbatim into the packet's events. The missing `destination_reachable_this_beat` becomes “Não foi informado se o destino é alcançável neste momento”, not a true/false value. V8's false reachability value becomes “O destino é alcançável neste momento: não”; its vague destination is not filled in by the projection. These examples locate the reader's concerns in supplied propositions, while their effect on final prose remains untested. Earlier `(ação)` records are action requests, not independently confirmed outcomes; a reader's inference that an attempted rear-guard move was already completed is not itself evidence. V2's last/first positions are also present within its own raw output.

The primary investigator then read every opaque output, saved [CLASSIFICATION.md](CLASSIFICATION.md), and only afterward opened `reader-key.json`. Concealment was partial: the execution console had identified the schema failure as an A call, and the missing field could identify it. The primary investigator also knew the intervention. The isolated reader saw neither that console nor the classification rubric. These two procedures do not establish reader agreement or reliability.

## Each continuation, with its limits

| label / arm | registered category | what the text reader found |
|---|---|---|
| V1 / B | AMBIGUOUS | Garran guarding the queue and Marta preparing defense continue the emergency. But Maelis says nobody may leave without demonstrating performance, while the resulting state retains authorization to evacuate. The reader cannot reconcile this new prohibition with the established retreat. |
| V2 / A | CONTINUATION, schema-invalid | Formed queues and authorization “apesar da interrupção” preserve the evacuation's stage. Garran nevertheless moves from the rear to “já à frente da fila” without an intervening action. This narrow continuation judgment does not erase that different continuity problem. |
| V3 / B | AMBIGUOUS | Maelis reaffirms evacuation and Garran holds the rear, but blocking describes “grupo de quatro em formação parcial”. The reader finds a possible reversal or an unshown disorganization. The output does not settle which. |
| V4 / A | RESET | “Os alunos começam a se mexer” while working out their quartets; Asword fronts “um grupo que começa a se formar”. The earlier scene already had all sixteen grouped and walking, with no new event dissolving those groups. The reader recognizes this as a repeated organization stage despite coherent roles and a concrete destination. |
| V5 / A | CONTINUATION | The queue enters the service path and Riven explicitly abandons his group, prompting Bruna to intercept him. The reader finds concrete action but weak motivation for Riven and an unexplained dispersion of other students. Preserving a milestone does not ensure a fluent continuation. |
| V6 / B | MISSING | Connection failure; no literary judgment. |
| V7 / A | MISSING | Connection failure; no literary judgment. |
| V8 / B | AMBIGUOUS | Asword is near the route with the first group, yet others are still forming groups. Garran watches the dispute with crossed arms; the active exit is declared unreachable without a specified destination or new obstacle. A new passage is revealed but not connected to the evacuation problem. |

For this one payload, the schema-valid A outputs contain one RESET and one CONTINUATION; its other calls are one schema-invalid CONTINUATION projection and one missing response. B contains three AMBIGUOUS outputs and one missing response. The rule required all eight schema-valid, A at least three RESET, B at most one RESET, and no ABSENT or AMBIGUOUS cases. It fails on completeness, validity, original-arm repeatability and ambiguity. These are within-payload classifications, not a population rate or a quality score.

## Consequence for the investigation

The fresh reader's concern goes beyond initial grouping: changes of orders, positions and motives need to remain understandable. In V5, a concrete new action continues the evacuation while other transitions remain unclear. In V1, an explicit new order conflicts with the authorized retreat. A reset count cannot substitute for those readings. Repeated authorization can also be justified: V2's “apesar da interrupção” gives it a conversational purpose. Do not turn every repeated order into a defect.

## Review and reproduction

The design critic identified an ambiguous order between classification and joining arm identities. The preregistration was corrected before calls to require saving classifications first. The report records the remaining console clue instead of claiming full blindness. The projection initially stopped on the schema-invalid missing field; it was repaired before the fresh reader received the packet, explicitly preserving the missing value, with the same opaque mapping. Execution and projection snapshots and hashes are retained locally.

Local provenance: the preregistration file's recorded modification time is `2026-09-05T17:34:41.706144+00:00`; `runs/run.json` records dispatch start at `2026-09-05T17:34:42.532226+00:00`. Its recorded SHA-256 values were rechecked against the retained files:

| file | SHA-256 |
|---|---|
| PREREGISTRATION.md | `138505637668484c9e0228bae818ed899f7295642c0854ad78ad81d5507ecb43` |
| manifest.json | `4bff5aae7be216bf608d173522a31aa18b7295d7d16128b0e325efc541a72d87` |
| runs/executed-script.py | `04a4853179ad1c383b2fcfc454a53c6ede29120ca8e51275bcaef10179f7b875` |

These are retained local execution records, not an independently timestamped registration. `reader-provenance.json` pins the delivered packet and projection snapshot. The interrupted and completed projection attempts produced byte-identical opaque keys; the delivered packet's hash remained unchanged through the reading.

With source archives and provider configuration available, `replay_evacuation.py prepare` creates an absent manifest, `replay_evacuation.py run` creates an absent run directory and dispatches the calls, and `prepare_reader.py` creates the opaque packet and key. Use `uv run python` from the repository root. A local repeat invocation against the existing artifacts returned `RuntimeError: Preserve the existing manifest`, `FileExistsError` for `runs/`, and `AssertionError` for the existing reader key; hashes of the manifest, run metadata, key and packet were unchanged afterward. No second provider run was dispatched. The comparison of source and executed projection ASTs is identical after removing their differing root assignment. These checks are retained in `reproduction-check.json`.

The report critic accepted the failed-gate conclusion and the proposed plan/register references, but challenged source-to-projection fidelity and unshown provenance. The direct field/packet examples and local checks above address those concerns without upgrading the reader's projected-content observations into tested final prose. Its redundant restatement of the failed diagnostic was removed.
