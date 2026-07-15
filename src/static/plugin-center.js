/* Experience-first plugin management UI. */

import { api } from './api.js';
import { t, getLocale } from './i18n.js';

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
    const updateCount = document.getElementById('plugin-update-count');
    const track = document.getElementById('plugin-view-track');
    const tabs = [...document.querySelectorAll('[data-plugin-tab]')];
    const views = [...document.querySelectorAll('[data-plugin-view]')];
    const tabNames = tabs.map((tab) => tab.dataset.pluginTab);
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let notify = () => {};
    let pendingConfirmation = null;
    let confirmationReturnFocus = null;
    let activeTab = 0;
    let gesture = null;

    function empty(container, key) {
        const element = document.createElement('p');
        element.className = 'plugin-empty';
        element.textContent = t(key);
        container.replaceChildren(element);
    }

    function shortHash(value) {
        return value ? value.slice(0, 12) : '';
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

    function experienceIsActive(experience, statusPlugins) {
        const activeVersions = new Map();
        statusPlugins.forEach((plugin) => {
            if (plugin.active) activeVersions.set(plugin.plugin_id, plugin.active.manifest.version);
        });
        if (activeVersions.size !== experience.plugins.length) return false;
        return experience.plugins.every((item) => {
            const version = activeVersions.get(item.id);
            return version !== undefined && (!item.version || item.version === version);
        });
    }

    function experienceCard(experience, releases, cachedKeys, isActive) {
        const card = document.createElement('article');
        card.className = `experience-card ${isActive ? 'active' : ''}`;
        const visual = document.createElement('div');
        visual.className = 'experience-visual';
        if (experience.image) {
            visual.style.backgroundImage = `url(${JSON.stringify(experience.image).slice(1, -1)})`;
        }
        const count = document.createElement('span');
        count.textContent = t('plugins.pluginCount', { count: experience.plugins.length });
        visual.append(count);
        const copy = document.createElement('div');
        copy.className = 'experience-copy';
        const titleRow = document.createElement('div');
        titleRow.className = 'experience-title-row';
        const title = document.createElement('h4');
        title.textContent = experience.name;
        titleRow.append(title);
        if (isActive) {
            const badge = document.createElement('span');
            badge.className = 'experience-active-badge';
            badge.textContent = t('plugins.experienceActive');
            titleRow.append(badge);
        }
        const description = document.createElement('p');
        description.textContent = experience.description;
        const activate = document.createElement('button');
        activate.className = 'btn btn-primary';
        activate.textContent = t('plugins.activateExperience');
        activate.addEventListener('click', () => {
            const items = experience.plugins.map((plugin) => {
                const available = releases.find((entry) => (
                    entry.id === plugin.id && (!plugin.version || entry.version === plugin.version)
                ));
                const version = plugin.version || available?.version || '';
                return {
                    name: available?.name || plugin.id,
                    version,
                    status: t(cachedKeys.has(`${plugin.id}@${version}`)
                        ? 'plugins.willActivate' : 'plugins.willInstall'),
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
        copy.append(titleRow, description, activate);
        card.append(visual, copy);
        return card;
    }

    function permissionBadges(manifest) {
        const permissions = document.createElement('div');
        permissions.className = 'plugin-permissions';
        manifest.permissions.forEach((permission) => {
            const badge = document.createElement('span');
            badge.textContent = permission;
            permissions.append(badge);
        });
        return permissions;
    }

    function installationReviewItems(manifest, sha256, { external = false } = {}) {
        const items = [{
            name: t('plugins.release'),
            version: `${manifest.version} · #${shortHash(sha256)}`,
            status: t('plugins.willInstallCache'),
        }];
        if (external) items.push({
            name: t('plugins.externalSource'),
            version: t('plugins.externalSourceDetail'),
            status: t('plugins.fullTrustWarning'),
            danger: true,
        });
        if (manifest.permissions.length) {
            manifest.permissions.forEach((permission) => items.push({
                name: permission,
                version: t('plugins.declaredPermission'),
                status: permission === 'model.call'
                    ? t('plugins.modelCallCostWarning') : t('plugins.permissionReview'),
                danger: permission === 'model.call',
            }));
        } else items.push({
            name: t('plugins.permissions'),
            version: t('plugins.noDeclaredPermissions'),
            status: t('plugins.reviewedContract'),
        });
        if (manifest.dependencies.length) items.push({
            name: t('plugins.dependencies'),
            version: manifest.dependencies.map((item) => (
                `${item.plugin_id} ${item.version}${item.optional ? ' ?' : ''}`
            )).join(', '),
            status: t('plugins.installRequirements'),
        });
        const entrypoints = Object.entries(manifest.entrypoints)
            .filter(([, value]) => value)
            .map(([kind, value]) => `${kind}: ${value}`)
            .join(', ');
        items.push({
            name: t('plugins.entrypoints'),
            version: entrypoints,
            status: t('plugins.codeLoadedInProcess'),
        });
        if (manifest.python_dependencies.length) items.push({
            name: t('plugins.pythonDependencies'),
            version: manifest.python_dependencies.join(', '),
            status: t('plugins.environmentOnActivation'),
        });
        return items;
    }

    function updateReviewItems(plugin) {
        const current = plugin.active || plugin.cached_versions[0];
        const candidate = plugin.curated;
        const items = [{
            name: t('plugins.release'),
            version: `${current.manifest.version} #${shortHash(current.sha256)} → ${candidate.manifest.version} #${shortHash(candidate.sha256)}`,
            status: t('plugins.willUpdateActivate'),
        }];
        const diff = candidate.diff;
        diff.permissions.added.forEach((permission) => items.push({
            name: permission,
            version: t('plugins.permissionAdded'),
            status: permission === 'model.call'
                ? t('plugins.modelCallCostWarning') : t('plugins.permissionReview'),
            danger: permission === 'model.call',
        }));
        diff.permissions.removed.forEach((permission) => items.push({
            name: permission,
            version: t('plugins.permissionRemoved'),
            status: t('plugins.accessReduced'),
        }));
        const dependencyChanges = [
            ...diff.dependencies.added,
            ...diff.dependencies.removed,
            ...diff.dependencies.changed,
        ];
        if (dependencyChanges.length) items.push({
            name: t('plugins.dependencies'),
            version: dependencyChanges.map((item) => item.plugin_id).join(', '),
            status: t('plugins.contractChanged'),
        });
        if (diff.entrypoints.changed) items.push({
            name: t('plugins.entrypoints'),
            version: JSON.stringify(diff.entrypoints.to),
            status: t('plugins.contractChanged'),
        });
        if (diff.python_dependencies.changed) items.push({
            name: t('plugins.pythonDependencies'),
            version: diff.python_dependencies.to.join(', ') || t('plugins.none'),
            status: t('plugins.environmentRebuilt'),
        });
        return items;
    }

    function requestUpdate(plugin) {
        showConfirmation({
            title: t('plugins.updateTitle', { name: plugin.name }),
            description: t('plugins.updateConfirm'),
            items: updateReviewItems(plugin),
            acceptLabel: t('plugins.updateAndActivate'),
            action: async () => {
                const candidate = plugin.curated;
                await api.updateCuratedPlugin(
                    plugin.plugin_id, candidate.manifest.version, candidate.sha256,
                );
                return { restart: true };
            },
        });
    }

    function removeInstallation(plugin, installation) {
        const manifest = installation.manifest;
        showConfirmation({
            title: t('plugins.removeTitle', { name: manifest.name }),
            description: t('plugins.removeConfirm', { name: manifest.name }),
            items: [{
                name: manifest.name,
                version: `${manifest.version} · ${shortHash(installation.sha256)}`,
                status: t(installation.active ? 'plugins.removeActive' : 'plugins.removeCached'),
                danger: true,
            }],
            acceptLabel: t('plugins.remove'),
            danger: true,
            action: async () => {
                const result = await api.uninstallPlugin(
                    manifest.plugin_id, manifest.version, installation.sha256,
                );
                return { restart: result.restart, messageKey: 'plugins.removed' };
            },
        });
    }

    async function activateInstallation(installation, button) {
        button.disabled = true;
        try {
            await api.activatePlugin(installation.manifest.plugin_id, {
                version: installation.manifest.version,
                sha256: installation.sha256,
            });
            notify(t('plugins.restarting'), 'success', 6000);
            setTimeout(() => window.location.reload(), 1400);
        } catch (error) {
            notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
            button.disabled = false;
        }
    }

    function cachedVersionRow(plugin, installation) {
        const row = document.createElement('div');
        row.className = `plugin-version-row ${installation.active ? 'active' : ''}`;
        const version = document.createElement('code');
        version.textContent = `${installation.manifest.version} #${shortHash(installation.sha256)}`;
        const status = document.createElement('span');
        status.textContent = t(installation.active ? 'plugins.activeVersion' : 'plugins.cachedVersion');
        const actions = document.createElement('div');
        if (!installation.active) {
            const activate = document.createElement('button');
            activate.className = 'btn btn-mini';
            activate.textContent = t('plugins.reactivate');
            activate.addEventListener('click', () => activateInstallation(installation, activate));
            actions.append(activate);
        }
        const remove = document.createElement('button');
        remove.className = 'btn btn-mini btn-danger-ghost';
        remove.textContent = t('plugins.remove');
        remove.addEventListener('click', () => removeInstallation(plugin, installation));
        actions.append(remove);
        row.append(version, status, actions);
        return row;
    }

    /* ── Generic plugin-config UI (contracts.SETTINGS) ───────────────────
     * Renders whatever a plugin declares via context.contribute('settings', ...);
     * no plugin-ID branch here or anywhere else in this file. */
    function pluginSettingField(pluginId, field, config) {
        const row = document.createElement('label');
        row.className = 'toggle plugin-setting-toggle';
        const inputId = `plugin-setting-${pluginId}-${field.key}`;
        row.setAttribute('for', inputId);
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.id = inputId;
        input.checked = Boolean(field.key in config ? config[field.key] : field.default);
        const track = document.createElement('span');
        track.className = 'toggle-track';
        const thumb = document.createElement('span');
        thumb.className = 'toggle-thumb';
        track.append(thumb);
        const copy = document.createElement('span');
        copy.className = 'plugin-setting-copy';
        const locale = getLocale();
        copy.textContent = field.label[locale] || field.label.en;
        row.append(input, track, copy);
        input.addEventListener('change', async () => {
            const next = { ...config, [field.key]: input.checked };
            input.disabled = true;
            try {
                await api.putPluginConfig(pluginId, next);
                config[field.key] = input.checked;
            } catch (error) {
                input.checked = !input.checked;
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
            } finally {
                input.disabled = false;
            }
        });
        return row;
    }

    function pluginSettingsForm(pluginId, descriptor, config) {
        const booleanFields = descriptor.fields.filter((field) => field.type === 'boolean');
        if (!booleanFields.length) return null;
        const form = document.createElement('div');
        form.className = 'plugin-settings';
        const heading = document.createElement('h5');
        heading.textContent = t('plugins.settingsTitle');
        form.append(heading, ...booleanFields.map((field) => pluginSettingField(pluginId, field, config)));
        return form;
    }

    function pluginCard(plugin, settingsDescriptors = new Map(), settingsConfigs = new Map()) {
        const primary = plugin.active || plugin.cached_versions[0];
        const manifest = primary.manifest;
        const hasUpdate = plugin.state === 'update_available';
        const card = document.createElement('article');
        card.className = `plugin-card plugin-card-group ${plugin.active ? 'active' : ''} ${hasUpdate ? 'has-update' : ''}`;
        const header = document.createElement('div');
        header.className = 'plugin-card-main';
        const copy = document.createElement('div');
        const titleRow = document.createElement('div');
        titleRow.className = 'plugin-title-row';
        const title = document.createElement('h4');
        title.textContent = manifest.name;
        titleRow.append(title);
        if (hasUpdate) {
            const badge = document.createElement('span');
            badge.className = 'plugin-update-badge';
            badge.textContent = t('plugins.updateAvailable');
            titleRow.append(badge);
        } else if (plugin.state === 'release_conflict') {
            const badge = document.createElement('span');
            badge.className = 'plugin-update-badge conflict';
            badge.textContent = t('plugins.releaseConflict');
            titleRow.append(badge);
        }
        const metadata = document.createElement('span');
        metadata.className = 'plugin-meta';
        metadata.textContent = `${manifest.version} · ${manifest.license} · #${shortHash(primary.sha256)}`;
        const description = document.createElement('p');
        description.textContent = manifest.description;
        copy.append(titleRow, metadata, description, permissionBadges(manifest));
        const actions = document.createElement('div');
        actions.className = 'plugin-card-actions';
        if (hasUpdate) {
            const update = document.createElement('button');
            update.className = 'btn btn-primary';
            update.textContent = t('plugins.updateAndActivate');
            update.addEventListener('click', () => requestUpdate(plugin));
            actions.append(update);
        }
        if (plugin.active) {
            const deactivate = document.createElement('button');
            deactivate.className = 'btn btn-mini';
            deactivate.textContent = t('plugins.deactivate');
            deactivate.addEventListener('click', async () => {
                deactivate.disabled = true;
                try {
                    await api.deactivatePlugin(plugin.plugin_id);
                    notify(t('plugins.restarting'), 'success', 6000);
                    setTimeout(() => window.location.reload(), 1400);
                } catch (error) {
                    notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
                    deactivate.disabled = false;
                }
            });
            actions.append(deactivate);
        } else {
            const activate = document.createElement('button');
            activate.className = 'btn btn-primary';
            activate.textContent = t('plugins.activate');
            activate.addEventListener('click', () => activateInstallation(primary, activate));
            actions.append(activate);
        }
        header.append(copy, actions);
        card.append(header);
        if (plugin.curated && hasUpdate) {
            const rail = document.createElement('div');
            rail.className = 'plugin-release-rail';
            const fromVersion = document.createElement('span');
            fromVersion.textContent = manifest.version;
            const line = document.createElement('i');
            line.setAttribute('aria-hidden', 'true');
            const toVersion = document.createElement('strong');
            toVersion.textContent = plugin.curated.manifest.version;
            rail.append(fromVersion, line, toVersion);
            card.append(rail);
        }
        const details = document.createElement('details');
        details.className = 'plugin-version-history';
        const summary = document.createElement('summary');
        summary.textContent = t('plugins.cachedVersions', { count: plugin.cached_versions.length });
        const rows = document.createElement('div');
        rows.className = 'plugin-version-list';
        rows.append(...plugin.cached_versions.map((item) => cachedVersionRow(plugin, item)));
        details.append(summary, rows);
        card.append(details);
        if (plugin.active && settingsDescriptors.has(plugin.plugin_id)) {
            const form = pluginSettingsForm(
                plugin.plugin_id,
                settingsDescriptors.get(plugin.plugin_id),
                settingsConfigs.get(plugin.plugin_id) || {},
            );
            if (form) card.append(form);
        }
        return card;
    }

    function catalogCard(plugin) {
        const release = plugin.curated;
        const manifest = release.manifest;
        const card = document.createElement('article');
        card.className = 'plugin-card';
        const copy = document.createElement('div');
        const title = document.createElement('h4');
        title.textContent = manifest.name;
        const metadata = document.createElement('span');
        metadata.className = 'plugin-meta';
        metadata.textContent = `${manifest.version} · ${manifest.license}`;
        const description = document.createElement('p');
        description.textContent = manifest.description;
        copy.append(title, metadata, description);
        const button = document.createElement('button');
        button.className = 'btn btn-primary';
        button.textContent = t('plugins.install');
        button.addEventListener('click', () => {
            showConfirmation({
                title: t('plugins.installTitle', { name: manifest.name }),
                description: t('plugins.curatedInstallConfirm'),
                items: installationReviewItems(manifest, release.sha256),
                acceptLabel: t('plugins.confirmInstall'),
                action: async () => {
                    await api.installCuratedPlugin(plugin.plugin_id, manifest.version);
                    return { restart: false, messageKey: 'plugins.installed' };
                },
            });
        });
        card.append(copy, button);
        return card;
    }

    async function refresh() {
        // Catalog synchronization materializes curated Experiences and validates artifact manifests.
        const catalog = await api.getPluginCatalog();
        const [experiences, status, events] = await Promise.all([
            api.listExperiences(), api.getPlugins(), api.getPluginEvents(),
        ]);
        const cachedKeys = new Set(status.plugins.flatMap((plugin) => (
            plugin.cached_versions.map((item) => (
                `${item.manifest.plugin_id}@${item.manifest.version}`
            ))
        )));
        if (experiences.length) {
            experienceGrid.replaceChildren(...experiences.map((experience) => (
                experienceCard(experience, catalog.plugins, cachedKeys, experienceIsActive(experience, status.plugins))
            )));
        } else empty(experienceGrid, 'plugins.noExperiences');
        const available = status.plugins.filter((plugin) => plugin.state === 'not_installed');
        if (available.length) {
            catalogStack.replaceChildren(...available.map(catalogCard));
        } else empty(catalogStack, 'plugins.noNewCatalog');
        const installed = status.plugins.filter((plugin) => plugin.cached_versions.length);
        if (installed.length) {
            const settingsDescriptors = new Map();
            (status.contributions.settings || []).forEach((item) => {
                if (!settingsDescriptors.has(item.plugin_id)) {
                    settingsDescriptors.set(item.plugin_id, item.value);
                }
            });
            const activeWithSettings = installed.filter((plugin) => (
                plugin.active && settingsDescriptors.has(plugin.plugin_id)
            ));
            const settingsConfigs = new Map(await Promise.all(activeWithSettings.map(async (plugin) => (
                [plugin.plugin_id, await api.getPluginConfig(plugin.plugin_id)]
            ))));
            pluginStack.replaceChildren(...installed.map((plugin) => (
                pluginCard(plugin, settingsDescriptors, settingsConfigs)
            )));
        } else empty(pluginStack, 'plugins.noPlugins');
        const updates = installed.filter((plugin) => plugin.state === 'update_available').length;
        updateCount.hidden = updates === 0;
        updateCount.textContent = String(updates);
        updateCount.setAttribute('aria-label', t('plugins.updateCount', { count: updates }));
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

    function trackPosition(index, offset = 0) {
        track.style.transform = `translate3d(calc(${-index * 100}% + ${offset}px), 0, 0)`;
    }

    function selectTab(name, { focus = false, animate = true } = {}) {
        const index = tabNames.indexOf(name);
        if (index < 0) return;
        activeTab = index;
        track.classList.toggle('no-transition', !animate || reducedMotion.matches);
        trackPosition(index);
        tabs.forEach((tab, tabIndex) => {
            const selected = tabIndex === index;
            tab.classList.toggle('active', selected);
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
            if (selected && focus) tab.focus({ preventScroll: true });
        });
        views.forEach((view, viewIndex) => {
            const selected = viewIndex === index;
            view.classList.toggle('active', selected);
            view.toggleAttribute('inert', !selected);
            view.setAttribute('aria-hidden', String(!selected));
        });
        requestAnimationFrame(() => track.classList.remove('no-transition'));
    }

    function ignoredGestureTarget(target) {
        return target.closest('button, a, input, select, textarea, summary, [role="alertdialog"]');
    }

    function finishGesture(event, cancelled = false) {
        if (!gesture || event.pointerId !== gesture.pointerId) return;
        const width = track.parentElement.clientWidth || 1;
        const elapsed = Math.max(performance.now() - gesture.startedAt, 1);
        const velocity = gesture.dx / elapsed;
        let next = activeTab;
        if (!cancelled && gesture.horizontal
            && (Math.abs(gesture.dx) >= width * 0.25 || Math.abs(velocity) >= 0.5)) {
            next += gesture.dx < 0 ? 1 : -1;
        }
        next = Math.max(0, Math.min(tabNames.length - 1, next));
        track.classList.remove('dragging');
        gesture = null;
        selectTab(tabNames[next], { focus: false, animate: true });
    }

    function initGestures() {
        track.addEventListener('pointerdown', (event) => {
            if (!['touch', 'pen'].includes(event.pointerType)
                || ignoredGestureTarget(event.target) || !confirmLayer.hidden) return;
            gesture = {
                pointerId: event.pointerId,
                x: event.clientX,
                y: event.clientY,
                dx: 0,
                horizontal: false,
                startedAt: performance.now(),
            };
            track.setPointerCapture(event.pointerId);
        });
        track.addEventListener('pointermove', (event) => {
            if (!gesture || event.pointerId !== gesture.pointerId) return;
            const dx = event.clientX - gesture.x;
            const dy = event.clientY - gesture.y;
            if (!gesture.horizontal && Math.hypot(dx, dy) < 10) return;
            if (!gesture.horizontal && Math.abs(dy) >= Math.abs(dx)) {
                finishGesture(event, true);
                return;
            }
            gesture.horizontal = true;
            gesture.dx = dx;
            event.preventDefault();
            let offset = dx;
            if ((activeTab === 0 && dx > 0) || (activeTab === tabNames.length - 1 && dx < 0)) {
                offset *= 0.28;
            }
            track.classList.add('dragging');
            trackPosition(activeTab, offset);
        });
        track.addEventListener('pointerup', (event) => finishGesture(event));
        track.addEventListener('pointercancel', (event) => finishGesture(event, true));
    }

    function init(options = {}) {
        notify = options.notify || notify;
        selectTab(tabNames[0], { animate: false });
        openBtn.addEventListener('click', open);
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
            if (event.key === 'Escape' && overlay.classList.contains('active')) {
                event.preventDefault();
                if (!confirmLayer.hidden) hideConfirmation();
                else overlay.classList.remove('active');
                return;
            }
            if (!tabs.includes(document.activeElement)) return;
            const navigation = {
                ArrowLeft: activeTab - 1,
                ArrowRight: activeTab + 1,
                Home: 0,
                End: tabNames.length - 1,
            }[event.key];
            if (navigation === undefined) return;
            event.preventDefault();
            const index = Math.max(0, Math.min(tabNames.length - 1, navigation));
            selectTab(tabNames[index], { focus: true });
        });
        tabs.forEach((tab) => {
            tab.addEventListener('click', () => selectTab(tab.dataset.pluginTab));
        });
        initGestures();
        installBtn.addEventListener('click', async () => {
            const file = zipPath.files?.[0];
            if (!file) return;
            installBtn.disabled = true;
            try {
                const inspected = await api.inspectPluginFile(file);
                const manifest = inspected.manifest;
                showConfirmation({
                    title: t('plugins.installTitle', { name: manifest.name }),
                    description: t('plugins.externalInstallConfirm'),
                    items: installationReviewItems(manifest, inspected.sha256, { external: true }),
                    acceptLabel: t('plugins.confirmExternalInstall'),
                    action: async () => {
                        const installed = await api.installPluginFile(file);
                        if (installed.sha256 !== inspected.sha256) {
                            throw new Error(t('plugins.fileChanged'));
                        }
                        zipPath.value = '';
                        return { restart: false, messageKey: 'plugins.installed' };
                    },
                });
            } catch (error) {
                notify(t('plugins.operationError', { error: error.message }), 'error', 6000);
            } finally { installBtn.disabled = false; }
        });
    }

    async function open() {
        overlay.classList.add('active');
        try { await refresh(); }
        catch (error) { notify(t('plugins.operationError', { error: error.message }), 'error'); }
    }

    return { init, refresh, open };
})();
