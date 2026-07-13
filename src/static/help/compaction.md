# 🗜️ History Compaction

As your roleplay goes on, the turn history grows and can consume significant LLM context tokens.

## How it works
1. Compaction preserves the **last N turns** verbatim (defined in settings).
2. It condenses all older narrative prose into a **public story summary** and **isolated character notes**.
3. It takes a backup of the session prior to compaction, allowing you to undo the compaction if no new turns have been played.
