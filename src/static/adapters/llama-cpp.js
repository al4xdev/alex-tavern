import { createProviderAdapter, standardGenerationFields } from './base.js';

export const llamaCppAdapter = createProviderAdapter({
    id: 'llama_cpp',
    label: 'llama.cpp',
    descriptionKey: 'provider.localDescription',
    badge: 'LOCAL',
    orbitClass: 'provider-orbit-local',
    fields: [
        {
            key: 'api_base',
            labelKey: 'provider.apiBase',
            type: 'url',
            placeholder: 'http://127.0.0.1:8888/v1',
            hintKey: 'provider.llamaHint',
        },
        {
            key: 'model',
            labelKey: 'provider.model',
            placeholderKey: 'provider.emptyModel',
        },
        ...standardGenerationFields().map((field) => ({ ...field, layout: 'numbers' })),
    ],
});
