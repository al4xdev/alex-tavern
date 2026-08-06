# Task 74 — An orchestrator with tools, instead of a fixed pipeline

> **Status:** backlog, **proposed 2026-08-05** by the owner, enabled by the budget
> rule (`AGENTS.md` §2). **Not scheduled.** It is the largest architectural
> proposal this project has had, and it must not be designed before the phase
> checkpoint — see §5.
>
> ---
>
> **⚠ Read §6 before §2. A survey of the repo (2026-08-06) found that a working
> prototype of this task already exists, disabled, in `src/watcher.py`** — and it
> falsifies §2's headline argument. Both §2 and §3 carry corrections below.

## 1. The proposal

Today the Runner *is* the orchestration: a fixed pipeline runs every turn —
Director → character queue → prose — with hard-coded clocks, burst rules and
exclusion windows deciding the variations.

Instead: an agent that reads the situation and **fires the tools it judges
necessary**, the way a coding agent decides which tool to call. Route these three
characters; resolve this whisper; replan the beat; skip the prose; do nothing at
all this turn.

## 2. Why this is not scope creep — it answers the phase's headline defect

The roadmap's own statement of the problem:

> **The engine cannot render a turn in which nothing happens.** `perception_events`
> requires `minItems: 1`, prose must reach 150 words, and prose may not narrate
> stillness.

Those are properties of a **fixed pipeline**: every stage must produce, because
every stage always runs. An orchestrator can call nothing. That is a structural
answer rather than another guard, and no other proposal in this phase has one.

> **❌ Falsified 2026-08-06 — by code already in this repo.** The pipeline
> *already has a place that decides to do nothing*, and it does not work. The
> recovery ladder's third rung is `RUNG_ALLOW_SILENCE` — literally *"tolerate one
> beat of silence before disrupting"* (`watcher.py:290`). When it fires,
> `_maybe_watcher_recovery` sets `silence_spent = True` and returns `None`
> (`runner.py:2250-2252`) — and **the turn is not silent.** The Director still
> runs under `perception_events: minItems 1`, and the prose still runs under the
> 150-word floor. What the rung suppresses is *the watcher's own intervention*,
> never the pipeline's mandatory production.
>
> So the engine contains a decision to be quiet that cannot make the turn quiet.
> The obstacle is not that orchestration is fixed — it is the three constraints
> task 72 already names (`minItems: 1`, the word floor, the stillness ban).
> Removing them makes silence renderable **with no orchestrator at all**, and
> leaving them in place makes an orchestrator unable to be quiet either.
>
> This does not kill the task. It kills its best argument, which is worse for the
> task and better for the roadmap: 74 must now be justified by *routing* (§2's
> three bullets below, which survive intact), not by stillness. Stillness belongs
> to 72.

Three more findings point the same way:

