/* ══════════════════════════════════════════════════════════════════════
   composer.js — the player's input surface and the turn it produces.

   Everything the player touches to act: the three fields, whisper and force
   speaker, the suggestion strip, the narrator-hint popup, the action popup,
   the mobile swipe gestures, and the three entry points that reach the
   backend — send, skip and undo.

   It owns no session state of its own; `state` is the app's, passed in at
   init. The two turn paths (send and skip) differ only in their payload and
   in whether an echo bubble exists, so what happens to a turn RESULT lives in
   one place: applyTurnResult.
   ══════════════════════════════════════════════════════════════════════ */

import { api } from './api.js';
import * as Compaction from './compaction-ui.js';
import * as DebugDrawer from './debug-drawer.js';
import { PluginRuntime } from './plugin-runtime.js';
import { SlashCommands } from './slash-commands.js';
import {
    addMessage,
    buildPlayerEcho,
    renderHistory,
    scrollToBottom,
    updatePlayerEcho,
} from './transcript.js';
import { bindTranslation, t, translateDocument } from './i18n.js';

const inputArea = document.getElementById('input-area');
const inputExpandBtn = document.getElementById('input-expand-btn');
const inputSpeech = document.getElementById('input-speech');
const inputThought = document.getElementById('input-thought');
const inputAction = document.getElementById('input-action');
const inputFieldsContainer = document.getElementById('input-fields-container');
const optionsPanel = document.getElementById('options-panel');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn');
const retryBanner = document.getElementById('retry-banner');
const retryBannerBtn = document.getElementById('retry-banner-btn');
const actionPopup = document.getElementById('action-popup');
const actionPopupSecondary = document.getElementById('action-popup-secondary');
const actionUndoBtn = document.getElementById('action-undo-btn');
const actionRetryBtn = document.getElementById('action-retry-btn');
const actionSkipBtn = document.getElementById('action-skip-btn');
const actionExpandMoreBtn = document.getElementById('action-expand-more-btn');
const actionSuggestBtn = document.getElementById('action-suggest-btn');
const actionHintBtn = document.getElementById('action-hint-btn');
const forceSpeakerSelect = document.getElementById('force-speaker-select');
const whisperBtn = document.getElementById('action-whisper-btn');
const whisperPopup = document.getElementById('whisper-popup');
const hintOverlay = document.getElementById('hint-overlay');
const hintTextarea = document.getElementById('hint-textarea');
const hintSendBtn = document.getElementById('hint-send-btn');
const hintCloseBtn = document.getElementById('hint-close-btn');

const LONG_PRESS_MS = 600;
const SWIPE_AXIS_LOCK_PX = 10;
const SWIPE_VERTICAL_PX = 30;
const SWIPE_DAMPEN = 0.4;
const SWIPE_RESET_MS = 300;

let state = null;
let deps = null;
let isCompactLayout = () => false;
let longPressTimer = null;
let autoSkipOnHintClose = false;
let touchStartX = 0;
let touchStartY = 0;
let isSwipingX = false;
let isSwipingY = false;

/**
 * @param {object} options
 * @param {object} options.state the shared app state
 * @param {() => boolean} options.isCompactLayout
 * @param {(message: string, type?: string, ms?: number) => void} options.notify
 * @param {(on: boolean, opts?: object) => void} options.setLoading
 * @param {(gameState: object) => void} options.ingestState
 * @param {(scene: object, changedKeys?: string[]) => void} options.renderScene
 */
export function init(options) {
    state = options.state;
    deps = options;
    isCompactLayout = options.isCompactLayout;
    wireEvents();
}

export function expandMobileInput({ focus = true } = {}) {
    if (!state.sessionId) return;
    inputArea.classList.remove('collapsed');
    scrollToBottom(true);
    // Opening the bar while a suggestion load is still in flight: tell the
    // player the suggestions are on their way, not lost.
    if (state.suggestionsLoading) deps.notify(t('suggestion.stillLoading'), 'info', 2500);
    if (focus && isCompactLayout()) {
        requestAnimationFrame(() => inputSpeech.focus({ preventScroll: true }));
    }
}

