/* ══════════════════════════════════════════════════════════════════════
   compaction-ui.js — the compaction button, its streamed progress bar, and
   the checkpoint restore.

   Compaction is the only long operation the player can watch: the backend
   streams stages over SSE and the bar reflects real completed units, never
   an estimated clock. Checkpoints are undone in LIFO order — turns played
   after a checkpoint survive, while divergent plugin-owned state needs an
   explicit resolver.
   ══════════════════════════════════════════════════════════════════════ */

import { el } from './dom.js';
import { api } from './api.js';
import { t } from './i18n.js';

const actionCompactBtn = el('action-compact-btn');
const actionRestoreCompactionBtn = el('action-restore-compaction-btn');
const compactProgress = el('compact-progress');
const compactProgressStatus = el('compact-progress-status');

// Stages that carry no unit count still have to move the bar somewhere
// truthful; summarizing owns the 8-84% band because it is the only stage
// that reports real progress.
const FIXED_STAGE_PERCENT = {
    checking: 3,
    before_commit: 88,
    checkpointing: 93,
    committing: 97,
    completed: 100,
    skipped: 3,
};
const SUMMARIZING_FLOOR = 8;
const SUMMARIZING_BAND = 76;
const BAR_RESET_MS = 400;

let state = null;
let deps = null;

/**
 * @param {object} options
 * @param {object} options.state the shared app state (sessionId, compactionAbortController)
 * @param {() => Promise<void>} options.reloadView re-read the session and redraw
 * @param {(on: boolean) => void} options.setTurnControlsDisabled
 * @param {(on: boolean) => void} options.setLoading
 * @param {() => void} options.hideActionPopup
 * @param {(message: string, type?: string, ms?: number) => void} options.notify
 */
export function init(options) {
    state = options.state;
    deps = options;

    actionCompactBtn.addEventListener('click', compactSession);
    actionRestoreCompactionBtn.addEventListener('click', restoreCompaction);
}

/* The action popup decides what the player can even see; compaction owns
   whether its own two buttons belong there. */
export function setAvailable(hasSession, hasCheckpoint) {
    actionCompactBtn.style.display = hasSession ? '' : 'none';
    actionRestoreCompactionBtn.style.display = hasSession && hasCheckpoint ? '' : 'none';
}

export function progressPercent(event) {
    if (event.stage === 'failed') {
        return Number.parseFloat(compactProgress.style.width) || 0;
    }
    if (!['summarizing', 'model_completed'].includes(event.stage)) {
        return FIXED_STAGE_PERCENT[event.stage] ?? 0;
    }
    if (!event.total_units) return SUMMARIZING_FLOOR;
    return SUMMARIZING_FLOOR + (event.completed_units / event.total_units) * SUMMARIZING_BAND;
}

function renderProgress(event) {
    const percent = Math.max(0, Math.min(100, progressPercent(event)));
    compactProgress.style.width = `${percent}%`;
    compactProgressStatus.textContent = t(`compaction.stage.${event.stage}`, {
        completed: event.completed_units ?? 0,
        total: event.total_units ?? 0,
    });
}

function setBusy(on) {
    actionCompactBtn.classList.toggle('busy', on);
    actionRestoreCompactionBtn.disabled = on;
    deps.setTurnControlsDisabled(on);
}

export async function compactSession() {
    if (!state.sessionId) return;
    deps.hideActionPopup();

    setBusy(true);
    compactProgress.style.width = '0%';
    const ac = new AbortController();
    state.compactionAbortController = ac;

    try {
        const data = await api.compact(state.sessionId, renderProgress, ac.signal);
        if (data.compacted) {
            deps.notify(
                t('compaction.done', { evicted: data.evicted_records, kept: data.kept_records }),
                'success',
                3500,
            );
            await deps.reloadView();
        } else {
            deps.notify(data.reason || t('compaction.none'), 'info', 2500);
        }
    } catch (err) {
        if (err.name !== 'AbortError') {
            deps.notify(t('compaction.error', { error: err.message }), 'error');
        }
    } finally {
        state.compactionAbortController = null;
        setTimeout(() => {
            setBusy(false);
            compactProgress.style.width = '0%';
            compactProgressStatus.textContent = '';
        }, BAR_RESET_MS);
    }
}

export async function restoreCompaction() {
    if (!state.sessionId) return;
    deps.hideActionPopup();
    if (!confirm(t('compaction.restoreConfirm'))) return;

    deps.setLoading(true);
    try {
        const data = await api.restoreCompaction(state.sessionId);
        if (data.restored) {
            deps.notify(
                t('compaction.restored', {
                    count: data.restored_records,
                    depth: data.remaining_compaction_depth,
                }),
                'success',
                3500,
            );
            await deps.reloadView();
        } else {
            deps.notify(data.reason || t('compaction.restoreUnavailable'), 'info', 3500);
        }
    } catch (err) {
        deps.notify(t('compaction.restoreError', { error: err.message }), 'error');
    } finally {
        deps.setLoading(false);
    }
}

/* The backend may compact on its own at the end of a turn; the view only has
   to catch up with what already happened. Returns true when history changed. */
export async function reconcileAutomatic(data) {
    const result = data?.automatic_compaction;
    if (!result) return false;
    if (result.compacted) {
        await deps.reloadView();
        deps.notify(t('compaction.automaticDone', { count: result.evicted_records }), 'info', 3500);
        return true;
    }
    if (result.status === 'blocked_by_retention_window') {
        deps.notify(t('compaction.automaticBlocked'), 'info', 3000);
    } else if (result.status === 'failed') {
        deps.notify(t('compaction.automaticFailed'), 'error', 4500);
    }
    return false;
}
