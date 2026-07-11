/* ══════════════════════════════════════════════════════════════════════
   app.js — game view: dynamic rendering, turns, debug drawer, toasts.
   ══════════════════════════════════════════════════════════════════════ */

/* ── State ────────────────────────────────────────────────────────────── */
const state = {
    sessionId: null,
    pendingOptions: null,
    characters: {},     // cid -> {mind, body} (from GET state)
    controlledId: null,
    order: [],          // stable ordering of cids for color assignment
    debug: false,
};

const CHAR_COLORS = ['#6c9cff', '#b07cff', '#40e0a0', '#ffb454', '#ff7ca8', '#4fd6e0'];

/* ── DOM refs ─────────────────────────────────────────────────────────── */
const chatLog       = document.getElementById('chat-log');
const sceneLocation = document.getElementById('scene-location');
const sceneTags     = document.getElementById('scene-tags');
const optionsPanel  = document.getElementById('options-panel');
const inputSpeech   = document.getElementById('input-speech');
const inputAction   = document.getElementById('input-action');
const sendBtn       = document.getElementById('send-btn');
const newSessionBtn = document.getElementById('new-session-btn');
const settingsBtn   = document.getElementById('settings-btn');
const emptyConfigBtn= document.getElementById('empty-config-btn');
const spinner       = document.getElementById('spinner');
const emptyState    = document.getElementById('empty-state');
const debugToggle   = document.getElementById('debug-toggle');
const debugDrawer   = document.getElementById('debug-drawer');
const debugContent  = document.getElementById('debug-content');
const previewBtn    = document.getElementById('preview-prompt-btn');
const toastWrap     = document.getElementById('toast-wrap');
const installBtn    = document.getElementById('install-btn');
const debugCloseBtn = document.getElementById('debug-close-btn');

/* ── Toast ────────────────────────────────────────────────────────────── */
function toast(message, type = 'info', ms = 4000) {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    toastWrap.appendChild(el);
    setTimeout(() => {
        el.classList.add('leaving');
        el.addEventListener('animationend', () => el.remove());
    }, ms);
}

/* ── Helpers ──────────────────────────────────────────────────────────── */
function setLoading(on) {
    const disable = on || !state.sessionId;
    inputSpeech.disabled = disable;
    inputAction.disabled = disable;
    sendBtn.disabled = disable;
    spinner.classList.toggle('active', on);
}

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

function controlledName() {
    const c = state.characters[state.controlledId];
    return (c && c.mind && c.mind.name) || 'Você';
}

function colorFor(cid) {
    const idx = state.order.indexOf(cid);
    return CHAR_COLORS[(idx < 0 ? 0 : idx) % CHAR_COLORS.length];
}

/* Resolve display info for any speaker id — fully dynamic, no hardcoding. */
function speakerInfo(speaker) {
    if (speaker === 'Narrator') {
        return { label: 'Narrador', color: null, initial: '🎭', cls: 'msg-narrator' };
    }
    if (speaker === 'Player') {
        const cid = state.controlledId;
        return {
            label: controlledName(),
            color: colorFor(cid),
            initial: controlledName().charAt(0).toUpperCase(),
            cls: 'msg-player',
        };
    }
    const ch = state.characters[speaker];
    if (ch) {
        return {
            label: ch.mind.name,
            color: colorFor(speaker),
            initial: ch.mind.name.charAt(0).toUpperCase(),
            cls: 'msg-npc',
        };
    }
    return { label: speaker, color: null, initial: '💬', cls: 'msg-npc' };
}

/* ── Render scene ─────────────────────────────────────────────────────── */
function renderScene(scene, changedKeys = []) {
    if (!scene) return;
    sceneLocation.textContent = scene.time_of_day
        ? `${scene.location} — ${scene.time_of_day}`
        : scene.location;

    sceneTags.innerHTML = '';
    for (const [key, val] of Object.entries(scene.physical_facts || {})) {
        const tag = document.createElement('span');
        tag.className = 'scene-tag';
        if (changedKeys.includes(key)) tag.classList.add('flash');
        tag.textContent = `${key}: ${val}`;
        sceneTags.appendChild(tag);
    }
}

