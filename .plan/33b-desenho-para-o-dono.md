# 33b — Desenho do watcher de transição de cena (pra você aceitar/vetar)

Tudo abaixo já foi validado por exploração curl em payloads reais
(2026-07-19, ver task 33b). Nada disso encosta no turno canônico sem o
toggle; OFF por padrão.

## As três peças

```text
turno commitado
      │
      ▼
[1] AUDITOR DE DELTA MATERIAL (1 call pequena, ~400 tokens out)
    "Este turno produziu delta material? Qual categoria?"
    categorias: decision_taken, information_revealed,
    position_or_access_changed, attempt_got_consequence,
    relationship_changed, threat_advanced,
    possibility_opened_or_closed, none
      │  (validado: detectou imobilidade semântica nos turnos
      │   travados do sorteio que âncora lexical não vê)
      ▼
[2] LADDER DE RECUPERAÇÃO (determinística, código — doc §6)
    contador de turnos sem delta consome o RELÓGIO da 40
    degraus 1-4: pressões leves já existentes (drive, hint de
    pressão, force_speaker, replan de beat)
      │  só no degrau final:
      ▼
[3] INTERVENÇÃO CAUSAL (1 call, só quando a ladder esgota)
    contrato: source_thread (evidência citada por turno) →
    event_now → expected_delta → refractory_turns
    (validado 3/3: toda intervenção cresceu de thread existente,
     zero "figura encapuzada do nada")
      │
      ▼
    vira narrator_hint (canal UPCOMING EVENT — o mesmo do
    drive/33, da disrupção/38 e do deadline do relógio/40)
```

## Decisões de desenho (minhas propostas — veta o que não gostar)

1. **Auditor roda a cada turno** quando o toggle está ON (custo: 1 call
   pequena/turno). Alternativa mais barata: só quando `narrative_tick -
   último_delta > 1`. Começo pela versão a cada turno na fase experimental
   (dado melhor), decido depois com número real de custo.
2. **A ladder é 100% código** — o LLM nunca decide "quando intervir", só
   responde às duas perguntas (houve delta? qual intervenção causal?).
   Mesma doutrina do relógio: o tempo/pressão não pertence à LLM.
3. **Refratário respeitado**: após intervenção, `refractory_turns` (o modelo
   pediu 3 em 3/3 runs) sem nova intervenção, contando pelo tick da 40.
4. **Confidencialidade**: threads/intervenção só chegam ao Diretor (como
   roteiro/schedule). Personagem e prosa nunca veem.
5. **Fronteira com a 40**: o deadline de ato dispara PELO RELÓGIO (tempo);
   o watcher dispara POR ESTAGNAÇÃO (falta de delta). Dois gatilhos, o mesmo
   canal de entrega, nunca no mesmo turno (deadline tem precedência; watcher
   entra em refratário quando o deadline enfileirou evento).
6. **Log**: cada auditoria e intervenção logadas no debug JSONL
   (`watcher:delta`, `watcher:intervention`) pro harness medir.

## O que a bateria A/B/C vai medir (com você acordado)

A = livre (sem watcher) / B = disrupção arbitrária / C = watcher causal.
Métricas do doc §7: taxa de delta material sustentada, threads
abertos-vs-resolvidos, necessidade de re-intervenção, coerência causal por
crítico cego. Previsão registrada: C vence em drive sustentado + coerência.

## Custo estimado

Auditor: ~1 call pequena/turno (só com toggle ON). Intervenção: rara (só
degrau final). Fase experimental: harness/replay primeiro, integração ao
runner só depois do seu aceite do desenho + bateria.
