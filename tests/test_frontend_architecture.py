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
    assert 'id="input-speech"' in html
    assert 'id="input-thought"' in html
    assert 'id="input-action"' in html
    assert 'id="interface-language"' in html
    assert '<option value="en">English</option>' in html
    assert '<option value="pt-BR">Português (Brasil)</option>' in html
    assert 'id="runtime-language"' not in html


def test_frontend_modules_use_explicit_imports_instead_of_shared_app_globals() -> None:
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")
    setup_source = (STATIC / "setup.js").read_text(encoding="utf-8")
    runtime_source = (STATIC / "runtime-config.js").read_text(encoding="utf-8")
    assert "import { api } from './api.js';" in app_source
    assert "import { Setup } from './setup.js';" in app_source
    assert "from './i18n.js';" in app_source
    assert "export const Setup" in setup_source
    assert "export const RuntimeConfig" in runtime_source
    assert "language: getLlmLanguage()" in runtime_source
    assert "queueLanguageSync();" in runtime_source
    assert "typeof RuntimeConfig" not in setup_source
    assert "typeof toast" not in setup_source
    assert "input: e.input," in app_source


def test_i18n_is_versioned_and_available_in_the_offline_shell() -> None:
    i18n_source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    service_worker = (STATIC / "sw.js").read_text(encoding="utf-8")

    assert "rpt_interface_locale_v1" in i18n_source
    assert "const DEFAULT_LOCALE = 'en';" in i18n_source
    assert "'/i18n.js'" in service_worker
    assert "rpt-shell-v6" in service_worker


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
