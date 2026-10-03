# T17 scene-key coverage: a corrected pending signal, not a fiction fix

**Observed in one archived turn.** In `base-P1-r3` (`55d03896`), the T17
Director event opens the west-wall breach and its accepted `scene_update`
records `terceira_brecha: aberta na parede oeste`. Event-text coverage alone
does not match the roteiro anchor `terceira brecha`; the real T18 request
still lists it under `Not in play yet` and keeps a `Current beat` beginning
with the breach opening. T18's accepted event opens it again. This is a
source juxtaposition, not proof that the pending line caused the repetition.

**Change.** A scene key updated and retained in the current beat now covers
an anchor when the key's whole name, with underscores treated as spaces,
equals that anchor after case/accent normalization. A deletion, a rejected or
evicted key, and a neighboring name do not count. The existing event/character
text coverage remains. On the archived T17 response, the coverage result is
`[]` from event texts and `['terceira brecha']` when the accepted scene key is
included. A unit test separates `terceira brecha` from `brecha` and `quarta
brecha`; integrated Runner tests verify both retained-update coverage and
noncoverage for a removed key.

**Limit.** This removes one false pending anchor in a next-turn roteiro
description. It does not change `Current beat`, prove that a replayed T18
would stop reopening the breach, or promote free `physical_facts` to closed
durable transitions. Task 69's input contradiction and cross-submission
fiction gates remain open. A content-only independent critic accepted the
narrow claim and explicitly distinguished coverage bookkeeping from model
behavior.

Validation: `uvx ruff check .`; `uvx mypy src/ tools/playtest_harness.py
tools/mcp_server.py tools/replay_llm.py tools/replay_session.py`; `uv run
pytest -q -x` (1197 passed, 2 deselected). Source:
`plans/artifacts/repetition-battery/base-P1-r3/sessions/55d03896/debug.jsonl`,
Director T17/T18; `src/roteiro.py`; `src/runner.py`; `tests/test_roteiro.py`.
