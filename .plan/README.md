# .plan — folder map

The state lives **distributed** — what is done in `closed/`, what is active in
`tasks/` (with a status banner at the top), and the narrative/rational in the
articles of `docs/cases/`. The monolithic `ROADMAP.md` was removed on 2026-07-20
and **came back on 2026-08-02**, scoped to one phase: a phase boundary needs one
place that says what the phase is and in what order it is being attacked. It is
an index and an ordering argument, not a container — per-task detail still lives
in `tasks/`. Close it when the phase closes.

Organized by state:

| Folder/file | What it is | When to look |
|---|---|---|
| `ROADMAP.md` | The **current phase** (immersion), its fronts, the order they are attacked in, and **the baseline each task has to beat** | When deciding what is next, and before implementing any task |
| `tasks/` | **Active** tasks (open or delivered-with-reservations, banner at the top) | When working |
| `para-o-dono/` | Things waiting for **your action** (smoke tests, designs to accept) | When you return |
| `backlog/` | Future without active work (06 RAG, 16 lore, public/real persona, New Journey, S02) | When planning |
| `reference/` | Living architecture docs (29.2 map, narrator_hint study) | When designing |
| `closed/` | Tasks closed WITH CONFIDENCE + completed explorations | As history |

Archived batteries and **the definition of every metric** live in `benchmarks/`
(committed) — `benchmarks/README.md` §7 is the glossary; read it before gating
anything on a number. Raw session artifacts stay in `output29/` and
`plans/artifacts/` (gitignored, local).

Permanent conventions: only migrate tasks to `closed/` when closed with confidence;
commits in English without AI trailers; curl-first method (AGENTS.md §6 — the validated
variant IS the shipped one).

The project's series of scientific papers/articles lives in `docs/cases/` (its own
index with reading paths).
