# 06 — Resíduo de retrocompatibilidade (contra o `AGENTS.md` §2)

> ✅ **Aplicado em `333de4c`** (branch `refactor/pre-1.0-cleanup`, 2026-07-26) — aplicado integralmente

**Escopo:** `src/config.py`, `src/models.py`, `src/store/sessions.py`,
`src/agents/character.py`, `src/confidentiality.py`
**Esforço:** M · **Risco:** baixo · **Quebra contrato:** config e sessão — **é o objetivo**

O `AGENTS.md` §2 proíbe "leitura dupla de config, scenario, sessão ou log" e
"campos antigos mantidos por segurança". Três lugares ainda fazem exatamente
isso.

## A — migração de config v1 → v2

```python
# src/config.py:20
LEGACY_CONFIG_SCHEMA_VERSION = 1
```

Usada em `config_schema_version:256,260,263` e `load_config:284,287`, que lê um
arquivo sem `schema_version`, carimba `2` e regrava. Em volta disso existe
`src/runtime_bootstrap.py` inteiro (51 linhas) com o parâmetro
`persist_migration=False` e um `try/except` que **engole a exceção** para não
derrubar o servidor no boot.

Custo hoje: um caminho de código, um parâmetro público e um módulo de bootstrap
existem para converter um formato que este projeto nunca publicou em release.

**Proposta:** apagar `LEGACY_CONFIG_SCHEMA_VERSION` e o ramo de migração.
`config_schema_version` passa a rejeitar qualquer coisa != 2. Config v1 no disco
vira erro explícito ("apague `.data/config.json`") — que é a política declarada
para dado local incompatível.

**Cuidado:** `runtime_bootstrap.prepare_runtime_config` **não** existe só para a
migração; ele também aplica a Experience padrão (`before_the_war`) no primeiro
boot, e o `persist_migration=False` é o mecanismo de "tentar de novo no próximo
boot quando o celular está sem rede". Esse comportamento precisa sobreviver — a
condição de disparo é que muda: em vez de "config < v2", passa a ser "config
existe mas nenhuma Experience foi aplicada ainda" (uma flag própria, p. ex.
`bootstrap_experience_applied`, ou a simples ausência de
`.data/plugins/started/`). Ler `tests/test_runtime_bootstrap.py` antes de mexer.

## B — defaults mortos nos desserializadores

`src/store/sessions.py:106` já **recusa** qualquer sessão cujo
`schema_version != 13`. Logo, tudo que `dict_to_game_state` lê com `.get(chave,
default)` para campos que existem desde a v13 é código inalcançável:

```python
src/models.py:555  snap.get("zones", {})            # v4+
src/models.py:556  snap.get("positions", {})
src/models.py:562  data.get("audience_origin", "whisper")   # v6+
src/models.py:563  data.get("perspective_snapshot", {})     # v3+
src/models.py:634  data.get("character_perspectives", {})
src/models.py:636  data.get("turns_since_injected_event", 0)  # v5+
src/models.py:638  data.get("narrative_tick", 0)             # v7+
src/models.py:639-641  watcher_*                             # v11+
src/models.py:643  data.get("schema_version", 1)   # ← nunca pode faltar: o loader já validou
```

O mesmo padrão em `dict_to_roteiro:323-357` (18 `.get` com default) e
`dict_to_perspective:140-155`.

**Proposta:** acesso direto (`data["zones"]`) para tudo que a v13 garante.
Um `KeyError` num arquivo corrompido é melhor do que preencher silenciosamente
um default e continuar — e `list_sessions` já trata `KeyError` como sessão
ilegível (`sessions.py:27`). Manter `.get` **apenas** onde o campo é
genuinamente opcional no schema atual (`data.get("roteiro")`, que é `None`
quando o roteiro está desligado).

Ganho real: quando você subir para a v14, o desserializador falha alto no campo
que faltou em vez de fabricar um default plausível.

## C — `getattr` defensivo sobre dataclasses próprias

```python
src/agents/character.py:334   getattr(rec, "audience_origin", "whisper")
src/confidentiality.py:153    getattr(rec, "audience_origin", "whisper")
src/confidentiality.py:231    getattr(rec, "audience_origin", "whisper")
src/agents/character.py:155   getattr(viewer_perspective, "memory_summary", "").strip()
src/agents/character.py:158   getattr(viewer_perspective, "recent_memory", [])
```

`TurnRecord.audience_origin` é campo declarado com default desde `models.py:207`;
`CharacterPerspective.memory_summary`/`recent_memory` idem (`models.py:129-130`).
Os `getattr` são de quando esses campos ainda não existiam. Trocar por acesso de
atributo — e, nos dois de `character.py`, o `viewer_perspective` pode ser `None`,
então o guard correto é `if viewer_perspective is None: return ""`, que é o que
o código quer dizer.

Bônus relacionado: `src/config.py:164`
`validate_api_base = getattr(adapter, "validate_api_base", None)` com fallback
para `parse_api_base`. O método está no `Protocol` (`llm/adapters/base.py:104`) e
os dois adapters built-in o implementam. Ou o protocolo é obrigatório (então
chama direto) ou é opcional (então declare `validate_api_base: Callable | None`
no protocolo). O `getattr` com fallback é a terceira opção, a que não se
documenta.

## D — o comentário de schema que já reconhece o problema

`src/models.py:33-37` documenta que `Roteiro.beat_actions_elapsed` **não** subiu
a versão por ser "puramente aditivo". A decisão está bem justificada, mas é
precisamente o precedente que produz a classe (B) acima. Com a 1.0, vale
fechar a regra: **campo novo com leitura defensiva = bump de versão**, sem
exceção "aditiva". O custo é zero (`AGENTS.md` §2: quebrar sessão é barato e
previsto) e a recompensa é que `dict_to_*` nunca mais precisa de default.

## Passos

1. (B) e (C) primeiro: são mecânicos e sem risco.
2. (D): registrar a regra no `AGENTS.md` §2.
3. (A) por último, com `tests/test_runtime_bootstrap.py` e
   `tests/test_provider_config.py` na mão — é o único item com lógica de boot
   envolvida.

## Como validar

- `uv run pytest tests/test_session_schema_version.py tests/test_provider_config.py
  tests/test_runtime_bootstrap.py tests/test_data_isolation.py`;
- abrir uma sessão v13 existente em `.data/sessions/` e conferir que carrega;
- forjar um `state.json` com um campo removido e conferir que ele aparece como
  incompatível/ilegível em `GET /sessions`, sem exception vazando pro HTTP;
- primeiro boot com `.data/` vazio: Experience padrão aplicada, config gravada
  em v2 direto.

## Não fazer

- **Não** escrever conversor de sessão v12→v13 nem de config v1→v2 "só desta
  vez". A regra existe porque cada shim desses vive para sempre.
</content>
