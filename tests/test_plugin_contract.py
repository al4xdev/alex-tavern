"""The exported plugin contract must describe the hooks the core actually fires.

``src/plugins/contracts.py`` is what the curated hub, ``tools/plugin_author.py``
and the agent MCPs read to scaffold and validate a plugin. Nothing linked it to
the call sites, so renaming a hook in the runner would have left the hub
generating plugins that register a hook nobody ever fires — silently, with no
error anywhere. This test is that link.
"""

from __future__ import annotations

import ast
import pathlib

from src.plugins.contracts import HOOK_CONTRACTS, Hook, exported_contract

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"

# HookRegistry method -> the kind of registration it dispatches.
DISPATCH_KINDS = {
    "action": "action",
    "action_sync": "action",
    "filter": "filter",
    "filter_strict": "filter",
    "filter_for_plugin": "filter",
    "filter_sync": "filter",
    "call_wrapped": "wrapper",
}


def _fired_hooks() -> dict[str, set[str]]:
    """Every ``hooks.<method>("name")`` in src/, mapped to the kinds dispatched."""
    fired: dict[str, set[str]] = {}
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            kind = DISPATCH_KINDS.get(node.func.attr)
            if kind is None or not node.args:
                continue
            target = node.args[0]
            name: str | None = None
            if isinstance(target, ast.Constant) and isinstance(target.value, str):
                name = target.value
            elif (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "Hook"
            ):
                name = getattr(Hook, target.attr)
            if name is not None:
                fired.setdefault(name, set()).add(kind)
    return fired


def test_every_fired_hook_is_documented() -> None:
    undocumented = sorted(set(_fired_hooks()) - set(HOOK_CONTRACTS))
    assert undocumented == [], (
        f"these hooks fire but the exported contract does not describe them: {undocumented}"
    )


def test_every_documented_hook_is_fired() -> None:
    """A documented hook nobody fires is a promise the core does not keep."""
    dead = sorted(set(HOOK_CONTRACTS) - set(_fired_hooks()))
    assert dead == [], f"the contract documents hooks the core never fires: {dead}"


def test_declared_kind_matches_the_dispatch_used() -> None:
    mismatches = []
    for name, kinds in sorted(_fired_hooks().items()):
        declared = HOOK_CONTRACTS[name]["kind"]
        if declared not in kinds:
            mismatches.append(f"{name}: declared {declared!r}, dispatched as {sorted(kinds)}")
    assert mismatches == []


def test_hook_constants_cover_the_contract_exactly() -> None:
    constants = {
        value
        for name, value in vars(Hook).items()
        if not name.startswith("_") and isinstance(value, str)
    }
    assert constants == set(HOOK_CONTRACTS)


def test_exported_contract_states_the_core_it_came_from() -> None:
    """The hub must be able to refuse a scaffold generated against another core."""
    contract = exported_contract()
    assert contract["core_version"]["session_schema"] >= 13
    assert contract["core_version"]["hooks"] == len(HOOK_CONTRACTS)
