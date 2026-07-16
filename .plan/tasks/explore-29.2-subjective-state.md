# Exploration — Task 29.2 Topology Spike 01: Identity Leak and Call Placement

**Status:** In progress (feeds the mandatory exploration gate of Task 29.2)
**Date:** 2026-07-15
**Method:** prototype prompts mutated from a *real* recorded production request, executed
against the configured provider (DeepSeek `deepseek-v4-flash`), no runtime code changed.
**Artifacts:** `plans/artifacts/sofia-alex-identity-leak/` (regression session) and
`plans/artifacts/explore-29.2-topology-spike/` (scripts + raw results, local-only).

## 1. Regression evidence (29.2 §11 item 2 — done)

Session `0aafaa67` (Casa do Tony, C1=Alex controlled, C2=Sofia, C3=Fernanda) is preserved
under `plans/artifacts/sofia-alex-identity-leak/session-0aafaa67/`. Sofia's `knowledge`
contains no mention of Alex, there was no introduction, yet her recorded turn-1 thought is
"Esse Alex chegou todo estilo". Her exact LLM request shows the canonical name entering
through two independent paths:

- `RECENT EVENTS`: `Turn 1 | TYPE=SPEECH | SPEAKER=Alex: ...` — history labels resolve
  through `speaker_label` (`src/models.py:176`, used at `src/agents/character.py:210`)
  regardless of what the viewer knows.
- `SCENE CONTEXT`: "Você ouviu **Alex** falar algo..." — `context_for_character` is free
  prose authored by the omniscient Narrator.

## 2. Canonical-name entry points into a Character prompt (inventory)

All five are render/selection surfaces; none require touching the transaction core:

1. `speaker_label` history labels (`src/agents/character.py:210`).
2. Narrator `context_for_character` free prose.
3. `_whisper_turn_note` confidant names (`src/agents/character.py:169`).
4. Compaction private notes (`src/agents/summarizer.py:160`, same `speaker_label`; plus
   the already-confirmed audience defect at `summarizer.py:154-159`).
5. `known_tokens` whitelists every character name universally
   (`src/confidentiality.py:130`), so output guards treat all names as public.

Characters never receive narration or other minds, so the identity problem is bounded to
these surfaces. That materially lowers the risk of 29.2's projection layer.

## 3. Experiments (25 + 20 provider calls, 2026-07-15)

Base request = Sofia's real turn-1 request from the regression session, byte-identical
except for the single controlled factor. "Leak" = `\balex\b` (case-insensitive) in the
generated speech or thought.

| Experiment | Variant | N | Result |
|---|---|---:|---|
| E0 control | original request verbatim | 13 | **7/13 leak** — e.g. speech "Oi, Alex! Tudo bem com você?" |
| E1a | SPEAKER label + context both viewer-relative | 13 | **0/13 leak**, responses natural, treats him as stranger ("nem sei quem é") |
| E1b | label kept, context redacted | 3 | 0/3 (small N; base-rate isolation inconclusive) |
| E1c | label redacted, context kept | 3 | 0/3 (same caveat) |
| E2a updater: no introduction | small structured "perspective updater" call; canonical roster visible as machine metadata | 3 | 3/3: `known_name=null`, reference "o homem na entrada com a camisa aberta", no name leak |
| E2b updater: audible self-intro | + event "Eu sou o Alex" | 3 | 3/3: `known_name="Alex"` |
| E2c updater: false name | + event "Me chamo Ricardo" (canonical still Alex) | 3 | 3/3: `known_name="Ricardo"` — belief ≠ truth held, canonical metadata resisted |
| E3a narrator + typed perception events (additive) | real narrator request + `perception_events` field | 2 | 2/2 valid events; avg 4.6s vs 3.6s baseline |
| E3b narrator + events replacing `context_for_character` | field removed from schema | 2 | 2/2 valid; avg 3.6s — **latency-neutral** |

Latency: character calls ~1.9s; updater calls ~1.7s (max_tokens 512).

## 4. Findings

1. **The leak is real, frequent, and structural.** 7/13 on the real request, in *audible
   speech* ("Oi, Alex!"), exactly the reported bug. The first 3 control samples showed 0
   leaks — single playtest runs cannot decide this class of defect; rates can.
2. **Context selection alone eliminates it.** 0/13 with viewer-relative projection and no
   new prompt rules. This confirms the 29.2 invariant "privacy comes from selection
   before the call, not instructions after exposure".
