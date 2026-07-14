"""Sync the curated source hub with git and install reviewed fixed-hash artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paths import EXPERIENCES_DIR, PLUGIN_HUB_DIR
from src.plugins.store import curated_catalog, install_curated

DEFAULT_REPOSITORY = "https://github.com/al4xdev/alex-tavern-plugins.git"


def sync_hub(repository: str = DEFAULT_REPOSITORY) -> dict[str, Any]:
    """Clone a fresh reviewed snapshot, then atomically expose it to the runtime."""
    PLUGIN_HUB_DIR.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="alex-tavern-hub-") as temporary_name:
        checkout = Path(temporary_name) / "checkout"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", repository, str(checkout)],
            check=True,
        )
        catalog = json.loads((checkout / "catalog.json").read_text(encoding="utf-8"))
        if catalog.get("schema_version") != 1:
            raise ValueError("Hub catalog must use schema_version 1")
        staged = PLUGIN_HUB_DIR.with_name(f".{PLUGIN_HUB_DIR.name}.staged")
        previous = PLUGIN_HUB_DIR.with_name(f".{PLUGIN_HUB_DIR.name}.previous")
        for path in (staged, previous):
            if path.exists():
                shutil.rmtree(path)
        shutil.copytree(checkout, staged, ignore=shutil.ignore_patterns(".git"))
        if PLUGIN_HUB_DIR.exists():
            PLUGIN_HUB_DIR.replace(previous)
        staged.replace(PLUGIN_HUB_DIR)
        if previous.exists():
            shutil.rmtree(previous)

    EXPERIENCES_DIR.mkdir(parents=True, exist_ok=True)
    installed_experiences: list[str] = []
    for entry in curated_catalog()["experiences"]:
        if not isinstance(entry, dict):
            continue
        manifest = (PLUGIN_HUB_DIR / str(entry.get("manifest", ""))).resolve()
        if PLUGIN_HUB_DIR.resolve() not in manifest.parents or not manifest.is_file():
            raise ValueError(f"Invalid Experience manifest path: {manifest}")
        value = json.loads(manifest.read_text(encoding="utf-8"))
        image = entry.get("image")
        if isinstance(image, str) and image:
            source_image = (PLUGIN_HUB_DIR / image).resolve()
            if PLUGIN_HUB_DIR.resolve() not in source_image.parents or not source_image.is_file():
                raise ValueError(f"Invalid Experience image path: {source_image}")
            target_image = EXPERIENCES_DIR / "assets" / source_image.name
            target_image.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_image, target_image)
            value["image"] = f"/experiences/assets/{source_image.name}"
        from src.plugins.experiences import save_experience

        save_experience(value)
        installed_experiences.append(str(value["id"]))
    return {
        "repository": repository,
        "plugins": len(curated_catalog()["plugins"]),
        "experiences": installed_experiences,
    }


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
