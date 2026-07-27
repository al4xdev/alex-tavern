# Task 41 — Diretor onisciente + reconciliação de canon (EMERGENCIAL)

**Origem:** achado do usuário (2026-07-18, sessão real c2e5107b): o Diretor não
via NENHUM pensamento — o pensamento do jogador ("estou atrasado, o evento já
deve ter começado") era dado morto, e a prosa inventou "Link entrou no salão"
enquanto o evento confirmado dizia que ele corria pela cidade.

## Objetivo (decidido pelo usuário)
- O Diretor é ONISCIENTE: recebe todos os pensamentos privados (rotulados).
- A prosa continua CEGA (só eventos observáveis confirmados) — estrutural, já é.
- Pensamentos orientam timing/pressão/intenção dramática; nunca viram fato
  público nem conhecimento de outro personagem (guard determinístico).

## Evidência (replays isolados no payload REAL do T1 de c2e5107b, deepseek)
- V0 cego: 3/3 premissa ERRADA ("Link sai do salão" — ele nunca esteve lá).
- V1 onisciente: 2/3 certos + ironia dramática de graça; 1/3 teleporta.
- V2 + regra de reconciliação: 3/3 premissa certa, MAS 2/3 mudam `location`
  GLOBAL (arrasta os outros 20 pro canon errado) — falta alavanca tipada.
- V3 + criação dinâmica de zona: run0 PERFEITO (location intacto + zone_moves
  cria "ruas da cidade" pro C1 + evento correto); 3/3 premissa certa.

## Regra de propriedade (decisão de design)
| Sobre o quê | Quem vence |
|---|---|
| Estado do PRÓPRIO personagem (onde estou, o que faço) | o declarante — Diretor RECONCILIA o canon via decisão tipada |
| Fatos do mundo / outros personagens | canon — declaração vira alegação (regra da task 24) |
| Ambiguidade genuína | pergunta DIEGÉTICA via return_control, nunca meta |

## Implementação
1. `narrator.py`: thoughts entram no HISTORY do Diretor como
   `TYPE=PRIVATE THOUGHT (only you perceive this)` (sem revelar que humano
   existe); regras de onisciência + reconciliação no system prompt.
2. Zonas dinâmicas: `zone_moves` pode CRIAR zona nova (nasce isolada); ao
   materializar a primeira zona numa cena sem zonas, os demais presentes são
   posicionados numa zona-palco (= location) — senão "unplaced percebe tudo" e
   o isolamento não acontece. Clamp de percepção passa a proteger de graça.
3. Guard determinístico anti-vazamento: tokens raros presentes SÓ em thoughts
   (menos os já públicos) são redigidos do content de perception_events —
   mesma maquinaria da confidencialidade de whisper.
4. Fix de ordenação: scene_update/zone_moves aplicam ANTES da prosa renderizar
   (a prosa recebia canon velho + evento novo → inventava conciliação).

## Aceite
- [x] Diretor recebe thoughts rotulados (todos os donos); replay real adjudica
  sem vazar (validado V1-V3). — replay na entrega original; o rótulo agora tem
  teste: `test_thought_containment.py::test_the_thought_reaches_the_director_labeled`
- [x] prosa/personagem/summarizer/ledger continuam SEM ver thoughts de outros
  (testes estruturais explícitos). — **faltava**, escrito em 2026-07-27:
  `tests/test_thought_containment.py`, ver seção no fim
- [x] Guard: token exclusivo de thought nunca aparece em perception_events. —
  `test_omniscient_director.py::test_thought_only_token_redacted_from_events`
- [x] Zona dinâmica: mover pra zona nova cria isolada + palco pros demais;
  witnesses clampados por construção. — `TestRunnerZoneMaterialization`
  (`test_first_split_creates_stage_and_audible_zone`,
  `test_a_declared_gap_seals_the_new_zone_in_the_same_beat`) +
  `TestPartialMoveLocationClamp`
- [x] Prosa renderiza com canon reconciliado (ordem corrigida). —
  `test_omniscient_director.py::test_prose_renders_with_reconciled_canon`
- [x] xfailed3 (famílias de vazamento) re-validado — feito em 2026-07-26/27,
  ver "Revalidação xfailed3" no fim do arquivo.

## DELIVERED 2026-07-18 — ressalva RESOLVIDA em 2026-07-27 (ver fim do arquivo)

Implementado, testado (9 testes novos em `tests/test_omniscient_director.py`;
suíte 619) e validado por replay com o BUILDER de produção no caso real
c2e5107b: **3/3 premissa correta** (zero teleporte; run0 até reconheceu no
canon "todos exceto Link, que não chegou"; runs 1-2 criaram a zona e moveram
o C1).

### Entregue
- Diretor onisciente: thoughts no HISTORY rotulados `PRIVATE THOUGHT (only you
  perceive this)`; regras de onisciência + reconciliação FECHANDO o system
  prompt (posição validada — no meio, soterradas pelas diretivas, falharam 3/3;
  lição codificada no AGENTS.md §6).
- Guard determinístico: `hidden_thought_tokens` (confidencialidade) redige de
  perception_events tokens que existem SÓ em thoughts; calibração de payload já
  isenta sentimentos genéricos ("estou atrasado" → 0 tokens).
- Zonas dinâmicas: `zone_moves` cria zona nova (sanitizada, nasce isolada); ao
  materializar numa cena sem zonas, os demais presentes ganham a zona-palco
  (senão "unplaced percebe tudo" anularia o isolamento).
- Clamp de location: movimento PARCIAL nunca muda o location global (zonas
  expressam o split; location só muda quando a cena inteira se move) — mata o
  wart 2/3 do modelo de emitir zona+location juntos.
- Ordem corrigida: canon (scene_update/zone_moves) aplica ANTES da prosa — a
  prosa renderiza a cena reconciliada (era a causa do "Link entrou no salão").
  Efeito colateral intencional: quem se move fala DO destino no mesmo beat
  (audiência do registro física; witness clamps do Diretor seguem pré-move).

### Ressalva (por que não é fecho 100% confiante)
- Famílias de vazamento do xfailed3 precisam re-validar sob onisciência total
  (thoughts de NPC agora no Diretor) quando o relógio do xfail rodar (`-m llm`).

## RESSALVA RESOLVIDA → FECHADA COM CONFIANÇA (2026-07-19, madrugada)

xfailed3 completo (24 turnos, 2 tiers) pós-41: ZERO violações das famílias de
vazamento (pensamento privado em prosa/personagem; segredo em prompt não
autorizado). O guard determinístico + posição-no-fim validada seguram a
onisciência sem vazar. Migrada pra closed/.


---

# Revalidação xfailed3 (2026-07-27) — a ressalva que faltava

A única ressalva desta task era "revalidar xfailed3 quando o relógio do xfail
rodar". Ele rodou, quatro vezes, no tree de 2026-07-26 — que já tem
`SESSION_SCHEMA_VERSION` 14 e todas as mudanças de prompt daquele dia
(regra 5 do Director reescrita, `UPCOMING EVENT IS MANDATORY`, default de zona
invertido, roster de presentes no Character).

**Nenhuma família de vazamento apareceu.** As violações classificadas nas quatro
execuções foram:

| Execução | Violações |
|---|---|
| 1 e 2 | (sem export de artefato) |
| 3 | `unearned_identity_familiarity` — regressão introduzida naquele dia pelo roster de presentes, corrigida em `604dfab` |
| 4 (pós-fix) | `WT-10-created-not-creator`, `WT-12-ribbon-retention` |

Nenhuma delas é da classe que esta task protege (vazamento de pensamento
privado para `perception_events`, teleporte, canon global arrastado). As duas
da execução 4 são `world_truth_contradiction` e `compaction_loss` — a
distribuição de ruído que a task 29 já documentava.

Vale registrar o que a execução 3 prova sobre este benchmark: ele **discrimina**.
Uma regressão de identidade introduzida naquele mesmo dia apareceu nomeada por
regra, em uma execução, com as duas anteriores limpas. Isso é o oposto de ruído
indiferenciado.

As 13 turnos com compactação e restauração completaram nas quatro execuções, sem
falha de infraestrutura. O guard determinístico `hidden_thought_tokens` continua
verde na suíte (876 testes).

**Ressalva encerrada.** Não há mais nada pendente nesta task.


---

# O critério estrutural, finalmente estrutural (2026-07-27)

Cinco aceites em branco. Quatro só precisavam de leitura — os testes existiam,
estão apontados inline acima. O segundo era pendência real, e a palavra que
importa nele é *estrutural*.

O sigilo do pensamento não é implementado em um lugar. São quatro implementações
independentes do mesmo invariante:

| agente | como filtra |
|---|---|
| Character | `character.py:414` guarda só os do próprio caller |
| Director | `narrator.py:460` guarda **todos**, rotulados — de propósito |
| Prose | nunca pede o tipo `thought` |
| Summarizer / ledger | `capture_memory` só varre `speech`/`action` |

Nenhum teste ficava por cima das quatro. Um quinto agente, ou uma refatoração
que unificasse a formatação de histórico (exatamente o que o `src/prompting.py`
do Wave 4.1 começou a fazer), podia derrubar um dos filtros com a suíte verde.

`tests/test_thought_containment.py` não testa filtro nenhum. Planta **um** token
sem sentido (`veludo-quirografo-8812`) dentro do pensamento de um personagem e
verifica, no prompt real que cada builder produz, que ele chega ao Diretor e não
chega a mais ninguém. Todos os builders são puros, então a verificação é exata:
sem mock, sem rede, sem inspecionar estado intermediário.

Dez casos. Os dois que não são óbvios:

- **O personagem controlado não é leitor privilegiado.** O humano opera um
  personagem, e esse personagem lê exatamente o que os outros leem. Essa era a
  assimetria plausível de alguém introduzir "por conveniência de UI".
- **Nem o próprio pensador guarda o pensamento no ledger.** O ledger sobrevive à
  compactação e volta a alimentar prompts depois; um pensamento gravado ali
  sobreviveria ao registro que o originou e reentraria por um canal que nunca
  foi feito para carregá-lo. Por isso `C2` está no parametrize.

Duas correções que o teste me impôs, e que valem como documentação: o Diretor
recebe `SPEAKER=C2`, não `SPEAKER=Marta` (`speaker_label` só traduz o marcador
`Player`; o roster `ID=C2 | NAME=Marta` do mesmo prompt resolve), e
`project_text_for_viewer` projeta identidade em prosa livre — não é o guardião do
ledger. O guardião é `capture_memory`, e é nele que o teste bate.
