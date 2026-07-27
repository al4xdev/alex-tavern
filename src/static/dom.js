/* ══════════════════════════════════════════════════════════════════════
   dom.js — one element lookup that fails loudly.

   Every module resolves its own DOM references at import time, before any
   of them is used. `document.getElementById` answers null for a typo, so
   the failure surfaced later and elsewhere: a listener silently never
   registered, or a `Cannot read properties of null` from a line that had
   nothing to do with the mistake.

   `el(id)` throws at import with the id in the message, which is where the
   mistake is. Use `optional(id)` for the rare element that genuinely may
   not be in the document.
   ══════════════════════════════════════════════════════════════════════ */

/**
 * The element with this id. Throws if the document does not have it.
 * @param {string} id
 * @returns {HTMLElement}
 */
export function el(id) {
    const found = document.getElementById(id);
    if (found === null) {
        throw new Error(`dom.el: no element with id "${id}" in index.html`);
    }
    return found;
}

/**
 * The element with this id, or null when it is legitimately absent.
 * @param {string} id
 * @returns {HTMLElement|null}
 */
export function optional(id) {
    return document.getElementById(id);
}
