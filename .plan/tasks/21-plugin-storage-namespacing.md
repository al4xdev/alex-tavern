# Task 21 — Plugin Storage Namespacing

## Goal

Introduce a first-class private storage namespace for every plugin.

Plugins may need to persist generated files, indexes, presets, session-specific
data, assets, caches, or other runtime artifacts. They should be free to
organize those files as needed, but they must not create arbitrary directories
across the core `.data/` structure.

The goal is to isolate plugin-owned files from core-owned application data while
keeping the SDK simple and flexible.

---

## Current Problem

Plugins currently have dedicated configuration support, but no equivalent
general-purpose storage namespace.

Without an official storage location, plugins may:

- create arbitrary directories under `.data/`;
- mix plugin-owned data with core presets, sessions, scenarios, or assets;
- derive internal application paths manually;
- conflict with other plugins;
- leave files behind in undocumented locations;
- accidentally make plugin implementation details part of the core filesystem
  contract.

The core should own the top-level data layout. Plugins should only own their
assigned namespace.

---

## Proposed Directory Model

Each plugin should receive a private directory based on its plugin ID:

```text
.data/plugins/storage/<plugin-id>/
```

Example:

```text
.data/plugins/storage/dev.alex-tavern.memory-tools/
├── sessions/
│   ├── a4363ccf/
│   │   ├── index.json
│   │   └── metadata.json
│   └── eb7d6ec3/
├── presets/
├── assets/
├── cache/
└── plugin-state.json
```

The internal structure is controlled by the plugin.

The core should not require plugins to use specific subdirectories such as
`sessions`, `cache`, or `presets`. These are examples only.

---

## Core Contract

The core should guarantee:

- one isolated storage namespace per plugin ID;
- automatic directory creation;
- safe path resolution;
- prevention of path traversal;
- prevention of writes outside the plugin namespace;
- stable path access through the SDK;
- no need for plugins to know the absolute `.data/` path.

The core should not interpret the files inside the namespace.

The plugin remains responsible for:

- its internal directory layout;
- file formats;
- migrations;
- cleanup of obsolete files;
- session-specific organization;
- concurrency rules;
- recovery from partial writes.

---

## SDK Exploration

Explore an API such as:

```python
storage_dir = context.storage.path
```

Possible helper APIs:

```python
path = context.storage.resolve("sessions", session_id, "index.json")
```

```python
with context.storage.open("plugin-state.json", "w") as file:
    ...
```

```python
context.storage.exists("sessions", session_id)
context.storage.mkdir("sessions", session_id)
context.storage.remove("cache", recursive=True)
```

The final API is intentionally open.

Prefer a small and predictable abstraction over a large virtual filesystem API.

Plugins may still use standard Python filesystem APIs after receiving a safe
root path.

---

## Session-Scoped Plugin Data

Plugins should be free to mirror application session IDs inside their own
namespace.

Example:

```text
.data/plugins/storage/<plugin-id>/sessions/<session-id>/
```

This is recommended for plugins that maintain session-specific state, indexes,
artifacts, or generated files.

The plugin-owned session directory must remain independent from:

```text
.data/sessions/<session-id>/
```

A plugin should not write directly into the core session directory unless a
separate explicit SDK contract permits it.

Explore whether the SDK should provide a convenience helper:

```python
session_dir = context.storage.for_session(session_id)
```

This helper should only resolve a path inside the plugin namespace. It should
not impose a mandatory internal structure.

---

## Configuration Remains Separate

Plugin configuration should continue using the existing dedicated location:

```text
.data/plugins/config/<plugin-id>.json
```

Configuration and storage have different responsibilities.

Configuration is:

- managed through the plugin configuration contract;
- expected to be small and structured;
- user-editable or UI-editable;
- validated by the plugin schema.

Plugin storage is:

- controlled directly by the plugin;
- potentially larger;
- allowed to contain arbitrary file types;
- allowed to use plugin-specific layouts;
- not interpreted by the core.

---

## Shared Logs

The current centralized plugin event log may remain shared:

```text
.data/plugins/events.jsonl
```

This task does not need to move logs into individual plugin directories unless
exploration identifies a concrete requirement.

