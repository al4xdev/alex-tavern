# `closed/` — history, not instruction

**Around 80 files. None of them tells you what to do.**

Every file here describes a decision **as it was being made**. It was accurate when
it was written and some of it is not accurate now: the engine moved, contracts
changed, and several of these documents contain a claim that a later file retracted.
Retractions are left standing next to the claim they retract, on purpose — that is
the record, and deleting the wrong half would hide how the right half was reached.

## How to use this folder

- **To answer "why is it like this?"** — yes. This is the best place in the
  repository for that question.
- **To answer "what should I build?"** — no. Use `.plan/tasks/`, and
  `.plan/ROADMAP.md` for the order.
- **To copy a code path, a threshold or a schema out of** — no. Check the code.
  Several of these describe an implementation that has since been deleted, and a
  few describe one that was never shipped because its falsifier fired.

## Two traps that have caught agents here

1. **A banner can be stale.** Task 65 sat in `tasks/` reading *"open, ready to
   implement"* for a week after it shipped. Fixed 2026-08-13, but assume it can
   happen again: **the tree is the truth, this folder is the story.**
2. **A section headed ✅ DELIVERED may be followed by a later section that
   withdraws part of it.** Read a file to the end before acting on its middle.

## What is worth reading here even so

- **39, 41, 55** — the method lessons that outlived their own delivery: measure a
  metric's variance before gating on it; position in the prompt is part of the
  variant; numbers that live in a temp directory are an account, not evidence.
- **next-pre-1.0-cleanup** — why a helper exists once instead of six times.
- **65** — the largest measured defect of the phase, and what closing one looks like.
