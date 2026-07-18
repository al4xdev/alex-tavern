# Task 27: Isolated Plugin SDK, Repository Topology, and Curated Submission Pipeline

**Status:** Open architectural exploration  
**Execution order:** Must be explored and accepted before Task 06 (RAG) implementation begins  
**Numbering rule:** `27` is only the next append-only task identifier; it does not express priority  
**Created:** 2026-07-15

> [!IMPORTANT]
> This task records a repository and ecosystem direction, but does not authorize creating
> repositories, moving source, publishing packages, installing GitHub Apps, adding secrets, or
> changing CI/CD. The first phase is exploration because the current core, hub, authoring MCP, SDK,
> documentation, artifacts, and curated plugin source are still coupled.

## 1. Intent

Separate plugin authorship from the curated hub before building the RAG plugin.

The intended ecosystem has four distinct concerns:

1. Alex Tavern core owns the runtime and generic plugin contract.
2. An isolated SDK repository teaches humans and coding agents how to build against that contract.
3. A plugin template repository gives another developer a ready-to-use GitHub project with
   development, promotion, validation, packaging, and curation-submission automation.
4. The existing `alex-tavern-plugins` repository becomes the curated review and distribution
   boundary rather than the default working tree in which every author writes plugin source.

Each real plugin should have an authoritative source repository owned by its author or maintainer.
When the author considers a release production-ready, automation should prepare a pull request for
curation in the Alex Tavern hub. Human curation remains mandatory; the pipeline submits evidence,
not approval.

The initial branch convention to investigate and document is:

- `dev`: active development and ordinary iteration;
- `prod`: reviewed, releasable plugin state;
- promotion from `dev` to `prod`: the boundary that can trigger or enable a curated submission.

The official template should make this path easy for a new developer. The platform should still
decide whether branch names are a strict protocol, a recommended convention, or configurable
inputs to reusable automation.

## 2. Why this must precede RAG

Task 06 is expected to be the first large plugin developed through the mature author workflow. The
RAG implementation will exercise background work, dependencies, storage, model calls, slash
commands, context privacy, tests, artifacts, and curation. Beginning it inside the current hub
layout would teach the wrong source ownership and create migration work immediately afterward.

Before RAG source work begins, this exploration must determine:

- where a new plugin repository comes from;
- which SDK version and live core contract it targets;
- how humans and coding agents scaffold and validate it;
- how its CI creates deterministic evidence;
- how a production release becomes a curation PR;
- how the curator independently verifies rather than trusts author-generated output;
- where the final artifact, source reference, catalog record, and review history live.

RAG should then serve as a demanding reference consumer of the new workflow, not as an exception
that keeps the old topology alive.

## 3. Repository roles under exploration

Names other than existing repositories are provisional.

| Repository | Intended authority | Must not become |
|---|---|---|
| `alex-tavern` | Core runtime, browser runtime, provider adapters, authoritative current plugin ABI/contract, and integration tests | A home for individual plugin source or duplicated authoring docs |
| `alex-tavern-plugin-sdk` | Versioned public SDK distribution, schemas/types, author documentation, CLI/MCP authoring tools, test harnesses, migration notes, and reusable CI building blocks | A second implementation of the Alex Tavern runtime or a stale copy of core contracts |
| `alex-tavern-plugin-template` | GitHub template for new plugin repositories, ready CI/CD, `dev`/`prod` workflow, example source/tests, and agent instructions | The authoritative SDK, a curated catalog, or a repository developers edit in place |
| `alex-tavern-plugins` | Curated intake, review evidence, catalog, pinned release identity, Experiences, media, advisories, and possibly content-addressed artifacts | The source-development monorepo for all community plugins |
| Individual plugin repository | The plugin's authoritative source, history, tests, documentation, issues, releases, and maintainer workflow | A fork that must manually copy SDK or hub internals |

Known future examples of individual repositories include provisional `alex-tavern-celestial` and
whatever repository is chosen for the RAG plugin. Third-party developers use their own GitHub
namespace and do not need direct write access to the curated hub.

