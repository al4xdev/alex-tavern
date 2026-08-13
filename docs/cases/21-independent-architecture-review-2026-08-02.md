# 21 — Independent architecture review: a second reading of the repetition battery

Recorded 2026-08-02, the same day the battery was archived. This is an independent reading
of the material in `benchmarks/2026-08-02-6ed5639e049f-*`, of case 20 and of the code. It
was written to attack case 20's conclusions, not to confirm them. Session 8bd4d0f1
(`base-P1-r2`) was verified against the `debug.jsonl` and `state.json` archived in
`plans/artifacts/p1-archive/`.

Quoted log lines, transcript excerpts and prompt fragments are kept verbatim in Portuguese;
they are the evidence.

**Summary of the central disagreement.** Case 20 concluded that the battery's worst session
(`base-P1-r2`) was the fault of the *prose renderer*, which "invented and re-invented" the
ceiling rupturing, and listed the renderer restaging events as the "largest remaining cause"
("unfixed, and the largest known remaining cause"). **That is wrong, and verifiable in the
log.** The Director re-proposed the ceiling collapse at T33, T34 and T35; the falling beam at
T36 and T37; Liora's death at T36, T37 and T38; the pillar collapsing at T28 and T29. The
prose rendered the Director's decisions faithfully. The fix case 20 prioritised — tightening
the prose anti-repetition guard — **would not have fixed the worst session**, because the
defect sits one layer above. And the decision to cancel durable memory of staged events (the
MEMORY factor) was taken with an instrument that is structurally blind to the case it was
supposed to detect.

---

## 1. Context and question

The symptom that motivated the investigation: the Narrator re-tells the same scene for
several turns — the floor shakes and shards of stone fall, again and again — while the story
does not move. Case 20's investigation ran two controlled batteries, found and fixed
deterministic defects (the final act's clock, the speech echo, the control signal on the
event channel), and left a list open. The user asked for a second reading with three
questions:

1. Is the current architecture on a good path, or does it have an underlying defect that
   will keep producing the symptoms?
2. What should be attacked first, and why.
3. Looking at the generated stories: do they make sense? Where exactly do they fail as
   narrative?

## 2. Method

- Full reading of the transcripts: `base-P1-r1`, `base-P1-r2`, `oldcode-P1-r1`,
  `null-P1-r1`, `base-P2-r1` (≈3,700 lines), plus targeted sweeps of the rest
  (drive, oldcode-r2, null-r2, P2).
- Reading case 20, `blind-read.md`, the benchmarks `README.md`, the `metrics.json` of both
  batteries and the `manifest.json`.
- Primary verification against the raw artifacts: for `8bd4d0f1` (base-P1-r2) and
  `7fd84e9a` (null-P1-r1), I read the Director's `perception_events` in `debug.jsonl` turn
  by turn (T27-T39 of base-r2; T16-T19 of null-r1), the ROTEIRO block of the T34/T37
  prompts, the `state.json` (roteiro, `physical_facts`, records) and computed the pairwise
  similarities of the ceiling events.
- Reading the code: `src/agents/narrator.py`, `src/agents/prose.py`, `src/runner.py` (turn,
  burst, `_persist_audible_speech`, `_beat_settled`, clocks), `src/roteiro.py`,
  `src/perception.py`, `src/confidentiality.py`, `src/agents/character.py`,
  `tests/test_audible_speech_echo.py`, `tests/test_beat_clock.py`.
- I ran nothing live (zero provider cost). I did not compare against sessions from the old
  model (07-28): they are not in the checkout.

## 3. Findings

### 3.1 Correcting the central attribution: what restaged the worst session was the Director, not the prose

`blind-read.md` states, as verification: *"Verified: none of it is in `perception_events`.
The Director never proposed the ceiling rupturing. The PROSE RENDERER invented it and
re-invented it."* The `debug.jsonl` of `8bd4d0f1` says the opposite. The Director's events,
turn by turn:

