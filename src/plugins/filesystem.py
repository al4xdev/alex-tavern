"""Filesystem operations shared by plugin snapshot and package publication."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


class TreeCopyError(OSError):
    """A source tree contains an entry that cannot be published safely."""


def copy_tree_contents(root: Path, destination: Path) -> None:
    """Copy a private runtime tree without permissions, timestamps, or xattrs.

    Android/Python 3.11 raises ``EACCES`` when ``shutil.copytree`` tries to copy
    SELinux extended attributes from the app cache into its private files
    directory. Runtime plugin trees need structure and bytes only.
    """
    if not root.is_dir():
        raise TreeCopyError(f"Plugin source tree is not a directory: {root}")
    destination.mkdir()
    try:
        for current_name, directory_names, file_names in os.walk(root):
            current = Path(current_name)
            target = destination / current.relative_to(root)
            target.mkdir(parents=True, exist_ok=True)
            for name in directory_names:
                source = current / name
                if source.is_symlink():
                    raise TreeCopyError(f"Plugin source tree contains a symbolic link: {source}")
                (target / name).mkdir(exist_ok=True)
            for name in file_names:
                source = current / name
                if source.is_symlink() or not source.is_file():
                    raise TreeCopyError(f"Plugin source tree contains an invalid file: {source}")
                shutil.copyfile(source, target / name)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