The exploration must preserve one source of truth for every contract and release. A repository
split that requires humans to synchronize the same source file among core, SDK, template, hub, and
plugin repositories is not acceptable.

## 4. Current-state findings

These findings describe the checkouts on 2026-07-15 and must be refreshed before implementation.

### 4.1 The hub currently owns too many roles

`alex-tavern-plugins` currently contains:

- curated plugin source under `plugins/`;
- deterministic ZIP files under `artifacts/`;
- Experience manifests and media;
- `catalog.json`;
- author documentation;
- an authoring MCP server;
- a repository-wide validation script;
- its own Python environment and test tooling.

Its README explicitly says plugin source, catalog metadata, authoring documentation, examples,
artifacts, and MCP all live together. Its `check.py` locates source beside every catalog artifact
and rejects source/catalog/artifact drift. That is coherent for the current small curated set but
does not represent author-owned independent repositories.

### 4.2 Core is the current SDK source of truth

The backend SDK and contracts live in `src/plugins/`; the browser SDK lives in
`src/static/plugin-runtime.js`; authoring commands live in `tools/plugin_author.py`. The hub MCP
imports those objects from a supplied core checkout through `--core-root`.

The exploration must distinguish:

- runtime implementation that necessarily remains integrated with core;
- public types, protocols, schemas, clients, fixtures, and authoring tools that can be released as
  an isolated SDK;
- generated/exported contract material whose source remains core;
- documentation and examples that should move rather than be copied.

"Isolate the SDK" must not create two independently edited implementations of the same ABI.

### 4.3 Agent instructions currently point authors into the hub

The main `AGENTS.md` and README currently tell an agent to clone
`../alex-tavern-plugins`, read its docs, run its MCP with the main checkout as `--core-root`, and
place authored source under the hub's `plugins/` directory. The hub `AGENTS.md` assumes the same
co-located source/artifact model.

That workflow must eventually be replaced forward-only. Coding agents asked from the main repo to
create a new plugin should use the isolated SDK and create or enter an independent plugin repo. They
should not edit the curated hub until performing an explicitly authorized curation-submission or
review operation.

### 4.4 Current GitHub automation is core-only

The main repository has test, Android, and Docker workflows. The hub checkout currently has no
maintained GitHub workflow tree visible in the sparse/full working copy. There is no reusable
author-repository workflow that validates a plugin, promotes `dev` to `prod`, proves deterministic
packaging, or opens an unrelated cross-repository curation PR.

## 5. Target developer experience

The task must specify a workflow comfortable for a developer who does not know Alex Tavern's core
layout.

### 5.1 Start from the template

1. The developer selects **Use this template** on `alex-tavern-plugin-template`, or uses an SDK CLI
   command that creates an equivalent repository.
2. The new repository contains a small example plugin, tests, manifest, README, license choice,
   changelog/release guidance, CI/CD, and an `AGENTS.md` written for coding agents.
3. The template initializes or documents `dev` and `prod`, branch protection, and promotion rules.
4. The author replaces example identity and source without copying anything from the curated hub.

The template's `AGENTS.md` should tell Claude Code, Codex, and other coding agents to:

- read the plugin repo's own instructions and open tasks first;
- locate a sibling isolated SDK checkout or clone the exact supported SDK release when absent;
- query the appropriate machine-readable contract before choosing hooks or services;
- use SDK-provided scaffold/validate/test/pack tools rather than copying an old plugin;
- keep plugin source in the current plugin repository;
- treat the core and hub as read-only unless a separate task explicitly authorizes changes;
- never commit, push, create releases, open PRs, or add secrets without user authorization;
- record which SDK/core compatibility target was used.

The precise clone URL, pinning mechanism, directory name, and MCP startup command belong to the
exploration because the SDK repository does not yet exist.

### 5.2 Develop on `dev`

The recommended template flow should make ordinary pushes and pull requests targeting `dev` run:

