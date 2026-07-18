# Plugin ecosystem topology — exploration ADR (Task 27)

**Status:** exploration only. This document records direction and decisions; it
authorizes **no** repository creation, source move, package publish, GitHub App,
secret, or CI/CD change (Task 27 §15 non-goals). It must be reviewed and
accepted before Task 06 (RAG) source work begins.

Grounded in the checkout at 2026-07-17 (`src/plugins/` ~2850 LOC,
`src/static/plugin-runtime.js`, `tools/plugin_author.py`) plus Task 27 §4
findings. Where the external `alex-tavern-plugins` hub is needed and not checked
out here, that is flagged as **verify-before-implementation**.

---

## 1. Repository topology ADR (deliverable 1)

Five authorities, one source of truth per contract:

| Repo | Owns | Must NOT become |
|---|---|---|
| `alex-tavern` (this repo) | Runtime, browser runtime, provider adapters, the **authoritative plugin contract source** (`src/plugins/contracts.py::exported_contract`), integration tests | A home for individual plugin source |
| `alex-tavern-plugin-sdk` | **Published** SDK: the exported contract JSON, public schemas/types, author docs, authoring MCP, scaffold/validate/test/pack CLI, reusable CI blocks | A second runtime implementation or a hand-edited copy of the contract |
| `alex-tavern-plugin-template` | GitHub template: example plugin, tests, CI, `dev`/`prod` flow, `AGENTS.md` | The SDK, the catalog, or a repo edited in place |
| `alex-tavern-plugins` (hub) | Curated intake, review evidence, catalog, pinned release identity, artifacts/advisories | The source monorepo for all plugins |
| Individual plugin repo | The plugin's authoritative source, tests, releases | A fork that must copy SDK/hub internals |

**Decision:** the contract's single source of truth is
`exported_contract()` in core. The SDK repo **publishes a generated snapshot**
of it (never a hand-maintained copy). Drift is caught by a check that
regenerates the snapshot from a pinned core commit and diffs it (deliverable 2).

---

## 2. SDK extraction inventory (deliverable 2)

Real surface in this checkout, classified:

| Item | Location | Disposition |
|---|---|---|
| `exported_contract()` (hooks, slots, services, settings, commands, permissions, crash policy) | `src/plugins/contracts.py` | **Generated** → SDK publishes the JSON; core stays the source |
| Manifest/Experience schemas | `src/plugins/manifest.py` | **Move public schema to SDK**, generated from core; validation logic stays where core needs it |
| Hook kinds/registry types | `src/plugins/hooks.py` | Public **types/enum** → SDK; the `HookRegistry` runtime stays core |
| `PluginContext` author-facing API (`config`, `storage`, `http`, `model`, `register/contribute/command`) | `src/plugins/sdk.py` | Public **interface/typestubs** → SDK; the concrete impl (esp. `unsafe`/runtime binding) stays core |
| Browser SDK | `src/static/plugin-runtime.js` | Public **types + loader interface** → SDK; the runtime host stays core |
| Authoring CLI | `tools/plugin_author.py` (consumes `exported_contract()`) | **Move to SDK** as the scaffold/validate/test/pack tool; drop the `--core-root` requirement by shipping the generated contract |
| Store/hub/runtime/experiences/commands | `src/plugins/{store,hub,runtime,experiences,commands}.py` | **Stay core/curator** (install, activation, crash policy, Experiences) — not author-facing |

**Single-source rule:** every generated artifact (contract JSON, manifest
schema) has exactly one input (core) and a drift check that fails loudly. The
SDK never hand-edits a contract; it regenerates.

**Answer to §7 key questions:** core does NOT depend on a released SDK package
(core is upstream); the SDK is generated FROM core at a pinned commit. Ordinary
plugin dev needs only the SDK (generated contract + typestubs + MCP), not a full
core checkout; a live core checkout is needed only for **integration** tests
against a specific core version (opt-in fixture).

---

## 3. Developer journey (deliverable 3)

```
Use the template  ->  develop on dev  ->  promote to prod  ->  curation PR to hub
```

1. **Template:** GitHub "Use this template" (or an SDK CLI equivalent). New repo
   has an example plugin, tests, manifest, CI, `AGENTS.md`, `dev`/`prod`.
2. **dev:** ordinary pushes/PRs to `dev` run validate + tests + SDK conformance
   + permission/dependency report + deterministic pack (as a non-published
   artifact). **dev CI never submits or publishes.**
