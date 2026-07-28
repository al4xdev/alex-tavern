import { el } from './dom.js';
import { api } from './api.js';
import { bindTranslation, getLocale, onLocaleChange, t, translateDocument } from './i18n.js';
import { PluginRuntime } from './plugin-runtime.js';

/* ══════════════════════════════════════════════════════════════════════
   setup.js — one coordinator for session snapshots, scenario records,
   character records, and engine settings.
   ══════════════════════════════════════════════════════════════════════ */

export const Setup = (() => {
    // DOM refs
    const overlay      = el('setup-overlay');
    const closeBtn     = el('setup-close-btn');
    const backBtn      = el('setup-back-btn');
    const modal        = el('setup-modal');
    const modalBody    = modal.querySelector('.modal-body');
    const titleEl      = el('setup-title');
    const subtitleEl   = el('setup-subtitle');
    const startFoot    = el('setup-start-foot');
    const scenarioSelect = el('scenario-select');
    const scenarioLoadBtn= el('scenario-load-btn');
    const scenarioNewBtn = el('scenario-new-btn');
    const scenarioDelBtn = el('scenario-delete-btn');
    const scenarioNameEl = el('scenario-name');
    const scenarioSaveBtn= el('scenario-save-btn');
    const directivesEl = el('setup-directives');
    const sceneLocEl   = el('setup-scene-location');
    const sceneTimeEl  = el('setup-scene-time');
    const factsListEl  = el('scene-facts-list');
    const addFactBtn   = el('add-fact-btn');
    const charsListEl  = el('chars-list');
    const addCharBtn   = el('add-char-btn');
    const controlledEl = el('setup-controlled');
    const errorEl      = el('setup-error');
    const startBtn     = el('start-btn');
    const cardTpl      = el('char-card-template');
    const presetSelect = el('preset-select');
    const presetDeleteBtn = el('preset-delete-btn');
    const presetEmpty = el('preset-empty');
    const presetNewBtn = el('preset-new-btn');
    const presetEditorList = el('preset-editor-list');
    const presetLibraryView = el('preset-library-view');
    const presetEditorView = el('preset-editor-view');
    const presetLibraryList = el('preset-library-list');
    const presetDraftResumeBtn = el('preset-draft-resume-btn');
    const presetEditorTitle = el('preset-editor-title');
    const characterPresetSelect = el('character-preset-select');
    const characterPresetAddBtn = el('character-preset-add-btn');
    const charactersIntro = el('characters-intro-copy');
    const activeSourceName = el('active-source-name');
    const activeScenarioName = el('active-scenario-name');
    const activeScenarioSaveBtn = el('active-scenario-save-btn');

    let onStartCb = null;
    let onSessionUpdatedCb = null;
    let getSessionIdCb = () => null;
    let onOpenCb = null;
    let onBackCb = null;
    let onCloseCb = null;
    let notifyCb = () => {};
    let returnFocusEl = null;
    let currentView = 'adventure';
    let editorMode = 'scenario';
    let activeRevision = 0;
    let backEntry = 'scenarios';
    let presetLibraryScrollTop = 0;

    function setDraftBusy(busy) {
        modalBody.inert = busy;
        modal.setAttribute('aria-busy', String(busy));
        scenarioSelect.disabled = busy;
        scenarioLoadBtn.disabled = busy;
        scenarioNewBtn.disabled = busy;
        scenarioSaveBtn.disabled = busy;
        if (busy) characterPresetAddBtn.disabled = true;
        else refreshCharacterPresetAvailability();
        startBtn.disabled = busy;
    }

    const VIEW_COPY = Object.freeze({
        adventure: ['apps.adventure', 'apps.adventureSubtitle'],
        characters: ['apps.characters', 'apps.charactersSubtitle'],
        presets: ['apps.characters', 'apps.charactersSubtitle'],
        settings: ['apps.settings', 'apps.settingsSubtitle'],
    });

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

    async function makeCharCard(data = {}, preset = {}, options = {}) {
        const mode = options.mode || 'roster';
        const target = options.target || charsListEl;
        const frag = cardTpl.content.cloneNode(true);
        translateDocument(frag);
        const card = frag.querySelector('.char-card');
        const mind = data.mind || {};
        const body = data.body || {};
        const nameInput = card.querySelector('.char-name');
        const summaryName = card.querySelector('.char-summary-name');
        const summaryAction = card.querySelector('.char-summary-action');
        const toggle = card.querySelector('.char-card-toggle');
        const initialName = mind.name || body.name || '';
        nameInput.value = initialName;
        summaryName.textContent = initialName || t('character.untitled');
        card.querySelector('.char-personality').value = mind.personality || '';
        card.querySelector('.char-mood').value = mind.current_mood || '';
        card.querySelector('.char-outfit').value = body.outfit || '';
        card.querySelector('.char-physical').value = body.physical_description || '';
        card.dataset.presetName = preset.preset_name || '';
        card.dataset.presetRevision = preset.revision ? String(preset.revision) : '';
        card.dataset.presetBuiltin = preset.builtin ? 'true' : 'false';
        card.dataset.avatarBase64 = '';
        card.dataset.mode = mode;
        card.querySelector('.char-preset-name').value = preset.preset_name || '';
        showCardAvatar(card, preset.avatar?.url || '');

        const setExpanded = (expanded) => {
            card.classList.toggle('collapsed', !expanded);
            toggle.setAttribute('aria-expanded', String(expanded));
            bindTranslation(summaryAction, expanded ? 'character.hideDetails' : 'character.editDetails');
        };
        setExpanded(options.expanded ?? (mode === 'preset' || !initialName));
        toggle.addEventListener('click', () => {
            setExpanded(toggle.getAttribute('aria-expanded') !== 'true');
        });

        const kList = card.querySelector('.knowledge-list');
        (mind.knowledge && mind.knowledge.length ? mind.knowledge : ['']).forEach((k) =>
            makeKnowledgeRow(kList, k));

        card.querySelector('.char-add-knowledge')
            .addEventListener('click', () => makeKnowledgeRow(kList, ''));
        card.querySelector('.char-remove').addEventListener('click', () => {
            card.remove();
            if (mode === 'roster') reindexCards();
        });

        // keep controlled dropdown in sync as the name changes
        if (mode === 'roster') {
            card.classList.add('roster-card');
            nameInput.addEventListener('input', refreshControlled);
        } else {
            card.classList.add('preset-card');
            card.querySelector('.char-id-badge').textContent = '◉';
            card.querySelector('.char-card-body').appendChild(card.querySelector('.char-preset-row'));
        }
        nameInput.addEventListener('input', () => {
            summaryName.textContent = nameInput.value.trim() || t('character.untitled');
            const fallback = card.querySelector('.char-avatar-preview span');
            if (!fallback.hidden) fallback.textContent = (nameInput.value.trim()[0] || '?').toUpperCase();
        });
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
        if (mode === 'roster') await PluginRuntime.runHook('setup.charCardHead', card, {});

        if (mode === 'roster') {
            charsListEl.appendChild(card);
            reindexCards();
        } else {
            target.appendChild(card);
        }
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
        refreshCharacterPresetAvailability();
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

    function linkedCharacterPresetNames() {
        return new Set(
            [...charsListEl.querySelectorAll('.char-card')]
                .map((card) => card.dataset.presetName)
                .filter(Boolean),
        );
    }

    function refreshCharacterPresetAvailability() {
        const linked = linkedCharacterPresetNames();
        [...characterPresetSelect.options].forEach((option) => {
            if (option.value) option.disabled = linked.has(option.value);
        });
        if (characterPresetSelect.selectedOptions[0]?.disabled) {
            characterPresetSelect.value = '';
        }
        const busy = modal.getAttribute('aria-busy') === 'true';
        characterPresetAddBtn.disabled = (
            busy || characterPresetSelect.disabled || !characterPresetSelect.value
        );
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
        const chars = { ...(cfg.characters || {}) };
        const presetIds = cfg.character_preset_ids || {};
        if (!Object.keys(chars).length && Object.keys(presetIds).length) {
            for (const [cid, presetName] of Object.entries(presetIds)) {
                const preset = await api.getPreset(presetName);
                chars[cid] = preset.character;
            }
        }
        const ids = Object.keys(chars);
        if (ids.length) {
            for (const cid of ids) {
                const card = await makeCharCard(chars[cid], { preset_name: presetIds[cid] || '' });
                if (presetIds[cid]) hydrateCardPreset(card, presetIds[cid]);
            }
        } else if (editorMode !== 'scenario') await makeCharCard({});

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
            const presets = data.presets.sort((left, right) =>
                Number(left.builtin) - Number(right.builtin)
                || left.display_name.localeCompare(right.display_name, getLocale()));
            presetSelect.innerHTML = '';
            characterPresetSelect.innerHTML = '';
            presetLibraryList.replaceChildren();

            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = presets.length
                ? t('presets.chooseSaved')
                : t('presets.noneSaved');
            characterPresetSelect.appendChild(placeholder);

            presets.forEach((preset) => {
                const option = document.createElement('option');
                option.value = preset.preset_name;
                option.textContent = `${preset.display_name} · ${preset.preset_name}`;
                option.dataset.revision = String(preset.revision);
                option.dataset.builtin = preset.builtin ? 'true' : 'false';
                presetSelect.appendChild(option);
                characterPresetSelect.appendChild(option.cloneNode(true));

                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'preset-library-item';
                item.dataset.presetName = preset.preset_name;
                const avatar = document.createElement('span');
                avatar.className = 'preset-library-avatar';
                avatar.textContent = (preset.display_name?.[0] || '?').toUpperCase();
                if (preset.avatar?.url) {
                    const image = document.createElement('img');
                    image.src = preset.avatar.url;
                    image.alt = '';
                    avatar.replaceChildren(image);
                }
                const copy = document.createElement('span');
                copy.className = 'preset-library-copy';
                const displayName = document.createElement('strong');
                displayName.textContent = preset.display_name;
                const slug = document.createElement('small');
                slug.textContent = preset.builtin
                    ? t('presets.builtinCharacter')
                    : preset.preset_name;
                copy.append(displayName, slug);
                const arrow = document.createElement('span');
                arrow.className = 'preset-library-arrow';
                arrow.setAttribute('aria-hidden', 'true');
                arrow.textContent = '→';
                item.append(avatar, copy, arrow);
                item.addEventListener('click', () => openPreset(preset.preset_name));
                presetLibraryList.appendChild(item);
            });
            if (selected && [...presetSelect.options].some((option) => option.value === selected)) {
                presetSelect.value = selected;
            }
            const empty = !presets.length;
            presetEmpty.hidden = !empty;
            characterPresetSelect.disabled = empty;
            refreshCharacterPresetAvailability();
        } catch (error) {
            notify(t('presets.listError', { error: error.message }), 'error');
        }
    }

    function showPresetLibrary() {
        const returningFromEditor = modal.dataset.presetMode === 'editor';
        modal.dataset.presetMode = 'library';
        presetLibraryView.hidden = false;
        presetEditorView.hidden = true;
        presetDraftResumeBtn.hidden = !presetEditorList.querySelector('.preset-card');
        if (returningFromEditor) {
            requestAnimationFrame(() => { modalBody.scrollTop = presetLibraryScrollTop; });
        }
    }

    function showPresetEditor({ existing = false } = {}) {
        if (modal.dataset.presetMode !== 'editor') {
            presetLibraryScrollTop = modalBody.scrollTop;
        }
        modal.dataset.presetMode = 'editor';
        presetLibraryView.hidden = true;
        presetEditorView.hidden = false;
        presetDeleteBtn.hidden = !existing;
        bindTranslation(presetEditorTitle, existing ? 'presets.editTitle' : 'presets.newTitle');
        modalBody.scrollTop = 0;
    }

    async function openPreset(name) {
        if (!name) return;
        const current = presetEditorList.querySelector('.preset-card');
        if (current?.dataset.presetName === name) {
            presetSelect.value = name;
            showPresetEditor({ existing: Boolean(current.dataset.presetRevision) });
            current.querySelector('.char-name').focus({ preventScroll: true });
            return;
        }
        try {
            const preset = await api.getPreset(name);
            presetSelect.value = name;
            presetEditorList.replaceChildren();
            const card = await makeCharCard(preset.character, preset, {
                mode: 'preset',
                target: presetEditorList,
            });
            showPresetEditor({ existing: !preset.builtin });
            card.querySelector('.char-name').focus({ preventScroll: true });
        } catch (error) {
            notify(t('presets.loadError', { error: error.message }), 'error');
        }
    }

    async function addSelectedPresetToRoster() {
        const presetName = characterPresetSelect.value;
        if (!presetName) return;
        if (linkedCharacterPresetNames().has(presetName)) {
            notify(t('presets.alreadyLinked'), 'error');
            refreshCharacterPresetAvailability();
            return;
        }
        setDraftBusy(true);
        try {
            const preset = await api.getPreset(presetName);
            const card = await makeCharCard(preset.character, preset);
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (error) {
            notify(t('presets.loadError', { error: error.message }), 'error');
        } finally {
            setDraftBusy(false);
        }
    }

    async function newPreset() {
        presetEditorList.replaceChildren();
        presetSelect.value = '';
        const card = await makeCharCard({}, {}, { mode: 'preset', target: presetEditorList });
        showPresetEditor();
        card.querySelector('.char-name').focus({ preventScroll: true });
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
            presetDeleteBtn.hidden = false;
            bindTranslation(presetEditorTitle, 'presets.editTitle');
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
            presetEditorList.replaceChildren();
            await refreshPresets();
            showPresetLibrary();
            notify(t('presets.deleted'));
        } catch (error) {
            notify(t('presets.deleteError', { error: error.message }), 'error');
        }
    }

    async function openPresetDraft(character, presetName, avatarFile = null) {
        openCharacters();
        presetEditorList.replaceChildren();
        presetSelect.value = '';
        const card = await makeCharCard(character, { preset_name: presetName }, {
            mode: 'preset',
            target: presetEditorList,
        });
        showPresetEditor();
        if (avatarFile) {
            try {
                const processed = await processAvatar(avatarFile);
                card.dataset.avatarBase64 = processed.base64;
                showCardAvatar(card, processed.preview);
            } catch (error) { notify(error.message, 'error'); }
        }
        card.querySelector('.char-name').focus({ preventScroll: true });
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
        if (ids.length === 0) return { key: 'validation.addCharacter', view: 'characters' };
        for (const cid of ids) {
            const c = cfg.characters[cid];
            if (!c.mind.name) {
                return {
                    key: 'validation.characterName',
                    params: { id: cid },
                    view: 'characters',
                    selector: `[data-cid="${cid}"] .char-name`,
                };
            }
            if (!c.mind.personality)
                return {
                    key: 'validation.personality',
                    params: { name: c.mind.name || cid },
                    view: 'characters',
                    selector: `[data-cid="${cid}"] .char-personality`,
                };
        }
        if (!cfg.scene.location) return { key: 'validation.location' };
        if (!cfg.controlled_character_id) {
            return {
                key: 'validation.controlled',
                view: 'characters',
                selector: '#setup-controlled',
            };
        }
        // Generic, not plugin-specific: present_characters defaults to "everyone" when
        // no plugin overrides it, so this is always trivially satisfied in that case.
        if (!cfg.scene.present_characters.includes(cfg.controlled_character_id)) {
            return {
                key: 'validation.controlledMustBePresent',
                view: 'characters',
                selector: '#setup-controlled',
            };
        }
        return null;
    }

    function revealProblem(problem) {
        if (problem.view !== 'characters') {
            showError(problem.key, problem.params);
            return;
        }
        notify(t(problem.key, problem.params), 'error');
        openCharacters();
        requestAnimationFrame(() => {
            const target = problem.selector ? modal.querySelector(problem.selector) : addCharBtn;
            target?.setAttribute('aria-invalid', 'true');
            target?.focus({ preventScroll: true });
        });
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

    async function loadSelectedScenario(announce = true) {
        setDraftBusy(true);
        const val = scenarioSelect.value;
        try {
            if (val.startsWith('builtin:')) {
                const name = val.replace(/^builtin:/, '');
                await loadBuiltinScenario(name);
                if (announce) notify(t('scenarios.defaultLoaded', { name }));
                return;
            }
            const name = val.replace(/^user:/, '');
            const cfg = await api.getScenario(name);
            await populate(cfg);
            clearError();
            if (announce) notify(t('scenarios.loaded', { name }));
        } catch (err) {
            showError('scenarios.serverLoadError', { error: err.message });
        } finally {
            setDraftBusy(false);
        }
    }

    async function newBlankScenario() {
        scenarioSelect.value = '';
        scenarioDelBtn.disabled = true;
        scenarioNameEl.value = '';
        await populate({
            controlled_character_id: '',
            narrator_directives: '',
            characters: {},
            character_preset_ids: {},
            scene: {
                location: '',
                time_of_day: '',
                present_characters: [],
                physical_facts: {},
            },
        });
        clearError();
        sceneLocEl.focus({ preventScroll: true });
    }

    async function saveCurrentScenario() {
        await saveScenarioSnapshot(scenarioNameEl.value.trim(), {
            afterSave: async (name) => {
                scenarioNameEl.value = '';
                await refreshScenarioSelect(`user:${name}`);
            },
        });
    }

    async function saveActiveScenario() {
        await saveScenarioSnapshot(activeScenarioName.value.trim(), {
            afterSave: async (name) => {
                activeScenarioName.value = '';
                activeSourceName.textContent = name;
            },
        });
    }

    async function saveScenarioSnapshot(name, { afterSave } = {}) {
        if (!name) { showError('scenarios.nameRequired'); return; }
        const cfg = await collect();
        const problem = validate(cfg);
        if (problem) {
            revealProblem(problem);
            return;
        }
        if (Object.keys(cfg.character_preset_ids).length !== Object.keys(cfg.characters).length) {
            showError('scenarios.linkedCharactersRequired');
            return;
        }
        const linkedPresetNames = Object.values(cfg.character_preset_ids);
        if (new Set(linkedPresetNames).size !== linkedPresetNames.length) {
            showError('scenarios.duplicateCharacterLinks');
            return;
        }
        const scenario = {
            controlled_character_id: cfg.controlled_character_id,
            narrator_directives: cfg.narrator_directives,
            character_preset_ids: cfg.character_preset_ids,
            scene: cfg.scene,
        };
        try {
            setDraftBusy(true);
            await api.saveScenario(name, scenario);
            await afterSave?.(name);
            clearError();
            notify(t('scenarios.saved', { name }));
        } catch (err) {
            showError('scenarios.saveError', { error: err.message });
        } finally {
            setDraftBusy(false);
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
    function openView(view) {
        clearError();
        currentView = view;
        const [titleKey, subtitleKey] = VIEW_COPY[view];
        modal.dataset.view = view;
        bindTranslation(titleEl, titleKey);
        bindTranslation(subtitleEl, subtitleKey);
        startFoot.hidden = true;
        returnFocusEl = document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
        overlay.classList.add('active');
        backBtn.focus({ preventScroll: true });
        if (view === 'settings' && onOpenCb) onOpenCb();
        if (view === 'presets') showPresetLibrary();
        if (view === 'characters' || view === 'presets') refreshPresets();
    }
    async function openAdventure() {
        const sessionId = getSessionIdCb();
        if (!sessionId) {
            onBackCb?.('sessions');
            return;
        }
        editorMode = 'active';
        backEntry = 'adventure';
        modal.dataset.editorMode = editorMode;
        openView('adventure');
        startFoot.hidden = false;
        bindTranslation(titleEl, 'apps.adventure');
        bindTranslation(subtitleEl, 'adventure.currentSubtitle');
        bindTranslation(charactersIntro, 'characters.activeSession');
        bindTranslation(startBtn.querySelector('span'), 'adventure.saveSession');
        setDraftBusy(true);
        try {
            const state = await api.getState(sessionId);
            activeRevision = state.revision;
            activeSourceName.textContent = state.scenario_source_id || t('adventure.customSource');
            activeScenarioName.value = '';
            await populate(state);
        } finally {
            setDraftBusy(false);
        }
    }
    function openCharacters() {
        editorMode = 'characters';
        backEntry = 'characters';
        modal.dataset.editorMode = editorMode;
        openView('presets');
    }
    async function openScenarios() {
        editorMode = 'scenario';
        backEntry = 'scenarios';
        modal.dataset.editorMode = editorMode;
        openView('adventure');
        bindTranslation(titleEl, 'apps.scenarios');
        bindTranslation(subtitleEl, 'apps.scenariosSubtitle');
        bindTranslation(charactersIntro, 'characters.scenarioCast');
        setDraftBusy(true);
        try {
            await refreshScenarioSelect();
            await loadSelectedScenario(false);
        } finally {
            setDraftBusy(false);
        }
    }
    async function openNewSession() {
        editorMode = 'new';
        backEntry = 'sessions';
        modal.dataset.editorMode = editorMode;
        openView('adventure');
        bindTranslation(titleEl, 'sessions.new');
        bindTranslation(subtitleEl, 'sessions.newSubtitle');
        bindTranslation(charactersIntro, 'characters.newSessionCast');
        bindTranslation(startBtn.querySelector('span'), 'setup.start');
        startFoot.hidden = false;
        setDraftBusy(true);
        try {
            await refreshScenarioSelect();
            await loadSelectedScenario(false);
        } finally {
            setDraftBusy(false);
        }
    }
    function openSettings() {
        editorMode = 'settings';
        backEntry = 'settings';
        modal.dataset.editorMode = editorMode;
        openView('settings');
    }

    function close() {
        overlay.classList.remove('active');
        if (onCloseCb) {
            onCloseCb();
        } else if (returnFocusEl?.isConnected) {
            returnFocusEl.focus({ preventScroll: true });
        }
        returnFocusEl = null;
    }

    function back() {
        if (currentView === 'presets' && modal.dataset.presetMode === 'editor') {
            showPresetLibrary();
            presetDraftResumeBtn.focus({ preventScroll: true });
            return;
        }
        overlay.classList.remove('active');
        if (onBackCb) onBackCb(backEntry);
    }

    /* ── Wiring ───────────────────────────────────────────────────────── */
    async function handlePrimary() {
        clearError();
        const cfg = await collect();
        const problem = validate(cfg);
        if (problem) { revealProblem(problem); return; }
        if (editorMode === 'active') {
            try {
                setDraftBusy(true);
                const sessionId = getSessionIdCb();
                const result = await api.updateSessionSetup(sessionId, {
                    ...cfg,
                    expected_revision: activeRevision,
                });
                activeRevision = result.state.revision;
                onSessionUpdatedCb?.(result.state);
                notify(t('adventure.sessionSaved'));
            } catch (error) {
                notify(t('adventure.sessionSaveError', { error: error.message }), 'error');
            } finally {
                setDraftBusy(false);
            }
            return;
        }
        if (editorMode === 'new') {
            const scenarioName = scenarioSelect.value.replace(/^(builtin|user):/, '');
            close();
            if (onStartCb) onStartCb({ ...cfg, scenario_name: scenarioName });
        }
    }

    function init(opts) {
        onStartCb = opts.onStart;
        onSessionUpdatedCb = opts.onSessionUpdated;
        getSessionIdCb = opts.getSessionId;
        onOpenCb = opts.onOpen;
        onBackCb = opts.onBack;
        onCloseCb = opts.onClose;
        notifyCb = opts.notify || notifyCb;

        addFactBtn.addEventListener('click', () => makeKvRow(factsListEl, '', ''));
        addCharBtn.addEventListener('click', () => { makeCharCard({}); });
        startBtn.addEventListener('click', handlePrimary);
        closeBtn.addEventListener('click', close);
        backBtn.addEventListener('click', back);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        document.addEventListener('keydown', (event) => {
            if (event.key !== 'Escape' || !overlay.classList.contains('active')) return;
            event.preventDefault();
            back();
        });

        // Scenarios
        scenarioLoadBtn.addEventListener('click', loadSelectedScenario);
        scenarioNewBtn.addEventListener('click', newBlankScenario);
        scenarioSaveBtn.addEventListener('click', saveCurrentScenario);
        activeScenarioSaveBtn.addEventListener('click', saveActiveScenario);
        scenarioDelBtn.addEventListener('click', deleteSelectedScenario);
        scenarioSelect.addEventListener('change', () => {
            scenarioDelBtn.disabled = !scenarioSelect.value.startsWith('user:');
        });
        characterPresetSelect.addEventListener('change', refreshCharacterPresetAvailability);
        presetDeleteBtn.addEventListener('click', deleteSelectedPreset);
        presetNewBtn.addEventListener('click', newPreset);
        presetDraftResumeBtn.addEventListener('click', () => {
            const card = presetEditorList.querySelector('.preset-card');
            if (!card) return;
            showPresetEditor({ existing: Boolean(card.dataset.presetRevision) });
            card.querySelector('.char-name').focus({ preventScroll: true });
        });
        characterPresetAddBtn.addEventListener('click', addSelectedPresetToRoster);
        onLocaleChange(() => {
            [...scenarioSelect.options].forEach((option) => {
                if (!option.value.startsWith('builtin:')) return;
                const name = option.value.replace(/^builtin:/, '');
                option.textContent = `${name} (${t('scenarios.builtinSuffix')})`;
            });
            if (currentView === 'presets') refreshPresets();
        });
        refreshPresets();
    }

    return {
        init,
        close,
        openAdventure,
        openCharacters,
        openScenarios,
        openNewSession,
        openSettings,
        openPresetDraft,
    };
})();
