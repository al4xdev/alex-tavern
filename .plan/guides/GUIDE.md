# Start here — a guide for the agent taking over

**Written 2026-08-13, for the model that inherits this repository next month.**
Not vendor-specific. If you are a human, this works for you too.

`AGENTS.md` is the contract and it is 550 lines. This page is the hour before it.

---

## What this is, in three sentences

A multi-agent roleplay engine. A **Director** decides what happens in the physical
world and who speaks next; **Character** agents speak and think with deliberately
restricted context; a **Runner** owns state, locks, persistence and — above all —
the human's agency. Everything is judged on one thing: **immersion**, which breaks
when the machine repeats itself or when the machinery becomes visible.

## The first hour, in order

1. **`AGENTS.md` §0** — the hard rules and which ones a test will catch. Ten minutes.
2. **`.plan/ROADMAP.md`** — the current phase, the waves, and the order. It is an
   index and an ordering argument, not a container.
3. **`.plan/CHECKPOINT-2026-08-13.md`** — where the phase actually stands.
4. **`.plan/reference/metric-validity.md`** — which instruments are trusted, which
   were downgraded, and which were measured and rejected. **Read this before you
   quote any number.**
5. **`.plan/reference/critic-protocol.md`** — how this project decides a sentence
   was worth writing.
6. Then `AGENTS.md` in full, once, before your first change.

## What the folders mean

| folder | meaning | how to read it |
|---|---|---|
| `.plan/tasks/` | has a **next action** | instructions |
| `.plan/backlog/` | real, no next action | ideas |
| `.plan/closed/` | done | **history, not instruction** |
| `.plan/para-o-dono/` | waiting on the owner | do not act; ask |
| `.plan/reference/` | living architecture docs | instructions |
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

Five rules carry most of that:

1. **The session is the unit.** Count per session, compare sessions. Pooling turns
   treats one Director decision as seven independent observations.
2. **Every headline number carries its per-session spread** — median, sd, range. A
   pooled 34% over a median of 15% means a handful of sessions carried the claim.
3. **Pre-register the decision rule before you run.** What result would change your
   mind, written down before the data exists.
4. **Never match a model-authored name with a string heuristic.** This project
   shipped that failure twice. When a detector scores zero, ask whether it can see
   the thing at all before concluding the thing is absent.
5. **`curl` before you believe.** Any claim about LLM behaviour is a hypothesis
   until a replay on a real payload confirms it, 3-4 runs, counting the rate.
   Method in `AGENTS.md` §6. **Position in the prompt is part of the variant** —
   rules validated at the end of a prompt worked 3/3; the same rules in the middle
   failed 3/3.

## What the owner expects from you

- **Cost, latency and backwards compatibility are cheap here.** Do not propose a
  worse design to save them, and do not ask permission to spend them (`AGENTS.md`
  §2). Complexity and a worse answer are what is expensive.
- **A negative result is a result.** An arm that fails its own pre-registered gate
  is not adopted, however good it looked. Write it down with its numbers so nobody
  re-derives it in a month.
- **Say "undiagnosed".** A measured symptom with an unknown cause is an honest and
  useful state. A confident mechanism where only a symptom was measured is the
  single most damaging thing you can put in this record.
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
  76 files and `docs/cases/` is 24; loading them as instruction is how you end up
  reimplementing something that shipped. Read what `tasks/` points you at.
- If Gemini is ever added as a **provider** to the engine itself (not as the coding
  agent), note that Gemini 3.x rejects `temperature`, `top_p`, `top_k` and
  `candidate_count`, and that `FunctionResponse` needs `call_id` and `name`. The
  adapter contract in `src/llm/adapters/` is where that belongs — not in the Runner.

## The three ways an agent has actually gone wrong here

Not hypotheticals. All three happened, and all three were expensive.

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
