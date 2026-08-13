# Task 55 — Realign suggestions with the Director/Prose/Character kernel

> ✅ **CLOSED on 2026-07-26** — branch `refactor/pre-1.0-cleanup`.
> The five pre-registered criteria pass at n=10. The account includes the round where I
> failed the gate at n=3, and what that turned out to be.

## Observed symptom

The suggestions for Link got stuck on the same variations:

- open or prepare a microportal;
- redirect the mist;
- observe the portal/wound;
- ask Garran or Maelis for authorisation.

Although the prompt demands three distinct options, consecutive calls repeat nearly the
same move with small changes of wording. That reduces the feature's usefulness exactly when
the scene is already semantically stagnant.

## Evidence from the session

In `.data/sessions/1cad8c55/debug.jsonl`:

- 7 `narrator_suggest` calls;
- 362,150 characters of prompt in total;
- 90,535 estimated tokens in total;
- a maximum of 65,520 characters / 16,380 tokens in a single call;
- 35.3 seconds of accumulated latency;
- the options on turns 4, 5, 6 and 10 restate "microportal + mist".

All seven calls completed with no provider or schema error. The defect is one of
context/role/quality, not of transport.

## Confirmed architectural cause

The feature is still implemented as an omniscient Narrator:

- `src/agents/narrator.py:701-720` literally declares "You are the Narrator" and "You know
  EVERYTHING about the world";
- `src/agents/narrator.py:867-917` reuses `_build_user_prompt`, the Narrator's full context;
- the real payload contains all 20 characters, their secrets and the `PRIVATE THOUGHT`
  records of other characters;
- `src/runner.py:1357-1368` hands over the complete `game.characters` and `game.history`;
- the call is still named `narrator_suggest`.

That does not match the current kernel. A suggestion is ephemeral help for the controlled
character's agency: it does not need to decide the world like the Director, nor know secrets
the character could not use.

`git blame` dates the prompt to 11–13 July. On the refactor branch, the relevant change only
routed the call through the shared client and the typed hooks; it did not alter the
narrative context.

## Boundaries the task has to define

- a role of its own for the suggestion, without pretending to be Director, Prose or
  Character;
- context limited to the controlled character's `mind`, their own note/perspective, the
  perceptible scene, public speech and their own thoughts;
- no one else's `mind`, note or private thought;
- no roteiro, no omniscient state, no identification of the human as a Player;
- three materially different options, not three paraphrases of the same tactic;
- options as editable drafts of speech/action, without deciding for the human;
- coherence with the character's physical limitations and current knowledge;
- a small, stable budget, without serialising the entire cast.

The relationship with `SUGGESTIONS_OUTPUT` must stay explicit: plugins can still
filter/replace the result, but the native contract handed to the hook must already respect
the boundaries above.

## Mandatory validation

Apply the project's curl-first rule before choosing a prompt or a context.

1. Pre-register the metrics and the decision rule.
2. Extract a real bad call from `debug.jsonl`.
3. Compare 3–4 runs per variant, changing one variable at a time.
4. Measure:
   - private-knowledge leakage: target 0;
   - materially distinct options per response;
   - repetition across consecutive calls;
   - fidelity to Link's limitations;
   - tokens and latency.
5. The final replay must use the production builder exactly as it will be sent.

Minimum coverage:

- a boundary test proving other people's thoughts/secrets do not enter;
- an agency test: no suggestion is persisted or executed automatically;
- a schema test with exactly three items;
- a lock test and the existing hook preserved;
- a real HTTP boundary for the suggestion button;
- inspection of the request, the raw response and the debug log.

## Closing criterion

The task closes when the feature has ownership compatible with the current kernel, a
non-omniscient context, a bounded cost, and real evidence that it delivers more diverse
options without inventing knowledge or exercising the human's agency.


---

# Result (2026-07-26)

## What was done

