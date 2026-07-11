/* ══════════════════════════════════════════════════════════════════════
   setup.js — the setup/lobby overlay: characters, scene, narrator
   directives, controlled character. Persists to localStorage and builds
   the config object for POST /session/start.
   ══════════════════════════════════════════════════════════════════════ */

const Setup = (() => {
    const LS_KEY = 'rpt_setup_v1';       // autosave of last setup
    const PRESETS_KEY = 'rpt_presets_v1'; // named presets: { name: config }
    const BUILTIN = '__thorn_lyra__';

    // DOM refs
    const overlay      = document.getElementById('setup-overlay');
    const closeBtn     = document.getElementById('setup-close-btn');
    const presetSelect = document.getElementById('preset-select');
    const presetLoadBtn= document.getElementById('preset-load-btn');
    const presetDelBtn = document.getElementById('preset-delete-btn');
    const presetNameEl = document.getElementById('preset-name');
    const presetSaveBtn= document.getElementById('preset-save-btn');
    const playerNameEl = document.getElementById('setup-player-name');
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
    let hasSession = false; // whether the close (✕) button is allowed

    /* ── Row builders ─────────────────────────────────────────────────── */
    function makeKvRow(listEl, key = '', val = '', keyPh = 'chave', valPh = 'valor') {
        const row = document.createElement('div');
        row.className = 'kv-row';
        const k = document.createElement('input');
        k.className = 'text-input kv-key';
        k.placeholder = keyPh;
        k.value = key;
        const v = document.createElement('input');
        v.className = 'text-input kv-val';
        v.placeholder = valPh;
        v.value = val;
        const rm = document.createElement('button');
        rm.className = 'kv-remove';
        rm.type = 'button';
        rm.textContent = '✕';
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
        input.placeholder = 'Um fato que o personagem conhece';
        input.value = val;
        const rm = document.createElement('button');
        rm.className = 'kv-remove';
        rm.type = 'button';
        rm.textContent = '✕';
        rm.addEventListener('click', () => row.remove());
        row.append(input, rm);
        listEl.appendChild(row);
        return row;
    }

    function makeCharCard(data = {}) {
        const frag = cardTpl.content.cloneNode(true);
        const card = frag.querySelector('.char-card');
        card.querySelector('.char-name').value     = data.name || '';
        card.querySelector('.char-personality').value = data.personality || '';
        card.querySelector('.char-mood').value      = data.current_mood || '';
        card.querySelector('.char-outfit').value    = data.outfit || '';
        card.querySelector('.char-physical').value  = data.physical_description || '';

        const kList = card.querySelector('.knowledge-list');
        (data.knowledge && data.knowledge.length ? data.knowledge : ['']).forEach((k) =>
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
            characters[cid] = {
                name: card.querySelector('.char-name').value.trim(),
                personality: card.querySelector('.char-personality').value.trim(),
                knowledge,
                current_mood: card.querySelector('.char-mood').value.trim(),
                physical_description: card.querySelector('.char-physical').value.trim(),
                outfit: card.querySelector('.char-outfit').value.trim(),
            };
        });

        const physical_facts = {};
        [...factsListEl.querySelectorAll('.kv-row')].forEach((row) => {
            const k = row.querySelector('.kv-key').value.trim();
            const v = row.querySelector('.kv-val').value.trim();
            if (k) physical_facts[k] = v;
        });

        return {
            player_name: playerNameEl.value.trim() || 'Jogador',
            controlled_character_id: controlledEl.value,
            narrator_directives: directivesEl.value.trim(),
            characters,
            scene: {
                location: sceneLocEl.value.trim(),
                time_of_day: sceneTimeEl.value.trim(),
                physical_facts,
            },
        };
    }

    function populate(cfg) {
        playerNameEl.value = cfg.player_name || '';
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

    /* ── Preset (from /defaults, which returns full dataclass dicts) ───── */
    function flattenPresetCharacters(raw) {
        const out = {};
        Object.entries(raw || {}).forEach(([cid, ch]) => {
            out[cid] = {
                name: ch.mind.name,
                personality: ch.mind.personality,
                knowledge: ch.mind.knowledge || [],
                current_mood: ch.mind.current_mood,
                physical_description: ch.body.physical_description,
                outfit: ch.body.outfit,
            };
        });
        return out;
    }

    async function loadBuiltinPreset(name = '') {
        try {
            const data = await api.getDefaults(name);
            populate({
                player_name: playerNameEl.value.trim(),
                narrator_directives: directivesEl.value.trim(),
                controlled_character_id: 'C1',
                characters: flattenPresetCharacters(data.characters),
                scene: {
                    location: data.scene.location,
                    time_of_day: data.scene.time_of_day,
                    physical_facts: data.scene.physical_facts,
                },
            });
        } catch (err) {
            showError(`Não foi possível carregar o preset padrão: ${err.message}`);
        }
    }

    /* ── Validation ───────────────────────────────────────────────────── */
    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.classList.add('active');
    }
    function clearError() {
        errorEl.classList.remove('active');
    }

    function validate(cfg) {
        const ids = Object.keys(cfg.characters);
        if (ids.length === 0) return 'Adicione ao menos um personagem.';
        for (const cid of ids) {
            const c = cfg.characters[cid];
            if (!c.name) return `Personagem ${cid} precisa de um nome.`;
            if (!c.personality)
                return `Personagem ${c.name || cid} precisa de uma personalidade.`;
        }
        if (!cfg.scene.location) return 'A cena precisa de um local.';
        if (!cfg.controlled_character_id) return 'Escolha qual personagem você controla.';
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
        if (typeof toast === 'function') toast(msg, type, 2500);
    }

    async function refreshPresetSelect(selected) {
        let defaultPresets = [];
        let userPresets = [];
        try {
            const defData = await api.getDefaults();
            defaultPresets = defData.presets || ['thorn-lyra'];
            userPresets = await api.listPresets();
        } catch (err) {
            showError(`Erro ao atualizar presets: ${err.message}`);
            defaultPresets = ['thorn-lyra'];
        }

        presetSelect.innerHTML = '';

        defaultPresets.forEach((name) => {
            const opt = document.createElement('option');
            opt.value = `builtin:${name}`;
            opt.textContent = `${name} (padrão)`;
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
            notify(`Preset padrão "${name}" carregado`);
            return;
        }
        const name = val.replace(/^user:/, '');
        try {
            const cfg = await api.getPreset(name);
            populate(cfg);
            clearError();
            notify(`Preset "${name}" carregado`);
        } catch (err) {
            showError(`Erro ao carregar preset do servidor: ${err.message}`);
        }
    }

    async function saveCurrentPreset() {
        const name = presetNameEl.value.trim();
        if (!name) { showError('Dê um nome ao preset antes de salvar.'); return; }
        const cfg = collect();
        const problem = validate(cfg);
        if (problem) { showError(problem); return; }
        try {
            await api.savePreset(name, cfg);
            presetNameEl.value = '';
            await refreshPresetSelect(`user:${name}`);
            clearError();
            notify(`Preset "${name}" salvo`);
        } catch (err) {
            showError(`Erro ao salvar preset: ${err.message}`);
        }
    }

    async function deleteSelectedPreset() {
        const val = presetSelect.value;
        if (!val.startsWith('user:')) return;
        const name = val.replace(/^user:/, '');
        try {
            await api.deletePreset(name);
            await refreshPresetSelect();
            notify(`Preset "${name}" apagado`);
        } catch (err) {
            showError(`Erro ao apagar preset: ${err.message}`);
        }
    }

    /* ── Open / close ─────────────────────────────────────────────────── */
    function open() {
        clearError();
        closeBtn.style.display = hasSession ? '' : 'none';
        overlay.classList.add('active');
    }
    function close() {
        overlay.classList.remove('active');
    }

    /* ── Wiring ───────────────────────────────────────────────────────── */
    function handleStart() {
        clearError();
        const cfg = collect();
        const problem = validate(cfg);
        if (problem) { showError(problem); return; }
        save(cfg);
        hasSession = true;
        close();
        if (onStartCb) onStartCb(cfg);
    }

    function init(opts) {
        onStartCb = opts.onStart;

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
        refreshPresetSelect();

        // Pre-fill from last saved setup, else empty scaffolding
        const saved = loadSaved();
        if (saved) populate(saved);
        else populate({ characters: {}, scene: {} });
    }

    return { init, open, close };
})();
