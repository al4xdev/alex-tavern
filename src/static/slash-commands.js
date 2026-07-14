import { api } from './api.js';
import { getLocale, onLocaleChange, t } from './i18n.js';
import { matchingCommands, resolveCommand, tokenizeSlash } from './slash-command-parser.js';

const input = document.getElementById('input-speech');
const list = document.getElementById('slash-suggestions');
const panel = document.getElementById('command-panel');
const panelTitle = document.getElementById('command-panel-title');
const panelSummary = document.getElementById('command-panel-summary');
const fieldsRoot = document.getElementById('command-fields');
const errorRoot = document.getElementById('command-error');
const closeButton = document.getElementById('command-panel-close');
const sendButton = document.getElementById('send-btn');

let catalog = [];
let suggestions = [];
let activeIndex = 0;
let activeCommand = null;
let getSessionId = () => null;
let notify = () => {};
let onPresetDraft = () => {};

function localized(value) {
    return value?.[getLocale()] || value?.en || '';
}

function parsedInput() {
    const resolved = resolveCommand(input.value, catalog);
    if (resolved) return { name: resolved.command.name, rest: resolved.rest };
    const parsed = tokenizeSlash(input.value);
    return parsed?.kind === 'query' ? { name: parsed.name, rest: parsed.rest } : null;
}

function hideSuggestions() {
    list.hidden = true;
    list.innerHTML = '';
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
}

function choose(command) {
    input.value = `/${command.name} `;
    input.dispatchEvent(new Event('input'));
    hideSuggestions();
}

function renderSuggestions() {
    list.innerHTML = '';
    suggestions.forEach((command, index) => {
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'slash-option';
        option.id = `slash-option-${index}`;
        option.role = 'option';
        option.setAttribute('aria-selected', String(index === activeIndex));
        const code = document.createElement('code');
        code.textContent = `/${command.name}`;
        const summary = document.createElement('span');
        summary.textContent = localized(command.summary);
        option.append(code, summary);
        option.addEventListener('mousedown', (event) => event.preventDefault());
        option.addEventListener('click', () => choose(command));
        list.appendChild(option);
    });
    const visible = suggestions.length > 0;
    list.hidden = !visible;
    input.setAttribute('aria-expanded', String(visible));
    if (visible) input.setAttribute('aria-activedescendant', `slash-option-${activeIndex}`);
}

function fieldElement(spec) {
    const group = document.createElement('label');
    group.className = 'command-field';
    const label = document.createElement('span');
    label.className = 'field-label';
    label.textContent = localized(spec.label);
    const hint = document.createElement('small');
    hint.textContent = localized(spec.hint);
    let control;
    if (spec.type === 'textarea') {
        control = document.createElement('textarea');
        control.rows = 5;
        control.className = 'text-area';
    } else {
        control = document.createElement('input');
        control.type = spec.type === 'file' ? 'file' : 'text';
        control.className = spec.type === 'file' ? 'command-file' : 'text-input';
        if (spec.type === 'file') control.accept = spec.accept.join(',');
    }
    control.dataset.commandField = spec.name;
    control.required = spec.required;
    group.append(label, control, hint);
    return group;
}

function activate(command) {
    if (activeCommand?.name === command.name) return;
    activeCommand = command;
    panelTitle.textContent = `/${command.name}`;
    panelSummary.textContent = localized(command.summary);
    fieldsRoot.innerHTML = '';
    command.fields.forEach((spec) => fieldsRoot.appendChild(fieldElement(spec)));
    errorRoot.textContent = '';
    panel.hidden = false;
    panel.closest('.input-area')?.classList.add('command-mode');
}

function close({ clearInput = false } = {}) {
    activeCommand = null;
    panel.hidden = true;
    fieldsRoot.innerHTML = '';
    errorRoot.textContent = '';
    panel.closest('.input-area')?.classList.remove('command-mode');
    hideSuggestions();
    if (clearInput) input.value = '';
}

function update() {
    const raw = input.value;
    if (!raw.startsWith('/') || raw.startsWith('//')) {
        close();
        return;
    }
    const parsed = parsedInput();
    const command = parsed && catalog.find((item) => item.name === parsed.name);
    if (command) {
        activate(command);
        hideSuggestions();
        return;
    }
    if (activeCommand) close();
    suggestions = matchingCommands(raw, catalog);
    activeIndex = 0;
    renderSuggestions();
}

