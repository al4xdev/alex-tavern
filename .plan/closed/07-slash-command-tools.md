# Task 07 closure: General slash-command tool system

**Status:** Completed on 2026-07-14

## Delivered contract

- Active backend plugins register executable utilities through strict
  `context.command(descriptor, handler)` descriptors.
- Command names are globally unique. Invalid descriptors and collisions disable the offending
  plugin for that boot and remove its partial registrations.
- `GET /commands` exposes localized discovery metadata. A session-bound POST endpoint validates
  arguments, fields, Base64 files, file sizes, and handler JSON output.
- Commands share the session lock but receive an isolated `GameState`; version 1 cannot create a
  turn, advance revision/history, call role agents implicitly, or participate in undo.
- Debug JSONL contains operation/plugin/version identity and normalized sizes, never uploaded
  Base64 or the full result draft.
- The Speech field owns `/` autocomplete, listbox keyboard/pointer operation, clear unknown-command
  errors, generic descriptor-driven forms, and `//` literal-slash escaping.
- `/commands`, command execution, and presets are network-only service-worker routes.

## Validation

- Registry collision, invalid input, non-mutation, log redaction, and session locking tests.
- All frontend modules pass Node parsing and the architecture/i18n suite.
- A real Uvicorn boundary loaded the packaged Character Converter, discovered the command, called
  a replay LLM through the shared provider, and confirmed history/revision remained unchanged.

RAG remains deferred under Task 06. It can later use this delivered command boundary without
changing the Narrator/Character turn pipeline.
