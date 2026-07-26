# A healthy server that could not publish: Android, Chaquopy, and plugin-tree integrity

| | |
|---|---|
| **Series** | Alex Tavern Engineering Cases, No. 17 |
| **Date** | 2026-07-25 |
| **Kind** | Incident reconstruction + boundary redesign |
| **Roadmap** | Task 51 (`.plan/tasks/51-android-runtime-and-plugin-integrity.md`) |
| **Commits** | `36942a9`, `f758b56`, `4865672`, `8bd5c4e` |
| **Status** | Implementation and build delivered; exact old/new PID device capture remains open |

## Abstract

The first Android failure looked like a Python-server outage, then like an Android
storage-permission problem. Neither diagnosis survived the boundary evidence. Uvicorn
was healthy and the application could write its private directory. The failures were
caused by two independent integration defects: the Kotlin-to-Python bridge did not
actually mutate `os.environ` before path modules imported, and Python's high-level tree
copy preserved filesystem metadata that Android's private-directory/SELinux boundary
would not permit. After those were removed, hub synchronization and all six curated
plugin installations completed on the device. A third defect appeared only after
activation: reloading a WebView cannot replace the in-process Chaquopy interpreter.
The resulting design keeps the generic plugin API unchanged but delegates Android
process replacement to a non-exported relay Activity in a separate process.

## 1. Competing hypotheses

The investigation began with three plausible explanations:

1. Python never started, so HTTP 500 represented an unhealthy backend.
2. Android denied ordinary writes under the application's private directory.
3. A successful plugin mutation was not being applied because only the browser reloaded.

The evidence separated them. `/health` answered after boot, so a failing endpoint was
not proof of a dead server. Every reported `EACCES` occurred while copying an extracted
tree from Chaquopy's cache into `files/data/plugins`; ordinary files and configuration
already existed under the same private root. Finally, activation pointers changed while
the old Python runtime remained resident, distinguishing persistence from application.

## 2. Root cause A: configuration crossed the bridge in the wrong form

`src.paths` resolves runtime directories at import time. The old Kotlin code obtained
Python's `os.environ` through a generic `PyObject` and called `put`. Under Chaquopy this
did not perform the environment mutation on which later imports depended.

The replacement makes the boundary explicit:

```text
MainActivity
  └─ android_runner.start_server(filesDir/data)
       ├─ os.environ["ROLEPLAY_DATA_DIR"] = data_dir
       └─ import src.main
```

The data directory is now set in Python before any `src` import. No Android-specific
path branch was introduced in the backend; the deployment supplies the canonical
`ROLEPLAY_DATA_DIR` contract like every other deployment.

## 3. Root cause B: bytes were writable; metadata was not portable

Both hub publication and third-party/curated package installation used
`shutil.copytree`. Its default `copy2` behavior calls `copystat`, attempting to preserve
mode, timestamps and extended attributes. Android rejected that metadata operation
even after file bytes had copied, producing long lists of misleading destination-side
`PermissionError` entries.

Plugin runtime trees do not derive authority from source filesystem metadata. Their
authority comes from validated paths, strict manifests and fixed SHA-256 hashes.
`copy_tree_contents` therefore publishes only structure and bytes:

- destination directories are created fresh;
- regular files use `copyfile`;
- symbolic links and irregular entries are rejected;
- a failed staging tree is removed;
- the existing atomic stage/replace protocol remains intact.

The helper is shared by hub snapshots and immutable plugin packages, so the second
failure was fixed at the same ownership boundary rather than by an Android conditional.
Regression tests monkeypatch `copystat` to always raise `EACCES`; both publication paths
still succeed, proving they no longer depend on metadata copying.

## 4. Root cause C: reload is not restart

The plugin API correctly batches activation changes and calls `/plugins/restart` when
the Plugin Center closes. On desktop, the supervisor replaces its Uvicorn child. Inside
the APK, Python and Uvicorn live in the Android application process; `location.reload()`
only reconstructed JavaScript and therefore preserved the old plugin registry.

The Android shell now exposes a narrowly scoped `AlexTavernAndroid.restartApplication`
bridge. It accepts calls only while the WebView is displaying the local server or the
packaged fallback. A non-exported `RestartActivity`, declared in `:restart`, receives
the main PID, kills that process, waits 350 ms and launches a clean application task.
The bridge is optional: ordinary web deployments retain the existing reload fallback.

This design preserves three security/ownership properties:

- the core plugin SDK contains no Android branch;
- an arbitrary remote WebView page cannot invoke the restart;
- the relay is not exported and cannot be launched by another application.

## 5. Measured result

| Boundary | Evidence | Result |
|---|---|---|
| Backend boot | Physical-device `/health` and `/version` during the session | Healthy |
| Hub publication | Curated catalog materialized after the metadata-copy fix | Passed |
| Package publication | Six curated install responses recorded with immutable cache paths | 6/6 passed |
| Static/package paths | Android regression suite imports from an unrelated CWD and stamps `version.txt` | Passed |
| Current build | Docker/Gradle `assembleDebug`, package `com.al4xdev.alextavern`, version `0.1` | Passed |
| Current APK | SHA-256 `c4836235b975276f0315c8872d5c8bc50e29c50db4ff633ed93fdb42fab164a0` | Recorded |
| Focused regression | Android packaging + frontend architecture + plugins | 62/62 passed |
| Full regression | `pytest -x`; Ruff format/check; mypy | 785 passed, 2 deselected; clean |
| Process replacement | Source/manifest contract and APK compilation | Passed |
| Physical old/new PID pair | ADB unavailable in the final restricted process | **Open gate** |

## 6. Limitations and falsifiable closure gate

The relay is compiled, structurally test-pinned, and follows Android's documented
process boundary, but implementation plausibility is not a PID measurement. Task 51
therefore remains active until one physical run records:

1. PID before an activation/deactivation;
2. Plugin Center close;
3. a different main PID after relaunch;
4. `/plugins` showing the selected active set after the new `/health` succeeds.

This limitation is deliberately narrow. It does not reopen the data-directory,
hub-publication or package-install findings, each of which already crossed its real
device boundary.

## Conclusion

The incident was not “Python versus Android permissions.” It was three ownership
mistakes that happened to surface on Android: implicit bridge mutation, accidental
metadata preservation, and confusing browser lifecycle with process lifecycle.
Replacing each with an explicit boundary kept the canonical backend and plugin runtime
portable while making the APK diagnosable and reproducible.