/* ── Action popup (undo / retry / force-speaker / suggest) ────────────── */
export function updateActionPopup() {
    if (actionUndoBtn) actionUndoBtn.style.display = state.canUndo ? '' : 'none';
    if (actionRetryBtn) actionRetryBtn.style.display = state.lastTurnFailed ? '' : 'none';
    const hasSession = !!state.sessionId;
    if (actionSkipBtn) actionSkipBtn.style.display = hasSession ? '' : 'none';
    if (forceSpeakerSelect) forceSpeakerSelect.style.display = hasSession ? '' : 'none';
    if (whisperBtn) whisperBtn.style.display = hasSession ? '' : 'none';
    if (actionSuggestBtn) actionSuggestBtn.style.display = hasSession ? '' : 'none';
    if (actionHintBtn) actionHintBtn.style.display = hasSession ? '' : 'none';
    Compaction.setAvailable(hasSession, state.compactionDepth > 0);
    // Hide the popup entirely when there's nothing to show — prevents
    // an empty bordered box (tiny black dot) from appearing on hover/long-press.
    if (actionPopup) {
        actionPopup.style.display = (state.canUndo || state.lastTurnFailed || hasSession) ? '' : 'none';
    }
    // Persistent, visible retry affordance mirrors the same failure flag as
    // the hidden popup entry, so it appears and clears together with it.
    if (retryBanner) retryBanner.hidden = !state.lastTurnFailed;
    updateExpandPill();
}

export function hideActionPopup() {
    if (actionPopup) actionPopup.classList.remove('visible');
    if (actionPopupSecondary) actionPopupSecondary.classList.remove('open');
    if (actionExpandMoreBtn) actionExpandMoreBtn.classList.remove('active');
}

export function updateSpeechPlaceholder() {
    inputSpeech.placeholder = t(
        state.sessionId && !state.playerHasSpoken
            ? 'input.speechObserver'
            : 'input.speech'
    );
}

/* ── Move suggestions ─────────────────────────────────────────────────── */
/* The pill doubles as a status line for everything folded inside the
   collapsed bar, by priority: a failed turn, ready suggestions, a suggestion
   load still in flight, or the plain write invitation. */
export function updateExpandPill() {
    const label = inputExpandBtn && inputExpandBtn.querySelector('.input-expand-label');
    if (!label) return;
    let key = 'input.expand';
    if (retryBanner && !retryBanner.hidden) key = 'input.expandRetry';
    else if (optionsPanel.classList.contains('active')) key = 'input.expandSuggestions';
    else if (state.suggestionsLoading) key = 'input.expandSuggestionsLoading';
    bindTranslation(label, key);
}

export function setSuggestionsLoading(on) {
    state.suggestionsLoading = !!on;
    updateExpandPill();
}

export function clearSuggestions() {
    optionsPanel.innerHTML = '';
    optionsPanel.classList.remove('active');
    updateExpandPill();
}

export function renderSuggestions(suggestions) {
    optionsPanel.innerHTML = '';
    if (!suggestions || suggestions.length === 0) {
        optionsPanel.classList.remove('active');
        updateExpandPill();
        return;
    }
    optionsPanel.classList.add('active');
    updateExpandPill();

    suggestions.forEach((s, i) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.style.animationDelay = `${i * 0.06}s`;

        const label = document.createElement('span');
        label.className = 'opt-label';
        if (s.speech) label.textContent = s.speech;
        else bindTranslation(label, 'suggestion.fallback', { number: i + 1 });
        btn.appendChild(label);

        if (s.action) {
            const desc = document.createElement('span');
            desc.className = 'opt-desc';
            desc.textContent = `🎬 ${s.action}`;
            btn.appendChild(desc);
        }
        // Fills both boxes — does not send on its own, the player confirms on Send.
        btn.addEventListener('click', () => {
            inputSpeech.value = s.speech || '';
            inputThought.value = '';
            inputAction.value = s.action || '';
            clearSuggestions();
            if (!isCompactLayout()) inputSpeech.focus();
            else expandMobileInput({ focus: false }); // the filled fields must be visible
        });
        optionsPanel.appendChild(btn);
    });
}

export async function suggestForMe() {
    if (!state.sessionId) return;
    hideActionPopup();
    deps.setLoading(true);
    setSuggestionsLoading(true);
    try {
        const data = await api.suggest(state.sessionId);
        setSuggestionsLoading(false);
        renderSuggestions(data.suggestions);
        deps.notify(t('suggestion.ready'), 'success', 2500);
        // The player asked for these — make sure the bar shows them.
        if (isCompactLayout()) expandMobileInput({ focus: false });
    } catch (err) {
        deps.notify(t('suggestion.error', { error: err.message }), 'error');
    } finally {
        setSuggestionsLoading(false);
        deps.setLoading(false);
    }
}

