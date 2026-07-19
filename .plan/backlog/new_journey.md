# Task: New Journey default Experience

**Status:** Future product and architecture exploration  
**Target milestone:** Alex Tavern 1.5 LTS  
**Repository:** Provisional `alex-tavern-new-journey`, dedicated and authoritative  
**Execution order:** After v1 evidence, the isolated SDK/curation workflow, and Celestial  
**Created:** 2026-07-15

> [!IMPORTANT]
> This task preserves the intended product direction. It does not authorize creating the
> repository, changing the default Experience, installing plugins, changing the base theme,
> publishing artifacts, or beginning Celestial. Re-read the current core, SDK, hub contracts,
> open Supertasks, and beta evidence before turning this exploration into implementation work.

## 1. Goal

Create **New Journey**, the first-party default Experience for the Alex Tavern 1.5 LTS era.

New Journey is the product composition users experience, while Alex Tavern core remains a stable
kernel. It selects an exact, reviewed set of plugins and configuration, presents them as one
coherent journey, explains why each plugin was chosen, and gives visible credit to every author.

The intended composition includes, subject to future evidence and review:

- Celestial as the agentic configuration command center and plugin host;
- the RAG plugin proven during the v1 cycle;
- a new visual theme delivered as a plugin rather than a replacement for the base theme;
- Celestial satellite plugins or other first-party/curated plugins that materially improve the
  combined experience;
- exact configuration and ordering required for the set to behave as one product.

New Journey should be preinstalled and selected as the default Experience in the v1.5 product, but
it must remain an ordinary, inspectable, replaceable Experience. It receives no hidden core
branches or permanent privilege merely because it is first-party or default.

## 2. Product and core boundary

The desired product model is:

```text
Alex Tavern Core LTS
├── stable Runner, persistence, providers, locks, logs, and plugin runtime
├── stable setup and Plugin Center
├── unchanged base theme and recovery UI
└── no knowledge of New Journey plugin identities

New Journey Experience
├── Celestial
├── New Journey/Celestial theme plugin
├── RAG
├── selected supporting plugins
└── exact versions, ordering, and configuration
```

Core must remain fully usable when New Journey is absent, disabled, incompatible, or fails to
start. The base theme is the recovery and fallback presentation. New Journey changes the perceived
product through public plugin and Experience contracts, not by replacing the base source.

Large future features and visual changes should generally arrive as plugins or new Experience
compositions. Core updates after the 1.5 LTS milestone should focus on correctness, security,
provider/runtime maintenance, contract fixes, and changes that truly belong to the kernel.

## 3. Dedicated repository

New Journey deserves its own repository because it is a versioned first-party product composition,
not merely one JSON row hidden in the curated hub.

The provisional repository `alex-tavern-new-journey` should be the authoritative home for:

- the Experience source manifest;
- its product README and design intent;
- the rationale for every included plugin;
- author, maintainer, license, repository, and release credits;
- screenshots, video/GIF previews, and other presentation media;
- exact release/lock evidence for the selected dependency closure;
- compatibility declarations for core, SDK, Plugin API, and Celestial;
- tests for composition, ordering, configuration, activation, failure, and fallback;
- release notes and the history of plugin additions, removals, and replacements;
- CI that validates the Experience against pinned curated releases;
- instructions for humans and coding agents working on the composition.

The repository must not duplicate plugin source. Celestial, RAG, the theme, and third-party plugins
remain authoritative in their own repositories. New Journey references reviewed releases by exact
identity and records why they belong together.

The exploration must decide how this repository submits or publishes an Experience through the
curated hub without creating two independently edited Experience manifests. The final path should
be content-addressed and forward-only, with one source of truth.

## 4. Experience contract boundaries

The current Experience schema contains presentation metadata plus an ordered list of plugins,
versions, and configuration. Project rules state that an Experience does not contain scenarios or
characters.

New Journey must preserve that separation:

- **Experience:** plugins, exact order, plugin configuration, description, and preview media;
- **theme plugin:** visual transformation activated by the Experience;
- **character preset:** reusable character content owned by the preset store;
- **scenario:** world/story setup owned by scenario storage;
- **Celestial:** agentic configuration plugin and host for declared satellite plugins.

If New Journey needs richer metadata for credits, rationale, release identity, compatibility, or
dependency review, investigate a generic Experience contract extension. Do not add fields or UI
branches recognized only when `experience_id == "new_journey"`.

