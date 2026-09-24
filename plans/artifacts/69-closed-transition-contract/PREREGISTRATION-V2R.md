# V2 production-retry screen

Date: 2026-09-19. Fixed before these calls are dispatched.

V2 failed its registered first-response gate: only one of four responses passed
the schema. Three failures were exactly the error classes that the production
structured-output client retries automatically: malformed JSON, a schema-invalid
event kind and too many routed speakers. This screen asks a narrower question
before changing the contract again: does the unmodified production retry path
make the already tested V2 request mechanically usable?

## Variant

Use the exact V2 messages and JSON Schema archived in `runs-v2`; do not change
the prompt, catalogue, state vocabulary or provider settings. Run four
independent calls through `src.llm.client.call_agent`, with its production
default of two retries after the first attempt. Retries resend the same request;
there is no corrective message and no local repair.

Give each call an isolated temporary data root and session ID so every raw
attempt is preserved without reading or writing the real runtime sessions.
Archive the redacted debug records and the final returned object. After the
client accepts the schema, apply the same exact local transition validation as
V2. A locally invalid final object counts as failure; it does not receive an
extra retry.

## Decision rule

The production retry boundary is mechanically viable only if:

- at least three of four calls return a schema-valid final object within the
  existing three-attempt budget;
- at least three of four final objects also pass exact local transition
  validation;
- no accepted final object reopens the chest, repeats the messenger crossing or
  repeats the survival-selection decree in reader-visible content;
- at least three accepted final objects progress the emergency rather than
  buying compliance through silence or a static recap;
- a blind source reader finds no material continuity contradiction in more than
  one accepted final object.

Report first-attempt and final-attempt validity separately. A pass here only
shows that production retries can support this boundary. It does not reverse
V2's failed first-response result, validate its spatial metadata, validate a
renderer, or authorize runtime implementation.

