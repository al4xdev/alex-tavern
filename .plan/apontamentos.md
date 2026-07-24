# Apontamentos — revisão dos commits após `3a20b95` (2026-07-24)

> **Resolução (2026-07-24, decidida com o dono):** A4 aceito — os benchmarks
> do Task 44 ficam como estão. A3 e A5 corrigidos no working tree (detalhes em
> cada item). A1/A2 registrados sem ação. Nada mais pendente desta revisão.

Escopo: os 16 commits `3a20b95..43fff9a` (feitos com um modelo menor).
Estado verificado em HEAD (`43fff9a`): **747 testes passam**, `ruff` limpo,
`mypy` no escopo documentado do AGENTS.md com **1 erro pré-existente** (já
existia no commit base — ver A3). Nenhum segredo vazado no diff. Links de
`.plan/` citados no README todos resolvem.

---

## A1 — `b076ad3` não compila isoladamente (hazard de bisect) 🟡

`b076ad3` (`fix(45): count player actions...`) adiciona em `src/runner.py` o
import de `log_unanswered_player`, mas a função só é criada no commit
**seguinte** (`f233506`, em `src/llm/debug_log.py`). Naquele commit o app
inteiro morre com `ImportError`.

- Impacto: zero em HEAD; quebra apenas `git bisect` / checkout daquele ponto.
- Já está publicado em `origin/master`, então **não** recomendo rebase.
- Ação proposta: nenhuma correção de código; registrar e seguir. Se um dia um
  bisect passar por ali, pular o commit (`git bisect skip`).

## A2 — `b076ad3` embute mudanças sem relação com o assunto 🟡

O mesmo commit "fix(45)" também:
1. **Reabre o Task 44** (rename `.plan/closed/44 → .plan/tasks/44`, R100) sem
   mencionar isso na mensagem — a reabertura só é explicada dois commits depois
   (`e345a02`).
2. Introduz o log de observabilidade `unanswered_player` (assunto do `f233506`).

- Impacto: só higiene de histórico/rastreabilidade. Sem ação de código.

## A3 — mypy: 1 erro pré-existente no escopo documentado 🟢

`uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py ...` (comando do
AGENTS.md §validação) reporta:

```
tools/playtest_harness.py:669: error: Incompatible types in assignment
```

- O arquivo é **idêntico** ao do commit base `3a20b95`; o erro já existia lá.
- Os commits revisados até **melhoraram** o quadro: os 2 erros antigos de
  `tools/mcp_server.py` foram corrigidos pelo `cast` em `43fff9a`.
- ✅ **Corrigido (2026-07-24):** a segunda ocorrência reaproveitava a variável
  `narration` do loop anterior (tipo `str`) para receber `output.get(...)`
  (`Any | None`); renomeada para `decision_narration`. Escopo mypy do
  AGENTS.md agora zera.

## A4 — Evidências dos gates do Task 44 não são reproduzíveis do repo 🟡

`fb6ddea` fecha o Task 44 citando: benchmark do deriver 18/18 (6 beats × 6
personagens, provider real), replicação do gate v3 com Cassian, boundary HTTP
real (PUT /config → impulso no prompt do C18) e boundary visual 1080p/2K.
Os payloads brutos ficaram em `plans/` (**gitignored**) — o próprio doc admite
e por isso inline-ou os resultados.

- Pontos a favor da veracidade: o outline de foco declarado
  (`rgb(176, 108, 255) solid 2px`) bate exatamente com `--accent-2: #b06cff`
  do `style.css`; o padrão de escrita "falha honesta v1 → correção → v2"
  inclui um caso reprovado (1/3) em vez de só sucessos; a correção de prompt
  citada existe de fato em `src/alignment.py` e está travada por teste.
- Ponto contra: nada disso é verificável por quem clona o repo, e foi um
  modelo menor que reportou as execuções.
- ✅ **Decisão do dono (2026-07-24): aceito.** Os resultados estão bons; os
  benchmarks ficam como registrados no doc do Task 44.

## A5 — Oráculo WT-06 ficou mais permissivo (`dc426ee`) 🟢

O regex do benchmark `test_xfailed3_counter_canon.py` agora aceita
`(?:não|nenhum|sem)[^.]{0,80}(?:sobrenatural|vampir)` como cobertura da
mortalidade pública. Janela de 80 chars pode casar falso positivo do tipo
"não sei se ele é sobrenatural".

- Impacto: só no benchmark xfailed3 (não roda no CI normal, marker `llm`).
  Tem self-test do padrão. Risco baixo.
- ✅ **Corrigido (2026-07-24):** lookahead negativo rejeita verbos de
  incerteza entre a negação e o termo sobrenatural (`sei`, `sabe(mos)`,
  `saber`, `será`, `seria`, `talvez`, `certeza`); self-test ganhou três
  frases de incerteza que o padrão antigo aceitava.

## A6 — Desserialização estrita nova (`49b581e`) — verificada, OK 🟢

`dict_to_game_state` e `dict_to_turn_record` agora exigem
`data["dispositions"]` / `data["disposition_snapshot"]` (KeyError se ausente).
Verifiquei que é seguro **por design**: o gate de `SESSION_SCHEMA_VERSION`
(agora 13) roda **antes** da desserialização em `src/store/sessions.py:106` e
recusa sessões antigas; checkpoints de compactação têm gate próprio
(`runner.py:1505`). Registro apenas como convenção a manter: qualquer caminho
futuro que construa `TurnRecord` de dict **sem** passar pelo gate vai estourar.

## A7 — Ordem snapshot × appraisal de disposição — verificada, OK 🟢

No `49b581e` cada `TurnRecord` grava `disposition_snapshot` no append, e
`_apply_disposition_feedback` só roda depois de todos os appends do step
(`runner.py:1070`), então o undo restaura o estado pré-turno corretamente,
inclusive em bursts multi-beat (cada beat tem step próprio).

---

## Resumo

| # | Commit | Gravidade | Ação |
|---|---|---|---|
| A1 | `b076ad3` | 🟡 histórico | registrado; `bisect skip` se precisar |
| A2 | `b076ad3` | 🟡 higiene | nenhuma |
| A3 | pré-existente | 🟢 lint | ✅ corrigido (`playtest_harness.py`) |
| A4 | `fb6ddea` | 🟡 evidência | ✅ aceito pelo dono |
| A5 | `dc426ee` | 🟢 benchmark | ✅ regex apertado + self-test |
| A6 | `49b581e` | 🟢 verificado | manter convenção |
| A7 | `49b581e` | 🟢 verificado | — |

Nenhum bug funcional encontrado no código em HEAD. Pós-correções:
747 testes passando, `ruff` limpo, `mypy` (escopo AGENTS.md) sem erros.
