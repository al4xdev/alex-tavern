/* Trusted frontend plugin loader and public browser SDK. */

import { api } from './api.js';
import { registerProviderAdapter } from './adapters/index.js';

const hooks = new Map();

function observe(pluginId, permission, details = {}) {
    fetch(`/plugins/${encodeURIComponent(pluginId)}/observe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ permission, ...details }),
        keepalive: true,
    }).catch(() => {});
}

function sdk(pluginId) {
    return Object.freeze({
        pluginId,
        api,
        registerProviderAdapter(adapter) {
            observe(pluginId, 'frontend.provider.register', { provider: adapter.id });
            registerProviderAdapter(adapter);
        },
        hook(name, handler) {
            const handlers = hooks.get(name) || [];
            handlers.push({ pluginId, handler });
            hooks.set(name, handlers);
        },
        mount(slot, element) {
            observe(pluginId, 'frontend.dom.mount', { slot });
            const target = document.querySelector(`[data-plugin-slot="${CSS.escape(slot)}"]`);
            if (!target) throw new Error(`Unknown plugin slot: ${slot}`);
            target.append(element);
        },
        unsafe: Object.freeze({ window, document }),
        observe(permission, details = {}) {
            observe(pluginId, permission, details);
        },
    });
}

async function runHook(name, value, context = {}) {
    let current = value;
    for (const item of hooks.get(name) || []) {
        try {
            current = await item.handler(current, context);
        } catch (error) {
            observe(item.pluginId, 'frontend.crash', { hook: name, error: String(error) });
        }
    }
    return current;
}

async function boot() {
    const status = await api.getPlugins();
    for (const plugin of status.loaded || []) {
        if (!plugin.frontend_url) continue;
        try {
            const module = await import(`${plugin.frontend_url}?v=${encodeURIComponent(plugin.version)}`);
            if (typeof module.activate !== 'function') {
                throw new Error('Frontend entrypoint must export activate(sdk)');
            }
            await module.activate(sdk(plugin.plugin_id));
            observe(plugin.plugin_id, 'frontend.loaded');
        } catch (error) {
            observe(plugin.plugin_id, 'frontend.crash', { error: String(error) });
        }
    }
    return status;
}

export const PluginRuntime = Object.freeze({ boot, runHook });
