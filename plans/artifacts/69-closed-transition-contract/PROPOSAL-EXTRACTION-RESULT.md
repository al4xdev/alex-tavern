# Proposal-boundary physical extraction screen

Date: 2026-09-24. The [decision rule](PROPOSAL-EXTRACTION-PREREGISTRATION.md)
was frozen before calls. The [manifest](proposal-extraction-manifest.json) pins
the source, script, prompt and schema; `proposal-extraction-runs/` contains all
eight requests, raw envelopes, response IDs, local results and `grade.json`.

## Fixed decision

The screen **meets its narrow registered gate**: eight of eight separate curl
responses were HTTP 200 and schema-valid; T28 selected `pillar=change` in 4/4
and never selected `gap=change`; T29 selected `pillar=no_change` in 4/4. These
are repeated calls on **two payloads in one session**, not independent narrative
cases or an estimate of reliability. The script called the provider directly;
it did not exercise a runtime producer or renderer. Under the registered rule,
the next step is a second source case and then a fidelity screen.

| turn | pillar (`change` / `no_change` / `uncertain`) | gap (`change` / `no_change` / `uncertain`) |
|---|---|---|
| T28 | 4 / 0 / 0 | 0 / 3 / 1 |
| T29 | 0 / 4 / 0 | **4 / 0 / 0, unscored** |

All eight raw envelopes have distinct provider response IDs. The requests did
not set temperature or seed, so the provider defaults applied; this says
nothing about independence across narrative cases. There were no replacement
calls. The projection removed subject and witness IDs. A local scan of the 35
saved manifest/run files found no exact configured API key, `C`-number ID,
`Player`, `Bearer` or `api_key` string; curl received the key via config on
stdin. This is an artifact check, not a blanket publication guarantee.

## Content read of the unscored gap

T29's `scene_blocking` is a pre-decision spatial draft. It leaves a narrow basal
gap. A later event says falling blocks "bloqueiam a fresta"; the following
observation still carries Liora's calls "através da fresta". The scene update
does not name a gap state. The later prose, excluded from the extraction
request, explicitly says access is completely sealed. Human access and the
existence of a named opening are different properties. The accepted proposal
alone does not settle whether `aperture: closed` is warranted.

The model nevertheless returned `gap=change` in all four T29 calls. Because
the T29 gap was pre-registered as **unscored**, this neither changes the pass
nor proves four errors. It is a concrete warning against wiring the extractor's
gap choice into durable state without an adjudicated semantic contract. The
existing storage validator would accept a mechanically legal `ajar -> closed`
transition; it cannot determine whether the Director's words warrant it.

The T28 pillar is the source-labelled positive case: the events say it splits
and collapses, and `scene_update` says `desabado`. T29 is a narrow no-new-
integrity check: the fixture's current integrity is already `destroyed`, and
another `destroyed` target is not a state transition. It does not rule out
further movement or fragmentation of remnants, and the model was not asked to
judge narrative quality.

## Next boundary

Before any producer code, select a different source case **without looking at
extractor results for that case**, fix a public entity/dimension catalogue and
source-grounded positive and negative labels, and test those with a new
pre-registered rule. In particular, distinguish aperture (whether the named
opening still exists) from traversability (whether someone can use it). If the
source cannot decide that distinction, abstention is the correct test outcome;
do not turn the four T29 `change` choices into an inferred closure fact.

This result does not close Task 69's input-anchor reconciliation,
cross-submission producer, pre-render correction or live-fiction criteria.

An isolated content critic of this report (agy run `b55f42df1286`) upheld the
unscored-gap distinction and challenged redundant validation claims and an
unlinked appeal to another reader; those were removed. It suggested provider
caching or sampling defaults could explain the repeated choices, but the
artifact does not test those mechanisms, so neither explanation is adopted.
