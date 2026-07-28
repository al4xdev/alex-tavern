/* Strict registry for core and plugin-provided app-drawer launchers. */

const LOCALES = Object.freeze(['en', 'pt-BR']);
const NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const coreEntries = [];
const pluginEntries = [];
let pluginOrder = 0;

function localized(value, field) {
    if (!value || typeof value !== 'object' || Array.isArray(value)
        || Object.keys(value).sort().join(',') !== LOCALES.slice().sort().join(',')) {
        throw new TypeError(`${field} must contain exactly en and pt-BR`);
    }
    const result = {};
    for (const locale of LOCALES) {
        if (typeof value[locale] !== 'string' || !value[locale].trim()) {
            throw new TypeError(`${field}.${locale} must be non-empty text`);
        }
        result[locale] = value[locale].trim();
    }
    return Object.freeze(result);
}

function descriptor(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        throw new TypeError('App entry descriptor must be an object');
    }
    const keys = Object.keys(value).sort();
    if (keys.join(',') !== ['icon', 'name', 'title'].sort().join(',')) {
        throw new TypeError('App entry accepts only name, title, and icon');
    }
    if (typeof value.name !== 'string' || !NAME.test(value.name)) {
        throw new TypeError('App entry name must be kebab-case');
    }
    if (typeof value.icon !== 'string' || !value.icon.trim() || value.icon.length > 32) {
        throw new TypeError('App entry icon must be 1 to 32 text characters');
    }
    return Object.freeze({
        name: value.name,
        title: localized(value.title, 'title'),
        icon: value.icon,
    });
}

function registration(scope, value, handler, order) {
    const normalized = descriptor(value);
    if (typeof handler !== 'function') throw new TypeError('App entry handler must be callable');
    return Object.freeze({
        id: scope === 'core' ? normalized.name : `${scope}/${normalized.name}`,
        pluginId: scope === 'core' ? null : scope,
        descriptor: normalized,
        handler,
        order,
    });
}

export function registerCoreApp(value, handler) {
    const item = registration('core', value, handler, coreEntries.length);
    if (coreEntries.some((entry) => entry.id === item.id)) {
        throw new Error(`Duplicate core app entry: ${item.id}`);
    }
    coreEntries.push(item);
    return item.id;
}

export function registerPluginApp(pluginId, value, handler) {
    if (typeof pluginId !== 'string' || !pluginId) throw new TypeError('pluginId is required');
    const item = registration(pluginId, value, handler, pluginOrder++);
    if (pluginEntries.some((entry) => entry.id === item.id)) {
        throw new Error(`Duplicate plugin app entry: ${item.id}`);
    }
    pluginEntries.push(item);
    return item.id;
}

export function removePluginAppEntries(pluginId) {
    for (let index = pluginEntries.length - 1; index >= 0; index -= 1) {
        if (pluginEntries[index].pluginId === pluginId) pluginEntries.splice(index, 1);
    }
}

export function appEntries() {
    return [...coreEntries, ...pluginEntries].sort((left, right) => {
        if (left.pluginId === null && right.pluginId !== null) return -1;
        if (left.pluginId !== null && right.pluginId === null) return 1;
        return left.order - right.order;
    });
}

export function resetAppRegistryForTests() {
    coreEntries.length = 0;
    pluginEntries.length = 0;
    pluginOrder = 0;
}
