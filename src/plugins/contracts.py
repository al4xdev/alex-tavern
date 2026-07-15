"""Machine-readable extension points exported to docs, tooling, and agent MCPs."""

from __future__ import annotations

from typing import Any

HOOK_CONTRACTS: dict[str, dict[str, Any]] = {
    "session.start": {
        "kind": "sync filter",
        "value": "session config dict",
        "context": ["runner"],
        "commit": "before",
        "description": "Rewrite complete session creation input before defaults are resolved.",
    },
    "session.before_commit": {
        "kind": "sync filter",
        "value": "GameState",
        "context": ["kind", "runner"],
        "commit": "before",
        "description": "Mutate a new session draft immediately before its first save.",
    },
    "session.after_commit": {
        "kind": "sync action",
        "value": "context only",
        "context": ["game", "kind"],
        "commit": "after",
        "description": "Observe a newly durable session.",
    },
    "narrator.call": {
        "kind": "wrapper",
        "value": "async Narrator operation",
        "context": ["game", "turn_number", "runner"],
        "commit": "before",
        "description": "Replace, surround, or bypass the complete Narrator call.",
    },
    "narrator.context": {
        "kind": "filter",
        "value": "list[str] of extra prompt lines",
        "context": ["game", "turn_number", "runner"],
        "commit": "before",
        "description": "Append read-only context lines to the Narrator's user prompt.",
    },
    "narrator.schema": {
        "kind": "filter",
        "value": "{'properties': dict, 'required': list[str]}",
        "context": ["game", "turn_number", "runner"],
        "commit": "before",
        "description": (
            "Extend the Narrator's JSON schema with an optional, plugin-owned property. "
            "Provider-independent — the property's own JSON Schema carries its semantics "
            "(e.g. a 'description'); pair it with narrator.context for prose guidance."
        ),
    },
    "narrator.result": {
        "kind": "filter",
        "value": "GameState (same-turn draft)",
        "context": ["narrator_output", "turn_number", "runner"],
        "commit": "before",
        "description": (
            "Validate and apply one plugin's own narrator.schema property to the turn draft. "
            "A plugin that finds its proposal invalid must return the draft unchanged (and may "
            "journal why) instead of raising — raising trips the shared crash policy and disables "
            "the plugin, which is reserved for genuine bugs, not routine LLM validation failures."
        ),
    },
    "character.call": {
        "kind": "wrapper",
        "value": "async Character operation",
        "context": ["game", "character_id", "turn_number", "runner"],
        "commit": "before",
        "description": "Replace, surround, or bypass the complete Character call.",
    },
    "turn.input": {
        "kind": "filter",
        "value": "dict",
        "context": ["game", "turn_number", "runner"],
        "commit": "before",
        "description": "Rewrite speech, thought, action, routing, hint, or skip.",
    },
    "narrator.output": {
        "kind": "filter",
        "value": "Narrator output dict",
        "context": ["game", "turn_number", "runner"],
        "commit": "before",
        "description": "Inspect or replace narration, routing, scene, and mood updates.",
    },
    "character.output": {
        "kind": "filter",
        "value": "CharacterOutput",
        "context": ["game", "character_id", "turn_number", "runner"],
        "commit": "before",
        "description": "Inspect or replace character speech and private thought.",
    },
    "turn.before_commit": {
        "kind": "filter",
        "value": "GameState",
        "context": ["kind", "runner"],
        "commit": "before",
        "description": "Last transactional mutation point; failed drafts are discarded.",
    },
    "turn.after_commit": {
        "kind": "action",
        "value": "context only",
        "context": ["game", "kind"],
        "commit": "after",
        "description": "Post-commit side effects; failures never replay the committed turn.",
    },
    "suggestions.output": {
        "kind": "filter",
        "value": "suggestion list",
        "context": ["game", "target_id", "runner"],
        "commit": "none",
        "description": "Inspect or replace move suggestions.",
    },
    "undo.before_commit": {
        "kind": "filter",
        "value": "GameState",
        "context": ["turn_number", "removed", "runner"],
        "commit": "before",
        "description": "Mutate the isolated state produced by undo before save.",
    },
    "undo.after_commit": {
        "kind": "action",
        "value": "context only",
        "context": ["game", "turn_number", "removed"],
        "commit": "after",
        "description": "Observe a durable undo.",
    },
    "compaction.before_commit": {
        "kind": "filter",
        "value": "CompactionDraft",
        "context": ["cutoff", "evicted", "runner"],
        "commit": "before",
        "description": "Mutate reversible history, summaries, notes, or plugin state.",
    },
    "compaction.after_commit": {
        "kind": "action",
        "value": "context only",
        "context": ["game", "cutoff", "evicted"],
        "commit": "after",
        "description": "Observe a durable compaction.",
    },
    "compaction.restore_after_commit": {
        "kind": "action",
        "value": "context only",
        "context": ["game", "result"],
        "commit": "after",
        "description": "Observe a successfully restored compaction backup.",
    },
    "compaction.undo_conflict": {
        "kind": "filter",
        "value": "plugin-owned state namespace",
        "context": ["paths", "checkpoint_id", "runner"],
        "commit": "before",
        "description": "Resolve later writes to paths changed by an undone compaction.",
    },
}

