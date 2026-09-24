# Durable-state interface for the current phase

Date: 2026-09-20

This is the storage decision owned by Task 69. It defines the substrate that
Tasks 72 and 66 may extend. It does not approve a Director output contract.
Later local screens passed narrow hall-gate fixtures but failed the
blue-gate duplicate and action-only semantic gates; none validated a producer.

## Root ownership

`GameState.durable_state` is the single persisted owner of enforceable physical,
commitment and possession state that must survive submissions. Existing scene
membership remains canonical in `Scene.present_characters`, and its zone-level
position in `Scene.positions`; Task 79 owns refining that spatial domain. Those
fields are location relations, not parallel copies of an entity's physical
dimensions. `Scene.physical_facts` remains descriptive prompt material in open
prose; a fact does not become binding merely because it appears there.

The root is typed by domain. Task 69 adds the physical domain. Task 72 may add a
commitment domain and Task 66 a possession domain, each with its own records and
validators under this root. Physical objects use physical entity IDs. Actors use
the canonical IDs already owned by `GameState.characters`; an actor entity's ID
must equal that character ID. Cross-domain records type those references
separately and validate referential integrity. A new persisted field still
requires a schema-version bump.

## Physical entities and independent dimensions

The physical domain keeps `physical_entities`, a map from stable entity ID to a
globally unique logical key, kind, optional scene key, registration provenance
and independent state dimensions. A dimension contains its current value and
latest accepted transition provenance.

The separation is essential. A door may be open, damaged and obstructed at the
same time. A chest may be open while its contents are tracked elsewhere. An
incapacitated person may remain in the scene. Flattening those facts into one
enum would make true states compete and would force ordinary actions through
fake intermediate states.

The initial dimensions and directed graphs are:

- vitality: `active -> incapacitated | dead`, `incapacitated -> active | dead`;
- aperture: `closed`, `ajar` and `open`, reversible between adjacent states and
  with direct `closed <-> open` edges for a beat's net result;
- security: `unlocked <-> locked`, `locked <-> sealed` and
  `unlocked <-> sealed`;
- integrity: `intact -> damaged | destroyed`, `damaged -> destroyed`;
- traversability: `clear <-> obstructed`;
- resource: `ready -> spent`.

`dead`, `destroyed` and `spent` have no reverse edge. Repair, revival or
replenishment would be distinct future operations with their own evidence; a
normal transition cannot silently undo them.

Kinds declare both required and optional dimensions. No missing dimension gets
a default during loading or transition:

| kind | required | optional | scene key |
|---|---|---|---|
| actor | vitality | none | absent; position owns location |
| passage | any one declared dimension | aperture, security, integrity, traversability | required, immutable fixture scope |
| container | aperture | security, integrity | required in schema 16 while scene-owned |
| object | integrity | resource | required in schema 16 while scene-owned |
| structure | integrity | none | required, immutable fixture scope |

Every entity declares at least one dimension. An omitted optional dimension
means that capability is absent from that entity instance and cannot be
transitioned. It is not an implicit `unlocked`, `clear` or `ready` value. A
doorless arch may therefore be a passage with only `traversability`; a door may
also declare aperture, security and integrity. Scenario bootstrap must declare
every dimension it expects the engine to enforce.

The scene key is a static partition label declared by the scenario, not an actor
coordinate or an enforceable foreign key to the current `Scene`. Schema 16 has
no active-scene ID or scene registry, so the key cannot yet prove co-presence,
drive visibility or be compared with the prose-facing `Scene.location`. Fixture
keys are immutable. Schema 16 requires portable objects and containers to carry
this declared scene partition while they remain scene-owned. When Task 66 adds
possession, that version must define the handoff to its possession relation and
require exactly one location owner; a container remains a container when
carried. The current foundation does not project these entities into prompts or
accept runtime entities, so it does not pretend that this future handoff already
exists.

There are deliberately no universal implications such as “destroyed means
unlocked” or “locked means closed.” Those statements are not true for every
mechanism: a ruined sealed container, a detached locked door and a blocked open
arch differ. Atomic batches preserve several dimensions together; a future
resolver may add rules for a declared entity capability, but the storage layer
does not invent physical law.

