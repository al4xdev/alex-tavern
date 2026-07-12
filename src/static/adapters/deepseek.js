import { createProviderAdapter, standardGenerationFields } from './base.js';

export const deepSeekAdapter = createProviderAdapter({
    id: 'deepseek',
    label: 'DeepSeek V4 Flash',
    description: 'Cloud · sem reasoning',
    badge: 'CLOUD',
    orbitClass: 'provider-orbit-cloud',
    statusText: 'CLOUD ATIVO',
    statusClass: 'cloud',
    forcedSettings: { thinking_enabled: false },
    notice: {
        icon: '◌',
        text: 'Reasoning desativado. O backend envia thinking.type = disabled em toda chamada.',
    },
    fields: [
        {
            key: 'api_key',
            label: 'Chave da API',
            type: 'password',
            autocomplete: 'new-password',
            placeholder: 'Cole uma nova chave ou deixe em branco para manter',
            secret: true,
        },
        { key: 'api_base', label: 'Base da API', type: 'url' },
        { key: 'model', label: 'Modelo' },
        ...standardGenerationFields().map((field) => ({ ...field, layout: 'numbers' })),
    ],
});
