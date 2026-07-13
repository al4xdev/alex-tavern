# Engineering case studies

This directory preserves completed investigations, implementation plans, validation reports, and
task closures from Alex Tavern's development. They are published as engineering evidence: each
case records the problem as it was understood at the time, the decisions taken, and what was
actually verified. Active planning and unfinished scratch work remain private under `.plan/`.

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

## Test architecture

- [`explore-test-suite-audit-2026-07-12.md`](./explore-test-suite-audit-2026-07-12.md): test
  redundancy, stochastic-test replacement, and maintained harness findings.

## Closed tasks

- [`03-docker-validation.md`](./03-docker-validation.md): clean Docker build,
  non-root runtime, and writable mounted-data validation.
- [`08-debug-mcp-server.md`](./08-debug-mcp-server.md): MCP debugging and deterministic replay.
- [`11-deepseek-provider-adapters.md`](./11-deepseek-provider-adapters.md): server-owned
  multi-provider adapters and DeepSeek V4 Flash.
