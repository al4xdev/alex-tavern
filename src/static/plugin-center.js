/* Experience-first plugin management UI. */

import { api } from './api.js';
import { t } from './i18n.js';

export const PluginCenter = (() => {
    const overlay = document.getElementById('plugins-overlay');
    const openBtn = document.getElementById('plugins-btn');
    const closeBtn = document.getElementById('plugins-close-btn');
    const experienceGrid = document.getElementById('experience-grid');
    const catalogStack = document.getElementById('plugin-catalog-stack');
    const pluginStack = document.getElementById('plugin-stack');
    const activity = document.getElementById('plugin-activity');
    const zipPath = document.getElementById('plugin-zip-path');
    const installBtn = document.getElementById('plugin-install-btn');
    const confirmLayer = document.getElementById('plugin-confirm-layer');
    const confirmTitle = document.getElementById('plugin-confirm-title');
    const confirmDescription = document.getElementById('plugin-confirm-description');
    const confirmList = document.getElementById('plugin-confirm-list');
    const confirmCancel = document.getElementById('plugin-confirm-cancel');
    const confirmAccept = document.getElementById('plugin-confirm-accept');
    let notify = () => {};
    let pendingConfirmation = null;
    let confirmationReturnFocus = null;

    function empty(container, key) {
        const element = document.createElement('p');
        element.className = 'plugin-empty';
        element.textContent = t(key);
        container.replaceChildren(element);
    }

    function confirmationItem(item) {
        const row = document.createElement('li');
        const copy = document.createElement('div');
        const title = document.createElement('strong');
        title.textContent = item.name;
        const metadata = document.createElement('span');
        metadata.textContent = item.version || t('plugins.latestVersion');
        copy.append(title, metadata);
        const status = document.createElement('span');
        status.className = `plugin-confirm-status ${item.danger ? 'danger' : ''}`;
        status.textContent = item.status;
        row.append(copy, status);
        return row;
    }

    function hideConfirmation({ restoreFocus = true } = {}) {
        confirmLayer.hidden = true;
        pendingConfirmation = null;
        if (restoreFocus && confirmationReturnFocus?.isConnected) {
            confirmationReturnFocus.focus({ preventScroll: true });
        }
        confirmationReturnFocus = null;
    }

    function showConfirmation({ title, description, items, acceptLabel, danger = false, action }) {
        confirmationReturnFocus = document.activeElement;
        confirmTitle.textContent = title;
        confirmDescription.textContent = description;
        confirmList.replaceChildren(...items.map(confirmationItem));
        confirmAccept.textContent = acceptLabel;
        confirmAccept.className = danger ? 'btn btn-danger' : 'btn btn-primary';
        confirmAccept.disabled = false;
        confirmCancel.disabled = false;
        pendingConfirmation = action;
        confirmLayer.hidden = false;
        confirmAccept.focus({ preventScroll: true });
    }

    async function acceptConfirmation() {
        if (!pendingConfirmation) return;
        confirmAccept.disabled = true;
        confirmCancel.disabled = true;
        try {
            const outcome = await pendingConfirmation();
            hideConfirmation({ restoreFocus: false });
            if (outcome.restart) {
                notify(t('plugins.restarting'), 'success', 6000);
                setTimeout(() => window.location.reload(), 1400);
            } else {
                await refresh();
                notify(t(outcome.messageKey), 'success');
            }
        } catch (error) {
            notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
            confirmAccept.disabled = false;
            confirmCancel.disabled = false;
        }
    }

    function experienceCard(experience, catalog, installedKeys) {
        const card = document.createElement('article');
        card.className = 'experience-card';
        const visual = document.createElement('div');
        visual.className = 'experience-visual';
        if (experience.image) visual.style.backgroundImage = `url(${JSON.stringify(experience.image).slice(1, -1)})`;
        const count = document.createElement('span');
        count.textContent = t('plugins.pluginCount', { count: experience.plugins.length });
        visual.append(count);
        const copy = document.createElement('div');
        copy.className = 'experience-copy';
        const title = document.createElement('h4');
        title.textContent = experience.name;
        const description = document.createElement('p');
        description.textContent = experience.description;
        const activate = document.createElement('button');
        activate.className = 'btn btn-primary';
        activate.textContent = t('plugins.activateExperience');
        activate.addEventListener('click', () => {
            const items = experience.plugins.map((plugin) => {
                const available = catalog.find((entry) => (
                    entry.id === plugin.id && (!plugin.version || entry.version === plugin.version)
                ));
                const version = plugin.version || available?.version || '';
                const cached = installedKeys.has(`${plugin.id}@${version}`);
                return {
                    name: available?.name || plugin.id,
                    version,
                    status: t(cached ? 'plugins.willActivate' : 'plugins.willInstall'),
                };
            });
            showConfirmation({
                title: experience.name,
                description: t('plugins.experienceConfirm', { name: experience.name }),
                items,
                acceptLabel: t('plugins.installAndActivate'),
                action: async () => {
                    await api.activateExperience(experience.id);
                    return { restart: true };
                },
            });
        });
        copy.append(title, description, activate);
        card.append(visual, copy);
        return card;
    }

    function pluginCard(item) {
        const manifest = item.manifest;
        const active = item.active;
        const card = document.createElement('article');
        card.className = `plugin-card ${active ? 'active' : ''}`;
        const copy = document.createElement('div');
        const title = document.createElement('h4');
        title.textContent = manifest.name;
        const metadata = document.createElement('span');
        metadata.className = 'plugin-meta';
        metadata.textContent = `${manifest.version} · ${manifest.license}`;
        const description = document.createElement('p');
        description.textContent = manifest.description;
        const permissions = document.createElement('div');
        permissions.className = 'plugin-permissions';
        manifest.permissions.forEach((permission) => {
            const badge = document.createElement('span');
            badge.textContent = permission;
            permissions.append(badge);
        });
        copy.append(title, metadata, description, permissions);
        const toggle = document.createElement('button');
        toggle.className = active ? 'btn btn-mini' : 'btn btn-primary';
        toggle.textContent = t(active ? 'plugins.deactivate' : 'plugins.activate');
        toggle.addEventListener('click', async () => {
            toggle.disabled = true;
            try {
                if (active) await api.deactivatePlugin(manifest.plugin_id);
                else await api.activatePlugin(manifest.plugin_id, {
                    version: manifest.version,
                    sha256: item.sha256,
                });
                notify(t('plugins.restarting'), 'success', 6000);
                setTimeout(() => window.location.reload(), 1400);
            } catch (error) {
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
                toggle.disabled = false;
            }
        });
        const remove = document.createElement('button');
        remove.className = 'btn btn-mini btn-danger-ghost';
        remove.textContent = t('plugins.remove');
        remove.addEventListener('click', () => {
            showConfirmation({
                title: t('plugins.removeTitle', { name: manifest.name }),
                description: t('plugins.removeConfirm', { name: manifest.name }),
                items: [{
                    name: manifest.name,
                    version: `${manifest.version} · ${item.sha256.slice(0, 12)}`,
                    status: t(active ? 'plugins.removeActive' : 'plugins.removeCached'),
                    danger: true,
                }],
                acceptLabel: t('plugins.remove'),
                danger: true,
                action: async () => {
                    const result = await api.uninstallPlugin(
                        manifest.plugin_id, manifest.version, item.sha256,
                    );
                    return { restart: result.restart, messageKey: 'plugins.removed' };
                },
            });
        });
        const actions = document.createElement('div');
        actions.className = 'plugin-card-actions';
        actions.append(toggle, remove);
        card.append(copy, actions);
        return card;
    }

    function catalogCard(item, installedKeys) {
        const installed = installedKeys.has(`${item.id}@${item.version}`);
        const card = document.createElement('article');
        card.className = 'plugin-card';
        const copy = document.createElement('div');
        const title = document.createElement('h4');
        title.textContent = item.name;
        const metadata = document.createElement('span');
        metadata.className = 'plugin-meta';
        metadata.textContent = `${item.version} · ${item.license}`;
        const description = document.createElement('p');
        description.textContent = item.description;
        copy.append(title, metadata, description);
        const button = document.createElement('button');
        button.className = installed ? 'btn btn-mini' : 'btn btn-primary';
        button.textContent = t(installed ? 'plugins.cached' : 'plugins.install');
        button.disabled = installed;
        button.addEventListener('click', async () => {
            button.disabled = true;
            try {
                await api.installCuratedPlugin(item.id, item.version);
                await refresh();
                notify(t('plugins.installed'), 'success');
            } catch (error) {
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
                button.disabled = false;
            }
        });
        card.append(copy, button);
        return card;
    }

    async function refresh() {
        // Catalog synchronization also materializes curated Experiences. Await it
        // before listing them so a fresh install is complete on its first open.
        const catalog = await api.getPluginCatalog();
        const [experiences, status, events] = await Promise.all([
            api.listExperiences(), api.getPlugins(), api.getPluginEvents(),
        ]);
        const installedKeys = new Set(status.installed.map((item) => (
            `${item.manifest.plugin_id}@${item.manifest.version}`
        )));
        if (experiences.length) {
            experienceGrid.replaceChildren(...experiences.map((experience) => (
                experienceCard(experience, catalog.plugins, installedKeys)
            )));
        } else empty(experienceGrid, 'plugins.noExperiences');
        if (catalog.plugins.length) {
            catalogStack.replaceChildren(...catalog.plugins.map((item) => catalogCard(item, installedKeys)));
        } else empty(catalogStack, 'plugins.noCatalog');
        if (status.installed.length) {
            pluginStack.replaceChildren(...status.installed.map(pluginCard));
        } else empty(pluginStack, 'plugins.noPlugins');
        if (events.length) {
            activity.replaceChildren(...events.reverse().map((event) => {
                const row = document.createElement('article');
                row.className = 'activity-row';
                const title = document.createElement('strong');
                title.textContent = `${event.plugin_id} · ${event.event}`;
                const details = document.createElement('code');
                details.textContent = JSON.stringify(event.details);
                row.append(title, details);
                return row;
            }));
        } else empty(activity, 'plugins.noActivity');
    }

    function selectTab(name) {
        document.querySelectorAll('[data-plugin-tab]').forEach((tab) => {
            tab.classList.toggle('active', tab.dataset.pluginTab === name);
        });
        document.querySelectorAll('[data-plugin-view]').forEach((view) => {
            view.classList.toggle('active', view.dataset.pluginView === name);
        });
    }

    function init(options = {}) {
        notify = options.notify || notify;
        openBtn.addEventListener('click', async () => {
            overlay.classList.add('active');
            try { await refresh(); }
            catch (error) { notify(t('plugins.operationError', { error: error.message }), 'error'); }
        });
        closeBtn.addEventListener('click', () => {
            if (!confirmLayer.hidden) hideConfirmation();
            else overlay.classList.remove('active');
        });
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) overlay.classList.remove('active');
        });
        confirmCancel.addEventListener('click', () => hideConfirmation());
        confirmAccept.addEventListener('click', acceptConfirmation);
        document.addEventListener('keydown', (event) => {
            if (event.key !== 'Escape' || !overlay.classList.contains('active')) return;
            event.preventDefault();
            if (!confirmLayer.hidden) hideConfirmation();
            else overlay.classList.remove('active');
        });
        document.querySelectorAll('[data-plugin-tab]').forEach((tab) => {
            tab.addEventListener('click', () => selectTab(tab.dataset.pluginTab));
        });
        installBtn.addEventListener('click', async () => {
            const file = zipPath.files?.[0];
            if (!file) return;
            installBtn.disabled = true;
            try {
                await api.installPluginFile(file);
                zipPath.value = '';
                await refresh();
                notify(t('plugins.installed'), 'success');
            } catch (error) {
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
            } finally { installBtn.disabled = false; }
        });
    }

    return { init, refresh };
})();
