# Controlled translation check — preregistration

Objective: check translation fidelity using the shipped translation_request builder and the shared
client/adapter's actual provider payload. This is not an English-versus-Portuguese fiction A/B.

Use controlled texts only, never personal sessions. Two cases, Portuguese to English and English
to Portuguese, with four separate fields each: speech, private thought, attempted action and event.
Run each exact payload three times via curl against the configured DeepSeek Flash profile, in an
isolated temporary ROLEPLAY_DATA_DIR. Do not change the real provider configuration or session data.

Admission rule, set before calls: every run must satisfy the JSON schema, keep the four fields
separate, preserve names and the password exactly, preserve negation, uncertainty and the attempted
rather than completed action, and add no facts. Read every translation against its source. Any
violation rejects that prompt variant; adjust only the translation instruction and repeat all six
calls with the production builder. Transport errors are failures to measure, not evidence of fidelity.

Store redacted requests and raw provider responses here. Credentials must travel through curl's
standard input configuration, never command arguments or persisted files. An independent reader
will review the source/output pairs for fidelity. Report counts as controlled-call evidence only.

Variant 1 rejected: PT→EN run 1 translated the proper name “Portal de Âmbar” into “Amber Portal”.
The three PT→EN calls had one name-preservation violation; the three EN→PT calls had none on
manual reading. All six schemas were valid. This does not satisfy the admission rule.

Variant 2 adds an explicit instruction that full names of places, artifacts, spells and
organizations retain their source-language internal words. Repeat the same six calls with
the same admission rule and production builder. Variant 1 evidence stays in provider-v1-rejected/.

Owner steering: all remaining provider validation must use the local llama.cpp server.
The DeepSeek results are retained as earlier evidence only; they do not validate the local model.
Use the same variant-2 production builder, fixtures, three runs per direction and admission rule.
Capture the actual native JSON Schema payload from the shared llama.cpp adapter, with no cloud calls
and no change to the persisted configuration. Store this new series in provider-local/.

Local variant 2 requires another iteration: all schemas and names passed, but EN→PT rendered
“lamp” as “lanterna” in run 1 and “lamparina” in run 2. These choices specify an object subtype
absent from the source. Treat them conservatively as failures of the no-added-facts rule; the
third EN→PT run used “lâmpada”. Preserve all six outputs in provider-local-v2-rejected/.

Variant 3 additionally requires ordinary direct translations of generic objects, preserving
specificity and inferring no materials, mechanisms or subtypes from the roleplay setting.
Repeat the same six local calls and the unchanged admission rule.
