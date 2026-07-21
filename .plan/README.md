# .plan — folder map

There is no longer a monolithic `ROADMAP.md` (removed 2026-07-20): the state lives
**distributed** — what is done in `closed/`, what is active in `tasks/` (with a
status banner at the top), and the narrative/rational in the articles of `docs/cases/`.
Organized by state:

| Folder/file | What it is | When to look |
|---|---|---|
| `tasks/` | **Active** tasks (open or delivered-with-reservations, banner at the top). Current open track: **43 — character disposition substrate** (phased roadmap, article No. 15) | When working |
| `para-o-dono/` | Things waiting for **your action** (smoke tests, designs to accept) | When you return |
| `backlog/` | Future without active work (02 media, 06 RAG, 16 lore, public/real persona, New Journey, S02) | When planning |
| `reference/` | Living architecture docs (29.2 map, narrator_hint study) | When designing |
| `closed/` | Tasks closed WITH CONFIDENCE + completed explorations | As history |

Permanent conventions: only migrate tasks to `closed/` when closed with confidence;
commits in English without AI trailers; curl-first method (AGENTS.md §6 — the validated
variant IS the shipped one); benchmark evidence in `output29/` and `plans/artifacts/`
(gitignored, local).

The project's series of scientific papers/articles lives in `docs/cases/` (its own
index with reading paths).
