/* ══════════════════════════════════════════════════════════════════════
   transcript.js — the chat log: who is speaking, how a turn becomes
   bubbles, and the typewriter reveal.

   Everything here is render. It never calls the API and never decides what
   a turn does; app.js hands it records and it draws them.
   ══════════════════════════════════════════════════════════════════════ */

import { bindTranslation, t } from './i18n.js';

const chatLog = document.getElementById('chat-log');
const emptyState = document.getElementById('empty-state');

const CHAR_COLORS = ['#6c9cff', '#b07cff', '#40e0a0', '#ffb454', '#ff7ca8', '#4fd6e0'];
const TYPE_MS_PER_CHAR = 6;
const TYPE_MIN_MS = 220;
const TYPE_MAX_MS = 1400;

let state = null;
let deps = null;

/**
 * @param {object} options
 * @param {object} options.state the shared app state (characters, order, avatarUrls)
 * @param {() => boolean} options.isScrollAnchored true while the log should stay pinned short
 * @param {() => void} options.resetOpeningSuggestions
 * @param {(sessionReady: boolean) => void} options.showEmptyState
 * @param {() => void} options.updateSpeechPlaceholder
 * @param {(ids: string[]) => string} options.whisperNamesFor
 */
export function init(options) {
    state = options.state;
    deps = options;
}

export function scrollToBottom(forceBottom = false) {
    if (!forceBottom && deps.isScrollAnchored()) {
        chatLog.scrollTo({ top: chatLog.scrollHeight - chatLog.clientHeight - 15, behavior: 'auto' });
    } else {
        chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: 'smooth' });
    }
}

export function controlledName() {
    const c = state.characters[state.controlledId];
    return (c && c.mind && c.mind.name) || t('input.you');
}

export function colorFor(cid) {
    const idx = state.order.indexOf(cid);
    return CHAR_COLORS[(idx < 0 ? 0 : idx) % CHAR_COLORS.length];
}

/* Resolve display info for any speaker id — fully dynamic, no hardcoding. */
export function speakerInfo(speaker) {
    if (speaker === 'Narrator') {
        return { label: t('input.narrator'), color: null, initial: '🎭', cls: 'msg-narrator' };
    }
    if (speaker === 'Player') {
        const cid = state.controlledId;
        return {
            label: controlledName(),
            color: colorFor(cid),
            initial: controlledName().charAt(0).toUpperCase(),
            cls: 'msg-player',
            avatar: state.avatarUrls[cid] || '',
        };
    }
    const ch = state.characters[speaker];
    if (ch) {
        return {
            label: ch.mind.name,
            color: colorFor(speaker),
            initial: ch.mind.name.charAt(0).toUpperCase(),
            cls: 'msg-npc',
            avatar: state.avatarUrls[speaker] || '',
        };
    }
    return { label: speaker, color: null, initial: '💬', cls: 'msg-npc' };
}

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/* Reveals `units` (an array of {node, text}, nodes already in the DOM but
   empty) progressively over a duration proportional to the total text
   length. Clicking `msg` while revealing skips straight to the full text. */
