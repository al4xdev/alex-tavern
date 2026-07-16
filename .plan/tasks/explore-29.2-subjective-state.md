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

## 8. Live evidence round 2 (2026-07-16, session `091b11c6`) and expanded mandate

Archived at `plans/artifacts/session-091b11c6-live-findings/`. Items that bear on the
29.2 architecture (prose-level items routed to Task 26; force-speaker to Task 28):

- **Knowledge leak confirmed at scale**: "do nada todos sabiam de um fato que só poucos
  personagens sabiam" — the audience/whisper guards protect *whispered* records, but
  ordinary knowledge still propagates through narration/context with no boundary. This
  is the exact gap the perspective ledger closes.
- **Internal ID `C6` leaked into reader-visible prose** — projection must strip IDs, not
  only unknown names.
- **Narrator passivity + role violations**: the Narrator neither generates events on
  skip turns nor reliably stays out of character speech. The user's assessment: the
  Narrator is the weakest link. **Expanded mandate from the user**: the blind-narrator
  *concept* stays, but the architecture around it may be reworked freely ("é tudo MVP
  ainda"), and the explicit direction is to SHRINK the Narrator's responsibilities and
  delegate more ("devemos diminuir as funções dele e delegar mais", 2026-07-16). Today
  one call owns prose + routing + per-viewer context + scene deltas + moods + event
  generation; the exploration should treat unbundling it (Decision/Prose split of §2.5,
  perception events, character action proposals) as the primary hypothesis rather than a
  fallback.
- **Product direction, user leaning yes (2026-07-16)**: give Characters the capacity to
  act physically, decentralizing the Narrator (today action belongs exclusively to it).
  Rationale: character calls are the cheapest in the pipeline and cache-dominated, so the
  marginal cost is low, while the Narrator is the measured weakest link. If adopted,
  Character output becomes {speech, thought, action-proposal} with deterministic
  validation and Narrator/Decision confirmation of outcomes ("an action is an attempt
  until confirmed" already exists as a rule). This interacts directly with the
  Decision-layer question and the perception-event contract; design it inside the 29.2
  exploration, not as an isolated patch.
- **Response budgets**: 24k narrator / 12k character measurably improved quality;
  defaults raised. Cost evidence from the session: 1.80M tokens total, 1.49M input
  cache-hit vs 0.28M miss, 38k output — provider-native prefix caching absorbs most of
  the cost, supporting 29.2's cache-first prompt shaping (§7 of the 29.2 doc).

## 9. User architecture hypothesis (2026-07-16): Director/Resolver split + bounded autonomous loop

Recorded verbatim in spirit; the user labels it "só teoria minha" — treat as the primary
candidate to test in the 29.2 exploration, not a decision.

**Diagnosis** (matches all measured evidence): today ONE Narrator call owns event
selection, routing, NPC action invention, consequence resolution, world updates, prose,
per-viewer private context, and next-speaker choice — which explains why it is the
weakest link.

**Proposed decomposition:**

```text
Character  -> speech + thought + action_intent   (intent, never outcome)
Resolver   -> validates intent, adjudicates real consequences (single physical authority)
Blind Prose Narrator -> renders ONLY confirmed public facts into prose
```

A character may return "Avançar com a lança e bloquear a passagem" as intent; it may
never assert "atravessa o coração do troll e o mata" — the kill belongs to the Resolver.
This formalizes the existing latent rule "an action is an attempt until narration
confirms it".

**Bounded autonomous loop** (attacks the passivity findings directly): Director picks an
event/next agent → Character produces speech/thought/intent → Resolver adjudicates →
blind renderer narrates → repeat until a stop condition: the player is addressed or
reacts, a strategic choice appears, the player is in danger, a dramatic beat ends, an
autonomous-action budget is hit, or the player interrupts/forces someone.

**Leak posture**: the prose renderer receives only public physical outcomes — no
thoughts, no full sheets, no internal IDs — so the C6-style and impossible-knowledge
leak classes are removed by construction (selection-before-call, the principle already
proven by the E1a projection experiment at 0/13).

**Cost argument**: session evidence shows cache-hit-dominated cost (1.49M hit / 0.28M
miss) and cheap output tokens; more, smaller calls with stable prefixes are affordable.

**Assessment (Claude, honest):** strong and consistent with every measurement; the two
real risks are (1) latency per visible beat (3 sequential calls ≈ 6-8s, multiplied by
the autonomous loop — needs progressive rendering or beat batching, must be measured in
the exploration), and (2) the Resolver quietly re-accumulating jobs until it becomes a
second overloaded narrator — its contract must be strictly "typed intent → typed outcome
+ typed perception events", never prose, viewer context, or moods. The autonomous loop
also changes the product's turn/undo/transaction model (what does undo mean across an
autonomous burst?) and should be staged as its own task on top of the split, not bundled
into 29.2's first delivery. E3 already gives partial supporting evidence: the narrator
emits valid typed events at zero latency cost when `context_for_character` is removed.

## 10. Idea board (2026-07-16): unified architecture map

The user asked to organize the accumulated hypotheses. One coherent map, by layer:

| Layer | Question it answers | Ideas on the table | Status/evidence |
|---|---|---|---|
| **State** | who knows/believes what | perspective ledger; initializer compiling priors + relationship map in act 1; lazy batched revision | E2 9/9; Fernanda ambiguous-priors case; 29.2 core |
| **Decision** | what actually happens | Director (event/routing) on demand; Resolver adjudicating `action_intent`; characters gain intent output | user hypothesis §9; supported by all live findings |
| **Rendering** | how it reads | blind prose renderer receiving only confirmed public facts; deterministic viewer-safe projection | E1a 0/13; E3b latency-neutral |
| **Drive** | why anything happens | pre-generated roteiro (story direction) + drift-triggered re-planning; escalating-probability auto-suggest injecting randomness | user tested suggest manually: "muda tudo completamente" |
| **Infra** | does it run reliably | unified retry (done, 31); raised budgets (done); 29.1/29.3 benchmark as the measuring stick | 31 closed; 29.1 in construction |

### Drive layer refinement (user, 2026-07-16)

- The **roteiro** is generated before the first word (same move as pre-initializing
  character variables: compile once, consume many turns). The Narrator/Director requests
  a NEW roteiro only when the story drifts too far — lazy re-planning, not per-turn.
- Ledger revision is co-scheduled with specific narrator calls (accepted latency spikes
  at chosen moments instead of every turn).
- The randomness "picada": reuse the EXISTING suggest mechanism, fired automatically by
  an algorithmic scheduler — each turn without an event raises the firing probability
  (hazard function), reset on fire; queued so it never collides with a player-initiated
  suggest.

### Honest caveats recorded with the ideas

1. **Drift detection must be algorithmic, not narrator self-assessment.** Asking the
   overloaded/passive agent to decide when it needs help reproduces the passivity bug at
   the meta level. Code owns scheduling (beat counters, turns-since-plan, roteiro
   checklist coverage, the hazard function); models own semantics. This matches the
   kernel philosophy already in README.
2. **Roteiro granularity**: a full one-shot script will be invalidated quickly by an
   unpredictable human co-author. Hierarchical shape survives contact: stable premise +
   act skeleton, rolling next-beat detail, replan only the rolling part. Also
   cache-friendly (stable prefix) and spoiler-safe (roteiro goes ONLY to Director-side
   calls, never to character prompts or the prose renderer).
3. **Ledger staleness window**: batching semantic revisions is right for cost, but
   identity events (a name learned mid-scene) must land before the viewer's next reply
   (E2 covers this case). Hybrid: cheap deterministic appends per turn, full semantic
   revision batched at the chosen moments.
4. **The auto-suggest scheduler is shippable now**, independent of the 29.2 core: the
   suggest pipeline exists and was validated manually. Smallest useful drive win.

## 11. Relationship to the program

- Task 29.1 should encode E0's *rate-based* measurement style: single-run pass/fail on
  stochastic leaks produces false confidence (0/3 then 7/10 here).
- Task 31 (structured-output robustness) remains a prerequisite for provider-backed
  benchmark runs; all 45 exploration calls here used client `retries=2` and lost none.