/* ── Narrator hint popup ──────────────────────────────────────────────── */
export function openHintPopup() {
    hideActionPopup();
    hintOverlay.classList.add('active');
    hintTextarea.value = state.narratorHint || '';
    hintTextarea.focus();
    refreshHintSendLabel();
}

// Opened by the swipe gesture, this button also runs a continuation — several
// beats of story, not just a queued event. It has to say so, or the gesture
// silently starts a burst the player never asked for.
function refreshHintSendLabel() {
    if (!hintSendBtn) return;
    bindTranslation(hintSendBtn, autoSkipOnHintClose ? 'hint.sendAndContinue' : 'hint.send');
}

function closeHintPopup() {
    hintOverlay.classList.remove('active');
    autoSkipOnHintClose = false; // Reset if closed via X or click outside
    refreshHintSendLabel();
}

function sendHint() {
    const text = hintTextarea.value.trim();
    state.narratorHint = text;
    
    const shouldSkip = autoSkipOnHintClose;
    closeHintPopup(); // This resets the flag, so we checked it first

    if (text) {
        deps.notify(t('hint.queued'), 'info', 2500);
    }
    
    if (shouldSkip && state.sessionId) {
        skipTurn();
    }
}

/* ── Routing and whisper controls ─────────────────────────────────────── */
export function populateForceSpeakerOptions() {
    if (!forceSpeakerSelect) return;
    const current = forceSpeakerSelect.value;
    forceSpeakerSelect.innerHTML = '<option value="" data-i18n="action.automatic"></option>';
    translateDocument(forceSpeakerSelect);
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
    narratorOpt.textContent = `🎭 ${t('input.narrator')}`;
    forceSpeakerSelect.appendChild(narratorOpt);
    if ([...forceSpeakerSelect.options].some((o) => o.value === current)) {
        forceSpeakerSelect.value = current;
    }
    populateWhisperOptions();
}

/* ── Whisper (audience) control — Task 30 ─────────────────────────────── */

function populateWhisperOptions() {
    if (!whisperPopup) return;
    const previous = new Set(getWhisperAudience());
    whisperPopup.innerHTML = '';
    const title = bindTranslation(document.createElement('div'), 'action.whisperHeading');
    title.className = 'whisper-popup-title';
    whisperPopup.appendChild(title);
    for (const cid of state.order) {
        if (cid === state.controlledId) continue;
        const ch = state.characters[cid];
        if (!ch) continue;
        const label = document.createElement('label');
        label.className = 'whisper-option';
        const box = document.createElement('input');
        box.type = 'checkbox';
        box.value = cid;
        box.checked = previous.has(cid);
        box.addEventListener('change', updateWhisperButton);
        label.appendChild(box);
        label.appendChild(document.createTextNode(` ${ch.mind.name}`));
        whisperPopup.appendChild(label);
    }
    updateWhisperButton();
}

function getWhisperAudience() {
    if (!whisperPopup) return [];
    return [...whisperPopup.querySelectorAll('input:checked')].map((box) => box.value);
}

function clearWhisperSelection() {
    if (!whisperPopup) return;
    for (const box of whisperPopup.querySelectorAll('input:checked')) box.checked = false;
    whisperPopup.hidden = true;
    updateWhisperButton();
}

function updateWhisperButton() {
    if (!whisperBtn) return;
    const count = getWhisperAudience().length;
    whisperBtn.classList.toggle('whisper-active', count > 0);
    whisperBtn.textContent = count > 0 ? `🤫${count}` : '🤫';
}

export function whisperNamesFor(ids) {
    return (ids || [])
        .map((cid) => state.characters[cid]?.mind?.name || cid)
        .join(', ');
}

if (whisperBtn) {
    whisperBtn.addEventListener('click', () => {
        whisperPopup.hidden = !whisperPopup.hidden;
    });
}


