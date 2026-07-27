import { el } from './dom.js';
import { api } from './api.js';
import { restartApplication } from './android-bridge.js';
import * as DebugDrawer from './debug-drawer.js';
import * as Onboarding from './onboarding.js';
import * as OpeningPicker from './opening-picker.js';
import * as SessionsModal from './sessions-modal.js';
import * as Compaction from './compaction-ui.js';
import * as Composer from './composer.js';
import {
    clearSuggestions,
    expandMobileInput,
    hideActionPopup,
    openHintPopup,
    populateForceSpeakerOptions,
    renderSuggestions,
    setSuggestionsLoading,
    skipTurn,
    suggestForMe,
    undoLastTurn,
    updateActionPopup,
    updateSpeechPlaceholder,
    whisperNamesFor,
} from './composer.js';
import * as Transcript from './transcript.js';
import {
    addMessage,
    buildPlayerEcho,
    controlledName,
    renderHistory,
    scrollToBottom,
    updatePlayerEcho,
} from './transcript.js';
import { RuntimeConfig } from './runtime-config.js';
import { PluginRuntime } from './plugin-runtime.js';
import { PluginCenter } from './plugin-center.js';
import { Setup } from './setup.js';
import { SlashCommands } from './slash-commands.js';
import {
    registerCoreAction,
    registerCoreCommandResultRenderer,
} from './slash-registry.js';
import {
    bindTranslation,
    getLocale,
    onLocaleChange,
    setLocale,
    t,
    translateDocument,
} from './i18n.js';

/* ══════════════════════════════════════════════════════════════════════
   app.js — the game view: session state, the turn flow, and the wiring that
   hands the other modules what they need.
   ══════════════════════════════════════════════════════════════════════ */

/* ── State ────────────────────────────────────────────────────────────── */
const state = {
    sessionId: null,
    characters: {},     // cid -> {mind, body} (from GET state)
    controlledId: null,
    order: [],          // stable ordering of cids for color assignment
    debug: false,
    lastInputs: null,       // { speech, thought, action, forceSpeaker } for retry
    lastTurnFailed: false,  // true when last sendTurn errored
    canUndo: false,         // true when there's a turn to undo
    abortController: null,  // AbortController for current turn
    compactionAbortController: null,
    compactionDepth: 0,
    busy: false,
    narratorHint: '',       // pending narrator event hint for next turn
    suggestionsLoading: false, // a suggestion fetch is in flight (manual or plugin preload)
    lastEchoMessage: null,  // optimistic player bubble updated with effective input
    playerHasSpoken: false, // derived from canonical history; controls observer warning only
    avatarUrls: {},        // cid -> revisioned native preset avatar URL
};

const COMPACT_LAYOUT_QUERY = '(max-width: 760px), (pointer: coarse) and (hover: none)';
const compactLayoutMedia = window.matchMedia(COMPACT_LAYOUT_QUERY);

function isCompactLayout() {
    return compactLayoutMedia.matches;
}

/* ── DOM refs ─────────────────────────────────────────────────────────── */
const chatLog       = el('chat-log');
const sceneLocation = el('scene-location');
const sceneTags     = el('scene-tags');
const scenePanel    = el('scene-panel');
const optionsPanel  = el('options-panel');
const inputArea     = el('input-area');
const inputExpandBtn= el('input-expand-btn');
const inputSpeech   = el('input-speech');
const inputThought  = el('input-thought');
const inputAction   = el('input-action');
const sendBtn       = el('send-btn');
const settingsBtn   = el('settings-btn');
const emptyConfigBtn= el('empty-config-btn');
const spinner       = el('spinner');
const spinnerLabel  = el('spinner-label');
const retryBanner   = el('retry-banner');
const retryBannerBtn = el('retry-banner-btn');
const roteiroEnabledInput = el('runtime-roteiro-enabled');
const emptyState    = el('empty-state');
const emptyKicker   = el('empty-kicker');
const emptyPrompt   = el('empty-prompt');
const emptyScrollCue= el('empty-scroll-cue');
const toastWrap     = el('toast-wrap');
const installBtn    = el('install-btn');
const actionUndoBtn = el('action-undo-btn');
const actionRetryBtn = el('action-retry-btn');
const actionSkipBtn = el('action-skip-btn');
const actionExpandMoreBtn = el('action-expand-more-btn');
const actionPopupSecondary = el('action-popup-secondary');
const actionSuggestBtn = el('action-suggest-btn');
const actionHintBtn = el('action-hint-btn');
const forceSpeakerSelect = el('force-speaker-select');
const whisperBtn = el('action-whisper-btn');
const whisperPopup = el('whisper-popup');
const actionPopup   = el('action-popup');
const stopBtn       = el('stop-btn');
const interfaceLanguage = el('interface-language');

