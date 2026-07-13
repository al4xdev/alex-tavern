# Playtest Partial Results: Gemma 4 26B (MXFP4 MoE)

**Date**: 2026-07-13
**Provider**: `llama_cpp` (local, http://192.168.0.183:8888)
**Model**: `gemma-4-26B-A4B-it.gguf` (Quantization: MXFP4 MoE)

## Overview
This document records the partial validation of a new model loaded via the `llama_cpp` adapter against the Alex Tavern roleplay API and narrative constraints.

> **⚠️ WARNING: PARTIAL RUN**
> The playtest harness execution was paused manually during the `natural-conversation` scenario due to time constraints. The complete playtest suite (especially `stress.json`) needs to be fully run and verified at a later time to ensure full regression coverage.

## 1. Prompt Cache Validation
The `prompt_cache_probe` proved that provider-native prefix reuse is functioning perfectly with this model.

- **Warm Request**: `49.1s` (5330 prompt tokens, 0 cached)
- **Repeat Requests**: `~185ms` (5329 cached tokens out of 5330, 99.98% hit rate)
- **Negative Control**: `48.5s` (0 cached tokens, properly isolated)
- **Status**: Verified

## 2. API and Schema Compatibility
The model flawlessly produced responses matching the required JSON Schemas:
- **Character Responses**: Successfully separated audible `speech` and internal subjective `thought`.
- **Narrator Responses**: Correctly generated `narration`, `next_speaker`, `context_for_character`, `scene_update`, and `mood_updates`.
- **Validation**: Zero JSON decoding errors, zero schema validation failures, and zero prompt leakages detected across all generated outputs in `.debug.jsonl`.

## 3. Narrative Quality and Continuity
Analysis of the `micro_consequence_pov.json` session history demonstrated exceptional factual consistency:
- **Object Permanence**: The Narrator maintained awareness of an empty cup moved by the Player in Turn 1, tracking its state across multiple turns (e.g., rainwater splashing into it in Turn 3, and rippling in Turn 5).
- **Action Duration**: When the Player requested an NPC (Mork) to close a window, the model correctly simulated the duration of the action. It took multiple turns of struggling with the stuck wooden latch rather than resolving instantly.
- **Spatial Tracking**: The Narrator perfectly tracked the Player's spatial location. When the Player walked to the door in Turn 4 and asked "Where am I standing now?" in Turn 5, both the Narrator and the Character (Lyra) accurately referenced the door.
- **Punctuation Rules**: The model rigidly adhered to the prohibition of Unicode em/en dashes, using proper commas and punctuation as instructed.

## Executed Scenarios
1. `micro_character_role.json`: Completed successfully.
2. `micro_consequence_pov.json`: Completed successfully.
3. `natural.json`: Manually cancelled at Turn 11.
4. `stress.json`: Not started.