## Registration and transition

Registration materializes a known entity once with valid initial dimensions.
Stable IDs and logical keys are nonempty and unique. Fixed fixtures require a
scene key. Each value's registration provenance must agree with the entity's
registration. The store takes a defensive copy, so later mutation of a caller's
object cannot bypass validation.

A transition is accepted only when:

- entity ID and logical key match a registered entity;
- the addressed dimension is registered on that entity instance;
- its turn is strictly later than that dimension's registration or last
  transition turn;
- `from_state` equals the current value and `to_state` differs;
- the directed graph contains the edge;
- update and transition IDs are nonempty and differ from that dimension's last
  accepted provenance.

The public transition APIs require the caller's current beat number and reject a
transition whose own turn differs. Within that beat, the monotonic check is an
anti-replay fence, not idempotency: an exact retry is rejected as
duplicate/stale. A future Runner producer must pass its actual `step`; callers
must not retry a batch after it committed. One causal update ID may span several
dimensions; each dimension has its own transition ID. A batch may change several
dimensions of one entity in the same beat, but never the same dimension twice.
Direct graph edges express the net result of one beat rather than manufacturing
an intra-beat chain.

All proposal refusals use `PhysicalTransitionRejectionError`, including malformed
field types, unknown entities or dimensions, stale provenance, repeated current
state and illegal graph edges. A producer may catch that narrow error and discard
its proposed physical change while allowing the rest of the story turn to
continue. Invalid persisted durable state still fails validation separately, and
an unexpected plugin exception must not be relabelled as a routine proposal
rejection. Catching the typed error protects state; a producer may continue the
turn only when its pre-render output path also omits or corrects the rejected
event. Catching after prose already described the event would preserve state by
creating a narrative contradiction.

Registration and transition batches run against an isolated copy. Any invalid
member discards the whole batch. Accepted state replaces the draft only after
all members validate, and the Runner persists that draft with the rest of the
turn under the existing session lock and atomic save.

The archived `8bd4d0f1` T29 beat repeats the pillar's held `destroyed`
integrity state. A **synthetic fixture**, inspired by the remaining rubble gap,
then rejects that duplicate without changing its T28 provenance and accepts a
separately chosen gap `ajar -> closed` transition. The actual T29 proposal does
not unambiguously establish complete aperture closure, so the fixture proves
only the storage boundary, not source-grounded extraction. If an invalid
duplicate and a valid independent change were put unchanged in one batch,
atomic rollback would discard both. A future producer must therefore keep
rejected proposals out of a batch containing independent legal transitions it
intends to preserve; pre-validation, splitting or corrected retry remain
producer-design choices.

## Persistence, growth and undo

Only current values and their last provenance live in `durable_state`. It does
not duplicate an unbounded transition log inside every turn snapshot. Audit
history belongs in `debug.jsonl`; roteiro completion belongs to the roteiro
domain. The current entity map has no eviction policy. Prompt projection is a
separate bounded read concern and must never delete authoritative state.
A persistence regression registers 41 physical entities, one above the
descriptive fact bag's historical cap, and requires their exact IDs to survive
the real `save_game`/`load_game` path. This guards the ownership boundary at the
known cap; it does not establish a practical maximum or authorize unbounded
runtime creation. See the [growth-boundary result](PERSISTENCE-GROWTH-RESULT.md).

Every `TurnRecord` stores the complete pre-beat durable-state snapshot. The
Runner stamps it onto every record together with the roteiro/clock undo anchor,
so producer call order cannot capture a post-transition state. Undo restores it
atomically with the other domains. Serialization reads every field by direct
access, and session schema version 16 refuses older session files.

## What is outside this store

These values are not physical dimensions:

- `present` / `gone`: derived from scene membership and the position domain;
- `empty`: derived from the versioned possession/containment domain once Task 66
  exists; before then the engine does not claim deterministic container content;
- `used`, `impact`, `opened`, `looted`: events, recorded once in the beat/debug
  evidence rather than made permanent entity adjectives;
- exact actor blocking or coordinates: Task 79;
- custody/equipment slots: Task 66;
- descriptive damage details such as “bent hinge” or “crack along the lintel”:
  prose, while the enforceable dimension holds `damaged`.