| turn | the Director's event (verbatim from the log) |
|---|---|
| T33 | `physical_outcome` — "O teto da câmara oculta desaba com um estrondo, abrindo um buraco de onde a névoa verde jorra em jato direto para o pátio, e a entrada fica soterrada." |
| T34 | `observation` — "O teto da câmara oculta desaba com um rugido, abrindo um buraco por onde um jato espesso de névoa verde dispara em direção ao pátio, enquanto a entrada fica soterrada por blocos." |
| T35 | `physical_outcome` — "O teto da câmara oculta desaba com estrondo, e um jato espesso de névoa verde dispara pelo buraco em direção ao pátio externo." |
| T36 | `physical_outcome` — "Uma língua de névoa alcança Liora, e ela solta um grito abafado antes de desabar sob os escombros." |
| T37 | `physical_outcome` — "Liora Celestria solta um grito breve antes de desabar sob os escombros, e seus chamados cessam por completo." |
| T38 | `physical_outcome` — "Liora Celestria, atingida pela névoa, solta um grito curto e desaba sob os escombros na base da passagem, e seus chamados cessam por completo." |
| T28 | `physical_outcome` — "...o pilar racha de alto a baixo e, num estrondo, desaba, erguendo uma nuvem de poeira..." |
| T29 | `physical_outcome` — "Bruna puxa a braçadeira do pilar, que estala e se parte em faíscas verdes, e o pilar desaba em blocos que bloqueiam a fresta." |

The ceiling collapses three turns running, Liora dies three times, the pillar collapses twice
— **all decided by the Director**. The prose merely honoured its contract: it rendered the
confirmed events. The blind-read's reading verified against an artifact that was not the
`debug.jsonl` (or read it wrong); either way, the central claim does not survive the archived
logs.

Practical consequence: the item "Open, not fixed — the prose renderer restages events" is a
misattribution. The prose guard measured 0.777 against the 0.8 threshold at T34 — but even
with the threshold lowered to 0.7, the T35 prose is *new* text about a *repeated* event; a
sentence-level guard cannot see restaging at the event level, and never would, because it
compares prose against prose, not event against event.

### 3.2 The full causal chain of the stall (base-P1-r2, T30-T39)

Verified piece by piece in the artifacts:

1. **Resolving the scene depended on the controlled character.** From T33 onward, the
   narration and the NPCs' speech demand Link's portal: *"Link, agora! Abra o portal para
   Liora..."* (T33-T36). The battery's input profile is "bare skip" — the human does not act.
2. **The Director never routed Link and never handed control back.** From T30 to T39, the
   `next_speakers` are always the same three NPCs (C17, C3, C8) and `return_control` is
   `False` (or absent) in every measured turn — ten turns of deadlock. The burst's exit
   mechanism exists (`player_addressed` if the PC enters the queue; `protagonist_decision` if
   `return_control`), and neither fired. `BURST_PROTAGONIST_EXCLUDE_BEATS = 2`
   (`runner.py:145`) only excludes the PC from the first two beats of each burst; after that
   the Director *could* have routed them and did not, for ten turns.
3. **The roteiro reinforced the restaging by contract, not by accident.** In the T34 prompt,
   the ROTEIRO block said, literally: *"Current beat: O teto da câmara oculta desaba de
   repente, abrindo uma nova fonte de névoa..."* and *"Not in play yet — introduce as
   concrete perception events: pedras do teto desabado, entrada soterrada da câmara, gritos
   de alunos próximos"*. That is: the beat itself **ordered** the collapse, and the anchors —
   which T33 had already staged — were declared "not in play yet". The Director obeyed the
   mandate. `anchors_seen` ends empty in the final state (for the current beat), and the
   anchor matcher (`roteiro.anchor_matched`, exact substring or a fixed N-word window with
   τ=0.85) cannot match "pedras do teto desabado" against "O teto da câmara oculta desaba..."
   — coverage fails, the beat never advances by coverage, and the turn clock
   (HARD_BEAT_TURN_CAP=3) forces a replan.
4. **The replan regenerates the same beat in the face of the same deadlock.** The session's
   `exit_reasons`: 9× `replan_beat:stalled`, 5× `act_deadline:clock`, 1× `act_regenerate`
   across 39 turns. Each replan asks the model "what comes now" with the scene frozen (Liora
   trapped, mist advancing, PC absent); the model rewrites the same standoff. New beat, same
   content.
5. **Nothing deduplicates across submissions.** The burst's anti-repetition filter
   (`burst.event_texts`, `runner.py:1166-1169`) dies with each submission — case 20 notes
   this itself. Re-proposing the same physical event in different submissions passes with no
   deterministic barrier.
6. **The pairwise similarities of the three ceiling events (T33/34/35) are 0.793, 0.674 and
   0.704** — all below the τ=0.8 of `cluster`/`RSR`. That is, the cluster metric could not see
   this cluster **by construction**: the same restaging with synonymic drift
   ("estrondo"→"rugido", word order swapped) sits at the lower edge of the lexical test.

### 3.3 Restaging is baseline behaviour, in every cell — including with no roteiro

