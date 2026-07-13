# Relatório final de remediação do `report.md`

**Data:** 2026-07-12

**Fonte exclusiva:** [`report.md`](./report.md)

**Resultado:** os seis bugs objetivos foram corrigidos e verificados; os problemas qualitativos
foram mitigados, mas continuam dependentes do modelo.

## Resultado por achado

| ID | Achado original | Estado | Evidência |
|---|---|---|---|
| B1 | `location` gravada em `physical_facts` | **RESOLVIDO** | `Runner._update_scene` trata `location` e `time_of_day` como campos reservados, limpa fatos da localização anterior e preserva undo. Testes cobrem troca, permanência, remoção e restauração. No playtest final, abrir a porta mudou o local para `Outside Old Mork's Tavern, alleyway`. |
| B2 | notas de compactação com IDs inutilizáveis | **RESOLVIDO** | O schema aceita apenas IDs da sessão, a resposta é filtrada por IDs canônicos e o prompt separa ID/nome. O playtest produziu notas `C1` e `C2`; a nota de Lyra apareceu no prompt do turno pós-compactação. |
| B3 | erros LLM registrados como string vazia | **RESOLVIDO** | O JSONL agora registra `str(e) or repr(e)`, `error_type`, `error_repr`, duração, tentativa e tamanho do prompt. Erros de JSON estruturado também são registrados e excluídos da fita. O timeout é configurável, com padrão de 60 s. |
| B4 | `force_speaker` podia reutilizar contexto de outro personagem | **RESOLVIDO** | O override é validado antes do Narrador e restringe schema/prompt ao ID efetivo; `Narrator` força contexto vazio. Testes e playtest cobriram `C2`, `Narrator`, inválido e automático. |
| B5 | log sem payload/override, impedindo replay exato | **RESOLVIDO (formato atual)** | Cada turno grava `turn_input` antes da primeira chamada, com fala, pensamento (thought), ação, override solicitado e efetivo. O replay exige esses marcadores e não tenta inferir logs antigos. Essa decisão segue a orientação de não criar uma camada de compatibilidade legada. |
| B6 | testes alteravam `.data` real | **RESOLVIDO** | `tests/conftest.py` define um `ROLEPLAY_DATA_DIR` temporário antes dos imports e recusa o diretório real ou descendentes. O hash e a contagem de `.data` permaneceram idênticos durante a validação final. |

## Mitigações qualitativas

- O Narrador recebeu regras para resolver primeiro a consequência imediata, evitar leitura de
  mente, preservar incerteza, estabilizar humores e reutilizar chaves físicas.
- Character limita fontes de fatos, proíbe repetição integral de frases recentes e pede revisão
  gramatical curta.
- Historian recebe `TYPE`, diferencia alegação/tentativa de fato confirmado e usa schema fechado.
- Respostas geradas normalizam U+2014/U+2013 somente depois do log bruto. No playtest final, houve
  1 travessão na resposta bruta e 0 no conteúdo persistido.

Esses itens são **MITIGADOS**, não declarados como eliminados: invenção, repetição, gramática,
mudança de humor e qualidade narrativa continuam probabilísticos. O playtest curto não substitui
uma avaliação estatística nem repete os 20 turnos originais.

## Validação executada

- `uvx ruff check .`: passou.
- `uvx ruff format --check .`: passou, 26 arquivos já formatados.
- `uvx mypy src/`: passou, 14 módulos sem erros.
- `uv run pytest -x`: **116 passed, 5 deselected**.
- `uv run pytest -m llm -x`: **5 passed, 116 deselected**, usando Gemma 4 local.
- `node --check src/static/app.js` e `src/static/api.js`: passaram.
- Playtest real isolado em `/tmp/roleplay-report-live-ayqs4vpq`: 5 turnos, 10 tentativas LLM,
  0 erros, 3 sugestões, compactação, turno pós-compactação, undo, recusa segura de restore com
  turno novo e restore bem-sucedido após undo.
- Nenhum prompt do playtest continha `SPEAKER=Player`.
- `.data`: 38 arquivos e hash agregado
  `472b03deca0ccdedb925e69b885f24cef017198a53a04dbed6a6514b5f880c0f` antes e depois.

Os sete timeouts/retries dos turnos 14–20 do relatório original não reapareceram nos cinco testes
LLM nem no playtest final. Portanto, a observabilidade foi corrigida, mas não há evidência para
alterar o timeout padrão ou introduzir compactação automática.

## Correções adicionais encontradas ao retomar

Após atualizar para o novo `HEAD`, a revisão encontrou três regressões fora dos achados originais,
mas impeditivas para a saúde do projeto:

- sintaxe de múltiplas exceções incompatível com MyPy em `src/store/presets.py` e
  `src/store/sessions.py`;
- importação local desordenada, comentário longo e ausência de tipo no endpoint de bootstrap em
  `src/main.py`.

Elas foram corrigidas e estão incluídas nas validações acima.

## Fora de escopo e riscos residuais

- `report.md` permaneceu inalterado como evidência original.
- O trabalho Android/Docker não foi alterado. Há uma incompatibilidade potencial a acompanhar no
  APK: o Gradle fixa Python 3.11, FastAPI 0.99 e Pydantic 1, enquanto o projeto declara Python
  3.14+ e FastAPI 0.115+.
- O diretório de playtest em `/tmp` foi preservado para inspeção.
- Nenhum commit, push ou outra mutação Git foi executada por esta remediação.
