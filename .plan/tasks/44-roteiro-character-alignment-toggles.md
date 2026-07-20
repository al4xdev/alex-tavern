# Task 44 — Toggles de roteiro e alinhamento dramático dos personagens

**Status:** 🟡 ABERTA (definição inicial, 2026-07-20)
**Origem:** primeiro playtest real do roteiro na sessão `380ea657`. O Diretor
compilou uma direção dramática, mas personagens coerentes com o mundo reagiram de
modo capaz de interromper essa direção. Exemplo observado: diante do líquido azul
perto do portal, Cassian pediu o fechamento dos portais. A reação é plausível numa
simulação, mas pode desmontar o beat que pretende fazer o grupo atravessá-los.

## Progresso (2026-07-20)

**Feito — Toggle 1 (roteiro on/off):** `roteiro_enabled` exposto em Settings
(`index.html` + `runtime-config.js` populate/collect + i18n PT/EN). Round-trips (o
bug do reset — collect omitia o campo — some pra ele) e **aplica em runtime sem
restart** (PUT /config reconstrói o Runner, main.py:709-712). Falta verificação
Playwright (dono confere no olho).

**Pendente — Toggle 2 (personagens seguem o roteiro):**
`character_roteiro_alignment_enabled`, condicional ao primeiro, com o AVISO
permanente. Precisa do mecanismo de alinhamento (contexto dramático derivado →
Character) e do gate curl "roteiro completo vs direção local derivada". É o grosso
da task. Ver também a ponte com a Ousadia (43) abaixo.

## A conclusão afiada (por que o toggle existe) — do dono, 2026-07-20