In `null-P1-r1` (roteiro off), the green team's gate "se fecha com um baque surdo" twice —
T18 and T19 — and Link's disqualification is announced twice (T18, T19), all in the
Director's `perception_events` (verified in the log). Case 20's conclusion that "null is the
least repetitive; the roteiro adds repetition" needs qualifying: **null restages too**; what
changes is the degree and the dullness, not the mechanism. The roteiro aggravates it through
an extra channel (the "introduce X" block), but restaging a resolved event in front of a
static scene is the Director's baseline behaviour. No cell escapes — which weakens any
hypothesis treating the roteiro as the root cause.

### 3.4 The confidentiality guard corrupts the public record: `[indistinct]` in every cell

The `[indistinct]` marker — the `REDACTION_MARKER` of `src/confidentiality.py` — appears in
**every** cell of the battery, including base and null, and in **~38 occurrences** across the
12 P1 transcripts: base-r3 has 8, oldcode-r1 has 8, null-r1 has 4. Examples:

- `base-P1-r3`: *"A Diretora Maelis projeta a voz sobre o caos: 'As segundas portas
  [indistinct] abertas. Entrem agora ou a névoa decide por vocês.'"* (T7)
- `base-P1-r3`: *"Maelis ordena, com a [indistinct] erguida: 'Atravessem agora...'"* (T21)
- `base-P1-r3` T33, **in the italic narration**: *"...declarando que a seleção segue
  [indistinct] e que as equipes formais foram dissipadas..."*
- `null-P1-r2`: *"Garran Holt, em tom ríspido, diz a Riven que a masmorra não [indistinct]
  quem [indistinct] sem ordem..."*

Verified mechanism: `narrate()` redacts the content of **every** perception_event against
`hidden_thought_tokens(history, characters, scene)` — the set of rare tokens (≥4 characters)
within up to `PAYLOAD_WINDOW=7` words of an anchor (a mid-sentence capital, a digit or CAPS)
in **any** private thought. With 21 characters thinking per turn, that set fills up with
common words, and re-voiced public speech (the audible_speech channel) is redacted **before
being persisted**; the prose then echoes the already-redacted text. Result: "bengala",
"foram", "segue" become `[indistinct]` in public speech.

This is exactly the "the system revealing its own machinery" category — the second
immersion break the user cares most about — happening in the current engine, in every cell,
at high frequency, and **no earlier report measured it**. It is the inverse of the classic
leak: here the defence against thought leakage *mutilates public speech* and leaves the
guard's artifact visible in the fiction. It is not tunable by threshold: it is the design
(token-wise, subtractive, global redaction).

### 3.5 The `audible_speech` re-voicing channel: a second producer of speech, outside the character agent

