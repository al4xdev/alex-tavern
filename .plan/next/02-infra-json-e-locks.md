# 02 — Infra compartilhada: escrita atômica de JSON e registry de locks

**Escopo:** novo `src/store/jsonfile.py` (ou `src/atomic.py`), 6 módulos consumidores
**Esforço:** S · **Risco:** baixo · **Quebra contrato:** nenhuma

## Sintoma A — seis escritas atômicas

```
src/config.py:219          def _atomic_write_json(path, value)
src/store/sessions.py:61   def _atomic_write_json(path, data)
src/store/presets.py:63    def _atomic_write(path, value)
src/store/scenarios.py:44  (inline dentro de save_scenario)
src/plugins/sdk.py:115     def _atomic_json(path, value)
src/plugins/hub.py:187     def _atomic_bytes(value, destination)
```

Cinco delas são o mesmo corpo: `mkdir(parents=True)` → `mkstemp` no diretório
alvo → `json.dump(indent=2, ensure_ascii=False)` → `flush` → `fsync` →
`replace` → `unlink` no `except BaseException`. As diferenças entre elas são
**acidentais, não intencionais**:

- `sessions.py` **não** escreve `\n` final; `config.py`, `presets.py` e `sdk.py`
  escrevem;
- `scenarios.py` usa `prefix=f"{name}_"` em vez de `prefix=f".{path.name}."`, ou
  seja, seu temporário **não é oculto** e aparece em `list_scenarios()` se o
  processo morrer no meio (`list_scenarios` filtra por `.json`, então o `.tmp`
  escapa — mas o arquivo fica lá para sempre);
- `scenarios.py` faz `os.fsync(fd)` com o fd cru enquanto os outros usam
  `handle.fileno()` (equivalente, mas é uma terceira grafia da mesma linha);
- só `sessions.py` usa `suffix=".tmp"`;
- `scenarios.py` e `config.py` fazem `if temporary.exists(): unlink()` enquanto
  os outros usam `unlink(missing_ok=True)`.

Nenhuma dessas diferenças é uma decisão — é deriva de cópia.

E o acoplamento que isso já produziu: `src/plugins/store.py:25` faz
`from src.plugins.sdk import _atomic_json`, **importando um símbolo privado de
outro módulo** só para não escrever a sexta cópia.

## Sintoma B — quatro registries de lock

```
src/store/sessions.py:31   _get_lock(session_id) -> asyncio.Lock
src/store/presets.py:50    _get_lock(name)       -> threading.RLock
src/store/scenarios.py:19  _get_lock(name)       -> threading.RLock
src/llm/debug_log.py:18    _get_lock(session_id) -> threading.Lock
```

Corpo idêntico nos quatro: `WeakValueDictionary` + `threading.Lock` guard +
get-or-create. Três nomes de módulo diferentes para a mesma função privada.

Pior: `src/runner.py:104` faz `from src.store.sessions import _get_lock` — de
novo, **símbolo privado atravessando módulo**, e desta vez no arquivo mais
importante do projeto. O lock de sessão é a peça central da concorrência
(`AGENTS.md` §4 documenta isso como invariante) e mesmo assim se chama `_get_lock`.

## Proposta

**A.** Um módulo `src/store/jsonfile.py`:

```python
def write_json(path: Path, value: Any) -> None:
    """Escrita atômica: temp oculto no mesmo dir, fsync, rename."""

def read_json(path: Path) -> Any | None:   # None quando ausente
```

Padroniza: temporário oculto (`.{name}.`), `indent=2`, `ensure_ascii=False`,
newline final, `fsync`, `unlink(missing_ok=True)` na falha. Os 5 sítios JSON
passam a chamá-lo; `hub._atomic_bytes` fica separado (é bytes, não JSON) mas
ganha o mesmo nome de prefixo.

**B.** Um `src/store/locks.py`:

```python
def session_lock(session_id: str) -> asyncio.Lock      # async, mutação de sessão
def named_lock(namespace: str, name: str) -> threading.RLock  # presets, scenarios
def append_lock(session_id: str) -> threading.Lock     # debug_log
```

sobre **um** helper genérico de registry fraco. `session_lock` é público e
nomeado — `runner.py` para de importar `_get_lock`.

## Passos

1. Criar `jsonfile.py` com testes próprios (temp oculto, sobrevive a exceção,
   conteúdo idêntico ao anterior).
2. Migrar `config.py`, `store/sessions.py`, `store/presets.py`,
   `store/scenarios.py`, `plugins/sdk.py`; apagar as 5 privadas.
3. Apagar o import privado em `plugins/store.py:25`.
4. Criar `locks.py`, migrar os 4 registries, renomear `_get_lock` → `session_lock`
   nos ~10 usos de `runner.py` e nos testes que importam.
5. Verificar que `save_game` continua com `fsync` — é o único save crítico
   citado no `AGENTS.md` §4.

## Como validar

- `uv run pytest tests/test_data_isolation.py tests/test_provider_config.py
  tests/test_plugin_storage.py tests/test_compaction.py`;
- teste novo: matar a escrita no meio (patch de `json.dump` levantando) e
  conferir que o arquivo original permanece íntegro e nenhum temporário sobra;
- `ls .data/scenarios/` depois de salvar um cenário: nenhum `*_*.tmp`.

## Não fazer

- **Não** transformar isso numa "camada de repositório" com classes por entidade.
  O ganho é só remover a cópia; o formato de cada arquivo continua sendo assunto
  do módulo dono.
- **Não** unificar `session_lock` (asyncio) com os locks de thread numa
  abstração única: são semânticas diferentes e a fusão só esconderia isso.
</content>
