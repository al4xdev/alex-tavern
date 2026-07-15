import { api } from './api.js';
import { getLocale, onLocaleChange, t } from './i18n.js';
import { matchingCommands, resolveCommand, tokenizeSlash } from './slash-command-parser.js';
import { commandResultRenderer, slashActions } from './slash-registry.js';

const input = document.getElementById('input-speech');
const trigger = document.getElementById('slash-trigger');
const list = document.getElementById('slash-suggestions');
const panel = document.getElementById('command-panel');
const panelTitle = document.getElementById('command-panel-title');
const panelOrigin = document.getElementById('command-panel-origin');
const panelSummary = document.getElementById('command-panel-summary');
const fieldsRoot = document.getElementById('command-fields');
const errorRoot = document.getElementById('command-error');
const closeButton = document.getElementById('command-panel-close');
const executeButton = document.getElementById('command-execute');
const inputArea = document.getElementById('input-area');

let backendCommands = [];
let catalogAvailable = true;
let suggestions = [];
let activeIndex = 0;
let activeCommand = null;
let slashMode = false;
let getContext = () => ({});
let notify = () => {};

function localized(value) {
    return value?.[getLocale()] || value?.en || '';
}

function availability(entry, context) {
    if (entry.scope === 'session' && !context.sessionId) {
        return { available: false, reason: t('commands.requiresSession') };
    }
    if (entry.scope === 'session' && context.busy) {
        return { available: false, reason: t('commands.sessionBusy') };
    }
    if (entry.kind === 'tool' && !commandResultRenderer(entry.result_kind)) {
        return { available: false, reason: t('commands.rendererMissing') };
    }
    if (entry.availability) {
        const result = entry.availability(context);
        if (result === false) return { available: false, reason: t('commands.unavailable') };
        if (typeof result === 'string') return { available: false, reason: result };
        if (result && typeof result === 'object' && result.available === false) return result;
    }
    return { available: true, reason: '' };
}

function combinedCatalog() {
    const context = getContext();
    const actions = slashActions();
    const tools = backendCommands.map((command, index) => ({
        ...command,
        kind: 'tool',
        scope: 'session',
        origin_id: command.plugin_id,
        origin_name: command.plugin_name,
        order: actions.length + index,
    }));
    return actions.concat(tools).map((entry) => ({ ...entry, ...availability(entry, context) }));
}

function hidePalette() {
    list.hidden = true;
    list.classList.remove('is-opening');
    list.replaceChildren();
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
}

function closeTool() {
    activeCommand = null;
    panel.hidden = true;
    fieldsRoot.replaceChildren();
    errorRoot.textContent = '';
}

function syncTrigger() {
    trigger.disabled = !slashMode;
    trigger.tabIndex = slashMode ? 0 : -1;
    trigger.setAttribute('aria-hidden', String(!slashMode));
}

function close({ clearInput = false } = {}) {
    slashMode = false;
    closeTool();
    hidePalette();
    inputArea.classList.remove('slash-mode', 'command-mode');
    syncTrigger();
    if (clearInput) input.value = '';
}

function setMode() {
    inputArea.classList.toggle('slash-mode', slashMode);
    syncTrigger();
    if (!slashMode) {
        inputArea.classList.remove('command-mode');
        closeTool();
    }
    return slashMode;
}

function optionElement(entry, index) {
    const option = document.createElement('button');
    option.type = 'button';
    option.className = 'slash-option';
    option.id = `slash-option-${index}`;
    option.role = 'option';
    option.setAttribute('aria-selected', String(index === activeIndex));
    option.setAttribute('aria-disabled', String(!entry.available));

    const icon = document.createElement('span');
    icon.className = 'slash-option-icon';
    icon.textContent = entry.icon;
    const copy = document.createElement('span');
    copy.className = 'slash-option-copy';
    const headline = document.createElement('span');
    headline.className = 'slash-option-headline';
    const code = document.createElement('code');
    code.textContent = `/${entry.name}`;
    const title = document.createElement('strong');
    title.textContent = localized(entry.title);
    headline.append(code, title);
    const summary = document.createElement('span');
    summary.className = 'slash-option-summary';
    summary.textContent = entry.available ? localized(entry.summary) : entry.reason;
    copy.append(headline, summary);
    const origin = document.createElement('span');
    origin.className = 'slash-option-origin';
    origin.textContent = entry.origin_name;
    option.append(icon, copy, origin);
    option.addEventListener('mousedown', (event) => event.preventDefault());
    option.addEventListener('click', () => activate(entry));
    return option;
}

