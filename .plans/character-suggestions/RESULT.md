# Character-based suggestions: delivered

The suggestions endpoint now uses the same `build_character_messages` as ordinary
Character.act, including personality, knowledge, mood, viewer history, durable
memory and relationships. The system prompt and ordinary Character output schema
are unchanged. A suffix requests three coordinated alternative responses, each
with speech, thought and action_intent. The endpoint maps action_intent to the
existing editable action field; the interface displays and fills all three fields.
Selecting an option does not send it. No session schema change or automatic action.

Suggestions reuse Character's movement validation, repetition detection and
whisper-secret guard, with one correction retry and deterministic fallbacks.
Shared current surroundings remain available in flat scenes. Unscoped physical
facts are excluded in split scenes because they have no per-fact witness metadata;
perceived history and memory are retained. No screenplay speech mandate or alignment
impulse is used to constrain the human's possible next move.

## Evidence

- Full pytest: **1,204 passed**, 2 LLM-marked tests deselected.
- Ruff lint and mypy: passed. Modified/new formatted sources pass checks; the
  repository-wide format check has pre-existing failures from the checkpoint.
- HTTP test traverses FastAPI and Runner, returns all three fields and confirms
  the session state bytes remain unchanged.
- Node executes the actual renderer and selection handler, including a thought-only
  choice. All 28 frontend JS modules parse; HTML parses. The full suite checks
  adapter registry and frontend contracts.
- Real provider comparison: two frozen real-session snapshots, three runs per
  version, six pairs via curl and the production provider adaptation. Candidate
  produced all 18 drafts. Independent blinded reader preferred candidate in **4/6**
  pairs and baseline in **2/6**. This is a small usefulness pilot, not universal proof.
- All six candidate request logs had zero lexical operator-ontology matches and
  zero C-number internal IDs. Source snapshots were unchanged.

The first candidate used three independent Character calls; reading and independent
evaluation found redundant alternatives and missing physical context. It was rejected.
The shipped candidate generates the alternatives together and shares the exact
Character message builder. Ordinary Character message contents are preserved.

Input-order experiments are diagnostic only and are NOT applied to production.
The user asked to set aside the already-known Character hallucination issue;
no investigation or repair of that issue is included in this delivery.

Raw snapshots, messages, responses and independent reader reports remain under
`private/`, ignored by Git in the isolated worktree. They contain session content
but no API keys. The tracked preregistration and scripts preserve the method.

The initial repository checkpoint is 06abc87. The owner subsequently authorized
a separate local commit containing only these suggestion changes. No remote
operation was performed.
