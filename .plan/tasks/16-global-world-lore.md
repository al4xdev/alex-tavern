# Task: Global World Lore (Shared Knowledge Plugin)

**Status:** Open (Refactored to Plugin Architecture)  
**README evidence:** `README.md:30-43` (Warning on Planned Plugin Refactoring)  
**Replaces:** Old structural core proposal for `world_lore`

## 1. Description & Plugin Fit
Instead of polluting the core domain models (`GameState`, `Character`, `Runner`) with hardcoded lore structures and building bespoke prompt-injection heuristics, the **Global World Lore** feature will be implemented as a **Hybrid Plugin** (`global-world-lore`).

This plugin will hook into the synchronous turn execution pipeline to inject shared background facts (e.g., world history, magic rules, local customs, current laws) into prompts, using dynamic filtering to control token usage.

---

## 2. Plugin Mechanics & Hooks

The plugin will utilize the following plugin capabilities:
1. **Trigger capability (`before_narrator` & `before_character`):** 
   - Intercepts prompts before LLM dispatch.
   - Appends relevant lore blocks to the Narrator's prompt (as a general truth filter) and to the active NPC Character's prompt (as subconscious shared memory).
2. **Background capability (Lore RAG Indexer):**
   - Indexes world lore files stored in `.data/plugins/world-lore/{preset_name}.md` in the background.
   - Prevents **Prompt Bloat** by performing semantic lookup (RAG) against the recent dialogue window to pull only *relevant* lore nodes, rather than dumping the entire lore Bible into every call.

---

## 3. Data Flow

```text
User Input / Turn Trigger
          │
          ▼
   [Core Runner]
          │
          ├─► Calls: plugin.before_narrator(messages, game_state)
          │     │
          │     ├── Gets last 3 turns of history
          │     ├── Queries background Lore Index (RAG) for keywords (e.g., "Mage Tower")
          │     └── Appends matched Lore: "Mage Tower: Rules of magic forbid..." to Narrator system prompt
          │
          ▼
   [Narrator LLM Call]
          │
          ├─► Routing chooses NPC C1
          │
          ├─► Calls: plugin.before_character(C1, messages, game_state)
          │     │
          │     └── Appends matching Lore to C1's Character system prompt
          │
          ▼
   [Character LLM Call]
```

---

## 4. Privacy & Knowledge Isolation
* **Shared Lore:** All matched lore nodes are injected as common knowledge.
* **Secret Knowledge Integration:** Character-specific secrets remain isolated in `character.mind.knowledge` (core domain). The plugin only handles lore tagged as *shared* or *discoverable* by specific factions, combining them dynamically at the hook boundary.

---

## 5. Implementation Roadmap
1. **Plugin Config:** Load lore markdown files from a dedicated folder under the plugin configuration workspace.
2. **Hook Registry:** Register `before_narrator` and `before_character` event listeners.
3. **RAG Search Integration:** Connect the RAG indexer to retrieve lore nodes.
4. **Token Control:** Enforce limits to ensure injected lore does not exceed a predefined token budget (e.g., maximum 500 tokens).
