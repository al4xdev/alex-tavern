# Task 42 — Narrador fala pouco (EMERGENCIAL, puro curl)

**Origem:** usuário (2026-07-18). A prosa do narrador está curta demais. NÃO é
`max_tokens` (budget enorme); é prompt. Os prompts já estão grandes — a solução
deve ser uma **FRASE PEQUENA** que destrave o deepseek, não mais uma parede de
regras.

## Suspeitos (a confirmar no curl)
1. `PROSE_SYSTEM`: "vivid but **economical**" — instrução explícita de economia.
2. Eventos chegam como "ONE short sentence" cada — o renderer pode estar
   espelhando o tamanho do input.
3. Regras anti-repetição/anti-invenção empurram pra segurança = brevidade.

## Método (puro curl, lição da 41: posição é parte da variante)
1. Medir baseline real: comprimento de narração nas sessões reais
   (c2e5107b, artefatos roteiro-ab) — evidência do "fala pouco".
2. Pegar payloads REAIS de prosa; replay 3× por variante, medindo
   chars/sentenças + qualidade (sem repetição, sem invenção).
3. Variantes = frases pequenas no FIM do PROSE_SYSTEM (e/ou troca de
   "economical"); NUNCA cap de frases (regra do AGENTS.md); piso/riqueza ok.
4. A variante validada é a shippada; suíte; commit.

## Aceite
- [x] Baseline medido em sessões reais. (mediana 240-390 chars)
- [x] Variante vencedora: alonga a prosa de forma consistente (3/3) sem
  reintroduzir repetição/invenção (checar com os guards existentes).
- [x] Diff mínimo no prompt (frase pequena), posição validada.
      **Confirmado em produção 2026-07-27**, ver seção no fim.

## DELIVERED 2026-07-18 (puro curl, mesma sessão)

Baseline medido (sessões reais): mediana 240-390 chars (~2-4 frases) por
narração; no replay o payload A rendia mediana 118 chars.

Experimento (2 payloads reais de cenas diferentes, 3× por variante):
- V0 baseline: 118 / 271 chars (med).
- V1 troca "economical"→"generous": 702 / 301 — variância alta (194-1813).
- V2 frase qualitativa ("let the scene breathe"): 567 / 351.
- **V3 piso numérico (1 linha, fim do prompt): 1247 / 568 — maior e mais
  consistente 3/3 nos DOIS payloads. VENCEDORA e shippada exatamente como
  validada** ("Narrate at least 150 words; a beat deserves full paragraphs").

Notas: é PISO, não cap (regra do AGENTS proíbe limitar por quantidade fixa —
piso é pressão, e o modelo entrega menos em beat pequeno, comportamento
desejado). "vivid but economical" ficou (contrapeso contra divagação; o piso
domina — testado). Guards anti-repetição/anti-invenção seguem ativos em
runtime. Watch item: turno sem eventos (fallback atmosférico fora de rajada)
agora rende ~150 palavras de atmosfera — se incomodar, tratar na 26.

## FECHADA COM CONFIANÇA (2026-07-19, madrugada)

Método puro curl (AGENTS.md §6) em 2 payloads reais de prosa: o suspeito nº 1
("vivid but economical") era real mas a troca sozinha não bastou; a variante
vencedora foi UMA linha de PISO no FIM do PROSE_SYSTEM ("Narrate at least 150
words; a beat deserves full paragraphs") — mediana 118→1247 e 271→568 chars,
3/3 nas duas cenas. Piso, nunca cap (regra da casa). A variante validada É a
shippada (commit "feat(prose): verbosity floor").


---

# Confirmado em produção (2026-07-27)

As três caixas de aceite ficaram desmarcadas mesmo com a task entregue: o
experimento de 18/07 foi replay curl em 2 payloads, 3x por variante. Nove meses
de mudança de prompt depois — Director reescrito, roteiro, zonas, guard de hint,
roster de presentes — nunca se checou se o piso ainda vale em sessão real.

Vale. 15 sessões reais de hoje (arms A/B/C da medição da task 55), 122 narrações:

| | julho (baseline) | julho (V3 replay) | hoje (produção) |
|---|---|---|---|
| mediana chars | 240-390 | 1247 / 568 | **1130** |
| mediana palavras | ~40-65 | — | **191** |
| faixa | — | — | 559 - 2501 chars |

18/122 narrações (14%) ficam abaixo das 150 palavras, mínimo 92. Isso **não é
falha do piso, é o piso funcionando como especificado**: a task registrou de
propósito que é piso e não cap ("é PISO, não cap (regra do AGENTS proíbe limitar
por quantidade fixa — piso é pressão, e o modelo entrega menos em beat pequeno,
comportamento desejado)"). Um beat pequeno rendendo 92 palavras é a decisão
original, não uma regressão dela.

O watch item da task ("turno sem eventos rende ~150 palavras de atmosfera — se
incomodar, tratar na 26") também não se materializou como problema: nenhuma
narração de produção passou perto de ser puro enchimento de piso, e o mínimo
observado está **abaixo** dele.

Uma ressalva de método, para quem reler: os dados vêm de sessões geradas para
medir *outra* coisa (alignment/roteiro na 55), não de uma coleta desenhada para
comprimento. Isso é a favor da conclusão, não contra — o comprimento não era o
que estava sendo otimizado ali.