- manifest and schema validation;
- backend and frontend syntax checks;
- plugin-local tests;
- SDK conformance tests;
- permission and dependency reporting;
- deterministic packaging as a non-published CI artifact;
- checks that no secret, `.data/`, local environment, or generated cache entered Git;
- optional integration fixtures against declared supported core versions.

Development CI must not open curation PRs or publish production artifacts.

### 5.3 Promote to `prod`

The intended promotion boundary is a reviewed PR from `dev` to `prod`. Investigation must settle
whether submission occurs on merge, release tag, GitHub Release, or an explicit manually approved
workflow on `prod`.

Production readiness should include:

- a monotonic SemVer change;
- exact manifest ID/version agreement;
- passing tests and conformance checks;
- permission, dependency, and compatibility diffs from the previous release;
- deterministic artifact and SHA-256;
- pinned source commit;
- release notes and review-relevant media when required;
- provenance sufficient for the hub to rebuild and compare independently.

### 5.4 Submit for curation

Automation should prepare a PR in the curator's `alex-tavern-plugins` repository without granting
the author direct hub write access. Candidate mechanisms to compare include:

- an SDK CLI that forks the hub, writes one submission descriptor, pushes a branch to the author's
  fork, and opens a PR;
- a reusable GitHub Action backed by a narrowly scoped GitHub App;
- a central intake workflow triggered by a signed/pinned release descriptor;
- a manual command that produces the exact PR payload when cross-repository automation is not
  authorized.

Unrelated Git repositories cannot create a normal cross-repository PR merely by pushing their
plugin branch: the PR must target shared hub history through a hub fork/branch or an authorized app.
The documentation must explain the real mechanism and credential boundary.

The submission should identify, at minimum:

- plugin ID and version;
- source repository and immutable commit;
- release/tag identity;
- declared SDK/core compatibility;
- artifact location and expected hash, if author-built artifacts are included;
- manifest, permissions, dependencies, entrypoints, and Python dependencies;
- test command/evidence;
- previous curated release when updating;
- changelog and review notes;
- media or Experience relationships when applicable;
- author/maintainer identity and source license.

The PR is a request for human curation. No passing workflow, branch name, badge, signature, or
author release automatically grants curated status.

## 6. Curator-side verification

The hub must independently verify submissions rather than treating author CI as trusted evidence.
Explore a review pipeline that:

1. parses a strict forward-only submission descriptor;
2. rejects mutable branch-only references;
3. fetches or checks out the exact pinned source commit;
4. validates the manifest against the supported SDK/core contract;
5. inspects dependency and permission changes;
6. runs syntax and contract tests in an ephemeral environment without curator secrets;
7. performs full-source human review for the exact release;
8. packs the plugin deterministically from reviewed source;
9. compares any author artifact to the curator-built artifact;
10. records the final `id/version/hash/source-commit` identity;
11. updates the catalog only after approval and merge;
12. preserves review provenance without copying an independently editable source tree.

The exploration must determine whether the hub stores:

- the final deterministic ZIP directly;
- a content-addressed release asset fetched from the plugin repository;
- an archive rebuilt and published by curator automation;
- only metadata pointing to an immutable external artifact;
- or a deliberately chosen combination.

The application currently synchronizes a catalog and relative artifacts from the curated hub.
External artifact URLs, GitHub Releases, multiple catalogs, and content-addressed caches may require
core/hub contract changes. Do not assume distribution is solved merely because source moved.

## 7. Isolated SDK boundary

The exploration must produce an exact inventory of what moves to or is published from the isolated
SDK repository.

Candidate SDK contents include:

- versioned manifest and contribution schemas;
- public backend protocols/types safe for plugin imports;
- browser SDK types and author-facing interfaces;
- machine-readable hook, service, permission, settings, command, workspace, and dependency
  contracts;
- documentation for manifests, hooks, model calls, frontend integration, testing, and curation;
- scaffolding templates;
- validation, test, trace, and deterministic pack commands;
- the authoring MCP server;
- reusable GitHub Actions or scripts consumed by template/plugin repositories;
- compatibility fixtures and example plugins;
- release/migration notes.

Questions that must be resolved:

