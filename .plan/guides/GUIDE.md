# Start here — a guide for the agent taking over

**Written 2026-08-13, for the model that inherits this repository next month.**
Not vendor-specific. If you are a human, this works for you too.

`AGENTS.md` is the contract and it is ~550 lines. This page is the hour before it.

---

## What this is, in three sentences

A multi-agent roleplay engine. A **Director** decides what happens in the physical
world and who speaks next; **Character** agents speak and think with deliberately
restricted context; a **Runner** owns state, locks, persistence and — above all —
the human's agency. Everything is judged on one thing: **immersion**, which breaks
when the machine repeats itself or when the machinery becomes visible.

## The first hour, in order

1. **`AGENTS.md` §0** — the hard rules and which ones a test will catch. Ten minutes.
2. **[`MEASURING.md`](./MEASURING.md)**, next to this file — the nine rules, and what
   each cost when it was broken. **Second on purpose:** you will produce a number on
   your first day, and the ruler has to arrive before you need it, not after.
3. **`.plan/ROADMAP.md`** — the current phase, the waves, and the order. It is an
   index and an ordering argument, not a container.
4. **`.plan/CHECKPOINT-2026-08-13.md`** — where the phase actually stands.
5. **`.plan/reference/critic-protocol.md`** — how this project decides a sentence
   was worth writing.
6. Then `AGENTS.md` in full, once, before your first change.

`.plan/reference/metric-validity.md` is **not** on this list. It is the register: you
look an instrument up in it the moment you are about to quote that instrument, and
you never read it end to end.

## What the folders mean

| folder | meaning | how to read it |
|---|---|---|
| `.plan/guides/` | how work is done here | **read once, end to end** |
| `.plan/tasks/` | has a **next action** | instructions |
| `.plan/backlog/` | real, no next action | ideas |
| `.plan/closed/` | done | **history, not instruction** |
| `.plan/para-o-dono/` | waiting on the owner | do not act; ask |
| `.plan/reference/` | living architecture docs + the metric register | **consulted**, by looking up a name |
| `docs/cases/` | the numbered article series | **history**, and the reasoning behind decisions |
| `benchmarks/` | archived batteries + the metric glossary (§7) | evidence |

**A file in `closed/` or `docs/cases/` describes a decision as it was being made.**
Some of them are wrong on purpose — a retracted claim is left standing next to its
retraction, because that is the record. Never take an instruction from either
folder without checking it against `tasks/` and the code.

## The house method, and why it is not optional

> **Every real finding in this project came from reading. Not one came from a
> metric announcing its own error.**

That is measured, not folklore: seven causal stories were killed in one work block,
and all seven were killed by reading records or code, never by a number looking
wrong. Five instruments in the same block reported a clean number and were wrong.

So the order is: **read the thing, form a claim, then find the number that could
prove you wrong.** Not the reverse.

The rules that carry that are the **nine in [`MEASURING.md`](./MEASURING.md)**, next
to this file — one copy, so this page cannot drift from it. Read them before you
quote any number; each one carries what it cost when it was broken.

The one rule this guide adds, because it is method rather than measurement:

> **`curl` before you believe.** Any claim about LLM behaviour is a hypothesis until
> a replay on a real payload confirms it — 3-4 runs, counting the rate, decision rule
> written down first. Method in `AGENTS.md` §6. **Position in the prompt is part of
> the variant**: rules validated at the end of a prompt worked 3/3; the same rules in
> the middle, buried under 5k characters of directives, failed 3/3.

## What the owner expects from you

- **Cost, latency and backwards compatibility are cheap here.** Do not propose a
  worse design to save them, and do not ask permission to spend them (`AGENTS.md`
  §2). Complexity and a worse answer are what is expensive.
- **Say "undiagnosed".** A measured symptom with an unknown cause is an honest and
  useful state. A confident mechanism where only a symptom was measured is the
  single most damaging thing you can put in this record. (Rules 6 and 9 in
  `MEASURING.md` are the same idea applied to a number: a negative result gets
  written down with its numbers, not quietly dropped.)
- **Do not commit or push without being asked**, and never write an AI authorship
  trailer (`.claude/skills/git-commit/SKILL.md`).
- **New findings go to `backlog/` by default.** A phase does not grow while nobody
  is watching. Promoting one to `tasks/` is the owner's call.
- When a decision is the owner's, write a page in `para-o-dono/` and **keep
  working on something else.** Do not block, and do not decide it for them.

## Notes for a Gemini 3.7 Flash agent specifically

Written from the model's own release guidance (2026-08-13), not from experience with
it in this repo. Treat as a starting configuration, and correct it once you have
evidence.

- **`thinking_level: medium`** is the default and the vendor's recommendation for
  coding and agentic work. Use `high` for the falsification work in this repo —
  designing a control, reading a session as fiction, deciding whether a mechanism
  survived. Use `low` for mechanical passes only.
- `thinking_budget` is deprecated in favour of `thinking_level`.
- The release's headline gain is **fewer failed agent loops**. This repository is a
  good place to spend that: the failure mode it punishes hardest is an agent that
  iterates on a symptom without ever isolating the call.
- **A 1M context window is not permission to read everything.** `.plan/closed/` is
  around 80 files and `docs/cases/` is 24; loading them as instruction is how you end up
  reimplementing something that shipped. Read what `tasks/` points you at.
- If Gemini is ever added as a **provider** to the engine itself (not as the coding
  agent), note that Gemini 3.x rejects `temperature`, `top_p`, `top_k` and
  `candidate_count`, and that `FunctionResponse` needs `call_id` and `name`. The
  adapter contract in `src/llm/adapters/` is where that belongs — not in the Runner.

## The three ways an agent has actually gone wrong here

The incidents behind rules 1, 2, 5 and 7 in `MEASURING.md` — kept as stories
because a rule is easy to nod at and an incident is not. Not hypotheticals. All
three happened, and all three were expensive.

1. **Believing a counter over a reader.** A similarity score of **0.02** between
   paragraphs a human sees as the same paragraph, four times over. A rate of "34% of
   all movement" that was 0% to 97% per session and turned out to be measuring
   naming style.
2. **A string heuristic over a model-authored name.** Shipped twice, nearly a third
   time. `named_exclusions` matched *"a menos de dois metros"*; a `HOLD` counter
   matched `fila` inside an order to **move**.
3. **Growing the phase while nobody watched.** Three tasks opened in one 2h49 block,
   all legitimate, against the roadmap's own warning. `tasks/` had to be swept back
   into `closed/` and `backlog/` a week later.

## When you are stuck

In this order: read a real session as fiction (`tools/render_transcript.py`), isolate
the single bad call from `debug.jsonl` and replay it with `curl`, then — and only
then — reach for a battery. The battery is the last instrument, not the first.

If you have a claim and no way to test it, say so and write it as a THEORY. That is
a finished piece of work here.
