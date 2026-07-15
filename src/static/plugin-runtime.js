/* Trusted frontend plugin loader and public browser SDK. */

import { api } from './api.js';
import { registerProviderAdapter } from './adapters/index.js';
import {
    registerPluginAction,
    registerPluginCommandResultRenderer,
    removePluginSlashRegistrations,
    reserveBackendCommands,
} from './slash-registry.js';

const hooks = new Map();

function observe(pluginId, permission, details = {}) {
    fetch(`/plugins/${encodeURIComponent(pluginId)}/observe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ permission, ...details }),
        keepalive: true,
    }).catch(() => {});
}

function sdk(pluginId, pluginName) {
    return Object.freeze({
        pluginId,
        api,
        registerProviderAdapter(adapter) {
            observe(pluginId, 'frontend.provider.register', { provider: adapter.id });
            registerProviderAdapter(adapter);
        },
        registerAction(descriptor, handler) {
            registerPluginAction(pluginId, pluginName, descriptor, handler);
            observe(pluginId, 'frontend.action.register', { action: descriptor?.name });
        },
        registerCommandResultRenderer(kind, renderer) {
            registerPluginCommandResultRenderer(pluginId, kind, renderer);
            observe(pluginId, 'frontend.command-renderer.register', { kind });
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
    reserveBackendCommands(status.commands || []);
    for (const plugin of status.loaded || []) {
        if (!plugin.frontend_url) continue;
        try {
            const module = await import(`${plugin.frontend_url}?v=${encodeURIComponent(plugin.version)}`);
            if (typeof module.activate !== 'function') {
                throw new Error('Frontend entrypoint must export activate(sdk)');
            }
            await module.activate(sdk(plugin.plugin_id, plugin.name));
            observe(plugin.plugin_id, 'frontend.loaded');
        } catch (error) {
            removePluginSlashRegistrations(plugin.plugin_id);
            observe(plugin.plugin_id, 'frontend.crash', { error: String(error) });
        }
    }
    return status;
}

export const PluginRuntime = Object.freeze({ boot, runHook });
