# Task 59 — Knowledge entries carry who else knows them

> **Status:** open. Design proposal is **signed, not neutral** — the reasoning
> below is mine and the owner has already agreed with the shape. Attack it; do
> not treat it as settled because it is written down.
>
> **Rewritten 2026-08-02** after the repetition investigation
> (`docs/cases/20-repetition-baseline-2026-08-01.md`). That work never touched
> `knowledge`, but it measured four system-wide fragilities that decide how this
> task must be built. They are in "What the repetition work changed about this
> task"; the original shape survives, the delivery constraints are stricter.

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

## What the repetition work changed about this task

Four measured findings, each with a consequence here.

**1. A prompt promise loses to a code-issued mandate, silently.** The Director
prompt contained, simultaneously, `roteiro.py`'s *"Never restage what already
happened"* and an `UPCOMING EVENT` block declared MANDATORY — *"no coherence
concern overrides it"* — backed by a correction retry. The mandate won 7 times
out of 12. Neither instruction was wrong in isolation; the one with code behind
it beat the one with only prose behind it.

*Consequence:* "who else knows this" must never be expressible only as prompt
text. If `known_by` ships as a rendered line the model is asked to respect, it
will lose the first time it contradicts something structural. It has to decide
**which prompt receives the fact at all**.

**2. `physical_facts` is a laundering channel, and it was open.**
`confidentiality.known_tokens` and `hidden_thought_tokens` subtract every token
appearing in `scene.physical_facts` from the whisper *and* thought secret sets,
for every viewer. `perception_events` were redacted on the way out;
`scene_update` was not. One whispered detail written into a fact silenced the
guard for everyone, permanently, because facts are never pruned. Fixed
(`scene_fact_secret_tokens`), with the counterfactual recorded.

*Consequence:* secrecy in this codebase is **subtractive and global**, not a
per-fact property. A `known_by` list is a second, per-fact source of truth about
who knows what. The two must be reconciled explicitly, or the older one wins by
accident. Concretely: if `known_by: ["C3"]` says C3 knows a fact, C3's
`known_tokens` must contain it — otherwise the redaction guards will strip that
fact's own words out of C3's prompts as if they were somebody else's secret.
**That integration is the task, more than the dataclass is.**

**3. State seeded once and never re-synced goes stale, and nothing notices.**
The act clock froze on the terminal act and re-fired the same world event twelve
times. `physical_facts` grows to 51-80 keys with no expiry except a location wipe
that never fires, because the Director re-emits the identical location string.

*Consequence — this is the change to Route A below.* `initialize_perspective`
runs **once**. A fact that starts secret and is later revealed in play has no
path to update the ledger, so the viewer's belief freezes in a state the story
has already left. Route A needs a re-seed rule or it reproduces the exact defect
just fixed.

**4. An invariant that cannot be scanned offline cannot be defended.** Every
defect found was found because `debug.jsonl` and `state.json` held the evidence,
and every fix has a counterfactual because the old engine could be re-run against
the same ruler. The two defects that hid longest hid because no metric looked at
them — one because every metric scored model *output* while the cause was model
*input*, one because a query bug read a key that does not exist.

*Consequence:* this task ships with an offline scanner, not only unit tests. See
"Closure evidence".

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

Verified 2026-07-27, re-verified 2026-08-02 — the consumers and the denial are
unchanged after the repetition work:

**`knowledge` today is strictly self-only.** It reaches the owner's own Character
prompt (`character.py:136`), the owner's perspective initialisation
(`perspective.py:206`, `:221`) and the owner's move suggestions
(`suggest.py:120`). The Director is denied it on purpose (`narrator.py:443-445`:
full profiles "would leak detail the Narrator has no scene reason to know"), and
a Character prompt never cites another character's sheet at all.

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

**Route A now carries a mandatory rider (finding 3).** Seeding at init is not
enough. Decide and write down what happens when a `known_by: []` fact is revealed
in play. The two honest options:

- *re-seed on disclosure* — when a fact's words appear in a record the viewer can
  see, that viewer joins `known_by` for the rest of the session. Deterministic,
  reuses `record_visible_to`, and mirrors how `known_tokens` already behaves.
- *declare the sheet immutable* — `known_by` describes the STARTING state only
  and everything after is the ledger's business. Cheaper, but then say so in the
  scenario-author docs, because "Link's secret" will read as permanent and will
  not be.

Shipping neither is the failure mode: the ledger silently disagrees with the
transcript and no test notices.

**Route B: a new block in the Character prompt.** Simpler to picture, but it
creates the cross-sheet channel, and every guard for it would have to be written
from scratch. Finding 1 applies to it directly: a rendered "others know this"
line is a prompt promise, and prompt promises lose.

## Conversion: the default is the whole decision

110 facts in `turma-dos-portais` alone (×2 locales), 6 in each `thorn-lyra`. The
conversion has to be programmatic, and the default is the difference between a
migration and a mass disclosure.

**Default `known_by: []` — "only me".** That preserves today's behaviour byte for
byte, because today nobody else's prompt receives these facts either. Scenario
authors then *promote* the facts that are common knowledge.

Defaulting to `None` would publish, in one commit, Link's other-world origin,
Lord Aurel's order and Asword's fire. **The safe default is the restrictive one,
and it is also the one that changes nothing until someone decides to.** Finding 2
sharpens this: the laundering path proved a leak here is not one bad turn, it is
permanent for the rest of the session.

Forward-only per `AGENTS.md` §2: `SESSION_SCHEMA_VERSION` **15 → 16** (the
original draft said 14 → 15; 15 shipped since), no migration path, sessions on 15
are refused.

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
- [ ] the Director still receives **no** knowledge at all
      (`narrator.py:443-445` is a deliberate denial — do not "fix" it while
      wiring this);
- [ ] the summarizer and prose renderer receive none of it;
- [ ] **(new, finding 2)** a fact with `known_by: ["C3"]` is inside C3's
      `known_tokens` and outside everyone else's — so the redaction guards
      neither strip a character's own knowledge out of their own prompt nor treat
      it as public for the rest;
- [ ] **(new, finding 2)** a `known_by: []` fact whose words are never spoken
      stays secret even if the Director writes them into `scene.physical_facts`;
      that channel publishes permanently and must not be a bypass;
- [ ] **(new, finding 3)** whichever disclosure rule is chosen has a test: either
      the viewer joins `known_by` after seeing it, or the sheet is proven
      immutable and the ledger is proven to be the only thing that moves;
- [ ] conversion of the four built-in scenarios produces byte-identical prompts
      to the ones produced before the change, for every character, with the
      `[]` default — the proof that the migration changed nothing.

The last one is the real gate. If the converted scenarios produce a different
prompt than before, the default was wrong.

## Closure evidence required

- [ ] the assertions above, green;
- [ ] `SESSION_SCHEMA_VERSION` bumped 15 → 16, no migration branch anywhere;
- [ ] the four built-in scenarios converted, with the byte-identity proof;
- [ ] at least one scenario fact *promoted* out of `[]` by hand, with a real run
      showing it reaching the intended reader and nobody else;
- [ ] **(new, finding 4)** an offline scanner, in the shape of
      `tools/acceptance/repetition_metrics.py`: given a recorded session it
      reports, per character, which classified facts appeared in a prompt that
      character should not have received. Zero is the invariant. Unit tests prove
      the wiring; only a scanner proves a live session did not leak, and only a
      scanner keeps proving it after the next change.

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
