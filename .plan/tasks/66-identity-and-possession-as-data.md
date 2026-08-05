# Task 66 — Identity and possession as data

> **Status:** open. **Wave 3.** Costs a `SESSION_SCHEMA_VERSION` bump, and task
> 59 wants the same bump — coordinate or one waits.
>
> The first draft of this task was "add a gender field". A blind narrative
> reviewer agreed the field is real and cheap and then showed it **does not touch
> the instances that actually hurt**. The task is broader than the field.

## Problem

Who a character is, and what they are holding, exist only as free prose. The data
model has no anchor for either:

```python
@dataclass
class CharacterMind:
    name: str
    personality: str
    knowledge: list[str]
    current_mood: str

@dataclass
class CharacterBody:
    name: str
    physical_description: str
    outfit: str
```

`src/models.py:47-62`. **No gender, no pronoun, no inventory, no possession.**
Everything the Director and the character agents know about identity comes from
`personality` and `physical_description` as prose, which means it is a prompt
promise — and the phase's finding #1 is that prompt promises lose to anything
with code behind it.

## What it produces, in three escalating kinds

**1. Pronoun flips.** `oldcode-P1-r2`: Nix Pata-Ligeira is "ela" throughout the
session and then

> *"Nix Pata-Ligeira desliza até a fenda… **Ele** se curva, as orelhas felinas
> eretas"*

A gender field fixes this one.

**2. Attribution bleed — a gender field does nothing here.** `base-P1-r2` T23:
three different characters, in one turn, attribute to **Doran** something
**Lucan** offered one turn earlier:

- Bruna: *"**Doran**, ecos da morte não vão achar a carga"*
- Riven: *"Doran quer ler ecos de morte"*
- Maelis: *"Doran, guarde seus ecos para depois."*

T24 is the same class: Nix delivers Bruna's line and acts with *"a braçadeira
direita"* — the bracelet is Bruna's — while Seraphine answers "Bruna". The
Director's model of who-said-what and who-holds-what is wrong, not its model of
pronouns.

**3. Possession with no transfer.** In `base-P1-r1` the emergency seal — the plot
object — is in Garran's palm through T13, in Elowen's palm at T13, demanded from
Link at T15, handed to Link at T17, and back with Elowen at T29. **No transfer is
ever staged.** The object teleports because nothing owns it.

**4. Phantom cast.** Names in dialogue that resolve to no character:

- `base-P1-r2` T2: *"Trio de busca, **Marcos e Lena**, me sigam até o leste"* —
  and a persisted action record *"fazendo sinal para Marcos e Lena me
  acompanharem"*. Neither exists in the 21-name cast. Nobody follows; nobody
  remarks.
- `base-P1-r2` T4: *"**Ferina**, acompanhe Ysara na arquibancada"* — *ferina* is
  the setting's **species** word (elsewhere: *"as orelhas da ferina"*). The
  Director addressed a race as a person.
- `base-P1-r1` T25 and T27: Seraphine thinks about *"**Iria**"* twice, apparently
  a corruption of *"Irmã"*, Elowen's title. `oldcode-P2-r1` has Seraphine address
  "Iria" aloud.

Four of sixteen sessions. Rare, and each one is a hole in the floor. The cast is
a **closed list of 21 ids**, so this is a deterministic check — the cheapest item
in this task and arguably the cheapest in the phase.

## Dependency on task 65

Part of the bleed arrives through the Director-authored speech channel: the T23
and T24 instances are Director-written third-person restatements, not character
agent output. **Task 65 removes that producer.** Measure what remains after 65
before designing anything here — the residue may be much smaller and of a
different kind.

## Direction

Ordered by cost:

1. **Cast integrity check.** A name in dialogue or a persisted record that
   resolves to no cast id is a defect. **The offline scanner moved here from task
   68 on 2026-08-05** — 68 was building five scanners for four wave-1 fixes, and
   this one serves no task before the checkpoint. Scanning the pre-wave-1 archive
   for phantom names measures a population this task's own falsifier expects to
   change. Build it here, against the post-checkpoint corpus. Consider a live
   validator on the path that already validates `witness_ids`.
2. **Gender / pronoun as a field.** Cheap, real, and must survive the
   scenario-preset conversion. Keep the shape simple enough for an LLM to fill
   reliably (per the owner's note in task 59) — not a free-form grammar
   specification.
3. **Possession as data.** The largest piece. An object with an owner, and a
   transfer that must be staged as an event for the owner to change. Overlaps
   task 69's closed transitions — the same machinery, applied to objects rather
   than to scene state. **Task 69 owns the durable-state storage decision for the
   phase** (set 2026-08-05); this consumes the interface it writes down and does
   not build a parallel store.

## Counter-argument, recorded

*"Attribution bleed is a model quality problem, not a data problem — a better
model would keep track."* Possibly true, and it is the reason this is wave 3
rather than wave 1. But the same argument was made about restaging and the
repetition phase found deterministic causes underneath it. The test is cheap:
after tasks 65 and 69, re-scan for bleed. If it has vanished, this task shrinks
to the pronoun field and the cast check.

## Closure evidence required

- [ ] measured **after** task 65: how much attribution bleed remains, and of
      which kind;
- [ ] no name in a persisted record resolves outside the cast — scanner at zero
      over the archive and over a fresh cell;
- [ ] a pronoun field exists, reaches the prompts that need it, and does not
      reach the Director as extra profile detail it is deliberately denied
      (`narrator.py:443-445`);
- [ ] the four built-in scenarios converted, with a byte-identity proof for
      everything except the new field;
- [ ] `SESSION_SCHEMA_VERSION` bumped once, coordinated with task 59, no
      migration branch (`AGENTS.md` §2);
- [ ] if possession ships: an object's owner cannot change without a staged
      transfer event, tested with the `base-P1-r1` seal sequence replayed.

**The measurement that would falsify this task:** if the bleed and the phantom
names disappear once 65 and 69 land, only the pronoun field survives, and it is
a one-afternoon change rather than a task.
