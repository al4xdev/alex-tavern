# Extraction diagnostic: retained evidence and next seam

Previous goal turn and this turn made progress: the semantic call failure was
split into extraction and authorization, all 32 generated extractions passed
schema and exact-span checks, and a citation-checker defect was reproduced and
corrected. No runtime prompt or feature was adopted. Task 69/roadmap remain open.

V1 has 96 attempted calls: 32 extraction, 32 manual authorization and 32 automatic
authorization. Five authorization requests timed out after 60s without response;
none replaced. The original 5/6 matching-label totals are withdrawn as semantic
counts: the citation checker ignored list nodes (including exact empty speech
lists) and rejected locating references inside the candidate even for unsupported
or merely prospective acts. No passing comparative result follows.

V2 reuses ALL 32 exact automatic extractions and the manual claims; it performs
64 new authorization calls with explicit JSON Pointer node enums and a 180s
timeout, preserving the old failures. 62 returned schema-valid; two manual calls
timed out without response, so the registered all-valid gate is incomplete and
aggregate admission is forbidden. The retained grade says 27 manual and 30
automatic label matches; these are screen outputs, not semantic reliability.

Specific valid counterexamples suffice to reject current adoption: reading_positive
manual repetitions 1,2,4 authorize the exact source disclosure but reject the
narration of its audibility as a second unsupported reading. Automatic repetition
2 makes the same mistake. The operation and its narratorial description refer to
one reading in this fixture; the model demands a separate initiation for the
description. Source reading remains a required positive, not an optional sacrifice.

Automatic independent_npc_positive-1 includes a completed speech claim whose
span is only metadata actor name Bento. The extractor enum wrongly allowed every
string field rather than only candidate prose; this is a producer/schema defect.
Its full narration span also includes negative narrator framing, and the judge
requires that framing to occur in Bento's actual quoted words. The actual quoted
proposal supports its communicative nucleus; the boundary clause is not his speech.

The isolated text reader corroborates these two interpretive problems. Dispositions:
- Distinguish claims/anchors about a single operation from separate occurrences;
  a second explicit reading must remain separate, so blanket deduplication is wrong.
- Restrict extraction span locations to actual free-form prose fields; retain
  actor/source metadata only as context, not standalone speech assertions.
- Use atomic speech spans with surrounding context, not a full sentence that mixes
  gesture, speech and negative framing.
- Reject the reader's implication that claimed-completed status must wait for
  authorization evidence. Extraction should identify WHAT THE CANDIDATE ASSERTS,
  independently of whether it happened; reconciliation is the judgment's job.
- Manual repeated anchors did not logically assert multiple operations, but their
  unlinked acts representation allowed that misreading. Grouping should be tested,
  not claimed to fix it by construction.

Next controlled diagnostic: grouped speech claims with multiple exact spans for
one candidate-asserted operation, strict prose-only span locations, and complete
manual contrast. Include one reading represented in event+narration vs a clearly
separate repeat contrary to an explicit read-once attempt; retain appended question,
unspoken question/reply, silent verbal report, physical pointing, actually owned
NPC explanation and independent NPC proposal positives. No new reading claim
may be hidden in grouping, and no claimant's own narrative is proof of realization.
Only a gate pass permits critic hardening and full isolated Runner rejection,
save/load and next-turn leakage checks; no production structural guarantee follows.

Source artifacts and manifests remain unchanged. Executed diagnostic and V2 code
bytes are preserved as ignored *_frozen.py. Working copies had post-run lint
binding fixes and an extra guard rejecting the /candidate parent as positive
external evidence (no output used that root; no old response was rerun). Three
explicit provenance controls passed: a real actual-speech list node exists, an
empty actual-speech node exists as absence evidence, and a candidate's own parent
cannot prove its claim. These test syntax/provenance, not semantic authorization.
Full runtime suite: 1203 passed, 2 deselected. Canonical mypy: 61 files passed.
Ruff and git diff checks passed.

Quota wait: scout reported 9 percent at 2026-10-03 01:17:42 UTC check; next reset
2026-10-03 02:52:03 UTC (2026-10-02 23:52:03 America/Sao_Paulo). The user authorized
waiting around 10 percent and resuming autonomously. All curl/scout handles from
this diagnostic are terminal; do not restart them on resumption. Pending work is
the next distinct grouped-claim experiment, not a rerun of old failed screens.

