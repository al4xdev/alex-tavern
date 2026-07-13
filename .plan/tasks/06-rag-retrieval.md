# Task: RAG retrieval system

**Status:** Explicit future work, deferred until after compaction  
**README evidence:** `README.md:508-513`, `README.md:562-588`

## Stated architecture

- Use vector embeddings rather than lexical keyword matching.
- Keep a separate vector store per session.
- Run an opt-in background vectorization agent while the human reads or plays.
- Incrementally embed older or already-compacted session JSON that has not been indexed.
- Do not block normal turns while indexing.
- Trigger retrieval explicitly with `/rag <keyword>`.
- Do not inject raw vector-search chunks directly into a live prompt.
- Use one LLM pass to curate retrieved results and a second pass to generate invisible
  context for the Narrator and Character.
- Keep generated retrieval context out of visible chat while recording it in underlying
  session data/logging.
- An approximately one-minute on-demand latency is considered acceptable by the README.

## Current repository state

- No embedding dependency, vector store, vectorization worker, retrieval agent, `/rag`
  handler, curation pass, retrieval-message pass, persistence schema, or tests exist.

## Dependencies on other open tasks

- `/rag` is intended to be the first consumer of the general slash-command tool system;
  see `07-slash-command-tools.md`.

## Open questions

- Embedding model, vector-store implementation, chunk boundaries, index versioning,
  deletion/rebuild behavior, retrieval count, failure handling, and exact prompt routing
  are not specified.
- The README does not define how retrieved context is scoped so a Character still receives
  only information it is allowed to know.
