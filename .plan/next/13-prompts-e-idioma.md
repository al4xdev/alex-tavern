# 13 — Contexto de prompt duplicado e idioma misturado

> ✅ **Aplicado em `92ca271`** (branch `refactor/pre-1.0-cleanup`, 2026-07-26) — aplicado integralmente

**Escopo:** `src/drive.py`, `src/watcher.py`, `src/roteiro.py`, `src/llm/client.py`,
`src/agents/narrator.py`
**Esforço:** S · **Risco:** baixo (mexe em prompt: exige método curl-first) · **Quebra contrato:** nenhuma

## A — o mesmo bloco de contexto escrito três vezes

`src/drive.py:60-75` e `src/watcher.py:326-343` são **byte a byte iguais**:

```python
recent = [r for r in game.history[-12:]
          if r.content_type in ("speech", "action", "narration")]
lines = [
    f"LOCATION: {game.scene.location} | TIME: {game.scene.time_of_day}",
    f"PHYSICAL FACTS: {game.scene.physical_facts}",
    "RECENT EVENTS (oldest to newest):",
    *(f"  {speaker_label(r.speaker, game.characters, game.player.controlled_character_id)}:"
      f" {r.content[:160]}" for r in recent),
]
if game.story_summary:
    lines.insert(0, f"STORY SO FAR: {game.story_summary[:600]}")
```

`src/roteiro.py:363-385` (`_story_context_lines`) é uma terceira variante da
mesma ideia. Ela filtra pela constante `_PROGRESS_RECORD_TYPES`
(`roteiro.py:48`) — que é *exatamente* a tupla `("speech", "action",
"narration")` que os outros dois escrevem inline —, mas resolve o nome do
falante à mão (`speaker = controlled if rec.speaker == "Player" else rec.speaker`) em vez
de chamar `speaker_label` — reimplementando a trava de agência mais importante
do projeto (`AGENTS.md` §3: `"Player"` nunca chega a um prompt).

Funciona hoje. Mas é **a regra de agência escrita em dois lugares**, e o segundo
não é o canônico. Se `speaker_label` ganhar um caso (um personagem controlado
renomeado, um apelido por perspectiva), `roteiro.py` fica para trás sem que
nenhum teste acuse.

**Proposta:** `src/prompting.py` (ou `src/agents/context.py`) com:

```python
def scene_header(game: GameState) -> list[str]
def recent_events(game: GameState, *, limit: int = 12, max_chars: int = 160) -> list[str]
def story_so_far(game: GameState, *, max_chars: int = 600) -> list[str]
```

Os três chamadores compõem o que precisam. `roteiro.py` passa a usar
`speaker_label` por construção. Os prompts gerados devem sair **idênticos** —
essa é a condição de aceite.

Os formatadores de história dos agentes (`narrator._build_user_prompt`,
`character._format_history_for_character`, `prose.build_prose_messages`,
`perspective`, `summarizer`) **não** entram nessa unificação: cada um filtra por
uma fronteira de visibilidade diferente, que é o coração do produto. Juntá-los
seria o erro oposto.

## B — mensagens de erro em português dentro de um core em inglês

```python
# src/llm/client.py:290
raise ValueError(f"Falha ao obter JSON válido após {attempts_made} tentativas. Último erro: {last_error}")

# src/agents/narrator.py:626
raise ValueError(f"Resposta do Narrador sem campos obrigatórios: {missing}. Recebido: ...")
```

Todo o resto de `src/` levanta em inglês (`"A turn needs speech, thought..."`,
`"Session {id} not found"`, `"present_characters cannot be empty."`). Essas duas
são exceções, e a primeira é justamente a que mais aparece em log de produção e
em `tools/replay_llm.py`.

Não é cosmético: essas strings chegam ao usuário via
`toast(t('turn.failed', {error: err.message}))` (`app.js:1741`) — ou seja, uma
mensagem que **já** está em português dentro de uma moldura traduzida, que fica
em inglês quando o locale é inglês. Ou o erro técnico é sempre inglês (a
recomendação: é diagnóstico, não texto de produto), ou vira chave de i18n. Hoje
é meio a meio por acidente.

Vale um teste de arquitetura simples, no espírito dos que já existem:
"nenhuma string levantada em `src/` contém caractere acentuado".

## C — `chat_completion` monta payload que é imediatamente sobrescrito

```python
# src/llm/client.py:100-122
payload = {"model": ..., "messages": messages, "max_tokens": ..., "stream": False}
if response_format is not None:
    payload["response_format"] = response_format
adapter = get_provider_adapter(provider)
prepared = adapter.prepare_request(...)
messages = prepared.messages
response_format = prepared.response_format
payload["messages"] = messages          # sobrescreve
if response_format is None:
    payload.pop("response_format", None) # desfaz
else:
    payload["response_format"] = response_format
```

Duas das cinco chaves (`messages` e `response_format`) são definidas duas vezes,
e a segunda ainda precisa de um `pop` para desfazer a primeira. Montar o
`payload` **depois** de
`prepare_request` remove 8 linhas e a única leitura possível fica sendo a
correta. Zero mudança de comportamento (dá para provar comparando o dict final
num teste).

## D — `content` tipado como `str`, atribuído `str | None`

`chat_completion` declara `-> str` e mantém `content: str | None = None`
(`client.py:127`), retornando-o em `client.py:192`. Na prática
`extract_openai_response` garante `str` (`adapters/base.py:143` levanta se não
for), então o `None` só existe para o caminho de log do `except`. Separar as duas
variáveis (`logged_content: str | None` e `content: str`) deixa o tipo honesto —
`warn_return_any` do mypy não pega isso porque o `raise` intermediário mascara.

## Passos

1. (C) e (D): mecânicos, sem risco.
2. (B): decidir a política (recomendo inglês para erro técnico) e aplicar +
   teste de arquitetura.
3. (A): extrair `prompting.py` e migrar drive → watcher → roteiro.

## Como validar

- **(A) exige prova de prompt idêntico**: capturar `request.messages` de uma
  chamada de `drive:event_seed`, `watcher:*` e `roteiro:*` em `debug.jsonl`
  antes e depois e comparar byte a byte. Se mudou, o refactor mudou o produto —
  e aí vale o método curl-first do `AGENTS.md` §6 antes de aceitar;
- `uv run pytest tests/test_drive_scheduler.py tests/test_watcher.py
  tests/test_roteiro.py tests/test_llm_retry_policy.py`;
- (B): `uv run pytest tests/test_frontend_i18n.py` + o teste novo.

## Não fazer

- **Não** mover os prompts grandes (`narrator._build_system_prompt`, 170 linhas)
  para arquivos `.txt` ou `.md`. Eles carregam comentários explicando *qual
  replay validou cada posição do texto* (`narrator.py:125-127`, `:186-187`) —
  separar o texto do comentário destrói a rastreabilidade que o `AGENTS.md` §6
  exige. No máximo, promover a constantes de módulo no mesmo arquivo.
- **Não** unificar os formatadores de história por papel (ver A).
</content>
