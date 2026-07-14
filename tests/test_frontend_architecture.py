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
    assert 'id="runtime-auto-compact"' in html
    assert 'id="runtime-auto-compact-threshold"' in html
    assert 'type="range" min="1" max="100"' in html
    assert 'id="compaction-help-btn"' in html
    assert 'id="runtime-compact-turns"' not in html


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
    assert "rpt-shell-v13" in service_worker


def test_setup_modal_is_always_dismissible() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    setup_source = (STATIC / "setup.js").read_text(encoding="utf-8")
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")

    assert 'id="setup-close-btn" type="button"' in html
    assert "closeBtn.addEventListener('click', close);" in setup_source
    assert "if (e.target === overlay) close();" in setup_source
    assert "event.key !== 'Escape'" in setup_source
    assert "closeBtn.style.display" not in setup_source
    assert "hasSession" not in setup_source
    assert "Setup.setHasSession" not in app_source


def test_plugin_center_syncs_catalog_before_listing_experiences() -> None:
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    catalog_sync = "const catalog = await api.getPluginCatalog();"
    experience_fetch = "api.listExperiences(), api.getPlugins(), api.getPluginEvents(),"

    assert catalog_sync in source
    assert experience_fetch in source
    assert source.index(catalog_sync) < source.index(experience_fetch)


def test_plugin_center_confirms_experiences_and_supports_uninstall() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    api_source = (STATIC / "api.js").read_text(encoding="utf-8")

    assert 'id="plugin-confirm-layer"' in html
    assert "showConfirmation({" in source
    assert "api.activateExperience(experience.id)" in source
    assert "api.uninstallPlugin(" in source
    assert "uninstallPlugin(pluginId, version, sha256)" in api_source


def test_plugin_center_groups_releases_and_exposes_reviewed_updates() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    api_source = (STATIC / "api.js").read_text(encoding="utf-8")

    assert "status.plugins.flatMap" in source
    assert "plugin.cached_versions.map" in source
    assert "plugin.state === 'update_available'" in source
    assert "diff.permissions.added" in source
    assert "permission === 'model.call'" in source
    assert "api.updateCuratedPlugin(" in source
    assert "updateCuratedPlugin(pluginId, version, sha256)" in api_source
    assert 'id="plugin-update-count"' in html


def test_plugin_installations_are_reviewed_before_curated_or_external_cache_write() -> None:
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    api_source = (STATIC / "api.js").read_text(encoding="utf-8")

    assert "installationReviewItems(manifest, release.sha256)" in source
    assert "api.inspectPluginFile(file)" in source
    assert "installationReviewItems(manifest, inspected.sha256, { external: true })" in source
    assert source.index("api.inspectPluginFile(file)") < source.index("api.installPluginFile(file)")
    assert "inspectPluginFile(file)" in api_source
    assert "'/plugins/inspect-upload'" in api_source


def test_plugin_center_tabs_are_accessible_and_touch_draggable() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    styles = (STATIC / "style.css").read_text(encoding="utf-8")

    assert html.count('role="tab"') == 3
    assert html.count('role="tabpanel"') == 3
    assert "ArrowLeft" in source and "ArrowRight" in source
    assert "Home: 0" in source and "End: tabNames.length - 1" in source
    assert "['touch', 'pen'].includes(event.pointerType)" in source
    assert "width * 0.25" in source and "Math.abs(velocity) >= 0.5" in source
    assert "reducedMotion.matches" in source
    assert "touch-action: pan-y" in styles
    assert ".plugin-view-track" in styles


def test_empty_session_invites_first_move_and_mobile_input_opens_directly() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    source = (STATIC / "app.js").read_text(encoding="utf-8")
    styles = (STATIC / "style.css").read_text(encoding="utf-8")

    assert 'id="empty-scroll-cue"' in html
    assert "else showEmptyState(true);" in source
    assert "function expandMobileInput" in source
    assert "inputArea.classList.remove('collapsed');" in source
    assert (
        "inputExpandBtn.addEventListener('click', () => {\n        expandMobileInput();" in source
    )
    assert ".empty-state.session-ready" in styles
    assert "min-height: calc(100% + 76px)" in styles


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


def test_transformed_player_input_updates_live_and_persisted_bubbles() -> None:
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")
    i18n_source = (STATIC / "i18n.js").read_text(encoding="utf-8")

    assert "data.effective_input" in app_source
    assert "data.transformed_fields" in app_source
    assert "record.input_transformed === true" in app_source
    assert "'input.adjusted'" in app_source
    assert "Adjusted by plugin" in i18n_source
    assert "Ajustado por plugin" in i18n_source


def test_compaction_progress_is_measured_and_accessible() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")
    api_source = (STATIC / "api.js").read_text(encoding="utf-8")

    assert 'id="compact-progress-status" aria-live="polite"' in html
    assert "estimatedMs" not in app_source
    assert "msgCount = chatLog" not in app_source
    assert "event.completed_units / event.total_units" in app_source
    assert "Accept: 'text/event-stream'" in api_source
    assert "Compaction stream ended without a terminal event" in api_source
    assert "onCompactionHelp" in app_source


def test_browser_compaction_parser_handles_chunked_utf8_and_requires_terminal() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = r"""
globalThis.window = { location: { protocol: 'http:' } };
const encoder = new TextEncoder();
function streamed(text) {
  const bytes = encoder.encode(text);
  return new Response(new ReadableStream({
    start(controller) {
      for (let i = 0; i < bytes.length; i += 7) controller.enqueue(bytes.slice(i, i + 7));
      controller.close();
    },
  }), { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
}
const { api } = await import('./src/static/api.js');
const checking = JSON.stringify({
  operation_id:'c1', sequence:1, stage:'checking', completed_units:0, total_units:0,
});
const completed = JSON.stringify({
  operation_id:'c1', sequence:2, stage:'completed', completed_units:1, total_units:1,
  result:{compacted:true,label:'ação'},
});
globalThis.fetch = async () => streamed(
  `: keepalive\n\nevent: checking\ndata: ${checking}\n\n` +
  `event: completed\ndata: ${completed}\n\n`
);
const stages = [];
const result = await api.compact('abc', event => stages.push(event.stage));
if (stages.join(',') !== 'checking,completed' || result.label !== 'ação') process.exit(2);
globalThis.fetch = async () => streamed(`data: ${checking}\n\n`);
let missingTerminal = false;
try { await api.compact('abc'); } catch (error) {
  missingTerminal = error.message.includes('without a terminal');
}
if (!missingTerminal) process.exit(3);
const duplicate = JSON.stringify({
  operation_id:'c1', sequence:3, stage:'skipped', completed_units:1, total_units:1,
  result:{compacted:false},
});
globalThis.fetch = async () => streamed(
  `data: ${checking}\n\ndata: ${completed}\n\ndata: ${duplicate}\n\n`
);
let duplicateTerminal = false;
try { await api.compact('abc'); } catch (error) {
  duplicateTerminal = error.message.includes('multiple terminal');
}
if (!duplicateTerminal) process.exit(4);
"""
    subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
