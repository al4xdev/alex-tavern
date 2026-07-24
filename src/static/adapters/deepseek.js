import { createProviderAdapter, standardGenerationFields } from './base.js';

export const deepSeekAdapter = createProviderAdapter({
    id: 'deepseek',
    label: 'DeepSeek V4',
    descriptionKey: 'provider.cloudDescription',
    badge: 'CLOUD',
    orbitClass: 'provider-orbit-cloud',
    statusClass: 'cloud',
    forcedSettings: { thinking_enabled: false },
    notice: {
        icon: '◌',
        textKey: 'provider.reasoningDisabled',
    },
    fields: [
        {
            key: 'api_key',
            labelKey: 'provider.apiKey',
            type: 'password',
            autocomplete: 'new-password',
            placeholderKey: 'provider.newKey',
            secret: true,
        },
        { key: 'api_base', labelKey: 'provider.apiBase', type: 'url' },
        {
            key: 'model',
            labelKey: 'provider.model',
            type: 'select',
            options: [
                { value: 'deepseek-v4-flash', label: 'deepseek-v4-flash' },
                { value: 'deepseek-v4-pro', label: 'deepseek-v4-pro' },
            ],
        },
        ...standardGenerationFields().map((field) => ({ ...field, layout: 'numbers' })),
    ],
});
