/* ══════════════════════════════════════════════════════════════════════
   debug-drawer.js — the raw session log panel and the prompt preview.

   Diagnostics only: nothing here participates in a turn. It reads
   /session/{id}/debug_log, which is the same material tools/replay_session.py
   and tools/analyze_memory_run.py consume.
   ══════════════════════════════════════════════════════════════════════ */

import { api } from './api.js';
import { bindTranslation, t, translateDocument } from './i18n.js';

const debugToggle = document.getElementById('debug-toggle');
const debugDrawer = document.getElementById('debug-drawer');
const debugContent = document.getElementById('debug-content');
const debugCloseBtn = document.getElementById('debug-close-btn');
const debugRefreshBtn = document.getElementById('debug-refresh-btn');
const previewBtn = document.getElementById('preview-prompt-btn');

let deps = null;
let lastDebugEntries = null;

/**
 * @param {object} options
 * @param {() => string|null} options.getSessionId
 * @param {(on: boolean) => void} options.onToggle told when the drawer opens/closes
 * @param {(message: string, type?: string, ms?: number) => void} options.notify
 */
export function init(options) {
    deps = options;
    debugToggle.addEventListener('change', () => setDebug(debugToggle.checked));
    debugCloseBtn.addEventListener('click', () => setDebug(false));
    debugRefreshBtn.addEventListener('click', refreshDebugLog);
    previewBtn.addEventListener('click', previewPrompt);
}

/** Clear the panel back to its instructions (a new or reset session). */
export function reset() {
    lastDebugEntries = null;
    debugContent.innerHTML = '<p class="debug-placeholder" data-i18n="debug.shortInstructions"></p>';
    translateDocument(debugContent);
}

/** Re-render the current entries, e.g. after the interface language changes. */
export function retranslate() {
    if (lastDebugEntries) renderRawLog(lastDebugEntries);
}

/** Open or close the drawer; opening always refreshes what it shows. */
export function setDebug(on) {
    debugToggle.checked = on;
    debugDrawer.classList.toggle('active', on);
    deps.onToggle(on);
    if (on) refreshDebugLog();
}

export function messagesToText(messages) {
    return (messages || [])
        .map((m) => `[${m.role.toUpperCase()}]\n${m.content}`)
        .join('\n\n');
}

function makeCopyBtn(getText) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    bindTranslation(btn, 'debug.copy');
    btn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(getText());
            btn.textContent = `✓ ${t('debug.copied')}`;
            btn.classList.add('copied');
            setTimeout(() => { bindTranslation(btn, 'debug.copy'); btn.classList.remove('copied'); }, 1500);
        } catch {
            deps.notify(t('debug.copyError'), 'error');
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

/* Raw sequential log of all LLM calls for the session. */
function renderRawLog(entries) {
    lastDebugEntries = entries;
    debugContent.innerHTML = '';
    if (!entries || entries.length === 0) {
        debugContent.innerHTML =
            '<p class="debug-placeholder" data-i18n="debug.noCalls"></p>';
        translateDocument(debugContent);
        return;
    }
    entries.forEach((e) => {
        try {
            const metrics = e.duration_ms != null
                ? t('debug.logMetrics', { attempt: e.attempt_number || 1, duration: e.duration_ms })
                : '';
            const title = t('debug.logTitle', {
                turn: e.turn_number,
                agent: e.agent,
                error: e.error ? t('debug.logErrorSuffix') : '',
                metrics,
            });
            const messages = (e.request && e.request.messages) || [];
            let raw;
            if (e.agent === 'turn_input') {
                raw = `[TURN INPUT]\n${JSON.stringify({
                    input: e.input,
                }, null, 2)}`;
            } else if (e.agent === 'turn_input_effective') {
                raw = `[EFFECTIVE TURN INPUT]\n${JSON.stringify({
                    input: e.input,
                    effective_force_speaker: e.effective_force_speaker,
                    transformed_fields: e.transformed_fields,
                }, null, 2)}`;
            } else if (e.error) {
                raw = `[${e.error_type || 'ERROR'}] ${e.error}\n${e.error_repr || ''}`.trim();
            } else if (e.agent === 'compact' || e.agent === 'restore' || e.agent === 'undo') {
                raw = `[${e.agent.toUpperCase()}]\n${JSON.stringify(e.details || {}, null, 2)}`;
            } else {
                raw = typeof e.response === 'string' ? e.response : JSON.stringify(e.response, null, 2);
            }
            debugContent.appendChild(renderDebugBlock(title, messages, raw));
        } catch (err) {
            debugContent.appendChild(renderDebugBlock('Error rendering entry', [], String(err.stack || err)));
        }
    });
}

export async function refreshDebugLog() {
    if (!deps.getSessionId()) return;
    try {
        const entries = await api.getDebugLog(deps.getSessionId());
        renderRawLog(entries);
    } catch (err) {
        deps.notify(t('debug.logError', { error: err.message }), 'error');
    }
}

export async function previewPrompt() {
    if (!deps.getSessionId()) { deps.notify(t('debug.startFirst'), 'error'); return; }
    try {
        const entries = await api.getDebugLog(deps.getSessionId());
        debugContent.innerHTML = '';
        lastDebugEntries = entries;
        // Find the last narrator call from the JSONL log
        const lastNarrator = [...(entries || [])].reverse().find(
            (e) => e.agent === 'narrator' && e.request && e.request.messages
        );
        if (lastNarrator) {
            const messages = lastNarrator.request.messages;
            const raw = lastNarrator.response;
            const title = t('debug.logTitle', {
                turn: lastNarrator.turn_number,
                agent: 'narrator',
                error: '',
                metrics: lastNarrator.duration_ms != null
                    ? t('debug.logMetrics', { attempt: lastNarrator.attempt_number || 1, duration: lastNarrator.duration_ms })
                    : '',
            });
            debugContent.appendChild(renderDebugBlock(title, messages, raw));
            deps.notify(t('debug.previewReady'), 'success', 2500);
        } else {
            debugContent.innerHTML = '<p class="debug-placeholder" data-i18n="debug.noCalls"></p>';
            translateDocument(debugContent);
            deps.notify(t('debug.previewError', { error: 'No narrator call found' }), 'info', 2500);
        }
    } catch (err) {
        deps.notify(t('debug.previewError', { error: err.message }), 'error');
    }
}