CONTRIBUTION_SLOTS = {
    "providers": "LLM provider descriptors backed by a registered ProviderAdapter",
    "routes": "HTTP route descriptors or unsafe host mutations",
    "settings": "Plugin-owned configuration UI",
    "panels": "Game-view panel definitions",
}

PERMISSIONS = {
    "config.read": "Read the plugin-owned configuration object",
    "config.write": "Replace the plugin-owned configuration object",
    "network": "Perform outbound HTTP requests",
    "model.call": "Call the active provider through the structured core model gateway",
    "session.state.write": "Mutate GameState and namespaced plugin_state",
    "provider.replace": "Register or replace an LLM provider adapter",
    "unsafe": "Reach or replace arbitrary runtime objects",
    "frontend.dom.mount": "Mount UI into a named frontend slot",
    "frontend.provider.register": "Register a browser-side provider adapter",
    "frontend.action.register": "Register a browser-side slash action",
    "frontend.command-renderer.register": "Render a plugin-namespaced command result",
}

SERVICES = {
    "model.call_json": {
        "kind": "async structured model call",
        "arguments": [
            "hook_context",
            "messages",
            "json_schema",
            "max_tokens",
            "use_configured_language",
        ],
        "requires_context": ["game", "turn_number", "runner"],
        "provider": "active provider through the shared client and ProviderAdapter",
        "agent": "plugin:<plugin_id>",
        "secrets": "never exposed to the plugin",
        "validation": "JSON Schema plus local validation and shared retries",
    }
}

SETTINGS = {
    "registration": "context.contribute('settings', descriptor)",
    "storage": "context.config.read()/.write() — one JSON object per plugin",
    "descriptor": {
        "required": ["fields"],
        "field": {
            "required": ["key", "type", "label", "default"],
            "types": ["boolean"],
            "locales": ["en", "pt-BR"],
        },
    },
    "defaults": "Materialized into the plugin's stored config the first time it activates.",
    "renderer": "Generic — the frontend renders any declared descriptor; no per-plugin branch.",
}

COMMANDS = {
    "registration": "context.command(descriptor, handler)",
    "schema_version": 2,
    "scope": (
        "session-bound utility; receives an isolated GameState and cannot mutate narrative state"
    ),
    "descriptor": {
        "required": [
            "name",
            "title",
            "summary",
            "icon",
            "aliases",
            "keywords",
            "inputs",
            "result_kind",
        ],
        "locales": ["en", "pt-BR"],
        "input_types": ["text", "textarea", "file"],
        "result_namespaces": ["core/*", "<plugin-id>/*"],
    },
    "handler": {
        "arguments": ["normalized_payload", "command_context"],
        "payload": {"values": "text and textarea inputs", "files": "decoded file inputs"},
        "context": ["game", "turn_number", "runner", "operation_id"],
        "result": "JSON object",
    },
}

FRONTEND_SLASH = {
    "actions": {
        "registration": "sdk.registerAction(descriptor, handler)",
        "descriptor": {
            "required": [
                "name",
                "title",
                "summary",
                "icon",
                "aliases",
                "keywords",
                "scope",
            ],
            "locales": ["en", "pt-BR"],
            "scopes": ["global", "session"],
        },
        "availability": "session actions require an open, idle session",
        "namespace": "names and aliases are shared with core actions and backend tools",
    },
    "command_result_renderers": {
        "registration": "sdk.registerCommandResultRenderer(kind, renderer)",
        "namespace": "kind must start with <plugin-id>/; core/* is reserved",
        "availability": "a backend tool without a renderer is disabled before execution",
    },
}


def exported_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "hooks": HOOK_CONTRACTS,
        "contribution_slots": CONTRIBUTION_SLOTS,
        "services": SERVICES,
        "settings": SETTINGS,
        "commands": COMMANDS,
        "frontend_slash": FRONTEND_SLASH,
        "permissions": PERMISSIONS,
        "crash_policy": {
            "before_commit": "discard plugin draft, disable plugin for boot, continue clean",
            "after_commit": "record and disable plugin; never retry committed work",
        },
    }
