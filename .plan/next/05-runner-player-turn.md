# 05 — Quebrar `Runner.player_turn`

> ✅ **Aplicado em `9f43c36`** (branch `refactor/pre-1.0-cleanup`, 2026-07-26) — aplicado integralmente

**Escopo:** `src/runner.py:360-1120`
**Esforço:** L · **Risco:** médio (é o caminho quente do produto) · **Quebra contrato:** nenhuma
**Depende de:** doc 01 (o null object tira ~19 branches antes de você começar)

## Sintoma

```
src/runner.py:360:15: PLR0912 Too many branches (80 > 12)
src/runner.py:360:15: PLR0915 Too many statements (245 > 50)
```

760 linhas em um único método. Para comparação, o segundo maior do arquivo,
`_compact_loaded_game`, tem 63 statements — e já é grande.

O método é bom código: cada bloco tem comentário explicando a decisão de produto
e a evidência que a motivou (Task 37, 40, 41, 45, WT-09...). O problema não é
qualidade linha a linha — é que **12 responsabilidades dividem um escopo de
variáveis**. Hoje `step`, `narrator_hint`, `injected_event`, `audience`,
`queue`, `narrator_raw`, `scene_up`, `narration`, `character_responses`,
`burst_event_texts`, `narrator_only_streak` e `stop_reason` são todas visíveis
ao mesmo tempo, e três delas (`step`, `narrator_hint`, `audience`) são
reatribuídas dentro do loop.

## Por que é dívida agora

1. **Não dá para testar um estágio isolado.** Todo teste de burst, watcher,
   roteiro ou whisper precisa mockar o Director inteiro e rodar o turno completo
   (é o que `tests/test_autonomous_burst.py`, `test_watcher_integration.py` e
   `test_audible_speech_persistence.py` fazem — daí a duplicação do doc 12).
2. **`narrator_hint` é um canal disputado por quatro produtores** (drive
   scheduler `:620`, clock invite `:637`, act deadline `:650`, watcher `:662`),
   com a precedência expressa como uma cadeia de `if not narrator_hint.strip()`.
   A regra existe e é intencional, mas está codificada na ordem física das
   linhas — não em nenhum lugar que se possa ler, testar ou documentar.
3. É o arquivo que qualquer feature nova de turno vai tocar. Entrar na 1.0 com
   ele assim significa que toda feature 1.x nasce dentro de um método de 245
   statements.

## Proposta

Manter tudo em `Runner` (a orquestração é dele, `AGENTS.md` §3) e extrair **em
métodos privados por estágio**, com dois objetos de estado pequenos:

```python
@dataclass(slots=True)
class TurnInput:
    speech: str; thought: str; action: str
    force_speaker: str | None; narrator_hint: str; skip: bool
    audience: list[str] | None
    transformed_fields: list[str]

@dataclass(slots=True)
class BurstState:
    beats: list[dict]; event_texts: list[str]
    narrator_only_streak: int = 0
    stop_reason: str = "budget_exhausted"
```

Estágios (nome → o que sai hoje):

| Método novo | Linhas atuais |
|---|---|
| `_validate_audience(game, audience, speech, action)` | 413-424 |
| `_resolve_turn_input(game, raw, step)` → `TurnInput` | 426-484 |
| `_maybe_automatic_compaction(game, ti, step)` | 486-569 |
| `_persist_player_input(game, ti, step)` | 571-597 |
| `_resolve_beat_hint(game, step, beat_index, ti)` → `(hint, injected)` | 611-666 |
| `_director_beat(game, step, ti, beat_index)` → `narrator_raw` | 668-740 |
| `_apply_canon(game, narrator_raw)` → `scene_up` | 765-806 |
| `_apply_time_skip(game, narrator_raw, step)` | 808-837 |
| `_render_and_prepare(game, narrator_raw, queue, step)` → `narration` | 839-869 |
| `_run_speaker_queue(game, queue, narrator_raw, ti, step)` → `responses` | 871-973 |
| `_persist_audible_speech(game, narrator_raw, step)` | 975-1026 |
| `_commit_beat(game, narrator_raw, responses, step, injected)` | 1028-1076 |
| `_beat_stop_reason(...)` → `str \| None` | 1087-1103 |

`player_turn` sobra com ~60 linhas: lock, validação, compactação, persistência
do input, o `for beat_index in range(max_beats)` chamando os estágios em ordem, e
a montagem da resposta.

**O ponto de maior valor é `_resolve_beat_hint`.** Ela transforma a precedência
implícita em explícita:

```python
# Um único canal, quatro produtores, precedência declarada:
#   1. narrator_hint do jogador (nunca sobrescrito)
#   2. drive scheduler (evento autônomo, só no beat 0 de um skip)
#   3. act deadline do roteiro (world_event já escrito no planejamento)
#   4. clock invite de compressão de tempo
#   5. watcher (fallback semântico quando nada mais carregou a cena)
```

e passa a ser testável em 5 casos deterministas, sem rodar turno nenhum.

## Bônus no mesmo arquivo

- **`game.__dict__.update(copy.deepcopy(compacted.__dict__))`**
  (`runner.py:1443`). É a única mutação por `__dict__` do projeto, e existe
  porque o chamador segura a referência de `game` e precisa vê-la compactada.
  Trocar por um `replace_state(game, compacted)` explícito (ou por retornar o
  `compacted` e o chamador reatribuir) remove a única linha do runner que depende
  do layout interno da dataclass.
- **Quatro dicts de resultado de compactação** montados à mão
  (`runner.py:529-538`, `551-560`, `1329-1338`, `1445-1458`) com as mesmas 8
  chaves. Um `_compaction_result(status, trigger, **extra)` mata ~40 linhas e a
  chance de uma delas divergir.
- **`_append_history`** começa com `if audience_origin is not None: pass`
  (`runner.py:2106`) — um `if` cujo corpo é um comentário. Inverter para
  `if audience_origin is None:` e cair no cálculo de zona.

## Passos

1. Fazer o doc 01 antes (menos branches para mover).
2. Extrair na ordem da tabela, **um método por commit**, rodando
   `uv run pytest` a cada um. Nenhuma mudança de comportamento em nenhum passo —
   é refatoração pura, e o suite de 785 testes é a rede.
3. Só depois de tudo extraído, escrever os testes novos e baratos de
   `_resolve_beat_hint` e `_beat_stop_reason`.
4. Rodar um playtest real (`tools/playtest_harness.py`) comparando o
   `debug.jsonl` de um burst antes e depois: mesma sequência de agentes, mesmo
   `stop_reason`.

## Como validar

- `uv run pytest` (785) verde em **cada** commit da série;
- `uvx ruff check --select PLR0912,PLR0915 src/runner.py` sem `player_turn`;
- um burst de 4+ beats real: `log_burst` com o mesmo `beat_count`/`stop_reason`
  que antes, e um undo revertendo exatamente um beat.

## Não fazer

- **Não** mover os estágios para um módulo `src/turn/` novo agora. Eles usam
  `self.config`, `self.client` e `self.plugins`; virar funções livres exigiria
  passar os três a cada chamada, trocando um método longo por acoplamento
  espalhado. Se depois de extraído ficar claro que um subconjunto é puro
  (`_resolve_beat_hint` e `_beat_stop_reason` são candidatos), aí sim promove.
- **Não** aproveitar para "melhorar" nenhuma regra narrativa no meio da
  refatoração. Toda linha movida deve ser idêntica; qualquer mudança de
  comportamento vira tarefa separada com o método curl-first do `AGENTS.md` §6.
</content>