- Does core depend on a released SDK package, or does core generate SDK artifacts from its
  authoritative source?
- How is drift detected in both directions?
- Can a plugin be developed and tested without cloning the entire core?
- When is a live core checkout still necessary for integration tests or contract export?
- How are backend Python and dependency-free browser contracts versioned together?
- What replaces the current `--core-root` authoring MCP requirement?
- Does the SDK MCP fetch a released contract, query a local core, or support both explicitly?
- How does an SDK release declare compatible Alex Tavern versions?
- How do early forward-only breaking changes update core, SDK, template, hub, and curated plugins
  together without compatibility fallbacks?

The chosen design must have one authoritative input for generated schemas and public contracts and
must fail loudly on drift.

## 8. Template repository contract

The provisional `alex-tavern-plugin-template` should be independently usable through GitHub's
template feature. Explore inclusion of:

- `AGENTS.md` with SDK discovery/clone instructions and repository safety rules;
- a concise human README from first edit through curation PR;
- canonical `plugin.toml` placeholders;
- backend and optional frontend entrypoint examples;
- unit and contract test examples;
- an ignored local data/environment policy;
- `uv` project metadata and reproducible lock guidance where appropriate;
- `dev` and `prod` branch documentation and protection setup;
- CI for validation/test/pack on `dev`;
- promotion checks for PRs into `prod`;
- a protected/manual release or curation-submission workflow;
- version/changelog/release templates;
- issue and pull-request templates;
- permission/dependency review output;
- deterministic artifact and SHA-256 reporting;
- SDK version pin/update automation;
- optional commands to configure GitHub repository settings without requiring them for local use.

The template must not contain a copied private core SDK, live secrets, owner-specific tokens,
hardcoded maintainer identity, or a workflow with excessive repository/organization permissions.

Determine how updates reach repositories previously created from the template. GitHub templates do
not automatically synchronize descendants. Reusable workflows, SDK-provided checks, update PRs, or
documented manual upgrades may be needed, but should not create a hidden compatibility layer.

## 9. GitHub authentication and automation safety

Opening a PR in another repository is an external mutation and needs an explicit, reviewable
credential model.

Threat-model:

- broad personal access tokens copied into every author repository;
- a GitHub App with excessive organization access;
- workflow injection from plugin-controlled strings, filenames, manifests, or changelogs;
- `pull_request_target` executing untrusted plugin source with hub secrets;
- author tests exfiltrating tokens or network credentials;
- mutable tags, force-pushed branches, or artifacts replaced at the same URL;
- release/version reuse with different content;
- dependency confusion and malicious Python dependencies;
- action pinning drift and compromised third-party Actions;
- bot-created PR spam or updates to another author's submission;
- automatic merge being confused with automatic submission;
- privileged self-hosted runners executing unreviewed plugin code;
- generated PRs that hide permission or dependency changes;
- branch promotion bypasses and direct pushes to `prod`.

Compare GitHub App, fine-grained PAT, hub fork plus ordinary token, `gh` CLI, and manual submission.
Prefer the least privilege that still makes the workflow helpful. Never require authors to share a
curator credential.

## 10. Agent and documentation migration

Once the topology is accepted, later implementation must update all instructions atomically. The
exploration must inventory at least:

- main `AGENTS.md` workspace instructions;
- main README plugin architecture and coding-agent prompts;
- `tools/README.md` and author CLI references;
- hub `AGENTS.md` and README;
- SDK `AGENTS.md`, docs, MCP instructions, and compatibility policy;
- template `AGENTS.md`, README, workflows, and repository setup guidance;
- any MCP client configuration examples;
- hub curation/review instructions;
- existing curated plugin READMEs that point at hub-local authoring paths.

The future main-repository agent flow should conceptually become:

```text
Request to create a plugin from alex-tavern
    -> inspect core tasks and live contract
    -> locate/clone the isolated SDK
    -> use SDK docs and authoring MCP
    -> create or enter an independent plugin repository from the template
    -> develop and test there
    -> submit to the hub only through an explicitly authorized curation operation
```