const hintOverlay   = el('hint-overlay');
const hintTextarea  = el('hint-textarea');
const hintSendBtn   = el('hint-send-btn');
const hintCloseBtn  = el('hint-close-btn');



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
// After a short delay a long turn swaps the generic spinner label for a
// reassuring, progressive message so the wait never reads as a frozen app.
// Purely time-based (frontend-only) — no backend progress signal involved.
// The multi-step wording is reserved for the turns that really are multi-step:
// a continuation runs several beats, a turn the player wrote runs exactly one,
// and promising "this is long" on both is what made a normal turn look like a
// runaway burst (owner report, 2026-07-21).
const LOADING_REASSURE_MS = 3500;
let loadingReassureTimer = null;

function setLoading(on, { multiStep = false } = {}) {
    state.busy = on;
    const disable = on || !state.sessionId;
    inputSpeech.disabled = on;
    inputThought.disabled = disable;
    inputAction.disabled = disable;
    sendBtn.disabled = disable;
    spinner.classList.toggle('active', on);

    if (loadingReassureTimer) { clearTimeout(loadingReassureTimer); loadingReassureTimer = null; }
    if (!spinnerLabel) return;
    if (on) {
        loadingReassureTimer = setTimeout(() => {
            const storyFlavor = multiStep && !!(roteiroEnabledInput && roteiroEnabledInput.checked);
            bindTranslation(spinnerLabel, storyFlavor ? 'loading.stillWorkingStory' : 'loading.stillWorking');
        }, LOADING_REASSURE_MS);
    } else {
        bindTranslation(spinnerLabel, 'loading.processing');
    }
}

function showEmptyState(sessionReady = false) {
    emptyState.classList.toggle('session-ready', sessionReady);
    bindTranslation(emptyKicker, sessionReady ? 'empty.sessionKicker' : 'empty.kicker');
    bindTranslation(emptyPrompt, sessionReady ? 'empty.sessionPrompt' : 'empty.prompt');
    emptyConfigBtn.hidden = sessionReady;
    if (!sessionReady) bindTranslation(emptyConfigBtn, 'sessions.manage');
    OpeningPicker.setVisible(sessionReady);
    emptyScrollCue.hidden = !sessionReady;
    emptyState.style.display = 'flex';
}

/* ── Session manager ──────────────────────────────────────────────────── */
async function loadSession(sessionId) {
    try {
        state.compactionAbortController?.abort();
        OpeningPicker.reset();
        let gameState = await api.getState(sessionId);
        gameState = await PluginRuntime.runHook('session.state', gameState, { state });
        clearSuggestions();
        DebugDrawer.reset();

        state.sessionId = sessionId;
        state.lastInputs = null;
        state.lastEchoMessage = null;
        state.lastTurnFailed = false;
        state.canUndo = gameState.history && gameState.history.length > 0;
        updateActionPopup();
        ingestState(gameState);
        await hydrateAvatarUrls(gameState);

        renderHistory(gameState.history);

        inputSpeech.disabled = false;
        inputThought.disabled = false;
        inputAction.disabled = false;
        sendBtn.disabled = false;
        bindTranslation(inputAction, 'input.actionAs', { name: controlledName() }, 'placeholder');
        if (!isCompactLayout()) {
            inputSpeech.focus();
        } else {
            inputArea.classList.add('collapsed');
            chatLog.scrollTop = chatLog.scrollHeight - chatLog.clientHeight - 15;
        }

        SessionsModal.close();
        toast(t('sessions.loaded', { id: sessionId }), 'success', 2500);
        Onboarding.showTipBanner();
    } catch (err) {
        toast(t('sessions.loadError', { error: err.message }), 'error');
    }
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
    
    // Evaluate if tags wrap to multiple lines to show the chevron
    requestAnimationFrame(() => {
        const collapsedHeight = Number.parseFloat(
            getComputedStyle(scenePanel).getPropertyValue('--scene-collapsed-height'),
        );
        if (scenePanel.scrollHeight > collapsedHeight + 1) {
            scenePanel.classList.add('has-multiple-lines');
        } else {
            scenePanel.classList.remove('has-multiple-lines');
            scenePanel.classList.remove('expanded');
        }
    });
}

/* ── Session compaction ───────────────────────────────────────────────── */
function builtinAction(name, icon, scope, title, summary, aliases, keywords, handler, availability = null) {
    registerCoreAction({
        name,
        icon,
        scope,
        title,
        summary,
        aliases,
        keywords,
        ...(availability ? { availability } : {}),
    }, handler);
}