/* ── Render message ───────────────────────────────────────────────────── */
function addMessage(speaker, content, contentType) {
    const info = speakerInfo(speaker);

    const msg = document.createElement('div');
    msg.className = `msg ${info.cls}`;

    const header = document.createElement('div');
    header.className = 'msg-header';
    if (info.color) header.style.color = info.color;

    if (info.cls !== 'msg-narrator') {
        const avatar = document.createElement('span');
        avatar.className = 'msg-avatar';
        avatar.textContent = info.initial;
        avatar.style.background = info.color
            ? `${info.color}33` : 'var(--surface-hi)';
        if (info.color) avatar.style.color = info.color;
        header.appendChild(avatar);
    }
    header.appendChild(document.createTextNode(info.label));
    msg.appendChild(header);

    const body = document.createElement('div');
    body.className = 'msg-content';
    // Render **text** as italic thought
    const parts = content.split(/(\*\*[^*]+\*\*)/g);
    for (const part of parts) {
        if (part.startsWith('**') && part.endsWith('**')) {
            const span = document.createElement('span');
            span.className = 'thought';
            span.textContent = part.slice(2, -2);
            body.appendChild(span);
        } else {
            body.appendChild(document.createTextNode(part));
        }
    }
    msg.appendChild(body);
    chatLog.appendChild(msg);
    emptyState.style.display = 'none';
    scrollToBottom();
}

/* ── Player options ───────────────────────────────────────────────────── */
function renderOptions(options) {
    optionsPanel.innerHTML = '';
    if (!options || options.length === 0) {
        optionsPanel.classList.remove('active');
        state.pendingOptions = null;
        return;
    }
    optionsPanel.classList.add('active');
    state.pendingOptions = options;

    options.forEach((opt, i) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.style.animationDelay = `${i * 0.06}s`;

        const label = document.createElement('span');
        label.className = 'opt-label';
        label.textContent = `${opt.index + 1}. ${opt.label}`;
        btn.appendChild(label);

        if (opt.description) {
            const desc = document.createElement('span');
            desc.className = 'opt-desc';
            desc.textContent = opt.description;
            btn.appendChild(desc);
        }
        btn.addEventListener('click', () => {
            inputAction.value = opt.label;
            sendTurn(opt.index);
        });
        optionsPanel.appendChild(btn);
    });
}

/* ── Debug drawer ─────────────────────────────────────────────────────── */
function messagesToText(messages) {
    return (messages || [])
        .map((m) => `[${m.role.toUpperCase()}]\n${m.content}`)
        .join('\n\n');
}

function makeCopyBtn(getText) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copiar';
    btn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(getText());
            btn.textContent = '✓ Copiado';
            btn.classList.add('copied');
            setTimeout(() => { btn.textContent = 'Copiar'; btn.classList.remove('copied'); }, 1500);
        } catch {
            toast('Não foi possível copiar', 'error');
        }
    });
    return btn;
}

function renderDebugBlock(title, messages, raw) {
    const block = document.createElement('div');
    block.className = 'debug-block';

    const head = document.createElement('div');
    head.className = 'debug-block-head';
    head.appendChild(document.createTextNode(title));
    const allText = () =>
        `${messagesToText(messages)}${raw != null ? `\n\n[RAW RESPONSE]\n${raw}` : ''}`;
    head.appendChild(makeCopyBtn(allText));
    block.appendChild(head);

    const pre = document.createElement('div');
    pre.className = 'debug-pre';
    (messages || []).forEach((m) => {
        const role = document.createElement('div');
        role.className = 'debug-role';
        role.textContent = m.role;
        pre.appendChild(role);
        pre.appendChild(document.createTextNode(m.content));
    });
    if (raw != null) {
        const role = document.createElement('div');
        role.className = 'debug-role';
        role.textContent = 'raw response';
        pre.appendChild(role);
        pre.appendChild(document.createTextNode(raw));
    }
    block.appendChild(pre);
    return block;
}

function renderDebug(debug) {
    debugContent.innerHTML = '';
    if (!debug) {
        debugContent.innerHTML =
            '<p class="debug-placeholder">Sem dados de debug neste turno.</p>';
        return;
    }
    if (debug.narrator) {
        debugContent.appendChild(
            renderDebugBlock('Narrador', debug.narrator.messages, debug.narrator.raw));
    }
    if (debug.character) {
        debugContent.appendChild(
            renderDebugBlock('Personagem', debug.character.messages, debug.character.raw));
    }
}

async function previewPrompt() {
    if (!state.sessionId) { toast('Inicie uma sessão primeiro', 'error'); return; }
    try {
        const speech = inputSpeech.value.trim();
        const action = inputAction.value.trim();
        const data = await api.previewPrompt(state.sessionId, { speech, action });
        debugContent.innerHTML = '';
        debugContent.appendChild(
            renderDebugBlock('Preview — Narrador', data.narrator_messages, null));
        toast('Prompt do Narrador montado (sem chamar o LLM)', 'success', 2500);
    } catch (err) {
        toast(`Erro no preview: ${err.message}`, 'error');
    }
}

