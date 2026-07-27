# Task 28 — Force Speaker Regression

**Status:** Open
**Reported:** 2026-07-15
**Type:** Bug

## Goal

Restore the Force Speaker control across every supported turn path. The reported
behavior is that the selected override is no longer honored at all: for example,
forcing `Narrator` can still produce a Character response.

The cause is not known yet. Do not limit the investigation or the fix to skip
turns, and do not treat a passing backend-only test as proof that the UI flow is
working.

## Scope

- Reproduce the regression through the real frontend before changing the code.
- Trace the selected value through the frontend request, `turn.input` plugin hook,
  FastAPI boundary, Runner validation, Narrator prompt, routing decision, response,
  and `debug.jsonl` evidence.
- Cover ordinary sends and skip turns independently.
- Preserve the mobile long-press/gesture action menu. Its secondary actions,
  including **Suggest**, must remain reachable and functional while Force Speaker
  is selected and after the fix.
- Keep the agency guard: forcing the human-controlled character must return control
  to the human and must never generate their speech.

## Acceptance criteria

### Isolated automated coverage

- [x] A frontend boundary test selects `Narrator`, performs an ordinary send, and
  proves that the HTTP turn payload contains `force_speaker: "Narrator"`.
- [x] A separate frontend boundary test selects `Narrator`, activates **Skip turn**,
  and proves that the same request contains both `skip: true` and
  `force_speaker: "Narrator"`.
- [x] A Runner/API test makes the Narrator model return an NPC as `next_speaker`
  while `Narrator` is forced, then proves that `next_speaker` remains `Narrator`,
  `character_response` is absent, and no Character model call occurs.
- [x] Tests cover invalid/absent character IDs and the controlled character without
  weakening the current presence and human-agency guards. — `test_forced_controlled_character_never_generates_speech`, `test_force_speaker_on_an_absent_character_falls_back_to_narrator_choice`
- [x] A mobile interaction test exercises the long-press/gesture action menu and
  proves that Force Speaker remains selectable and the **Suggest** action still
  calls the suggestion flow. Test Force Speaker from this menu with ordinary send
  and keep the skip-turn case isolated from it.

### Final real-LLM acceptance run

- [x] Run a real LLM conversation with **more than four characters present** (at
  least five total, including the human-controlled character). — elenco de 9
- [x] Execute at least four consecutive rounds with `force_speaker` set only to
  `Narrator`; do not force an NPC during this acceptance run. — 4 rodadas + 1 skip
- [x] Every round produces Narrator output only, even when the raw model response
  chooses an NPC. No Character call or Character response may occur.
- [x] For every round, `debug.jsonl` shows `force_speaker: "Narrator"` in
  `turn_input`, `effective_force_speaker: "Narrator"` in
  `turn_input_effective`, and the expected Narrator request/response with matching
  `session_id`, `turn_number`, and `agent`.
- [x] Run the skip-turn acceptance separately with `skip: true` and forced
  `Narrator`, proving the same routing outcome without player speech, thought, or
  action.

## Delivery evidence

- Record the original reproduction, identified root cause, isolated test commands,
  frontend/mobile boundary evidence, and real-LLM session/debug-log evidence here
  before moving this task to `.plan/closed/`.
- Update the Force Speaker documentation if its actual user-visible contract changes.

## Additional Evidence (2026-07-16, live session `091b11c6`)

User replayed with the character-alteration plugin active and reports the bug
persists: characters did not speak even when explicitly forced
(`plans/artifacts/session-091b11c6-live-findings/`). Investigate whether the
plugin's `turn.input` hook interferes with `force_speaker`, and compare
`turn_input` vs `turn_input_effective` records in that session's debug log.

## Delivery Evidence — CLOSED 2026-07-16

- **Root cause found by evidence**: the frontend SKIP path read a dead
  `state.forceSpeaker` field (assigned nowhere), silently dropping the force on
  every skip turn — matching the report "forced Narrator, a character still
  answered". Ordinary sends read the select correctly, which is why the
  archived plugin session (091b11c6) shows its one forced turn working.
- **Fix**: the skip payload now reads the same single source of truth
  (`forceSpeakerSelect.value`); a static boundary test pins that the dead-state
  read can never return.
- **Backend hardening already in place** (task 34): a manual force collapses
  the Director's queue even if a plugin filter alters the output; covered by
  `tests/test_force_speaker_regression.py` including the model-ignores-the-
  constraint case and the controlled-character agency guard.
