"""Real child-process supervisor used for plugin and Experience restarts."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

RESTART_EXIT_CODE = 75


def request_restart() -> bool:
    """Ask the supervising parent to replace this server process."""
    if os.environ.get("ROLEPLAY_SUPERVISED") != "1":
        return False
    os.kill(os.getppid(), signal.SIGUSR1)
    return True


def supervise(host: str, port: int) -> int:
    restart_requested = threading.Event()
    child: subprocess.Popen[bytes] | None = None

    def restart(_signum: int, _frame: object) -> None:
        restart_requested.set()
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGUSR1, restart)
    while True:
        restart_requested.clear()
        environment = {**os.environ, "ROLEPLAY_SUPERVISED": "1"}
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=Path(__file__).resolve().parent.parent,
            env=environment,
        )
        try:
            code = child.wait()
        except KeyboardInterrupt:
            if child.poll() is None:
                child.terminate()
                child.wait()
            return 130
        if restart_requested.is_set() or code == RESTART_EXIT_CODE:
            continue
        return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8889)
    args = parser.parse_args()
    return supervise(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
