/* ══════════════════════════════════════════════════════════════════════
   sessions-modal.js — the saved-adventure list: open, fork, delete, and
   the incompatible-session gate.

   Cards are built with createElement/textContent rather than innerHTML, so
   untrusted fields (character names, scene text) can never be interpreted
   as markup and there is no manual escaping to remember at each
   interpolation.
   ══════════════════════════════════════════════════════════════════════ */

import { api } from './api.js';
import { bindTranslation, t } from './i18n.js';

const sessionsOverlay = document.getElementById('sessions-overlay');
const sessionList = document.getElementById('session-list');
const sessionsCloseBtn = document.getElementById('sessions-close-btn');
const sessionsNewBtn = document.getElementById('sessions-new-btn');
const sessionsBtn = document.getElementById('sessions-btn');

const LONG_PRESS_MS = 600;

let state = null;
let deps = null;
let lastSessionList = null;

/**
 * @param {object} options
 * @param {object} options.state the shared app state (sessionId, compactionDepth)
 * @param {(sessionId: string) => void} options.loadSession
 * @param {() => void} options.onNewSession asked for a blank adventure
 * @param {() => void} options.onCurrentSessionDeleted reset the view
 * @param {(message: string, type?: string, ms?: number) => void} options.notify
 */
export function init(options) {
    state = options.state;
    deps = options;

    sessionsBtn.addEventListener('click', open);
    sessionsCloseBtn.addEventListener('click', close);
    sessionsNewBtn.addEventListener('click', () => {
        close();
        deps.onNewSession();
    });
    sessionsOverlay.addEventListener('click', (e) => {
        if (e.target === sessionsOverlay) close();
    });
}

export async function open() {
    sessionsOverlay.classList.add('active');
    try {
        render(await api.listSessions());
    } catch (err) {
        deps.notify(t('sessions.listError', { error: err.message }), 'error');
    }
}

export function close() {
    sessionsOverlay.classList.remove('active');
}

/** Re-render the last fetched list, e.g. after the interface language changes. */
export function retranslate() {
    if (lastSessionList) render(lastSessionList);
}

export function timeAgo(iso) {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return t('sessions.now');
    const min = Math.floor(sec / 60);
    if (min < 60) return t('sessions.minutesAgo', { count: min });
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return t('sessions.hoursAgo', { count: hrs });
    const days = Math.floor(hrs / 24);
    if (days < 30) return t('sessions.daysAgo', { count: days });
    return iso.slice(0, 10);
}

export function render(sessions) {
    lastSessionList = sessions;
    sessionList.innerHTML = '';
    if (!sessions || sessions.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'session-empty';
        bindTranslation(empty, 'sessions.emptyCreate');
        sessionList.appendChild(empty);
        return;
    }
    sessions.forEach((s) => {
        const card = document.createElement('div');
        card.className = 'session-card';
        const incompatible = s.compatible === false;
        if (incompatible) card.classList.add('incompatible');
        if (s.session_id === state.sessionId) card.classList.add('active');

        const sceneText = s.scene_location || '';
        const turnText = t('sessions.turns', { count: s.turn_count || 0 });
        const dateText = timeAgo(s.created_at);
        const extra = [turnText, dateText].filter(Boolean).join(' · ');

        const info = document.createElement('div');
        info.className = 'session-info';

        const tagsWrap = document.createElement('div');
        tagsWrap.className = 'session-char-tags';
        (s.characters || []).filter((c) => c.name).forEach((c) => {
            const tag = document.createElement('span');
            tag.className = 'session-char-tag';
            tag.textContent = c.name;
            tagsWrap.appendChild(tag);
        });
        info.appendChild(tagsWrap);

        const meta = document.createElement('div');
        meta.className = 'session-meta';
        const sceneMetaItem = document.createElement('span');
        sceneMetaItem.className = 'session-meta-item';
        sceneMetaItem.textContent = sceneText;
        meta.appendChild(sceneMetaItem);
        if (extra) {
            const extraItem = document.createElement('span');
            extraItem.className = 'session-meta-item';
            extraItem.textContent = extra;
            meta.appendChild(extraItem);
        }
        if (incompatible) {
            const lock = document.createElement('div');
            lock.className = 'session-incompatible-badge';
            const symbol = document.createElement('span');
            symbol.textContent = '⛔';
            symbol.setAttribute('aria-hidden', 'true');
            const label = document.createElement('span');
            bindTranslation(label, 'sessions.incompatible');
            bindTranslation(card, 'sessions.incompatible', {}, 'title');
            lock.append(symbol, label);
            meta.appendChild(lock);
        }
        info.appendChild(meta);
        card.appendChild(info);

        const sceneDiv = document.createElement('div');
        sceneDiv.className = 'session-scene';
        sceneDiv.textContent = sceneText;
        card.appendChild(sceneDiv);

        const actions = document.createElement('div');
        actions.className = 'session-actions';
        if (!incompatible) {
            const forkBtn = document.createElement('button');
            forkBtn.className = 'session-action-btn';
            forkBtn.dataset.action = 'fork';
            bindTranslation(forkBtn, 'sessions.fork', {}, 'title');
            bindTranslation(forkBtn, 'sessions.fork', {}, 'ariaLabel');
            forkBtn.textContent = '🔀';
            actions.append(forkBtn);
            forkBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                card.classList.remove('show-actions');
                try {
                    const result = await api.forkSession(s.session_id);
                    deps.notify(t('sessions.forked', { id: result.session_id }), 'success', 3000);
                    render(await api.listSessions());
                } catch (err) {
                    deps.notify(t('sessions.forkError', { error: err.message }), 'error');
                }
            });
        }
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'session-action-btn danger';
        deleteBtn.dataset.action = 'delete';
        bindTranslation(deleteBtn, 'common.delete', {}, 'title');
        bindTranslation(deleteBtn, 'common.delete', {}, 'ariaLabel');
        deleteBtn.textContent = '🗑️';
        actions.append(deleteBtn);
        card.appendChild(actions);

        // Click to load; incompatible sessions can never be opened again.
        card.addEventListener('click', (e) => {
            if (e.target.closest('.session-actions')) return;
            if (incompatible) {
                deps.notify(t('sessions.incompatibleToast', { found: s.schema_version }), 'error');
                return;
            }
            deps.loadSession(s.session_id);
        });

        // Long-press for mobile actions
        let longTimer = null;
        card.addEventListener('pointerdown', () => {
            longTimer = setTimeout(() => card.classList.add('show-actions'), LONG_PRESS_MS);
        });
        const clearLongTimer = () => { clearTimeout(longTimer); longTimer = null; };
        card.addEventListener('pointerup', clearLongTimer);
        card.addEventListener('pointerleave', clearLongTimer);
        card.addEventListener('pointercancel', clearLongTimer);
        card.addEventListener('contextmenu', (e) => { e.preventDefault(); card.classList.toggle('show-actions'); });

        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            card.classList.remove('show-actions');
            if (!confirm(t('sessions.deleteConfirm', { id: s.session_id }))) return;
            try {
                await api.deleteSession(s.session_id);
                card.remove();
                deps.notify(t('sessions.deleted'), 'info', 2500);
                if (s.session_id === state.sessionId) deps.onCurrentSessionDeleted();
            } catch (err) {
                deps.notify(t('sessions.deleteError', { error: err.message }), 'error');
            }
        });

        sessionList.appendChild(card);
    });
}