export async function skipTurn() {
    if (!state.sessionId) return;
    hideActionPopup();
    deps.setLoading(true, { multiStep: true });  // only a continuation runs several beats
    clearSuggestions();
    state.lastTurnFailed = false;
    updateActionPopup();

    if (isCompactLayout()) {
        inputArea.classList.add('collapsed');
        const activeEl = document.activeElement;
        if (activeEl === inputSpeech || activeEl === inputThought || activeEl === inputAction) {
            activeEl.blur();
        }
    }

    const ac = new AbortController();
    state.abortController = ac;

    try {
        let payload = {
            speech: '',
            thought: '',
            action: '',
            skip: true,
            narrator_hint: state.narratorHint || undefined,
            // Single source of truth is the select control; a dead
            // state.forceSpeaker read here silently dropped the force on
            // every skip turn (Task 28 regression).
            force_speaker: (forceSpeakerSelect ? forceSpeakerSelect.value : '') || undefined,
        };
        payload = await PluginRuntime.runHook('turn.input', payload, { state });
        let data = await api.turn(state.sessionId, payload, ac.signal);
        data = await PluginRuntime.runHook('turn.output', data, { state });

        const historyWasReconciled = await Compaction.reconcileAutomatic(data);
        if (state.debug) DebugDrawer.refreshDebugLog();
        if (!historyWasReconciled) {
            const beats = data.beats || [data];
            for (const beat of beats) {
                if (beat.narration) addMessage('Narrator', beat.narration, 'narration', { animate: true });
                for (const entry of (beat.character_responses || [])) {
                    addMessage(entry.character_id, { speech: entry.speech, thought: entry.thought }, 'response', { animate: true });
                }
            }
        }
        if (data.scene_update) {
            try {
                const gameState = await api.getState(state.sessionId);
                deps.renderScene(gameState.scene, Object.keys(data.scene_update));
            } catch { /* non-critical */ }
        }

        state.narratorHint = '';
        state.lastTurnFailed = false;
        state.canUndo = true;
        updateActionPopup();
    } catch (err) {
        if (err.name === 'AbortError') {
            deps.notify(t('turn.stopped'), 'info', 2500);
            state.lastTurnFailed = false;
        } else {
            state.lastTurnFailed = true;
            deps.notify(t('turn.failed', { error: err.message }), 'error', 6000);
        }
        updateActionPopup();
    } finally {
        state.abortController = null;
        deps.setLoading(false);
    }
}

export async function undoLastTurn() {
    if (!state.sessionId || !state.canUndo) return;
    hideActionPopup();
    deps.setLoading(true);
    try {
        const data = await api.undo(state.sessionId);
        if (!data.undone) { deps.notify(t('turn.noneToUndo'), 'info', 2500); deps.setLoading(false); return; }

        // Re-render from the authoritative history returned by the backend,
        // instead of guessing how many DOM bubbles the undone step had — a
        // step can produce fewer than 3 (e.g. no character response), and
        // removing a fixed count desyncs the DOM from the real state.
        if (data.state) {
            const gameState = await PluginRuntime.runHook('session.state', data.state, { state });
            renderHistory(gameState.history);
            deps.ingestState(gameState);
        }
        state.lastTurnFailed = false;
        state.canUndo = !!(data.state && data.state.history && data.state.history.length > 0);
        updateActionPopup();

        // Restore last player inputs so they can edit and resend
        if (state.lastInputs) {
            inputSpeech.value = state.lastInputs.speech || '';
            inputThought.value = state.lastInputs.thought || '';
            inputAction.value = state.lastInputs.action || '';
            if (forceSpeakerSelect) forceSpeakerSelect.value = state.lastInputs.forceSpeaker || '';
            state.narratorHint = state.lastInputs.narratorHint || '';
            if (!isCompactLayout()) inputSpeech.focus();
        }

        deps.notify(t('turn.undone'), 'success', 2000);
    } catch (err) {
        deps.notify(t('turn.undoError', { error: err.message }), 'error');
    } finally {
        deps.setLoading(false);
    }
}

export function retryTurn() {
    if (!state.lastInputs) return;
    hideActionPopup();
    // Restore inputs (they may have been cleared on error)
    inputSpeech.value = state.lastInputs.speech || '';
    inputThought.value = state.lastInputs.thought || '';
    inputAction.value = state.lastInputs.action || '';
    if (forceSpeakerSelect) forceSpeakerSelect.value = state.lastInputs.forceSpeaker || '';
    state.narratorHint = state.lastInputs.narratorHint || '';
    sendTurn(true);
}

