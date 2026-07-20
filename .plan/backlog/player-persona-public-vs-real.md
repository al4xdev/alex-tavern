# Backlog — Player character: split PUBLIC persona from REAL persona

**Status:** Backlog — design note, not started (captured 2026-07-20 from live play).
**Origin:** owner observation on session `17b66db3` (Academia, seleção), turns 1-2.
**Related:** 29.2 (subjective state / perspective ledgers), 35 (perception
boundary / Historian), 41 (omniscient Director), 08 (speech audience model).
**Roadmap:** absorbed as **Phase 4 of Task 43** (character disposition substrate)
— public persona = default *prior*, a dyadic Trust/Warmth entry = an observer's
*posterior* deviating from it. See `.plan/tasks/43-character-disposition-substrate.md`
and `docs/cases/15-character-disposition-substrate-2026-07-20.md` §6.

## 1. The motivating moment

Link (the player, C1) is by lore **power 8 — the weakest of the class**: minimal
mana, despised "Portas" support, micro-portals with "quase nenhum poder
ofensivo". He also **hides an other-world origin**. On turn 2 he bluffed
strength — *"Você chama de treino, mas está mais pra massacre"* — and laughed.
Riven (C13) half-saw through it (*"estaria no chão em segundos"*). The scene
worked, but exposed a missing concept.

## 2. What the current architecture already gets RIGHT (do not "fix")

- NPCs perceive Link **subjectively** via their perspective ledgers (29.2):
  Asword "precisão incomum", Riven "suporte miúdo que mal segura uma espada",
  Liora "movimentação impossível abala minha teoria". They DO carry his
  weakness, so irony can land.
- Link's **secret** (other-world origin, exact power level, true portal limits)
  does NOT leak into NPC prompts — the perception boundary (35) holds; no ledger
  mentions "outro mundo". NPCs lacking his full sheet is CORRECT, not a bug.

## 3. The real gap

Link's character sheet (`C1.mind`) is **one blob** that mixes three distinct
things with no first-class separation:
1. **REAL persona** — true stats (power 8), true capabilities/limits, hidden
   origin, secrets. This is what the WORLD should adjudicate against.
2. **PUBLIC persona** — how Link is known / what he presents. This is what seeds
   NPC reactions.
3. **Secrets** — subset of REAL that must never reach any character prompt.

Because there is no split, the engine cannot support the richer mechanic the
moment gestures at: the player deliberately managing a public face that DIFFERS
from the truth.

## 4. Proposed design

Give the player character (and, symmetrically, any character the owner marks) a
declared split:

- **REAL persona → Narrator/Director-side only.** True power, true limits,
  hidden origin. Used to ADJUDICATE outcomes (Link bluffs a massacre; if it
  comes to blows, power 8 loses) and to sustain dramatic irony. Never rendered
  into another character's prompt (reuses the 41 Director-confidentiality and 35
  perception boundary).
- **PUBLIC persona → seeds NPC perception + defines what the player presents.**
  What the room believes about Link by default; the baseline the perspective
  ledgers initialize from. Can deliberately DIFFER from REAL:
  - bluff of strength (present power the player lacks),
  - hidden strength (present weakness, true power concealed),
  - disguise / assumed identity.

NPCs react to PUBLIC (and to what they witness); the Narrator resolves against
REAL. The gap between the two IS the drama — and it is exactly the 29.2 program
("who you are" vs "who others think you are") applied to the PLAYER, where today
it is applied only to how the player sees others.

## 5. Design questions for the owner (decide before building)

- Is PUBLIC persona AUTHORED per character, or DERIVED from REAL minus secrets?
  (Authored enables deliberate bluff/disguise; derived is simpler but cannot lie.)
- Does the player CHANGE their public persona in play (start a bluff, drop a
  disguise), and through what surface?
- How do NPCs UPDATE from public→real when they witness the truth (Link actually
  fights and loses/wins)? This is the ledger-revision path (29.2/39) — a witnessed
  contradiction should revise the perceived persona.
- Adjudication hook: where does the Narrator read REAL to resolve an action whose
  public framing overclaims? (Ties to the player-attempt adjudication rule:
  world-response + return_control, never dictating will.)

## 6. Acceptance (draft — freeze when started)

- [ ] A character can carry a REAL persona and a distinct PUBLIC persona.
- [ ] REAL/secret never appears in another character's or the prose prompt
  (scan NONE, reusing the 35/41 guards).
- [ ] NPC ledgers initialize from PUBLIC, not REAL.
- [ ] The Narrator adjudicates an over-claimed action against REAL (curl-validated
  on a bluff scene: a power-8 character who claims a massacre does not win by fiat).
- [ ] A witnessed contradiction revises the perceived persona (ledger revision).
