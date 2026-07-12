/* Server-owned LLM settings, rendered and serialized by provider adapters. */

import { api } from './api.js';
import { providerAdapterMap, providerAdapters } from './adapters/index.js';

export const RuntimeConfig = (() => {
    const switchEl = document.getElementById('provider-switch');
    const panelsEl = document.getElementById('provider-panels');
    const statusEl = document.getElementById('engine-status');
    const errorEl = document.getElementById('runtime-config-error');
    const saveBtn = document.getElementById('runtime-config-save-btn');
    const languageEl = document.getElementById('runtime-language');
    const compactTurnsEl = document.getElementById('runtime-compact-turns');

    let selectedProvider = '';
    let notify = () => {};
    let rendered = false;

    function setError(message = '') {
        errorEl.textContent = message;
        errorEl.classList.toggle('active', Boolean(message));
    }

    function renderAdapters() {
        if (rendered) return;
        providerAdapters.forEach((adapter) => {
            adapter.renderCard(switchEl, chooseProvider);
            adapter.renderPanel(panelsEl);
        });
        rendered = true;
    }

    function chooseProvider(name) {
        const selected = providerAdapterMap.get(name);
        if (!selected) throw new Error(`Adapter de frontend ausente para ${name}`);
        selectedProvider = name;
        providerAdapters.forEach((adapter) => adapter.setActive(adapter.id === name));
        statusEl.textContent = selected.statusText;
        statusEl.className = `engine-status ${selected.statusClass}`.trim();
    }

    function populate(config) {
        const backendProviders = Object.keys(config.providers || {}).sort();
        const frontendProviders = [...providerAdapterMap.keys()].sort();
        if (JSON.stringify(backendProviders) !== JSON.stringify(frontendProviders)) {
            throw new Error(
                `Adapters divergentes: backend=${backendProviders.join(',')} frontend=${frontendProviders.join(',')}`,
            );
        }
        languageEl.value = config.language || '';
        compactTurnsEl.value = config.compaction_keep_recent_turns;
        providerAdapters.forEach((adapter) => adapter.populate(config.providers[adapter.id]));
        chooseProvider(config.active_provider);
        setError();
    }

    function collect() {
        return {
            active_provider: selectedProvider,
            language: languageEl.value.trim(),
            compaction_keep_recent_turns: Number.parseInt(compactTurnsEl.value, 10),
            providers: Object.fromEntries(
                providerAdapters.map((adapter) => [adapter.id, adapter.read()]),
            ),
        };
    }

    async function refresh() {
        saveBtn.disabled = true;
        statusEl.textContent = 'CARREGANDO';
        try {
            populate(await api.getConfig());
        } catch (error) {
            setError(`Não foi possível carregar o motor: ${error.message}`);
            statusEl.textContent = 'INDISPONÍVEL';
        } finally {
            saveBtn.disabled = false;
        }
    }

    async function save() {
        saveBtn.disabled = true;
        setError();
        try {
            populate(await api.saveConfig(collect()));
            notify('Motor de IA atualizado', 'success', 2500);
        } catch (error) {
            setError(`Não foi possível salvar: ${error.message}`);
        } finally {
            saveBtn.disabled = false;
        }
    }

    function init(options = {}) {
        notify = options.notify || notify;
        renderAdapters();
        saveBtn.addEventListener('click', save);
        refresh();
    }

    return { init, refresh };
})();
