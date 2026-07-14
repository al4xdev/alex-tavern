import { createProviderAdapter, standardGenerationFields } from '/adapters/base.js';

export function activate(sdk) {
    sdk.registerProviderAdapter(createProviderAdapter({
        id: 'openrouter',
        label: 'OpenRouter',
        descriptionKey: 'provider.cloudDescription',
        badge: 'ROUTER',
        orbitClass: 'provider-orbit-cloud',
        statusClass: 'cloud',
        forcedSettings: { thinking_enabled: false },
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
    }));
}
