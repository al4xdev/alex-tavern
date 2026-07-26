# 12 — Fábricas de teste (19 arquivos repetem o mesmo cenário)

**Escopo:** `tests/conftest.py`, novo `tests/factories.py`
**Esforço:** M · **Risco:** nenhum (não toca produção) · **Quebra contrato:** nenhuma

## Sintoma

19 arquivos de teste declaram o próprio elenco. Comparando
`tests/test_autonomous_burst.py:19-35` com `tests/test_watcher_integration.py:29-45`:

```python
async def _fake_prose() -> str:
    return "Narracao de teste."

def _char(name: str) -> Character:
    return Character(
        mind=CharacterMind(name=name, personality="p", knowledge=[], current_mood="m"),
        body=CharacterBody(name=name, physical_description="d", outfit="o"),
    )

CHARACTERS = {"C1": _char("Rui"), "C2": _char("Marta")}
SCENE = Scene(location="Estalagem", time_of_day="Noite",
              present_characters=["C1", "C2", "Player"], physical_facts={})
```

Idêntico, caractere por caractere, exceto pela quantidade de personagens. Os 19
arquivos: `test_action_intent`, `test_alignment`, `test_audible_speech_persistence`,
`test_autonomous_burst`, `test_disposition`, `test_disposition_integration`,
`test_drive_scheduler`, `test_force_speaker_regression`, `test_ledger_memory`,
`test_llm_retry_policy`, `test_memory_retention`, `test_omniscient_director`,
`test_opening_suggestions`, `test_perception`, `test_perspective`,
`test_prose_renderer`, `test_roteiro`, `test_watcher`, `test_watcher_integration`.

Além disso, ~10 arquivos definem o próprio duplo de LLM (`class Fake...` ou
`monkeypatch.setattr(..., chat_completion_json, fake)`), cada um com uma forma
diferente de programar respostas por agente.

O `tests/conftest.py` tem 41 linhas e só cuida do isolamento de `.data/` — que
faz muito bem (`assert_safe_test_data_root` é uma boa ideia).

## Por que é dívida agora

O `AGENTS.md` §2 diz para não travar melhoria de core por medo de quebrar
sessão: "basta subir `SESSION_SCHEMA_VERSION`". Só que hoje um campo novo em
`Character` ou `Scene` custa **19 edições de teste** — e é justamente esse
atrito que faz alguém decidir por um campo "puramente aditivo" em vez de subir a
versão (exatamente o que aconteceu em `models.py:33-37`).

Ou seja: a duplicação nos testes está, indiretamente, empurrando o schema para
soluções que o próprio projeto documenta como piores.

## Proposta

`tests/factories.py`:

```python
def make_character(name: str, **overrides) -> Character
def make_scene(*, present: list[str], **overrides) -> Scene
def make_cast(*names: str) -> dict[str, Character]        # {"C1": ..., "C2": ...}
def make_game(*, cast=..., scene=..., controlled="C1", **overrides) -> GameState
```

e uma `FakeDirector` única, que substitui os ~10 duplos ad-hoc:

```python
class FakeDirector:
    """Programa respostas por agente e grava as chamadas recebidas."""
    def beat(self, *, speakers=(), events=(), scene_update=None, return_control=False) -> dict
    def replies(self, **by_character: str) -> None
    calls: list[dict]      # (agent, messages, schema) de cada chamada
```

Os testes existentes migram por substituição direta — o corpo de cada teste não
muda, só o preâmbulo some.

Manter em `factories.py` (importado explicitamente) e **não** como fixtures
autouse do `conftest.py`: os testes deste projeto se apoiam em constantes de
módulo (`SCENE`, `CHARACTERS`) e leem melhor assim do que com injeção implícita.

## Passos

1. Escrever `factories.py` reproduzindo exatamente os valores hoje repetidos
   (`personality="p"`, `physical_description="d"`, `outfit="o"`, "Estalagem",
   "Noite") — assim a migração não muda nenhum assert.
2. Migrar 2 arquivos, conferir que o diff é só remoção, e então os outros 17.
3. Migrar os duplos de LLM para `FakeDirector` (mais cuidadoso: cada um programa
   respostas de um jeito; fazer por arquivo, com o teste verde a cada passo).
4. Só depois: revisar se algum teste que hoje "monta o cenário na mão" na
   verdade precisa de um cenário específico — nesse caso, `**overrides` cobre e
   a intenção fica explícita.

## Como validar

- `uv run pytest` (785 verdes, mesma contagem — nenhum teste deve sumir);
- `git diff --stat` da série: só remoção líquida em `tests/`;
- prova do valor: adicionar um campo obrigatório de mentira em `CharacterMind`,
  rodar os testes e conferir que o conserto é **um** arquivo. Reverter.

## Não fazer

- **Não** mexer em `assert_safe_test_data_root` nem no `TEST_DATA_DIR`: é a
  proteção que impede um teste de escrever no `.data/` real, e está correta.
- **Não** transformar os testes de integração de turno em unitários no mesmo
  movimento. A oportunidade real de simplificá-los aparece depois do doc 05
  (com os estágios extraídos, vários deles testam um método em vez do turno
  inteiro) — e aí sim vale revisitar.
</content>
