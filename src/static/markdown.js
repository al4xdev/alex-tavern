/* ══════════════════════════════════════════════════════════════════════
   markdown.js — the small Markdown subset the in-app guides are written in.

   Deliberately not a library: it serves seven help articles we write
   ourselves, and a dependency would cost more than it saves. It escapes < and
   > on every line first, so an article can never inject markup.
   ══════════════════════════════════════════════════════════════════════ */

/** Bold and links, inside a line that is already HTML-escaped. */
export function parseInlineMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
}

/** Headings, bullet lists and paragraphs. Everything else renders as text. */
export function parseMarkdown(text) {
    const lines = text.split('\n');
    let inList = false;
    const result = [];

    for (const rawLine of lines) {
        const line = rawLine.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const trimmed = line.trim();

        if (trimmed.startsWith('- ')) {
            if (!inList) {
                result.push('<ul>');
                inList = true;
            }
            result.push(`<li>${parseInlineMarkdown(trimmed.substring(2))}</li>`);
            continue;
        }

        if (inList) {
            result.push('</ul>');
            inList = false;
        }

        if (trimmed.startsWith('### ')) {
            result.push(`<h3>${parseInlineMarkdown(trimmed.substring(4))}</h3>`);
        } else if (trimmed.startsWith('## ')) {
            result.push(`<h2>${parseInlineMarkdown(trimmed.substring(3))}</h2>`);
        } else if (trimmed.startsWith('# ')) {
            result.push(`<h1>${parseInlineMarkdown(trimmed.substring(2))}</h1>`);
        } else if (trimmed.length > 0) {
            result.push(`<p>${parseInlineMarkdown(line)}</p>`);
        }
    }

    if (inList) result.push('</ul>');
    return result.join('\n');
}
