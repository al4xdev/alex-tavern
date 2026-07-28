import { el } from './dom.js';
import { appEntries } from './app-registry.js';
import { getLocale, onLocaleChange, t } from './i18n.js';

const overlay = el('app-drawer-overlay');
const grid = el('app-drawer-grid');
const trigger = el('app-drawer-btn');
const closeBtn = el('app-drawer-close-btn');
const errorEl = el('app-drawer-error');

let returnFocus = null;
let lastTile = null;
let notify = () => {};

function titleFor(entry) {
    return entry.descriptor.title[getLocale()] || entry.descriptor.title.en;
}

function tileFor(entry) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'app-tile';
    button.dataset.appEntry = entry.id;
    const title = titleFor(entry);
    button.title = title;
    button.setAttribute('aria-label', title);

    const icon = document.createElement('span');
    icon.className = 'app-tile-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = entry.descriptor.icon;
    const label = document.createElement('span');
    label.className = 'app-tile-title';
    label.textContent = title;
    button.append(icon, label);

    button.addEventListener('click', async () => {
        lastTile = button;
        errorEl.hidden = true;
        try {
            await entry.handler({ entryId: entry.id, returnToDrawer: back });
            overlay.classList.remove('active');
        } catch (error) {
            const message = t('apps.launchError', { error: error.message });
            errorEl.textContent = message;
            errorEl.hidden = false;
            notify(message, 'error', 4000);
        }
    });
    return button;
}

export function render() {
    const prior = document.activeElement?.dataset?.appEntry;
    grid.replaceChildren(...appEntries().map(tileFor));
    if (overlay.classList.contains('active')) {
        (prior && grid.querySelector(`[data-app-entry="${CSS.escape(prior)}"]`)
            || grid.querySelector('.app-tile'))?.focus({ preventScroll: true });
    }
}

export function open() {
    returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : trigger;
    render();
    overlay.classList.add('active');
    grid.querySelector('.app-tile')?.focus({ preventScroll: true });
}

export function close() {
    overlay.classList.remove('active');
    (returnFocus?.isConnected ? returnFocus : trigger).focus({ preventScroll: true });
    returnFocus = null;
}

export function back(entryId = null) {
    render();
    overlay.classList.add('active');
    const target = entryId
        ? grid.querySelector(`[data-app-entry="${CSS.escape(entryId)}"]`)
        : lastTile && grid.querySelector(`[data-app-entry="${CSS.escape(lastTile.dataset.appEntry)}"]`);
    (target || grid.querySelector('.app-tile'))?.focus({ preventScroll: true });
}

export function init(options = {}) {
    notify = options.notify || notify;
    trigger.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', (event) => {
        if (event.target === overlay) close();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape' || !overlay.classList.contains('active')) return;
        event.preventDefault();
        close();
    });
    onLocaleChange(render);
}