There must be no transitional instruction that sometimes writes new source into the old hub path
"for compatibility." Producers and consumers move to the new workflow together.

## 11. Existing plugin migration

Inventory every source package currently under `alex-tavern-plugins/plugins/`, including the
character converter, dynamic character presence, grammar tools, and OpenRouter provider.

For each one, decide:

- authoritative future repository;
- maintainer and license metadata;
- SDK compatibility target;
- test and release workflow;
- immutable source commit recorded by the hub;
- artifact rebuild and hash continuity;
- Experience/catalog/media relationships;
- issue/history preservation;
- removal of the old hub-local source path after cutover.

Migration must be forward-only. Do not retain hub-local source and an external authoritative source
as two editable copies. Existing release artifacts and review records may remain immutable evidence
when their ownership is clearly documented.

## 12. Relationship to Celestial and hosted plugins

S02 already records that `alex-tavern-celestial` should have its own repository. Task 27 must make
that repository an ordinary first-class consumer of the isolated SDK and curation pipeline rather
than a privileged exception.

The SDK/template/submission design must also accommodate plugins that declare another plugin, such
as Celestial, as a required dependency. Curation evidence must preserve the full dependency
closure, compatibility constraints, permissions, and exact release hashes shown to the reviewer
and later to the installer.

## 13. Exploration deliverables

This task is complete as exploration only after producing evidence-backed artifacts for:

1. **Repository topology ADR:** exact ownership of core, SDK, template, hub, and plugin repos.
2. **SDK extraction inventory:** files/contracts that move, remain, or are generated, with a
   single-source-of-truth rule for each.
3. **Developer journey:** template creation, `dev` iteration, `prod` promotion, release, and
   curation submission.
4. **Template repository specification:** contents, `AGENTS.md`, branch model, protections,
   workflows, examples, and update behavior.
5. **Author CI contract:** validation, tests, conformance, deterministic pack, hashes,
   permissions/dependencies, and provenance.
6. **Submission protocol:** strict descriptor schema, immutable source identity, authentication,
   PR creation mechanism, retries, and duplicate/update behavior.
7. **Curator pipeline:** independent fetch, validation, safe tests, human review, rebuild, catalog
   update, artifact publication, and audit evidence.
8. **Supply-chain threat model:** untrusted code, secrets, Actions, dependencies, mutable refs,
   runners, bots, and credential scope.
9. **Distribution decision:** where artifacts live and how the existing app verifies/downloads
   them without source duplication.
10. **Agent workflow migration:** exact changes needed in every `AGENTS.md`, README, MCP setup, and
    authoring prompt.
11. **Existing plugin migration map:** one future source owner and cutover path for every current
    hub plugin.
12. **RAG readiness gate:** proof that a new large plugin can start in its own repository and reach
    a reviewable curation PR using only public SDK/template mechanisms.
13. **Celestial readiness check:** proof that dedicated first-party repositories and plugin
    dependencies fit the same ecosystem.
14. **Decision register:** rejected alternatives, unresolved questions, and evidence.
15. **Implementation decomposition:** smaller tasks only after the exploration is reviewed.

## 14. Exploration acceptance criteria

- [ ] The number `27` is documented as an identifier, while execution is explicitly ordered before
  Task 06 RAG.
- [ ] Plugin authorship no longer conceptually requires writing source inside
  `alex-tavern-plugins`.
- [ ] Core, SDK, template, hub, and individual plugin repositories each have one clear authority.
- [ ] No public contract or SDK implementation has two manually synchronized sources.
- [ ] A developer can start from `alex-tavern-plugin-template` without cloning the curated hub.
- [ ] The template contains a complete `AGENTS.md` that directs coding agents to the isolated SDK.
- [ ] The recommended `dev` to `prod` promotion flow and branch protections are specified.
- [ ] Ordinary `dev` CI never publishes or submits a curated release.
- [ ] Production submission requires a versioned, immutable source commit and deterministic hash.
- [ ] The cross-repository PR mechanism is technically real and uses least-privilege credentials.
- [ ] Authors never need a curator token or direct hub write permission.
- [ ] Hub CI never exposes secrets to or executes unreviewed source in a privileged context.
- [ ] Human source review remains mandatory before curation.
- [ ] Author artifacts are independently reproducible or rebuilt by the curator.
- [ ] Main, hub, SDK, template, and plugin agent instructions have a forward-only migration map.
- [ ] Existing curated plugins each have a single-source migration decision.
- [ ] RAG can be developed as the first major plugin on the new workflow without an exception.
- [ ] Celestial and its future satellite dependencies fit the same release/submission contracts.
- [ ] No repository, workflow, package, token, PR, release, or source move is created by this
  exploration task.

