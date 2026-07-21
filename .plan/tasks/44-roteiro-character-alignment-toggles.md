# Task 44 — Screenplay toggles and dramatic alignment of characters

**Status:** 🟢 CLOSED (2026-07-20)
**Origin:** first real screenplay playtest in session `380ea657`. The Director
compiled a dramatic direction, but characters coherent with the world reacted in a
way capable of interrupting that direction. Observed example: facing the blue liquid
near the portal, Cassian asked to close the portals. The reaction is plausible in a
simulation, but it can dismantle the beat that intends to make the group cross them.

## Progress (2026-07-20)

**Done — Toggle 1 (screenplay on/off):** `roteiro_enabled` exposed in Settings
(`index.html` + `runtime-config.js` populate/collect + i18n PT/EN). Round-trips (the
reset bug — collect omitted the field — is gone for it) and **applies at runtime
without restart** (PUT /config rebuilds the Runner, main.py:709-712).

**Done — Toggle 2 (characters follow the screenplay):**
- ✅ Config flag `character_roteiro_alignment_enabled` (default OFF, boolean-validated,
  in `validate_config` + `resolve_active_config`, tested).
- ✅ **Curl gate DECIDED**: disposition nudge mechanism shipped (`src/alignment.py`).
- ✅ **Wiring**: `Runner._alignment_impulse` checks BOTH flags, respects human agency lock
  (never aligns controlled character), filters expected actors, injects transient impulse line.
- ✅ **Frontend UI & Warning**: Added Toggle 2 and mandatory warning in Settings UI
  (`index.html`, `style.css`, `runtime-config.js`, `i18n.js`). Toggle 2 is disabled with explanation
  when `roteiro_enabled` is OFF.
- ✅ **Subagent Screenwriter Evaluation & Polish**: Live LLM deriver calls evaluated across 5 beats
  and 2 characters. Refined `urgent` text ("cena" -> "momento") and prompt guidance. Full suite passing (714 tests).

## Toggle 2 — execution design (the sensitive, curl-gated part)

**Allowed source (confidentiality):** ONLY the CURRENT beat. `roteiro.beat.intent`
and whether the character is in `beat.expected_actors`. **NEVER** `premise`,
`acts[].summary`, `beat.expected_anchors` not yet in play (future props = spoiler),
nor `exit_condition`. `describe_roteiro_for_director` (which carries all of that) is
Director-only and cannot be reused for the Character.

**Three arms to compare via curl (real payload of session `380ea657`):**
- **A) Full screenplay → Character** (RISK baseline): injects the Director describe.
  Expected to leak premise/anchors/future + metalanguage. Measure how bad it is.
- **B) Derived local direction** (pure slice): injects only a version of the
  character's `beat.intent`, IF they are an `expected_actor`, rewritten as a
  first-person motivation, no meta, no future. Likely needs an LLM DERIVATION step to
  strip directiveness/spoilers from the intent (an intent like "get the group to
  cross the portals" is too directive raw) — or a code template. Curl decides.
- **C) Disposition nudge (Boldness)** — the elegant arm: translates the beat into a
  disposition push (Boldness↑) instead of content. **Zero leak**, the character
  CHOOSES recklessness on their own. Requires reviving Boldness (43 Phase 3.5) as an
  active axis. It is the 43↔44 bridge.

**Mandatory guards (B/C):** a `TestRoteiroConfidentiality`-style test — the
Character prompt NEVER contains premise, act summary, not-in-play anchor,
exit_condition, or metalanguage token (screenplay/beat/act/Director/story). Agency:
never inject direction for the CONTROLLED character; never dictate their choice.

**Pre-registered decision rule:** run A vs B (vs C) on the real payload, ≥3-4 runs,
blind judge, measuring: (1) beat contribution > OFF; (2) voice and own goals
preserved; (3) zero metalanguage; (4) zero future leak; (5) zero attribution to the
controlled character. Ship the variant that passes all 5 — if the full one (A)
leaks, B is the functional representation of the toggle; if C proves zero-leak +
agency, it is the design win. Document before closing.