- **Task 64** — `return_control=True` on 5 of 482 turns, and 5 of 12 sessions
  never returned control. `BURST_PROTAGONIST_EXCLUDE_BEATS` excludes the
  protagonist by clock while the fiction is screaming for them (case 21 §3.2: ten
  turns of standoff where the Director's own events say *"Link, abra o portal"*).
  A situation-reading dispatcher routes the PC because the scene needs them.
- **Task 70** — the Director's prompt names the protagonist to exclude them,
  because routing lives inside the narration call. Move routing out and the
  narration prompt stops carrying a cast-exclusion instruction at all.
- **Task 65** — the Director authors speech partly because it is the only agent
  awake at that moment. A dispatcher that can call a character instead does not
  need the Director to improvise one.

**So 64, 70 and part of 65 may be symptoms of one cause: too many decisions in
one call, and a pipeline that cannot choose.** That subsumption claim is the
thing to test, and it is why this cannot be designed before those tasks land —
if wave 1 already fixes them, the case for 74 shrinks a great deal.

## 3. The constraint that decides whether this is safe

**Every leak invariant in this engine is enforced by code *before* the call** —
perception clamped by the zone graph, prose never given minds, speech reduced to
markers, redaction applied per viewer. This project has measured, repeatedly,
that **a prompt promise loses to a code-issued mandate** (task 59 finding 1, task
65's ignored DIALOGUE OWNERSHIP rule, task 71's ignored zone rule in `prose.py`).

An orchestrator is, by construction, a prompt deciding control flow.

> **Non-negotiable if this is ever built: the orchestrator chooses WHAT happens
> and never HOW. Every tool enforces its own invariant internally, and there is
> no tool, argument or ordering that can skip a clamp.** If "call the prose
> renderer with the whispers included" is expressible, the design has already
> failed.

**This constraint is already frozen, accepted and shipped — under another name.**
Task 33b's design decision #2, accepted by the owner on 2026-07-19, reads
*"Ladder 100% código, LLM só responde as 2 perguntas"*, and `watcher.py`'s own
header states it as *"The ladder never talks to the model: it decides which
recovery kind to take, deterministically, from an explicit context."* So the
project has already answered this question once, and answered it **more strictly
than §3 asks**: not "the model chooses what, code chooses how", but *the model
does not choose at all* — it answers a bounded question about the situation and
**code decides what fires**.

That is the real fork this task has to pick, and it is not a detail:

| | who reads the situation | who decides the call |
|---|---|---|
| **watcher shape** (built) | LLM (`audit_delta`, one bit + evidence) | code (`select_recovery_step`, pure) |
| **74 as proposed** | LLM | LLM |

The watcher shape satisfies §3 *by construction*, because a model that never
names a call cannot name a forbidden one. The proposed shape has to earn the
same guarantee with schema design (§6.4). **74's cheapest first form is therefore
not a new agent: it is widening the situation-reading call and the ladder that
already consumes it** — which is also, per §6.2, the only version whose missing
inputs wave 2 is already building.

## 4. The cost that is NOT free

`AGENTS.md` §2 makes tokens and latency cheap, which is what makes this thinkable.
Two costs it does not cover:

- **Comparability.** Batteries compare runs that made the same calls. A dynamic
  call graph makes `llm_calls_per_action` a *variable* rather than a control, and
  the archive's whole method is controlled cells. Any battery with an
  orchestrator cell needs the fixed pipeline running beside it, exactly as
  `oldcode` does today.
- **Complexity**, which §2 explicitly keeps expensive. One more call is cheap;
  one more layer that can reorder the engine is not.

## 5. How to test it for almost nothing, before building anything

**Run the orchestrator read-only over the archived sessions.** The 16 sessions in
`plans/artifacts/` carry every turn's full state and the Director's raw decisions.
Give a dispatcher agent the same situation each archived turn presented, let it
say what it *would* have called, and never execute anything.

Then score its decisions against what actually happened:

- on the **ten stalled turns of `base-P1-r2` T30–T39**, does it route the
  protagonist? (`return_control` was false on every one of them);
- on turns the blind reader called restaging, does it choose to **do nothing**?
- how often does it propose a call the fixed pipeline did not make, and does that
  correlate with the turns a reader disliked?

Zero engine change, zero risk, and it directly tests the one claim that justifies
the whole idea: *can it represent a turn where nothing happens?* If it cannot, or
if it fires the same calls the fixed pipeline already fires, this task closes
cheaply and honestly.

**The measurement that would falsify this task:** if wave 1 + 69 already produce
turns that can be quiet and a protagonist that gets routed, the pipeline was not
the cause and this is a rewrite in search of a defect.

---

## 6. Inventory — what is already implemented here (surveyed 2026-08-06)

The owner asked what tooling already exists that this task would reuse. The
answer changed the task, so it is recorded in full rather than summarised.

### 6.1 The prototype already exists, wired and disabled: `src/watcher.py`

Task 33b (**closed 2026-07-20**) shipped a three-piece situation-reader → 
dispatcher → intervention chain, fully wired into the Runner, behind
`watcher_enabled` (**False** by default, `watcher.py:200`):

| piece | symbol | kind | what it is |
|---|---|---|---|
| 1 | `audit_delta` | LLM | blind per-turn auditor: did this turn produce a material delta? 8-category frozen taxonomy incl. explicit `none` |
| 2 | `select_recovery_step` | **pure code** | the ladder: picks a recovery *kind* from `LadderContext`, deterministically |
| 3 | `generate_causal_intervention` | LLM | typed contract `source_thread → target_state → event_now → expected_delta → refractory_turns` |

Wiring: `runner.py:1501` audits every committed beat; `runner.py:1101` consults
the ladder while resolving the next beat's hint; `watcher_quiet_turns`,
`watcher_last_intervention_tick` and `watcher_silence_spent` are **durable**
`GameState` fields (`models.py:403-410`, serialized at `:671-673`).

**A dispatcher that reads the situation and fires an agent is not a new idea
here. It is off.** Whoever schedules 74 starts by turning it on and measuring it,
not by designing.

### 6.2 Three of the ladder's five rungs are dead code — and wave 2 is what revives them

`LadderContext` (`watcher.py:238-244`) declares six inputs. The Runner supplies
**three** (`runner.py:2244-2248`): `quiet_turns`, `turns_since_intervention`,
`silence_spent`. The other three are permanently `False`, so only
`allow_silence` and `causal_disruption` can ever fire — the ladder skips
straight to its last resort.

| dormant rung | input it needs | who is building that input |
|---|---|---|
| `execute_promised_transition` | `promised_transition_ready` | **task 69** (closed transitions) — the docstring says the task-40 clock owns this rung, but the ladder cannot see it |
| `adjudicate_attempt` | `unadjudicated_attempt` | **task 72** (a request has a resolution) |
| `reincorporate_thread` | `open_thread` | **task 72** (open threads as state) |

**This is the strongest argument in the whole file, and it is an argument for
doing wave 2 first.** The gentle rungs — reuse what is already in play — are
exactly the ones that never fire, and the disruptive rung is the one that always
does. 69 and 72 do not merely reduce the need for 74; they supply the state that
makes its existing dispatcher work as designed.

### 6.3 The one time this project measured an intervention layer, the result was uncomfortable

From the A/B/C battery (`.plan/closed/33b`, `docs/cases/13`):

- **C** (clock + causal watcher) had the best material-delta rate, 6/10, **with
  the watcher never firing once** — act deadlines carried the scene alone.
- **B** (arbitrary template disruption) re-stalled and the ladder re-fired.
- **The blind critic scored B highest.** The pre-registered prediction that C
  would win on coherence did **not** hold: drama with agency buys narrative
  licence from a reader.
- Every incoherence the critic flagged (2 events across 6 critiques) came from
  the **drive's** unanchored seeds — never from the clock, roteiro or causal
  contract.

Two things follow. First, "the layer fired more often" and "the reading improved"
came apart, in this engine, on this instrument — which is why §5's offline scoring
must be against the blind read, not against call counts. Second, the battery's
Decision B (*the drive's seed generator adopts the causal contract*) **was
implemented**: `drive.build_event_seed_schema` carries `source_thread` /
`event` / `expected_delta` (`drive.py:88-101`), 3 of the contract's 5 fields.
It does not carry `target_state` or `refractory_turns`. Not a defect, just the
actual state of it.

### 6.4 There is no tool-calling in this engine, and that is good news

`tool_call`, `tools=`, `tool_choice`, `function_call`: **zero occurrences across
`src/`.** Every model call in the engine — thirteen call sites across twelve
modules — goes through one gateway:

```
src/llm/client.py::call_agent(client, config, messages, *, agent, json_schema, max_tokens, ...)
```

messages + JSON schema → validated dict, **grammar-constrained on the server**
(`response_format: json_schema`, `client.py:246-250`), schema-validated locally,
retried with backoff, and logged per call.

So "an orchestrator with tools like Claude Code" **cannot be built in this
engine's current call shape.** What it can be is a **plan-returning call**: one
`call_agent` whose schema is an array of typed, enumerated call descriptors,
which the Runner then executes. That is not a downgrade — it is strictly better
against §3:

- the **schema is the enforcement**, not the prompt, and it is enforced by the
  decoder before a token is emitted. An unlisted call is *unrepresentable*, not
  merely forbidden — which is exactly the "code mandate beats prompt promise"
  result §3 cites;
- a plan can be **validated whole, before anything executes**;
- it terminates by construction. A real tool loop has unbounded turns, per-provider
  differences and a new provider capability to maintain — the opposite of the
  guarantee §3 demands.

**Write this down before anyone reaches for an agent SDK.**

### 6.5 The plugin system is the tool boundary that already exists

`src/plugins/` is a full extension runtime: **20 named hooks** with a
machine-readable contract (`contracts.py::HOOK_CONTRACTS`), three kinds
(action / filter / **wrapper**), deterministic cross-machine ordering
(topological, `before`/`after`/`priority`, `hooks.py:89`), a **13-permission**
model including `model.call` and `session.state.write`, a per-plugin SDK
(storage / config / http / model / unsafe), and a journal.

The `wrapper` kind's contract is, verbatim: *"Replace, surround, or bypass the
complete Narrator call"* / *"…the complete Character call"*. The Runner already
dispatches through it (`runner.py:1377-1388`).

**An orchestrator can therefore be written as a plugin with zero core change** —
`turn.input` + a `narrator.call` wrapper + a `character.call` wrapper. That is
almost certainly its right first home, because it answers §4's comparability
problem for free: the control cell is the same binary with the plugin off.

One correction to an easy assumption: `plugins/commands.py::validate_descriptor`
is a **UI** command schema — its input types are `text` / `textarea` / `file`,
form widgets, not model types. It is a precedent for namespacing, validation and
dispatch; it is **not** a reusable tool-schema layer.

### 6.6 What is already tool-shaped, and what is welded to the Runner

**Already callable in isolation** — pure, or `(client, game, config, …) -> dict`,
no Runner state:

- `perception.can_perceive`, `eligible_witnesses`, `validate_perception_events`,
  `render_events_for_viewer`, `describe_zones_for_narrator`
- `roteiro.evaluate_roteiro` (deterministic trigger) / `replan_roteiro` (content
  only) / `measure_beat_progress` / `anchor_matched`
- `drive.evaluate_event_hazard` (seeded, replay-stable) / `generate_event_seed`
- `watcher.select_recovery_step` / `audit_delta` / `generate_causal_intervention`
- `disposition.*`, `confidentiality.*`, `compaction.*`,
  `alignment.derive_alignment_impulse`
- every agent: `narrator.narrate`, `character.act`, `prose.render_narration`,
  `perspective.initialize/update_identity/revise_memory`, `summarizer.summarize`,
  `suggest.suggest_moves`

**Welded to the Runner** — they mutate `game` in place and return partial values:
`_director_beat`, `_resolve_beat_hint`, `_apply_canon`, `_apply_time_skip`,
`_render_and_prepare`, `_run_speaker_queue`, `_persist_audible_speech`,
`_commit_beat`, `_append_history`, `_ensure_perspective`, `_update_scene`,
`_update_moods` — plus the burst loop itself (`player_turn`'s 100-line `for
beat_index` block, `BurstState`, `_beat_settled`, the "beat produced nothing"
drop). **That loop *is* the orchestration this task wants to replace, and it is
inline.**

The decomposition is nonetheless already done — `runner.py:816` states it: *"each
one owns a single step of the beat and can be read (or tested) without the
others."* What is missing is that stages mutate rather than return effects. A
bounded refactor, and **not needed for §5's read-only experiment.**

### 6.7 §5's free experiment needs no new harness

Already built and used:

- `tools/replay_llm.py` — OpenAI-compatible server replaying recorded outputs
  from a session's raw debug log
- `tools/replay_session.py` — re-runs a recorded session through the real HTTP
  API and diffs outputs
- `mcp_server.py::replay_extract_call` / `replay_llm_call` — pull one recorded
  call and re-issue it with system-prompt edits (this is how a new dispatcher
  prompt gets tried against a real archived situation, for pennies)
- `tools/acceptance/watcher_abc.py --audit <sid>` — **arm-neutral offline
  per-turn material-delta audit over a finished history.** This is task 75's §4
  ("run the critic offline over an archive") already written *and already run
  once*
- `tools/acceptance/immersion_scanners.py` (task 68) — the scanners any critic
  must beat to earn its place
- `tools/render_transcript.py`, `acceptance/blind_continuity.py`,
  `acceptance/archive_benchmark.py`, `acceptance/repetition_battery.py`

**Both §5 here and §3-§4 of task 75 are a new prompt plus a scoring script.** No
harness work, no engine change.

### 6.8 What this inventory changes

1. §2's stillness argument is dead (see the correction there); the routing
   argument stands.
2. The first form of this task is **turn the watcher on and give its ladder the
   inputs it is missing**, not build a new agent. Wave 2 supplies those inputs.
3. If a dispatcher agent is built anyway, it is a **plan-returning schema call**
   living in a **plugin**, not a tool-calling loop in the core.
4. The measurement bar is the blind read, because the one prior battery here
   showed call-count and reading quality moving in opposite directions.
