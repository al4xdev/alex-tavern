---
name: android-apk-lab
description: Monta o ambiente Android reproduzível do Alex Tavern, compila o APK Chaquopy/FastAPI em Docker e valida instalação, boot, HTTP, plugins, WebView e reinício de processo em aparelho físico via ADB. Use ao criar ou depurar builds Android, instalar um APK local, investigar erros que só aparecem no celular, testar ativação/instalação de plugins ou preparar evidência antes de um commit Android.
---

# Android APK lab

Trabalhar sempre a partir da raiz do checkout. Consultar `.plan/tasks/` e
`AGENTS.md` antes de editar. Não fazer push. Não desinstalar o app sem autorização:
`adb install -r` preserva os dados; `adb uninstall` apaga todo o diretório privado.

Os dois scripts do fluxo vivem junto desta skill, não em `scripts/` na raiz:

```fish
set lab .claude/skills/android-apk-lab/scripts
```

Eles descobrem a raiz do repositório sozinhos, então podem ser chamados de
qualquer diretório.

## Fluxo obrigatório

1. Confirmar alterações locais e o aparelho:

   ```fish
   git status -sb
   adb devices -l
   ```

2. Rodar regressões proporcionais antes do build:

   ```fish
   uv run pytest -q tests/test_android_packaging.py tests/test_frontend_architecture.py tests/test_plugins.py tests/test_plugin_hub.py
   uvx ruff check .
   uvx ruff format --check .
   uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py tools/replay_llm.py tools/replay_session.py
   ```

3. Executar `$lab/build-debug-apk.sh`. O primeiro uso baixa um SDK isolado
   para `.ci-cd/android/.local/` (ignorado pelo Git); os usos seguintes
   reutilizam SDK, Gradle e a mesma `debug.keystore`. A chave estável é
   essencial para instalar com `-r`.

4. Executar `$lab/adb-smoke.sh`. O script instala por cima, inicia o app,
   cria um forward local para a porta 8889 do aparelho, verifica `/health` e
   `/version`, coleta PID, pacote, janela ativa, log de boot e screenshot.
   Aceita o caminho de um APK como primeiro argumento; sem argumento usa o
   build de debug recém-gerado.

5. Exercitar manualmente o boundary alterado. Teste estático não substitui:

   - instalação de plugin: tocar em `Choose file` e confirmar que o seletor de
     documentos Android abre;
   - ativação/desativação: fechar a loja, registrar o PID anterior e confirmar
     que o PID muda após o relançamento;
   - fullscreen: capturar screenshot desbloqueado e confirmar ausência das
     faixas de status e navegação;
   - persistência: consultar `/plugins` depois do novo processo subir.

6. Rodar `uv run pytest -x`, registrar o SHA-256 do APK e só então commitar
   localmente se houver autorização explícita.

## Diagnóstico via ADB

Usar estes comandos em fish:

```fish
# Backend Android acessível no host
adb forward tcp:18889 tcp:8889
curl -fsS http://127.0.0.1:18889/health | jq .
curl -fsS http://127.0.0.1:18889/version | jq .
curl -fsS http://127.0.0.1:18889/plugins | jq .

# Evidência de boot e processo
adb shell pidof com.al4xdev.alextavern
adb logcat -d -s TavernBootstrap
adb shell run-as com.al4xdev.alextavern tail -80 files/bootstrap.log
adb shell dumpsys window | rg 'mCurrentFocus|alextavern'

# Evidência visual e hierarquia nativa
adb exec-out screencap -p > /tmp/alex-tavern-screen.png
adb shell uiautomator dump /sdcard/alex-tavern-ui.xml
adb pull /sdcard/alex-tavern-ui.xml /tmp/alex-tavern-ui.xml
```

O `uiautomator` enxerga bem o seletor de documentos, mas pode representar o
conteúdo do WebView como um único nó. Nesse caso, usar screenshot, logcat e a
resposta HTTP como evidência complementar.

Se o aparelho estiver bloqueado, `NotificationShade` será a janela ativa e uma
screenshot pode sair preta. Acordar a tela e pedir ao dono para desbloquear; não
tentar contornar PIN ou biometria.

## Falhas conhecidas e decisão

- `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: a keystore usada mudou. Não desinstalar.
  Recuperar a chave de `.ci-cd/android/.local/android-home/debug.keystore` ou a
  chave que assinou o APK instalado.
- `Permission denied` ao copiar plugins no armazenamento privado não implica
  permissão Android ausente. Metadados de ZIP/Git podem carregar modos somente
  leitura; copiar conteúdo para uma árvore nova e deixar o processo criar os
  destinos.
- servidor saudável com HTTP 500: separar boot de Uvicorn da falha do endpoint;
  ler `bootstrap.log`, resposta HTTP e traceback Python.
- ativação persistida sem efeito: WebView recarregada não reinicia Chaquopy.
  Confirmar que o bridge chama o `RestartActivity` no processo `:restart` e que
  o PID principal foi substituído.
- `adb` sem acesso ao daemon/socket: executar fora do sandbox ou solicitar a
  autorização ADB apropriada; não iniciar loops de polling.

## Contratos que o APK deve preservar

- backend e frontend vêm do source canônico; não criar cópia Android do runtime;
- `ROLEPLAY_DATA_DIR` deve ser definido antes de importar `src.main`;
- dados ficam em `files/data`, não em armazenamento externo;
- bridge JavaScript aceita reinício somente para o frontend local confiável;
- `RestartActivity` continua não exportada e em processo separado;
- dependências Chaquopy permanecem pure Python (`pydantic<2`, Uvicorn sem extras);
- o build informa o commit em `src/version.txt`, que permanece ignorado pelo Git.
