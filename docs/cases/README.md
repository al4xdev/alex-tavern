# Engineering case studies

This directory preserves completed investigations, implementation plans, validation reports, and
case studies from Alex Tavern's development. They are published as engineering evidence: each
case records the problem as it was understood at the time, the decisions taken, and what was
actually verified. Active planning and tasks are tracked in the [`.plan/`](../../.plan/) directory.

Historical plans may describe intermediate architecture that a later closure report supersedes.
Use each case's final report or closed-task record as its outcome, and the current README/source as
the product contract.

## Report remediation

- [`report.md`](./report.md): original real-session findings preserved as evidence.
- [`report-remediation-plan.md`](./report-remediation-plan.md): execution plan derived from the
  original report.
- [`report-remediation-final.md`](./report-remediation-final.md): verified closure of the six
  objective defects and qualitative mitigations.
- [`explore-live-playtest-2026-07-12.md`](./explore-live-playtest-2026-07-12.md): post-remediation
  live exploration.

## Memory and narrative continuity

- [`multi-character-memory-retention-2026-07-14.md`](./multi-character-memory-retention-2026-07-14.md):
  controlled reproduction attempt of a reported multi-character recall loss under alternating
  narrative focus; the reported defect did not reproduce, and the experiment confirmed the absence
  of an information boundary plus a latent trim/compaction gap. Follow-up work is tracked in
  `.plan/tasks/22-*` through `26-*`.
- [`speech-audience-model-2026-07-15.md`](./speech-audience-model-2026-07-15.md):
  the remediation — witnessed actions (Task 24) and a whisper/audience model for speech
  (Task 22), validated by two-level recall assertions, blind continuity review, and a
  bias-controlled loop of uncontexted fixer subagents (2 cycles). Pipeline leak-free at
  closure; behavioral residuals routed to Tasks 25/26.
- [`character-output-guard-2026-07-15.md`](./character-output-guard-2026-07-15.md):
  Task 25 — the deterministic output guard (retry-then-redact) that made secret
  handling structural instead of prompt-based, with informational-payload secret
  derivation and a whisper-turn marker designed by an uncontexted fixer agent. Zero
  record-level leaks across all measured runs; residuals routed to Task 26.

## Provider architecture and model evaluation

- [`deepseek-provider-integration-2026-07-12.md`](./deepseek-provider-integration-2026-07-12.md):
  DeepSeek discovery, adapters, security, E2E, and Gemma comparison.
- [`explore-adaptability-coupling-audit-2026-07-12.md`](./explore-adaptability-coupling-audit-2026-07-12.md):
  architecture audit plus final remediation closure.
- [`playtest-suite-gemma-baseline-2026-07-12.md`](./playtest-suite-gemma-baseline-2026-07-12.md):
  controlled local-model baseline.

## Prompt caching

- [`09-prompt-caching.md`](./09-prompt-caching.md): versioned positive and
  negative cache proof for DeepSeek and llama.cpp, including raw usage counters and limitations.
- [`token-economics-agentic-architecture-2026-07-16.md`](./token-economics-agentic-architecture-2026-07-16.md):
  provider-billing case study showing how a 96.79% input cache-hit ratio changed the economic
  trade-off for explicit Director, Prose, Character, Perspective, Historian, and Drive boundaries;
  includes the no-cache counterfactual, limitations, and the V1.0 update protocol.

## Test architecture

- [`explore-test-suite-audit-2026-07-12.md`](./explore-test-suite-audit-2026-07-12.md): test
  redundancy, stochastic-test replacement, and maintained harness findings.

## Closed tasks

- [`03-docker-validation.md`](../../.plan/closed/03-docker-validation.md): clean Docker build,
  non-root runtime, and writable mounted-data validation.
- [`08-debug-mcp-server.md`](../../.plan/closed/08-debug-mcp-server.md): MCP debugging and deterministic replay.
- [`11-deepseek-provider-adapters.md`](../../.plan/closed/11-deepseek-provider-adapters.md): server-owned
  multi-provider adapters and DeepSeek V4 Flash.
- [`09-prompt-caching.md`](../../.plan/closed/09-prompt-caching.md): provider-native prompt caching.