export function revealTypewriter(msg, units) {
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

export function messageSegments(content, contentType) {
    if (content && typeof content === 'object') {
        return [
            content.thought ? { type: 'thought', text: content.thought } : null,
            content.speech ? { type: 'speech', text: content.speech } : null,
            content.action ? { type: 'action', text: `🎬 ${content.action}` } : null,
        ].filter(Boolean);
    }
    if (contentType === 'thought') return [{ type: 'thought', text: content }];

    return [{ type: contentType, text: content }];
}

export function addMessage(
    speaker, content, contentType,
    { animate = false, transformed = false, whisperNames = '' } = {}
) {
    const info = speakerInfo(speaker);

    const msg = document.createElement('div');
    msg.className = `msg ${info.cls}`;

    const header = document.createElement('div');
    header.className = 'msg-header';
    if (info.color) header.style.color = info.color;

    if (info.cls !== 'msg-narrator') {
        const avatar = document.createElement('span');
        avatar.className = 'msg-avatar';
        if (info.avatar) {
            const image = document.createElement('img');
            image.src = info.avatar;
            image.alt = '';
            avatar.appendChild(image);
        } else {
            avatar.textContent = info.initial;
        }
        avatar.style.background = info.color
            ? `${info.color}33` : 'var(--surface-hi)';
        if (info.color) avatar.style.color = info.color;
        header.appendChild(avatar);
    }
    if (speaker === 'Narrator') {
        header.appendChild(bindTranslation(document.createElement('span'), 'input.narrator'));
    } else {
        header.appendChild(document.createTextNode(info.label));
    }
    msg.appendChild(header);

    if (transformed) {
        const badge = bindTranslation(document.createElement('span'), 'input.adjusted');
        badge.className = 'msg-transform-badge';
        header.appendChild(badge);
        msg.classList.add('msg-transformed');
    }

    if (whisperNames) {
        const badge = document.createElement('span');
        badge.className = 'msg-whisper-badge';
        badge.textContent = `🤫 ${t('msg.whisperTo')} ${whisperNames}`;
        header.appendChild(badge);
        msg.classList.add('msg-whispered');
    }

    const body = document.createElement('div');
    body.className = 'msg-content';
    const shouldType = animate && !prefersReducedMotion();

    const units = [];
    const segments = messageSegments(content, contentType);
    segments.forEach((segment, index) => {
        const isThought = segment.type === 'thought';
        const text = `${index ? '\n' : ''}${segment.text}`;
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
    });
    msg.appendChild(body);
    chatLog.appendChild(msg);
    deps.resetOpeningSuggestions();
    emptyState.style.display = 'none';
    scrollToBottom();

    if (shouldType) revealTypewriter(msg, units);
    return msg;
}

/* Combines the player's speech, thought, and action into the single echo bubble text
   (used both for the live echo in sendTurn and for replaying history). */
export function buildPlayerEcho(speech, thought, action) {
    return { speech: speech || null, thought: thought || null, action: action || null };
}

export function updatePlayerEcho(message, effectiveInput, transformed) {
    if (!message || !effectiveInput) return;
    const replacement = addMessage(
        'Player',
        buildPlayerEcho(effectiveInput.speech, effectiveInput.thought, effectiveInput.action),
        'response',
        { transformed },
    );
    message.replaceWith(replacement);
    state.lastEchoMessage = replacement;
}

/* Replays a canonical history into bubbles. Consecutive speech/thought/action
   records from the same speaker in the same turn collapse into one bubble,
   which is why the buffer exists. */
export function renderHistory(history) {
    deps.resetOpeningSuggestions();
    chatLog.innerHTML = '';
    chatLog.appendChild(emptyState);
    const records = history || [];
    state.playerHasSpoken = records.some((record) =>
        record.speaker === 'Player' &&
        record.content_type === 'speech' &&
        String(record.content || '').trim()
    );
    deps.updateSpeechPlaceholder();
    if (records.length) emptyState.style.display = 'none';
    else deps.showEmptyState(true);

    let responseBuffer = null;
    const flushResponseBuffer = () => {
        if (!responseBuffer) return;
        addMessage(responseBuffer.speaker, responseBuffer, 'response', {
            transformed: responseBuffer.transformed,
            whisperNames: responseBuffer.audienceOrigin === 'whisper' && responseBuffer.audience
                ? deps.whisperNamesFor(responseBuffer.audience) : '',
        });
        responseBuffer = null;
    };
    for (const record of records) {
        const combinable = ['speech', 'thought', 'action'].includes(record.content_type) &&
            record.speaker !== 'Narrator';
        if (combinable) {
            if (!responseBuffer || responseBuffer.turnNumber !== record.turn_number ||
                responseBuffer.speaker !== record.speaker) {
                flushResponseBuffer();
                responseBuffer = {
                    turnNumber: record.turn_number,
                    speaker: record.speaker,
                    speech: null,
                    thought: null,
                    action: null,
                    transformed: false,
                    audience: null,
                    audienceOrigin: null,
                };
            }
            responseBuffer[record.content_type] = record.content;
            responseBuffer.transformed ||= record.input_transformed === true;
            if (record.audience != null) {
                responseBuffer.audience = record.audience;
                responseBuffer.audienceOrigin = record.audience_origin;
            }
            continue;
        }
        flushResponseBuffer();
        addMessage(record.speaker, record.content, record.content_type);
    }
    flushResponseBuffer();
}