3. **prod:** a reviewed PR `dev`→`prod` is the promotion boundary. Production
   readiness = monotonic SemVer, exact manifest id/version, passing conformance,
   permission/dependency diff, deterministic artifact + SHA-256, pinned source
   commit, provenance for independent rebuild.
4. **Curation PR:** automation opens a PR in the hub (author never gets hub write
   access). The PR is a request for human review — no green check grants curated
   status.

---

## 4. Template repository spec (deliverable 4)

Contents: `AGENTS.md` (SDK discovery + safety rules), human README, canonical
`plugin.toml` placeholders, backend + optional frontend entrypoint examples,
unit + contract test examples, `.gitignore` for `.data/`/secrets/caches, `uv`
project metadata, `dev`/`prod` docs + protection guidance, CI for
validate/test/pack on `dev`, promotion checks into `prod`, a protected/manual
curation-submission workflow, version/changelog/issue/PR templates,
permission/dependency + SHA-256 reporting, SDK-pin update automation.

Must NOT contain: a copied private core SDK, live secrets, owner tokens,
hardcoded maintainer identity, or an over-privileged workflow.

**Template descendants** do not auto-update: ship security/workflow updates as
**reusable workflows referenced by tag** + optional update PRs; never a hidden
compatibility layer.

---

## 5. Author CI contract (deliverable 5)

`dev`: manifest/schema validation, backend + frontend syntax, plugin-local
tests, SDK conformance tests, permission/dependency report, deterministic pack
(unpublished), secret/`.data`/cache leak check, optional integration fixtures
against declared core versions.
`prod`: the above + SemVer monotonicity + manifest id/version agreement +
artifact SHA-256 + pinned source commit + provenance.

---

## 6. Submission protocol (deliverable 6)

A strict, forward-only submission descriptor (verify exact schema before
implementation) identifying: plugin id + version, source repo + **immutable
commit** (reject mutable branch refs), release/tag identity, declared SDK/core
compatibility, artifact location + expected hash (if author-built), manifest +
permissions + dependencies + entrypoints + Python deps, test command/evidence,
previous curated release, changelog + review notes, media/Experience relations,
author/maintainer identity + license.

**PR creation mechanism (compare, pick least privilege):** SDK CLI that forks
the hub + pushes a branch to the author's fork + opens a PR (ordinary token,
no hub write) **[preferred default]**; vs a narrowly-scoped GitHub App; vs a
central intake workflow on a signed descriptor; vs a manual command that emits
the exact PR payload when cross-repo automation is not authorized. Unrelated
repos cannot open a cross-repo PR merely by pushing — the PR targets shared hub
history through a hub fork/branch or an authorized app.

---

## 7. Curator pipeline (deliverable 7)

Independent verification, never trusting author CI: parse the strict descriptor
→ reject mutable refs → checkout the exact pinned commit → validate manifest
against the supported contract → inspect permission/dependency diffs → run
syntax + contract tests in an **ephemeral env without curator secrets** →
full-source human review → **deterministically rebuild** from reviewed source →
compare author artifact to curator-built artifact → record final
`id/version/hash/source-commit` → update catalog only after approval/merge →
preserve review provenance without an independently editable source copy.

---

## 8. Supply-chain threat model (deliverable 8)

Primary threats and mitigations:

- **Untrusted code with secrets** → never `pull_request_target` on plugin source
  with hub secrets; run author code only in ephemeral, secret-less envs.
- **Broad credentials** → authors never hold a curator token; prefer hub-fork +
  ordinary token or a narrowly-scoped App. Least privilege over convenience.
- **Mutable refs / re-used versions** → require immutable commit + monotonic
  SemVer + content hash; reject branch-only refs and version reuse with new
  content.
- **Dependency confusion / malicious deps** → pin + review Python deps; test
  without giving setup code secrets or privileged runners.
- **Action pinning drift** → pin third-party Actions by SHA.
- **Workflow injection** from plugin-controlled strings/filenames/manifests →
  never interpolate untrusted strings into shell; treat all descriptor fields as
  data.
- **Auto-merge confused with auto-submit** → submission ≠ approval; human review
  mandatory; no green check grants curated status.
- **Self-hosted runner risk** → no privileged runner executes unreviewed source.

---

## 9. Distribution decision (deliverable 9)

