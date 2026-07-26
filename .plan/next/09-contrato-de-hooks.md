# 09 — O contrato de hooks precisa ser verificável

**Escopo:** `src/plugins/contracts.py`, `src/runner.py`, `tests/`
**Esforço:** S/M · **Risco:** baixo · **Quebra contrato:** SDK (nomes exportados)

Este é o doc que mais importa para o pedido de "manter compatível com o SDK de
plugins": a compatibilidade hoje é mantida **por atenção humana**, não por
mecanismo.

## Sintoma

`src/plugins/contracts.py:7-157` declara 21 hooks com `kind`, `value`, `context`
e `commit`. É o que `tools/plugin_author.py:167` exporta e o que o hub e o MCP
consomem para gerar scaffold e validar plugins.

Do outro lado, `src/runner.py` chama os hooks por **string literal**, em 21
sítios (`runner.py:175, 265, 270, 449, 675, 678, 717, 723, 924, 937, 1039, 1044,
1074, 1182, 1190, 1226, 1392, 1470, 1538, 1595`).

E não existe nada ligando os dois:

```
$ grep -rn "HOOK_CONTRACTS" --include=*.py . | grep -v src/plugins/contracts.py
(vazio)
```

Nenhum teste, nenhuma checagem. Se alguém renomear `narrator.result` no runner e
esquecer o `contracts.py`, o hub continua gerando plugins que registram um hook
que nunca dispara — silenciosamente, sem erro em lugar nenhum. O `kind` também
pode divergir: `contracts.py` diz que `session.start` é `"sync filter"`, e é o
`runner.py:175` (`filter_sync`) quem decide isso de verdade.

O doc 01 já vai forçar essa atualização (`session.*` deixa de ser sync). Fazer os
dois juntos é natural.

## Proposta

**1. Nomes como constantes.** Em `contracts.py`, ao lado do dicionário:

```python
class Hook:
    SESSION_START = "session.start"
    NARRATOR_CALL = "narrator.call"
    ...
```

e `runner.py` passa a usar `Hook.NARRATOR_CALL`. Um typo vira `AttributeError`
no import, não um hook morto em produção. Plugins continuam registrando por
string (o SDK não muda) — a constante protege o **core**, que é quem dispara.

**2. Um teste de coerência.** `tests/test_plugin_contract.py`:

- varre `src/**/*.py` com AST atrás de toda chamada `hooks.<verbo>("nome")`;
- afirma que todo nome encontrado existe em `HOOK_CONTRACTS`;
- afirma o contrário: todo nome de `HOOK_CONTRACTS` é disparado em algum lugar
  (pega hook documentado que ninguém chama);
- afirma que o verbo bate com o `kind` declarado (`filter*` → `"filter"`,
  `action*` → `"action"`, `call_wrapped` → `"wrapper"`).

São ~40 linhas de teste que transformam o documento numa garantia. É o mesmo
espírito de `tests/test_frontend_architecture.py`, que já faz asserção
estrutural sobre o frontend — o precedente existe no repo.

**3. `exported_contract()` ganha `core_version`.** Hoje o hub consome o contrato
sem saber de qual build ele veio. Um campo com o `SESSION_SCHEMA_VERSION` e a
versão do contrato de hooks deixa o hub recusar um scaffold gerado contra um core
diferente — e é o que permite quebrar o SDK sem medo depois.

## Enquanto estiver ali: o `PluginContext.command`

```python
# src/plugins/sdk.py:291
self.unsafe.runtime.commands.register(...)
```

O registro de comando — que é uma feature de primeira classe, documentada em
`contracts.COMMANDS` — passa pelo `UnsafeAccess`, o escape hatch que existe para
plugins que precisam mexer em objeto arbitrário. Efeito prático: todo plugin que
registra um comando emite um evento `permission_access` com
`permission="unsafe"` no journal, poluindo a auditoria e fazendo um comando
inofensivo parecer perigoso na revisão.

`PluginContext` deveria receber a `CommandRegistry` no `__init__` (o
`PluginRuntime` já a tem em `runtime.py:60`) e chamar direto. O `unsafe` volta a
significar só o que promete.

## Passos

1. Constantes `Hook` + substituição nos 21 sítios do runner.
2. Teste de coerência (rodar antes de mudar qualquer nome — ele deve passar no
   estado atual; se não passar, achou drift real).
3. Atualizar `kind` de `session.*` junto do doc 01.
4. `PluginContext.command` sem `unsafe`.
5. `core_version` no `exported_contract()`.

## Como validar

- `uv run pytest tests/test_plugins.py tests/test_plugin_hub.py
  tests/test_commands_presets.py` + o teste novo;
- `uv run python -m tools.plugin_author contract` (ou o comando equivalente do
  arquivo) e conferir o JSON exportado;
- instalar um plugin curado com comando e conferir em `GET /plugins/events` que
  **não** aparece mais `permission: "unsafe"` no registro.

## Não fazer

- **Não** transformar `HOOK_CONTRACTS` em algo derivado automaticamente do
  código. As descrições e o campo `commit` são conhecimento humano que o AST não
  tem; o teste checa a *interseção*, não gera o documento.
- **Não** versionar hooks individualmente ("narrator.call v2"). Projeto novo,
  regra forward-only: quando o contrato muda, o hub muda junto.
</content>
