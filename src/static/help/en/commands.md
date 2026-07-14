# 💬 Shortcuts & Features

Use these tools to control the flow of the narrative:
- 💡 **Suggestion**: Ask the AI to suggest a next move for your character.
- 📜 **Narrator Hint**: Force an upcoming event or environmental detail.
- ↩ **Undo**: Revert the last complete turn (both player input and NPC reaction).
- ⏭ **Skip**: Skip your turn, allowing the Narrator to progress the scene or NPCs to interact.

## Slash commands

Type `/` in the **Speech** field to see the tools provided by active plugins. Keep typing to narrow
the list, use ↑/↓ to choose, and press Enter or Tab to complete the command. A recognized command
opens a clearly bordered tool card with the fields it needs.

Commands are utilities, not character dialogue. Their input goes directly to the selected tool and
does not create a story turn, call the Narrator, change undo history, or appear in the chat. A wrong
command is stopped with an explanation instead of being sent as speech.

To make your character literally say something beginning with `/`, type `//`. The first slash is
treated as an escape and only one slash is sent to the story.

## Character Converter

When the curated **Character Converter** plugin is active, use:

`/convert-character lyra-nightfall`

Then either paste one description or select one open Character Card V1/V2/V3 PNG/JSON. Do not fill
both sources. An ordinary avatar PNG has no card definition and will be rejected clearly. The tool
does not infer a character from image pixels.

The result opens as an editable character preset draft. Review the name, personality, knowledge,
appearance, outfit, mood, and optional avatar before pressing **Save preset**. Existing preset names
always ask before replacement.
