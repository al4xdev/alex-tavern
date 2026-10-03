# Identity/aspect screen: incomplete, with source-visible binding errors

The [frozen nine-packet protocol](IDENTITY-ASPECT-PREREGISTRATION.md) sent
**36** direct DeepSeek curl calls, four per packet. All returned HTTP 200 with
distinct provider IDs and schema-valid JSON. **33/36** met the complete
technical contract. Three `t38_static_green` calls said `identity=other` while
returning no closing-action quote; the registered validator rejected that
internally inconsistent combination. The fourth correctly said `absent`.
No call was replaced. Under the registered rule this screen is **incomplete**:
there is no aggregate semantic pass and this reader is not admitted.

Individual responses still expose content errors. For bare archived T37,
`o portão se fecha com um baque surdo`, the four outputs correctly recognized
a completed closing action but marked the **blue** target `named` once and
`resolved` three times. The offered text never says `azul` and has no
antecedent. Literal quotes such as `o portão` did not establish identity. In
the synthetic two-gate sentence, three outputs called `o portão` resolved to
the blue target, although blue and green are parallel competing antecedents;
one abstained as ambiguous. The static green-gate passage produced the three
invalid `other` responses noted above despite containing only an already
sealed gate and no new closure. These are specific response readings, not a
model error-rate estimate.

The archived T37 **long-context label is contested by content readers**. Two
earlier independent readers treated the offered blue-gate mention plus
time-skip summary as ambiguous because the summary says the closure seals all
groups and later mentions plural gates. A later independent reader, shown the
same passage and model judgments, read its singular closing gate as a clear
anaphor for the blue gate. The frozen negative label remains the experiment's
decision rule, and all four model calls missed it (`named` three times,
`resolved` once). That does **not** establish that all four made a literary
identity error. The three `named` outputs do fail the prompt's narrower
definition: the closing clause itself says only `o portão`; the one `resolved`
output accords with the later reader. This disagreement blocks treating T37
long-context outcomes as calibrated ground truth.

Other selected controls show the fields can sometimes separate aspect from
identity: explicit T38, future warning, natural single-gate anaphora and
interrupted closure each matched both frozen fields 4/4. The wrong-target
blue-closure passage produced `other` 4/4 and one `completed=false` response
despite depicting a completed closure; this single response does not diagnose
why the fields diverged. The blind reader independently found the bare,
two-gate, static and wrong-target mismatches; for T37 long context it supplied
the competing interpretation above.

The admissible conclusion is narrow: a quote-valid identity field can still
bind an ungrounded or competing `o portão` to the target, and this contract
failed its technical prerequisite. No producer, durable-state comparison,
proposal rewrite or renderer repair follows from it. A future approach needs
an explicit rule for ungrounded versus competing referents and must preserve
the content-reader disagreement on T37; repeating this prompt against the
same nine cases would only tune to the screen.
