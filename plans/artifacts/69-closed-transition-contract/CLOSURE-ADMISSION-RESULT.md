# Manually bound gate-closure admission: incomplete screen, admission withheld

The [frozen 11-case rule](CLOSURE-ADMISSION-PREREGISTRATION.md) required 88
HTTP-200, schema-valid, literal-support calls before semantic scoring. All 88
requests were dispatched once, with distinct provider response IDs, but only
**86 passed validation**. `t36_blue` extractor repetition 2 produced a readable
raw envelope but curl exited `-6` (`free(): invalid pointer`) and returned no
HTTP status. `t38_green` checker repetition 4 returned HTTP 200 and valid JSON
but supplied a paraphrase not present literally in the source. Neither call was
replaced. The registered technical gate failed, so the screen's formal status
is **incomplete**, with no aggregate semantic pass or reliability estimate.

The saved valid outputs still show two concrete faults in this candidate. On
archived T38 with **the green gate** as subject, one extractor returned `yes`
and another `ambiguous`, both citing the event `O portão azul se fecha com um
baque surdo`. The full event list says only that Link remains before the green
gate **already sealed**; it does not close in T38. On the separate weak-support
control, the source really does assert blue-gate closure, but the checker was
offered only `No salão, restam apenas Link, ainda diante do portão verde selado
...`. All four checker calls returned `entailed` by citing a **different**
blue-closure sentence found elsewhere in the full source. Thus the checker
ignored the registered offered-support condition. An isolated [content-only
reader](CLOSURE-ADMISSION-CONTENT-PACKET.txt) agreed that the green-gate
positive/ambiguous outputs lacked support and that all four weak-support
checker approvals used evidence outside the offered passage. The packet
contains the complete T38 events and each output without expected labels.

The accepted T37 time-skip closure also exposes a narrower support problem:
extractor repetitions 1 and 3 offered only a fragment saying `o portão se
fecha`, without any identifier for **which** gate. The full T37 event list
resolves that referent through `fresta do portão azul`, but the offered fragments
alone do not; the checker nevertheless returned `entailed` in both calls. An
isolated [support-only read](T37-SUPPORT-CONTENT-PACKET.txt) flagged this
missing identity. Its stricter judgment of the two longer T37 supports is not
adopted here: those passages mention the blue team and blue tunnel and permit
a contextual reading, even without repeating the gate's color.

Other local cases remain descriptive: T37 and T38 blue-gate positive assertions
were extracted and admitted in four of four repetitions each; the synthetic
ambiguous two-gate text was marked ambiguous four of four times. Those matches
do not establish a formal pass, and the identity and support-boundary errors
remain observed faults in this sample. The private
`closed`-state comparison and a proposal-repair-to-renderer test were not run;
there is still no approved model producer or runtime guard. The next candidate
must test whether the checker can respect the offered-support boundary while
retaining enough context to detect contradictions and resolve a local referent.
Whether a prompt or a different input boundary fixes this is unmeasured.
