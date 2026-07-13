import { createProviderAdapter, standardGenerationFields } from './base.js';

export const deepSeekAdapter = createProviderAdapter({
    id: 'deepseek',
    label: 'DeepSeek V4 Flash',
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
        { key: 'model', labelKey: 'provider.model' },
        ...standardGenerationFields().map((field) => ({ ...field, layout: 'numbers' })),
    ],
});