export async function sendTurn(isRetry = false) {
    if (!state.sessionId) return;
    if (!isRetry && await SlashCommands.interceptSend()) return;
    const speech = inputSpeech.value.trim();
    const thought = inputThought.value.trim();
    const action = inputAction.value.trim();
    const forceSpeaker = forceSpeakerSelect ? forceSpeakerSelect.value : '';
    const whisperAudience = getWhisperAudience();
    if (!speech && !thought && !action && !state.narratorHint) {
        deps.notify(t('action.inputRequired'), 'info', 2500);
        return;
    }
    if (whisperAudience.length && !speech && !action) {
        deps.notify(t('action.whisperNeedsContent'), 'info', 3000);
        return;
    }

    // Save inputs for potential retry
    state.lastInputs = { speech, thought, action, forceSpeaker, narratorHint: state.narratorHint };

    if (isCompactLayout()) {
        inputArea.classList.add('collapsed');
        // Blur inputs to close the mobile keyboard
        const activeEl = document.activeElement;
        if (activeEl === inputSpeech || activeEl === inputThought || activeEl === inputAction) {
            activeEl.blur();
        }
    }

    // Echo the player's own input as a bubble (skip on retry to avoid duplicates)
    if (!isRetry) {
        state.lastEchoMessage = addMessage(
            'Player', buildPlayerEcho(speech, thought, action), 'response',
            { whisperNames: whisperAudience.length ? whisperNamesFor(whisperAudience) : '' }
        );
    }

    deps.setLoading(true);
    clearSuggestions();
    state.lastTurnFailed = false;
    updateActionPopup();

    // Create AbortController for stop button
    const ac = new AbortController();
    state.abortController = ac;

    try {
        let payload = {
            speech: speech || '',
            thought: thought || '',
            action: action || '',
            force_speaker: forceSpeaker || undefined,
            narrator_hint: state.narratorHint || undefined,
            audience: whisperAudience.length ? whisperAudience : undefined,
        };
        payload = await PluginRuntime.runHook('turn.input', payload, { state });
        let data = await api.turn(state.sessionId, payload, ac.signal);
        data = await PluginRuntime.runHook('turn.output', data, { state });

        const historyWasReconciled = await Compaction.reconcileAutomatic(data);
        if (!historyWasReconciled) {
            updatePlayerEcho(
                state.lastEchoMessage,
                data.effective_input,
                Array.isArray(data.transformed_fields) && data.transformed_fields.length > 0,
            );
        } else {
            state.lastEchoMessage = null;
        }

        if (String(data.effective_input?.speech || '').trim()) {
            state.playerHasSpoken = true;
            updateSpeechPlaceholder();
        }

        if (state.debug) DebugDrawer.refreshDebugLog();

        if (!historyWasReconciled) {
            const beats = data.beats || [data];
            for (const beat of beats) {
                if (beat.narration) addMessage('Narrator', beat.narration, 'narration', { animate: true });
                for (const entry of (beat.character_responses || [])) {
                    addMessage(entry.character_id, { speech: entry.speech, thought: entry.thought }, 'response', { animate: true });
                }
            }
        }

        if (data.scene_update) {
            try {
                const gameState = await api.getState(state.sessionId);
                deps.renderScene(gameState.scene, Object.keys(data.scene_update));
            } catch { /* scene refresh is non-critical */ }
        }

        inputSpeech.value = '';
        inputThought.value = '';
        inputAction.value = '';
        state.narratorHint = '';
        if (!isCompactLayout()) inputSpeech.focus();
        state.lastTurnFailed = false;
        state.canUndo = true;
        clearWhisperSelection();
        updateActionPopup();
    } catch (err) {
        try {
            let gameState = await api.getState(state.sessionId);
            gameState = await PluginRuntime.runHook('session.state', gameState, { state });
            deps.ingestState(gameState);
            renderHistory(gameState.history);
        } catch { /* best-effort reconciliation after an ambiguous turn failure */ }
        if (err.name === 'AbortError') {
            // User pressed stop — don't treat as failure, keep inputs
            deps.notify(t('turn.stopped'), 'info', 2500);
            state.lastTurnFailed = false;
        } else {
            state.lastTurnFailed = true;
            // Keep inputs in fields so user can edit and retry
            deps.notify(t('turn.failed', { error: err.message }), 'error', 6000);
        }
        updateActionPopup();
    } finally {
        state.abortController = null;
        deps.setLoading(false);
    }
}