function emptyPalette() {
    const empty = document.createElement('div');
    empty.className = 'slash-empty';
    empty.setAttribute('role', 'status');
    empty.textContent = t('commands.noResults');
    return empty;
}

function catalogNotice() {
    const notice = document.createElement('div');
    notice.className = 'slash-catalog-notice';
    notice.textContent = t('commands.catalogUnavailable');
    return notice;
}

function renderPalette() {
    const opening = list.hidden;
    const children = [];
    if (!catalogAvailable) children.push(catalogNotice());
    if (suggestions.length) children.push(...suggestions.map(optionElement));
    else children.push(emptyPalette());
    list.replaceChildren(...children);
    list.hidden = false;
    list.classList.toggle('is-opening', opening);
    input.setAttribute('aria-expanded', 'true');
    if (suggestions.length) input.setAttribute('aria-activedescendant', `slash-option-${activeIndex}`);
    else input.removeAttribute('aria-activedescendant');
}

function update() {
    if (!setMode()) {
        hidePalette();
        return;
    }
    closeTool();
    const context = getContext();
    suggestions = matchingCommands(`/${input.value}`, combinedCatalog(), { locale: getLocale(), context });
    activeIndex = 0;
    renderPalette();
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
    const error = document.createElement('span');
    error.className = 'command-field-error';
    error.dataset.commandError = spec.name;
    error.setAttribute('role', 'alert');
    group.append(label, control, hint, error);
    return group;
}

function openTool(command) {
    activeCommand = command;
    input.value = command.name;
    panelTitle.textContent = `/${command.name} · ${localized(command.title)}`;
    panelOrigin.textContent = command.origin_name;
    panelSummary.textContent = localized(command.summary);
    fieldsRoot.replaceChildren(...command.inputs.map(fieldElement));
    errorRoot.textContent = '';
    panel.hidden = false;
    inputArea.classList.add('slash-mode', 'command-mode');
    hidePalette();
    fieldsRoot.querySelector('input, textarea')?.focus();
}

async function activate(entry) {
    if (!entry.available) {
        notify(entry.reason, 'info');
        return;
    }
    input.value = entry.name;
    if (entry.kind === 'tool') {
        openTool(entry);
        return;
    }
    close({ clearInput: true });
    try {
        await entry.handler(getContext());
    } catch (error) {
        notify(error.message || String(error), 'error');
    }
}

function complete(entry) {
    input.value = entry.name;
    input.dispatchEvent(new Event('input'));
}

