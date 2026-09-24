# Blue-gate action-only screen: local candidate stopped

The [pre-registered](BLUE-GATE-ACTION-PREREGISTRATION.md) action-only smoke test **failed its semantic gate**. All sixteen frozen curl calls returned HTTP 200, schema-valid JSON, literal nonempty quotes from their supplied event text, and distinct provider response IDs. No call was replaced. The manifest and run directory preserve source/script/preregistration hashes, requests, envelopes and individual grades. These are four selected turns in **one session**, sampled four times each, not a reliability estimate.

| Turn | Expected `closing_action` | Returned |
| --- | --- | --- |
| T36 | `false` | `false` three times, `true` once |
| T37 | `true` | `true` four times |
| T38 | `true` | `true` four times |
| T39 | `false` | `false` four times |

The T36 `true` response cited `Garran grita que restam apenas cinco segundos para o portão azul se fechar de vez.` That is a warning of **future** closure, not an assertion that the gate finished closing in the beat; T36's other gate event narrows the usable gap. The same warning was also cited by a T36 `false` response. The verdict/quote pair is unsupported by the cited text; it does not diagnose whether the model misread tense, anchored on a keyword, or mishandled other events. A separate text-only reader of the [T36 event/output packet](T36-ACTION-OUTPUT-CONTENT-PACKET.txt) agreed that the gap remained passable and the `true` response lacks source support. T37's quotes point to the accepted time-skip closure; T38's to the second closure proposed in `perception_events`; T39's to an observation of already sealed gates. I read every quote against the full supplied event list; none of the other fifteen verdicts contradicts those four local source labels. The quote check alone would not prove the false cases, which is why the full-event read matters.

The technical prerequisite passed, so this is a **semantic failure** under the unanimous four-per-turn rule. Separating action extraction from deterministic state comparison made T38's proposed action visible in this local run, but the unsupported T36 positive stops this exact shape. T37/T38 use nearly identical closure wording, so even a clean pass would have been only a lexical smoke test pending different wording and other objects. No producer, pre-render repair or runtime guard is adopted. The earlier combined transition screen failed for different local labels; neither result establishes that action-only extraction is generally better or worse. A next source-grounded contrast should vary warning/completion, target identity and wording to test which boundary fails before changing the prompt or integrating a model producer.
