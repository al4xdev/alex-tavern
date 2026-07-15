/* Shared registry for core actions, frontend plugin actions, and result renderers. */

const LOCALES = ['en', 'pt-BR'];
const TOKEN = /^[a-z][a-z0-9-]{0,63}$/;
const actions = [];
const renderers = new Map();
const namespace = new Map();
let sequence = 0;

export function normalizeSlashText(value) {
    return String(value || '')
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLocaleLowerCase();
}

function localizedText(value, label) {
    if (!value || typeof value !== 'object' || Object.keys(value).sort().join() !== 'en,pt-BR') {
        throw new Error(`${label} must contain exactly en and pt-BR`);
    }
    const result = Object.fromEntries(LOCALES.map((locale) => [locale, String(value[locale] || '').trim()]));
    if (Object.values(result).some((item) => !item)) throw new Error(`${label} translations cannot be empty`);
    return result;
}

function localizedTerms(value, label) {
    if (!value || typeof value !== 'object' || Object.keys(value).sort().join() !== 'en,pt-BR') {
        throw new Error(`${label} must contain exactly en and pt-BR`);
    }
    return Object.fromEntries(LOCALES.map((locale) => {
        const terms = value[locale];
        if (!Array.isArray(terms) || terms.some((term) => typeof term !== 'string' || !term.trim())) {
            throw new Error(`${label}.${locale} must be a string array`);
        }
        return [locale, terms.map((term) => term.trim())];
    }));
}

function actionDescriptor(descriptor) {
    if (!descriptor || typeof descriptor !== 'object') throw new Error('action descriptor must be an object');
    const allowed = new Set(['name', 'title', 'summary', 'icon', 'aliases', 'keywords', 'scope', 'availability']);
    const unknown = Object.keys(descriptor).filter((key) => !allowed.has(key));
    if (unknown.length) throw new Error(`unknown action descriptor fields: ${unknown.sort().join(', ')}`);
    if (!TOKEN.test(descriptor.name || '')) throw new Error('action name must be lowercase kebab-case');
    if (!['global', 'session'].includes(descriptor.scope)) throw new Error('action scope must be global or session');
    if (typeof descriptor.icon !== 'string' || !descriptor.icon.trim() || descriptor.icon.length > 32) {
        throw new Error('action icon must be a non-empty string of at most 32 characters');
    }
    if (descriptor.availability !== undefined && typeof descriptor.availability !== 'function') {
        throw new Error('action availability must be a function');
    }
    const aliases = localizedTerms(descriptor.aliases, 'aliases');
    const aliasTokens = aliases.en.concat(aliases['pt-BR']).map(normalizeSlashText);
    if (aliasTokens.some((alias) => !TOKEN.test(alias))) throw new Error('action aliases must be lowercase kebab-case');
    const names = [descriptor.name, ...aliasTokens];
    if (new Set(names).size !== names.length) throw new Error('action name and aliases must be unique');
    return Object.freeze({
        name: descriptor.name,
        title: localizedText(descriptor.title, 'title'),
        summary: localizedText(descriptor.summary, 'summary'),
        icon: descriptor.icon.trim(),
        aliases,
        keywords: localizedTerms(descriptor.keywords, 'keywords'),
        scope: descriptor.scope,
        availability: descriptor.availability || null,
    });
}

function claimNames(owner, displayOwner, names) {
    names.forEach((name) => {
        const existing = namespace.get(name);
        if (existing) throw new Error(`slash name or alias /${name} is already reserved by ${existing.display}`);
    });
    names.forEach((name) => namespace.set(name, { owner, display: displayOwner }));
}

function registerAction(origin, descriptor, handler) {
    if (typeof handler !== 'function') throw new Error('action handler must be callable');
    const normalized = actionDescriptor(descriptor);
    const names = [
        normalized.name,
        ...normalized.aliases.en.map(normalizeSlashText),
        ...normalized.aliases['pt-BR'].map(normalizeSlashText),
    ];
    claimNames(`action:${origin.id}`, origin.name, names);
    actions.push(Object.freeze({
        ...normalized,
        kind: 'action',
        origin_id: origin.id,
        origin_name: origin.name,
        handler,
        order: sequence++,
    }));
}

export function registerCoreAction(descriptor, handler) {
    registerAction({ id: 'core', name: 'Alex Tavern' }, descriptor, handler);
}

export function registerPluginAction(pluginId, pluginName, descriptor, handler) {
    registerAction({ id: pluginId, name: pluginName }, descriptor, handler);
}

export function reserveBackendCommands(commands) {
    for (const command of commands || []) {
        const names = [
            command.name,
            ...Object.values(command.aliases || {}).flat().map(normalizeSlashText),
        ];
        claimNames(`backend:${command.plugin_id}`, command.plugin_name, names);
    }
}

function registerRenderer(owner, kind, renderer, { core = false } = {}) {
    if (typeof kind !== 'string' || !kind.includes('/') || kind.endsWith('/')) {
        throw new Error('result renderer kind must be namespaced');
    }
    if (core ? !kind.startsWith('core/') : !kind.startsWith(`${owner}/`)) {
        throw new Error(core ? 'core renderer kind must use core/' : `renderer kind must use ${owner}/`);
    }
    if (typeof renderer !== 'function') throw new Error('result renderer must be callable');
    if (renderers.has(kind)) throw new Error(`result renderer ${kind} is already registered`);
    renderers.set(kind, { owner, renderer });
}

export function registerCoreCommandResultRenderer(kind, renderer) {
    registerRenderer('core', kind, renderer, { core: true });
}

export function registerPluginCommandResultRenderer(pluginId, kind, renderer) {
    registerRenderer(pluginId, kind, renderer);
}

export function removePluginSlashRegistrations(pluginId) {
    for (let index = actions.length - 1; index >= 0; index -= 1) {
        if (actions[index].origin_id === pluginId) actions.splice(index, 1);
    }
    for (const [name, claim] of namespace) {
        if (claim.owner === `action:${pluginId}`) namespace.delete(name);
    }
    for (const [kind, item] of renderers) if (item.owner === pluginId) renderers.delete(kind);
}

export function slashActions() {
    return [...actions];
}

export function commandResultRenderer(kind) {
    return renderers.get(kind)?.renderer || null;
}