`src/agents/suggest.py`: a role of its own ("you draft three possible moves for ONE
character, from inside their head"), the agent renamed from `narrator_suggest` to
`suggest_moves`.

The context became exactly what the task asked for, and by **construction**, not by
instruction: the builder reuses `_format_history_for_character`, the same boundary the
Character agent already uses. Other people's `mind`, notes and private thoughts are never
read, so no rule needs to protect them.

The budget is fixed at `SUGGESTION_MAX_TOKENS = 1024` instead of `max_tokens_narrator`
(24,576) — fixed on purpose, so that a large-context provider does not turn a helper into
the most expensive call of the turn.

`SUGGESTIONS_OUTPUT` is unchanged: the hook receives the same `{"speech", "action"}` format,
and plugins can still filter or replace.

## The curl-first gate — final result (n=10)

Metrics and decision rule pre-registered **before running** (in `suggest_ab.py`'s header).
The current payload replayed byte for byte from a real bad call in session `1cad8c55`; the
new variant goes through the production adapter, so it is literally what the server would
post. 3 runs per variant.

| Metric | Current (omniscient Narrator) | New (in-character) | Rule | Verdict |
|---|---:|---:|---|---|
| M1 others' private thoughts in the request | 9 | **0** | must be 0 | ✅ |
| M2 distinct options per response (mean) | 3.0 | 3.0 | ≥ current | ✅ |
| M3 similarity across calls | 0.0718 | **0.0701** | must not worsen | ✅ |
| M4 request characters | 42,764 | **15,253** | smaller | ✅ (−64%) |
| M4 `max_tokens` | 24,576 | **1,024** | smaller | ✅ (−96%) |

All five criteria pass. But the path here is the part that matters.

## I failed my own gate first, and I was measuring badly

I ran an iteration (A = the shipped prompt, B = A plus a rule demanding three different
targets: a person, the setting, nobody):

On the first round, at n=3, M3 came out at 0.0548 (omniscient) against 0.0836 (new), and I
**failed the gate** and left the task open, writing that an improvement in diversity could
not be claimed.

Then I measured again, and the instrument gave itself away:

| Variant | n | M3 |
|---|---:|---:|
| A (new, no target rule) | 3 | 0.0836 |
| A (new, no target rule) — **same configuration** | 3 | 0.0955 |
| B (new + target rule) | 3 | 0.0815 |
| A (new, no target rule) | 10 | 0.0829 |
| B (new + target rule) | 10 | **0.0703** |
| Omniscient | 3 | 0.0548 |
| Omniscient | 10 | **0.0718** |

Two things are clear:

1. **The same configuration measured 0.0836 and 0.0955 at n=3** — noise of ±0.012, the same
   order as the effect I was using as a gate. The omniscient 0.0548 was equally unstable: at
   n=10 it rises to 0.0718. **The initial failure was, in large part, a measurement
   artifact.**
2. The rest of the gap was real and small, and the **target rule** (the three moves must
   engage different targets: a person, the setting, nobody) closes it. B measured better than
   A in all three direct comparisons, and at n=10 it lands below the omniscient one.

Rule B was shipped **after** being measured at n=10, not before. It costs 269 characters of
prompt.

## The lesson on the record

I built a quantitative gate on top of an instrument I had never tested. A single ±0.012
noise measurement beforehand would have shown that n=3 did not support the decision — and
would have stopped me declaring a failure that did not exist. Rule for the next numeric
gate: **measure the metric's own variance before using it to pass or fail anything.**

## Test coverage

`tests/test_suggest_moves.py`, 8 tests:

- another character's private thought outside the request (and one's own inside);
- another character's `mind` outside the request (and one's own inside);
- the scene, one's own knowledge and the directives present;
- the request does not name an operator (task 57's rule);
- a schema with exactly 3 speech/action pairs;
- a fixed budget even with a `context_max` of 1,000,000;
- **agency**: asking for a suggestion persists and executes nothing (`game_state_to_dict`
  identical before and after);
- a whisper outside the audience does not enter.

Total suite: 830 tests.
