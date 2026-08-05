# Task 73 — Travel Journal Compendium & 8-Bit Loading Experience Plugin

> **Status:** backlog (created as a future feature proposal).
> **Concept:** Dual-purpose plugin serving as an in-game **Travel Journal (Diário de Bordo)** and an interactive **8-bit Loading Screen Experience** featuring non-spoiler recaps, world lore, and a rich library of pixel-art character animations.

---

## 1. Context & Motivation

Turn execution involving multi-agent dialogue and narrator validation takes several seconds per turn. Rather than presenting a static spinner, the player is engaged with an active **8-bit animated loading screen** that displays non-spoiler recaps and world lore.

Furthermore, this data doubles as an in-game **Diário de Bordo (Travel Journal)** accessible at any time from the UI menu, ensuring that work done during loading screens is not discarded and becomes a permanent, readable log of the journey.

---

## 2. Core Features

### A. Diário de Bordo (In-Game Travel Journal)
- Maintains a structured `journal.json` in plugin storage.
- Automatically compiles past committed public history into readable journal entries, character notes, and discovered world facts.
- Accessible via the UI menu as a permanent compendium.

### B. 8-Bit Animated Loading Screen
- **Non-Spoiler Recaps & Lore:** Displays cards with past event summaries and world facts while waiting for `mutate_submit_turn` to complete.
- **Pixel-Art Sprite Library:** Integrates an extensive library of ~100 distinct 8-bit character animations (walking, resting, campfire scenes, reading maps, battling shadows, etc.) to ensure visual variety and prevent repetition during loading waits.

---

## 3. Architecture & Plugin Integration

```text
[Turn Submission]
       │
       ▼
Plugin Async Hook (before_commit / background)
       ├─► Update Diário de Bordo (journal.json)
       └─► Supply Loading Screen UI (Random 8-Bit Animation + Non-Spoiler Card)
```

1. **No-Spoiler Invariant:**
   The generator strictly reads committed public history and player-perceptible facts. It never accesses uncommitted drafts, hidden thoughts, or future script beats.

2. **Storage & Namespace:**
   Uses standard plugin storage namespaces (`.data/plugins/<plugin-id>/storage/journal.json`).

---

## 4. Verification & Criteria

- [ ] Plugin executes asynchronously without blocking the primary engine turn locks.
- [ ] Diário de Bordo persists cleanly across sessions.
- [ ] Strictly non-spoiler: assertions verify no hidden or future state leaks into loading cards or journal entries.
- [ ] Frontend loading screen cycles smoothly between 8-bit animations and lore cards with fallbacks.
