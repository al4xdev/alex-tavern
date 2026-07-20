# Task 26b — Re-descrição de ambiência: ataque via PROMPT (experimental)

> **Status: ⏸️ PARQUEADA — resultado NEGATIVO (documentado no artigo No. 13).**
> 24 calls, 3 variantes em 2 iterações: TODAS pioraram a banda (16.4%→21-23%) —
> a linha sobre cenário vira ímã de atenção. Ataque via prompt fechado como
> beco. Direção futura: nível dos eventos (delta-material da 33b), não prompt.

**Origem:** decisão do dono (2026-07-19): "via prompt, se não der fallback
pra tentarmos parquear". Task experimental, filha da lane 26.

## Evidência que motiva (medição offline 2026-07-19)

4 sessões reais, 549 sentenças de narração comparadas com narrações
anteriores (script `measure26.py`):

- Eco quase-verbatim (≥0.8): 2 casos em 549 — e ambos porque a compactação
  escondeu a sentença anterior da guarda. A guarda determinística de prosa
  está funcionando.
- A família dominante é OUTRA: **paráfrase de ambiência** na banda 0.7–0.8
  (~9% das sentenças). Exemplos reais: "o estojo de prata sob o pedestal
  continua lacrado" → "o estojo de prata jaz esquecido, seu lacre intacto";
  "a fita azul não se move" re-observada turno após turno.
- Threshold fuzzy não resolve: >0.85 nunca dispara; baixar pra 0.7 mataria
  callbacks legítimos.

## Hipótese

O renderizador de prosa re-descreve objetos/estado que NÃO mudaram porque
nada no prompt diz que ambiência só merece tinta quando muda. Uma regra
pequena no FIM do PROSE_SYSTEM (posição validada nas tasks 41/42) pode
redirecionar essa tinta pro que aconteceu AGORA.

## Método (obrigatório: AGENTS.md §6, igual à 42)

1. Extrair 2+ payloads reais de prosa de turnos com re-descrição medida
   (usar `replay_extract_call` do MCP novo; sessões xf-full T9/T12/T19 têm
   casos medidos).
2. Testar variantes de UMA linha via `replay_llm_call`, 3 runs cada,
   métrica dupla: (a) taxa de sentenças 0.7–0.8 vs narrações anteriores
   (reusar `measure26.py`), (b) tamanho — NÃO pode derrubar o piso da 42
   (as duas regras vão conviver; medir juntas).
3. Candidatas iniciais (afinar no curl):
   - "Spend your words on what changed or happened this beat; setting
     already described stays as silent backdrop unless it changes."
   - variante com permissão explícita de callback intencional.
4. A variante validada É a shippada, mesma posição testada.

## Aceite

- [ ] Banda 0.7–0.8 cai de forma consistente nos payloads medidos (alvo:
      ~9% → <4%) sem quebrar o piso de verbosidade da 42 (3/3 acima do piso).
- [ ] Zero novas regras além de 1 linha; nunca cap.
- [ ] Se não atingir em ~2 iterações de variante: **parquear** (decisão do
      dono) e registrar o resultado negativo aqui.

## RESULTADO (2026-07-19): NEGATIVO em 2 iterações → PARQUEADA (fallback do dono)

24 calls em 3 payloads reais de prosa (T9/T12/T19 de ce87167b, turnos com
re-descrição medida), 2 runs por variante por turno; métrica: % de sentenças
na banda ≥0.7 vs narrações anteriores + palavras (piso da 42):

| Variante | banda ≥0.7 | palavras med |
|---|---|---|
| V0 baseline | **16.4%** (9/55) | 146 |
| V1 "silent backdrop" | 22.4% (15/67) | 179 |
| V2 V1+callback | 21.3% (16/75) | 213 |
| V3 proibição direta ("zero words") | 22.8% (13/57) | 192 |

TODAS as variantes PIORARAM a banda. Leitura: qualquer linha que menciona
cenário/re-descrição funciona como ímã de atenção — o modelo re-afirma o
estado parado por contraste ("o estojo continua lacrado") justamente porque a
regra o fez pensar nos objetos estabelecidos. O piso da 42 não foi violado
(min 118-151), mas as linhas também INFLAM o tamanho.

Direção futura (se despertar de novo): não é prompt — é o nível dos EVENTOS.
O renderizador cego só orna o que o Diretor emite; a re-descrição residual
entra quando eventos re-encenam estado parado. Candidato real: auditoria de
delta material da 33b marcando evento-sem-delta antes da prosa. Fica pra
depois da integração do watcher.
