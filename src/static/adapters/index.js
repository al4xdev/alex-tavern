import { deepSeekAdapter } from './deepseek.js';
import { llamaCppAdapter } from './llama-cpp.js';

export const providerAdapters = Object.freeze([llamaCppAdapter, deepSeekAdapter]);
export const providerAdapterMap = new Map(
    providerAdapters.map((adapter) => [adapter.id, adapter]),
);

if (providerAdapterMap.size !== providerAdapters.length) {
    throw new Error('Provider adapter identifiers must be unique');
}
