# V2 technical correction before a separate provider run

The frozen first screen in
[AUTHORITATIVE-TRANSACTION-PREREGISTRATION.md](AUTHORITATIVE-TRANSACTION-PREREGISTRATION.md)
completed 16 valid Director calls, each matching its expected ordered
operation sequence, but **all 16 subsequent prose calls received HTTP 400**.
The saved provider error says `json_object` requests must have the word `json`
somewhere in the prompt. The first harness called the production
`build_prose_messages` but skipped the DeepSeek adapter's required technical
schema instruction. Thus the 400s are a harness protocol failure, not evidence
about prose generation. The original manifest, raw requests, responses and
`authoritative_transaction_screen_v1.py` remain preserved. No failed call is
replaced inside that run.

V2 keeps the same four cases, expected operation objects, Director experimental
schema, direct curl settings, four calls per case, derived physical-event
sentences, production prose builder and content criteria. The **only request
construction change** is that the prose request is prepared by the actual
`DeepSeekAdapter.prepare_request` with `build_prose_schema()`, exactly as the
shared client does. This appends the adapter's JSON Schema instruction to the
system message and sets `response_format=json_object`. Its source file is
included in the new manifest hash. Freeze V2 script, this delta, original
preregistration, cases, adapter source and 16 new Director requests before
calls. Do not reuse the first run's Director outputs or response IDs; perform
16 fresh Director calls and one prose call for each valid decision, with no
retries or replacements.

The original all-valid technical and full-content decision rules remain in
force. A V2 pass still supplies only a local synthetic contract signal, not a
runtime producer or a model reliability estimate.
