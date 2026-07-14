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

COMMANDS = {
    "registration": "context.command(descriptor, handler)",
    "scope": "session-bound utility; cannot mutate GameState in schema_version 1",
    "descriptor": {
        "required": ["name", "summary", "usage", "arguments", "fields", "result_kind"],
        "locales": ["en", "pt-BR"],
        "field_types": ["text", "textarea", "file"],
    },
    "handler": {
        "arguments": ["normalized_payload", "command_context"],
        "context": ["game", "turn_number", "runner", "operation_id"],
        "result": "JSON object",
    },
}


def exported_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "hooks": HOOK_CONTRACTS,
        "contribution_slots": CONTRIBUTION_SLOTS,
        "services": SERVICES,
        "commands": COMMANDS,
        "permissions": PERMISSIONS,
        "crash_policy": {
            "before_commit": "discard plugin draft, disable plugin for boot, continue clean",
            "after_commit": "record and disable plugin; never retry committed work",
        },
    }
