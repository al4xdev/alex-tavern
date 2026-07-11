/* ══════════════════════════════════════════════════════════════════════
   app.js — game view: dynamic rendering, turns, debug drawer, toasts.
   ══════════════════════════════════════════════════════════════════════ */

/* ── State ────────────────────────────────────────────────────────────── */
const state = {
    sessionId: null,
    characters: {},     // cid -> {mind, body} (from GET state)
    controlledId: null,
    order: [],          // stable ordering of cids for color assignment
    debug: false,
    lastInputs: null,       // { speech, action, forceSpeaker } for retry
    lastTurnFailed: false,  // true when last sendTurn errored
    canUndo: false,         // true when there's a turn to undo
    abortController: null,  // AbortController for current turn
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
const sessionsBtn   = document.getElementById('sessions-btn');
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
const debugRefreshBtn = document.getElementById('debug-refresh-btn');
const actionUndoBtn = document.getElementById('action-undo-btn');
const actionRetryBtn = document.getElementById('action-retry-btn');
const actionSuggestBtn = document.getElementById('action-suggest-btn');
const actionCompactBtn = document.getElementById('action-compact-btn');
const compactProgress = document.getElementById('compact-progress');
const forceSpeakerSelect = document.getElementById('force-speaker-select');
const actionPopup   = document.getElementById('action-popup');
const stopBtn       = document.getElementById('stop-btn');
const sessionsOverlay = document.getElementById('sessions-overlay');
const sessionsBody  = document.getElementById('sessions-body');
const sessionList   = document.getElementById('session-list');
const sessionsCloseBtn = document.getElementById('sessions-close-btn');
const sessionsNewBtn  = document.getElementById('sessions-new-btn');

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

/* ── Action popup (undo / retry / force-speaker / suggest) ────────────── */
function updateActionPopup() {
    if (actionUndoBtn) actionUndoBtn.style.display = state.canUndo ? '' : 'none';
    if (actionRetryBtn) actionRetryBtn.style.display = state.lastTurnFailed ? '' : 'none';
    const hasSession = !!state.sessionId;
    if (forceSpeakerSelect) forceSpeakerSelect.style.display = hasSession ? '' : 'none';
    if (actionSuggestBtn) actionSuggestBtn.style.display = hasSession ? '' : 'none';
    if (actionCompactBtn) actionCompactBtn.style.display = hasSession ? '' : 'none';
    // Hide the popup entirely when there's nothing to show — prevents
    // an empty bordered box (tiny black dot) from appearing on hover/long-press.
    if (actionPopup) {
        actionPopup.style.display = (state.canUndo || state.lastTurnFailed || hasSession) ? '' : 'none';
    }
}

function hideActionPopup() {
    if (actionPopup) actionPopup.classList.remove('visible');
}

/* ── Session manager ──────────────────────────────────────────────────── */
function timeAgo(iso) {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return 'agora';
    const min = Math.floor(sec / 60);
    if (min < 60) return `há ${min}m`;
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return `há ${hrs}h`;
    const days = Math.floor(hrs / 24);
    if (days < 30) return `há ${days}d`;
    return iso.slice(0, 10);
}

async function openSessionsModal() {
    sessionsOverlay.classList.add('active');
    try {
        const list = await api.listSessions();
        renderSessionList(list);
    } catch (err) {
        toast(`Erro ao listar sessões: ${err.message}`, 'error');
    }
}

function closeSessionsModal() {
    sessionsOverlay.classList.remove('active');
}

function renderSessionList(sessions) {
    sessionList.innerHTML = '';
    if (!sessions || sessions.length === 0) {
        sessionList.innerHTML = '<p class="session-empty">Nenhuma sessão ainda. Crie uma nova!</p>';
        return;
    }
    sessions.forEach((s) => {
        const card = document.createElement('div');
        card.className = 'session-card';
        if (s.session_id === state.sessionId) card.classList.add('active');

        // Character tags
        const tagsHtml = (s.characters || [])
            .filter((c) => c.name)
            .map((c) => `<span class="session-char-tag">${escHtml(c.name)}</span>`)
            .join('');

        const sceneText = s.scene_location || '';
        const turnText = s.turn_count > 0 ? `${s.turn_count} turnos` : '0 turnos';
        const dateText = timeAgo(s.created_at);
        const extra = [turnText, dateText].filter(Boolean).join(' · ');

        card.innerHTML = `
            <div class="session-info">
                <div class="session-char-tags">${tagsHtml}</div>
                <div class="session-meta">
                    <span class="session-meta-item">${escHtml(sceneText)}</span>
                    ${extra ? `<span class="session-meta-item">${extra}</span>` : ''}
                </div>
            </div>
            <div class="session-scene">${escHtml(sceneText)}</div>
            <div class="session-actions">
                <button class="session-action-btn" data-action="fork" title="Fork (copiar)">🔀</button>
                <button class="session-action-btn danger" data-action="delete" title="Apagar">🗑️</button>
            </div>
        `;

        // Click to load
        card.addEventListener('click', (e) => {
            if (e.target.closest('.session-actions')) return;
            loadSession(s.session_id);
        });

        // Long-press for mobile actions
        let longTimer = null;
        card.addEventListener('pointerdown', () => {
            longTimer = setTimeout(() => card.classList.add('show-actions'), 600);
        });
        card.addEventListener('pointerup', () => { clearTimeout(longTimer); longTimer = null; });
        card.addEventListener('pointerleave', () => { clearTimeout(longTimer); longTimer = null; });
        card.addEventListener('contextmenu', (e) => { e.preventDefault(); card.classList.toggle('show-actions'); });

        // Action buttons
        card.querySelector('[data-action="fork"]').addEventListener('click', async (e) => {
            e.stopPropagation();
            card.classList.remove('show-actions');
            try {
                const result = await api.forkSession(s.session_id);
                toast(`Fork criado: ${result.session_id}`, 'success', 3000);
                // Refresh list
                const list = await api.listSessions();
                renderSessionList(list);
            } catch (err) {
                toast(`Erro no fork: ${err.message}`, 'error');
            }
        });
        card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
            e.stopPropagation();
            card.classList.remove('show-actions');
            if (!confirm(`Apagar sessão ${s.session_id}?`)) return;
            try {
                await api.deleteSession(s.session_id);
                card.remove();
                toast('Sessão apagada', 'info', 2500);
                if (s.session_id === state.sessionId) {
                    // Current session was deleted — reset UI
                    state.sessionId = null;
                    chatLog.innerHTML = '';
                    chatLog.appendChild(emptyState);
                    emptyState.style.display = 'flex';
                    clearSuggestions();
                    renderScene({});
                }
            } catch (err) {
                toast(`Erro ao apagar: ${err.message}`, 'error');
            }
        });

        sessionList.appendChild(card);
    });
}

function escHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str || ''));
    return div.innerHTML;
}

/* Clears the chat log and re-renders it from the authoritative backend
   history — merges the Player's speech+action of a turn into one bubble
   (same as the live echo in sendTurn). Used on session load AND after undo,
   so the DOM never has to guess how many bubbles a turn produced. */
function renderHistory(history) {
    chatLog.innerHTML = '';
    chatLog.appendChild(emptyState);
    emptyState.style.display = 'none';

    let playerBuffer = null; // { turnNumber, speech, action }
    const flushPlayerBuffer = () => {
        if (!playerBuffer) return;
        addMessage('Player', buildPlayerEcho(playerBuffer.speech, playerBuffer.action), 'speech');
        playerBuffer = null;
    };
    for (const record of (history || [])) {
        if (record.speaker === 'Player' && (record.content_type === 'speech' || record.content_type === 'action')) {
            if (!playerBuffer || playerBuffer.turnNumber !== record.turn_number) {
                flushPlayerBuffer();
                playerBuffer = { turnNumber: record.turn_number, speech: '', action: '' };
            }
            playerBuffer[record.content_type] = record.content;
            continue;
        }
        flushPlayerBuffer();
        addMessage(record.speaker, record.content, record.content_type);
    }
    flushPlayerBuffer();
}

