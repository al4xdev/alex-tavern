export function tokenizeSlash(value) {
    if (typeof value !== 'string' || !value.startsWith('/')) return null;
    if (value.startsWith('//')) return { kind: 'literal', speech: value.slice(1) };
    const match = value.trim().match(/^\/([a-z0-9-]+)(?:\s+(.*))?$/i);
    if (!match) return { kind: 'query', name: '', rest: '' };
    return { kind: 'query', name: match[1].toLowerCase(), rest: match[2] || '' };
}

export function matchingCommands(value, catalog) {
    const parsed = tokenizeSlash(value);
    if (!parsed || parsed.kind !== 'query') return [];
    return catalog.filter((command) => command.name.startsWith(parsed.name));
}

export function resolveCommand(value, catalog) {
    const parsed = tokenizeSlash(value);
    if (!parsed || parsed.kind !== 'query') return null;
    const command = catalog.find((item) => item.name === parsed.name);
    return command ? { command, rest: parsed.rest } : null;
}