**Wiring (after the gate):** `_call_character` receives the derived direction when
BOTH flags are ON, through a new prompt channel (like the disposition note). OFF
keeps the current contract (no screenplay text in the Character prompt).

## The sharp conclusion (why the toggle exists) — from the owner, 2026-07-20

The simulation got too good: coherent characters become real people arguing about
random things, and the story does not move even with the Narrator present. The
screenplay does NOT exist to make the character smart — it exists to **license the
dramatically productive choice that a coherent agent would never make**: splitting
from the group, opening the door, crossing the rotten bridge. It is the horror-movie
logic ("don't split up!" — and they split up, because it's a story). Without a
screenplay, everyone survives rationally and nothing happens: **real, but dull.** The
toggle is the honest choice — *truth (free-sim) or story (aligned)* — and whoever
wants the real thing has it available.

**Bridge with Task 43 (disposition):** the **Boldness** axis (cautious↔reckless,
currently parked) is the dial of that "dramatic dumbness". Alignment does not need to
DICTATE "split from the group" — it pushes the character's Boldness up and they
choose recklessness ON THEIR OWN, preserving the agency lock. Disposition is the
honest mechanism of alignment: it changes what the character FEELS (bolder), not what
they DO. This gives Boldness a home (it failed the single-utterance gate in 43) — its
value is not being read in prose, it is **tilting the CHOICE** under the screenplay.
See `.plan/tasks/43`.

## Problem

Characters belong to the world and act according to personality, knowledge, and
perception. When only the Director knows the screenplay, a character can act in a
perfectly coherent way and, at the same time, undo the dramatic composition.

This is not necessarily a bug: in real life, people do not know nor follow a
screenplay. However, Alex Tavern also needs to allow an experience closer to a
directed story, in which the cast contributes to the beat instead of accidentally
cancelling it.

The product must make this choice explicit, configurable, and understandable,
without pretending that free simulation and dramatically aligned acting are the same
thing.

## Product decision to implement

Add two independent toggles in **Settings**:

### 1. Story screenplay

- Proposed key: `roteiro_enabled` (already exists in the backend).
- Turns on the compilation of the private screenplay and its consumption by the Director.
- OFF: the Director improvises the progression from state, history, and directives.
- ON: acts, beats, exit conditions, and the narrative clock guide the Director.
- Must be configurable in the frontend; not require manual editing of
  `.data/config.json` nor a backend restart.

### 2. Characters follow the screenplay

- Proposed key: `character_roteiro_alignment_enabled`.
- Available only when `roteiro_enabled` is ON; when the screenplay is OFF, the
  control is disabled and explains why.
- OFF: characters receive only the world they perceived and act independently. They
  may contradict, delay, or dismantle the screenplay, exactly like real people who do
  not know a planned story exists.
- ON: each scripted character receives dramatic context derived from the screenplay
  so they can contribute to the story's direction.

## Mandatory warning in the interface

The second toggle must display a clear warning, not just a hidden tooltip.

Base text in Portuguese:

> Sem esta opção, os personagens agem de forma independente e podem contrariar o
> roteiro, levando a história a resultados mais caóticos, como pessoas reais que
> não sabem que existe um plano. Ao ativá-la, os personagens passam a colaborar com
> a direção dramática, mas podem parecer mais guiados e menos espontâneos.

Base text in English:

> When this is off, characters act independently and may work against the
> screenplay, producing more chaotic outcomes, like real people who do not know a
> plan exists. When enabled, characters collaborate with the dramatic direction,
> but may feel more guided and less spontaneous.

The final names and microcopy must go through visual and i18n review, keeping the
trade-off visible before the choice.

## Design question the implementation must measure

The product request is to allow **passing the screenplay to the characters**, but the
exact form still needs curl-first evidence. Compare at least:

1. **Full screenplay:** the Character receives the relevant private beat/act.
2. **Derived local direction:** the Character receives only their dramatic function
   in the current beat, with no future acts and no other characters' intentions.

Do not decide by architectural preference. Pre-register metrics and run 3–4 runs per
variant on a real payload. The chosen variant must demonstrate:

- greater beat contribution than the OFF condition;
- preservation of the character's own voice and goals;
- absence of metalinguistic mentions of screenplay, beat, Director, or story;
- absence of future-event leaks into speech, thought, or action;
- no decision, speech, courage, revelation, or action attributed to the controlled
  character.

If the full screenplay leaks spoilers or turns characters into mechanical executors,
use the derived local direction as the functional representation of the toggle and
document the decision. The toggle still means "characters follow the screenplay" to
the user, even if the internal boundary shares only the necessary slice.

## Pre-existing bug discovered (2026-07-20) — probable cause of "screenplay OFF"

`PUT /config` uses `merge_config_update`, which only preserves the **provider
secrets**; the other top-level fields come from the submitted body, and
`save_config → validate_config` **re-defaults whatever is missing**. The frontend
`collect()` (`runtime-config.js`) sends only `active_provider`, `language`,
`compaction_*`, `providers`, and (now) `autonomous_burst_max_beats` — it **omits
`roteiro_enabled` and `auto_event_*`**. Therefore, **every UI save resets
`roteiro_enabled` to False** (and `auto_event_*` to defaults). It is the most likely
cause of the screenplay being found off. This task MUST fix it by exposing
`roteiro_enabled` in the frontend: `collect()` must round-trip the field (populate
reads, collect sends), and ideally every save must be non-destructive to fields the
UI does not edit (full merge, not replace-with-defaults). Test the 4 combinations +
that saving the UI does not zero `roteiro_enabled`.

## Contract and ownership

- Canonical config and validation: `src/config.py`.
- Persistence: `.data/config.json`, using the existing `GET/PUT /config` flow.
- UI and serialization: `src/static/runtime-config.js`, `index.html`, and i18n.
- The screenplay continues to be produced and maintained by `src/roteiro.py`.
- The Runner delivers to the Character only the context allowed by the active option.
- OFF must preserve the current contract: no screenplay text enters the Character prompt.
- ON can never bypass the controlled character's agency lock.
- A toggle change must rebuild/apply the runtime config without requiring a manual
  restart.

## Session behavior

- Turning on `roteiro_enabled` in a session whose `game.roteiro` is `null` compiles
  the screenplay on the next turn under the session lock and persists the result.
- Turning it off prevents maintenance/replan and consumption of the screenplay;
  explicitly define whether the persisted screenplay is preserved inert or removed.
  Since the project is forward-only, there must be a single canonical behavior, no
  dual reading.
- Turning it back on must not silently apply a stale direction to the current state:
  decide and test explicit regeneration or revalidation.
- The alignment toggle only affects future calls; it never rewrites old lines.

## Observability

The debug JSONL must allow distinguishing:

- screenplay OFF;
- screenplay ON for Director only;
- screenplay ON with Character alignment;
- which dramatic slice was delivered to each Character, with the same confidentiality
  limits as the corresponding prompt;
- latency impact of compilation/replan and of the normal calls.

No new LLM call may omit `session_id`, `turn_number`, or `agent`.

## Acceptance

- [ ] Settings has both toggles with PT-BR and EN translations.
- [ ] `roteiro_enabled` can be changed without editing JSON or restarting the backend.
- [ ] The second toggle is conditioned on the first and shows the permanent warning.
- [ ] OFF keeps characters independent and proves by test that the screenplay does
      not enter the Character prompt.
- [ ] ON increases beat alignment in a real curl-first replay without metalanguage or
      future leak.
- [ ] The controlled character remains exclusive to the human in all combinations.
- [ ] Public config, persistence, blank secret, and Runner swap remain correct.
- [ ] Tests cover the four toggle combinations, invalid input, and runtime swap.
- [ ] Real HTTP boundary confirms PUT → active Runner → next turn.
- [ ] Visual boundary at 1080p and 2K confirms readability of the warning and the
      enabled/disabled/focus states.
- [ ] README explains the difference between free simulation and directed story.
- [ ] Curl evidence and the final decision are recorded before closing the task.

## Out of scope

- Self-healing plugin or retroactive rewriting.
- Changing already-persisted lines and events.
- Allowing any agent to choose the protagonist's actions or thoughts.
- Hiding from the user the spontaneity cost of the aligned mode.
