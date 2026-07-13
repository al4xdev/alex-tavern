# Task: Measured compaction progress

**Status:** Conditional improvement; current UI is intentionally simulated  
**README evidence:** `README.md:333-334`, `README.md:380-383`

## Current behavior

- `src/static/app.js::compactSession` estimates duration from rendered message count.
- The bar animates to at most 90%, then jumps to 100% after the API response.
- The backend returns one completed response; it does not stream Historian progress.

## Potential future behavior identified by the README

- Replace the estimate with measured progress if real progress tracking becomes worth the
  additional streaming architecture.

## Open questions

- The README does not commit to implementing this feature.
- It does not define whether progress means tokens generated, Historian lifecycle stages,
  elapsed-time estimation, SSE, or another transport.
