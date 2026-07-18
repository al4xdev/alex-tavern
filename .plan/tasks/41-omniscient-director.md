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
- [ ] Diretor recebe thoughts rotulados (todos os donos); replay real adjudica
  sem vazar (validado V1-V3).
- [ ] prosa/personagem/summarizer/ledger continuam SEM ver thoughts de outros
  (testes estruturais explícitos).
- [ ] Guard: token exclusivo de thought nunca aparece em perception_events.
- [ ] Zona dinâmica: mover pra zona nova cria isolada + palco pros demais;
  witnesses clampados por construção.
- [ ] Prosa renderiza com canon reconciliado (ordem corrigida).
- [ ] xfailed3 (famílias de vazamento) re-validado quando o relógio do xfail
  rodar.

## DELIVERED 2026-07-18 — ressalva pequena: revalidação xfailed3 pendente

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
