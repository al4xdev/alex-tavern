# Durable-state growth boundary result

Date: 2026-09-21

## Decision

On the tested current-schema save/load path, 41 durable physical entities
survive without eviction. The persistence test registers those entities, saves
the game through the real atomic session store, loads it again and requires the
exact 41 entity IDs to survive.

This addresses the stated eviction risk at the descriptive `physical_facts`
bag's historical 40-key boundary for physical entities. It is not evidence that
arbitrary growth is free or that every durable entity should enter a prompt.

## Test

`test_authoritative_store_persists_beyond_the_descriptive_fact_cap`:

1. creates a current-schema `GameState`;
2. registers 41 unique scene-owned structure fixtures in
   `GameState.durable_state.physical_entities`;
3. persists the complete game with `save_game`;
4. loads it through `load_game` and current-schema validation;
5. asserts both count 41 and exact ID-set equality;
6. deletes the isolated test session.

The count is deliberately one above `_MAX_PHYSICAL_FACTS = 40`, the cap whose
eviction motivated the original checklist item. The test would fail if durable
state were routed through that bag or later acquired the same cap.

## Scope

The durable-state interface separately specifies bounded prompt projection as a
read concern. Prompt projection may bound what a model sees, but must not delete
authoritative state. This test exercises persistence, not prompt projection.

The test establishes save/load preservation at the historical cap boundary. It
does not measure process memory, large-manifest latency, runtime registration or
a maximum practical entity count.

## Validation

- `uv run pytest -q tests/test_durable_state.py`: 47 passed;
- `uv run pytest -q`: 1,191 passed, 2 LLM tests deselected and the existing
  FastAPI `TestClient` deprecation warning;
- `uvx ruff check tests/test_durable_state.py`: passed;
- `uvx ruff format --check tests/test_durable_state.py`: passed.