function handleKeydown(event) {
    if (!slashMode) return false;
    if (event.key === 'Escape') {
        event.preventDefault();
        close({ clearInput: true });
        return true;
    }
    if (event.key === 'Backspace' && input.value === '') {
        event.preventDefault();
        close({ clearInput: true });
        return true;
    }
    if (activeCommand && event.key === 'Enter') {
        event.preventDefault();
        fieldsRoot.querySelector('input, textarea')?.focus();
        return true;
    }
    if (!list.hidden && suggestions.length) {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            const direction = event.key === 'ArrowDown' ? 1 : -1;
            activeIndex = (activeIndex + direction + suggestions.length) % suggestions.length;
            renderPalette();
            list.querySelector(`#slash-option-${activeIndex}`)?.scrollIntoView({ block: 'nearest' });
            return true;
        }
        if (event.key === 'Tab') {
            event.preventDefault();
            complete(suggestions[activeIndex]);
            return true;
        }
        if (event.key === 'Enter') {
            event.preventDefault();
            activate(suggestions[activeIndex]);
            return true;
        }
    }
    if (event.key === 'Enter') {
        event.preventDefault();
        interceptSend();
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

function parsedCommandError(error) {
    try {
        const detail = JSON.parse(error.message);
        return { message: detail.message || error.message, field: detail.field || null };
    } catch { return { message: error.message, field: null }; }
}

function clearFieldErrors() {
    fieldsRoot.querySelectorAll('.command-field-error').forEach((element) => { element.textContent = ''; });
    fieldsRoot.querySelectorAll('[aria-invalid="true"]').forEach((element) => element.removeAttribute('aria-invalid'));
}

function showFieldError(field, message) {
    const control = fieldsRoot.querySelector(`[data-command-field="${CSS.escape(field)}"]`);
    const target = fieldsRoot.querySelector(`[data-command-error="${CSS.escape(field)}"]`);
    if (target) target.textContent = message;
    control?.setAttribute('aria-invalid', 'true');
    control?.focus();
}

async function executeTool() {
    if (!activeCommand) return;
    const currentAvailability = availability(activeCommand, getContext());
    if (!currentAvailability.available) {
        notify(currentAvailability.reason, 'info');
        return;
    }
    clearFieldErrors();
    const values = {};
    const files = {};
    const rawFiles = {};
    for (const spec of activeCommand.inputs) {
        const control = fieldsRoot.querySelector(`[data-command-field="${CSS.escape(spec.name)}"]`);
        if (spec.type === 'file') {
            const file = control.files?.[0];
            if (spec.required && !file) {
                showFieldError(spec.name, t('commands.required'));
                return;
            }
            if (file && file.size > spec.max_bytes) {
                showFieldError(spec.name, t('commands.fileTooLarge', { bytes: spec.max_bytes }));
                return;
            }
            if (file) {
                rawFiles[spec.name] = file;
                files[spec.name] = await filePayload(file);
            }
        } else {
            values[spec.name] = control.value;
            if (spec.required && !control.value.trim()) {
                showFieldError(spec.name, t('commands.required'));
                return;
            }
        }
    }
    errorRoot.textContent = '';
    executeButton.disabled = true;
    panel.classList.add('is-running');
    try {
        const response = await api.executeCommand(
            getContext().sessionId,
            activeCommand.name,
            { values, files },
        );
        const renderer = commandResultRenderer(response.result_kind);
        if (!renderer) throw new Error(t('commands.rendererMissing'));
        await renderer(response.result, { command: activeCommand, rawFiles, notify });
        notify(t('commands.completed', { command: activeCommand.name }), 'success');
        close({ clearInput: true });
    } catch (error) {
        const detail = parsedCommandError(error);
        errorRoot.textContent = detail.message;
        if (detail.field) showFieldError(detail.field, detail.message);
        notify(detail.message, 'error');
    } finally {
        panel.classList.remove('is-running');
        executeButton.disabled = false;
    }
}

async function interceptSend() {
    if (!slashMode) return false;
    const commandText = `/${input.value}`;
    const resolved = resolveCommand(commandText, combinedCatalog());
    if (!resolved) {
        const message = t('commands.unknown', { command: commandText.split(/\s/, 1)[0] });
        errorRoot.textContent = message;
        notify(message, 'error');
        update();
        return true;
    }
    await activate(resolved.command);
    return true;
}

async function refresh() {
    try {
        const response = await api.getCommands();
        if (response.schema_version !== 2) throw new Error('Unsupported command catalog schema');
        backendCommands = response.commands || [];
        catalogAvailable = true;
    } catch (error) {
        backendCommands = [];
        catalogAvailable = false;
        console.warn('Could not load slash command catalog:', error);
    }
    if (slashMode) update();
}

function openPalette() {
    if (getContext().busy) return;
    input.disabled = false;
    if (slashMode) {
        input.focus({ preventScroll: true });
        if (!activeCommand && list.hidden) update();
        return;
    }
    slashMode = true;
    input.value = '';
    input.focus({ preventScroll: true });
    update();
}

function handleInput() {
    if (!slashMode) {
        if (input.value.startsWith('//')) {
            input.value = tokenizeSlash(input.value).speech;
            close();
            return;
        }
        if (!input.value.startsWith('/')) {
            close();
            return;
        }
        slashMode = true;
        input.value = input.value.slice(1);
        update();
        return;
    }
    if (input.value.startsWith('/')) {
        slashMode = false;
        setMode();
        hidePalette();
        return;
    }
    update();
}

function init(options) {
    getContext = options.getContext;
    notify = options.notify;
    syncTrigger();
    input.addEventListener('input', handleInput);
    trigger.addEventListener('click', openPalette);
    closeButton.addEventListener('click', () => close({ clearInput: true }));
    executeButton.addEventListener('click', executeTool);
    onLocaleChange(() => {
        if (activeCommand) openTool(activeCommand);
        else if (!list.hidden) update();
    });
    refresh();
}

export const SlashCommands = { init, refresh, handleKeydown, interceptSend, open: openPalette };
