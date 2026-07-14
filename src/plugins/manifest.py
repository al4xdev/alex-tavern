"""Strict, forward-only plugin and Experience manifest contracts."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Any

PLUGIN_API_VERSION = 1
_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


class ManifestError(ValueError):
    """Raised when a package does not implement the current plugin contract."""


@total_ordering
@dataclass(frozen=True, slots=True)
class SemanticVersion:
    """SemVer 2.0 precedence value; build metadata does not affect ordering."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> SemanticVersion:
        match = _VERSION_RE.fullmatch(value)
        if match is None:
            raise ManifestError(f"Invalid semantic version: {value}")
        prerelease = tuple((match.group(4) or "").split(".")) if match.group(4) else ()
        build = tuple((match.group(5) or "").split(".")) if match.group(5) else ()
        if any(part.isdigit() and len(part) > 1 and part.startswith("0") for part in prerelease):
            raise ManifestError(f"Invalid semantic version: {value}")
        return cls(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            prerelease,
            build,
        )

    def _compare_prerelease(self, other: SemanticVersion) -> int:
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for left, right in zip(self.prerelease, other.prerelease, strict=False):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                return -1 if int(left) < int(right) else 1
            if left_numeric != right_numeric:
                return -1 if left_numeric else 1
            return -1 if left < right else 1
        if len(self.prerelease) == len(other.prerelease):
            return 0
        return -1 if len(self.prerelease) < len(other.prerelease) else 1

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        return core < other_core or (core == other_core and self._compare_prerelease(other) < 0)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (
            self.major,
            self.minor,
            self.patch,
            self.prerelease,
        ) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )


def compare_versions(left: str, right: str) -> int:
    """Return SemVer precedence without treating build metadata as a release update."""
    parsed_left = SemanticVersion.parse(left)
    parsed_right = SemanticVersion.parse(right)
    return (parsed_left > parsed_right) - (parsed_left < parsed_right)


@dataclass(frozen=True, slots=True)
class Entrypoints:
    backend: str | None = None
    frontend: str | None = None


@dataclass(frozen=True, slots=True)
class Dependency:
    plugin_id: str
    version: str = "*"
    optional: bool = False


@dataclass(frozen=True, slots=True)
class PluginManifest:
    schema_version: int
    plugin_id: str
    name: str
    version: str
    description: str
    license: str
    authors: tuple[str, ...]
    permissions: tuple[str, ...]
    entrypoints: Entrypoints
    dependencies: tuple[Dependency, ...] = ()
    before: tuple[str, ...] = ()
    after: tuple[str, ...] = ()
    priority: int = 0
    python_dependencies: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "license": self.license,
            "authors": list(self.authors),
            "permissions": list(self.permissions),
            "entrypoints": {
                "backend": self.entrypoints.backend,
                "frontend": self.entrypoints.frontend,
            },
            "dependencies": [
                {
                    "plugin_id": item.plugin_id,
                    "version": item.version,
                    "optional": item.optional,
                }
                for item in self.dependencies
            ],
            "before": list(self.before),
            "after": list(self.after),
            "priority": self.priority,
            "python_dependencies": list(self.python_dependencies),
        }


