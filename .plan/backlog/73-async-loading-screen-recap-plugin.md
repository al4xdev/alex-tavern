# Task 73 — Diário de Bordo, and the loading experience that buys us latency

> **Status:** backlog. **Rewritten 2026-08-05** with the owner's framing; the
> first draft was a rough sketch and got the point of the feature backwards.
>
> The sketch presented the loading screen as a way to make waiting less annoying.
> That is not what it is for. It is the thing that **buys the right to spend
> latency on narrative quality** — see the stance below, which is the whole
> reason this task exists and the part that must not be lost in a refactor.

## 1. The stance this implements

> *"Latência não é problema. Se demorar 10 minutos e chegarmos em boa qualidade,
> é uma questão de tempo — os modelos melhoram a cada trimestre e isso está a
> nosso favor."*

Latency is the **cheap currency** of this project and narrative quality is the
expensive one. Time spent engineering the engine to be fast is invested in an
asset that depreciates every quarter on its own; time spent on the fiction does
not depreciate at all. So the engine is allowed to be slow if slowness buys
quality — more agent calls, real routing, per-viewer projection, validation that
actually validates.

That stance has a UX bill, and this task is how it gets paid: the player is given
something worth looking at while the world is computed. It is **not** a
workaround for a temporary constraint, which is why it survives the constraint
going away.

The same reasoning decided task 65 one level down (accepting +1 character call
per turn to keep the role boundary). This is the general form of it, and it now
lives in `AGENTS.md` §2 as a standing budget rule rather than only here.

## 2. Two features with opposite lifespans — split them

**73a — Diário de Bordo (the journal).** A product feature whose value has no
relation to latency at all. A readable, permanent log of the journey is worth
having whether a turn takes eight seconds or eighty milliseconds. It is the half
that survives any future, and it is the one to build first — the loading
experience is a *consumer* of it, not the other way round.

- structured `journal.json` in plugin storage
  (`.data/plugins/<plugin-id>/storage/`);
- compiles committed public history into readable entries, character notes and
  discovered world facts;
- reachable from the UI menu at any time, not only while waiting.

**73b — The loading experience.** Implements the stance. Its value is
proportional to the wait, and if latency ever collapses it is deleted and the
journal stays. That retreat is cheap **because it is presentation, never data** —
keep it that way. No invariant, no persisted shape and no contract may come to
depend on it.

- 8-bit animated scenes, cards with world lore and (conditionally, see §5) recaps;
- the sprite library is the expensive part and the part with **zero
  architectural value**. Ship with 3–5 animations and grow it only if the wait
  actually feels repetitive: the variety a player perceives comes from the
  **cards**, which change on their own because the session changes.

## 3. ⚠ The product question that has to be answered before 73b is designed

**8–20 seconds and 60 seconds are not the same product.**

Today's turn is roughly 8–20s (character calls run at a 2,716 ms median and a
turn makes several). A design that budgets up to a minute is not "absorbing
latency" — it is choosing **play-by-mail**: the player reads a chapter, answers,
comes back later. That is a legitimate and possibly better product for this
engine's strengths (long, careful prose, a real cast, no chat urgency), but it
changes what the thing *is*, exactly like task 71's question about narration.

**It is the owner's call and it goes in writing here before 73b is designed**,
same protocol as 71. Until then, 73a is unblocked and 73b is not.

## 4. What this task does NOT protect against

The "we will look foolish in two years" risk is real, and **it is not the loading
screen** — that is a view, deleted in an afternoon. It is that once latency is
free to spend, it gets spent invisibly: a serial fan-out where parallel was
available, a synchronous validation chain, one more call nobody counted. Then the
models get ten times faster and the engine is still slow, for reasons no one
measured.

That is this project's documented failure mode wearing new clothes — the number
nobody looks at is the one that rots (`.plan/ROADMAP.md`, the inverted `NSR`
gate; `benchmarks/README.md` §7).

**So the stance ships with an instrument, or it is drift.** Cheap, because the
data already exists: every `debug.jsonl` record carries `duration_ms`, and
`metrics.json` already reports `llm_calls_per_action`.

- wall-clock latency per turn, and per agent role;
- **how much of it is serial versus parallelisable** — the number that actually
  decays into embarrassment;
- reported in every battery beside the other metrics, **never a gate** (the phase
  rule on reported-not-gated applies: a large move is a prompt to go look).

Task 65's `asyncio.gather` is the first concrete instance of what this instrument
would defend, and it is being built anyway.

## 5. The card rule, and the one real dependency

A recap card that tells the player what they just read is the phase's headline
defect in a new channel. Splitting the card types removes the risk entirely:

- **lore / world cards** — authored, static, not derived from the session:
  **free**, no dependency, no repetition risk. This is what the sketch actually
  wanted, and what the player enjoys without wondering why it is there.
- **recap cards** — generated from session history: only from **older** material,
  never the previous turn, **and they inherit task 71's projection dependency.**

The no-spoiler invariant in the sketch ("reads committed public history and
player-perceptible facts") is precisely the per-viewer projection problem of
tasks 71/63/59. History has no viewer projection today — that is why narration
hands the player scenes their character cannot reach. A recap built on the same
unprojected history leaks the same way, and then there are two consumers to fix
instead of one. **If recap cards ship, they ship after 71**, where the projection
already exists and the invariant comes for free.

## 6. The alternative worth costing before 73b

**Progressive delivery** — streaming narration as it is produced, showing
character replies as they land. It attacks the same perception of waiting, and it
**degrades well in both directions**: if latency collapses it does not become
dead weight, it becomes instant.

It is not a replacement for 73a, and it may not be a replacement for 73b either
(a 60-second wait wants something to look at even if it is streaming). But it
should be costed before the sprite library is commissioned, because it is the
cheaper half of the same goal.

## 7. Verification

- [ ] **73a:** the journal persists across sessions and is reachable from the
      menu, not only from the loading screen;
- [ ] **73a:** no hidden state, no uncommitted draft and no future beat reaches an
      entry — asserted against the real builders, not by reading the output;
- [ ] the product question in §3 answered in writing before 73b is designed;
- [ ] **§4's latency instrument exists and is reported in a battery** before the
      stance is used to justify a second expensive design;
- [ ] **73b:** the plugin never blocks the turn locks;
- [ ] **73b:** lore cards carry no session-derived content; recap cards, if they
      exist at all, draw only from material older than the previous turn;
- [ ] deleting 73b leaves 73a and the engine untouched — the check that keeps the
      retreat cheap.