## 5. Plugin selection and rationale

Every included plugin needs a documented selection record. At minimum, record:

| Field | Purpose |
|---|---|
| Plugin identity | Stable ID, exact version, artifact hash, source repository, and immutable source commit |
| Authors and maintainers | Visible credit with the spelling and links requested by the authors |
| License | User-visible attribution and redistribution obligations |
| Why it is included | The concrete user value it adds to New Journey |
| Why this plugin | Why it was chosen over alternatives or core implementation |
| Required or optional | Whether New Journey can remain coherent without it |
| Configuration | Exact defaults selected by New Journey and the reason for each non-obvious choice |
| Ordering/dependencies | Host, satellite, before/after, and activation requirements |
| Permissions and data | What it reads, writes, sends to a provider, or accesses over the network |
| Model cost | Whether it introduces model calls, expected budgets, and user-facing controls |
| Failure behavior | What degrades, what is disabled, and whether the base experience remains usable |
| Evidence | Tests, benchmarks, beta feedback, media, and review record supporting inclusion |
| Removal/replacement | How the plugin can leave the set without legacy runtime paths |

Selection must be evidence-based. A plugin is not included only because it is first-party, novel,
or technically impressive. The combined Experience must be easier to understand and more coherent
than independently enabling the same plugins without guidance.

## 6. Author credits

New Journey must treat author credit as product content, not a buried legal afterthought.

Explore a generic credits representation that can appear in:

- the New Journey repository README;
- an Experience details screen before activation;
- the installed Experience view;
- release notes when a plugin is added or updated;
- a durable credits/licenses view available offline.

Credits should include plugin name, author/maintainer identity, source link, license, exact included
release, and a short description of the contribution. An author should not lose visible attribution
because their plugin is presented inside a first-party Experience.

The curated manifest, plugin manifest, and Experience credits must not drift into contradictory
identities. Determine which record is authoritative and which views are generated.

## 7. Theme strategy

The Alex Tavern base theme remains unchanged and maintained by core. New Journey introduces its
own theme through a generic plugin capability.

The theme must:

- activate only as part of its declared plugin/Experience state;
- leave setup, approvals, Plugin Center, diagnostics, and safe mode accessible;
- unload cleanly and restore the base theme without a compatibility branch;
- use public design-token, component, slot, or workspace contracts established by the future SDK;
- avoid editing base CSS/HTML files at installation time;
- remain attributable as a plugin with its own version, author, license, and failure record;
- support accessibility, localization, reduced motion, small screens, and offline loading;
- fail closed to the base theme rather than leaving an unreadable application.

Whether the theme is a standalone generic plugin, a Celestial satellite, or a small set of theme
plugins remains an exploration question. Keeping it separate from Celestial is a useful composition
test, but should not be decided without the future SDK and UI contracts.

## 8. Default, preinstallation, and user control

"Default" must not mean irreversible or invisible.

Investigate a v1.5 distribution in which:

- New Journey metadata is available on a clean installation;
- its exact reviewed plugin closure is bundled, cached, or installable according to a deliberate
  offline and deployment policy;
- the user sees its plugins, permissions, model costs, network access, versions, and authors;
- first activation is transactional and does not leave a half-installed set;
- the user can choose another Experience or the base product;
- safe mode can start without New Journey plugins;
- uninstalling or disabling New Journey never deletes independent session, preset, or scenario
  data without a separate explicit operation;
- updates show dependency, permission, author, and behavior diffs before activation;
- a failed update restores the previously working exact closure.

The Experience must remain reproducible by immutable `id/version/hash` identities. "Use latest" is
not acceptable for an LTS default composition.

## 9. Activation and composition evidence

Before New Journey can become default, test the complete composition rather than validating each
plugin only in isolation.

Required evidence should include:

- clean online and offline installation;
- activation, restart, deactivation, update, rollback, and safe-mode recovery;
- deterministic plugin order and dependency closure;
- Celestial host plus satellite lifecycle behavior;
- RAG storage, background work, retrieval privacy, and cancellation;
- theme loading and fallback at every application entrypoint;
- provider configuration and secret redaction;
- model-call budgets, attribution, retries, and failure behavior;
- session start, long play, compaction, undo, fork, resume, and deletion under the active set;
- plugin state participation in persistence and recovery;
- user review of permissions, credits, costs, and changes;
- real boundary tests through HTTP, browser modules, provider adapters, and packaging;
- multiple deployment profiles without embedding development `.data` or secrets.

