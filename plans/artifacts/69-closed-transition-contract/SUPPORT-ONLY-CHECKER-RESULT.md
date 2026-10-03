# Support-only checker candidate: incomplete and not a one-variable ablation

The [pre-registered seven-case screen](SUPPORT-ONLY-CHECKER-PREREGISTRATION.md)
promised to change **only** the checker's visible context. Source review after
execution found a protocol deviation: the new request also changed the system
instruction and the claim wording. It is therefore **not** an isolated test of
context removal, and no difference from the prior pilot can be attributed to
that variable. This candidate supplied only frozen offered passages. All 28
direct curl calls were dispatched once with
distinct provider IDs; **27/28** passed HTTP, schema and literal-support
validation. The remaining `wrong_target` response echoed the JSON schema
rather than supplying `verdict` and `support`. It was not replaced. The formal
technical gate failed, so this run has **no aggregate semantic pass**.

The valid outputs nevertheless expose a specific tradeoff. Both T37 generic
`o portão se fecha` support fragments and the static green-gate weak quote were
rejected in four of four calls each, as intended. But the archived T38 sentence
`O portão azul se fecha com um baque surdo, isolando completamente o túnel da
equipe azul do salão` also received `insufficient` in **four of four** calls,
despite naming the target, asserting closure and stating that the tunnel is
completely isolated. The synthetic `O portão azul se fechou de vez com um
baque` was accepted in four of four. An isolated [content-only read](SUPPORT-ONLY-CONTENT-PACKET.txt)
judged both T38 and the synthetic sentence to assert completed closure, and
the four T38 `insufficient` outputs contrary to the supplied text. The
present-versus-past wording is an observed difference, **not** an established
cause of the model behaviour.

In this candidate, weak support was rejected and an explicit positive was also
missed. The protocol deviation prevents a causal explanation of either change
relative to the earlier full-source checker. This support-only checker is not
admitted. No new extractor, private state comparison, proposal
repair or renderer integration followed. The next isolated question is whether
a **one-variable**, frozen comparison can distinguish the effects of available
source context from instruction wording. The present-versus-past difference
is another hypothesis, not yet isolated. Both require real-payload replay before
any runtime prompt is changed.
