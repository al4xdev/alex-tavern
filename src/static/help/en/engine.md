# 🎬 Screenplay & Backend Engine

Alex Tavern operates via a deterministic, state-driven architecture where human agency is preserved and the world is governed by clear, isolated roles.

---

### 1. Runner Architecture and Canonical State

- **Single Persisted State:** All speech, actions, thoughts, locations, and emotional states live in a single JSON file per session (`state.json`).
- **Transactional Locks:** Every turn, undo, or compaction acquires an exclusive per-session lock. No mutation happens outside this boundary.
- **Human Agency Lock:** The human player exclusively controls their character. AI character agents never dictate your character's speech, physical actions, or thoughts.

---

### 2. Private Screenplay, Acts, and Beats

When the **Story screenplay** option is enabled:

- **Omniscient Director:** The Director compiles a private narrative plan that characters cannot see.
- **Acts and Beats:** The story is structured into **Acts** (major arcs) and **Beats** (immediate dramatic scene goals).
- **Expected Actors:** Each beat defines a dramatic intent and identifies which characters are called to interact during that beat.

---

### 3. Adaptive Replanning (*Beat Replans*)

Alex Tavern is not a rigid script. If the story takes an unexpected turn (due to player choices or organic character reactions):

- The Director detects the divergence and executes a **Replan** (adaptive rewriting of the beat or act).
- The screenplay adjusts to what just happened in the scene, recalibrating future goals without breaking logical consistency.

---

### 4. Character Dramatic Alignment (Toggle 2)

- **Acting Logic:** When character alignment is on, non-controlled agents listed as *Expected Actors* receive a **transient dramatic impulse** (such as *bold*, *urgent*, or *cautious*).
- **Leak-Safe Construction:** The character receives only a generic inner feeling (enum), never private screenplay facts or future spoilers. They choose to serve the story while retaining their unique voice and personality.
