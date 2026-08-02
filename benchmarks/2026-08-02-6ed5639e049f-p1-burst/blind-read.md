# Blind read of the twelve P1 transcripts

A clean-context reader was given the twelve transcripts under opaque names
(`T01`–`T12`), with no knowledge that cells existed, and asked to judge them as a
reader: does the same physical event happen twice, does the scene progress, how
does it read. It was told not to look outside that directory.

This is here because it outperformed the metrics. Twenty-five numbers, one pass
of reading — the reading won.

## It recovered the design without being told there was one

| group it formed, unprompted | what those runs actually were |
|---|---|
| "the only three where nothing ever bursts in" | **`null` ×3, exactly** |
| "worst" | `oldcode` r1, `oldcode` r2, **`base` r2** |
| "stuck at one threshold" | `drive` r1, `drive` r3, `oldcode` r3 |
| "disaster arrives and the party travels" | `base` r1, `base` r3, `drive` r2 |

Ranking, least to most repetitive, unmasked:

| # | run | | # | run |
|---|---|---|---|---|
| 1 | null-r2 | | 7 | drive-r3 |
| 2 | null-r3 | | 8 | drive-r1 |
| 3 | **base-r1** | | 9 | oldcode-r3 |
| 4 | **base-r3** | | 10 | oldcode-r2 |
| 5 | null-r1 | | 11 | oldcode-r1 |
| 6 | drive-r2 | | 12 | **base-r2** |

`oldcode` taking 9, 10 and 11 of 12 is independent confirmation of the fixes —
from a reader that did not know which engine it was reading.

## The finding that matters: the metrics missed the worst session

`base-r2` is ranked **worst of twelve**. Every metric scored it clean:
`RSR_prop` 1.7%, `ECHO_PERSIST` 0, `BOCC` 3, repeated injected event 1.

What the reader saw: the hidden chamber's ceiling ruptures at T33, T34, T35 and
T38. Bruna's bracelet cracks the pillar at T27, T28, T29, T30. Mirella announces
she is descending at T29, 30, 31, 33, 35, 36, 37, 38, 39 — and never descends.
Twelve turns of no net change.

**Verified: none of it is in `perception_events`.** The Director never proposed
the ceiling rupturing. The PROSE RENDERER invented it and re-invented it. That is
a different defect from everything fixed in this investigation, and the
instrument was blind to it *by design* — its own docstring says it measures "the
decision, not the prose, because the renderer paraphrases". That design choice is
exactly why it could not see the worst session in the battery.

Why the prose repetition guard did not fire, measured on T33 vs T34:

| comparison | value | threshold |
|---|---|---|
| whole text | 0.1349 | > 0.85 |
| best sentence pair | **0.7770** | > 0.80 |

Missed by 0.023. The guard is alive — it fired at T35 — but it compares
sentences, and one event re-described across a long, freshly-worded paragraph
does not present as a similar sentence. Same structural weakness as the speech
echo guard had, but **not the same fix**: there the wrapper hid identical text,
here the text genuinely differs.

## Two more real defects, invisible to every metric

Both verified against the archive, both rare (1 occurrence in ~480 turns), both
covered by an invariant the repo says it holds:

- **Internal character ids reaching prose.** `oldcode-r1` T39: *"C17 ordena que
  C20 permaneça com os estilhaços e que C18 a acompanhe"*. Only in the pre-fix
  cell, but n=1 — no claim that the current engine prevents it.
- **Narration flipping to English** with `language` pinned to Brazilian
  Portuguese. `null-r2`.

## A trade-off that was under-weighted

`null` — roteiro off — ranks 1st, 2nd and 5th: **least repetitive of all**. The
reader also calls those three the only ones where "nothing ever bursts in", and
"dull". `NSR` said the same thing numerically (2.87 vs 3.77) and it was read as
"the roteiro is better". The roteiro adds events *and* adds repetition; which
side of that trade is right is a product decision, not a metric.

## Other reader observations, not verified

Recorded as-is; they are worth checking but were not confirmed here.

- Character continuity: Nix referred to as "ela" throughout then "Ele se curva,
  as orelhas felinas eretas" (`oldcode-r2`); Mirella claiming Ysara's scent
  trait; Riven completing his evaluation then demanding his turn for 18 turns.
- Scene headers naming a location the action is not in ("Pátio" while everyone
  is inside the Salão dos Quatro Arcos).
- Endings: four runs stop mid-air on an order nobody obeys.

## Reproducing the blind read

Rename the transcripts to opaque labels, strip the session id from the first
line, keep the key outside the directory the reader can see, and ask for a
ranking plus groupings before any per-file detail. Do not tell it how many
configurations exist.