function registerBuiltinSlashEntries() {
    const localized = (en, ptBR) => ({ en, 'pt-BR': ptBR });
    const terms = (en = [], ptBR = []) => ({ en, 'pt-BR': ptBR });
    builtinAction('help', '◇', 'global', localized('Help', 'Ajuda'),
        localized('Open the Alex Tavern guides.', 'Abra os guias do Alex Tavern.'),
        terms([], ['ajuda']), terms(['guide', 'shortcuts'], ['guia', 'atalhos']),
        () => Onboarding.setHelp(true));
    builtinAction('plugins', '✦', 'global', localized('Plugins', 'Plugins'),
        localized('Open Experiences and active plugins.', 'Abra Experiences e plugins ativos.'),
        terms(), terms(['extensions', 'experiences'], ['extensoes', 'experiencias']),
        () => PluginCenter.open());
    builtinAction('settings', '⚙', 'global', localized('Settings', 'Configurações'),
        localized('Configure the adventure and AI engine.', 'Configure a aventura e o motor de IA.'),
        terms([], ['configuracoes']), terms(['configure', 'engine'], ['configurar', 'motor']),
        () => Setup.open());
    builtinAction('sessions', '▤', 'global', localized('Sessions', 'Sessões'),
        localized('Open, fork, or delete adventures.', 'Abra, bifurque ou apague aventuras.'),
        terms([], ['sessoes']), terms(['adventures', 'history'], ['aventuras', 'historico']),
        SessionsModal.open);
    builtinAction('new', '＋', 'global', localized('New adventure', 'Nova aventura'),
        localized('Prepare a new adventure.', 'Prepare uma nova aventura.'),
        terms([], ['novo']), terms(['start', 'create'], ['iniciar', 'criar']),
        () => Setup.open());

    builtinAction('suggest', '💡', 'session', localized('Suggest a move', 'Sugerir jogada'),
        localized('Ask the Narrator for possible moves.', 'Peça ao Narrador possíveis jogadas.'),
        terms([], ['sugestao']), terms(['move', 'idea'], ['jogada', 'ideia']), suggestForMe);
    builtinAction('hint', '📜', 'session', localized('Narrator event', 'Evento do Narrador'),
        localized('Queue an event hint for the Narrator.', 'Prepare uma dica de evento para o Narrador.'),
        terms([], ['dica']), terms(['event', 'narrator'], ['evento', 'narrador']), openHintPopup);
    builtinAction('undo', '↩', 'session', localized('Undo turn', 'Desfazer turno'),
        localized('Remove the latest complete turn.', 'Remova o último turno completo.'),
        terms([], ['desfazer']), terms(['back', 'revert'], ['voltar', 'reverter']), undoLastTurn,
        (context) => context.canUndo || t('commands.nothingToUndo'));
    builtinAction('skip', '⏭', 'session', localized('Skip turn', 'Pular turno'),
        localized('Give the next beat directly to the Narrator.', 'Passe o próximo momento direto ao Narrador.'),
        terms([], ['pular']), terms(['pass', 'continue'], ['passar', 'continuar']), skipTurn);
    builtinAction('compact', '🗜', 'session', localized('Compact history', 'Compactar histórico'),
        localized('Summarize older events into memory.', 'Resuma eventos antigos na memória.'),
        terms([], ['compactar']), terms(['summarize', 'memory'], ['resumir', 'memoria']), Compaction.compactSession);
    builtinAction('restore', '🧯', 'session', localized('Restore compaction', 'Restaurar compactação'),
        localized('Undo the latest compaction checkpoint.', 'Desfaça o checkpoint de compactação mais recente.'),
        terms([], ['restaurar']), terms(['checkpoint', 'uncompact'], ['checkpoint', 'descompactar']),
        Compaction.restoreCompaction, (context) => context.compactionDepth > 0 || t('commands.noCheckpoint'));

    registerCoreCommandResultRenderer('core/completion', async () => {});
    registerCoreCommandResultRenderer('core/character-preset-draft', async (result, context) => {
        const avatar = context.rawFiles['source-file'];
        const avatarFile = avatar && (avatar.type === 'image/png' || avatar.name.toLowerCase().endsWith('.png'))
            ? avatar : null;
        await Setup.openPresetDraft(result.character, result.preset_name, avatarFile);
    });
}

