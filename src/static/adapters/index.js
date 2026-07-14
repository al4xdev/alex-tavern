import { deepSeekAdapter } from './deepseek.js';
import { llamaCppAdapter } from './llama-cpp.js';

export const providerAdapters = [llamaCppAdapter, deepSeekAdapter];
export const providerAdapterMap = new Map(
    providerAdapters.map((adapter) => [adapter.id, adapter]),
);

if (providerAdapterMap.size !== providerAdapters.length) {
    throw new Error('Provider adapter identifiers must be unique');
}

export function registerProviderAdapter(adapter) {
    if (!adapter?.id) throw new Error('Provider adapter requires an id');
    const existing = providerAdapterMap.get(adapter.id);
    if (existing) {
        const index = providerAdapters.indexOf(existing);
        providerAdapters[index] = adapter;
    } else {
        providerAdapters.push(adapter);
    }
    providerAdapterMap.set(adapter.id, adapter);
}
