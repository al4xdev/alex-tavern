"""Execute the actual suggestion renderer and selection handler in Node."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is required")
def test_selection_fills_all_fields_without_sending():
    composer = Path(__file__).resolve().parents[1] / "src/static/composer.js"
    script = r"""
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
function element() {
    const classes = new Set();
    return {
        children: [], style: {}, value: 'previous value', handlers: {},
        classList: {add: x => classes.add(x), remove: x => classes.delete(x)},
        appendChild(child) { this.children.push(child); },
        addEventListener(event, handler) { this.handlers[event] = handler; },
        focus() {},
        set innerHTML(value) { this.children = []; },
    };
}
const document = {createElement: () => element()};
const optionsPanel = element();
const inputSpeech = element(), inputThought = element(), inputAction = element();
const updateExpandPill = () => {};
const isCompactLayout = () => false;
const expandMobileInput = () => {throw new Error('unexpected mobile call');};
const bindTranslation = (el, key) => {el.textContent = key;};
const body = source.slice(source.indexOf('export function clearSuggestions()'),
                          source.indexOf('export async function suggestForMe()'))
                   .replaceAll('export ', '');
eval(body + `
    renderSuggestions([{speech: 'Oi', thought: 'Quero entender', action: 'examinar a porta'}]);
    assert.equal(optionsPanel.children.length, 1);
    assert.deepEqual(optionsPanel.children[0].children.map(c => c.textContent),
                     ['Oi', '💭 Quero entender', '🎬 examinar a porta']);
    optionsPanel.children[0].handlers.click();
    assert.deepEqual([inputSpeech.value, inputThought.value, inputAction.value],
                     ['Oi', 'Quero entender', 'examinar a porta']);
    assert.equal(optionsPanel.children.length, 0);
    renderSuggestions([{speech: '', thought: 'Preciso esperar', action: ''}]);
    optionsPanel.children[0].handlers.click();
    assert.deepEqual([inputSpeech.value, inputThought.value, inputAction.value],
                     ['', 'Preciso esperar', '']);
`);
"""
    subprocess.run(["node", "-e", script, str(composer)], check=True, capture_output=True)
