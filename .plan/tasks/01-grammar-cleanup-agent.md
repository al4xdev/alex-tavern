# Task: Optional grammar-cleanup agent

**Status:** Explicitly planned, deliberately unimplemented  
**README evidence:** `README.md:158`, `README.md:175-178`

## Stated behavior

- Add an opt-in configuration flag.
- Before human text enters history, make a short LLM call that fixes grammar and style.
- Preserve the blind-agent rule: the processed text must enter the fiction as the
  controlled character, without revealing that a human exists.
- The internal `speaker == "Player"` marker remains available to identify which input is
  eligible for cleanup.

## Current repository state

- No grammar-cleanup agent, configuration key, call site, or test exists in `src/` or
  `tests/`.
- Human speech/action is currently appended directly by `Runner.player_turn` before the
  Narrator call.

## Open questions recorded by the README

- The feature is optional and should only be implemented if it proves necessary.
- The README does not define whether speech and physical action are both rewritten, what
  happens when the cleanup call fails, or how the raw original input is retained.
