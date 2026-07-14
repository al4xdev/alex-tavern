"""Authoring CLI used by people and the curated repository MCP server."""

from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.plugins.contracts import exported_contract
from src.plugins.journal import read
from src.plugins.manifest import load_manifest
from src.plugins.store import validate_package

BACKEND_TEMPLATE = '''"""{name} plugin."""


def setup(context) -> None:  # noqa: ANN001
    """Register hooks and contributions through the Alex Tavern SDK."""
    context.event("setup_complete")
'''

FRONTEND_TEMPLATE = """export function activate(sdk) {\n    sdk.observe('setup_complete');\n}\n"""


def scaffold_plugin(
    destination: Path,
    plugin_id: str,
    name: str,
    *,
    backend: bool = True,
    frontend: bool = False,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    entrypoints: list[str] = []
    if backend:
        (destination / "backend.py").write_text(
            BACKEND_TEMPLATE.format(name=name), encoding="utf-8"
        )
        entrypoints.append('backend = "backend.py"')
    if frontend:
        (destination / "frontend.js").write_text(FRONTEND_TEMPLATE, encoding="utf-8")
        entrypoints.append('frontend = "frontend.js"')
    if not entrypoints:
        raise ValueError("At least one of backend or frontend must be enabled")
    manifest = f'''schema_version = 1
id = "{plugin_id}"
name = "{name}"
version = "0.1.0"
description = "Describe the user-visible capability."
license = "MIT"
authors = ["Your name"]
permissions = []
dependencies = []

[entrypoints]
{chr(10).join(entrypoints)}

[order]
priority = 0
before = []
after = []

[python]
dependencies = []
'''
    (destination / "plugin.toml").write_text(manifest, encoding="utf-8")
    (destination / "README.md").write_text(
        f"# {name}\n\nExplain behavior, permissions, configuration, and failure modes.\n",
        encoding="utf-8",
    )
    return validate_plugin(destination)


def validate_plugin(package: Path) -> dict[str, Any]:
    manifest = validate_package(package)
    checks: list[str] = ["manifest", "entrypoints"]
    if manifest.entrypoints.backend:
        py_compile.compile(str(package / manifest.entrypoints.backend), doraise=True)
        checks.append("python-syntax")
    if manifest.entrypoints.frontend:
        subprocess.run(
            ["node", "--check", str(package / manifest.entrypoints.frontend)],
            check=True,
            capture_output=True,
            text=True,
        )
        checks.append("javascript-syntax")
    return {"valid": True, "manifest": manifest.public_dict(), "checks": checks}


def pack_plugin(package: Path, output: Path) -> dict[str, Any]:
    manifest = load_manifest(package)
    validate_plugin(package)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            info = zipfile.ZipInfo(str(path.relative_to(package)), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    from src.plugins.store import _sha256

    return {
        "plugin_id": manifest.plugin_id,
        "version": manifest.version,
        "path": str(output),
        "sha256": _sha256(output),
    }


def test_plugin(package: Path) -> dict[str, Any]:
    result = validate_plugin(package)
    tests = package / "tests"
    if tests.is_dir():
        completed = subprocess.run(
            ["uv", "run", "pytest", str(tests)],
            check=True,
            capture_output=True,
            text=True,
        )
        result["tests"] = completed.stdout
    else:
        result["tests"] = "No plugin-local tests directory; contract checks passed."
    return result


def trace_plugin(plugin_id: str, limit: int = 200) -> list[dict[str, Any]]:
    return [event for event in read(limit) if event.get("plugin_id") == plugin_id]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("contract")
    scaffold = commands.add_parser("scaffold")
    scaffold.add_argument("destination", type=Path)
    scaffold.add_argument("--id", required=True)
    scaffold.add_argument("--name", required=True)
    scaffold.add_argument("--frontend", action="store_true")
    scaffold.add_argument("--no-backend", action="store_true")
    validate = commands.add_parser("validate")
    validate.add_argument("package", type=Path)
    test = commands.add_parser("test")
    test.add_argument("package", type=Path)
    pack = commands.add_parser("pack")
    pack.add_argument("package", type=Path)
    pack.add_argument("output", type=Path)
    trace = commands.add_parser("trace")
    trace.add_argument("plugin_id")
    trace.add_argument("--limit", type=int, default=200)
    return parser


def main() -> None:
    args = _parser().parse_args()
    result: Any
    if args.command == "contract":
        result = exported_contract()
    elif args.command == "scaffold":
        result = scaffold_plugin(
            args.destination,
            args.id,
            args.name,
            backend=not args.no_backend,
            frontend=args.frontend,
        )
    elif args.command == "validate":
        result = validate_plugin(args.package)
    elif args.command == "test":
        result = test_plugin(args.package)
    elif args.command == "pack":
        result = pack_plugin(args.package, args.output)
    else:
        result = trace_plugin(args.plugin_id, args.limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
