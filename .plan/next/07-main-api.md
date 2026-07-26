# 07 — `src/main.py`: contrato de erro, imports e duplicações

**Escopo:** `src/main.py` (1.219 linhas, 46 rotas)
**Esforço:** M · **Risco:** baixo · **Quebra contrato:** HTTP interno (frontend acompanha)

## A — 35 imports dentro de funções

```
$ grep -c "^\s\+from src\." src/main.py
35
```

Quase toda rota abre com `from src.store.presets import ...`,
`from src.plugins.store import ...`, `from src.models import ...`. Confirmado
que **não há ciclo de import**: nenhum módulo de `src/` importa `src.main`
(`grep -rn "import src.main" src tools` → vazio). E o import é caro só na
primeira vez — como o `lifespan` já constrói `PluginRuntime`, `Runner` e resolve
config no boot, a maioria desses módulos já está carregada antes da primeira
requisição.

Não achei justificativa documentada em `AGENTS.md`, `.plan/` ou nos comentários.
Na prática o custo é: nenhuma ferramenta consegue ver o grafo de dependências do
módulo, e o mesmo `from src.plugins.store import PluginInstallError` aparece
**6 vezes** no arquivo.

**Proposta:** subir todos para o topo. Se algum realmente pesar no cold start do
APK (medível: `time python -c "import src.main"` com e sem), manter só esse,
**com comentário dizendo o número medido**.

## B — dois contratos de erro convivendo

Metade do Runner sinaliza falha por exceção (`PresenceRevisionConflictError`,
`IncompatibleSessionError`, `CommandError`, `PresetError`) e a outra metade
devolve `{"error": ...}` no dict de retorno. Resultado: 7 rotas repetem

```python
result = await ...
if "error" in result:
    raise HTTPException(status_code=404, detail=result["error"])
```

(`main.py:496, 508, 534, 599, 624, 640, 649`) e uma delas precisa espiar um
código dentro do dict para escolher o status (`main.py:508`:
`409 if result.get("code") == "conversation_started" else 404`).

Pior, o mesmo dict de erro precisa continuar existindo *dentro* do
`PlayerTurnResponse` (`main.py:307: error: str | None`), então o campo `error` é
simultaneamente sinal de controle e campo de payload.

**Proposta:** uma exceção `SessionNotFoundError(session_id)` em
`src/store/sessions.py` (junto de `IncompatibleSessionError`, que já usa esse
padrão com handler global em `main.py:88`) e um handler
`@app.exception_handler(SessionNotFoundError)` devolvendo 404. Os
`return {"error": f"Session {id} not found"}` do runner (9 ocorrências) viram
`raise`. As 7 rotas perdem o `if "error" in result`.

Para o caso `conversation_started`, uma `OpeningUnavailableError` com `code` e
status próprios — mesmo padrão, sem inspecionar dict.

## C — duas rotas de upload idênticas

`main.py:951-968` (`/plugins/install-upload`) e `main.py:972-990`
(`/plugins/inspect-upload`) são o mesmo corpo: `TemporaryDirectory` → stream em
chunks → limite de 100 MiB → rejeitar vazio → chamar `install_zip`/`inspect_zip`
→ mapear `PluginInstallError` em 422. Diferem em **uma linha**.

**Proposta:**

```python
async def _receive_plugin_zip(request: Request, handler: Callable[[Path], dict]) -> dict:
```

com o limite `MAX_PLUGIN_ZIP_BYTES = 100 * 1024 * 1024` como constante nomeada
(hoje é o literal `100 * 1024 * 1024` escrito duas vezes).

## D — `body.dict(exclude_none=True)` (verificado)

```python
# src/main.py:845
save_scenario(name, body.dict(exclude_none=True))
```

Único ponto de `src/` que chama a API do pydantic direto em vez de passar pelo
`src/pydantic_compat.dump()`. Reproduzido:

```
$ uv run python -W error::DeprecationWarning -c "... PUT /scenarios/zz ..."
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
```

Funciona hoje nas duas versões, some no pydantic v3. **Proposta:** estender
`pydantic_compat.dump(model, *, exclude_none=False)` e usar aqui — o shim volta
a ser o único ponto do projeto que conhece a diferença de versão, como o seu
próprio docstring promete (`pydantic_compat.py:9-11`).

## E — `StartSessionRequest` reusado como corpo de cenário

`PUT /scenarios/{name}` (`main.py:841`) tipa o corpo como `StartSessionRequest`.
Funciona porque um cenário salvo é "o que você mandaria para criar sessão", mas
o nome mente e os dois contratos vão divergir na primeira feature de cenário
(tags, autor, capa). Um `ScenarioBody` explícito, mesmo que hoje tenha os mesmos
campos, deixa a divergência futura barata.

## F — miudezas do mesmo arquivo

- `main.py:440`: `assert game is not None, "Newly-created session should exist"`
  logo depois de criar a sessão — com `python -O` a asserção some e o `None`
  segue para `game_state_to_dict`. Trocar por `raise RuntimeError(...)`.
- `_compaction_event_stream` (`main.py:538-591`, 54 linhas de SSE) não é rota:
  é infraestrutura de streaming no meio das rotas. Cabe em `src/http/sse.py`
  (ou no fim do arquivo, abaixo de um separador claro).
- `MAX_READ_LIMIT = 1000` está bom; já os `100 * 1024 * 1024` e o `15` do
  keepalive SSE (`main.py:554`) merecem nome.

## Passos

1. (D) e (F) — minutos.
2. (C) — dedup do upload.
3. (A) — imports para o topo, com uma medição do import time antes/depois.
4. (B) — o contrato de erro, que é o de maior valor e o único que toca o
   frontend (`api.js` já lê `detail`/`error`/`reason`, então o payload não muda;
   confira `src/static/api.js:56`).
5. (E) — quando mexer em cenários.

## Como validar

- `uv run pytest tests/test_integration.py tests/test_api_limits.py
  tests/test_security.py tests/test_plugins.py`;
- `curl` em cada rota tocada conferindo status e corpo (o método curl-first do
  `AGENTS.md` §6 vale aqui também: a variante validada é a que entra);
- frontend: abrir uma sessão inexistente pela URL e conferir o toast de erro.

## Não fazer

- **Não** dividir `main.py` em routers por domínio nesta tarefa. 46 rotas num
  arquivo é grande mas navegável, e a divisão só faz sentido depois de (B) — com
  o contrato de erro único, cortar por domínio vira mecânico. Fica como sucessora
  natural, não como pré-requisito.
</content>