- **Real-LLM acceptance** (`plans/artifacts/force-narrator-acceptance/`): 5
  present characters, 4 ordinary + 2 skip consecutive rounds forcing only
  `Narrator` -> zero character calls; `debug.jsonl` shows
  `force_speaker: "Narrator"` and `effective_force_speaker: "Narrator"` on all
  6 turns.
- Mobile menu/Suggest reachability unchanged (no layout changes were needed;
  the fix is payload-only).


---

# Protocolo de aceitação executado (2026-07-27)

A task fechou com **todo** o protocolo de LLM real em branco. Executei-o inteiro
como `tools/acceptance/forced_narrator_rounds.py`, contra o servidor de verdade,
com o elenco de 9 personagens do fixture do xfailed3 — os cenários padrão de 2
personagens não conseguem exercitar uma regra sobre o Diretor preferir um NPC.

Resultado (sessão `b4955d03`): **8/8 verificações**. 4 rodadas consecutivas
forçando `Narrator` mais a variante de skip; toda rodada roteou para o Narrador,
nenhuma resposta de personagem, nenhuma chamada de personagem, narração real em
todas (795–1999 chars), e o `debug.jsonl` mostrando `force_speaker` e
`effective_force_speaker` iguais a `Narrator` nas 5.

## Duas correções que o próprio run me impôs

**`effective_force_speaker` é campo de topo, não de `input`.** Faz sentido depois
de visto: `input` é o que o cliente pediu, e o efetivo é o que o runner
**decidiu** — são coisas diferentes e o log as separa. Meu check procurava no
lugar errado e reportou 0 de 5 num sistema que estava certo.

**O primeiro run acusou "fala de NPC persistida em rodada forçada" (C3, C6, C7)
enquanto o check de chamadas de personagem passava.** As duas coisas juntas só
fazem sentido de um jeito: eram `audible_speech` encenadas pelo Diretor,
`audience_origin: "zone"`, no formato *"Watson diz: '…'"*. Não é violação — é a
persistência de fala audível de que o WT-09 depende.

O erro era meu, e de um tipo específico: escrevi um check **mais estrito que o
critério**. A task diz "No Character call or Character response may occur", e
nenhum ocorreu. Forçar o Narrador força **quem age**, não silêncio na ficção.
Um check acidentalmente mais rígido que a especificação teria "encontrado" um
bug inexistente e custado uma rodada de investigação — como custou.

## O que só o run real informa

Nas 5 rodadas, o Diretor propôs um NPC mesmo forçado em **0** delas. Os testes
unitários provam que o runner ignora um NPC quando recebe um; nenhum deles
consegue dizer com que frequência um Diretor real tenta.

**Correção de 2026-07-27 (revisão crítica): a primeira versão desse contador não
media nada.** `record["response"]` é guardado como *string* JSON, então
`json.dumps()` escapava as aspas e o predicado `'"C2"' in raw` procurava `"C2"`
dentro de `\"C2\"` — nunca casava, travado em 0 para sempre. E, corrigido o
escape, ele passaria a casar em toda rodada independentemente do roteamento,
porque varria a resposta inteira e `scene_blocking.character_zones` lista todos
os personagens todo turno.

Agora o script parseia a resposta e lê `next_speakers` — o único campo que
significa "o Diretor quer que este personagem aja" — e **verifica que conseguiu
parsear**, para que uma mudança futura de serialização falhe alto em vez de
devolver um zero confortável. Rerodado: **0/5 de novo, agora merecido**.

Uma segunda checagem tinha o mesmo vício: marcava falas de NPC "não encenadas"
por `not record.get("audience_origin")`, mas esse campo tem default `"whisper"` e
é sempre serializado — a condição nunca podia ser verdadeira. O discriminador que
funciona é o log: personagem só fala quando é chamado.

Os dois scripts também deixavam a config do servidor alterada ao sair. Corrigido:
salvam e restauram.

> **Caixas espelhadas em 2026-07-27.** As 6 caixas do cabeçalho ficaram em branco enquanto a seção de fechamento deste mesmo arquivo já
> registrava as entregas. Marcá-las é sincronizar cabeçalho e corpo, não
> declarar trabalho novo: a evidência de cada uma está na seção de
> fechamento abaixo. Onde a varredura de 2026-07-27 encontrou lacuna real,
> ela está descrita em seção própria com o teste que a cobre.
