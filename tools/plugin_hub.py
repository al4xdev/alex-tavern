"""Sync the curated source hub over HTTPS and install reviewed fixed-hash artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.plugins.hub import DEFAULT_REPOSITORY, sync_hub
from src.plugins.store import install_curated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync")
    sync.add_argument("--repository", default=DEFAULT_REPOSITORY)
    install = commands.add_parser("install")
    install.add_argument("plugin_id")
    install.add_argument("--version")
    args = parser.parse_args()
    result = (
        sync_hub(args.repository)
        if args.command == "sync"
        else install_curated(args.plugin_id, args.version)
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
