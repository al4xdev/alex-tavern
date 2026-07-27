# Task 34 — Sequential Multi-Character Speech (no Narrator between speakers)

## Goal

Let one narrated turn route SEVERAL characters speaking in sequence, without a
Narrator call between them. First concrete increment of the Decision-layer
direction in `.plan/reference/explore-29.2-architecture-map.md`: the Narrator's
routing output becomes an ordered queue, and later speakers react having heard
the earlier ones. Requested by the user 2026-07-16 ("pode deixar nessa update
múltiplos personagens falarem em sequência sem o narrador").

## Design

- Narrator contract (forward-only, no compatibility path): `next_speaker: str`
  is replaced by `next_speakers: array` (1..3, enum of present IDs +
  "Narrator"). JSON-schema-first per the model guidance: deepseek-v4-flash
  fills typed contracts better than free text.
- Normalization in `narrator.act`: drop unknown/absent entries, dedupe
  preserving order, truncate at "Narrator" (nothing speaks after "no one
  reacts"), cap at 3, empty -> ["Narrator"]. `force_speaker` -> [forced].
- Runner executes the queue sequentially: each response is appended to history
  BEFORE the next character call, so speaker N+1 perceives speaker N's speech
  through the normal visibility filter. The queue stops at the controlled
  character (human agency preserved). `context_for_character` goes to the
  FIRST speaker only; later speakers rely on the fresh history (prevents the
  Narrator from pre-scripting replies it has not seen, a Task 26 defect).
- Turn result contract: `character_responses: [{character_id, speech,
  thought}]` + `next_speakers: [...]` replace `character_response` +
  `next_speaker`. Frontend renders the list.
- Whisper semantics per speaker: reply-audience inheritance applies to each
  queued speaker independently (same formula as before).

## Acceptance Criteria

- [x] Narrator schema/prompt emit and document `next_speakers`. —
  `build_narrator_json_schema`; `TestValidSpeakers` em `test_integration.py`
- [x] Normalization unit tests (unknown/dup/Narrator-terminator/cap/forced). —
  `test_valid_speakers_accepts_custom_id`, `test_valid_speakers_fallback_invalid`,
  `test_forced_narrator_collapses_queue`, `test_forced_speaker_constrains_schema_and_context_target`
- [x] Runner test: queue of two characters produces two responses in order and
  the second character's prompt contains the first one's fresh speech. —
  **confirmado também ao vivo em 2026-07-27**, ver seção no fim
- [x] Runner test: queue stops at the controlled character without generating
  their speech. — `test_autonomous_burst.py::test_stops_when_player_is_addressed`
  (`player_addressed`, nenhuma fala gerada para o controlado)
- [x] Existing agency/presence/whisper guards unchanged (suite green). — suíte
  em 918 testes; `test_absent_next_speaker_never_receives_a_character_call`
- [x] Real-LLM smoke run showing a multi-speaker exchange in one turn. —
  campanha xfailed3 de 2026-07-27 (elenco de 9), ver seção no fim

> **CLOSED 2026-07-16** (commit ae0e001). Delivered: next_speakers queue (1-3,
> ordered), sequential execution with fresh-history perception between
> speakers, agency stop at the controlled character, force collapse under
> plugin filters. Real-run evidence: narrator routed [C3,C2,C4] in one turn
> with genuine interplay (plans/artifacts/task34-smoke). Residual test-fake
> updates delegated to the test-fixing model.


---

# Verificado ao vivo (2026-07-27, campanha xfailed3 `8484d749`)

Os dois critérios de run real ficaram em branco. Rodei a campanha de 24 turnos
com provider real e elenco de **9 personagens** — o cenário certo para isto, ao
contrário das sessões de 2 personagens das outras medições.

**A prova sequencial.** Dois turnos dispararam duas chamadas de personagem em
fila, e nos dois o segundo personagem recebeu a fala **fresca** do primeiro no
próprio prompt:

| turno | fila | fala fresca do primeiro no prompt do segundo |
|---|---|---|
| 19 | Dorothy → Dama do Norte | sim |
| 23 | Watson → Dama do Norte | sim |

## O erro de medição que isso corrigiu

Minha primeira métrica contava *turnos com 2+ falantes distintos no histórico*.
Deu 20 de 24 turnos — número lisonjeiro e **errado**. O turno 5 tem quatro
registros de fala (Player, Van Helsing, Alice, Dama do Norte) e **uma única**
chamada de personagem: as outras três são `audible_speech` escritas pelo Diretor
e persistidas como fala.

São dois mecanismos diferentes com a mesma aparência no histórico. O critério da
34 é sobre a fila de chamadas, não sobre quantos nomes aparecem falando. Medido
pelo mecanismo, o número real é 4 turnos com 2+ chamadas, dos quais 2 são fila
genuína — os outros dois são a mesma personagem chamada duas vezes, que é
**retry de guard**, não fila.

Terceira vez esta noite que a métrica de superfície discordou do mecanismo (as
outras: menções vs. vocativo na 54, e o filtro por nome de agente na 38). O
padrão é consistente o bastante para virar regra: quando o critério fala de um
mecanismo, conte o mecanismo no `debug.jsonl`, nunca o efeito no estado.

> **Ressalva de reprodutibilidade (2026-07-27).** As sessões citadas nesta seção
> foram geradas em diretório temporário e **não estão no repositório**: os números
> não são auditáveis por terceiros nem por uma sessão futura. Foram conferidos por
> mim no momento da execução e o método está descrito acima com detalhe suficiente
> para ser refeito, mas quem reler deve tratá-los como *relato*, não como
> evidência verificável. Medições que precisem valer como prova têm de escrever
> seus artefatos em `docs/` ou `.plan/`, ou o critério deve exigir um script de
> aceitação em `tools/acceptance/` que qualquer um rode.
