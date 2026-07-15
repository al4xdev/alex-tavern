# 💬 Shortcuts & Features

Use these tools to control the flow of the narrative:
- 💡 **Suggestion**: Ask the AI to suggest a next move for your character.
- 📜 **Narrator Hint**: Force an upcoming event or environmental detail.
- ↩ **Undo**: Revert the last complete turn (both player input and NPC reaction).
- ⏭ **Skip**: Skip your turn, allowing the Narrator to progress the scene or NPCs to interact.

## Slash commands

Type `/` in the **Speech** field to open the palette. The typed slash becomes the violet sigil beside
the field, so the command query stays clean. It includes Alex Tavern actions and contributions from
active plugins. Keep typing to narrow the list, use ↑/↓ to choose, Tab to complete the canonical
name, and Enter to activate. Backend tools open a clearly bordered card showing every input they
need.

Useful built-ins include `/help`, `/plugins`, `/settings`, `/sessions`, `/new`, `/suggest`, `/hint`,
`/undo`, `/skip`, `/compact`, and `/restore`. Unavailable actions stay visible and explain what is
missing. Plugin tools and actions show their origin.

Commands are utilities, not character dialogue. Their input goes directly to the selected tool and
does not create a story turn, call the Narrator, change undo history, or appear in the chat. A wrong
command is stopped with an explanation instead of being sent as speech.

To make your character literally say something beginning with `/`, type `//`. The second slash
closes the palette and sigil immediately, leaving one literal slash in the speech field.

## Character Converter

When the curated **Character Converter** plugin is active, use:

`/convert-character`

Enter the preset name in the visible field. Then either paste one description or select one open
Character Card V1/V2/V3 PNG/JSON. Do not fill
both sources. An ordinary avatar PNG has no card definition and will be rejected clearly. The tool
does not infer a character from image pixels.

The result opens as an editable character preset draft. Review the name, personality, knowledge,
appearance, outfit, mood, and optional avatar before pressing **Save preset**. Existing preset names
always ask before replacement.