/* ── Session lifecycle ────────────────────────────────────────────────── */
function ingestState(gameState) {
    if (!gameState) return;
    state.characters = gameState.characters || {};
    state.order = Object.keys(state.characters);
    state.controlledId = gameState.player && gameState.player.controlled_character_id;
    if (gameState.scene) renderScene(gameState.scene);
}

async function startSession(cfg) {
    // reset the view
    chatLog.innerHTML = '';
    chatLog.appendChild(emptyState);
    emptyState.style.display = 'flex';
    renderOptions(null);
    sceneTags.innerHTML = '';
    sceneLocation.textContent = '';
    debugContent.innerHTML =
        '<p class="debug-placeholder">Envie um turno ou use "Preview do prompt".</p>';

    setLoading(true);
    try {
        const data = await api.startSession(cfg);
        state.sessionId = data.session_id;
        ingestState(data.state);
        emptyState.style.display = 'none';
        inputSpeech.disabled = false;
        inputAction.disabled = false;
        sendBtn.disabled = false;
        inputAction.placeholder = `🎬 Ação (você é ${controlledName()})`;
        inputSpeech.focus();
        toast(`Aventura iniciada como ${controlledName()}`, 'success', 2500);
    } catch (err) {
        toast(`Erro ao iniciar sessão: ${err.message}`, 'error');
        emptyState.style.display = 'flex';
    } finally {
        setLoading(false);
    }
}

async function sendTurn(chosenOption = null) {
    if (!state.sessionId) return;
    const speech = inputSpeech.value.trim();
    const action = inputAction.value.trim();
    const chosenOptionVal = chosenOption !== null ? chosenOption : undefined;

    // Echo the player's own input as a bubble (only on a fresh action, not option replays)
    if (chosenOption === null && (speech || action)) {
        const echo = [speech, action ? `🎬 ${action}` : ''].filter(Boolean).join('\n');
        addMessage('Player', echo, 'speech');
    }

    setLoading(true);
    renderOptions(null);

    try {
        const data = await api.turn(state.sessionId, {
            speech: speech || '',
            action: action || '',
            chosen_option: chosenOptionVal,
            debug: state.debug,
        });

        if (state.debug && data.debug) renderDebug(data.debug);

        // Narrator asked for a choice — pause, show options
        if (data.type === 'options') {
            renderOptions(data.options);
            inputSpeech.value = '';
            inputAction.value = '';
            inputSpeech.focus();
            setLoading(false);
            return;
        }

        if (data.narration) addMessage('Narrator', data.narration, 'narration');
        if (data.character_response) {
            addMessage(data.next_speaker || 'Narrator', data.character_response, 'speech');
        }

        if (data.scene_update) {
            try {
                const gameState = await api.getState(state.sessionId);
                renderScene(gameState.scene, Object.keys(data.scene_update));
            } catch { /* scene refresh is non-critical */ }
        }

        if (data.player_options && data.player_options.length > 0) {
            renderOptions(data.player_options);
        } else {
            renderOptions(null);
        }

        inputSpeech.value = '';
        inputAction.value = '';
        inputSpeech.focus();
    } catch (err) {
        // Graceful: llama down returns 500 — show a friendly message.
        toast(`Falha no turno: ${err.message}. O LLM está rodando?`, 'error', 6000);
    } finally {
        setLoading(false);
    }
}

/* ── Event wiring ─────────────────────────────────────────────────────── */
sendBtn.addEventListener('click', () => sendTurn());

inputAction.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTurn(); }
});
inputSpeech.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inputAction.focus(); }
});

newSessionBtn.addEventListener('click', () => Setup.open());
settingsBtn.addEventListener('click', () => Setup.open());
if (emptyConfigBtn) emptyConfigBtn.addEventListener('click', () => Setup.open());

function setDebug(on) {
    state.debug = on;
    debugToggle.checked = on;
    debugDrawer.classList.toggle('active', on);
}
debugToggle.addEventListener('change', () => setDebug(debugToggle.checked));
if (debugCloseBtn) debugCloseBtn.addEventListener('click', () => setDebug(false));

previewBtn.addEventListener('click', previewPrompt);

/* ── PWA: install prompt + service worker ─────────────────────────────── */
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) installBtn.hidden = false;
});
if (installBtn) {
    installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        await deferredPrompt.userChoice;
        deferredPrompt = null;
        installBtn.hidden = true;
    });
}
window.addEventListener('appinstalled', () => {
    if (installBtn) installBtn.hidden = true;
    toast('App instalado 🎉', 'success', 2500);
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => { /* offline shell optional */ });
    });
}

/* ── Init ─────────────────────────────────────────────────────────────── */
Setup.init({ onStart: (cfg) => startSession(cfg) });
Setup.open(); // show setup on first load
