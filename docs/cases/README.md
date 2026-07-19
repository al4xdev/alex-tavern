# Alex Tavern Engineering Cases

A numbered series of engineering case studies from Alex Tavern's development,
published as evidence: each article records the problem as it was understood at
the time, the method, the measured results, and what was actually verified.
Every article opens with a metadata block and an abstract; bodies preserve the
original evidence verbatim. Historical articles may describe intermediate
architecture that a later article or closed task supersedes — contract notes
inline mark those places. Active planning lives in [`.plan/`](../../.plan/).

**Method note.** Two disciplines recur through the series and were codified in
`AGENTS.md`: findings are recorded before fixes, and every prompt-level change
is validated by isolated replay on real payloads before it ships — the
validated variant IS the shipped variant, and its position in the prompt is
part of the variant.

## The series

| Nº | Article | One-line finding |
|---|---|---|
| 01 | [From a real playtest to verified remediation](./01-real-playtest-remediation-2026-07-11.md) | The four-stage loop (findings → plan → verified closure → live validation) that became the house method. |
| 02 | [DeepSeek provider integration](./02-deepseek-provider-integration-2026-07-12.md) | Server-owned adapters: the browser never holds credentials; the boundary every later call flows through. |
| 03 | [Adaptability and coupling audit](./03-adaptability-coupling-audit-2026-07-12.md) | The seams the provider migration had to respect, found before the migration. |
| 04 | [Test-suite audit](./04-test-suite-audit-2026-07-12.md) | Deterministic suite + explicitly-marked real-LLM benchmarks, still the suite's shape. |
| 05 | [Local-model baseline: Gemma 4 26B](./05-local-model-baseline-gemma-2026-07-12.md) | The control arm: the failure families that became the engine's structural benchmarks. |
| 06 | [Prompt caching evidence](./06-prompt-caching-evidence-2026-07-12.md) | Versioned positive AND negative cache proof; append-only prompts make the fan-out affordable. |
| 07 | [Multi-character memory retention](./07-multi-character-memory-retention-2026-07-14.md) | The reported bug did not reproduce; the real bug (no information boundary) was worse. |
| 08 | [Speech audience model](./08-speech-audience-model-2026-07-15.md) | Audience-stamped records as the perception substrate, closed by a bias-controlled fixer loop. |
| 09 | [Character output guard](./09-character-output-guard-2026-07-15.md) | Structure over prompt: retry-then-redact makes secret leaks impossible by construction. |
| 10 | [Token economics as an architectural enabler](./10-token-economics-agentic-architecture-2026-07-16.md) | An 89.57% cache-hit ratio is what makes the six-agent fan-out economically rational. |
| 11 | [Roteiro, drive and scene stagnation](./11-roteiro-drive-scene-stagnation-2026-07-17.md) | A concrete disruptive beat breaks a stall 3/3; an abstract instruction 0/3. |
| 12 | [Scene stagnation as absent state transition](./12-scene-state-transition-theory-2026-07-17.md) | The theory: two clocks, material delta, causal contract, recovery ladder — the active program. |

## Reading paths

- **The stagnation program** (active): 11 → 12, then the delivered mechanisms in
  `.plan/tasks/40-narrative-tick-clock.md` (narrative clock + time compression)
  and `.plan/tasks/33b-continuous-roteiro-watcher.md` (material-delta watcher,
  validated by exploration; A/B/C battery in `tools/acceptance/watcher_abc.py`).
- **Confidentiality by construction**: 07 → 08 → 09, then the perception ledger
  and omniscient-Director work in `.plan/closed/` (Tasks 29.2, 35, 39, 41).
- **Provider and cost**: 02 → 05 → 06 → 10.

## Closed-task records referenced by the series

- [`03-docker-validation.md`](../../.plan/closed/03-docker-validation.md)
- [`08-debug-mcp-server.md`](../../.plan/closed/08-debug-mcp-server.md)
- [`09-prompt-caching.md`](../../.plan/closed/09-prompt-caching.md)
- [`11-deepseek-provider-adapters.md`](../../.plan/closed/11-deepseek-provider-adapters.md)
