/* Declarative frontend adapter factory for one server-side LLM provider. */

import { bindTranslation, t } from '../i18n.js';

const INTEGER_FIELDS = new Set([
    'context_max',
    'max_tokens_narrator',
    'max_tokens_character',
    'summarizer_max_tokens',
]);

function inputId(provider, key) {
    return `provider-${provider}-${key.replaceAll('_', '-')}`;
}

function makeElement(tag, className = '', text = '') {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
}

export function standardGenerationFields() {
    return [
        { key: 'context_max', labelKey: 'provider.context', type: 'number', min: 1 },
        { key: 'max_tokens_narrator', labelKey: 'provider.narrator', type: 'number', min: 1 },
        { key: 'max_tokens_character', labelKey: 'provider.character', type: 'number', min: 1 },
        { key: 'summarizer_max_tokens', labelKey: 'provider.summary', type: 'number', min: 1 },
        { key: 'llm_timeout_seconds', labelKey: 'provider.timeout', type: 'number', min: 0.5, step: 0.5 },
    ];
}

export function createProviderAdapter(definition) {
    const fields = Object.freeze(definition.fields.map((field) => Object.freeze({ ...field })));
    const forcedSettings = Object.freeze({ ...(definition.forcedSettings || {}) });
    let card = null;
    let panel = null;

    function renderCard(container, onSelect) {
        card = makeElement('button', 'provider-card');
        card.type = 'button';
        card.dataset.provider = definition.id;
        card.setAttribute('role', 'radio');
        card.setAttribute('aria-checked', 'false');

        const orbit = makeElement('span', `provider-orbit ${definition.orbitClass}`);
        const copy = makeElement('span', 'provider-copy');
        copy.append(
            makeElement('strong', '', definition.label),
            bindTranslation(makeElement('small'), definition.descriptionKey),
        );
        card.append(orbit, copy, makeElement('span', 'provider-badge', definition.badge));
        card.addEventListener('click', () => onSelect(definition.id));
        container.appendChild(card);
    }

    function renderField(field, parent) {
        const wrapper = makeElement('div', 'field-group provider-wide');
        const id = inputId(definition.id, field.key);
        const label = bindTranslation(makeElement('label', 'field-label'), field.labelKey);
        label.htmlFor = id;
        const input = makeElement(field.type === 'select' ? 'select' : 'input', 'text-input');
        input.id = id;
        input.dataset.providerField = field.key;
        if (field.type === 'select') {
            (field.options || []).forEach((choice) => {
                const option = makeElement('option', '', choice.label || choice.value);
                option.value = choice.value;
                input.appendChild(option);
            });
        } else {
            input.type = field.type || 'text';
            input.autocomplete = field.autocomplete || 'off';
            if (field.placeholder) input.placeholder = field.placeholder;
            if (field.placeholderKey) bindTranslation(input, field.placeholderKey, {}, 'placeholder');
            if (field.min !== undefined) input.min = String(field.min);
            if (field.step !== undefined) input.step = String(field.step);
            if (input.type === 'number') input.inputMode = field.step ? 'decimal' : 'numeric';
        }
        wrapper.append(label, input);
        if (field.hint || field.hintKey || field.secret) {
            const hint = field.hintKey
                ? bindTranslation(makeElement('p', 'field-hint'), field.hintKey)
                : makeElement('p', 'field-hint', field.hint || '');
            hint.dataset.fieldHint = field.key;
            wrapper.appendChild(hint);
        }
        parent.appendChild(wrapper);
    }

    function renderPanel(container) {
        panel = makeElement('div', 'provider-panel');
        panel.dataset.providerPanel = definition.id;
        panel.hidden = true;

        fields.filter((field) => field.layout !== 'numbers').forEach((field) => {
            renderField(field, panel);
        });

        if (definition.notice) {
            const notice = makeElement('div', 'reasoning-lock provider-wide');
            notice.append(
                makeElement('span', 'reasoning-lock-icon', definition.notice.icon),
                bindTranslation(makeElement('span', 'reasoning-lock-copy'), definition.notice.textKey),
            );
            panel.appendChild(notice);
        }

        const numericFields = fields.filter((field) => field.layout === 'numbers');
        if (numericFields.length) {
            const grid = makeElement('div', 'provider-number-grid');
            numericFields.forEach((field) => {
                const label = makeElement('label');
                const textSpan = bindTranslation(makeElement('span'), field.labelKey);
                const input = makeElement('input', 'text-input');
                input.id = inputId(definition.id, field.key);
                label.htmlFor = input.id;
                input.dataset.providerField = field.key;
                input.type = 'number';
                input.min = String(field.min ?? 1);
                if (field.step !== undefined) input.step = String(field.step);
                input.inputMode = field.step ? 'decimal' : 'numeric';
                label.append(textSpan, input);
                grid.appendChild(label);
            });
            panel.appendChild(grid);
        }
        container.appendChild(panel);
    }

    function populate(config) {
        fields.forEach((field) => {
            const input = panel.querySelector(`[data-provider-field="${field.key}"]`);
            const value = field.secret ? '' : (config[field.key] ?? '');
            if (field.type === 'select' && value !== ''
                && ![...input.options].some((option) => option.value === value)) {
                // A stored model outside the current catalog (set via API or an
                // older release) must stay selectable, not be silently swapped.
                const extra = makeElement('option', '', value);
                extra.value = value;
                input.appendChild(extra);
            }
            input.value = value;
            if (field.secret) {
                const configured = Boolean(config[`${field.key}_configured`]);
                const hint = panel.querySelector(`[data-field-hint="${field.key}"]`);
                bindTranslation(hint, configured ? 'provider.keyConfigured' : 'provider.keyMissing');
                hint.classList.toggle('configured', configured);
            }
        });
    }

    function read() {
        const config = { ...forcedSettings };
        fields.forEach((field) => {
            const input = panel.querySelector(`[data-provider-field="${field.key}"]`);
            const raw = input.value.trim();
            if (INTEGER_FIELDS.has(field.key)) config[field.key] = Number.parseInt(raw, 10);
            else if (field.key === 'llm_timeout_seconds') config[field.key] = Number.parseFloat(raw);
            else config[field.key] = raw;
        });
        return config;
    }

    function setActive(active) {
        card.classList.toggle('active', active);
        card.setAttribute('aria-checked', active ? 'true' : 'false');
        panel.hidden = !active;
    }

    return Object.freeze({
        id: definition.id,
        statusText: () => t('engine.statusActive', { kind: definition.badge }),
        statusClass: definition.statusClass || '',
        renderCard,
        renderPanel,
        populate,
        read,
        setActive,
    });
}
