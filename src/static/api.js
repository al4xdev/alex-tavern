/* ══════════════════════════════════════════════════════════════════════
   api.js — thin fetch wrappers around the backend.
   Every wrapper throws on non-2xx so callers can show a friendly toast.
   ══════════════════════════════════════════════════════════════════════ */
// WARNING (Antigravity AI): Modified to switch BASE_URL to local server when running in WebView
const BASE_URL = window.location.protocol === 'file:' ? 'http://127.0.0.1:8889' : '';

async function apiFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`;
    const res = await fetch(fullUrl, options);
    let data = null;
    try {
        data = await res.json();
    } catch {
        data = null;
    }
    if (!res.ok) {
        const detail = (data && (data.detail || data.error || data.reason)) || `HTTP ${res.status}`;
        const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        err.status = res.status;
        throw err;
    }
    return data;
}

async function compactStream(sessionId, onProgress = () => {}, signal = null) {
    const res = await fetch(`${BASE_URL}/session/${sessionId}/compact`, {
        method: 'POST',
        headers: { Accept: 'text/event-stream' },
        signal,
    });
    if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
            const data = await res.json();
            detail = data.detail || data.error || detail;
        } catch { /* preserve the status detail */ }
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    if (!res.body) throw new Error('Compaction progress stream is unavailable');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let lastSequence = 0;
    let terminal = null;
    let terminalCount = 0;

    function consume(frame) {
        if (!frame.trim() || frame.trimStart().startsWith(':')) return;
        const dataLines = frame
            .split('\n')
            .filter((line) => line.startsWith('data:'))
            .map((line) => line.slice(5).trimStart());
        if (!dataLines.length) return;
        const event = JSON.parse(dataLines.join('\n'));
        if (!Number.isInteger(event.sequence) || event.sequence <= lastSequence) {
            throw new Error('Compaction progress sequence is invalid');
        }
        lastSequence = event.sequence;
        onProgress(event);
        if (['completed', 'skipped', 'failed'].includes(event.stage)) {
            terminalCount += 1;
            if (terminalCount > 1) {
                throw new Error('Compaction stream has multiple terminal events');
            }
            terminal = event;
        }
    }

    while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() || '';
        frames.forEach(consume);
        if (done) break;
    }
    if (buffer.trim()) consume(buffer);
    if (!terminal) throw new Error('Compaction stream ended without a terminal event');
    if (terminal.stage === 'failed') {
        throw new Error(terminal.error_type || 'Compaction failed');
    }
    return terminal.result;
}

export const api = {
    getConfig() {
        return apiFetch('/config');
    },

    saveConfig(config) {
        return apiFetch('/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
    },

    getBuiltinScenario(name = '') {
        const url = name ? `/scenario-defaults?name=${encodeURIComponent(name)}` : '/scenario-defaults';
        return apiFetch(url);
    },

    startSession(config) {
        return apiFetch('/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
    },

    turn(sessionId, payload, signal = null) {
        const opts = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        };
        if (signal) opts.signal = signal;
        return apiFetch(`/session/${sessionId}/turn`, opts);
    },

    getState(sessionId) {
        return apiFetch(`/session/${sessionId}/state`);
    },

    undo(sessionId) {
        return apiFetch(`/session/${sessionId}/undo`, { method: 'POST' });
    },

    suggest(sessionId) {
        return apiFetch(`/session/${sessionId}/suggest`, { method: 'POST' });
    },

    compact(sessionId, onProgress = () => {}, signal = null) {
        return compactStream(sessionId, onProgress, signal);
    },

    restoreCompaction(sessionId) {
        return apiFetch(`/session/${sessionId}/restore_compaction`, { method: 'POST' });
    },

    getDebugLog(sessionId) {
        return apiFetch(`/session/${sessionId}/debug_log`);
    },

    listSessions() {
        return apiFetch('/sessions');
    },

    forkSession(sessionId) {
        return apiFetch(`/session/${sessionId}/fork`, { method: 'POST' });
    },

    deleteSession(sessionId) {
        return apiFetch(`/session/${sessionId}`, { method: 'DELETE' });
    },

    listScenarios() {
        return apiFetch('/scenarios');
    },

    getScenario(name) {
        return apiFetch(`/scenarios/${name}`);
    },

    saveScenario(name, cfg) {
        return apiFetch(`/scenarios/${name}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cfg),
        });
    },

    deleteScenario(name) {
        return apiFetch(`/scenarios/${name}`, { method: 'DELETE' });
    },

    getVersion() {
        return apiFetch('/version');
    },

    getPlugins() {
        return apiFetch('/plugins');
    },

    getPluginCatalog() {
        return apiFetch('/plugins/catalog');
    },

    installPlugin(zipPath) {
        return apiFetch('/plugins/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ zip_path: zipPath }),
        });
    },

    installPluginFile(file) {
        return apiFetch('/plugins/install-upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/zip' },
            body: file,
        });
    },

    inspectPluginFile(file) {
        return apiFetch('/plugins/inspect-upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/zip' },
            body: file,
        });
    },

    installCuratedPlugin(pluginId, version = null) {
        const query = version ? `?version=${encodeURIComponent(version)}` : '';
        return apiFetch(`/plugins/catalog/${encodeURIComponent(pluginId)}/install${query}`, {
            method: 'POST',
        });
    },

    updateCuratedPlugin(pluginId, version, sha256) {
        return apiFetch(`/plugins/catalog/${encodeURIComponent(pluginId)}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version, sha256 }),
        });
    },

    activatePlugin(pluginId, selection = {}) {
        return apiFetch(`/plugins/${encodeURIComponent(pluginId)}/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(selection),
        });
    },

    deactivatePlugin(pluginId) {
        return apiFetch(`/plugins/${encodeURIComponent(pluginId)}/deactivate`, { method: 'POST' });
    },

    uninstallPlugin(pluginId, version, sha256) {
        const id = encodeURIComponent(pluginId);
        const selectedVersion = encodeURIComponent(version);
        const selectedHash = encodeURIComponent(sha256);
        return apiFetch(`/plugins/${id}/installations/${selectedVersion}/${selectedHash}`, {
            method: 'DELETE',
        });
    },

    getPluginEvents() {
        return apiFetch('/plugins/events');
    },

    listExperiences() {
        return apiFetch('/experiences');
    },

    activateExperience(experienceId) {
        return apiFetch(`/experiences/${encodeURIComponent(experienceId)}/activate`, {
            method: 'POST',
        });
    },
};