function ingestState(gameState) {
    if (!gameState) return;
    state.characters = gameState.characters || {};
    state.order = Object.keys(state.characters);
    state.controlledId = gameState.player && gameState.player.controlled_character_id;
    state.compactionDepth = Array.isArray(gameState.compaction_stack)
        ? gameState.compaction_stack.length
        : 0;
    if (gameState.scene) renderScene(gameState.scene);
    populateForceSpeakerOptions();
    updateActionPopup();
}

/* Re-read the session from the backend and redraw everything that depends on
   it. The backend is authoritative after any operation that rewrites history —
   compaction, checkpoint restore, undo — so the view never patches its own
   guess of what changed. */
async function reloadView() {
    let gameState = await api.getState(state.sessionId);
    gameState = await PluginRuntime.runHook('session.state', gameState, { state });
    ingestState(gameState);
    renderHistory(gameState.history);
    state.canUndo = !!(gameState.history && gameState.history.length > 0);
    updateActionPopup();
}

/* Everything that submits or alters a turn, disabled as one group while a
   long backend operation owns the session. */
function setTurnControlsDisabled(on) {
    for (const control of [
        sendBtn, actionUndoBtn, actionRetryBtn, actionSkipBtn, actionSuggestBtn, actionHintBtn,
    ]) {
        control.disabled = on;
    }
}

async function hydrateAvatarUrls(gameState) {
    state.avatarUrls = {};
    const byPreset = new Map();
    await Promise.all(Object.entries(gameState?.character_preset_ids || {}).map(async ([cid, name]) => {
        try {
            if (!byPreset.has(name)) byPreset.set(name, api.getPreset(name));
            const preset = await byPreset.get(name);
            if (preset.avatar?.url) state.avatarUrls[cid] = preset.avatar.url;
        } catch { /* the initial remains the stable fallback */ }
    }));
}

async function startSession(cfg) {
    state.compactionAbortController?.abort();
    OpeningPicker.reset();
    // reset the view
    chatLog.innerHTML = '';
    chatLog.appendChild(emptyState);
    showEmptyState(false);
    clearSuggestions();
    DebugDrawer.reset();
    sceneTags.innerHTML = '';
    sceneLocation.textContent = '';

    setLoading(true);
    try {
        const data = await api.startSession(cfg);
        const gameState = await PluginRuntime.runHook('session.state', data.state, { state });
        state.sessionId = data.session_id;
        state.lastInputs = null;
        state.lastEchoMessage = null;
        state.lastTurnFailed = false;
        state.canUndo = false;
        updateActionPopup();
        ingestState(gameState);
        await hydrateAvatarUrls(gameState);
        renderHistory(gameState.history);
        inputSpeech.disabled = false;
        inputThought.disabled = false;
        inputAction.disabled = false;
        sendBtn.disabled = false;
        bindTranslation(inputAction, 'input.actionAs', { name: controlledName() }, 'placeholder');
        if (!isCompactLayout()) inputSpeech.focus();
        toast(t('turn.started', { name: controlledName() }), 'success', 2500);
        Onboarding.showTipBanner();
    } catch (err) {
        toast(t('turn.startError', { error: err.message }), 'error');
        showEmptyState(Boolean(state.sessionId));
    } finally {
        setLoading(false);
    }
}

// Push messages up when the input area expands (chatLog shrinks)
let prevChatLogHeight = chatLog.clientHeight;
new ResizeObserver(() => {
    const newHeight = chatLog.clientHeight;
    const diff = prevChatLogHeight - newHeight;
    if (diff > 0) {
        // Container shrank, push text up
        chatLog.scrollTop += diff;
    } else if (diff < 0) {
        // Container grew, scroll down if we were pinned to bottom
        const distanceToBottom = chatLog.scrollHeight - chatLog.scrollTop - prevChatLogHeight;
        if (distanceToBottom <= 15) {
            chatLog.scrollTop += diff; 
        }
    }
    prevChatLogHeight = newHeight;
}).observe(chatLog);

let lastScrollTop = 0;
chatLog.addEventListener('scroll', () => {
    if (!isCompactLayout()) return;
    
    const currentScrollTop = chatLog.scrollTop;
    const isScrollingUp = currentScrollTop < lastScrollTop;
    const distanceToBottom = chatLog.scrollHeight - currentScrollTop - chatLog.clientHeight;
    
    if (!isScrollingUp && distanceToBottom <= 10) {
        inputArea.classList.remove('collapsed');
    } else if (isScrollingUp && distanceToBottom > 40) {
        const activeEl = document.activeElement;
        const isInputFocused = activeEl === inputSpeech || activeEl === inputThought || activeEl === inputAction;
        if (!isInputFocused) {
            inputArea.classList.add('collapsed');
        }
    }
    lastScrollTop = currentScrollTop;
});