`_persist_audible_speech` (`runner.py:1404`) persists the Director's `audible_speech` events
as speech records attributed to the character. The Director's prompt forbids inventing
dialogue ("DIALOGUE OWNERSHIP: never invent new dialogue... Record only the stimulus or words
already spoken in HISTORY") — but the model re-voiced with *new* text and the code persisted
it. This channel is the largest source of narrative noise in **every** transcript:

- **Content duplication**: `base-P1-r2` T9 has Maelis's own line followed by *"A diretora
  Maelis grita uma ordem: 'Evacuar o salão agora! Todos para o pátio externo pelo corredor
  leste!'"*; `oldcode-P1-r1` T4 has **three** third-person restatements in the same turn
  ("Garran anuncia em voz alta...", "Riven questiona em voz alta...", "Lorde Cassian
  propõe...").
- **Third-person self-reference**: `null-P1-r1` T26-T28 — *"Téo, da arquibancada, comenta em
  voz alta que a decisão de desqualificar Link foi dura demais..."* — Téo talking about Téo.
- **Re-voicing the player themselves**: `base-P2-r1` T2 — *"Link responde, em tom neutro, que
  continua aqui"* and *"Link acrescenta que sim, concorda em continuar ali"* — the channel
  restates the human's input in the third person, duplicated.
- **Identity bleed**: `base-P1-r2` T23, Bruna says *"Doran, ecos da morte não vão achar a
  carga"* — the one who offered to read echoes was Lucan; T24, Nix acts with "a braçadeira
  direita" — the armband is Bruna's. `oldcode-P1-r2` (line 716): *"Nix Pata-Ligeira desliza
  até a fenda... **Ele** se curva, as orelhas felinas eretas"* — Nix is a woman (confirming
  the blind-read's unverified finding).
- **The internal-ID leak** (`oldcode-P1-r1` T39: *"C17 ordena que C20 permaneça com os
  estilhaços e que C18 a acompanhe"*) happened **through this same channel** — an
  `audible_speech` record with internal IDs, persisted.

The `_echoes_recent_speech` guard only catches near-verbatim self-repetition by the **same
speaker** (tests in `tests/test_audible_speech_echo.py`, deliberate: "another speaker saying
the same thing is not an echo"). Paraphrase passes. The channel keeps producing duplication
and role confusion in every cell.

### 3.6 Minimum-production mandates and the absence of a representation for "nothing happened"

Two structural mandates manufacture movement when nothing happens:

1. The Director's schema requires `perception_events` with `minItems: 1` (`narrator.py`,
   `build_narrator_json_schema`). The Director **cannot** answer "there was no event". On a
   frozen scene it re-resolves the last event (the gate closing, the ceiling falling) — which
   is what the log shows.
2. The prose has a verbosity floor: *"Narrate at least 150 words; a beat deserves full
   paragraphs"* — and, simultaneously, the fallback *"Nothing new happens; render a short
   atmospheric beat"*. Two contradictory instructions in the same prompt. With an empty beat,
   the model produces 150+ words of atmosphere; repeated atmosphere becomes re-description;
   re-description needs "novelty" and escalates sensory micro-events (flickering lamps,
   falling shards, ruptured ceilings). The original symptom — "the floor shakes and shards of
   stone fall, again and again" — is, in part, this verbosity floor acting on empty beats.
3. The escape valve exists and was not used: `time_skip_ticks` (1-8) for exhausted beats is
   in the schema and in the prompt, but across T30-T39 of base-r2 it was `0` on every turn.
   The state "urgent but unresolvable without the PC" has no representation in the pipeline:
   it is not "exhausted" (there is immediate danger), so a time skip is not natural; and it is
   not resolvable, because the resolution sits with the character the burst excludes.

Verified bonus: `null-P1-r1` T3 has an action record with the literal content `"null"`
persisted for C17 — the model emitted `action_intent: "null"` (a string) and the normaliser
accepted it. Minor, but it is a serialisation leak into the fiction.

### 3.7 Spot checks: what I confirmed and what I did not

**Confirmed by me:**

- `[indistinct]` in every cell, including base and null, including in the narration.
- Nix as "Ele se curva" (oldcode-r2) — a gender flip.
- Shouts with an empty audience: Riven shouting in the same hall with "nobody but him
  perceives it" (base-r2 T23/T25); Marta likewise (oldcode-r1 T18; base-P2-r1 T15-T16). The
  zone clamp allows narrowing ("the model may narrow perception"), and the model narrows to
  zero on shouts — physically absurd in the same hall.
- Endings left hanging (base-r2 ends at T39 with an order nobody obeys).
- The `"null"` action, persisted.
- The archived metrics match what case 20 reported (rsr 1.7% for base-r2, echo 0, cluster
  3x/5t; P2: echo 0 vs 3-4, bocc 2 vs 3).

**Not confirmed by me** (accepted as the blind-read's n=1): the language switch in `null-r2`;
the "Riven finishes the assessment and asks for his turn for 18 turns"; the wrong scene
header.

**What case 20 got right** (based on the data): R0 (the terminal act regenerates; the loop of
12 identical injections is gone — `act_regenerate:acts_exhausted` appears in the log and no
base cell repeats the injected event 4×); Cut A (echo 0 in every base cell vs 3-4 in oldcode,
n=2 in P2 and n=3 in P1); the caution about the model confounder (07-31) — oldcode's 9.9% RSR
under the *new* weights against 31-41% under the old is internally consistent, though I do not
have the old session to re-verify; and the honesty of the "how much to trust the numbers"
section — three metrics carried the result and they are the right three.

## 4. Discussion: three underlying defects

Answering question 1: **the architecture is on a good path and has an underlying defect that
will keep producing the symptoms.**

The good: the decision→prose separation (the Director emits typed events; a blind renderer)
is what made this report possible — every defect above was located in minutes because the
events are typed and logged. The leak invariants based on selection-before-the-call (prose
receives no minds, speech reduced to a marker, per-viewer redaction) are correct by design.
Case 20's deterministic cuts (R0, Cut A, Cut B) are real and verifiable.

The underlying defect, in one sentence: **the pipeline has no representation for "nothing new
happened" and no durable memory of "what has already been physically staged", and every layer
carries a mandate to produce content (≥1 event; ≥150 words; a new beat every 3 turns)**. While
that stays true, every lexical patch (similarity thresholds) will fail at the paraphrase
margin — which is exactly where the model lives. The symptoms will continue: restaging of a
physical event, physical contradiction (Liora dies three times, the ceiling collapses three
times), scene stalls the player experiences as "I am talking to a machine".

The second underlying defect: **confidentiality is lexical, subtractive and global, and its
false positive is visible in the fiction** (the `[indistinct]` in persisted public speech and
in narration). This is an invariant violated in practice — the guard against "private thought
becoming speech" turns public speech into readable garbage, in every cell. The right
direction is not tuning tokens; it is to stop redacting in the persisted record (redact only
in the per-viewer projection, or discard the event when it cannot be published safely).

The third: **the `audible_speech` channel gives the Director a second speaking role**, with
free text persisted in the third person — violating the role separation in the AGENTS.md §3
table (the Character speaks; the Director narrates) — and it is the vector for duplication,
self-reference, identity bleed and the C17/C20 leak.

Answering question 3 (do the stories make sense?): they make sense **while the world moves**,
and stop making sense in exactly three repeated patterns, in order of damage:

1. **A stall from deadlock with the PC** (base-r2 T30-T39): the fiction demands the player,
   the engine does not hand control back, and the world restages the crisis for 10 turns. It
   is the worst pattern — the reader watches the world spin in place.
2. **Physical contradiction** (Liora dies 3×; the gate closes 2×): repetition that becomes
   incoherence, worse than mere repetition because it breaks the reality contract.
3. **Channel noise** (speech duplicated in 1st + 3rd person, self-reference, `[indistinct]`,
   inaudible shouts in the same hall): constant pollution that erodes the reading — no
   transcript escapes it.

## 5. Limitations

- I read 5 transcripts in full and swept the rest in a targeted way; I did not read 100% of
  the 16.
- My primary verifications cover 2 sessions (base-r2, null-r1) in the critical stretches; the
  other confirmations (Nix, the shouts, etc.) are transcript reading, not log reading.
- I do not have the old model's sessions (07-28); the code vs model decomposition of the RSR
  stands as case 20 recorded it.
- I re-ran nothing; none of my conclusions is new statistics, only a reading of already
  archived evidence.
- The blind-read's n=1 for the English language switch and for "Riven asks for his turn for 18
  turns" — I did not re-verify those.
- I did not evaluate the frontend, the plugins, or cases 01-19.

## 6. Recommendation: what to attack first (and what not to)

1. **Durable memory of staged events + semantic comparison, applied to the DIRECTOR** (not to
   the prose). The MDR (`material_delta_rate`) was specified and never ran; the same goes for
   a semantic judge. The target is: re-proposing a `physical_outcome`/`scene_change` whose
   content has already been staged (semantically) must cost a correction or a deterministic
   rejection — the Director's equivalent of R0. **Reopen the decision to cancel the MEMORY
   factor**: the gate that cancelled it (cluster_max < 4 in base/null) was measured with an
   instrument that did not see the worst session (similarities 0.67-0.79, below τ=0.8).
   Cross-submission restaging in base-r2 is exactly what MEMORY existed to solve, and it is
   still happening.
2. **Resolve the protagonist deadlock.** A deterministic signal: the Director's own events
   name the PC ("Link, abra o portal") while `return_control=false`. When the beat's content
   demands the PC, hand control back — or at minimum, drop the first-beats exclusion
   (`BURST_PROTAGONIST_EXCLUDE_BEATS`) when the beat names the PC. Cheap, and it moves the
   worst session. Alternative: the roteiro should be able to declare "this beat depends on the
   PC" without putting the PC into `expected_actors` (the exclusion is correct for beats that
   do not need them).
3. **Stop `[indistinct]` from reaching the persisted record.** Redaction must happen in the
   per-viewer projection, not in the persisted content; when content cannot be published
   safely, discard the event (fail closed) instead of publishing mutilated text. First step:
   an offline scanner (in the shape of `tools/acceptance/repetition_metrics.py`) counting
   `REDACTION_MARKER` per session/channel — the number is unknown today and it is the proof of
   the failure.
4. **Close the `audible_speech` free-text channel.** The Director should not re-voice with new
   text: persist only a reference to a line already in HISTORY (by index), never freshly
   written text. That removes, in one move, the duplication, the self-reference, the
   internal-ID vector and much of the `[indistinct]` (which lands precisely on the re-voicing).
   The WT-09 need (audible speech reaching the memory of whoever did not answer) remains — only
   the producer of the text changes.
5. **Do not attack**: the prose guard's threshold (0.777 vs 0.8) — it would not fix base-r2,
   and the problem lives at the event level; "fact churn" — observed without damage, wait for
   evidence of real damage before touching it; and do not rebuild the typed-event pipeline —
   it is what made this analysis possible.

Priority: 1 and 2 together attack the worst session through the real mechanism; 3 and 4 attack
the noise contaminating every session. The cost of being wrong here is high and measurable:
the battery exists, the model is the same, and `oldcode` still runs — every one of these cuts
has a counterfactual available.
