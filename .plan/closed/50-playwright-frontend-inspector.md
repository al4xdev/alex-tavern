# Task 50 — Shared Playwright frontend inspector

**Status:** CLOSED (2026-07-21)

## Goal

Give repository agents one repeatable way to inspect the live frontend instead
of inventing ad-hoc Firefox commands or temporary application code.

## Frozen contract

- Python Playwright belongs to the `dev` dependency group, never application
  runtime dependencies.
- `tools/frontend_inspector.py` provides a CLI/library boundary with fresh,
  headless browser contexts, bounded viewport/timeouts, console/page-error
  capture, visible body text and a PNG under `/tmp`.
- Chromium is the default engine. Firefox and WebKit are opt-in when their
  Playwright browser bundle is installed.
- Supported interaction steps are typed and intentionally small: click, fill,
  press, select option, wait for selector and bounded wait. No arbitrary JS
  evaluation is exposed.
- The debug MCP exposes a read-only `inspect_frontend` tool for a passive page
  capture and a non-read-only `mutate_frontend_flow` tool for interaction steps.
- MCP output names are sanitized and always resolve under
  `/tmp/alex-tavern-frontend/`. No screenshots, profiles or browser cache enter
  Git or `.data`.
- Missing browser bundles fail with an actionable `playwright install` message.

## Acceptance

- [x] Dependency lock, CLI/library validation and MCP registry are tested.
- [x] Passive and stepped MCP wrappers have correct annotations and output paths.
- [x] A real Chromium capture of the temporary Alex Tavern server succeeds.
- [x] `tools/README.md`, root README and MCP inventory document setup and usage.
- [x] Standard focused checks pass and task moves to `.plan/closed/`.

## Delivery evidence

- `uv.lock` resolves Playwright 1.61.0 in the dev group with `greenlet` and
  `pyee`; the managed Chromium bundle was installed through the documented
  `uv run playwright install chromium` boundary.
- Request validation covers every allowed action plus invalid URL, output path,
  browser, viewport, timeout, selector, value and wait duration. Arbitrary JS
  evaluation is not an action.
- MCP registry tests prove that `inspect_frontend` is read-only,
  `mutate_frontend_flow` is non-read-only, unsafe output names are rejected and
  both resolve PNGs under `/tmp/alex-tavern-frontend/`.
- The old file launcher was replaced forward-only with
  `python -m tools.mcp_server`, so sibling tool imports work without path hacks;
  every README/config example and the stdio test producer changed together.
- A real CLI capture against the isolated server at `127.0.0.1:8891` returned
  HTTP 200 at 390x844, title `Alex Tavern`, no console warnings/errors, no page
  errors and `/tmp/alex-tavern-frontend/task50-real.png`.
- A second real capture called `inspect_frontend` through the FastMCP registry at
  1365x900 and produced `/tmp/alex-tavern-frontend/task50-mcp.png`, again with
  zero browser errors.
- Final focused slice: 70 passed, one known stdio-boundary test deselected.
  Ruff check/format and mypy over `src/`, `frontend_inspector.py` and
  `mcp_server.py` passed. The aggregate suite repeated its previously documented
  no-output boundary hang and was interrupted without an observed assertion
  failure.
