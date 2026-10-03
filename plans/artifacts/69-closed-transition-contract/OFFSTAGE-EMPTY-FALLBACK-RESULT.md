# Empty offstage narration is now omitted

The post-render offstage guard already returned an empty string when **every**
sentence named an actor outside the viewer cluster. Its caller then used
`_strip_offstage_actors(...) or narration`, restoring the original, entirely
offstage draft. This was a deterministic contradiction of the per-viewer
narration boundary, independently of whether a model produces such a draft
in a live scene. The Runner already skips empty narration strings for a
cluster in `_render_and_prepare`.

`render_narration` now preserves the guard's empty result. A regression at
the actual renderer boundary supplies a wholly offstage two-sentence model
response for the hall cluster and requires `""`; the old fallback would fail
that test by returning both sentences. A mixed-response regression still
keeps the hall sentence and removes only the offstage one. The existing
guard-unit test now describes the caller's omission behavior accurately.
An integration test drives a split Runner turn with an empty hall render and
confirms that no empty hall narration record is persisted while the other
cluster's narration remains.

This fixes only the **all-sentences-removed** path. It does not preserve
Garran's witnessed T6 crossing, which the same name-based guard can remove
from a mixed paragraph, nor does it solve pronouns left behind after a
sentence is removed. A source-bound event-time authorization is a possible
path for T6; a blanket exemption for a moved actor failed its separate local
screen. No live LLM output or prevalence estimate was used to claim the
fallback occurred in a session.

Validation: 68 focused tests passed; full suite 1,194 passed, 2 deselected;
`uvx ruff check .` passed. `uvx ruff format --check` on the three touched
files still reports pre-existing formatting in `src/agents/prose.py` and
`tests/test_per_viewer_narration.py`, outside changed lines. The standard
`uvx mypy` command still reports three existing `src/runner.py` errors at
883, 1301 and 1974; no new error was reported. `git diff --check` passed.