A simulação ficou boa demais: personagens coerentes viram gente real discutindo
coisas aleatórias, e a história não anda nem com o Narrador presente. O roteiro NÃO
existe pra deixar o personagem esperto — existe pra **licenciar a escolha
dramaticamente produtiva que um agente coerente nunca faria**: se separar do grupo,
abrir a porta, cruzar a ponte podre. É a lógica do filme de terror ("não se
separem!" — e eles se separam, porque é história). Sem roteiro, todo mundo sobrevive
racionalmente e nada acontece: **real, porém chato.** O toggle é a escolha honesta —
*verdade (sim-livre) ou história (alinhada)* — e quem quiser o real tem disponível.

**Ponte com a Task 43 (disposição):** o eixo **Ousadia** (cauteloso↔temerário, hoje
estacionado) é o dial dessa "burrice dramática". O alinhamento não precisa DITAR "se
separe do grupo" — ele empurra a Ousadia do personagem pra cima e ele escolhe a
temeridade SOZINHO, preservando a trava de agência. A disposição é o mecanismo
honesto do alinhamento: muda o que o personagem SENTE (mais audaz), não o que FAZ.
Isso dá casa à Ousadia (que falhou o gate de fala-única na 43) — o valor dela não é
ser lida na prosa, é **inclinar a ESCOLHA** sob o roteiro. Ver `.plan/tasks/43`.

## Problema

Personagens pertencem ao mundo e agem de acordo com personalidade, conhecimento e
percepção. Quando somente o Diretor conhece o roteiro, um personagem pode agir de
forma perfeitamente coerente e, ao mesmo tempo, desfazer a composição dramática.

Isso não é necessariamente um bug: na vida real, as pessoas não conhecem nem seguem
um roteiro. Porém, Alex Tavern também precisa permitir uma experiência mais próxima
de uma história dirigida, na qual o elenco contribui para o beat em vez de
acidentalmente cancelá-lo.

O produto deve tornar essa escolha explícita, configurável e compreensível, sem
fingir que simulação livre e atuação dramaticamente alinhada são a mesma coisa.

## Decisão de produto a implementar

Adicionar dois toggles independentes em **Settings**:

### 1. Roteiro da história

- Chave proposta: `roteiro_enabled` (já existe no backend).
- Liga a compilação do roteiro privado e seu consumo pelo Diretor.
- OFF: o Diretor improvisa a progressão a partir do estado, histórico e diretivas.
- ON: atos, beats, condições de saída e relógio narrativo orientam o Diretor.
- Deve ser configurável no frontend; não exigir edição manual de `.data/config.json`
  nem reinício do backend.

### 2. Personagens seguem o roteiro

- Chave proposta: `character_roteiro_alignment_enabled`.
- Disponível apenas quando `roteiro_enabled` estiver ON; quando o roteiro estiver
  OFF, o controle fica desabilitado e explica o motivo.
- OFF: personagens recebem somente o mundo que perceberam e agem de forma
  independente. Eles podem contrariar, atrasar ou desmontar o roteiro, exatamente
  como pessoas reais que não sabem que existe uma história planejada.
- ON: cada personagem roteado recebe contexto dramático derivado do roteiro para
  poder contribuir com a direção da história.

## Aviso obrigatório na interface

O segundo toggle precisa exibir um aviso claro, e não apenas um tooltip escondido.
Texto-base em português:

> Sem esta opção, os personagens agem de forma independente e podem contrariar o
> roteiro, levando a história a resultados mais caóticos, como pessoas reais que
> não sabem que existe um plano. Ao ativá-la, os personagens passam a colaborar com
> a direção dramática, mas podem parecer mais guiados e menos espontâneos.

Texto-base em inglês:

> When this is off, characters act independently and may work against the
> screenplay, producing more chaotic outcomes, like real people who do not know a
> plan exists. When enabled, characters collaborate with the dramatic direction,
> but may feel more guided and less spontaneous.

Os nomes finais e a microcopy devem passar por revisão visual e de i18n, mantendo o
trade-off visível antes da escolha.

## Questão de desenho que a implementação deve medir

O pedido de produto é permitir **passar o roteiro aos personagens**, mas a forma
exata ainda precisa de evidência curl-first. Comparar pelo menos:

1. **Roteiro completo:** o Character recebe o beat/ato privado relevante.
2. **Direção local derivada:** o Character recebe apenas sua função dramática no
   beat atual, sem atos futuros nem intenções de outros personagens.

Não decidir por preferência arquitetural. Pré-registrar métricas e executar 3–4
runs por variante em payload real. A variante escolhida precisa demonstrar:

- maior contribuição ao beat do que a condição OFF;
- manutenção da voz e dos objetivos próprios do personagem;
- ausência de menções metalinguísticas a roteiro, beat, Diretor ou história;
- ausência de vazamento de eventos futuros para fala, pensamento ou ação;
- nenhuma decisão, fala, coragem, revelação ou ação atribuída ao personagem
  controlado.

Se o roteiro completo vazar spoilers ou transformar personagens em executores
mecânicos, usar direção local derivada como representação funcional do toggle e
documentar a decisão. O toggle continua significando “personagens seguem o
roteiro” para o usuário, mesmo que a fronteira interna compartilhe apenas o recorte
necessário.

## Bug pré-existente descoberto (2026-07-20) — provável causa do "roteiro OFF"

`PUT /config` usa `merge_config_update`, que só preserva os **segredos de provider**;
os demais campos top-level vêm do corpo enviado, e `save_config → validate_config`
**re-defaulta o que faltar**. O `collect()` do frontend (`runtime-config.js`) envia
apenas `active_provider`, `language`, `compaction_*`, `providers` e (agora)
`autonomous_burst_max_beats` — **omite `roteiro_enabled` e `auto_event_*`**. Logo,
**todo save pela UI reseta `roteiro_enabled` para False** (e `auto_event_*` para os
defaults). É a causa mais provável de o roteiro ter sido encontrado desligado.
Esta task DEVE corrigir isso ao expor `roteiro_enabled` no frontend: o `collect()`
tem que round-tripar o campo (populate lê, collect envia), e idealmente todo save
deve ser não-destrutivo para campos que a UI não edita (merge completo, não replace
com defaults). Testar as 4 combinações + que salvar a UI não zera `roteiro_enabled`.

## Contrato e ownership

- Config canônica e validação: `src/config.py`.
- Persistência: `.data/config.json`, usando o fluxo existente `GET/PUT /config`.
- UI e serialização: `src/static/runtime-config.js`, `index.html` e i18n.
- Roteiro continua sendo produzido e mantido por `src/roteiro.py`.
- O Runner entrega ao Character somente o contexto permitido pela opção ativa.
- OFF deve preservar o contrato atual: nenhum texto do roteiro entra no prompt de
  Character.
- ON nunca pode contornar a trava de agência do personagem controlado.
- Mudança de toggle deve reconstruir/aplicar a configuração runtime sem exigir
  restart manual.

## Comportamento de sessão

- Ligar `roteiro_enabled` numa sessão cujo `game.roteiro` é `null` compila o
  roteiro no próximo turno sob o lock da sessão e persiste o resultado.
- Desligar impede manutenção/replan e consumo do roteiro; definir explicitamente se
  o roteiro persistido é preservado inerte ou removido. Como o projeto é
  forward-only, deve existir um único comportamento canônico, sem leitura dupla.
- Religar não pode aplicar silenciosamente uma direção obsoleta ao estado atual:
  decidir e testar regeneração ou revalidação explícita.
- O toggle de alinhamento só afeta chamadas futuras; nunca reescreve falas antigas.

## Observabilidade

O debug JSONL deve permitir distinguir:

- roteiro OFF;
- roteiro ON somente para Diretor;
- roteiro ON com alinhamento de Character;
- qual recorte dramático foi entregue a cada Character, com os mesmos limites de
  confidencialidade do prompt correspondente;
- impacto de latência da compilação/replan e das chamadas normais.

Nenhuma chamada LLM nova pode omitir `session_id`, `turn_number` ou `agent`.

## Aceite

- [ ] Settings possui os dois toggles com traduções PT-BR e EN.
- [ ] `roteiro_enabled` pode ser alterado sem editar JSON ou reiniciar o backend.
- [ ] O segundo toggle fica condicionado ao primeiro e mostra o aviso permanente.
- [ ] OFF mantém personagens independentes e prova por teste que roteiro não entra
      em prompt de Character.
- [ ] ON aumenta alinhamento ao beat em replay curl-first real sem metalinguagem ou
      vazamento de futuro.
- [ ] Personagem controlado continua exclusivo do humano em todas as combinações.
- [ ] Config pública, persistência, segredo em branco e troca de Runner continuam
      corretos.
- [ ] Testes cobrem as quatro combinações dos toggles, input inválido e troca em
      runtime.
- [ ] Boundary HTTP real confirma PUT → Runner ativo → próximo turno.
- [ ] Boundary visual em 1080p e 2K confirma legibilidade do aviso e estados
      enabled/disabled/focus.
- [ ] README explica a diferença entre simulação livre e história dirigida.
- [ ] Evidência curl e decisão final ficam registradas antes de fechar a task.

## Fora de escopo

- Plugin de self-healing ou reescrita retroativa.
- Alterar falas e eventos já persistidos.
- Permitir que qualquer agente escolha ações ou pensamentos do protagonista.
- Ocultar do usuário o custo de espontaneidade do modo alinhado.