3. **A small identity/perspective resolver is highly reliable on the configured model.**
   9/9 including the adversarial false-name case, while seeing canonical metadata it must
   not surface. Output `reference` strings are directly usable as viewer-relative labels.
4. **Do not push viewer-knowledge onto the Narrator.** Even instructed "no unstated
   names", E3 event contents and `context_for_character` kept using canonical names.
   The Narrator reliably decides *what happened and who could perceive it*
   (`witness_ids` were sensible), but per-viewer identity rendering must live downstream.
   This validates the product intuition that led to 29.2 (do not transfer per-viewer
   cognitive tracking to the narrating call).
5. **Replacing `context_for_character` with typed events is latency-neutral** (E3b), and
   event content is machine data: canonical names inside it are acceptable *if and only
   if* a deterministic projection resolves them through the viewer's ledger before any
   Character prompt.

## 5. Candidate turn shape supported by this evidence

Consistent with 29.2 placement option 2 (between Narrator and Character), smallest set of
moving parts observed to work:

```mermaid
flowchart TD
    P[Player input] --> N[Narrator call<br/>narration + next_speaker +<br/>typed perception_events with witness_ids]
    N --> V{deterministic<br/>witness/audience validation}
    V --> U[perspective updater call(s)<br/>only for viewers with new<br/>identity-relevant events]
    U --> L[(per-character ledger:<br/>known_name / reference / provenance)]
    L --> R[deterministic projection:<br/>history labels + event rendering<br/>via viewer ledger]
    R --> C[Character call<br/>sees only viewer-safe brief]
```

- Narrator: keeps physical authority; emits events (E3b shape) instead of free
  viewer-facing prose.
- Updater (E2 shape): the only new semantic call; ~1.7s, skippable when a turn carries no
  identity-relevant event for a viewer.
- Projection: deterministic; replaces `speaker_label` output and event content names for
  subjects whose `known_name` is null. This also fixes entry points 3-5 (whisper note,
  compaction labels, `known_tokens` earned-knowledge model) as code-only changes.

## 6. What this spike does NOT yet show (open before freezing 29.2)

- `witness_ids` correctness under real spatial pressure (the 29.1 closed-partition case);
  only the easy same-room case was exercised.
- Multi-turn dynamics: ledger growth, `processed_through_turn` catch-up, stale state for
  silent witnesses, undo/fork snapshots.
- Cost/latency at 5+ characters and the fan-out/caching strategy (29.2 §7 experiments).
- Whether the updater should own more than identity (relationships, belief/status) in one
  call — E2 tested identity only.
- The E1 leak-path isolation (label vs context) needs N≥10 per arm if it ever matters;
  with full projection at 0/13 it likely does not.

## 7. Additional live evidence (2026-07-15, interactive session `ef6b5b90`)

The user replayed the party scenario interactively (controlling Alex). Archived at
`plans/artifacts/sofia-alex-identity-leak/session-ef6b5b90/`. Two findings matter
architecturally:

1. **The leak reproduces in live play.** Turn 3, Sofia with no introduction ever:
   speech "Ai, **Alex**... só uma criadora de conteúdo mesmo." Same two entry points
   (SPEAKER label + narrator context).
2. **Ambiguous priors resolve differently per call surface.** (Corrected after user
   clarification: the "knows nobody" line was authored in the sheet, not invented.)
   Fernanda's `knowledge` contains BOTH "ex-namorada de Alex" AND "Ainda não conhece
   ninguém além do Tony". The Narrator's `context_for_character` resolved that ambiguity
   one way ("Você não conhece bem nenhum deles", including Alex), while her own
   Character call resolved it the other way (thought: "Que estranho ver o Alex assim com
   outra..."). Two model calls re-interpreting the same raw contradictory prose produced
   divergent knowledge states in the same turn. This is direct evidence for the 29.2
   initializer: scenario priors must be compiled ONCE into a per-viewer ledger, and every
   surface must render from that single resolution instead of re-reading raw text.
3. **"What you remember: (none yet)" persists across every turn** (notes only exist
   after compaction), so no rapport accumulates inside a session — the continuous
   ledger updates of 29.2 absorb exactly this gap (and reconcile with Task 23).

## 8. Relationship to the program

- Task 29.1 should encode E0's *rate-based* measurement style: single-run pass/fail on
  stochastic leaks produces false confidence (0/3 then 7/10 here).
- Task 31 (structured-output robustness) remains a prerequisite for provider-backed
  benchmark runs; all 45 exploration calls here used client `retries=2` and lost none.
