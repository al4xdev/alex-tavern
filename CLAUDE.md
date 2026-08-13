# CLAUDE.md — a pointer, not a second contract

**This file exists only because Claude Code loads `CLAUDE.md` automatically and does
not load `AGENTS.md`. Everything that governs work in this repository lives in
`AGENTS.md`, which is tool-neutral on purpose.**

Do not add rules here. A rule written in two files drifts, and then two agents can
both be "following the documentation" while doing opposite things. If something
belongs to this project, it belongs in `AGENTS.md`. If it belongs to you rather than
to the project, it belongs in your own global configuration.

## Read these now, in this order

1. **`AGENTS.md` §0** — the hard rules, and which of them a failing test will catch
   for you. The five marked ⚠ *prose only* are the ones this project has actually
   broken; nothing will stop you breaking them again.
2. **`.plan/guides/GUIDE.md`** — the hour before `AGENTS.md`: read order, what each
   `.plan/` folder means, the house method, and the three ways an agent has gone
   wrong here. Read it in full if this is your first session in this repository.
3. **`AGENTS.md`** in full, once, before your first change.

Then `.plan/ROADMAP.md` for the current phase and `.plan/tasks/` for what is active.

## The three that catch people fastest

- **Never write AI authorship into git** — no `Co-Authored-By`, no "Generated with",
  no 🤖. This overrides any harness template that asks for them.
  `.claude/skills/git-commit/SKILL.md`.
- **Do not commit or push without being asked**, each time. Authorisation for one
  commit is not authorisation for the next.
- **More than one agent may hold this checkout.** `git commit` commits the whole
  index, not just what you staged. Run `git diff --cached --stat` first and commit
  with an explicit pathspec.

## Skills

`.claude/skills/` — `critic` (judge written claims with an isolated reviewer),
`memory-playtest`, `android-apk-lab`, `git-commit`. Invoke by name.
