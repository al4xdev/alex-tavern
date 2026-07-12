"""Static architecture checks for the dependency-free ES-module frontend."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "static"


def test_frontend_entrypoint_uses_modules_without_provider_markup() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert '<script type="module" src="app.js"></script>' in html
    assert 'data-provider="llama_cpp"' not in html
    assert 'data-provider="deepseek"' not in html
    assert 'id="provider-switch"' in html
    assert 'id="provider-panels"' in html


def test_frontend_modules_use_explicit_imports_instead_of_shared_app_globals() -> None:
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")
    setup_source = (STATIC / "setup.js").read_text(encoding="utf-8")
    runtime_source = (STATIC / "runtime-config.js").read_text(encoding="utf-8")
    assert "import { api } from './api.js';" in app_source
    assert "import { Setup } from './setup.js';" in app_source
    assert "export const Setup" in setup_source
    assert "export const RuntimeConfig" in runtime_source
    assert "typeof RuntimeConfig" not in setup_source
    assert "typeof toast" not in setup_source


def test_frontend_adapter_registry_loads_both_provider_modules() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = (
        "const m=await import('./src/static/adapters/index.js');"
        "const ids=[...m.providerAdapterMap.keys()];"
        "if(ids.join(',')!=='llama_cpp,deepseek')process.exit(2);"
    )
    subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