def _string(value: object, field_name: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ManifestError(f"{field_name} must be a non-empty string")
    return value.strip()


def _strings(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ManifestError(f"{field_name} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


def _entrypoint(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    path = _string(value, field_name)
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ManifestError(f"{field_name} must be a package-relative path")
    return path


def parse_manifest(value: dict[str, Any]) -> PluginManifest:
    allowed = {
        "schema_version",
        "id",
        "name",
        "version",
        "description",
        "license",
        "authors",
        "permissions",
        "entrypoints",
        "dependencies",
        "order",
        "python",
    }
    unknown = set(value) - allowed
    if unknown:
        raise ManifestError(f"Unknown manifest fields: {', '.join(sorted(unknown))}")
    if value.get("schema_version") != PLUGIN_API_VERSION:
        raise ManifestError(f"schema_version must be {PLUGIN_API_VERSION}")
    plugin_id = _string(value.get("id"), "id")
    if not _ID_RE.fullmatch(plugin_id):
        raise ManifestError("id must be a lowercase dotted/dashed identifier")
    version = _string(value.get("version"), "version")
    if not _VERSION_RE.fullmatch(version):
        raise ManifestError("version must use semantic versioning")

    raw_entrypoints = value.get("entrypoints")
    if not isinstance(raw_entrypoints, dict):
        raise ManifestError("entrypoints must be a table")
    if set(raw_entrypoints) - {"backend", "frontend"}:
        raise ManifestError("entrypoints only accepts backend and frontend")
    entrypoints = Entrypoints(
        backend=_entrypoint(raw_entrypoints.get("backend"), "entrypoints.backend"),
        frontend=_entrypoint(raw_entrypoints.get("frontend"), "entrypoints.frontend"),
    )
    if not entrypoints.backend and not entrypoints.frontend:
        raise ManifestError("at least one entrypoint is required")

    dependencies: list[Dependency] = []
    raw_dependencies = value.get("dependencies", [])
    if not isinstance(raw_dependencies, list):
        raise ManifestError("dependencies must be an array of tables")
    for index, raw in enumerate(raw_dependencies):
        if not isinstance(raw, dict) or set(raw) - {"id", "version", "optional"}:
            raise ManifestError(f"dependencies[{index}] is invalid")
        dependency_id = _string(raw.get("id"), f"dependencies[{index}].id")
        if not _ID_RE.fullmatch(dependency_id):
            raise ManifestError(f"dependencies[{index}].id is invalid")
        optional = raw.get("optional", False)
        if not isinstance(optional, bool):
            raise ManifestError(f"dependencies[{index}].optional must be boolean")
        dependencies.append(
            Dependency(dependency_id, _string(raw.get("version", "*"), "version"), optional)
        )

    order = value.get("order", {})
    python = value.get("python", {})
    if not isinstance(order, dict) or set(order) - {"before", "after", "priority"}:
        raise ManifestError("order must contain only before, after, and priority")
    if not isinstance(python, dict) or set(python) - {"dependencies"}:
        raise ManifestError("python must contain only dependencies")
    priority = order.get("priority", 0)
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ManifestError("order.priority must be an integer")
    authors = _strings(value.get("authors"), "authors")
    if not authors:
        raise ManifestError("authors cannot be empty")
    return PluginManifest(
        schema_version=PLUGIN_API_VERSION,
        plugin_id=plugin_id,
        name=_string(value.get("name"), "name"),
        version=version,
        description=_string(value.get("description"), "description", empty=True),
        license=_string(value.get("license"), "license"),
        authors=authors,
        permissions=_strings(value.get("permissions", []), "permissions"),
        entrypoints=entrypoints,
        dependencies=tuple(dependencies),
        before=_strings(order.get("before", []), "order.before"),
        after=_strings(order.get("after", []), "order.after"),
        priority=priority,
        python_dependencies=_strings(python.get("dependencies", []), "python.dependencies"),
    )


def load_manifest(package_dir: Path) -> PluginManifest:
    path = package_dir / "plugin.toml"
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ManifestError(f"Cannot read {path}: {error}") from error
    return parse_manifest(raw)


def satisfies_version(version: str, expression: str) -> bool:
    """Evaluate the small semver constraint language used by plugin dependencies."""

    actual = SemanticVersion.parse(version)
    if expression.strip() in {"", "*"}:
        return True
    for raw_constraint in expression.split(","):
        constraint = raw_constraint.strip()
        operator = next(
            (
                candidate
                for candidate in (">=", "<=", ">", "<", "^", "~", "=")
                if constraint.startswith(candidate)
            ),
            "=",
        )
        expected = SemanticVersion.parse(constraint.removeprefix(operator).strip())
        if operator == ">=" and actual < expected:
            return False
        if operator == "<=" and actual > expected:
            return False
        if operator == ">" and actual <= expected:
            return False
        if operator == "<" and actual >= expected:
            return False
        if operator == "=" and actual != expected:
            return False
        if operator == "^" and not (actual >= expected and actual.major == expected.major):
            return False
        if operator == "~" and not (
            actual >= expected and (actual.major, actual.minor) == (expected.major, expected.minor)
        ):
            return False
    return True
