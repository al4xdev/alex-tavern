# Task 59 — Knowledge entries carry who else knows them

> **Status:** open. Design proposal is **signed, not neutral** — the reasoning
> below is mine and the owner has already agreed with the shape. Attack it; do
> not treat it as settled because it is written down.

## Problem

`CharacterMind.knowledge` is `list[str]`. Every entry answers one question —
*what does this character know?* — and nothing answers the second one the
scenarios clearly need: *who else knows it?*

That second question is answered today **in prose**, inside `narrator_directives`
and `personality`, which means the Director has to read it and honour it:

> "ninguém além de Link sabe que ele veio de outro mundo"
> "Lorde Aurel ordenou que Mirella observe Asword e Link; ninguém além dos dois
> conhece a ordem"
> "Esconde que incendiou uma ala de treino"

Those are prompt promises. `AGENTS.md` §3 exists because prompt promises fail
silently, and the pre-1.0 audit spent a full session proving it.

## Shape

```python
@dataclass
class KnownFact:
    fact: str
    known_by: list[str] | None = None
    truthful: bool = True          # deferred, see "Out of scope"
```

`known_by` deliberately mirrors `TurnRecord.audience` **exactly**, so the project
gains no new visibility vocabulary:

| value | meaning | already shipped as |
|---|---|---|
| `None` | common knowledge, everyone knows | `audience is None` = public record |
| `[]` | this character alone | a secret |
| `["C3","C7"]` | those characters know it too | whisper audience |

The reason this matters more than it looks: a naive `public`/`private` boolean
would be a **third** visibility concept alongside `audience` and the zone graph.
Task 58 closed on exactly that failure mode — two labelling systems in one prompt,
and a model left to reconcile them.

## The finding that should shape the delivery

Verified 2026-07-27, and it is not what I assumed when proposing this:

**`knowledge` today is strictly self-only.** It reaches the owner's own Character
prompt (`character.py:136`), the owner's perspective initialisation
(`perspective.py:221`) and the owner's move suggestions (`suggest.py:120`). The
Director is denied it on purpose (`narrator.py:437`: full profiles "would leak
detail the Narrator has no scene reason to know"), and a Character prompt never
cites another character's sheet at all.

So a non-empty `known_by` does not merely *filter* an existing flow — **it opens
a channel that does not currently exist**: a fact from A's sheet appearing in B's
prompt. That is new content crossing a confidentiality boundary that is absolute
today.

### Two routes, and the one I would take

**Route A (recommended): feed the perspective ledger, do not open a new block.**
`CharacterPerspective` already carries per-viewer beliefs, already reaches
prompts, and is already guarded. `known_by` seeds it deterministically at
initialisation instead of a new "things others told you" section in the Character
prompt. Same principle as the visibility choice above: **feed an existing
channel, do not build a parallel one.**

This also collects the second prize. `initialize_perspective` is currently an LLM
call that reads `personality + knowledge` as prose and *guesses* who the viewer
knows, with `_validated_people` clamping invented acquaintance afterwards.
Classified facts make part of that deterministic, so the model is consulted only
where the sheet is genuinely ambiguous.

**Route B: a new block in the Character prompt.** Simpler to picture, but it
creates the cross-sheet channel, and every guard for it would have to be written
from scratch.

## Conversion: the default is the whole decision

110 facts in `turma-dos-portais` alone (×2 locales), 6 in each `thorn-lyra`. The
conversion has to be programmatic, and the default is the difference between a
migration and a mass disclosure.

**Default `known_by: []` — "only me".** That preserves today's behaviour byte for
byte, because today nobody else's prompt receives these facts either. Scenario
authors then *promote* the facts that are common knowledge.

Defaulting to `None` would publish, in one commit, Link's other-world origin,
Lord Aurel's order and Asword's fire. **The safe default is the restrictive one,
and it is also the one that changes nothing until someone decides to.**

Forward-only per `AGENTS.md` §2: `SESSION_SCHEMA_VERSION` 14 → 15, no migration
path, sessions on 14 are refused.

## Editor UI

The fact row stays a text input. Beside it, a three-state chip — **everyone /
only me / some…** — where "some…" opens the **whisper audience popup that already
exists** (`populateWhisperOptions`, `composer.js:287`). Common case is one click;
the rare case reuses shipped, tested UI instead of inventing a picker.

Owner's note (2026-07-27): character-card complexity is no longer a constraint,
because filling presets with an LLM is planned. Keep the shape simple enough for
a model to generate reliably — that is a reason to prefer three states over a
free-form audience expression, not a reason to add fields.

## Testing: no prompt A/B, but not "no tests"

The owner's read is right and worth stating: **there is no new prompt template,
no new agent and no new instruction**, so `AGENTS.md` §6 does not call for a
curl-first wording experiment. Code decides who receives what; no model judgement
is involved.

But this moves a confidentiality boundary, so the deterministic tests are
mandatory and cheap:

- [ ] a fact with `known_by: []` reaches **only** its owner's prompts — assert
      against the real builders, not helpers;
- [ ] a fact with `known_by: ["C3"]` reaches C3 and nobody else, including via
      the ledger;
- [ ] a fact with `known_by: None` reaches everyone present;
- [ ] the Director still receives **no** knowledge at all (`narrator.py:437` is a
      deliberate denial — do not "fix" it while wiring this);
- [ ] the summarizer and prose renderer receive none of it;
- [ ] conversion of the four built-in scenarios produces byte-identical prompts
      to the ones produced before the change, for every character, with the
      `[]` default — the proof that the migration changed nothing.

The last one is the real gate. If the converted scenarios produce a different
prompt than before, the default was wrong.

## Closure evidence required

- [ ] the six assertions above, green;
- [ ] `SESSION_SCHEMA_VERSION` bumped, no migration branch anywhere;
- [ ] the four built-in scenarios converted, with the byte-identity proof;
- [ ] at least one scenario fact *promoted* out of `[]` by hand, with a real run
      showing it reaching the intended reader and nobody else;
- [ ] suite, Ruff and mypy green; local commits only.

## Out of scope — and why it is a separate task

`truthful=False` is the public-vs-real persona split (the standing README
backlog item): a fact everyone believes that is not true. The data shape supports
it, which is why the field is sketched above, but shipping it needs an answer to
a question this task does not touch:

**what does the Director do when the world tests the claim?** A character
presents power they lack, takes a hit, and the Director resolves either by the
real sheet — the bluff collapses — or by the observers' belief. That is narrative
arbitration, not schema, and it deserves its own measurement rather than being
smuggled in with a data change.

Deliverable 1 (this task) gives *hiding*. Deliverable 2 gives *bluffing*, with
the experiment it requires.
