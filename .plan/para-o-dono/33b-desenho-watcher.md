# 33b — Desenho do watcher de transição de cena (pra você aceitar/vetar)

> ## ✅ RESOLUÇÃO (2026-07-19, noite — autorizada por você antes de dormir)
>
> Você concordou com **1, 2, 3, 5, 6** e com as **2 decisões da bateria**
> (integrar watcher atrás de flag = SIM; drive adotar contrato causal = SIM).
> A **#4** ficou em dúvida sua → resolvida por **curl em janela real**, não por
> hipótese (regra de decisão pré-registrada). Veredito: **#4 ACEITA como está
> (só-Diretor).** Todas as 8 decisões fechadas. Evidência abaixo e em
> `plans/artifacts/watcher-decision4/` (local, gitignored).
>
> **Experimento #4** (2 janelas reais: sorteio `ccb521ab`, incêndio `e7760040`;
> deepseek-v4-flash; 4 runs/braço; juiz cego):
>
> | Nível | Métrica | 4a (cego/shipped) | 4b (personagem vê pressão difusa) |
> |---|---|---|---|
> | Personagem | iniciativa (0-2) | **1.88** | **2.00** |
> | Personagem | inventa evento externo (risco de colisão) | 0/8 | 0/8 |
> | Personagem | meta/quebra de imersão | 0/8 | 0/8 |
> | Personagem | vaza o evento do Diretor | — | **não (0)** |
>
> | Nível de EVENTO | coerência causal (0-2, juiz cego, média de 3) |
> |---|---|
> | causal (ancorado em thread) | **1.83** (fogo 2.0 / sorteio 1.67) |
> | chapado/arbitrário | **0.00** (ambas as janelas, todos os runs) |
>
> **Leitura:** rotear o sinal do watcher ao personagem (relaxar #4) rende
> ~0.12 de iniciativa num teto que o prompt-base já satura (1.88) — ruído. E o
> travamento NÃO é falta de iniciativa do personagem: no 4a eles JÁ tomam
> iniciativa (1.88) e mesmo assim o turno não produz delta material — falta a
> **consequência externa nova**, que só o evento concreto do Diretor entrega e
> que o personagem não deve fabricar (é a colisão que a #4 previne). O valor do
> watcher vive inteiro no nível do Diretor/evento — exatamente onde a #4 o põe.
> Bônus: o nível de evento mostra o alvo — causal 1.83 vs chapado **0.00** de
> coerência — o que **reforça a Decisão B da bateria** (seeds do drive adotarem
> o contrato causal: o chapado é o "cristal sem causa").


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