async function loadSession(sessionId) {
    try {
        const gameState = await api.getState(sessionId);
        clearSuggestions();
        debugContent.innerHTML = '<p class="debug-placeholder">Clique em "🔄 Log" ou "Preview do prompt".</p>';

        state.sessionId = sessionId;
        state.lastInputs = null;
        state.lastTurnFailed = false;
        state.canUndo = gameState.history && gameState.history.length > 0;
        updateActionPopup();
        ingestState(gameState);

        renderHistory(gameState.history);

        inputSpeech.disabled = false;
        inputAction.disabled = false;
        sendBtn.disabled = false;
        inputAction.placeholder = `🎬 Ação (você é ${controlledName()})`;
        inputSpeech.focus();

        closeSessionsModal();
        toast(`Sessão ${sessionId} carregada`, 'success', 2500);
    } catch (err) {
        toast(`Erro ao carregar sessão: ${err.message}`, 'error');
    }
}

async function undoLastTurn() {
    if (!state.sessionId || !state.canUndo) return;
    hideActionPopup();
    setLoading(true);
    try {
        const data = await api.undo(state.sessionId);
        if (!data.undone) { toast('Nada a desfazer', 'info', 2500); setLoading(false); return; }

        // Re-render from the authoritative history returned by the backend,
        // instead of guessing how many DOM bubbles the undone step had — a
        // step can produce fewer than 3 (e.g. no character response), and
        // removing a fixed count desyncs the DOM from the real state.
        if (data.state) {
            renderHistory(data.state.history);
            ingestState(data.state);
        }
        state.lastTurnFailed = false;
        state.canUndo = !!(data.state && data.state.history && data.state.history.length > 0);
        updateActionPopup();
        toast('Turno desfeito', 'success', 2000);
    } catch (err) {
        toast(`Erro ao desfazer: ${err.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

function retryTurn() {
    if (!state.lastInputs) return;
    hideActionPopup();
    // Restore inputs (they may have been cleared on error)
    inputSpeech.value = state.lastInputs.speech || '';
    inputAction.value = state.lastInputs.action || '';
    if (forceSpeakerSelect) forceSpeakerSelect.value = state.lastInputs.forceSpeaker || '';
    sendTurn(true);
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
/* ── Typewriter reveal (Narrator/Character messages only) ─────────────── */
const TYPE_MS_PER_CHAR = 6;
const TYPE_MIN_MS = 220;
const TYPE_MAX_MS = 1400;

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/* Reveals `units` (an array of {node, text}, nodes already in the DOM but
   empty) progressively over a duration proportional to the total text
   length. Clicking `msg` while revealing skips straight to the full text. */
function revealTypewriter(msg, units) {
    const totalLen = units.reduce((sum, u) => sum + u.text.length, 0);
    if (totalLen === 0) return;
    const durationMs = Math.min(TYPE_MAX_MS, Math.max(TYPE_MIN_MS, totalLen * TYPE_MS_PER_CHAR));

    let done = false;
    const start = performance.now();

    function showChars(count) {
        let remaining = count;
        for (const u of units) {
            if (remaining <= 0) { u.node.textContent = ''; continue; }
            u.node.textContent = u.text.slice(0, remaining);
            remaining -= u.text.length;
        }
    }

    function finish() {
        if (done) return;
        done = true;
        showChars(totalLen);
        msg.removeEventListener('click', onSkip);
        scrollToBottom();
    }

    function onSkip() { finish(); }
    msg.addEventListener('click', onSkip);

    function tick(now) {
        if (done) return;
        const elapsed = now - start;
        const shown = Math.floor((elapsed / durationMs) * totalLen);
        if (shown >= totalLen) { finish(); return; }
        showChars(shown);
        scrollToBottom();
        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function addMessage(speaker, content, contentType, { animate = false } = {}) {
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
    const shouldType = animate && !prefersReducedMotion();

    // Render **text** as italic thought
    const parts = content.split(/(\*\*[^*]+\*\*)/g);
    const units = [];
    for (const part of parts) {
        if (!part) continue;
        const isThought = part.startsWith('**') && part.endsWith('**');
        const text = isThought ? part.slice(2, -2) : part;
        let node;
        if (isThought) {
            node = document.createElement('span');
            node.className = 'thought';
        } else {
            node = document.createTextNode('');
        }
        node.textContent = shouldType ? '' : text;
        body.appendChild(node);
        units.push({ node, text });
    }
    msg.appendChild(body);
    chatLog.appendChild(msg);
    emptyState.style.display = 'none';
    scrollToBottom();

    if (shouldType) revealTypewriter(msg, units);
}

/* Combines the player's speech + action into the single echo bubble text
   (used both for the live echo in sendTurn and for replaying history). */
function buildPlayerEcho(speech, action) {
    return [speech, action ? `🎬 ${action}` : ''].filter(Boolean).join('\n');
}

/* ── Sugestão de jogada ("sugira pra mim") ─────────────────────────────── */
function clearSuggestions() {
    optionsPanel.innerHTML = '';
    optionsPanel.classList.remove('active');
}

function renderSuggestions(suggestions) {
    optionsPanel.innerHTML = '';
    if (!suggestions || suggestions.length === 0) {
        optionsPanel.classList.remove('active');
        return;
    }
    optionsPanel.classList.add('active');

    suggestions.forEach((s, i) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.style.animationDelay = `${i * 0.06}s`;

        const label = document.createElement('span');
        label.className = 'opt-label';
        label.textContent = s.speech || '(sem fala)';
        btn.appendChild(label);

        if (s.action) {
            const desc = document.createElement('span');
            desc.className = 'opt-desc';
            desc.textContent = `🎬 ${s.action}`;
            btn.appendChild(desc);
        }
        // Preenche as duas caixas — não envia sozinho, o jogador confirma no Enviar.
        btn.addEventListener('click', () => {
            inputSpeech.value = s.speech || '';
            inputAction.value = s.action || '';
            clearSuggestions();
            inputSpeech.focus();
        });
        optionsPanel.appendChild(btn);
    });
}

async function suggestForMe() {
    if (!state.sessionId) return;
    hideActionPopup();
    setLoading(true);
    try {
        const data = await api.suggest(state.sessionId);
        renderSuggestions(data.suggestions);
        toast('Sugestões prontas — escolha uma', 'success', 2500);
    } catch (err) {
        toast(`Erro ao sugerir: ${err.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/* ── Compactar sessão ─────────────────────────────────────────────────── */
// NOTE: the progress fill below is a MOCKED estimate, not real backend
// progress — measuring actual LLM generation progress would require
// streaming (SSE), which is more than this personal MVP needs right now.
// We guess a duration from how much is on screen, animate up to ~90%
// over that guess, and only jump to 100% once the real response lands.
// Fine to swap for real progress later if that's ever worth doing.
async function compactSession() {
    if (!state.sessionId || !actionCompactBtn || !compactProgress) return;
    hideActionPopup();

    const msgCount = chatLog.querySelectorAll('.msg').length;
    const estimatedMs = Math.min(3500, 400 + msgCount * 120);
    actionCompactBtn.classList.add('busy');
    compactProgress.style.width = '0%';
    const start = performance.now();
    let done = false;

    function tick(now) {
        if (done) return;
        const elapsed = now - start;
        const pct = Math.min(90, (elapsed / estimatedMs) * 90);
        compactProgress.style.width = `${pct}%`;
        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);

    try {
        const data = await api.compact(state.sessionId);
        done = true;
        compactProgress.style.width = '100%';
        if (data.compacted) {
            toast(
                `Compactado: ${data.evicted_turns} registros resumidos, ${data.kept_turns} mantidos`,
                'success',
                3500
            );
            const gameState = await api.getState(state.sessionId);
            ingestState(gameState);
            renderHistory(gameState.history);
            state.canUndo = !!(gameState.history && gameState.history.length > 0);
            updateActionPopup();
        } else {
            toast(data.reason || 'Nada para compactar ainda', 'info', 2500);
        }
    } catch (err) {
        done = true;
        toast(`Erro ao compactar: ${err.message}`, 'error');
    } finally {
        setTimeout(() => {
            actionCompactBtn.classList.remove('busy');
            compactProgress.style.width = '0%';
        }, 400);
    }
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

/* Log bruto e sequencial de TODAS as chamadas LLM da sessão (GET /debug_log) —
   substitui o antigo debug embutido na resposta do turno. Uma entrada por
   chamada real (inclui retries), na ordem em que aconteceram. */
function renderRawLog(entries) {
    debugContent.innerHTML = '';
    if (!entries || entries.length === 0) {
        debugContent.innerHTML =
            '<p class="debug-placeholder">Nenhuma chamada LLM registrada ainda nesta sessão.</p>';
        return;
    }
    entries.forEach((e) => {
        const title = `Turno ${e.turn_number} · ${e.agent}${e.error ? ' · ERRO' : ''}`;
        const messages = (e.request && e.request.messages) || [];
        const raw = e.error ? `[ERROR] ${e.error}` : e.response;
        debugContent.appendChild(renderDebugBlock(title, messages, raw));
    });
}

async function refreshDebugLog() {
    if (!state.sessionId) return;
    try {
        const entries = await api.getDebugLog(state.sessionId);
        renderRawLog(entries);
    } catch (err) {
        toast(`Erro ao carregar log: ${err.message}`, 'error');
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

function populateForceSpeakerOptions() {
    if (!forceSpeakerSelect) return;
    const current = forceSpeakerSelect.value;
    forceSpeakerSelect.innerHTML = '<option value="">🎲 Automático</option>';
    for (const cid of state.order) {
        const ch = state.characters[cid];
        if (!ch) continue;
        const opt = document.createElement('option');
        opt.value = cid;
        opt.textContent = ch.mind.name;
        forceSpeakerSelect.appendChild(opt);
    }
    const narratorOpt = document.createElement('option');
    narratorOpt.value = 'Narrator';
    narratorOpt.textContent = '🎭 Narrador';
    forceSpeakerSelect.appendChild(narratorOpt);
    if ([...forceSpeakerSelect.options].some((o) => o.value === current)) {
        forceSpeakerSelect.value = current;
    }
}

/* ── Session lifecycle ────────────────────────────────────────────────── */
function ingestState(gameState) {
    if (!gameState) return;
    state.characters = gameState.characters || {};
    state.order = Object.keys(state.characters);
    state.controlledId = gameState.player && gameState.player.controlled_character_id;
    if (gameState.scene) renderScene(gameState.scene);
    populateForceSpeakerOptions();
}

async function startSession(cfg) {
    // reset the view
    chatLog.innerHTML = '';
    chatLog.appendChild(emptyState);
    emptyState.style.display = 'flex';
    clearSuggestions();
    sceneTags.innerHTML = '';
    sceneLocation.textContent = '';
    debugContent.innerHTML =
        '<p class="debug-placeholder">Clique em "🔄 Log" ou "Preview do prompt".</p>';

    setLoading(true);
    try {
        const data = await api.startSession(cfg);
        state.sessionId = data.session_id;
        state.lastInputs = null;
        state.lastTurnFailed = false;
        state.canUndo = false;
        updateActionPopup();
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

async function sendTurn(isRetry = false) {
    if (!state.sessionId) return;
    const speech = inputSpeech.value.trim();
    const action = inputAction.value.trim();
    const forceSpeaker = forceSpeakerSelect ? forceSpeakerSelect.value : '';

    // Save inputs for potential retry
    state.lastInputs = { speech, action, forceSpeaker };

    // Echo the player's own input as a bubble (skip on retry to avoid duplicates)
    if (!isRetry && (speech || action)) {
        addMessage('Player', buildPlayerEcho(speech, action), 'speech');
    }

    setLoading(true);
    clearSuggestions();
    state.lastTurnFailed = false;
    updateActionPopup();

    // Create AbortController for stop button
    const ac = new AbortController();
    state.abortController = ac;

    try {
        const data = await api.turn(state.sessionId, {
            speech: speech || '',
            action: action || '',
            force_speaker: forceSpeaker || undefined,
        }, ac.signal);

        if (state.debug) refreshDebugLog();

        if (data.narration) addMessage('Narrator', data.narration, 'narration', { animate: true });
        if (data.character_response) {
            addMessage(data.next_speaker || 'Narrator', data.character_response, 'speech', { animate: true });
        }

        if (data.scene_update) {
            try {
                const gameState = await api.getState(state.sessionId);
                renderScene(gameState.scene, Object.keys(data.scene_update));
            } catch { /* scene refresh is non-critical */ }
        }

        inputSpeech.value = '';
        inputAction.value = '';
        if (forceSpeakerSelect) forceSpeakerSelect.value = '';
        inputSpeech.focus();
        state.lastTurnFailed = false;
        state.canUndo = true;
        updateActionPopup();
    } catch (err) {
        if (err.name === 'AbortError') {
            // User pressed stop — don't treat as failure, keep inputs
            toast('Turno cancelado', 'info', 2500);
            state.lastTurnFailed = false;
        } else {
            state.lastTurnFailed = true;
            // Keep inputs in fields so user can edit and retry
            toast(`Falha no turno: ${err.message}. O LLM está rodando?`, 'error', 6000);
        }
        updateActionPopup();
    } finally {
        state.abortController = null;
        setLoading(false);
    }
}

/* ── Event wiring ─────────────────────────────────────────────────────── */
sendBtn.addEventListener('click', (e) => {
    // If popup was opened via long-press, close it instead of sending
    if (actionPopup && actionPopup.classList.contains('visible')) {
        hideActionPopup();
        return;
    }
    sendTurn();
});

// Long-press / hover for action popup
let longPressTimer = null;
const LONG_PRESS_MS = 600;

function showActionPopup() {
    if (!state.canUndo && !state.lastTurnFailed && !state.sessionId) return;
    if (actionPopup) actionPopup.classList.add('visible');
}
function cancelLongPress() {
    if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null; }
}

sendBtn.addEventListener('pointerdown', () => {
    cancelLongPress();
    longPressTimer = setTimeout(() => showActionPopup(), LONG_PRESS_MS);
});
sendBtn.addEventListener('pointerup', cancelLongPress);
sendBtn.addEventListener('pointerleave', cancelLongPress);
sendBtn.addEventListener('pointercancel', cancelLongPress);
// Prevent text selection context menu on long-press for ALL icon/action buttons
document.addEventListener('contextmenu', (e) => {
    if (e.target.closest('button')) e.preventDefault();
});

// Hide popup when clicking outside
document.addEventListener('click', (e) => {
    if (actionPopup && !actionPopup.contains(e.target) && e.target !== sendBtn) {
        hideActionPopup();
    }
});

// Undo / retry button clicks
if (actionUndoBtn) actionUndoBtn.addEventListener('click', undoLastTurn);
if (actionRetryBtn) actionRetryBtn.addEventListener('click', retryTurn);
if (actionSuggestBtn) actionSuggestBtn.addEventListener('click', suggestForMe);
if (actionCompactBtn) actionCompactBtn.addEventListener('click', compactSession);

// Stop button — abort current turn
if (stopBtn) stopBtn.addEventListener('click', () => {
    if (state.abortController) state.abortController.abort();
});

inputAction.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTurn(); }
});
inputSpeech.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inputAction.focus(); }
});

// Sessions button — open sessions modal
if (sessionsBtn) sessionsBtn.addEventListener('click', openSessionsModal);
if (sessionsCloseBtn) sessionsCloseBtn.addEventListener('click', closeSessionsModal);
if (sessionsNewBtn) sessionsNewBtn.addEventListener('click', () => {
    closeSessionsModal();
    Setup.open();
});
sessionsOverlay.addEventListener('click', (e) => {
    if (e.target === sessionsOverlay) closeSessionsModal();
});
settingsBtn.addEventListener('click', () => Setup.open());
if (emptyConfigBtn) emptyConfigBtn.addEventListener('click', () => Setup.open());

function setDebug(on) {
    state.debug = on;
    debugToggle.checked = on;
    debugDrawer.classList.toggle('active', on);
    if (on) refreshDebugLog();
}
debugToggle.addEventListener('change', () => setDebug(debugToggle.checked));
if (debugCloseBtn) debugCloseBtn.addEventListener('click', () => setDebug(false));
if (debugRefreshBtn) debugRefreshBtn.addEventListener('click', refreshDebugLog);

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
openSessionsModal(); // show sessions list on first load (empty state offers "Nova sessão")
