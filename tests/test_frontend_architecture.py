"""Static architecture checks for the dependency-free ES-module frontend."""

# ruff: noqa: E501 -- embedded JavaScript harnesses remain readable at their native width.

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
    assert "rpt-shell-v16" in service_worker
    assert "'/slash-commands.js'" in service_worker
    assert "'/slash-command-parser.js'" in service_worker
    assert "'/slash-registry.js'" in service_worker


def test_slash_parser_autocomplete_resolution_and_literal_escape() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = r"""
        const m = await import('./src/static/slash-command-parser.js');
        const terms = (en, pt) => ({en, 'pt-BR': pt});
        const catalog = [
          {name: 'convert-character', aliases: terms(['character'], ['personagem']),
           title: terms('Convert character', 'Converter personagem'),
           keywords: terms(['preset'], ['predefinição']), scope: 'session', available: true, order: 1},
          {name: 'settings', aliases: terms([], ['configuracoes']),
           title: terms('Settings', 'Configurações'), keywords: terms(['engine'], ['motor']),
           scope: 'global', available: true, order: 0},
        ];
        const assert = (value, message) => { if (!value) throw new Error(message); };
        assert(m.matchingCommands('/con', catalog, {locale: 'en'})[0].name === 'convert-character', 'name prefix');
        assert(m.matchingCommands('/person', catalog, {locale: 'pt-BR'})[0].name === 'convert-character', 'alias prefix');
        assert(m.matchingCommands('/predefinicao', catalog, {locale: 'pt-BR'})[0].name === 'convert-character', 'diacritic keyword');
        assert(m.matchingCommands('/configurações', catalog, {locale: 'pt-BR'})[0].name === 'settings', 'diacritic alias');
        const resolved = m.resolveCommand('/personagem', catalog);
        assert(resolved.command.name === 'convert-character', 'resolution');
        assert(resolved.rest === '', 'no hidden arguments');
        assert(m.resolveCommand('/unknown', catalog) === null, 'unknown command');
        const literal = m.tokenizeSlash('//waves');
        assert(literal.kind === 'literal' && literal.speech === '/waves', 'literal escape');
        assert(m.matchingCommands('/zzzz', catalog).length === 0, 'zero results');
    """
    subprocess.run(
        [node, "--no-warnings", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_slash_registry_rejects_collisions_and_foreign_result_namespaces() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = r"""
        const m = await import('./src/static/slash-registry.js');
        const descriptor = (name, alias = []) => ({
          name, title: {en: 'Action', 'pt-BR': 'Ação'},
          summary: {en: 'Summary', 'pt-BR': 'Resumo'}, icon: '✦',
          aliases: {en: alias, 'pt-BR': []}, keywords: {en: [], 'pt-BR': []}, scope: 'global',
        });
        m.registerCoreAction(descriptor('help', ['guide']), () => {});
        let collision = false;
        try { m.registerPluginAction('dev.test', 'Test', descriptor('other', ['guide']), () => {}); }
        catch (error) { collision = error.message.includes('/guide'); }
        if (!collision) throw new Error('alias collision was accepted');
        let namespace = false;
        try { m.registerPluginCommandResultRenderer('dev.test', 'other/result', () => {}); }
        catch (error) { namespace = error.message.includes('dev.test/'); }
        if (!namespace) throw new Error('foreign result namespace was accepted');
    """
    subprocess.run(
        [node, "--no-warnings", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_session_list_renders_compatible_and_incompatible_cards() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = r"""
        import fs from 'node:fs';
        import vm from 'node:vm';

        class Classes {
          constructor() { this.values = new Set(); }
          add(...names) { names.forEach((name) => this.values.add(name)); }
          remove(...names) { names.forEach((name) => this.values.delete(name)); }
          toggle(name) {
            if (this.values.has(name)) this.values.delete(name); else this.values.add(name);
          }
        }
        class Element {
          constructor(tag = 'div') {
            this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {};
            this.attributes = {}; this.listeners = {}; this.classList = new Classes();
            this.className = ''; this.textContent = '';
          }
          set innerHTML(value) { if (value === '') this.children = []; }
          addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); }
          dispatchEvent(event) { (this.listeners[event.type] || []).forEach((handler) => handler(event)); }
          append(...items) { this.children.push(...items); }
          appendChild(item) { this.children.push(item); return item; }
          setAttribute(name, value) { this.attributes[name] = String(value); }
        }

        const app = fs.readFileSync('./src/static/app.js', 'utf8');
        const start = app.indexOf('function renderSessionList(sessions)');
        const end = app.indexOf('/* Clears the chat log', start);
        if (start < 0 || end < 0) throw new Error('renderSessionList source not found');

        const sessionList = new Element();
        const loaded = []; const forked = []; const notices = [];
        const sessions = [
          {session_id: 'current', compatible: true, characters: [{name: 'Lyra'}], turn_count: 2},
          {session_id: 'legacy', compatible: false, schema_version: 1, characters: [{name: 'Nox'}]},
        ];
        const context = {
          api: {
            forkSession: async (sessionId) => { forked.push(sessionId); return {session_id: 'copy'}; },
            listSessions: async () => sessions,
          },
          bindTranslation() {}, clearTimeout, confirm: () => false,
          document: {createElement: (tag) => new Element(tag)}, lastSessionList: null,
          loadSession: (sessionId) => loaded.push(sessionId), sessionList, setTimeout, state: {sessionId: null},
          t: (key, values = {}) => key === 'sessions.turns' ? `${values.count} turns` : key,
          timeAgo: () => 'now', toast: (message) => notices.push(message),
        };
        vm.createContext(context);
        vm.runInContext(`${app.slice(start, end)}\nthis.renderSessionList = renderSessionList;`, context);
        context.renderSessionList(sessions);

        const assert = (value, message) => { if (!value) throw new Error(message); };
        assert(sessionList.children.length === 2, 'both session cards must remain visible');
        const actionNames = (card) => card.children.at(-1).children.map((button) => button.dataset.action);
        assert(actionNames(sessionList.children[0]).join(',') === 'fork,delete',
          'compatible session actions are wrong');
        assert(actionNames(sessionList.children[1]).join(',') === 'delete',
          'incompatible session must only allow deletion');
        sessionList.children[1].dispatchEvent({type: 'click', target: {closest: () => null}});
        assert(loaded.length === 0 && notices.at(-1) === 'sessions.incompatibleToast',
          'incompatible session was not blocked');
        const forkButton = sessionList.children[0].children.at(-1).children[0];
        await forkButton.listeners.click[0]({stopPropagation() {}});
        assert(forked.join(',') === 'current', 'compatible session did not keep its fork action');
        assert(sessionList.children.length === 2, 'fork refresh did not render the complete list');
    """
    subprocess.run(
        [node, "--no-warnings", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_slash_palette_dom_harness_button_keyboard_form_and_renderer() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    script = r"""
        class Classes {
          constructor() { this.values = new Set(); }
          add(...names) { names.forEach((name) => this.values.add(name)); }
          remove(...names) { names.forEach((name) => this.values.delete(name)); }
          toggle(name, force) {
            if (force === undefined ? !this.values.has(name) : force) this.values.add(name);
            else this.values.delete(name);
          }
          contains(name) { return this.values.has(name); }
        }
        class Element {
          constructor(tag = 'div', id = '') {
            this.tagName = tag.toUpperCase(); this.id = id; this.hidden = false;
            this.children = []; this.dataset = {}; this.attributes = {}; this.listeners = {};
            this.classList = new Classes(); this.value = ''; this.files = []; this.textContent = '';
          }
          addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); }
          dispatchEvent(event) { (this.listeners[event.type] || []).forEach((handler) => handler(event)); return true; }
          click() { this.dispatchEvent({type: 'click', preventDefault() {}}); }
          append(...items) { this.children.push(...items); }
          appendChild(item) { this.children.push(item); return item; }
          replaceChildren(...items) { this.children = items; }
          setAttribute(name, value) { this.attributes[name] = String(value); }
          getAttribute(name) { return this.attributes[name]; }
          removeAttribute(name) { delete this.attributes[name]; }
          focus() { document.activeElement = this; }
          scrollIntoView() {}
          querySelector(selector) {
            const all = this.querySelectorAll(selector); return all[0] || null;
          }
          querySelectorAll(selector) {
            const result = [];
            const matches = (item) => {
              if (selector === 'input, textarea') return ['INPUT', 'TEXTAREA'].includes(item.tagName);
              if (selector === '[aria-invalid="true"]') return item.attributes['aria-invalid'] === 'true';
              const id = selector.match(/^#(.+)$/); if (id) return item.id === id[1];
              const data = selector.match(/^\[data-command-(field|error)="(.+)"\]$/);
              if (data) return item.dataset[data[1] === 'field' ? 'commandField' : 'commandError'] === data[2];
              if (selector === '.command-field-error') return item.className === 'command-field-error';
              return false;
            };
            const visit = (item) => { if (matches(item)) result.push(item); item.children.forEach(visit); };
            this.children.forEach(visit); return result;
          }
        }
        const ids = ['input-speech', 'slash-trigger', 'slash-suggestions', 'command-panel',
          'command-panel-title', 'command-panel-origin', 'command-panel-summary', 'command-fields',
          'command-error', 'command-panel-close', 'command-execute', 'input-area'];
        const elements = Object.fromEntries(ids.map((id) => [id, new Element('div', id)]));
        elements['input-speech'].tagName = 'INPUT';
        globalThis.document = {
          activeElement: null, documentElement: {lang: ''},
          getElementById: (id) => elements[id], createElement: (tag) => new Element(tag),
          querySelectorAll: () => [],
        };
        globalThis.window = {location: {protocol: 'http:'}};
        globalThis.CSS = {escape: (value) => value};
        let executed = false; let rendered = false;
        globalThis.fetch = async (url, options = {}) => ({
          ok: true,
          json: async () => options.method === 'POST'
            ? {result_kind: 'core/test-result', result: {ok: true}}
            : {schema_version: 2, commands: [{
                name: 'tool', title: {en: 'Tool', 'pt-BR': 'Ferramenta'},
                summary: {en: 'Run it', 'pt-BR': 'Execute'}, icon: '⚒',
                aliases: {en: [], 'pt-BR': []}, keywords: {en: [], 'pt-BR': []},
                inputs: [{name: 'value', type: 'text', required: true,
                  label: {en: 'Value', 'pt-BR': 'Valor'}, hint: {en: 'Required', 'pt-BR': 'Obrigatório'}}],
                result_kind: 'core/test-result', plugin_id: 'dev.tool', plugin_name: 'Tool Plugin',
                plugin_version: '1.0.0',
              }]},
        });
        const registry = await import('./src/static/slash-registry.js');
        registry.registerCoreAction({name: 'help', title: {en: 'Help', 'pt-BR': 'Ajuda'},
          summary: {en: 'Open help', 'pt-BR': 'Abrir ajuda'}, icon: '◇',
          aliases: {en: [], 'pt-BR': ['ajuda']}, keywords: {en: [], 'pt-BR': []}, scope: 'global'},
          () => { executed = true; });
        registry.registerCoreCommandResultRenderer('core/test-result', () => { rendered = true; });
        const {SlashCommands} = await import('./src/static/slash-commands.js');
        SlashCommands.init({getContext: () => ({sessionId: 's1', busy: false}), notify: () => {}});
        await new Promise((resolve) => setTimeout(resolve, 0));
        if (!elements['slash-trigger'].disabled || elements['slash-trigger'].getAttribute('aria-hidden') !== 'true')
          throw new Error('sigil is interactive before slash mode');
        elements['input-speech'].value = '/';
        elements['input-speech'].dispatchEvent({type: 'input'});
        if (elements['input-speech'].value !== '' || elements['slash-trigger'].disabled || elements['slash-suggestions'].hidden)
          throw new Error('first slash did not become the palette sigil');
        elements['input-speech'].value = '/';
        elements['input-speech'].dispatchEvent({type: 'input'});
        if (elements['input-speech'].value !== '/' || !elements['slash-trigger'].disabled || !elements['slash-suggestions'].hidden)
          throw new Error('second slash did not return to one literal slash');
        elements['input-speech'].value = '/ajuda';
        elements['input-speech'].dispatchEvent({type: 'input'});
        SlashCommands.handleKeydown({key: 'Tab', preventDefault() {}});
        if (elements['input-speech'].value !== 'help') throw new Error('Tab did not canonicalize alias');
        SlashCommands.handleKeydown({key: 'Enter', preventDefault() {}});
        await new Promise((resolve) => setTimeout(resolve, 0));
        if (!executed) throw new Error('Enter did not execute action');
        elements['input-speech'].value = '/tool';
        elements['input-speech'].dispatchEvent({type: 'input'});
        SlashCommands.handleKeydown({key: 'Enter', preventDefault() {}});
        const control = elements['command-fields'].querySelector('[data-command-field="value"]');
        if (!control || elements['command-panel'].hidden) throw new Error('tool form did not open');
        control.value = 'ready';
        elements['command-execute'].click();
        await new Promise((resolve) => setTimeout(resolve, 0));
        if (!rendered) throw new Error('result renderer was not dispatched');
    """
    subprocess.run(
        [node, "--no-warnings", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


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


def test_plugin_center_batches_active_changes_until_every_close_path() -> None:
    source = (STATIC / "plugin-center.js").read_text(encoding="utf-8")
    api_source = (STATIC / "api.js").read_text(encoding="utf-8")

    assert "let restartPending = false;" in source
    assert "restartPending = true;" in source
    assert "await api.restartPlugins();" in source
    assert "restartPlugins()" in api_source
    assert "apiFetch('/plugins/restart', { method: 'POST' })" in api_source
    assert source.count("window.location.reload()") == 1
    assert "else close();" in source
    assert "if (event.target === overlay) close();" in source
    assert "const result = await api.activatePlugin" in source
    assert "const result = await api.deactivatePlugin" in source
    assert "await settleOutcome(result);" in source


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


def test_setup_exposes_generic_presence_hooks_for_plugins() -> None:
    """setup.js calls plugin-agnostic hooks; no plugin-ID branch anywhere in core."""
    source = (STATIC / "setup.js").read_text(encoding="utf-8")

    assert "import { PluginRuntime } from './plugin-runtime.js';" in source
    assert "runHook('setup.charCardHead'" in source
    assert "'setup.presentCharacters'" in source
    assert "'setup.restorePresence'" in source
    # The mount hook runs before the card joins the DOM, so a plugin's toggle is
    # part of the same insertion (no flash of an unstyled/incomplete header).
    assert source.index("setup.charCardHead") < source.index("charsListEl.appendChild(card)")
    # Generic: gated on scene.present_characters, true even with no plugin active.
    assert "cfg.scene.present_characters.includes(cfg.controlled_character_id)" in source
    assert "dev." not in source and "alex-tavern" not in source


def test_session_view_exposes_a_generic_plugin_tools_slot() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'data-plugin-slot="session.tools"' in html
    # Sits with the always-present scene chrome, not inside a conditional template.
    assert html.index('id="scene-panel"') < html.index('data-plugin-slot="session.tools"')


def test_api_exposes_generic_presence_endpoints() -> None:
    source = (STATIC / "api.js").read_text(encoding="utf-8")
    assert "setPresence(sessionId, presentCharacters, expectedRevision)" in source
    assert "/session/${sessionId}/presence" in source
    assert "undoPresence(sessionId)" in source
    assert "/session/${sessionId}/presence/undo" in source


def test_char_card_presence_toggle_styling_is_generic_and_inert_when_unused() -> None:
    styles = (STATIC / "style.css").read_text(encoding="utf-8")
    assert ".char-presence-toggle" in styles
    assert ".presence-panel" in styles
    # Reuses the shared toggle component rather than inventing a new control.
    assert ".char-presence-toggle .toggle-label" in styles


def test_i18n_declares_presence_toggle_and_validation_strings() -> None:
    source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    for key in (
        "'character.inScene'",
        "'validation.controlledMustBePresent'",
        "'presence.panelTitle'",
        "'presence.undoButton'",
    ):
        assert source.count(key) == 2, f"{key} must be declared in both en and pt-BR catalogs"
