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
        const detail = (data && (data.detail || data.error)) || `HTTP ${res.status}`;
        const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        err.status = res.status;
        throw err;
    }
    return data;
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

    getDefaults(name = '') {
        const url = name ? `/defaults?name=${encodeURIComponent(name)}` : '/defaults';
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

    compact(sessionId) {
        return apiFetch(`/session/${sessionId}/compact`, { method: 'POST' });
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

    listPresets() {
        return apiFetch('/presets');
    },

    getPreset(name) {
        return apiFetch(`/presets/${name}`);
    },

    savePreset(name, cfg) {
        return apiFetch(`/presets/${name}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cfg),
        });
    },

    deletePreset(name) {
        return apiFetch(`/presets/${name}`, { method: 'DELETE' });
    },

    getVersion() {
        return apiFetch('/version');
    },
};
