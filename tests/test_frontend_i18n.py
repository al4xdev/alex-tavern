"""Behavior and integration checks for the dependency-free frontend i18n module."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "static"


def run_node(script: str) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    subprocess.run(
        [node, "--no-warnings", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_locale_detection_translation_and_safe_fallback() -> None:
    run_node(
        r"""
        const m = await import('./src/static/i18n.js');
        const assert = (value, message) => { if (!value) throw new Error(message); };
        assert(m.i18nConfig.DEFAULT_LOCALE === 'en', 'English must be the default');
        assert(m.detectLocale(['pt-PT']) === 'pt-BR', 'Portuguese variants must map to pt-BR');
        assert(m.detectLocale(['fr-FR', 'en-GB']) === 'en', 'the first supported locale wins');
        assert(m.detectLocale(['fr-FR']) === 'en', 'unsupported locales must fall back to English');
        assert(m.getLlmLanguage('en') === 'English', 'English LLM language');
        assert(m.getLlmLanguage('pt-PT') === 'Brazilian Portuguese', 'Portuguese LLM language');
        assert(m.t('validation.characterName', {id: 'C2'}, 'pt-BR').includes('C2'), 'params');
        assert(m.t('provider.timeout', {}, 'pt-BR') === 'Timeout (s)', 'catalog fallback');
        assert(m.t('missing.raw.key', {}, 'pt-BR') === '', 'raw keys must never be displayed');
        assert(Object.keys(m.catalogs.en).length > Object.keys(m.catalogs['pt-BR']).length,
               'the Portuguese catalog should exercise runtime fallback');
        """,
    )


def test_selection_persists_and_retranslates_without_changing_input_value() -> None:
    run_node(
        """
        const m = await import('./src/static/i18n.js');
        const writes = [];
        globalThis.localStorage = {
            getItem: () => null,
            setItem: (key, value) => writes.push([key, value]),
        };
        const attributes = {};
        const element = {
            dataset: {i18n: 'setup.title', i18nPlaceholder: 'input.speech'},
            textContent: '', placeholder: '', value: 'unsaved player text',
            setAttribute: (key, value) => { attributes[key] = value; },
        };
        globalThis.document = {
            documentElement: {lang: ''},
            querySelectorAll: () => [element],
        };
        let notifications = 0;
        m.onLocaleChange(() => { notifications += 1; });
        m.setLocale('pt-BR');
        if (element.textContent !== 'Configurar aventura')
            throw new Error('text was not translated');
        if (element.placeholder !== '💬 Fala...') throw new Error('placeholder was not translated');
        if (element.value !== 'unsaved player text') throw new Error('input value changed');
        if (document.documentElement.lang !== 'pt-BR')
            throw new Error('document lang was not updated');
        if (writes.at(-1).join(':') !== 'rpt_interface_locale_v1:pt-BR')
            throw new Error('not persisted');
        m.setLocale('pt-BR');
        if (notifications !== 2 || element.value !== 'unsaved player text')
            throw new Error('not idempotent');
        """,
    )


def test_saved_locale_wins_over_browser_locale_on_startup() -> None:
    run_node(
        """
        globalThis.localStorage = {getItem: () => 'en', setItem: () => {}};
        Object.defineProperty(globalThis, 'navigator', {
            value: {languages: ['pt-BR']}, configurable: true,
        });
        const m = await import('./src/static/i18n.js?startup-test');
        if (m.getLocale() !== 'en') throw new Error('saved locale did not win');
        """,
    )


def test_setup_and_app_dynamic_messages_use_catalog_keys() -> None:
    setup = (STATIC / "setup.js").read_text(encoding="utf-8")
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    catalog = (STATIC / "i18n.js").read_text(encoding="utf-8")

    assert "t('presets.saved', { name })" in setup
    assert "'presets.saved':" in catalog
    assert "t('sessions.loaded', { id: sessionId })" in app
    assert "'sessions.loaded':" in catalog


def test_every_referenced_translation_key_exists_in_english_catalog() -> None:
    run_node(
        r"""
        import fs from 'node:fs';
        const {catalogs} = await import('./src/static/i18n.js');
        const files = [
            'index.html', 'app.js', 'setup.js', 'runtime-config.js',
            'adapters/base.js', 'adapters/llama-cpp.js', 'adapters/deepseek.js',
        ];
        const patterns = [
            /data-i18n(?:-[a-z-]+)?=["']([^"']+)["']/g,
            /\bt\(\s*["']([^"']+)["']/g,
            /bindTranslation\([^,]+,\s*["']([^"']+)["']/g,
            /(?:setError|showError)\(\s*["']([^"']+)["']/g,
            /return\s+\{\s*key:\s*["']([^"']+)["']/g,
            /(?:labelKey|descriptionKey|hintKey|placeholderKey|textKey):\s*["']([^"']+)["']/g,
        ];
        const missing = [];
        for (const file of files) {
            const source = fs.readFileSync(`src/static/${file}`, 'utf8');
            for (const pattern of patterns) {
                for (const match of source.matchAll(pattern)) {
                    if (match[1].includes('.') && !(match[1] in catalogs.en)) {
                        missing.push(`${file}:${match[1]}`);
                    }
                }
            }
        }
        if (missing.length) throw new Error(`Missing English keys: ${missing.join(', ')}`);
        """,
    )