A scene-owned single-use projectile may declare `resource: ready` and transition
to `spent`. Actor custody waits for Task 66. A reusable tool omits the resource
dimension; using it does not mutate durable state merely to prove an action
occurred.

## Bootstrap and consumers

Scenario manifests now bootstrap deterministic physical entities at turn 0;
committed story beats start at turn 1, so the first transition is strictly
later. The manifest carries
stable entity IDs, globally unique keys, static scene-partition labels and
complete initial dimension values. Bootstrap establishes canonical storage
ordering by sorting on entity ID; source-list order has no physical semantics,
while duplicate IDs or keys remain invalid. Actor entries are all-or-none: when
a scenario declares actor vitality, it uses every existing character ID,
including the controlled character. Their current scene membership continues to
come from `Scene.present_characters`. This mapping must never be rendered or
formatted differently in an agent prompt. Dynamic entity creation remains
deferred.

Raw `(entity_id, dimension, target_state)` triples must not be emitted by the
model. Physical entity IDs have no permitted prompt projection, and equality
would validate satisfaction without validating target selection. A screened
candidate instead exposed a scenario-owned catalogue of prompt-safe objectives
and asked the Architect to return an enum label mapped privately to a triple.
The full-catalogue candidate remained mechanically valid but selected the
required context label in only 2/4 calls on each of two frozen payloads, below
its pre-registered 3/4 gates. A subsequent active-only candidate kept future
entries out of the enum before their act, but selected the active target in only
1/4 C2 calls and its prose planned it in 2/4, again below the fixed 3/4
requirements. Neither catalogue shape is approved; see the
[full-catalogue result](OBJECTIVE-CATALOG-RESULT.md) and
[active-only result](ACTIVE-OBJECTIVE-RESULT.md). There is currently no approved
model-selection boundary for physical targets.

If that boundary validates, satisfaction is exact equality between current and
target state. Roteiro records its own satisfied objective IDs so a later
legitimate reversal does not reopen a completed beat. Directed reachability is
a separate check for whether an unsatisfied target remains possible. Exact
satisfaction may contribute directly to beat completion. The watcher's dormant
`promised_transition_ready` rung remains unwired until it owns a concrete
deterministic action; a satisfied objective alone is evidence that a beat can
advance, not an instruction to execute another transition. These consumers use
private resolved IDs and state graphs, not lexical similarity.

## Evidence boundary

This foundation deliberately does not expose durable entities to a model,
accept model-authored transitions, infer aliases from prose, decide causes or
witnesses, or project transitions into reader-visible prose.

At the Runner boundary, hardcoded fixtures now demonstrate four storage
properties across real submissions: a legal transition persists and undoes, a
second proposal for the already-held state is rejected without changing the
first transition's provenance, and `intact -> damaged -> destroyed` persists
across two turns. The archived pillar-pair fixture additionally rejects a
repeated `destroyed` pillar value while allowing a separately chosen gap
closure. **Source-boundary correction, 2026-09-24:** the gap's `closed`
**aperture** label is synthetic. Persisted narration explicitly closes access;
neither it nor the accepted Director proposal resolves the named opening's
aperture after blocks obstruct it. These tests exercise the transactional state
boundary and a manually selected decomposition, not a model producer or a
narration-correction path. See the [corrected pillar-pair result](PILLAR-PAIR-RESULT.md).

V1 rejected free state vocabulary after zero of four corrections converged. V2
and V2R exposed and exhausted retries on a contradictory prompt/schema contract.
V3 made atomic operations mechanically valid, but free observations still
restaged prior events in three of four outputs. V4 removed prose and still
produced incoherent causes, witnesses and simultaneous workloads in three of
four plans. V5's same-model selector chose none of the sole plan accepted by the
blind reader. These results support a deterministic store and reject the tested
generation boundaries; they do not supply a safe producer.

After deterministic target consumption exists, a new Director contract may be
screened against real payloads. Possession, spatial position and causal
attribution must constrain any producer that emits relations among entities.
Task 72 commitments remain a distinct future domain over this root.