function handleKeydown(event) {
    if (!input.value.startsWith('/') || input.value.startsWith('//')) return false;
    if (!list.hidden && suggestions.length) {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            const direction = event.key === 'ArrowDown' ? 1 : -1;
            activeIndex = (activeIndex + direction + suggestions.length) % suggestions.length;
            renderSuggestions();
            return true;
        }
        if (event.key === 'Enter' || event.key === 'Tab') {
            event.preventDefault();
            choose(suggestions[activeIndex]);
            return true;
        }
    }
    if (event.key === 'Escape') {
        event.preventDefault();
        close({ clearInput: true });
        return true;
    }
    if (event.key === 'Enter' && activeCommand) {
        event.preventDefault();
        fieldsRoot.querySelector('input, textarea')?.focus();
        return true;
    }
    return false;
}

async function filePayload(file) {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = '';
    const block = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += block) {
        binary += String.fromCharCode(...bytes.subarray(offset, offset + block));
    }
    return { name: file.name, media_type: file.type || 'application/octet-stream', data_base64: btoa(binary) };
}

function commandError(error) {
    try {
        const detail = JSON.parse(error.message);
        return detail.message || error.message;
    } catch { return error.message; }
}

async function interceptSend() {
    if (input.value.startsWith('//')) {
        input.value = tokenizeSlash(input.value).speech;
        return false;
    }
    if (!input.value.startsWith('/')) return false;
    const parsed = parsedInput();
    const command = parsed && catalog.find((item) => item.name === parsed.name);
    if (!command) {
        const message = t('commands.unknown', { command: input.value.split(/\s/, 1)[0] });
        errorRoot.textContent = message;
        notify(message, 'error');
        return true;
    }
    activate(command);
    const sessionId = getSessionId();
    if (!sessionId) {
        notify(t('commands.startFirst'), 'error');
        return true;
    }
    const argumentValues = parsed.rest.split(/\s+/).filter(Boolean);
    const argumentsPayload = {};
    command.arguments.forEach((spec, index) => { argumentsPayload[spec.name] = argumentValues[index] || ''; });
    const fields = {};
    const files = {};
    let avatarFile = null;
    for (const spec of command.fields) {
        const control = fieldsRoot.querySelector(`[data-command-field="${spec.name}"]`);
        if (spec.type === 'file') {
            const file = control.files?.[0];
            if (file) {
                files[spec.name] = await filePayload(file);
                if (file.type === 'image/png' || file.name.toLowerCase().endsWith('.png')) avatarFile = file;
            }
        } else {
            fields[spec.name] = control.value;
        }
    }
    errorRoot.textContent = '';
    sendButton.disabled = true;
    panel.classList.add('is-running');
    try {
        const response = await api.executeCommand(sessionId, command.name, {
            arguments: argumentsPayload,
            fields,
            files,
        });
        if (response.result_kind === 'character_preset_draft') {
            await onPresetDraft(
                response.result.character,
                response.result.preset_name || argumentsPayload.preset_name,
                avatarFile,
            );
        }
        notify(t('commands.completed', { command: command.name }), 'success');
        close({ clearInput: true });
    } catch (error) {
        const message = commandError(error);
        errorRoot.textContent = message;
        notify(message, 'error');
    } finally {
        panel.classList.remove('is-running');
        sendButton.disabled = false;
    }
    return true;
}

async function refresh() {
    try {
        const response = await api.getCommands();
        catalog = response.commands || [];
        update();
    } catch (error) {
        catalog = [];
        console.warn('Could not load slash commands:', error);
    }
}

function init(options) {
    getSessionId = options.getSessionId;
    notify = options.notify;
    onPresetDraft = options.onPresetDraft;
    input.addEventListener('input', update);
    input.addEventListener('blur', () => setTimeout(hideSuggestions, 120));
    closeButton.addEventListener('click', () => close({ clearInput: true }));
    onLocaleChange(() => { update(); if (activeCommand) activate(activeCommand); });
    refresh();
}

export const SlashCommands = { init, refresh, handleKeydown, interceptSend };
