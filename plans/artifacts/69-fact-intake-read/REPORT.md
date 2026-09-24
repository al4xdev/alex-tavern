# A suffix veto drops a supported door-lock fact in replay

2026-09-14. **OBSERVED channel loss:** in d5a2ccf0 T8, the accepted Director
response at debug line 92 describes smoke “de trás das portas trancadas” and
proposes `doors_state: trancadas`. The persisted last T8 snapshot has no such
key, and the next accepted Director request, T9 at line 108, also omits it
from Physical facts. It retains the door runes, smoke and other updates.
This is loss from that state channel, not proof that the model could no longer
find the event in history or that the omission caused later repetition.

The isolated [content read](CONTENT-VERDICT.md), case 5, distinguishes the
locked upper-wing steel doors from the earlier closed stone arches. It finds
the locking statement supported but notes that the generic key does not
identify every door precisely. The fix preserves what the Director proposed;
it does not resolve that referent ambiguity.

## Deterministic change and evidence

The intake rule previously accepted exact-key updates first, then rejected
every new key ending in `_action`, `_position`, `_stance`, `_state` or `_status`.
Its comment called these per-character transient facts. There is no required
suffix namespace in the free-form scene-fact contract; a `_state` suffix does
not distinguish a character's posture from a door's lock. The archived
predicate is in `intake-before.json`.

Only the suffix veto was removed. Exact updates, the separate similarity
predicate, secrecy cleanup and the existing 40-entry cap remain. The direct
tradeoff is wider admission: a character-scoped or redundant fact formerly
rejected solely by its suffix can now enter. The cap limits entries, not
semantic damage. No net narrative-quality benefit is claimed.

The regression using the recorded four-key T8 delta failed before the change
with `KeyError: doors_state`, then passed. The [boundary replay](replay_intake.py)
also runs the archived predicate and the changed predicate against the complete
recorded prior facts and delta. Its result differs by exactly one entry:
`doors_state: trancadas`. This isolates the suffix veto from the unchanged
similarity check. Saving and loading an isolated fresh GameState preserves the
result. This is a replay of the state boundary, not a new narrative session.

All 20 fact-hygiene tests pass, including the existing secrecy, coercion,
similarity and eviction cases. The full suite passes 1,141 tests, with two
deselected and one Starlette deprecation warning. Ruff check passes. Mypy
reports three type errors at runner.py lines 854, 1272 and 1945; the format
check flags 44 files. Thus the repository-wide checks are not all clean.
The preceding validation in `../69-state-delta-contract/REPORT.md` recorded
the corresponding failures at lines 873, 1291 and 1964: unpacking three values
from a two-item annotation, returning a three-item tuple under that annotation,
and assigning `str | BaseException` to `str`. No claim about identical sets of
formatting diagnostics follows merely from equal counts.

## What the broader read does and does not support

The fixed selection takes up to the first four accepted calls containing a
current-key-check refusal in each of three specified sources: fb62cc2f has
three selected calls, d5a2ccf0 four, and 8bd4d0f1 four. These 11 calls are a
diagnostic reading set, not an error-rate sample. Classification was by the
reader's interpretation of complete event and fact excerpts, not key similarity.

The reader found mixed cases. The secret-passage collapse in case 10 is also
recorded under `secret_passage` in that same delta, so refusing its other label
does not by itself lose the collapse. Case 9 contains a new green fissure
alongside repeated passage details. Case 8 describes debris clearing, but
whether it already permits safe passage remains uncertain. The alarm and
messenger state in case 4 also have semantic qualifications. These readings
do not validate blanket removal of all intake checks or automatic merging of
similar keys. The similarity predicate was left unchanged, not vindicated.

The proposal critic required checking the historical destination and isolating
the suffix's role. Those checks were performed, but the result critic rejected
joining them into proof of the complete historical causal chain: the archived
predicate is the pre-change checkout's rule, not a recovered executable from
that old session. The historical key absence is observed; the suffix veto is
sufficient to reproduce it in the controlled replay. This report does not rule
out every alternative historical cause or intermediate mutation.
The critic also warned that one false positive does not measure the net benefit of
removing all five suffixes. Removal is a scoped engineering decision to stop
using that spelling rule as an ownership test, not a measured optimum.
Task 69 remains open; no prompt was modified in this change.