The app today syncs a catalog + relative artifacts from the curated hub.
**Decision (verify-before-implementation):** the hub stores the
**curator-rebuilt deterministic ZIP** as the distributed artifact plus metadata
pointing to the immutable source commit; author-built artifacts are compared but
not trusted as the distributed bytes. External artifact URLs / GitHub Releases /
content-addressed caches are a **later** contract change, not assumed solved by
moving source.

---

## 10. Agent + documentation migration (deliverable 10)

Files to update atomically at cutover (inventory): main `AGENTS.md` §"Workspace
do hub para agentes" (currently tells agents to clone `../alex-tavern-plugins`
and write source under its `plugins/`), main README plugin section,
`tools/README.md`, hub `AGENTS.md`/README, SDK `AGENTS.md`/docs/MCP, template
`AGENTS.md`/workflows, MCP client config examples, curated plugin READMEs
pointing at hub-local authoring paths.

Target agent flow (replaces the hub-local one, forward-only, no transitional
"write to old hub for compatibility"):

```
Request to create a plugin from alex-tavern
  -> inspect core tasks + live contract (exported_contract)
  -> locate/clone the isolated SDK (pinned release)
  -> use SDK docs + authoring MCP (no --core-root; contract is shipped)
  -> create/enter an independent plugin repo from the template
  -> develop + test there
  -> submit to the hub only via an explicitly authorized curation operation
```

---

## 11. Existing plugin migration map (deliverable 11)

For each current hub plugin (`character-converter`,
`dynamic-character-presence`, `grammar-tools`, `openrouter-provider`): assign one
future authoritative repo + maintainer + license + SDK target + test/release
workflow + immutable source commit recorded by the hub + artifact rebuild/hash
continuity + Experience/catalog/media relations + issue/history preservation +
removal of the hub-local source path after cutover. **Forward-only: never keep a
hub-local source copy and an external authoritative copy as two editable trees.**
(Exact per-plugin decisions require the hub checkout — verify-before-migration.)

---

## 12. RAG + Celestial readiness (deliverables 12–13)

- **RAG gate:** RAG (Task 06) must be creatable in its own repo from the template
  and reach a reviewable curation PR using only public SDK/template mechanisms —
  no exception that keeps the old topology alive. RAG then serves as the
  demanding reference consumer (background work, deps, storage — now real via
  Task 21, model calls, commands, context privacy, tests, artifacts, curation).
- **Celestial:** `alex-tavern-celestial` (S02) becomes an ordinary first-class
  SDK/template consumer, not a privileged exception; the SDK/submission design
  must carry the full dependency closure (a plugin depending on Celestial) with
  compatibility constraints, permissions, and exact release hashes shown to
  reviewer and installer.

---

## 13. Decision register (deliverable 14)

| Decision | Choice | Rejected / open |
|---|---|---|
| Contract source of truth | core `exported_contract()`; SDK publishes a generated snapshot | Rejected: hand-maintained SDK copy (drift) |
| Core↔SDK dependency direction | SDK generated FROM core at a pinned commit | Rejected: core depends on released SDK (cycle) |
| Full core checkout for dev | Not required; SDK ships the contract | — |
| PR mechanism | Hub-fork + ordinary token (default); App if needed | Open: App vs central intake — verify |
| Distributed artifact | Curator-rebuilt deterministic ZIP | Open: external URL / content-addressed — later |
| `dev`/`prod` | Recommended convention with configurable branch names | Open: strict protocol vs configurable |
| Cutover | Forward-only, no transitional hub-local write | — |

**Unresolved (need the hub checkout / owner decision):** exact submission
descriptor schema; App vs fork-token final call; artifact hosting; per-plugin
migration owners; where the authoring MCP finally lives.

---

## 14. Implementation decomposition (deliverable 15) — AFTER review

Only once this exploration is accepted, in order:
1. Contract-snapshot generator + drift check in core (no new repo yet).
2. SDK repo scaffold from the generated snapshot + typestubs + MCP (authorized
   separately).
3. Template repo (authorized separately).
4. Author CI + submission descriptor + curator pipeline.
5. Migrate existing plugins forward-only.
6. RAG as the first template-native plugin.

---

## 15. Acceptance status (Task 27 §14)

Exploration deliverables 1–15 drafted above. Items still requiring the external
hub checkout or an owner decision are flagged **verify-before-implementation** /
**open** (submission descriptor schema, PR-mechanism final call, artifact
hosting, per-plugin migration owners). **No repository, workflow, package,
token, PR, release, or source move was created by this exploration** (§15
non-goals honored).
