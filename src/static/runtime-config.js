/* Server-owned LLM settings, rendered and serialized by provider adapters. */

import { api } from './api.js';
import { providerAdapterMap, providerAdapters } from './adapters/index.js';
import { bindTranslation, getLlmLanguage, onLocaleChange, t } from './i18n.js';

export const RuntimeConfig = (() => {
    const switchEl = document.getElementById('provider-switch');
    const panelsEl = document.getElementById('provider-panels');
    const statusEl = document.getElementById('engine-status');
    const errorEl = document.getElementById('runtime-config-error');
    const saveBtn = document.getElementById('runtime-config-save-btn');
    const compactTurnsEl = document.getElementById('runtime-compact-turns');

    let selectedProvider = '';
    let notify = () => {};
    let rendered = false;
    let configMutation = Promise.resolve();

    function enqueueConfigMutation(operation) {
        const pending = configMutation.then(operation);
        configMutation = pending.catch(() => {});
        return pending;
    }

    function setError(key = '', params = {}) {
        if (key) bindTranslation(errorEl, key, params);
        else {
            errorEl.textContent = '';
            delete errorEl.dataset.i18n;
            delete errorEl.dataset.i18nParams;
        }
        errorEl.classList.toggle('active', Boolean(key));
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
        if (!selected) throw new Error(t('engine.missingAdapter', { name }));
        selectedProvider = name;
        providerAdapters.forEach((adapter) => adapter.setActive(adapter.id === name));
        statusEl.textContent = selected.statusText();
        statusEl.className = `engine-status ${selected.statusClass}`.trim();
    }

    function populate(config) {
        const backendProviders = Object.keys(config.providers || {}).sort();
        const frontendProviders = [...providerAdapterMap.keys()].sort();
        if (JSON.stringify(backendProviders) !== JSON.stringify(frontendProviders)) {
            throw new Error(
                t('engine.adapterMismatch', {
                    backend: backendProviders.join(','),
                    frontend: frontendProviders.join(','),
                }),
            );
        }
        compactTurnsEl.value = config.compaction_keep_recent_turns;
        providerAdapters.forEach((adapter) => adapter.populate(config.providers[adapter.id]));
        chooseProvider(config.active_provider);
        setError();
    }

    function collect() {
        return {
            active_provider: selectedProvider,
            language: getLlmLanguage(),
            compaction_keep_recent_turns: Number.parseInt(compactTurnsEl.value, 10),
            providers: Object.fromEntries(
                providerAdapters.map((adapter) => [adapter.id, adapter.read()]),
            ),
        };
    }

    async function refresh() {
        saveBtn.disabled = true;
        bindTranslation(statusEl, 'common.loading');
        try {
            const config = await api.getConfig();
            populate(config);
            if (config.language !== getLlmLanguage()) queueLanguageSync();
        } catch (error) {
            setError('engine.loadError', { error: error.message });
            bindTranslation(statusEl, 'common.unavailable');
        } finally {
            saveBtn.disabled = false;
        }
    }

    function queueLanguageSync() {
        return enqueueConfigMutation(async () => {
            const config = await api.getConfig();
            const language = getLlmLanguage();
            if (config.language === language) return;
            await api.saveConfig({ ...config, language });
        }).catch((error) => {
            setError('engine.languageSyncError', { error: error.message });
        });
    }

    async function save() {
        saveBtn.disabled = true;
        setError();
        try {
            populate(await enqueueConfigMutation(() => api.saveConfig(collect())));
            notify(t('engine.updated'), 'success', 2500);
        } catch (error) {
            setError('engine.saveError', { error: error.message });
        } finally {
            saveBtn.disabled = false;
        }
    }

    function init(options = {}) {
        notify = options.notify || notify;
        renderAdapters();
        saveBtn.addEventListener('click', save);
        onLocaleChange(() => {
            if (selectedProvider) chooseProvider(selectedProvider);
            queueLanguageSync();
        });
        refresh();
    }

    return { init, refresh };
})();
