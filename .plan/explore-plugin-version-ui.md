# Explore: Plugin versions in the installed-cache UI

**Date**: 2026-07-13; expanded 2026-07-14
**Scope**: Remote update detection, installed package representation, activation pointers, and
Plugin Center navigation

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
- The controlled remote-update check then left 1.0.0 installed and active while the synchronized
  curated catalog advertised 2.0.0. The catalog card displayed the generic `Install` action; no
  update label, version transition, or warning appeared.

### Remote releases are classified only by exact `id@version` cache keys

- `refresh()` builds `installedKeys` as `${plugin_id}@${version}` and `catalogCard()` asks only
  whether that exact key exists (`src/static/plugin-center.js:208-249`).
- The UI does not compare SemVer, associate a catalog entry with an older installed release of the
  same plugin ID, or distinguish upgrade, downgrade, same-version/new-hash, and new installation.
- Clicking the catalog action calls only the install endpoint. It caches the candidate but does not
  replace the activation pointer; activation remains a second action on a separate cache card.
- No frontend or backend test covers detection of a newer catalog release, a permission-changing
  update, or multiple cached versions rendered as one logical plugin.

### The catalog cannot describe a reviewed update diff

- Catalog entries currently expose ID, name, version, description, license, artifact path, and
  SHA-256. They do not expose permissions, dependencies, entrypoints, authors, or installation
  requirements.
- Installed entries expose the full parsed manifest, so the client can inspect the old side but not
  the candidate side before installation.
- Grammar Tools demonstrates the gap: 1.0.0 declares `config.read` and `session.state.write`, while
  2.0.0 removes both and adds the cost-bearing `model.call` permission. The current catalog card
  cannot show this transition.
- The closed plugin-system design explicitly requires release comparison and renewed review when
  permissions, dependencies, entrypoints, domains, or install scripts change
  (`.plan/closed/S01-plugin-system.md:629-650`).
- Exact version alone is also insufficient for cache identity: the backend cache and activation
  pointer include SHA-256, while the frontend's cached key omits it. A catalog artifact changed
  under the same version would be displayed as already cached.

### Tab navigation currently swaps display state rather than moving a viewport

- The modal contains three sibling sections under `.plugin-center-body`: Experiences, Plugins, and
  Activity (`src/static/index.html:268-301`).
- Inactive views use `display: none`; the active view uses a 180 ms fade
  (`src/static/style.css:243-263`). There is no persistent horizontal track for adjacent panels to
  move together.
- `selectTab()` only toggles the `active` class. It does not retain tab indices or transition
  direction, and there are no touch, pointer, drag, or keyboard-arrow handlers in
  `plugin-center.js`.
- The application already contains a hand-written touch-direction lock for the mobile input area,
  but it is coupled to turn actions and a mobile-only 50% threshold rather than being a reusable
  carousel primitive (`src/static/app.js:1381-1543`).
- `.plugin-center-body` owns vertical scrolling. An interactive horizontal drag therefore has to
  distinguish horizontal intent from vertical list scrolling. Buttons, the ZIP file input, text
  selection, and confirmation overlays are interactive descendants of the same region.
- The global reduced-motion media query shortens CSS transitions, but direct per-frame transforms
  from gesture code would require separate reduced-motion handling.
- The tablist currently lacks `role="tab"`, `aria-selected`, `aria-controls`, matching tabpanel
  roles, and Left/Right keyboard behavior; class changes are the only tab state.

## Implemented resolution (2026-07-14)

- `GET /plugins` now groups immutable packages by plugin ID, exposes the active selection, all cached
  versions, and a full candidate manifest derived from the verified ZIP.
- SemVer plus SHA-256 classifies current, newer, cached candidate, older catalog, and release
  conflict states. Same-version/different-hash artifacts never become normal updates.
- The reviewed update endpoint requires the exact candidate version and hash, prepares the uv
  environment before switching the pointer, activates it, and retains every previous package for
  rollback. Plain ZIP installation remains cache-only.
- The Installed view renders one card per logical plugin, an active-to-candidate release rail,
  permission/dependency/entrypoint review, and an expandable version ledger.
- The three panels remain mounted on a horizontal track. Click and keyboard navigation slide them;
  touch and pen can drag after a horizontal direction lock. Each panel owns its vertical scroll,
  and reduced-motion mode makes autonomous transitions immediate while direct drag follows input.
