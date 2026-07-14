import { api } from './api.js';
import { bindTranslation, onLocaleChange, t, translateDocument } from './i18n.js';
import { PluginRuntime } from './plugin-runtime.js';

/* ══════════════════════════════════════════════════════════════════════
   setup.js — the setup/lobby overlay: characters, scene, narrator
   directives, controlled character. Persists to localStorage and builds
   the config object for POST /session/start.
   ══════════════════════════════════════════════════════════════════════ */

export const Setup = (() => {
    const LS_KEY = 'rpt_setup_v2'; // canonical nested mind/body setup

    // DOM refs
    const overlay      = document.getElementById('setup-overlay');
    const closeBtn     = document.getElementById('setup-close-btn');
    const scenarioSelect = document.getElementById('scenario-select');
    const scenarioLoadBtn= document.getElementById('scenario-load-btn');
    const scenarioDelBtn = document.getElementById('scenario-delete-btn');
    const scenarioNameEl = document.getElementById('scenario-name');
    const scenarioSaveBtn= document.getElementById('scenario-save-btn');
    const directivesEl = document.getElementById('setup-directives');
    const sceneLocEl   = document.getElementById('setup-scene-location');
    const sceneTimeEl  = document.getElementById('setup-scene-time');
    const factsListEl  = document.getElementById('scene-facts-list');
    const addFactBtn   = document.getElementById('add-fact-btn');
    const charsListEl  = document.getElementById('chars-list');
    const addCharBtn   = document.getElementById('add-char-btn');
    const controlledEl = document.getElementById('setup-controlled');
    const errorEl      = document.getElementById('setup-error');
    const startBtn     = document.getElementById('start-btn');
    const cardTpl      = document.getElementById('char-card-template');
    const presetSelect = document.getElementById('preset-select');
    const presetLoadBtn = document.getElementById('preset-load-btn');
    const presetDeleteBtn = document.getElementById('preset-delete-btn');
    const presetEmpty = document.getElementById('preset-empty');

    let onStartCb = null;
    let onOpenCb = null;
    let notifyCb = () => {};
    let returnFocusEl = null;

    /* ── Row builders ─────────────────────────────────────────────────── */
    function makeKvRow(listEl, key = '', val = '') {
        const row = document.createElement('div');
        row.className = 'kv-row';
        const k = document.createElement('input');
        k.className = 'text-input kv-key';
        bindTranslation(k, 'setup.keyPlaceholder', {}, 'placeholder');
        k.value = key;
        const v = document.createElement('input');
        v.className = 'text-input kv-val';
        bindTranslation(v, 'setup.valuePlaceholder', {}, 'placeholder');
        v.value = val;
        const rm = document.createElement('button');
        rm.className = 'kv-remove';
        rm.type = 'button';
        rm.textContent = '✕';
        bindTranslation(rm, 'common.remove', {}, 'ariaLabel');
        rm.addEventListener('click', () => row.remove());
        row.append(k, v, rm);
        listEl.appendChild(row);
        return row;
    }

    function makeKnowledgeRow(listEl, val = '') {
        const row = document.createElement('div');
        row.className = 'knowledge-row';
        const input = document.createElement('input');
        input.className = 'text-input knowledge-val';
        bindTranslation(input, 'character.knowledgePlaceholder', {}, 'placeholder');
        input.value = val;
        const rm = document.createElement('button');
        rm.className = 'kv-remove';
        rm.type = 'button';
        rm.textContent = '✕';
        bindTranslation(rm, 'common.remove', {}, 'ariaLabel');
        rm.addEventListener('click', () => row.remove());
        row.append(input, rm);
        listEl.appendChild(row);
        return row;
    }

    function characterFromCard(card) {
        const name = card.querySelector('.char-name').value.trim();
        return {
            mind: {
                name,
                personality: card.querySelector('.char-personality').value.trim(),
                knowledge: [...card.querySelectorAll('.knowledge-val')]
                    .map((input) => input.value.trim()).filter(Boolean),
                current_mood: card.querySelector('.char-mood').value.trim(),
            },
            body: {
                name,
                physical_description: card.querySelector('.char-physical').value.trim(),
                outfit: card.querySelector('.char-outfit').value.trim(),
            },
        };
    }

    function showCardAvatar(card, url = '') {
        const img = card.querySelector('.char-avatar-preview img');
        const fallback = card.querySelector('.char-avatar-preview span');
        img.src = url;
        img.hidden = !url;
        fallback.hidden = Boolean(url);
        if (!url) fallback.textContent = (card.querySelector('.char-name').value.trim()[0] || '?').toUpperCase();
    }

    async function processAvatar(file) {
        if (!file || file.size > 10 * 1024 * 1024) throw new Error(t('presets.avatarTooLarge'));
        const bitmap = await createImageBitmap(file);
        const side = Math.min(bitmap.width, bitmap.height);
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const context = canvas.getContext('2d');
        context.drawImage(
            bitmap,
            (bitmap.width - side) / 2,
            (bitmap.height - side) / 2,
            side,
            side,
            0,
            0,
            256,
            256,
        );
        bitmap.close();
        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', 0.82));
        if (!blob) throw new Error(t('presets.avatarProcessError'));
        const bytes = new Uint8Array(await blob.arrayBuffer());
        let binary = '';
        bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
        return { base64: btoa(binary), preview: URL.createObjectURL(blob) };
    }

    async function makeCharCard(data = {}, preset = {}) {
        const frag = cardTpl.content.cloneNode(true);
        translateDocument(frag);
        const card = frag.querySelector('.char-card');
        const mind = data.mind || {};
        const body = data.body || {};
        card.querySelector('.char-name').value = mind.name || body.name || '';
        card.querySelector('.char-personality').value = mind.personality || '';
        card.querySelector('.char-mood').value = mind.current_mood || '';
        card.querySelector('.char-outfit').value = body.outfit || '';
        card.querySelector('.char-physical').value = body.physical_description || '';
        card.dataset.presetName = preset.preset_name || '';
        card.dataset.presetRevision = preset.revision ? String(preset.revision) : '';
        card.dataset.avatarBase64 = '';
        card.querySelector('.char-preset-name').value = preset.preset_name || '';
        showCardAvatar(card, preset.avatar?.url || '');

        const kList = card.querySelector('.knowledge-list');
        (mind.knowledge && mind.knowledge.length ? mind.knowledge : ['']).forEach((k) =>
            makeKnowledgeRow(kList, k));

        card.querySelector('.char-add-knowledge')
            .addEventListener('click', () => makeKnowledgeRow(kList, ''));
        card.querySelector('.char-remove').addEventListener('click', () => {
            card.remove();
            reindexCards();
        });

        // keep controlled dropdown in sync as the name changes
        card.querySelector('.char-name').addEventListener('input', refreshControlled);
        card.querySelector('.char-avatar-file').addEventListener('change', async (event) => {
            try {
                const processed = await processAvatar(event.target.files?.[0]);
                card.dataset.avatarBase64 = processed.base64;
                showCardAvatar(card, processed.preview);
            } catch (error) {
                notify(error.message, 'error');
            }
        });
        card.querySelector('.char-save-preset').addEventListener('click', () => saveCardPreset(card));

        // Mount point in the card header (badge/name/remove already live there) for a
        // plugin-owned control, e.g. the "Na cena" presence toggle. A handler must
        // mutate and return the same card.
        await PluginRuntime.runHook('setup.charCardHead', card, {});

        charsListEl.appendChild(card);
        reindexCards();
        return card;
    }

    /* ── Ids / controlled dropdown ────────────────────────────────────── */
    function reindexCards() {
        const cards = [...charsListEl.querySelectorAll('.char-card')];
        cards.forEach((card, i) => {
            card.dataset.cid = `C${i + 1}`;
            card.querySelector('.char-id-badge').textContent = `C${i + 1}`;
        });
        refreshControlled();
    }

    function refreshControlled() {
        const prev = controlledEl.value;
        controlledEl.innerHTML = '';
        [...charsListEl.querySelectorAll('.char-card')].forEach((card) => {
            const cid = card.dataset.cid;
            const name = card.querySelector('.char-name').value.trim() || cid;
            const opt = document.createElement('option');
            opt.value = cid;
            opt.textContent = `${name} (${cid})`;
            controlledEl.appendChild(opt);
        });
        if ([...controlledEl.options].some((o) => o.value === prev)) {
            controlledEl.value = prev;
        }
    }

    /* ── Collect / populate ───────────────────────────────────────────── */
    async function collect() {
        const characters = {};
        const character_preset_ids = {};
        const cards = [...charsListEl.querySelectorAll('.char-card')];
        cards.forEach((card) => {
            const cid = card.dataset.cid;
            characters[cid] = characterFromCard(card);
            if (card.dataset.presetName) character_preset_ids[cid] = card.dataset.presetName;
        });

        const physical_facts = {};
        [...factsListEl.querySelectorAll('.kv-row')].forEach((row) => {
            const k = row.querySelector('.kv-key').value.trim();
            const v = row.querySelector('.kv-val').value.trim();
            if (k) physical_facts[k] = v;
        });

        // Default: everyone present. A plugin (e.g. dynamic character presence) can
        // return a different list by reading its own per-card toggle state off `cards`.
        const defaultPresent = [...Object.keys(characters), 'Player'];
        const present_characters = await PluginRuntime.runHook(
            'setup.presentCharacters', defaultPresent, { cards, characters },
        );

        return {
            controlled_character_id: controlledEl.value,
            narrator_directives: directivesEl.value.trim(),
            characters,
            character_preset_ids,
            scene: {
                location: sceneLocEl.value.trim(),
                time_of_day: sceneTimeEl.value.trim(),
                present_characters,
                physical_facts,
            },
        };
    }

    async function populate(cfg) {
        directivesEl.value = cfg.narrator_directives || '';
        sceneLocEl.value   = (cfg.scene && cfg.scene.location) || '';
        sceneTimeEl.value  = (cfg.scene && cfg.scene.time_of_day) || '';

        factsListEl.innerHTML = '';
        const facts = (cfg.scene && cfg.scene.physical_facts) || {};
        const factEntries = Object.entries(facts);
        if (factEntries.length) factEntries.forEach(([k, v]) => makeKvRow(factsListEl, k, v));
        else makeKvRow(factsListEl, '', '');

        charsListEl.innerHTML = '';
        const chars = cfg.characters || {};
        const ids = Object.keys(chars);
        const presetIds = cfg.character_preset_ids || {};
        if (ids.length) {
            for (const cid of ids) {
                const card = await makeCharCard(chars[cid], { preset_name: presetIds[cid] || '' });
                if (presetIds[cid]) hydrateCardPreset(card, presetIds[cid]);
            }
        } else await makeCharCard({});

        reindexCards();
        if (cfg.controlled_character_id &&
            [...controlledEl.options].some((o) => o.value === cfg.controlled_character_id)) {
            controlledEl.value = cfg.controlled_character_id;
        }

        // Lets a plugin restore its own per-card toggle state from the persisted list.
        const cards = [...charsListEl.querySelectorAll('.char-card')];
        const presentCharacters = (cfg.scene && cfg.scene.present_characters) || null;
        await PluginRuntime.runHook('setup.restorePresence', presentCharacters, { cards });
    }

    async function hydrateCardPreset(card, name) {
        try {
            const preset = await api.getPreset(name);
            card.dataset.presetName = name;
            card.dataset.presetRevision = String(preset.revision);
            card.querySelector('.char-preset-name').value = name;
            showCardAvatar(card, preset.avatar?.url || '');
        } catch { /* a missing preset is reported when starting the session */ }
    }

    async function refreshPresets(selected = '') {
        try {
            const data = await api.listPresets();
            presetSelect.innerHTML = '';
            data.presets.forEach((preset) => {
                const option = document.createElement('option');
                option.value = preset.preset_name;
                option.textContent = `${preset.display_name} · ${preset.preset_name}`;
                option.dataset.revision = String(preset.revision);
                presetSelect.appendChild(option);
            });
            if (selected && [...presetSelect.options].some((option) => option.value === selected)) {
                presetSelect.value = selected;
            }
            const empty = !data.presets.length;
            presetEmpty.hidden = !empty;
            presetSelect.disabled = empty;
            presetLoadBtn.disabled = empty;
            presetDeleteBtn.disabled = empty;
        } catch (error) {
            notify(t('presets.listError', { error: error.message }), 'error');
        }
    }

    async function loadSelectedPreset() {
        if (!presetSelect.value) return;
        try {
            const preset = await api.getPreset(presetSelect.value);
            const card = await makeCharCard(preset.character, preset);
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (error) {
            notify(t('presets.loadError', { error: error.message }), 'error');
        }
    }

    async function saveCardPreset(card) {
        const name = card.querySelector('.char-preset-name').value.trim();
        if (!/^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/.test(name)) {
            notify(t('presets.nameError'), 'error');
            return;
        }
        let revision = Number(card.dataset.presetRevision) || null;
        let replace = Boolean(revision && card.dataset.presetName === name);
        const payload = () => ({
            character: characterFromCard(card),
            avatar: card.dataset.avatarBase64
                ? { media_type: 'image/webp', data_base64: card.dataset.avatarBase64 }
                : null,
            expected_revision: replace ? revision : null,
            replace,
        });
        try {
            let saved;
            try {
                saved = await api.savePreset(name, payload());
            } catch (error) {
                if (error.status !== 409 || !confirm(t('presets.replaceConfirm', { name }))) throw error;
                const current = await api.getPreset(name);
                revision = current.revision;
                replace = true;
                saved = await api.savePreset(name, payload());
            }
            card.dataset.presetName = name;
            card.dataset.presetRevision = String(saved.revision);
            card.dataset.avatarBase64 = '';
            showCardAvatar(card, saved.avatar?.url || '');
            await refreshPresets(name);
            notify(t('presets.saved', { name }));
        } catch (error) {
            notify(t('presets.saveError', { error: error.message }), 'error');
        }
    }

    async function deleteSelectedPreset() {
        const option = presetSelect.selectedOptions[0];
        if (!option || !confirm(t('presets.deleteConfirm', { name: option.value }))) return;
        try {
            await api.deletePreset(option.value, Number(option.dataset.revision));
            await refreshPresets();
            notify(t('presets.deleted'));
        } catch (error) {
            notify(t('presets.deleteError', { error: error.message }), 'error');
        }
    }

    async function openPresetDraft(character, presetName, avatarFile = null) {
        open();
        const card = await makeCharCard(character, { preset_name: presetName });
        if (avatarFile) {
            try {
                const processed = await processAvatar(avatarFile);
                card.dataset.avatarBase64 = processed.base64;
                showCardAvatar(card, processed.preview);
            } catch (error) { notify(error.message, 'error'); }
        }
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.querySelector('.char-name').focus();
    }

    /* ── Built-in scenarios use the same canonical shape as user scenarios ─ */
    async function loadBuiltinScenario(name = '') {
        try {
            const data = await api.getBuiltinScenario(name);
            await populate(data.scenario);
        } catch (err) {
            showError('scenarios.defaultLoadError', { error: err.message });
        }
    }

    /* ── Validation ───────────────────────────────────────────────────── */
    function showError(key, params = {}) {
        bindTranslation(errorEl, key, params);
        errorEl.classList.add('active');
    }
    function clearError() {
        errorEl.classList.remove('active');
        errorEl.textContent = '';
        delete errorEl.dataset.i18n;
        delete errorEl.dataset.i18nParams;
    }

    function validate(cfg) {
        const ids = Object.keys(cfg.characters);
        if (ids.length === 0) return { key: 'validation.addCharacter' };
        for (const cid of ids) {
            const c = cfg.characters[cid];
            if (!c.mind.name) return { key: 'validation.characterName', params: { id: cid } };
            if (!c.mind.personality)
                return { key: 'validation.personality', params: { name: c.mind.name || cid } };
        }
        if (!cfg.scene.location) return { key: 'validation.location' };
        if (!cfg.controlled_character_id) return { key: 'validation.controlled' };
        // Generic, not plugin-specific: present_characters defaults to "everyone" when
        // no plugin overrides it, so this is always trivially satisfied in that case.
        if (!cfg.scene.present_characters.includes(cfg.controlled_character_id)) {
            return { key: 'validation.controlledMustBePresent' };
        }
        return null;
    }

    /* ── Persistence ──────────────────────────────────────────────────── */
    function save(cfg) {
        try { localStorage.setItem(LS_KEY, JSON.stringify(cfg)); } catch { /* ignore */ }
    }
    function loadSaved() {
        try {
            const raw = localStorage.getItem(LS_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    }

    /* ── Named scenarios ────────────────────────────────────────────────── */
    function notify(msg, type = 'success') {
        notifyCb(msg, type, 2500);
    }

    async function refreshScenarioSelect(selected) {
        let defaultScenarios = [];
        let userScenarios = [];
        try {
            const defData = await api.getBuiltinScenario();
            defaultScenarios = defData.scenarios;
            userScenarios = await api.listScenarios();
        } catch (err) {
            showError('scenarios.refreshError', { error: err.message });
        }

        scenarioSelect.innerHTML = '';

        defaultScenarios.forEach((name) => {
            const opt = document.createElement('option');
            opt.value = `builtin:${name}`;
            opt.textContent = `${name} (${t('scenarios.builtinSuffix')})`;
            scenarioSelect.appendChild(opt);
        });

        userScenarios.forEach((name) => {
            const opt = document.createElement('option');
            opt.value = `user:${name}`;
            opt.textContent = name;
            scenarioSelect.appendChild(opt);
        });

        if (selected && [...scenarioSelect.options].some((o) => o.value === selected)) {
            scenarioSelect.value = selected;
        } else if (defaultScenarios.length > 0) {
            scenarioSelect.value = `builtin:${defaultScenarios[0]}`;
        }
        scenarioDelBtn.disabled = !scenarioSelect.value.startsWith('user:');
    }

    async function loadSelectedScenario() {
        const val = scenarioSelect.value;
        if (val.startsWith('builtin:')) {
            const name = val.replace(/^builtin:/, '');
            await loadBuiltinScenario(name);
            notify(t('scenarios.defaultLoaded', { name }));
            return;
        }
        const name = val.replace(/^user:/, '');
        try {
            const cfg = await api.getScenario(name);
            await populate(cfg);
            clearError();
            notify(t('scenarios.loaded', { name }));
        } catch (err) {
            showError('scenarios.serverLoadError', { error: err.message });
        }
    }

    async function saveCurrentScenario() {
        const name = scenarioNameEl.value.trim();
        if (!name) { showError('scenarios.nameRequired'); return; }
        const cfg = await collect();
        const problem = validate(cfg);
        if (problem) { showError(problem.key, problem.params); return; }
        try {
            await api.saveScenario(name, cfg);
            scenarioNameEl.value = '';
            await refreshScenarioSelect(`user:${name}`);
            clearError();
            notify(t('scenarios.saved', { name }));
        } catch (err) {
            showError('scenarios.saveError', { error: err.message });
        }
    }

    async function deleteSelectedScenario() {
        const val = scenarioSelect.value;
        if (!val.startsWith('user:')) return;
        const name = val.replace(/^user:/, '');
        try {
            await api.deleteScenario(name);
            await refreshScenarioSelect();
            notify(t('scenarios.deleted', { name }));
        } catch (err) {
            showError('scenarios.deleteError', { error: err.message });
        }
    }

    /* ── Open / close ─────────────────────────────────────────────────── */
    function open() {
        clearError();
        returnFocusEl = document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
        overlay.classList.add('active');
        closeBtn.focus({ preventScroll: true });
        if (onOpenCb) onOpenCb();
        refreshPresets();
    }
    function close() {
        overlay.classList.remove('active');
        if (returnFocusEl?.isConnected) {
            returnFocusEl.focus({ preventScroll: true });
        }
        returnFocusEl = null;
    }

    /* ── Wiring ───────────────────────────────────────────────────────── */
    async function handleStart() {
        clearError();
        const cfg = await collect();
        const problem = validate(cfg);
        if (problem) { showError(problem.key, problem.params); return; }
        save(cfg);
        close();
        if (onStartCb) onStartCb(cfg);
    }

    function init(opts) {
        onStartCb = opts.onStart;
        onOpenCb = opts.onOpen;
        notifyCb = opts.notify || notifyCb;

        addFactBtn.addEventListener('click', () => makeKvRow(factsListEl, '', ''));
        addCharBtn.addEventListener('click', () => { makeCharCard({}); });
        startBtn.addEventListener('click', handleStart);
        closeBtn.addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        document.addEventListener('keydown', (event) => {
            if (event.key !== 'Escape' || !overlay.classList.contains('active')) return;
            event.preventDefault();
            close();
        });

        // Scenarios
        scenarioLoadBtn.addEventListener('click', loadSelectedScenario);
        scenarioSaveBtn.addEventListener('click', saveCurrentScenario);
        scenarioDelBtn.addEventListener('click', deleteSelectedScenario);
        scenarioSelect.addEventListener('change', () => {
            scenarioDelBtn.disabled = !scenarioSelect.value.startsWith('user:');
        });
        presetLoadBtn.addEventListener('click', loadSelectedPreset);
        presetDeleteBtn.addEventListener('click', deleteSelectedPreset);
        onLocaleChange(() => {
            [...scenarioSelect.options].forEach((option) => {
                if (!option.value.startsWith('builtin:')) return;
                const name = option.value.replace(/^builtin:/, '');
                option.textContent = `${name} (${t('scenarios.builtinSuffix')})`;
            });
        });
        refreshScenarioSelect();
        refreshPresets();

        // Pre-fill from last saved setup, else empty scaffolding
        const saved = loadSaved();
        if (saved) populate(saved);
        else populate({ characters: {}, scene: {} });
    }

    return { init, open, close, openPresetDraft };
})();