## 10. Release and update model

New Journey has its own version and release notes. Its version records changes to the composition,
not the version of Alex Tavern core or any one plugin.

The intended long-term model is:

- Alex Tavern 1.5 becomes the LTS core/product milestone associated with New Journey and Celestial;
- core patch releases can remain small and conservative for years;
- New Journey and its plugins can evolve independently through reviewed releases;
- a new visual direction or major optional feature normally appears as a plugin or another
  Experience, not as an unconditional base-theme/core rewrite;
- exact compatibility among core, Plugin API, SDK, Celestial, satellites, and New Journey remains
  machine-readable;
- breaking plugin-contract evolution uses its own explicit API/SDK version even when the product
  milestone is named Alex Tavern 1.5.

## 11. Exploration deliverables

This task is ready for implementation decomposition only after it produces:

1. a repository ownership and publication decision for `alex-tavern-new-journey`;
2. a generic Experience metadata proposal for credits, rationale, compatibility, and immutable
   dependency identity;
3. a documented plugin selection rubric;
4. a proposed initial plugin set with evidence and per-plugin rationale;
5. a generic theme-plugin contract study and fallback UX;
6. a default/preinstallation, offline, activation, rollback, and safe-mode design;
7. an author-credit and license presentation design;
8. a composition-level test and benchmark matrix;
9. a release/versioning relationship among core, New Journey, Celestial, SDK, and Plugin API;
10. an implementation task breakdown created only after the exploration is accepted.

## 12. Exploration acceptance criteria

- [ ] New Journey has one authoritative repository and no duplicated editable manifest.
- [ ] Every included plugin has an exact release identity, reason for inclusion, evidence, author
  credit, license, permissions, costs, configuration rationale, and failure behavior.
- [ ] Plugin source remains authoritative in each plugin author's repository.
- [ ] The Experience contains no characters or scenarios.
- [ ] The base theme remains unchanged and usable without New Journey.
- [ ] The New Journey theme uses a generic plugin contract and falls back safely.
- [ ] Core and shared frontend code contain no New Journey or Celestial plugin-ID branches.
- [ ] Default activation remains visible, reviewable, reversible, and reproducible.
- [ ] The complete dependency closure is pinned and reviewed before activation.
- [ ] Credits are visible in repository, review, installed, and offline product surfaces.
- [ ] Composition tests cover Celestial, satellites, RAG, theme, persistence, providers, and
  failure/recovery boundaries together.
- [ ] The design supports years of LTS maintenance without making every Experience update a core
  release.
- [ ] No repository, plugin, theme, artifact, or default activation is created by this exploration.

## 13. Open questions

- What exact repository name and organization should own New Journey?
- Which metadata belongs to the Experience manifest versus generated documentation?
- Does the curated hub store the Experience artifact, immutable metadata, or both?
- Which plugins form the first v1.5 composition after future benchmarks and beta evidence?
- Is the theme generic, Celestial-dependent, or split into multiple plugins?
- How is a preinstalled dependency closure delivered consistently across desktop, Docker, and
  other supported deployments?
- Which user choices survive switching away from and back to New Journey?
- How are author credits localized and kept synchronized with exact releases?
- Which New Journey changes require product `1.5.x`, Experience-only, or individual-plugin
  releases?
- What is the smallest safe fallback when one required plugin fails boot?

<details>
<summary><strong>Preserved future context: v1 evidence and long-duration roleplay</strong></summary>

This section is strategic memory, not immediate New Journey implementation scope.

Alex Tavern v1 should be earned by evidence that the roleplay engine survives difficult,
long-duration use. The most valuable beta inputs are not polished fixtures designed around the
architecture, but varied presets and scenarios created by beta testers specifically because they
stress assumptions the author may not anticipate.

The v1 evidence program should include:

- conversations long enough to require repeated compaction cycles;
- different genres, casts, relationship structures, narrator styles, and world constraints;
- presets intentionally difficult to preserve across many turns;
- server restart, resume, fork, undo, compaction restoration, and failure recovery;
- strict checks for player agency and private-knowledge boundaries;
- state, prompt, response, and debug-log inspection in addition to transcript reading;
- model-based evaluators focused on detailed conversation consistency;
- human beta review and deterministic assertions as independent signals;
- multiple providers/models and token-budget profiles where feasible.

