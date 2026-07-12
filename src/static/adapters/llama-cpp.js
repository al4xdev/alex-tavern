import { createProviderAdapter, standardGenerationFields } from './base.js';

export const llamaCppAdapter = createProviderAdapter({
    id: 'llama_cpp',
    label: 'llama.cpp',
    description: 'Local · sua máquina ou rede',
    badge: 'LOCAL',
    orbitClass: 'provider-orbit-local',
    statusText: 'LOCAL ATIVO',
    fields: [
        {
            key: 'api_base',
            label: 'Base da API',
            type: 'url',
            placeholder: 'http://127.0.0.1:8888/v1',
            hint: 'Inclua /v1 para o endpoint OpenAI do llama.cpp.',
        },
        {
            key: 'model',
            label: 'Modelo',
            placeholder: 'Vazio usa o modelo carregado',
        },
        ...standardGenerationFields().map((field) => ({ ...field, layout: 'numbers' })),
    ],
});