## 15. Non-goals

- Create the SDK or template repositories now.
- Move current plugin source now.
- Implement RAG now.
- Open curation PRs now.
- Publish SDK packages, reusable Actions, artifacts, or GitHub Releases now.
- Create GitHub Apps, PATs, organization secrets, branch protections, or repository settings now.
- Automatically curate, approve, merge, or publish third-party code.
- Require a developer to expose secrets to Alex Tavern or its curator.
- Preserve the old hub-local authoring path as a fallback after cutover.
- Turn the template repository into another source of SDK truth.
- Commit, push, create repositories, or modify remotes without separate explicit authorization.

## 16. Open questions

- What is the final isolated SDK repository name and package identity?
- Which runtime SDK files remain core-owned, and which author-facing pieces move or are generated?
- Can ordinary plugin development avoid a full core checkout?
- How is SDK/core compatibility represented in `plugin.toml` and the catalog?
- Is `dev`/`prod` mandatory for the official workflow or a template recommendation with
  configurable branch names?
- Should merging into `prod`, creating a tag, publishing a release, or manually dispatching a
  workflow initiate submission?
- Is the safest intake mechanism a hub fork, GitHub App, CLI, or another protocol?
- Who creates the branch and PR in shared hub history when the source repo is unrelated?
- What data belongs in the submission descriptor versus curator-generated catalog metadata?
- Does the hub store deterministic ZIPs, rebuild release assets, or point to immutable external
  artifacts?
- How are source archives and Git submodules pinned and reviewed?
- How are Python dependencies tested without giving untrusted setup code secrets or privileged
  runners?
- Which reusable workflows belong in the SDK repo versus the template repo?
- How do template descendants receive future workflow/security updates?
- Where does the authoring MCP live, and what replaces or preserves the explicit `--core-root`
  boundary?
- Does the hub retain a separate curation MCP after the authoring MCP moves?
- How are existing plugin Git histories split or preserved?
- What repository and package will own RAG?
- How does a plugin with a mandatory Celestial dependency submit and prove its exact dependency
  closure?

These questions must be answered before implementation code establishes another de facto authoring
workflow.

## Exploration DELIVERED 2026-07-17 (Opus session) — pending owner acceptance

Exploration document (deliverables 1-15 + threat model + decision register):
`docs/plugin-ecosystem-topology-exploration-2026-07-17.md`. Grounded in the
2026-07-17 checkout (`src/plugins/` ~2850 LOC, `exported_contract()` as the
single contract source, browser SDK, `tools/plugin_author.py`).

Key decisions recorded: contract source of truth = core `exported_contract()`,
SDK publishes a GENERATED snapshot (never a hand copy); core is upstream of the
SDK (no cycle); ordinary plugin dev needs only the SDK, not a full core checkout;
`dev`->`prod`->curation-PR journey; hub-fork + ordinary token as the default
least-privilege PR mechanism; curator independently rebuilds and compares;
forward-only cutover with no transitional hub-local write.

STILL OPEN / verify-before-implementation (need the external hub checkout or an
owner call): exact submission descriptor schema; App-vs-fork-token final choice;
artifact hosting model; per-plugin migration owners; final home of the authoring
MCP. NON-GOALS honored: no repo/source/package/token/PR/release created.

Task stays in tasks/ until the owner reviews and accepts the exploration (§14
acceptance is an owner action) and the hub-checkout items are verified.
