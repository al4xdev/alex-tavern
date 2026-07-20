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
    const autoCompactEl = document.getElementById('runtime-auto-compact');
    const autoCompactThresholdEl = document.getElementById('runtime-auto-compact-threshold');
    const autoCompactStateEl = document.getElementById('auto-compact-state');
    const autoCompactThresholdValueEl = document.getElementById('auto-compact-threshold-value');
    const autoCompactThresholdExplanationEl = document.getElementById(
        'auto-compact-threshold-explanation'
    );
    const compactionThresholdEl = document.getElementById('compaction-threshold');
    const compactionHelpBtn = document.getElementById('compaction-help-btn');
    const burstMaxBeatsEl = document.getElementById('runtime-burst-max-beats');

    let selectedProvider = '';
    let compactionKeepRecentTurns = 8;
    let notify = () => {};
    let openCompactionHelp = () => {};
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

    function thresholdBand(value) {
        if (value <= 65) return 'earlier';
        if (value <= 85) return 'balanced';
        return 'later';
    }

    // Multi-beat continuation (Task 45): keep the field within the backend's
    // validated bound [1, 24] so a blank or out-of-range entry never fails the save.
    function readBurstBeats() {
        const beats = Number.parseInt(burstMaxBeatsEl.value, 10);
        if (!Number.isFinite(beats)) return 6;
        return Math.min(24, Math.max(1, beats));
    }

    function refreshCompactionControl() {
        const enabled = autoCompactEl.checked;
        const value = Number.parseInt(autoCompactThresholdEl.value, 10) || 80;
        const band = thresholdBand(value);
        autoCompactStateEl.textContent = t(
            enabled ? 'engine.autoCompactOn' : 'engine.autoCompactOff'
        );
        autoCompactThresholdValueEl.textContent = `${value}% · ${t(
            `engine.autoCompactBand.${band}`
        )}`;
        autoCompactThresholdExplanationEl.textContent = t(
            `engine.autoCompactExplanation.${band}`
        );
        autoCompactThresholdEl.disabled = !enabled;
        compactionThresholdEl.classList.toggle('disabled', !enabled);
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
        compactionKeepRecentTurns = config.compaction_keep_recent_turns;
        autoCompactEl.checked = config.automatic_compaction_enabled;
        autoCompactThresholdEl.value = config.automatic_compaction_threshold_percent;
        burstMaxBeatsEl.value = config.autonomous_burst_max_beats;
        refreshCompactionControl();
        providerAdapters.forEach((adapter) => adapter.populate(config.providers[adapter.id]));
        chooseProvider(config.active_provider);
        setError();
    }

    function collect() {
        return {
            active_provider: selectedProvider,
            language: getLlmLanguage(),
            compaction_keep_recent_turns: compactionKeepRecentTurns,
            automatic_compaction_enabled: autoCompactEl.checked,
            automatic_compaction_threshold_percent: Number.parseInt(
                autoCompactThresholdEl.value, 10
            ),
            autonomous_burst_max_beats: readBurstBeats(),
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
        openCompactionHelp = options.onCompactionHelp || openCompactionHelp;
        renderAdapters();
        saveBtn.addEventListener('click', save);
        autoCompactEl.addEventListener('change', refreshCompactionControl);
        autoCompactThresholdEl.addEventListener('input', refreshCompactionControl);
        compactionHelpBtn.addEventListener('click', openCompactionHelp);
        onLocaleChange(() => {
            if (selectedProvider) chooseProvider(selectedProvider);
            refreshCompactionControl();
            queueLanguageSync();
        });
        refresh();
    }

    return { init, refresh };
})();
