# Pre-1.0 code cleanup — closed

> ✅ **COMPLETE** on 2026-07-26, branch `refactor/pre-1.0-cleanup`, 33 commits on top
> of `9387bdc`. The 13 items from the 2026-07-25 review were applied. The `.plan/next/`
> folder and `to_the_next.md` were removed: this article is what remains of them.

## What it was

A line-by-line review of `src/`, `tools/`, `tests/` and `.ci-cd/android/`, done because
development had wrapped up and 1.0 was about to freeze the base. The declared goal was
not to hunt bugs — 785 tests passed, ruff and mypy clean — but to **avoid entering the
first version with structural debt**: the same helper written six times, the same
defensive `if` nineteen times, a 245-statement method.

House rule throughout: forward-only. Nothing here created a shim, a converter or a
double read; where the cleanup broke the plugin SDK, both sides changed together.

## Measured numbers, before and after

| | Before (`9387bdc`) | After | |
|---|---:|---:|---|
| Tests | 785 | **847** | +62, none removed |
| ruff / mypy | clean | clean | 58 files |
| `Runner.player_turn` | 245 statements / 80 branches | off the list | 13 named stages |
| Imports outside the top | 80 | 45 | `main.py` went from 35 to **0** |
| Atomic JSON writes | 6 copies | **1** | +1 in `tools/` |
| Lock registries | 4 copies | **1** | generic, 3 domains |
| LLM transport blocks | 18 | **1** | `call_agent` |
| Hand-written log envelopes | 15 | **1** | `_emit` |
| `if self.plugins is not None` | 19 | **0** | |
| `_char` duplicated in tests | 15 files | **1** factory | |
| Hand-written Director dicts | 43 across 18 files | **1** factory | |
| `document.getElementById` | 161 scattered | **1** `dom.el` | fails loudly, with the id |
| `app.js` | 2,424 lines | **620** | 10 modules extracted |

## What was broken on purpose

- **Config v1**: `LEGACY_CONFIG_SCHEMA_VERSION` and the conversion are gone. Config v2
  stays valid — verified with a real boot.
- **`session.*` hooks**: no longer synchronous. Synchronous plugin handlers still work;
  the hub has to regenerate the exported contract.
- **`context.command`**: no longer passes through `unsafe`. Verified on a real server
  with the 3 curated plugins: **zero** `permission: "unsafe"` events in the journal
  (before, every plugin with a command emitted one).
- **`GET /bootstrap_log`**: removed. Nobody consumed it; `MainActivity` reads the file
  natively.
- **`tools/frontend_inspector.py`** and the two frontend MCP tools: removed in favour of
  the editor's Playwright plugin. See `50-playwright-*`.
- **Sessions**: `SESSION_SCHEMA_VERSION` remains **13**. Nothing here invalidated an
  existing session.

## Five things the suite (or a measurement) caught, worth recording

1. **`log_compaction_status` writes `"error": None` on purpose.** I read it as a
   leftover and "fixed" it. The message of a summariser failure carries the world's
   private summary, and that entry is read by tools and by the debug drawer.
   `tests/test_compaction.py` failed immediately. It is documented next to the test that
   locks it.

2. **The i18n `presence.*` keys are not dead.** They have no reader in this repository
   because their user is the curated presence plugin. I removed them,
   `test_frontend_architecture.py` failed, I restored them all. The header of `i18n.js`
   now warns that the catalogue is a plugin contract.

3. **`drive`/`watcher` and `roteiro` never rendered the same context.** They looked
   identical on reading; the byte-by-byte before/after comparison showed the first two
   label characters by ID ("C2") and the third by name ("Marta"). It became an explicit
   parameter with a comment: unifying them is a prompt experiment, not a refactor.

4. **No hand-written Director double carried the whole contract.** While writing the
   test that compares `director_beat()` against the shipped schema, I discovered that
   `scene_blocking`, `time_skip_ticks` and `time_skip_summary` were required in the
   schema and absent from all 43 dicts. The factory also had shared mutable defaults —
   two bugs found by the test of the factory itself.

5. **I claimed "Playwright cannot click" and it was false.** The failing targets sit
   inside `#setup-overlay`, a closed modal (`opacity: 0`, `pointer-events: none`). It
   was refusing correctly. Opening the modal in the right order, it drives the whole UI
   — including a swipe gesture in a phone viewport.

## How each gate was closed

- **The suite, ruff, mypy** on every commit.
- **A byte-identical prompt** wherever the refactor touched prompt context (doc 13):
  captured from `debug.jsonl` before and after.
- **A real boot** in both scenarios: empty `.data/` (default Experience applied, marker
  written) and an existing v2 config (API key preserved).
- **`curl`** against the error contracts: 404 for a non-existent session, 422 for an
  invalid turn, 409 for an opening after the conversation started.
- **A real session against DeepSeek**, played through the frontend at a 390×844
  viewport: create the session, generate openings, swipe the carousel, take a turn, get
  a suggestion, force a compaction, undo, open the debug drawer. Zero console errors.
- **The owner's manual playtest** (task 02), which produced tasks 53 through 57.

## What was left out of scope, declared

- `config: dict` → a typed dataclass (it crosses adapters, the SDK,
  `runtime-config.js` and ~40 tests: a supertask of its own).
- Splitting `main.py` into per-domain routers.
- Moving the large prompts into `.txt` files — it would destroy the traceability of the
  comments that cite which replay validated each position in the text.
- `style.css` (2,852 lines), not reviewed.

## The gate that is still yours

**The APK and the device** (`.claude/skills/android-apk-lab`). Docs 10 and 11 touched
exactly what only fails on the phone: `android-bridge.js`, the service worker shell
(currently `rpt-shell-v31`), `build_info`, the native boot strings and the v1 side of
`pydantic_compat`, which no desktop test covers.
