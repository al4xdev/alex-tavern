import { api } from './api.js';
import { bindTranslation, onLocaleChange, t, translateDocument } from './i18n.js';

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
    const presetSelect = document.getElementById('preset-select');
    const presetLoadBtn= document.getElementById('preset-load-btn');
    const presetDelBtn = document.getElementById('preset-delete-btn');
    const presetNameEl = document.getElementById('preset-name');
    const presetSaveBtn= document.getElementById('preset-save-btn');
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

    let onStartCb = null;
    let onOpenCb = null;
    let notifyCb = () => {};
    let hasSession = false; // whether the close (✕) button is allowed

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

    function makeCharCard(data = {}) {
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
    function collect() {
        const characters = {};
        [...charsListEl.querySelectorAll('.char-card')].forEach((card) => {
            const cid = card.dataset.cid;
            const knowledge = [...card.querySelectorAll('.knowledge-val')]
                .map((i) => i.value.trim())
                .filter(Boolean);
            const name = card.querySelector('.char-name').value.trim();
            characters[cid] = {
                mind: {
                    name,
                    personality: card.querySelector('.char-personality').value.trim(),
                    knowledge,
                    current_mood: card.querySelector('.char-mood').value.trim(),
                },
                body: {
                    name,
                    physical_description: card.querySelector('.char-physical').value.trim(),
                    outfit: card.querySelector('.char-outfit').value.trim(),
                },
            };
        });

        const physical_facts = {};
        [...factsListEl.querySelectorAll('.kv-row')].forEach((row) => {
            const k = row.querySelector('.kv-key').value.trim();
            const v = row.querySelector('.kv-val').value.trim();
            if (k) physical_facts[k] = v;
        });

        return {
            controlled_character_id: controlledEl.value,
            narrator_directives: directivesEl.value.trim(),
            characters,
            scene: {
                location: sceneLocEl.value.trim(),
                time_of_day: sceneTimeEl.value.trim(),
                present_characters: [...Object.keys(characters), 'Player'],
                physical_facts,
            },
        };
    }

    function populate(cfg) {
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
        if (ids.length) ids.forEach((cid) => makeCharCard(chars[cid]));
        else makeCharCard({});

        reindexCards();
        if (cfg.controlled_character_id &&
            [...controlledEl.options].some((o) => o.value === cfg.controlled_character_id)) {
            controlledEl.value = cfg.controlled_character_id;
        }
    }

    /* ── Built-in presets use the same canonical shape as user presets ─ */
    async function loadBuiltinPreset(name = '') {
        try {
            const data = await api.getDefaults(name);
            populate(data.preset);
        } catch (err) {
            showError('presets.defaultLoadError', { error: err.message });
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

    /* ── Named presets ────────────────────────────────────────────────── */
    function notify(msg, type = 'success') {
        notifyCb(msg, type, 2500);
    }

    async function refreshPresetSelect(selected) {
        let defaultPresets = [];
        let userPresets = [];
        try {
            const defData = await api.getDefaults();
            defaultPresets = defData.presets;
            userPresets = await api.listPresets();
        } catch (err) {
            showError('presets.refreshError', { error: err.message });
        }

        presetSelect.innerHTML = '';

        defaultPresets.forEach((name) => {
            const opt = document.createElement('option');
            opt.value = `builtin:${name}`;
            opt.textContent = `${name} (${t('presets.builtinSuffix')})`;
            presetSelect.appendChild(opt);
        });

        userPresets.forEach((name) => {
            const opt = document.createElement('option');
            opt.value = `user:${name}`;
            opt.textContent = name;
            presetSelect.appendChild(opt);
        });

        if (selected && [...presetSelect.options].some((o) => o.value === selected)) {
            presetSelect.value = selected;
        } else if (defaultPresets.length > 0) {
            presetSelect.value = `builtin:${defaultPresets[0]}`;
        }
        presetDelBtn.disabled = !presetSelect.value.startsWith('user:');
    }

    async function loadSelectedPreset() {
        const val = presetSelect.value;
        if (val.startsWith('builtin:')) {
            const name = val.replace(/^builtin:/, '');
            await loadBuiltinPreset(name);
            notify(t('presets.defaultLoaded', { name }));
            return;
        }
        const name = val.replace(/^user:/, '');
        try {
            const cfg = await api.getPreset(name);
            populate(cfg);
            clearError();
            notify(t('presets.loaded', { name }));
        } catch (err) {
            showError('presets.serverLoadError', { error: err.message });
        }
    }

    async function saveCurrentPreset() {
        const name = presetNameEl.value.trim();
        if (!name) { showError('presets.nameRequired'); return; }
        const cfg = collect();
        const problem = validate(cfg);
        if (problem) { showError(problem.key, problem.params); return; }
        try {
            await api.savePreset(name, cfg);
            presetNameEl.value = '';
            await refreshPresetSelect(`user:${name}`);
            clearError();
            notify(t('presets.saved', { name }));
        } catch (err) {
            showError('presets.saveError', { error: err.message });
        }
    }

    async function deleteSelectedPreset() {
        const val = presetSelect.value;
        if (!val.startsWith('user:')) return;
        const name = val.replace(/^user:/, '');
        try {
            await api.deletePreset(name);
            await refreshPresetSelect();
            notify(t('presets.deleted', { name }));
        } catch (err) {
            showError('presets.deleteError', { error: err.message });
        }
    }

    /* ── Open / close ─────────────────────────────────────────────────── */
    function open() {
        clearError();
        closeBtn.style.display = hasSession ? '' : 'none';
        overlay.classList.add('active');
        if (onOpenCb) onOpenCb();
    }
    function close() {
        overlay.classList.remove('active');
    }

    /* ── Wiring ───────────────────────────────────────────────────────── */
    function handleStart() {
        clearError();
        const cfg = collect();
        const problem = validate(cfg);
        if (problem) { showError(problem.key, problem.params); return; }
        save(cfg);
        hasSession = true;
        close();
        if (onStartCb) onStartCb(cfg);
    }

    function init(opts) {
        onStartCb = opts.onStart;
        onOpenCb = opts.onOpen;
        notifyCb = opts.notify || notifyCb;

        addFactBtn.addEventListener('click', () => makeKvRow(factsListEl, '', ''));
        addCharBtn.addEventListener('click', () => makeCharCard({}));
        startBtn.addEventListener('click', handleStart);
        closeBtn.addEventListener('click', () => { if (hasSession) close(); });
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay && hasSession) close();
        });

        // Presets
        presetLoadBtn.addEventListener('click', loadSelectedPreset);
        presetSaveBtn.addEventListener('click', saveCurrentPreset);
        presetDelBtn.addEventListener('click', deleteSelectedPreset);
        presetSelect.addEventListener('change', () => {
            presetDelBtn.disabled = !presetSelect.value.startsWith('user:');
        });
        onLocaleChange(() => {
            [...presetSelect.options].forEach((option) => {
                if (!option.value.startsWith('builtin:')) return;
                const name = option.value.replace(/^builtin:/, '');
                option.textContent = `${name} (${t('presets.builtinSuffix')})`;
            });
        });
        refreshPresetSelect();

        // Pre-fill from last saved setup, else empty scaffolding
        const saved = loadSaved();
        if (saved) populate(saved);
        else populate({ characters: {}, scene: {} });
    }

    return { init, open, close };
})();
