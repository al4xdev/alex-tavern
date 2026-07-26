# 03 — Uma função para "chamar um agente"

**Escopo:** `src/llm/client.py` + 11 módulos que chamam modelo
**Esforço:** S/M · **Risco:** baixo · **Quebra contrato:** nenhuma

## Sintoma

18 chamadas a `chat_completion_json` em `src/`, distribuídas em 11 módulos, e
**todas** repetem o mesmo bloco:

```python
result = await chat_completion_json(
    client,
    messages,
    model=config.get("model", ""),
    language=config.get("language", ""),
    max_tokens=<algum max>,
    timeout=resolve_llm_timeout(config),
    json_schema=build_<algo>_schema(),
    session_id=session_id,
    turn_number=turn_number,
    agent="<nome>",
    **llm_request_options(config),
)
```

Sítios: `agents/narrator.py:601,853,915`, `agents/character.py:519`,
`agents/prose.py:332,344`, `agents/summarizer.py:140`,
`agents/perspective.py:209,308,475`, `roteiro.py:482,614`, `watcher.py:176,404`,
`drive.py:126`, `disposition.py:361`, `alignment.py:125`, `plugins/sdk.py:206`.

São ~8 linhas × 18 = **~145 linhas que dizem a mesma coisa**. Quando você
adicionar um campo de transporte (um header novo, um `seed`, um budget de
retries por agente), são 18 edições — e basta esquecer uma para ter um agente
com comportamento diferente sem que teste nenhum perceba.

Que a abstração é desejada já está no código: `agents/prose.py:321` monta um
`request_kwargs: dict[str, Any] = dict(...)` justamente para poder reusar o
bloco entre a chamada normal e o retry. É a abstração certa, feita local e uma
vez só.

## Por que é dívida

O `config: dict` é passado inteiro para cada agente e cada agente decide sozinho
quais chaves ler, com defaults duplicados (`config.get("model", "")` aparece 18
vezes, `config.get("max_tokens_narrator", 2048)` aparece 5). O default de verdade
vive em `src/config.py:DEFAULT_CONFIG` e nos adapters — esses `.get(chave,
default)` são uma **terceira** fonte de verdade para o mesmo valor.

## Proposta

Em `src/llm/client.py`:

```python
async def call_agent(
    client: httpx.AsyncClient,
    config: dict,
    messages: list[dict],
    *,
    agent: str,
    json_schema: dict,
    max_tokens: int,
    session_id: str = "",
    turn_number: int = 0,
    retries: int = 2,
) -> dict:
    """Chamada estruturada de um agente: transporte, log e retry vêm do config."""
```

Ela resolve internamente `model`, `language`, `timeout` e
`**llm_request_options(config)`. Os 18 sítios viram:

```python
result = await call_agent(
    client, config, messages,
    agent="drive:event_seed",
    json_schema=build_event_seed_schema(),
    max_tokens=256,
    session_id=game.session_id, turn_number=turn_number,
)
```

`chat_completion_json` continua existindo como camada de baixo nível (é o que
`call_agent` usa e o que testes de retry exercitam em
`tests/test_llm_retry_policy.py`).

**`max_tokens` fica explícito de propósito**: é a única coisa que varia com
intenção real entre os agentes (2048 no Director, 1024 no Character, 512 no
opening, 256 no drive). Escondê-lo dentro do helper obrigaria a um mapa
agente→budget, que é acoplamento pior do que o argumento.

## Passos

1. Escrever `call_agent` e um teste que prove que ela repassa exatamente os
   mesmos kwargs que a forma manual (comparar com um duplo de
   `chat_completion_json`).
2. Migrar os 18 sítios (mecânico, um módulo por commit).
3. Remover os imports de `llm_request_options`/`resolve_llm_timeout` que ficarem
   órfãos nos agentes — só `client.py` e `config.py` precisam conhecê-los.
4. `plugins/sdk.py:206` (`PluginModel.call_json`) passa a usar `call_agent`
   também: hoje ele reimplementa o mesmo bloco com `agent=f"plugin:{id}"`.

## Como validar

- `uv run pytest` inteiro (todo teste que mocka LLM passa por aqui);
- `grep -c "llm_request_options(config)" src/**/*.py` deve cair de 17 para 1;
- um turno real contra o provider ativo com `debug.jsonl` aberto: os campos
  `provider`, `model`, `agent`, `prompt_estimated_tokens` de cada entrada devem
  ficar idênticos aos de antes (o log é a prova de que o transporte não mudou).

## Não fazer

- **Não** aproveitar para converter `config: dict` numa dataclass tipada nesta
  tarefa. É a melhoria óbvia seguinte (mata os ~60 `config.get(...)` espalhados),
  mas atravessa adapters, SDK de plugins, `runtime-config.js` e ~40 testes: é uma
  supertask própria, não um efeito colateral desta.
- **Não** embutir a construção do schema dentro de `call_agent`: cada agente é
  dono do seu contrato estruturado (`AGENTS.md` §4).
</content>
