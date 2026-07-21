# Task 46 — Schema `description` as the primary instruction channel (structured output)

**Status:** 🔵 SHELVED (backlog / design note, 2026-07-20). Large and transverse
rework, **gated behind curl re-validation**. DO NOT start in parts (half
migration = unvalidated state).
**Origin:** observation of the owner (GenAI eng), 2026-07-20.

## The idea

The most reliable channel to guide **structured output** is not the system nor the user prompt,
but rather the `description` fields of the **JSON Schema** passed in the request (property-level,
and the schema-level description). An instruction pasted directly to the exact slot the model is going to
fill is followed more faithfully than the same rule buried in prose inside the system prompt,
and stays **local** to the field it governs.

## Why it matters here

- Today, the *output shape* instruction lives in the system prompt: the watcher's delta taxonomy,
  the appraisal attribution rule, the Character's output constraints,
  and the eligibility of `next_speakers`. Much of this is **per-field** guidance that belongs to the field.
- **Traceability ("track all"):** with the rule in the schema, every constraint is
  enumerable in a single structured place — we can audit/trace what governs each
  output field, instead of prose spread across N system prompts.
- The project **already does this** in one place: `next_speakers` in Task 45 carries
  "Return only character IDs listed in items.enum..." as the field description — the
  pattern that this task generalizes.

## Nuance (honest scope — it's rebalancing, not erasing the system prompt)

- **Schema-description WINS** for: field constraints/format, enum semantics,
  per-slot do/don't, output shape (delta categories; appraisal
  direction/attribution; next_speakers eligibility; speech/thought split).
- **System still carries**: global persona/role, task framing,
  confidentiality invariants, and reasoning not tied to a single slot.

## The cost that makes this backlog, not now

- Moving the instruction load changes the effective prompt of **every** structured agent. The
  house rule is **"the validated variant IS the shipped one"** — so this breaks the
  curl-validated state of each: watcher delta (4/4), appraisal (4/5), Character output guard,
  screenplay beat, prose, narrator, disposition band.
- Each migrated schema needs to **re-run its curl gate** proving that the schema-variant
  ≥ system-variant in that metric. It is a re-validation campaign, not a simple reflow.
- Therefore: **no piecemeal migration.** Either it is a deliberate and budgeted campaign with
  per-agent A/B (system-variant vs schema-variant, blind gate), or it is not.

## Active pilots (where the technique proves cheap)

**Task 45 (`next_speakers`)** is the most natural pilot: narrator.py:219-224 already proved
that the **hard enum** breaks (validator rejects), but the **field `description`** was never
tested. The gate for 45 is a ready A/B — baseline (prosa in user message) vs
variant (per-beat description naming the ineligible), measuring structural validity,
honored exclusion, and fewer dropped slots. See `.plan/tasks/45`.

## Proposed cheap pilot (first low-risk step)

The **disposition/appraisal** schema (`build_appraisal_schema`) is new, has empty
`description` fields, and its gate costs ~20 curl calls
(`scratchpad/exp_disposition_appraisal.py`). Migrating the attribution rule and the
"most turns shift nothing" discipline from system prompt to the `description` of the fields there, and
re-running the gate (≥4/5, same threshold), **proves or kills the lift** without touching any
other agent. If the pilot shows gains, then decide on the campaign.

## Acceptance Criteria (draft — freeze when starting)

- [ ] Inventory of all structured output schemas; classify each system instruction as
  **field-local (movable)** vs **global (remains)**.
- [ ] Per agent, curl A/B gate: schema-variant vs current, pre-registered; the
  schema-variant must be ≥ the current one in that agent's existing metric.
- [ ] Traceability output: a registry listing, per output field, the description
  governing it (the "track all" gain).
- [ ] No confidentiality regression (moving text to schema must not leak
  screenplay/secrets in a viewer's structured call).
- [ ] README/AGENTS documents schema-description as the canonical channel for field-local
  guidance.

## Out of Scope

- Moving global persona/framing or confidentiality invariants to the schema.
- Any migration without the per-agent re-validation gate of that prompt.
- Rewriting already shipped prompts "for elegance" without proving the lift via curl.
