# Explore: three-field turn input across debugger and tools

**Date:** 2026-07-12  
**Scope:** `speech`, `thought`, and `action` from browser input through API, Runner, JSONL,
debug drawer, MCP, deterministic replay, playtest harness, fixtures, tests, and documentation.

## Finding

The runtime contract is already three-field end to end. No functional path was found that drops a
non-empty `thought`. The drift is limited to stale comments/public case-study wording and missing
coverage in replay/playtest artifacts.

```text
browser composer
├── speech
├── thought
└── action
    │
    ▼
PlayerTurnRequest / PreviewPromptRequest
    │
    ▼
Runner.player_turn
├── typed history records
├── turn_input JSONL marker
└── Narrator bypass for thought-only input
    │
    ├── debug drawer: renders the complete marker generically
    ├── MCP submit tool: forwards all three fields
    ├── replay driver: restores all three fields
    └── playtest harness: validates and forwards all three fields
```

## Current functional coverage

- Backend request schemas declare all three fields and reject only when all are empty
  (`src/main.py:107-118`, `src/main.py:121-124`).
- The Runner logs and persists each populated field independently; a thought-only turn is private
  and intentionally makes no LLM call (`src/runner.py:129-212`).
- `turn_input.input` contains `speech`, `thought`, `action`, and `force_speaker`
  (`src/llm/debug_log.py:48-80`).
- The debug drawer does not destructure an old two-field shape. It serializes `e.input` as a whole,
  so `thought` appears automatically; prompt preview also submits all three fields
  (`src/static/app.js:752-805`).
- Live send, retry state, player echo, history grouping, and session reload all retain all three
  fields (`src/static/app.js:262-291`, `src/static/app.js:540-544`,
  `src/static/app.js:878-910`).
- MCP client/tool signatures forward all three fields, and its HTTP adapter test asserts the exact
  JSON body with a non-empty thought (`tools/mcp_server.py:196-219`,
  `tools/mcp_server.py:333-350`, `tests/test_mcp_server.py:100-106`).
- Replay represents `RecordedTurn.thought`, defaults only missing legacy values to `""`, and sends
  the thought back to the real API (`tools/replay_session.py:20-29`,
  `tools/replay_session.py:81-124`, `tools/replay_session.py:231-244`).
- The queued playtest loader accepts an optional thought, requires at least one of the three
  fields, and forwards all three (`tools/playtest_harness.py:112-145`,
  `tools/playtest_harness.py:214-224`).
- The main README and `tools/README.md` describe the current three-field marker and legacy replay
  fallback accurately (`README.md:501-504`, `README.md:957-994`, `tools/README.md:51-79`).

## Stale wording

- Two frontend comments still say a bubble combines only “speech + action”, while the adjacent
  implementation combines `speech`, `thought`, and `action` (`src/static/app.js:261-263`,
  `src/static/app.js:540-544`).
- Runner docstrings describe grouped history as human “speech/action” and omit thought even though
  the code stores it (`src/runner.py:138-139`, `src/runner.py:579-581`).
- The published closed MCP case calls its legacy fixture “the current format” and lists
  `turn_input`/MCP submission without thought (`docs/cases/tasks/08-debug-mcp-server.md:54-71`).
- The remediation closure similarly describes the then-current marker as containing speech and
  action but not thought (`docs/cases/report-remediation-final.md:18`). This is historical evidence,
  but the wording reads as a current contract rather than a dated limitation.

## Coverage gaps

- None of the maintained JSON scenarios under `tools/playtests/` contains a `thought` property.
  The harness supports it, but live bulk playtests never exercise thought-only or combined
  speech/thought/action turns.
- `tests/test_replay_session.py` verifies the legacy fallback where `thought` is absent, but has no
  marker containing a non-empty thought and therefore no direct regression for preserving it.
- `tests/fixtures/current_replay.debug.jsonl` predates typed thought input. This is intentional and
  documented in `tools/README.md`, but the filename `current_replay` can suggest current three-field
  coverage that the fixture does not provide.
- The debugger's generic `JSON.stringify(e.input)` behavior is correct, but there is no frontend
  regression test asserting that a `turn_input` marker visibly includes a non-empty thought.

## Answer to the original question

The debugger and tools did not remain on an old two-field JSON contract. They already accept,
store, display, and replay all three fields. What is outdated is the explanatory surface around
them and the maintained evidence set: comments/case-study text still mention two fields, while
replay and playtest fixtures do not positively exercise non-empty thoughts.

---

## Resolution Summary

The three-field turn input (`speech`, `thought`, and `action`) was fully resolved and strictly enforced across the debugger and all tools:

1. **Strict Three-Field Contract:** In `tools/replay_session.py`, we removed the legacy compatibility fallback that defaulted missing thoughts to `""`. The validation now strictly asserts the presence and type of the `thought` string key within the logged input payload.
2. **Comment Cleanup:** Stale references to "speech+action" or "speech/action" were updated in frontend comments (`src/static/app.js`) and runner docstrings (`src/runner.py`) to correctly document `speech`, `thought`, and `action`.
3. **Fixture Updates:** The original two-field `current_replay.debug.jsonl` fixture was updated to contain valid `thought` keys in all `turn_input` markers (including a non-empty thought test). The legacy compatibility tape (which lacked thoughts) was completely retired and deleted from git tracking (moved to `/tmp/legacy_replay.debug.jsonl.bak`).
4. **Playtests Enrichment:** Enriched playtest scenarios (`tools/playtests/micro_character_role.json`) to include non-empty thoughts to ensure the playtest harness tests are actively running turns containing thoughts.
5. **Regression Tests:** 
   - Added unit test cases to verify explicit parsing/preservation of the `thought` field (`test_turn_input_markers_recover_thought`).
   - Updated existing test input records to follow the strict three-field schema.
   - Added a static architecture regression check to assert that `app.js` continues to dynamically serialize `e.input` as a whole rather than destructuring it to a subsets of keys.
   - Verified that the entire test suite (169 tests) passes perfectly.