Plugin-specific diagnostic artifacts that are not part of the shared event
stream may be stored inside the plugin namespace.

---

## Existing Cache Directory

Review the current directory:

```text
.data/plugins/cached/
```

Determine whether it should be:

- migrated to `.data/plugins/storage/`;
- retained temporarily as a compatibility alias;
- removed if it is currently unused;
- migrated automatically during startup;
- handled through a one-time migration.

Because plugin storage may contain persistent data, the new directory should use
the name `storage`, not `cached`.

Migration must not silently delete existing files.

---

## Path Safety

The SDK must reject attempts to escape the plugin namespace through:

- absolute paths;
- `..` traversal;
- malformed plugin IDs;
- symbolic-link traversal where relevant;
- session IDs or user inputs used directly as paths.

Examples that must not be allowed:

```python
context.storage.resolve("../../sessions")
context.storage.resolve("/etc/passwd")
```

Plugin IDs should already be validated by the plugin system, but storage
resolution must not rely only on that assumption.

---

## Plugin Lifecycle

Explore and document behavior for:

- plugin installation;
- plugin startup;
- plugin disable;
- plugin upgrade;
- plugin uninstall;
- application restart;
- session deletion.

The default should prioritize data safety.

Disabling or uninstalling a plugin should not automatically delete its storage
unless the user explicitly requests deletion or a future lifecycle API defines
that behavior.

The task does not need to implement a complete uninstall-data UI unless required
by the final design.

---

## Existing Plugin Review

Review every currently published plugin in the public plugin repository.

For each plugin, identify:

- whether it writes files;
- where those files are currently stored;
- whether it derives `.data/` paths manually;
- whether it creates generated presets, indexes, assets, or session data;
- how it should use the new storage namespace;
- whether an SDK capability is missing.

Current published plugins should serve as real validation cases for the storage
API.

At minimum, review:

- `character-converter`;
- `dynamic-character-presence`;
- `grammar-tools`;
- `openrouter-provider`.

If several plugins need the same helper or workaround, treat that as evidence
that the SDK abstraction should be improved.

---

## Compatibility

The implementation should avoid breaking plugins that do not use storage.

For plugins currently writing files in legacy locations:

- identify the old path;
- define whether migration is automatic or plugin-managed;
- avoid silent data loss;
- document any required plugin version bump;
- provide clear errors when legacy paths are no longer writable.

The core should not indefinitely preserve arbitrary undocumented plugin paths.

---

## Testing

Expected coverage should include:

- unique storage roots for different plugin IDs;
- automatic directory creation;
- stable paths across restarts;
- safe nested path resolution;
- traversal rejection;
- absolute-path rejection;
- malformed path components;
- session-scoped path helpers, if added;
- plugins using identical internal filenames without conflicts;
- migration from `.data/plugins/cached/`, if implemented;
- behavior when the storage directory is missing;
- behavior when the storage directory is read-only;
- compatibility with plugins that never access storage.

Use at least one real published plugin as an integration case.

---

## Documentation

Document:

- the difference between configuration and storage;
- the official storage path;
- how plugins should obtain their storage root;
- recommended session-specific organization;
- path-safety restrictions;
- lifecycle expectations;
- migration guidance from legacy paths;
- examples for common file operations.

The documentation should make it clear that plugins own everything inside their
namespace, but must not write elsewhere in `.data/`.

---

## Constraints

The final solution should:

- preserve plugin freedom inside its namespace;
- keep the core `.data/` layout clean;
- avoid coupling the core to plugin-specific file formats;
- avoid unnecessary dependencies;
- remain simple for small plugins;
- support large or session-aware plugins;
- not confuse persistent storage with disposable cache;
- not require the core to understand plugin migrations;
- prevent storage namespace escape.

---

## Deliverables

The exact implementation is intentionally open and may change after exploration.

Expected outcomes:

- official `.data/plugins/storage/<plugin-id>/` layout;
- SDK access to the current plugin storage root;
- safe path-resolution behavior;
- migration decision for `.data/plugins/cached/`;
- tests for isolation and path safety;
- review and migration of affected published plugins;
- developer documentation and examples;
- notes about any missing SDK abstractions discovered during plugin review.
