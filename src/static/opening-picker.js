/* ══════════════════════════════════════════════════════════════════════
   opening-picker.js — the three opening suggestions offered on an empty
   session, as a carousel with keyboard and swipe navigation.

   Generation is ephemeral: nothing is persisted until the player confirms,
   and confirming reuses the existing narrator-hint + skip path instead of a
   second turn implementation.
   ══════════════════════════════════════════════════════════════════════ */

import { api } from './api.js';
import { t } from './i18n.js';

const openingStart = document.getElementById('opening-start');
const openingGenerateBtn = document.getElementById('opening-generate-btn');
const openingCarousel = document.getElementById('opening-carousel');
const openingCard = document.getElementById('opening-card');
const openingCardText = document.getElementById('opening-card-text');
const openingPrevBtn = document.getElementById('opening-prev-btn');
const openingNextBtn = document.getElementById('opening-next-btn');
const openingDots = document.getElementById('opening-dots');
const openingCounter = document.getElementById('opening-counter');
const openingStartBtn = document.getElementById('opening-start-btn');
const openingRegenerateBtn = document.getElementById('opening-regenerate-btn');

const SWIPE_THRESHOLD_PX = 45;

let state = null;
let deps = null;
let suggestions = [];
let index = 0;
let busy = false;
let pointerStartX = null;

/**
 * @param {object} options
 * @param {object} options.state the shared app state (sessionId, narratorHint)
 * @param {(on: boolean) => void} options.setLoading
 * @param {(message: string, type?: string, ms?: number) => void} options.notify
 * @param {() => Promise<void>} options.skipTurn confirms an opening as a turn
 */
export function init(options) {
    state = options.state;
    deps = options;

    openingGenerateBtn.addEventListener('click', generate);
    openingRegenerateBtn.addEventListener('click', generate);
    openingStartBtn.addEventListener('click', startWithOpening);
    openingPrevBtn.addEventListener('click', () => show(index - 1));
    openingNextBtn.addEventListener('click', () => show(index + 1));
    openingCarousel.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            show(index - 1);
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            show(index + 1);
        }
    });
    openingCard.addEventListener('pointerdown', (e) => { pointerStartX = e.clientX; });
    openingCard.addEventListener('pointerup', (e) => {
        if (pointerStartX == null) return;
        const distance = e.clientX - pointerStartX;
        pointerStartX = null;
        if (Math.abs(distance) < SWIPE_THRESHOLD_PX) return;
        show(index + (distance < 0 ? 1 : -1));
    });
    openingCard.addEventListener('pointercancel', () => { pointerStartX = null; });
}

/** Show or hide the whole picker with the session-ready empty state. */
export function setVisible(visible) {
    openingStart.hidden = !visible;
    if (visible) render();
    else reset();
}

export function render(direction = 0) {
    const hasSuggestions = suggestions.length === 3;
    openingGenerateBtn.hidden = hasSuggestions;
    openingGenerateBtn.disabled = busy;
    openingCarousel.hidden = !hasSuggestions;
    if (!hasSuggestions) return;

    openingCardText.textContent = suggestions[index];
    openingCounter.textContent = t('opening.counter', {
        current: index + 1,
        total: suggestions.length,
    });
    openingPrevBtn.disabled = busy || index === 0;
    openingNextBtn.disabled = busy || index === suggestions.length - 1;
    openingStartBtn.disabled = busy;
    openingRegenerateBtn.disabled = busy;

    openingDots.replaceChildren(...suggestions.map((_, position) => {
        const dot = document.createElement('button');
        dot.type = 'button';
        dot.className = `opening-dot${position === index ? ' active' : ''}`;
        dot.disabled = busy;
        dot.setAttribute('aria-label', t('opening.option', { number: position + 1 }));
        dot.setAttribute('aria-current', position === index ? 'true' : 'false');
        dot.addEventListener('click', () => show(position));
        return dot;
    }));

    openingCard.classList.remove('from-left', 'from-right');
    if (direction) {
        void openingCard.offsetWidth;
        openingCard.classList.add(direction > 0 ? 'from-right' : 'from-left');
    }
}

export function reset() {
    suggestions = [];
    index = 0;
    busy = false;
    pointerStartX = null;
    render();
}

function show(target) {
    if (busy || target < 0 || target >= suggestions.length || target === index) return;
    const direction = target > index ? 1 : -1;
    index = target;
    render(direction);
}

async function generate() {
    if (!state.sessionId || busy) return;
    busy = true;
    render();
    deps.setLoading(true);
    try {
        const data = await api.suggestOpenings(state.sessionId);
        if (!Array.isArray(data.suggestions) || data.suggestions.length !== 3) {
            throw new Error('Opening suggestions response is invalid');
        }
        suggestions = data.suggestions.map((item) => String(item));
        index = 0;
        deps.notify(t('opening.ready'), 'success', 2500);
    } catch (err) {
        deps.notify(t('opening.error', { error: err.message }), 'error');
    } finally {
        busy = false;
        deps.setLoading(false);
        render(1);
    }
}

async function startWithOpening() {
    const opening = suggestions[index];
    if (!opening || busy || !state.sessionId) return;
    busy = true;
    render();
    state.narratorHint = opening;
    await deps.skipTurn();
    if (state.lastTurnFailed) {
        busy = false;
        render();
    } else {
        reset();
    }
}
