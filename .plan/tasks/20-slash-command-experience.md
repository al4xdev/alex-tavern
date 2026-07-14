## Existing Plugin Migration

This task must review every currently published plugin in the public repository
and evaluate how each one should integrate with the redesigned slash experience.

The goal is not only to update the plugins, but also to validate whether the new
slash API is expressive enough for real-world extensions.

Each plugin should be reviewed and, where appropriate:

- expose slash commands;
- expose contextual actions;
- provide autocomplete metadata;
- provide discoverable descriptions;
- contribute contextual suggestions;
- validate that the SDK exposes all required extension points.

Current public plugins should serve as the primary validation suite for the
slash API.

If multiple plugins require the same workaround or custom implementation, that
should be considered evidence that the SDK is missing an abstraction and should
be improved instead of duplicating logic.

The final implementation should require little or no plugin-specific special
cases.

The migration should document any SDK improvements discovered during the review.
