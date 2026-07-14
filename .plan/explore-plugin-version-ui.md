# Explore: Plugin versions in the installed-cache UI

**Date**: 2026-07-13
**Scope**: Installed package representation, activation pointers, and Plugin Center rendering

## Findings

### Multiple cached versions are an intentional backend invariant

- Packages are immutable under `plugin_id/version/sha256` in `src/plugins/store.py`.
- `installed_plugins()` returns every cached artifact and marks exactly the artifact selected by the
  per-plugin activation pointer as active.
- `activate()` replaces the single pointer for a plugin ID, so only one cached version can be active
  even while older versions remain available for rollback.

### The Plugin Center renders artifacts instead of logical plugins

- `src/static/plugin-center.js` maps every `status.installed` entry directly through `pluginCard()`.
- Two versions of the same plugin therefore become two visually independent cards with the same
  name and generic Activate/Deactivate/Remove actions.
- The screen does not label the active version, group cached versions, or identify a newer cached
  version as an available update.
- The closed plugin-system design describes the Installed view in terms of active versions and
  available updates, while the current UI exposes the lower-level immutable-cache representation.

### Observed Grammar Tools state

- The screenshot captured Grammar Tools 1.0.0 active alongside Grammar Tools 2.0.0 cached and
  inactive.
- After 1.0.0 was removed, `/plugins` reported only 2.0.0 cached, with no active or loaded Grammar
  Tools version. Upload/install and activation are separate operations.

## Open Questions

- Whether the Installed view should show one card per plugin ID with an expandable cached-version
  list, or separate an Active view from a Cache/rollback manager.
- Whether installing a newer version should offer an explicit reviewed update action while leaving
  plain ZIP installation non-activating.
