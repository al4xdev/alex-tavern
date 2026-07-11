/* ══════════════════════════════════════════════════════════════════════
   api.js — thin fetch wrappers around the backend.
   Every wrapper throws on non-2xx so callers can show a friendly toast.
   ══════════════════════════════════════════════════════════════════════ */

async function apiFetch(url, options = {}) {
    const res = await fetch(url, options);
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

const api = {
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

    previewPrompt(sessionId, payload) {
        return apiFetch(`/session/${sessionId}/preview_prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
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
};
