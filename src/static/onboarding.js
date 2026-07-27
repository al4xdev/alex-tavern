/* ══════════════════════════════════════════════════════════════════════
   onboarding.js — help drawer, in-app guides, tip banner, version check.

   Everything that talks ABOUT the app rather than playing it.
   ══════════════════════════════════════════════════════════════════════ */

import { el } from './dom.js';
import { api } from './api.js';
import { getLocale, t } from './i18n.js';
import { parseMarkdown } from './markdown.js';

// Where the update check looks. One constant, not a URL buried in a function.
const REPO_URL = 'https://github.com/al4xdev/alex-tavern';
const REPO_COMMITS_API = 'https://api.github.com/repos/al4xdev/alex-tavern/commits/master';

let deps = null;

/**
 * @param {object} options
 * @param {(on: boolean) => void} options.setDebug closes the debug drawer when help opens
 * @param {(message: string, type?: string, ms?: number) => void} options.notify shared toast
 */
export function init(options) {
    deps = options;
    const drawer = el('help-drawer');
    const brand = el('brand-header');
    const closeBtn = el('help-close-btn');
    const backBtn = el('help-back-btn');
    const banner = el('tip-banner');
    const bannerClose = el('tip-close-btn');

    brand.addEventListener('click', () => setHelp(!drawer.classList.contains('active')));
    brand.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setHelp(!drawer.classList.contains('active'));
        }
    });
    closeBtn.addEventListener('click', () => setHelp(false));
    backBtn.addEventListener('click', showHelpMenu);
    document.querySelectorAll('.help-menu-list li').forEach((li) => {
        li.addEventListener('click', () => showHelpArticle(li.dataset.helpTopic));
    });

    banner.addEventListener('click', (e) => {
        if (e.target.closest('#tip-close-btn')) return;
        const path = banner.dataset.helpPath;
        if (path) {
            setHelp(true);
            showHelpArticle(path);
        }
    });
    bannerClose.addEventListener('click', (e) => {
        e.stopPropagation();
        banner.style.display = 'none';
    });
}

export function setHelp(on) {
    const drawer = el('help-drawer');
    drawer.classList.toggle('active', on);
    if (on) {
        deps.setDebug(false);
        showHelpMenu();
    }
}

function showHelpMenu() {
    const menu = el('help-menu-view');
    menu.classList.add('active');
    menu.classList.remove('active-left');
    el('help-article-view').classList.remove('active');
}

export async function showHelpArticle(topic) {
    const content = el('help-article-content');
    el('help-menu-view').classList.add('active-left');
    el('help-article-view').classList.add('active');
    content.textContent = t('help.loading');

    const locale = getLocale() || 'en';
    try {
        let res = await fetch(`help/${locale}/${topic}.md`);
        if (!res.ok) res = await fetch(`help/en/${topic}.md`); // fall back to English
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        content.innerHTML = parseMarkdown(await res.text());
    } catch (err) {
        content.textContent = t('help.loadFailed', { error: err.message });
    }
}

/** Show one random usage warning, linked to the guide that explains it. */
export async function showTipBanner() {
    const banner = el('tip-banner');
    try {
        const res = await fetch('help/warning.json');
        if (!res.ok) throw new Error();
        const warnings = await res.json();
        if (!warnings || warnings.length === 0) return;
        const tip = warnings[Math.floor(Math.random() * warnings.length)];

        const text = el('tip-text');
        text.setAttribute('data-i18n', tip.text_key);
        text.textContent = t(tip.text_key);
        banner.dataset.helpPath = tip.help_path;
        banner.style.display = 'flex';
    } catch {
        banner.style.display = 'none';
    }
}

/**
 * Warn when the running build is behind the published repository.
 *
 * Silent by design when offline, in debug mode, or on a build with no commit
 * stamp: this is a courtesy for people running from source, never an error.
 */
export async function checkVersionSync() {
    try {
        const local = await api.getVersion();
        if (local?.debug || !local?.commit || local.commit === 'unknown') return;

        const response = await fetch(REPO_COMMITS_API);
        if (!response.ok) return;
        const remote = await response.json();
        if (remote?.sha && remote.sha !== local.commit) {
            deps.notify(`${t('version.updateAvailable')} ${t('version.outOfSync', { url: REPO_URL })}`,
                'warning', 8000);
        }
    } catch {
        // No connectivity, rate limit, or no GitHub: nothing to tell the user.
    }
}