function wireEvents() {
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
if (retryBannerBtn) retryBannerBtn.addEventListener('click', retryTurn);
if (actionSkipBtn) actionSkipBtn.addEventListener('click', skipTurn);
if (actionExpandMoreBtn && actionPopupSecondary) {
    actionExpandMoreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        actionPopupSecondary.classList.toggle('open');
        actionExpandMoreBtn.classList.toggle('active');
    });
}
if (actionSuggestBtn) actionSuggestBtn.addEventListener('click', suggestForMe);
if (actionHintBtn) actionHintBtn.addEventListener('click', openHintPopup);

// Hint popup events
if (hintCloseBtn) hintCloseBtn.addEventListener('click', closeHintPopup);
if (hintSendBtn) hintSendBtn.addEventListener('click', sendHint);
if (hintOverlay) hintOverlay.addEventListener('click', (e) => {
    if (e.target === hintOverlay) closeHintPopup();
});

// Stop button — abort current turn
if (stopBtn) stopBtn.addEventListener('click', () => {
    if (state.abortController) state.abortController.abort();
});

inputAction.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTurn(); }
});
inputSpeech.addEventListener('keydown', (e) => {
    if (SlashCommands.handleKeydown(e)) return;
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inputThought.focus(); }
});
inputThought.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inputAction.focus(); }
});

if (inputExpandBtn) {
    inputExpandBtn.addEventListener('click', () => {
        expandMobileInput();
    });
}

let touchStartX = 0;
let touchStartY = 0;
let isSwipingX = false;
let isSwipingY = false;
const inputFieldsContainer = document.getElementById('input-fields-container');

inputArea.addEventListener('touchstart', (e) => {
    if (!isCompactLayout()) return;
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    isSwipingX = false;
    isSwipingY = false;
    inputFieldsContainer.style.transition = 'none';
    // Suggestions and the retry banner live inside the bar — drag them along.
    optionsPanel.style.transition = 'none';
    if (retryBanner) retryBanner.style.transition = 'none';
    if (inputExpandBtn) {
        inputExpandBtn.style.transition = 'none';
        const labelEl = inputExpandBtn.querySelector('.input-expand-label');
        const actionLeftEl = inputExpandBtn.querySelector('.input-expand-action-left');
        const actionRightEl = inputExpandBtn.querySelector('.input-expand-action-right');
        if (labelEl) labelEl.style.transition = 'none';
        if (actionLeftEl) actionLeftEl.style.transition = 'none';
        if (actionRightEl) actionRightEl.style.transition = 'none';
    }
}, { passive: true });

inputArea.addEventListener('touchmove', (e) => {
    if (!isCompactLayout() || !touchStartX || !touchStartY) return;
    const diffX = e.touches[0].clientX - touchStartX;
    const diffY = e.touches[0].clientY - touchStartY;

    if (!isSwipingX && !isSwipingY) {
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 10) {
            isSwipingX = true;
        } else if (Math.abs(diffY) > 10) {
            isSwipingY = true;
        }
    }

    if (isSwipingX) {
        e.preventDefault();
        const threshold = window.innerWidth * 0.5;
        const dampen = 0.4;
        const moveX = diffX * dampen;
        
        inputFieldsContainer.style.transform = `translateX(${moveX}px)`;
        optionsPanel.style.transform = `translateX(${moveX}px)`;
        if (retryBanner) retryBanner.style.transform = `translateX(${moveX}px)`;
        if (inputExpandBtn) {
            inputExpandBtn.style.transform = `translateX(${moveX}px)`;
            
            // Crossfade label and action based on swipe distance
            const progress = Math.min(1, Math.abs(diffX) / (threshold * 0.6));
            const labelEl = inputExpandBtn.querySelector('.input-expand-label');
            const actionLeftEl = inputExpandBtn.querySelector('.input-expand-action-left');
            const actionRightEl = inputExpandBtn.querySelector('.input-expand-action-right');
            
            if (labelEl) {
                labelEl.style.opacity = 1 - progress;
            }
            if (diffX > 0) {
                // Swiping Right -> Undo
                if (actionRightEl) {
                    actionRightEl.style.opacity = progress;
                    actionRightEl.style.transform = `translateY(-50%) translateX(${15 * (1 - progress)}px)`;
                }
                if (actionLeftEl) {
                    actionLeftEl.style.opacity = 0;
                }
            } else {
                // Swiping Left -> Suggestion/Hint
                if (actionLeftEl) {
                    actionLeftEl.style.opacity = progress;
                    actionLeftEl.style.transform = `translateY(-50%) translateX(${-15 * (1 - progress)}px)`;
                }
                if (actionRightEl) {
                    actionRightEl.style.opacity = 0;
                }
            }
        }

        // Liquid gradient effect on the stationary parent
        const percent = Math.min(100, (Math.abs(diffX) / threshold) * 100);
        if (diffX > 0) {
            // Swiping Right -> Undo (Blue)
            inputArea.style.background = `linear-gradient(to right, rgba(0, 150, 255, 0.4) ${percent}%, transparent ${percent + 20}%)`;
        } else {
            // Swiping Left -> Suggestion (Orange)
            inputArea.style.background = `linear-gradient(to left, rgba(255, 150, 0, 0.4) ${percent}%, transparent ${percent + 20}%)`;
        }
    }
}, { passive: false });

