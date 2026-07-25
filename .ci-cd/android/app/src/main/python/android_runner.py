"""Entry point Chaquopy calls to run the backend inside the Android app.

Everything here exists so a failure is *visible*. A bare ``uvicorn.run`` sends
its traceback to the Chaquopy stderr bridge only, where it is easy to miss and
often truncated; without a stacktrace nobody can tell an import error apart from
a bind failure apart from no network. So every path also lands in
``<filesDir>/bootstrap.log``, which MainActivity renders on screen and the
``/bootstrap_log`` endpoint serves.
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8889


def _log_path() -> Path | None:
    """Sibling of the data dir, matching where MainActivity writes its log."""
    data_dir = os.environ.get("ROLEPLAY_DATA_DIR")
    if not data_dir:
        return None
    return Path(data_dir).parent / "bootstrap.log"


def log(message: str) -> None:
    """Append to the on-device bootstrap log and mirror it to stderr."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{stamp}] runner: {message}"
    print(line, file=sys.stderr, flush=True)
    path = _log_path()
    if path is None:
        return
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as error:
        # Never let logging be the thing that takes the server down.
        print(f"{line} (bootstrap.log unwritable: {error})", file=sys.stderr, flush=True)


def start_server(data_dir: str) -> None:
    """Run uvicorn in the calling thread, reporting whatever goes wrong.

    The Android boundary passes ``filesDir/data`` explicitly. Mutating a Python
    mapping through Chaquopy's generic ``PyObject.put`` does not update
    ``os.environ``; configure it here before importing any ``src`` module,
    because :mod:`src.paths` resolves all runtime paths at import time.

    Catching ``BaseException`` is deliberate: uvicorn raises ``SystemExit`` when
    the port is already bound or the app fails to import, and that is exactly
    the case this log exists to capture.
    """
    os.environ["ROLEPLAY_DATA_DIR"] = data_dir
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    try:
        log(f"python {sys.version.split()[0]} | data dir {data_dir}")

        import uvicorn

        # Imported eagerly so an import-time failure is reported as one, instead
        # of surfacing as an opaque uvicorn startup error.
        import src.main
        from src.paths import STATIC_DIR

        # First thing worth knowing when a build misbehaves: which build is it.
        log(f"build commit {src.main.get_git_commit()}")

        # Whether Chaquopy extracts the non-.py files under src/static decides
        # if the frontend can be served over HTTP; MainActivity falls back to
        # the APK assets when it cannot. Record which way it went.
        if STATIC_DIR.is_dir():
            log(f"static dir {STATIC_DIR} present ({len(list(STATIC_DIR.iterdir()))} entries)")
        else:
            log(f"static dir {STATIC_DIR} MISSING; frontend will fall back to APK assets")

        log(f"app imported, binding {HOST}:{PORT}")
        uvicorn.run("src.main:app", host=HOST, port=PORT, log_level="info")
        log("uvicorn returned; server stopped")
    except BaseException:
        log("server failed:\n" + traceback.format_exc())
        raise
