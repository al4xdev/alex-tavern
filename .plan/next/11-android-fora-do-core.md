# 11 — O que é do APK sai de `src/`

**Escopo:** `src/main.py`, `src/static/app.js`, `.ci-cd/android/`
**Esforço:** M · **Risco:** baixo · **Quebra contrato:** remove `GET /bootstrap_log`

Levantamento do que existe em `src/` **por causa do Android**, com o veredito de
cada item. Nem tudo pode sair — parte é restrição real da plataforma — mas parte
é diagnóstico de build morando no servidor de produto.

## Sai: `GET /bootstrap_log`

```python
# src/main.py:1200-1208
@app.get("/bootstrap_log")
def get_bootstrap_log() -> HTMLResponse:
    """Returns the Android bootstrap log for diagnostics."""
    log_path = DATA_DIR.parent / "bootstrap.log"
```

Nove linhas de rota + um `import html` no topo, servindo um arquivo que **só
existe no Android** (escrito por `android_runner.log()` e por
`MainActivity.logBootstrap()`). Nenhum cliente consome:

```
$ grep -rn "bootstrap_log" --include=*.py --include=*.js --include=*.kt .
src/main.py:1200          (a definição)
android_runner.py:8       (uma menção no docstring)
```

E o mesmo conteúdo já é lido nativamente: `MainActivity.kt:59` abre
`File(filesDir, "bootstrap.log")` e renderiza na tela de status.

**Proposta:** apagar a rota (e o `import html`, que fica órfão). Quem precisar do
log em campo tem a tela nativa e `adb shell run-as ... cat files/bootstrap.log`,
já documentado na skill `android-apk-lab`. Se um dia fizer falta via HTTP, é um
plugin — o slot `routes` de `contracts.CONTRIBUTION_SLOTS` existe exatamente
para isso, e um plugin ativado só no build de debug é o lugar certo.

## Sai: os 49 linhas de parsing de `.git` dentro de `main.py`

`get_git_commit()` (`main.py:1137-1184`) abre `.git/HEAD`, resolve `ref:`,
consulta `packed-refs` e tem fallback para `src/version.txt` (o arquivo que o CI
carimba em `.ci-cd/android/action.yml:26`). É a função mais longa do módulo de
rotas e não tem nada a ver com HTTP.

**Proposta:** `src/build_info.py` com `build_commit() -> str`, e `/version` vira
duas linhas. Ganhos: testável sozinho (hoje `tests/test_android_packaging.py`
precisa do app inteiro), e o comentário sobre "APK construído de commits
descartados" fica junto do código que resolve o problema.

Enquanto isso, uma verificação: `src/version.txt` está corretamente no
`.gitignore:24` e **não** é rastreado — a cópia local (`44ccc54`) é resto de um
build antigo e é inofensiva porque o fallback só é lido quando `.git` não existe.
Vale apagar a local para não confundir ninguém.

## Sai: a ponte `window.AlexTavernAndroid` do `app.js`

```js
// app.js:2347-2352
const bridge = window.AlexTavernAndroid;
if (!bridge || typeof bridge.restartApplication !== 'function') return false;
```

Enterrado dentro de `initializeApplication`, no meio da config do `PluginCenter`.
**Proposta:** um `src/static/android-bridge.js` de ~15 linhas exportando
`restartApplication()` e `isNativeShell()`. Fica óbvio o que o WebView precisa
expor, e o contrato entre Kotlin e JS passa a ter um arquivo com nome.

## Fica (e por quê)

- **`src/pydantic_compat.py`** — Chaquopy não compila `pydantic-core` (Rust, sem
  wheel Android); `.ci-cd/android/app/build.gradle:58-63` fixa `pydantic<2`.
  Enquanto o backend for FastAPI, o shim é obrigatório. O doc 08 corta metade
  dele (o `_ValuesProxy`), que é o máximo honesto aqui.
- **`STATIC_DIR` resolvido do módulo** (`paths.py:14-19`) e o mount condicional
  (`main.py:1217`) — sem isso o servidor morre no boot do APK. O comentário já
  explica; mantenha.
- **`copy_tree_contents`** (`plugins/filesystem.py`) — existe por `EACCES` de
  xattr SELinux no Android, mas é um helper genérico e correto para qualquer
  host. Fica.
- **`BASE_URL` de `file://`** (`api.js:6`) e os caminhos relativos do
  `index.html` — necessários para o WebView offline. Só limpar a atribuição
  "Antigravity AI" do comentário (doc 10).
- **`store.py:562-573`**, o `FileNotFoundError` do `uv` — a mensagem clara
  ("uv is required...") vale para qualquer host sem gerenciador de pacotes, não
  só Android. Fica; talvez sem citar Android no comentário.

## Do lado do `.ci-cd/android/`, enquanto estiver ali

- `MainActivity.kt` e `build.gradle` misturam comentários em português
  (`build.gradle:83`, `MainActivity.kt:232`) com o resto do repositório em
  inglês. Uniformizar (o padrão do repo é código e comentário em inglês, docs de
  `.plan/` em português).
- `MainActivity.kt:74`: `showStatus("Iniciando Alex Tavern…")` é a única string
  de UI hardcoded fora do i18n do projeto; ela aparece antes do WebView existir,
  então não dá para usar `i18n.js` — mas dá para pôr em `res/values/strings.xml`
  (e `values-pt/`), que é o mecanismo nativo e já está no projeto.
- A sincronização dos assets (`action.yml:29-32`, `cp -r src/static/*`) mantém
  **duas** cópias do frontend no APK: uma nos assets e outra dentro do pacote
  Python extraído. `android_runner.py:76-81` já loga qual das duas venceu. Não
  proponho mudar — o fallback salva builds em que o Chaquopy não extrai os
  não-`.py` —, mas vale registrar a duplicação como conhecida, com o log como
  prova de qual caminho está ativo.

## Passos

1. Apagar `/bootstrap_log` + `import html`.
2. Extrair `src/build_info.py`; ajustar `tests/test_android_packaging.py`.
3. Criar `android-bridge.js` (junto do doc 10).
4. Uniformizar idioma dos comentários no projeto Android + `strings.xml`.
5. Apagar `src/version.txt` local.

## Como validar

- `uv run pytest tests/test_android_packaging.py tests/test_integration.py`;
- `GET /version` continua devolvendo o commit certo no desktop (com `.git`) e no
  APK (com `version.txt`);
- **build real e aparelho**: `.claude/skills/android-apk-lab` — instalar, botar,
  conferir HTTP, plugins, WebView e restart de processo. Este doc mexe justamente
  no que só falha no celular; validar só no desktop não vale.

## Não fazer

- **Não** tentar remover o shim do pydantic "migrando o backend para
  dataclasses". FastAPI depende de pydantic; a troca seria reescrever a camada
  HTTP inteira para economizar 35 linhas.
- **Não** mover `src/paths.py` nem `plugins/filesystem.py` para o projeto
  Android: eles rodam em todos os deployments; só o *motivo* de uma linha é
  Android.
</content>