inputArea.addEventListener('touchend', (e) => {
    if (!isCompactLayout() || !touchStartX || !touchStartY) return;
    const diffX = e.changedTouches[0].clientX - touchStartX;
    const diffY = e.changedTouches[0].clientY - touchStartY;

    inputFieldsContainer.style.transition = 'transform 0.3s ease';
    optionsPanel.style.transition = 'transform 0.3s ease';
    if (retryBanner) retryBanner.style.transition = 'transform 0.3s ease';
    if (inputExpandBtn) {
        inputExpandBtn.style.transition = 'transform 0.3s ease';
        const labelEl = inputExpandBtn.querySelector('.input-expand-label');
        const actionLeftEl = inputExpandBtn.querySelector('.input-expand-action-left');
        const actionRightEl = inputExpandBtn.querySelector('.input-expand-action-right');
        if (labelEl) {
            labelEl.style.transition = 'opacity 0.3s ease';
            labelEl.style.opacity = '';
        }
        if (actionLeftEl) {
            actionLeftEl.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            actionLeftEl.style.opacity = '';
            actionLeftEl.style.transform = '';
        }
        if (actionRightEl) {
            actionRightEl.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            actionRightEl.style.opacity = '';
            actionRightEl.style.transform = '';
        }
    }
    inputArea.style.transition = 'background 0.3s ease';
    
    inputFieldsContainer.style.transform = '';
    optionsPanel.style.transform = '';
    if (retryBanner) retryBanner.style.transform = '';
    if (inputExpandBtn) inputExpandBtn.style.transform = '';
    inputArea.style.background = '';

    setTimeout(() => {
        inputFieldsContainer.style.transition = '';
        optionsPanel.style.transition = '';
        if (retryBanner) retryBanner.style.transition = '';
        if (inputExpandBtn) {
            inputExpandBtn.style.transition = '';
            const labelEl = inputExpandBtn.querySelector('.input-expand-label');
            const actionLeftEl = inputExpandBtn.querySelector('.input-expand-action-left');
            const actionRightEl = inputExpandBtn.querySelector('.input-expand-action-right');
            if (labelEl) labelEl.style.transition = '';
            if (actionLeftEl) actionLeftEl.style.transition = '';
            if (actionRightEl) actionRightEl.style.transition = '';
        }
        inputArea.style.transition = '';
    }, 300);

    if (isSwipingX) {
        const threshold = window.innerWidth * 0.5;
        if (diffX > threshold) {
            if (state.canUndo) undoLastTurn();
            else deps.notify('Nothing to undo', 'info', 2000);
        } else if (diffX < -threshold) {
            if (state.sessionId) {
                autoSkipOnHintClose = true;
                openHintPopup();  // labels its button as a continuation
            }
        }
    } else if (isSwipingY || (!isSwipingX && Math.abs(diffY) > 30)) {
        if (diffY > 30) {
            const activeEl = document.activeElement;
            if (activeEl === inputSpeech || activeEl === inputThought || activeEl === inputAction) {
                activeEl.blur();
            }
            inputArea.classList.add('collapsed');
        } else if (diffY < -30) {
            expandMobileInput({ focus: false });
        }
    }
    
    touchStartX = 0;
    touchStartY = 0;
    isSwipingX = false;
    isSwipingY = false;
});

}
