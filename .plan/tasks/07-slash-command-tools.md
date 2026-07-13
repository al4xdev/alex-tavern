# Task: General slash-command tool system

**Status:** Explicit future work  
**README evidence:** `README.md:587-593`

## Stated behavior

- Add a small plugin/registration mechanism for slash commands.
- Let tools be invoked on demand without adding one-off conditionals to the normal
  Narrator/Character turn pipeline.
- Make `/rag` the first registered tool while allowing additional capabilities later.

## Current repository state

- No slash-command parser, registry, plugin interface, command dispatch, or related tests
  exist in `src/` or `tests/`.
- Current manual capabilities are fixed REST endpoints and frontend controls.

## Open questions

- Command syntax/escaping, discovery/help, permissions, async execution, cancellation,
  persistence, error display, and the frontend entry point are not specified.
- The boundary between a local command plugin and an LLM-backed agent is not defined.
