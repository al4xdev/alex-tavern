---
name: memory-playtest
description: Runs the multi-character memory playtest (alternating X/Y/Z narrative focus) against a real LLM, locates losses layer by layer, and has a clean subagent judge the narrative as a screenwriter. Use when the user asks to test memory retention, fact recall, cross-character leakage, or narrative continuity in long sessions.
---

# Memory playtest — full flow

Four stages: run the scenario against the real LLM → locate losses by layer →
render the script → narrative evaluation by a subagent **with no inherited
context**. Each run's artifacts are the evidence; never delete them.

## 1. Run the playtest

```fish
uv run python -m tools.playtest_harness tools/playtests/memory_focus_xyz.json \
  --config-file .data/config.json --language Portuguese --llm-timeout 120 \
  --model-label memoria-xyz --repeat 1 --output-dir <RUN_DIR>
```

Available scenarios:
- `tools/playtests/memory_focus_xyz.json` — retention under alternating focus + isolation checks (checks 2/3 fail until Task 22 exists; that is expected).
- `tools/playtests/memory_action_fact.json` — a fact that enters only through the `action` field (a scroll shown and burned); Task 24's acceptance.

- `<RUN_DIR>` must be a new directory (the harness refuses existing directories and anything inside `.data/`). Use the session scratchpad or `plans/artifacts/<name>-runN`.
- Long runs: execute in the background and wait for the completion notification.
- Exit ≠ 0 is expected when a required `recall_check` fails — that IS the result, not a harness defect.
- Read `runs[].events[].recall` in `playtest-results.json`: `prompt_passed` false = loss before the provider (state/selection/prompt); `prompt_passed` true with `reply_passed` false = the model failed to recall.
- `invariant_violations` must be empty — that is the proof there was no compaction, no presence edit and no participant swap mid-session.
- Model recall is stochastic: to claim "reproduced / did not reproduce", use `--repeat 2..3` and compare the checks across repetitions.

## 2. Locate losses layer by layer

```fish
uv run python -m tools.analyze_memory_run <RUN_DIR> \
  --marker "ORQU[ÍI]DEA-741" --marker "GIRASSOL-222"
```

Layers: 1 STATE (persisted history) → 2 SELECTION (content_type filter + trim, recomputed offline) → 3 PROMPT (the real requests in `debug.jsonl`) → 4 REPLY (what the character actually said). The first layer where the marker disappears is where the loss lives; the fix belongs to that layer only.

## 3. Render the script

```fish
uv run python -m tools.render_transcript <RUN_DIR> --out <TRANSCRIPT.md>
```

Produces a readable script (narration, dialogue, actions and private thoughts marked) with no leakage of code, prompts or config — it is the only material stage 4's subagent may receive.

## 4. Narrative evaluation by a clean subagent

Launch a **fresh** `general-purpose` subagent (never `SendMessage` an existing agent — the evaluator must have no inherited context). Inviolable prompt rules:

- Hand over ONLY: the transcript path and a short description of the expected scenario (e.g. "three characters in a tavern; Dario entrusts a password to Vela early on, the conversation drifts at length toward Rook with several codes, and at the end Dario tests what both remember").
- FORBIDDEN: inspecting code, tests, plans, earlier analyses, configs or any file beyond the transcript; modifying files; proposing an implementation or a technical fix.
- Role: screenwriter / continuity editor reading the scene as an ordinary reader.
- The written report must answer:
  1. Do the characters recall earlier events naturally?
  2. Does each one's behaviour stay consistent?
  3. Does any character show knowledge they should not have?
  4. Do facts, names, codes, relationships or motivations get confused at any point?
  5. Does the conversation read as continuous across the narrative focus switches?
  6. Is there any strange discontinuity an ordinary reader would notice?

## 5. Consolidate

Report to the user in a single summary: the `recall_checks` outcome (keeping the prompt×reply distinction), the per-marker layer table, the invariants, and the subagent's report. An isolation failure (one pair's secret appearing in the prompt of the other character present) is current behaviour by design — every `speech` is public among those present; log it as a product question, not a regression.