// Sessions button — open sessions modal
settingsBtn.addEventListener('click', () => {
    Setup.open();
});
if (emptyConfigBtn) emptyConfigBtn.addEventListener('click', () => {
    if (state.sessionId) expandMobileInput();
    else SessionsModal.open();
});

if (interfaceLanguage) {
    interfaceLanguage.value = getLocale();
    interfaceLanguage.addEventListener('change', () => setLocale(interfaceLanguage.value));
    onLocaleChange((locale) => {
        interfaceLanguage.value = locale;
        SessionsModal.retranslate();
        DebugDrawer.retranslate();
        OpeningPicker.render();
        updateSpeechPlaceholder();
        if (state.sessionId) {
            bindTranslation(inputAction, 'input.actionAs', { name: controlledName() }, 'placeholder');
            populateForceSpeakerOptions();
        }
    });
}

// Scene panel expand/collapse gestures
let sceneStartY = null;
scenePanel.addEventListener('touchstart', (e) => {
    sceneStartY = e.touches[0].clientY;
}, { passive: true });
scenePanel.addEventListener('touchmove', (e) => {
    if (sceneStartY === null || !scenePanel.classList.contains('has-multiple-lines')) return;
    const diff = e.touches[0].clientY - sceneStartY;
    if (diff > 15) {
        scenePanel.classList.add('expanded');
    } else if (diff < -15) {
        scenePanel.classList.remove('expanded');
    }
}, { passive: true });
scenePanel.addEventListener('touchend', () => {
    sceneStartY = null;
});
scenePanel.addEventListener('click', () => {
    if (scenePanel.classList.contains('has-multiple-lines')) {
        scenePanel.classList.toggle('expanded');
    }
});

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
    toast(t('pwa.installed'), 'success', 2500);
});

window.addEventListener('beforeunload', () => {
    state.compactionAbortController?.abort();
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => { /* offline shell optional */ });
    });
}

/* ── Init ─────────────────────────────────────────────────────────────── */
async function initializeApplication() {
    // Hand the native suggestion panel to the plugin SDK (sdk.ui) before any
    // plugin activates; plugins render through it instead of touching the DOM.
    PluginRuntime.provideUi({ renderSuggestions, clearSuggestions, setSuggestionsLoading });
    try {
        await PluginRuntime.boot();
    } catch (error) {
        console.warn('Plugin frontend boot failed:', error);
    }
    RuntimeConfig.init({
        notify: toast,
        onCompactionHelp: () => {
            Onboarding.setHelp(true);
            Onboarding.showHelpArticle('compaction');
        },
    });
    PluginCenter.init({ notify: toast, restartApplication });
    Composer.init({
        state,
        isCompactLayout,
        notify: toast,
        setLoading,
        ingestState,
        renderScene,
    });
    Compaction.init({
        state,
        reloadView,
        setTurnControlsDisabled,
        setLoading,
        hideActionPopup,
        notify: toast,
    });
    SessionsModal.init({
        state,
        loadSession,
        onNewSession: () => Setup.open(),
        onCurrentSessionDeleted: () => {
            state.sessionId = null;
            state.compactionDepth = 0;
            chatLog.innerHTML = '';
            chatLog.appendChild(emptyState);
            showEmptyState(false);
            clearSuggestions();
            renderScene({});
        },
        notify: toast,
    });
    OpeningPicker.init({
        state,
        setLoading,
        notify: toast,
        skipTurn,
    });
    Transcript.init({
        state,
        isScrollAnchored: () => isCompactLayout() && inputArea.classList.contains('collapsed'),
        resetOpeningSuggestions: OpeningPicker.reset,
        showEmptyState,
        updateSpeechPlaceholder,
        whisperNamesFor,
    });
    DebugDrawer.init({
        getSessionId: () => state.sessionId,
        onToggle: (on) => { state.debug = on; },
        notify: toast,
    });
    Onboarding.init({ setDebug: DebugDrawer.setDebug, notify: toast });
    Setup.init({
        onStart: (cfg) => startSession(cfg),
        onOpen: () => RuntimeConfig.refresh(),
        notify: toast,
    });
    SlashCommands.init({
        getContext: () => ({
            sessionId: state.sessionId,
            busy: state.busy || state.compactionAbortController !== null,
            canUndo: state.canUndo,
            compactionDepth: state.compactionDepth,
            state,
        }),
        notify: toast,
    });
    await PluginRuntime.runHook('app.ready', null, { state, toast });
    Onboarding.checkVersionSync();
}

registerBuiltinSlashEntries();
initializeApplication();