A dedicated evaluator model, including the proposed Claude-based history reviewer, can inspect each
conversation detail, but no single model judge defines quality. The project should combine model
evaluation, deterministic invariants, debug evidence, author review, and beta-tester judgment to
avoid optimizing the system for one evaluator's preferences.

Additional LLM calls may be justified when specialized passes measurably stabilize long stories.
Core complexity is acceptable when it becomes explicit, owned, tested, and stable. Every call must
have a narrow responsibility, structured contract, context boundary, `session_id`, `turn_number`,
agent identity, timeout/retry behavior, cost/token budget, failure semantics, and persistent debug
evidence. Invisible heuristic calls are not acceptable.

</details>

<details>
<summary><strong>Preserved future context: release milestones and the 1.5 LTS era</strong></summary>

This section records the intended chronology so future work does not accidentally move Celestial
into the v1 gate.

```text
beta evidence
  -> critical stability and usability corrections
  -> isolated SDK, plugin template, and curated submission workflow
  -> RAG as the large reference plugin
  -> final v1 validation
  -> Alex Tavern v1
  -> Celestial development, potentially lasting months
  -> New Journey composition and full integration evidence
  -> Alex Tavern 1.5 LTS
  -> years of small core maintenance and plugin/Experience evolution
```

Celestial is explicitly not a v1 requirement. RAG is the large plugin intended for the v1 line and
validates the separated SDK, independent plugin repository, CI/CD, curation, storage, model calls,
background work, slash commands, and privacy boundaries.

Celestial marks a new product era. It may force a new Plugin API/SDK generation and make earlier
plugins incompatible. The product milestone can remain **Alex Tavern 1.5 LTS** while the Plugin API
and isolated SDK use their own major compatibility version. After that milestone, the intention is
to spend years refining the 1.5 LTS line instead of chasing major product numbers. Ordinary product
patches use valid versions such as `1.5.1`, `1.5.2`, and later `1.5.x` releases.

</details>

<details>
<summary><strong>Preserved future context: Celestial and plugins for plugins</strong></summary>

This section summarizes S02; S02 remains the authoritative detailed exploration.

Celestial is envisioned as a full-screen `/chat` configuration command center, effectively an
agentic tool comparable in ambition to a coding agent inside Alex Tavern. It uses the configured
provider through server-owned secrets, receives project skills and typed tools, supports `/plan`,
can inspect and prepare coordinated configuration changes, and never applies a mutation without an
exact visible user approval.

Celestial is also a host plugin. Satellite plugins may contribute skills, resources, tools,
workflows, integrations, or UI through a versioned Celestial extension contract. They declare a
compatible Celestial dependency; missing or incompatible hosts must be explained before activation.
The core supplies only generic dependency, service-discovery, lifecycle, attribution, and approval
mechanics. It does not learn Celestial satellite identities.

Celestial has its own `alex-tavern-celestial` repository. New Journey includes a pinned reviewed
Celestial release and explains why it was selected. Celestial remains an ordinary plugin despite
its scale: no secret provider access, private core imports, automatic writes, or hardcoded core/UI
branches.

</details>

<details>
<summary><strong>Preserved future context: core LTS, plugin-led UI, and repository ecosystem</strong></summary>

The architectural thesis is a stable kernel with evolving compositions:

- `alex-tavern` owns the LTS core, runtime invariants, base theme, and generic contracts;
- an isolated SDK repository owns the public authoring kit without duplicating runtime truth;
- a plugin template repository helps developers start with `dev`/`prod`, CI/CD, tests, packaging,
  agent instructions, and curation-submission automation;
- `alex-tavern-plugins` becomes the curated intake/distribution boundary rather than the working
  monorepo for every plugin;
- each plugin has an authoritative repository owned by its author;
- `alex-tavern-new-journey` owns the default v1.5 Experience composition and credits;
- plugins and Experiences deliver most future visual and feature evolution.

The template should help another developer create a GitHub repository, work on `dev`, promote
reviewed state to `prod`, and prepare a curation PR. Automation submits evidence; it never grants
curated status or merges automatically. Its `AGENTS.md` should teach coding agents to locate or
clone the isolated SDK and operate only in the current plugin repository unless separately
authorized.

The base UI is deliberately conservative and always available. A new theme comes from a plugin
selected by New Journey or another Experience. If users want a different direction later, the
project can release a new theme/plugin composition without replacing the fallback UI or destabilizing
the LTS kernel.

</details>
