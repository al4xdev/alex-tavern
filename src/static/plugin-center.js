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
    let notify = () => {};

    function empty(container, key) {
        const element = document.createElement('p');
        element.className = 'plugin-empty';
        element.textContent = t(key);
        container.replaceChildren(element);
    }

    function experienceCard(experience) {
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
        activate.addEventListener('click', async () => {
            activate.disabled = true;
            try {
                await api.activateExperience(experience.id);
                notify(t('plugins.restarting'), 'success', 6000);
                setTimeout(() => window.location.reload(), 1400);
            } catch (error) {
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
                activate.disabled = false;
            }
        });
        copy.append(title, description, activate);
        card.append(visual, copy);
        return card;
    }

    function pluginCard(item, loadedIds) {
        const manifest = item.manifest;
        const active = loadedIds.has(manifest.plugin_id) || item.active;
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
        card.append(copy, toggle);
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
        const [experiences, status, events, catalog] = await Promise.all([
            api.listExperiences(), api.getPlugins(), api.getPluginEvents(), api.getPluginCatalog(),
        ]);
        if (experiences.length) experienceGrid.replaceChildren(...experiences.map(experienceCard));
        else empty(experienceGrid, 'plugins.noExperiences');
        const loadedIds = new Set((status.loaded || []).map((plugin) => plugin.plugin_id));
        const installedKeys = new Set(status.installed.map((item) => (
            `${item.manifest.plugin_id}@${item.manifest.version}`
        )));
        if (catalog.plugins.length) {
            catalogStack.replaceChildren(...catalog.plugins.map((item) => catalogCard(item, installedKeys)));
        } else empty(catalogStack, 'plugins.noCatalog');
        if (status.installed.length) {
            pluginStack.replaceChildren(...status.installed.map((item) => pluginCard(item, loadedIds)));
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
        closeBtn.addEventListener('click', () => overlay.classList.remove('active'));
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) overlay.classList.remove('active');
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
