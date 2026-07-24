# Plugin Storage Namespace (Task 21)

Every plugin gets one private, path-safe storage namespace for its runtime
files. The core owns the top-level `.data/` layout; a plugin owns everything
inside its namespace and nothing outside it.

## Path

```
.data/plugins/storage/<plugin-id>/
```

The internal layout is entirely the plugin's own (the core never interprets the
files). A recommended — not required — convention for session-specific state:

```
.data/plugins/storage/<plugin-id>/sessions/<session-id>/
```

## SDK

`context.storage` is a `PluginStorage`:

```python
def setup(context):
    root = context.storage.path  # namespace root (created lazily)
    index = context.storage.resolve("sessions", sid, "index.json")

    with context.storage.open("plugin-state.json", mode="w") as fh:
        fh.write(json.dumps(state))

    if context.storage.exists("cache", "embeddings.bin"):
        ...
    context.storage.mkdir("assets", "img")
    session_dir = context.storage.for_session(sid)  # sessions/<sid>/ under the namespace
    context.storage.remove("cache", recursive=True)
```

- `path` — the namespace root `Path`, created on first access.
- `resolve(*parts)` — a safe `Path` inside the namespace (see Path safety).
- `open(*parts, mode="r")` — open a file; parent dirs are created for write modes
  and text mode defaults to UTF-8.
- `exists(*parts)`, `mkdir(*parts)`, `remove(*parts, recursive=False)`.
- `for_session(session_id)` — the recommended per-session subdirectory.

After obtaining a safe root/path, plugins may use ordinary Python filesystem
APIs — the abstraction is deliberately small.

## Path safety

`resolve()` rejects any attempt to escape the namespace and every other method
routes through it:

- absolute components (`/etc/passwd`);
- `..` traversal (`resolve("..", "..", "sessions")`);
- empty/blank/NUL components;
- symlink escape — the fully resolved path (symlinks followed) must stay under
  the plugin root;
- session IDs or other user input used directly as path components are still
  re-checked for containment.

`remove()` refuses to delete the storage root itself.

## Storage vs configuration

They are different responsibilities and stay in different places:

| | Configuration | Storage |
|---|---|---|
| Path | `.data/plugins/config/<plugin-id>.json` | `.data/plugins/storage/<plugin-id>/` |
| Owner | user/UI-editable, schema-validated | the plugin, directly |
| Size/shape | small, structured | arbitrary files and layouts |
| Core reads it? | yes (validated) | no (opaque) |

## `.data/plugins/cached/` is NOT this

`PLUGIN_CACHE_DIR` (`.data/plugins/cached/`) holds core-owned **installed plugin
archives** (`<plugin-id>/<version>/<hash>/plugin.toml`, see
`src/plugins/store.py`), not plugin-authored runtime files. It is correctly
named `cached`. No migration from `cached/` to `storage/` is needed — they are
separate concerns. The new namespace uses `storage` (persistent), never
`cached` (disposable).

## Lifecycle (data-safety first)

- Install / startup / restart: the namespace is created on first access;
  contents persist across restarts.
- Disable / uninstall: storage is **not** auto-deleted — disabling or removing a
  plugin leaves its data recoverable. Explicit deletion is a future lifecycle
  API, not a side effect.
- Session deletion (`.data/sessions/<id>/`) does not touch a plugin's mirrored
  `sessions/<id>/` inside its own namespace; the plugin owns that cleanup.

## Published-plugin review

The current example/published plugins (`turn_counter`, and the hub's
`character-converter`, `dynamic-character-presence`, `grammar-tools`,
`openrouter-provider`) do not derive `.data/` paths manually today; those that
need to persist generated files should adopt `context.storage`. When several
plugins would need the same helper, add it to `PluginStorage` rather than
letting each work around the abstraction.
