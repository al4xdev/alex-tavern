import { normalizeSlashText } from './slash-registry.js';

export function tokenizeSlash(value) {
    if (typeof value !== 'string' || !value.startsWith('/')) return null;
    if (value.startsWith('//')) return { kind: 'literal', speech: value.slice(1) };
    const content = value.slice(1);
    const space = content.search(/\s/);
    const rawName = space < 0 ? content : content.slice(0, space);
    return {
        kind: 'query',
        name: normalizeSlashText(rawName),
        rest: space < 0 ? '' : content.slice(space).trim(),
    };
}

function aliases(entry) {
    return Object.values(entry.aliases || {}).flat().map(normalizeSlashText);
}

function localized(value, locale) {
    return value?.[locale] || value?.en || '';
}

function matchRank(entry, query, locale) {
    const name = normalizeSlashText(entry.name);
    const entryAliases = aliases(entry);
    if (name === query || entryAliases.includes(query)) return 0;
    if (name.startsWith(query)) return 1;
    if (entryAliases.some((alias) => alias.startsWith(query))) return 2;
    const title = normalizeSlashText(localized(entry.title, locale));
    const keywords = (entry.keywords?.[locale] || entry.keywords?.en || []).map(normalizeSlashText);
    if (title.startsWith(query) || keywords.some((keyword) => keyword.startsWith(query))) return 3;
    return Number.POSITIVE_INFINITY;
}

function contextualRank(entry, context) {
    const hasSession = !!context?.sessionId;
    const available = entry.available !== false;
    const scopeRank = hasSession
        ? (entry.scope === 'session' ? 0 : 1)
        : (entry.scope === 'global' ? 0 : 1);
    return scopeRank + (available ? 0 : 2);
}

export function matchingCommands(value, catalog, { locale = 'en', context = {} } = {}) {
    const parsed = tokenizeSlash(value);
    if (!parsed || parsed.kind !== 'query') return [];
    return catalog
        .map((entry, index) => ({
            entry,
            index,
            match: matchRank(entry, parsed.name, locale),
            context: contextualRank(entry, context),
        }))
        .filter((item) => Number.isFinite(item.match))
        .sort((left, right) => (
            left.match - right.match
            || left.context - right.context
            || (left.entry.order ?? left.index) - (right.entry.order ?? right.index)
            || left.entry.name.localeCompare(right.entry.name)
        ))
        .map((item) => item.entry);
}

export function resolveCommand(value, catalog) {
    const parsed = tokenizeSlash(value);
    if (!parsed || parsed.kind !== 'query') return null;
    const command = catalog.find((entry) => (
        normalizeSlashText(entry.name) === parsed.name || aliases(entry).includes(parsed.name)
    ));
    return command ? { command, rest: parsed.rest } : null;
}
