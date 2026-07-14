# Task 12 closure: Character Converter

**Status:** Completed on 2026-07-14

## Delivered scope

The source, deterministic artifact, and catalog entry for
`dev.alex-tavern.character-converter` version `1.0.0` live in the sibling curated hub checkout.
The plugin registers `/convert-character <preset-name>` and accepts exactly one of:

- an unstructured character description;
- an open Character Card V1/V2/V3 JSON;
- an open Character Card V1/V2/V3 PNG with `ccv3` or `chara` metadata.

The pure-stdlib PNG reader checks signature, bounds, every chunk CRC, final IEND, strict Base64,
UTF-8 JSON, and prefers `ccv3`. Ordinary avatar PNGs and unsupported JPEG/WebP/ZIP/CHARX inputs
produce novice-readable errors. No vision and no RAG were added.

Card content is quoted as untrusted data for the active structured model provider. Output uses the
canonical `mind`/`body` schema with matching names, third-person factual prose, and no User/Player,
Markdown, or roleplay stage directions. One correction call is permitted after semantic validation.
The result is an editable `character_preset_draft`; the plugin never writes a preset.

## Curated release preparation

- MCP scaffold, live core contract, validate, test, and pack flows were used.
- Eight plugin-local tests cover V1/V2/V3, `ccv3` precedence, ordinary PNG, CRC failure, exact-one
  input, semantic correction, and provider failure.
- Artifact: `artifacts/character-converter-1.0.0.zip`
- SHA-256: `55923fc6c5de0caae4c3d3e01f82e2bcc0e38306700fe6f712511bed445c4b06`
- Hub check passes with three plugins and one Experience.

No commit, push, remote mutation, or publication was performed.
