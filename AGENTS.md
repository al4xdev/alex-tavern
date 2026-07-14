# Diretrizes do Projeto para Agentes

Alex Tavern é uma aplicação de roleplay multiagente orientada a estado. Um Narrador governa o
mundo físico e roteia a cena; agentes de Personagem falam e pensam com contexto restrito; o
Runner preserva a agência humana, persiste cada sessão e coordena chamadas a provedores LLM.

Este arquivo é o contrato de trabalho para qualquer agente que modificar o repositório. Ele
descreve a arquitetura e as decisões vigentes. História, auditorias e implementações concluídas
ficam em `.plan/closed/`; trabalho ainda aberto fica em `.plan/tasks/`.

> [!IMPORTANT]
> **Regra Básica de Execução para Agentes:**
> Antes de criar qualquer código ou feature nova, você **deve sempre consultar a pasta `.plan/tasks/`** para verificar se já existe uma especificação ou planejamento em andamento, evitando retrabalho e mantendo a consistência arquitetural.
> Dê prioridade e preferência para implementar ou alinhar suas alterações com as tasks que começam com a letra **`S`** (ex: `S01-plugin-system.md`). O prefixo **`S`** indica uma **Supertask**, que planeja uma mudança estrutural e de grande impacto na base de código.

## 1. Visão atual

O projeto está deixando a fase experimental e consolidando uma arquitetura pequena, explícita e
adaptável:

- backend FastAPI e Runner independentes de fornecedor LLM;
- um adapter backend e um adapter frontend por provider;
- configuração e segredos pertencem ao servidor;
- estado persistido em JSON com locks transacionais e escritas atômicas;
- contratos estruturados entre programa e modelo;
- frontend vanilla em módulos ES, sem globals de aplicação;
- plugins Python/JavaScript confiáveis, in-process, sem sandbox e com SDK explícito;
- Experiences como composições ordenadas de plugins/configuração;
- observabilidade, replay, MCP e playtests como ferramentas externas ao turno normal;
- a documentação extensa é parte do estudo de caso, não um problema a ser reduzido.

O objetivo não é acumular mecanismos. É manter limites claros para que novas features sejam
adicionadas no dono correto, com testes e sem ampliar acoplamento.

## 2. Regra forward-only

> **“Mover, em vez de criar retrocompatibilidade e legados. O projeto é muito novo e não deve
> ter dependência de ontem.”**

Este é um projeto novo. Quando um contrato muda, todos os produtores e consumidores mudam juntos.

Não criar:

- conversores ou fallback para formatos anteriores;
- leitura dupla de config, scenario, sessão ou log;
- campos antigos mantidos “por segurança”;
- arquivos duplicados em runtime e source;
- branches permanentes para comportamentos removidos;
- wrappers que apenas preservam uma API interna abandonada;
- caches ou storage alternativos para esconder divergência de contrato.

Dados locais incompatíveis podem ser descartados durante o desenvolvimento. Se uma mudança exigir
migração real no futuro, ela precisa ser uma decisão explícita de produto, isolada e testada; nunca
deve aparecer incidentalmente dentro do parser atual.

Remover o formato anterior por completo é preferível a transformar o código num conjunto de
camadas de compatibilidade.

## 3. Invariantes de domínio

### Agência e imersão

O humano controla um personagem do mundo. As LLMs não recebem a existência de um “Player”,
usuário ou operador externo.

- `Player.controlled_character_id` é conhecimento do Runner, não dos agentes.
- registros internos com `speaker="Player"` são renderizados com o nome do personagem antes de
  chegar a qualquer prompt;
- quando o Narrador escolhe o personagem controlado como próximo falante, o Runner devolve o
  controle ao humano e não gera sua fala;
- não existe nome, persona ou prompt separado para o jogador;
- nenhuma chamada nova pode contornar essa trava de agência.

### Responsabilidades dos papéis

| Papel | Responsabilidade | Contexto permitido |
|---|---|---|
| Narrador | Mundo físico, consequência, transição, cena, humor e próximo falante | Cena, todos os personagens, `mind`, `body`, resumo e janela ativa |
| Personagem | Somente fala e pensamento subjetivo em primeira pessoa | Sua `mind`, sua própria nota, contexto do Narrador, falas públicas e pensamentos próprios |
| Runner | Agência, ordem das chamadas, estado, locks, persistência e routing | Estado completo da aplicação, nunca decisões narrativas heurísticas |
| Historiador | Compactar eventos antigos sem cruzar fronteiras privadas | Resumo mundial recebe eventos públicos; cada memória privada recebe eventos públicos, nota própria e pensamentos próprios |

Personagem não executa nem descreve ação física. Pensamento sobre outra pessoa é interpretação
subjetiva, não descrição objetiva. `body`, cena, narração histórica, personalidade alheia e notas
de outros personagens nunca entram no prompt de Character.

### Estado canônico

- Personagem usa uma única forma: `{"mind": {...}, "body": {...}}`.
- Personalidade usa apenas `personality`.
- Cena usa campos reservados (`location`, `time_of_day`, `present_characters`) e
  `physical_facts` para fatos livres.
- Scenarios built-in imutáveis vivem em `src/scenarios/`.
- Config, scenarios do usuário, sessões, backups e logs vivem exclusivamente em `.data/` ou no
  `ROLEPLAY_DATA_DIR` do deployment.
- Cada sessão vive em `.data/sessions/{id}/`, com `state.json`, `debug.jsonl` e `backups/`.
- Cache, ativação física, config, ambiente e journal de plugins vivem em `.data/plugins/`.
- `.data/` nunca é rastreado pelo Git nem reutilizado por CI/CD.

## 4. Arquitetura e ownership

```text
Frontend ES modules
    ├── api.js
    ├── setup.js
    ├── runtime-config.js
    ├── plugin-runtime.js / plugin-center.js
    └── adapters/<provider>.js
                 │ HTTP
                 ▼
FastAPI ── RuntimeState ── PluginRuntime ── Runner ── role agents
                                  │
                                  ▼
                         shared LLM client
                          ├── adapters/<provider>.py
                          ├── schema.py
                          └── debug_log.py
```

### Runner e concorrência

`src/runner.py` não mantém `GameState` em `self`. Cada operação resolve a sessão pelo ID.

Turnos, sugestões, snapshots, histórico, preview, fork, delete, undo, compactação e restauração
compartilham o mesmo lock por sessão. Não introduza um endpoint que leia ou altere uma sessão fora
desse limite transacional.

- save crítico usa temporário, flush, `fsync` e rename;
- delete espera operações ativas e remove estado, log e backups juntos;
- scenarios têm lock por nome;
- debug JSONL tem lock próprio para append e leitura;
- registries de locks usam referências fracas;
- locks atuais são process-local: o deployment suportado usa um único processo Uvicorn.

`RuntimeState`, pertencente ao FastAPI, reúne config persistida, config resolvida, cliente HTTP e
Runner ativo. Uma troca de provider persiste e substitui o Runner sob o mesmo lock. Não recrie
globals mutáveis paralelos.

### Plugins e Experiences

Plugins são código confiável in-process e podem substituir comportamento central. Não existe
sandbox nem bloqueio por permissão: `permissions` documenta acesso para review e journal. O escape
`unsafe` é deliberado. O repositório curado fornece confiança por revisão integral da fonte e
SHA-256 fixo; ZIP de terceiro é responsabilidade de quem instala.

- `plugin.toml` é strict/forward-only e usa `schema_version = 1`;
- pacotes instalados são imutáveis por `id/version/hash`;
- arquivos em `.data/plugins/started/` são o conjunto global ativo;
- dependências usam constraints semver e o ambiente exato é reconstruído com uv;
- ordem é um DAG determinístico, e a ordem declarada pela Experience vira arestas padrão;
- filtros pre-commit recebem drafts isolados; falha descarta o draft e desativa o plugin no boot;
- ações post-commit nunca repetem trabalho já persistido;
- wrappers `narrator.call` e `character.call` podem substituir a operação inteira;
- o supervisor precisa ser o pai real do Uvicorn para trocar o processo Python.

O SDK e os contratos machine-readable vivem em `src/plugins/`. Exemplos e CLI de autoria ficam em
`plugins/examples/` e `tools/plugin_author.py`. O hub curado/MCP é um repositório separado; o MCP
não possui ferramentas Git ou publicação.

### Providers

Adapters built-in ficam em `src/llm/adapters/`; providers adicionais devem preferencialmente ser
plugins que registram o mesmo `ProviderAdapter` durante o boot. Cada adapter possui:

- identidade e defaults;
- campos secretos e requisitos de ativação;
- settings forçados;
- URL e autenticação;
- adaptação do request;
- extração do envelope de resposta.

O cliente compartilhado possui HTTP, timeout, retry, política textual e parsing. Validação local
pertence a `src/llm/schema.py`; persistência de observabilidade pertence a
`src/llm/debug_log.py`. Diferenças de fornecedor não entram no Runner nem nos agentes.

Frontend adapters built-in ficam em `src/static/adapters/`; plugins registram o mesmo contrato pelo
SDK do browser antes de `RuntimeConfig.init`. Cada um declara card, campos, segredo,
settings forçados, parsing e serialização. `index.html` contém somente containers; não adicione
formulário hardcoded por provider nem branches de provider em `runtime-config.js`.

Adicionar um provider exige os dois adapters e testes de config, redaction, request, response e UI.
O registry backend extensível é a fonte de verdade do contrato do servidor; a UI recusa catálogos
divergentes em runtime.

### Contratos estruturados

Narrador, Character, sugestões e Historiador usam JSON. Llama.cpp recebe JSON Schema nativo. DeepSeek V4
Flash recebe `json_object`, a instrução técnica de schema adicionada pelo adapter e validação local
posterior. Isso é adaptação de capacidade, não um prompt narrativo específico por provider.

`src/llm/schema.py` implementa um subconjunto explícito. Tipo, keyword ou constraint não suportado
deve falhar antes de aceitar a resposta. Nunca ignore silenciosamente uma parte do schema e nunca
substitua contrato estruturado por parser regex.

### Configuração e segredos

`.data/config.json` é a única configuração runtime. Ela contém config comum, provider ativo e um
objeto completo por provider.

- `GET /config` retorna somente representação redigida;
- segredo em branco no PUT preserva o valor armazenado;
- chave nunca entra em localStorage, cache do service worker, log ou argumento CLI;
- `/config` é network-only;
- deployments criam sua própria config; não copiam a config de desenvolvimento.

## 5. Fluxo de um turno

1. Runner adquire o lock da sessão e carrega o estado.
2. `turn.input` pode transformar um draft da entrada.
3. Fala, pensamento privado e ação humanos são persistidos separadamente com um único `turn_number`.
4. Narrador recebe o estado canônico e devolve JSON validado; wrappers/filtros podem substituir a chamada/saída.
5. Runner aplica `force_speaker` quando solicitado e preserva a agência do personagem controlado.
6. Se necessário, Character recebe apenas seu contexto permitido e gera `speech`/`thought` estruturados.
7. Runner aplica `scene_update` e `mood_updates` e executa `turn.before_commit` em draft isolado.
8. Estado é salvo atomicamente, a revisão avança uma vez e `turn.after_commit` é emitido.

Todos os registros do passo compartilham `turn_number`, `scene_snapshot`, `mood_snapshot` e
`plugin_state_snapshot`. Undo
remove o passo inteiro e restaura esses snapshots.

Qualquer nova chamada ao modelo precisa propagar `session_id`, `turn_number` e `agent` para o log.
Não existem chamadas LLM invisíveis.

## 6. Prompts e contexto

Prompts são compartilhados entre providers e descrevem regras de papel de forma declarativa.

- não criar prompt narrativo especial para um fornecedor;
- não repetir a mesma regra em várias camadas;
- não introduzir macros, injeção por profundidade ou parser textual;
- não limitar a narração por quantidade fixa de frases;
- manter fatos atribuídos como alegações até confirmação pelo Narrador;
- consequência imediata vem antes de expansão sensorial;
- humor é estado persistente e muda somente quando houver mudança real;
- texto gerado não usa em dash/en dash; a normalização é global no cliente;
- histórico é limitado por orçamento de tokens, nunca por corte de caracteres.

Compactação é um evento transacional: cria backup, resume turnos antigos, mantém a janela recente
e atualiza `story_summary`/`character_notes`. Restauração só ocorre quando não apagaria turnos
novos. RAG, se implementado, será recuperação semântica de volume externo e não um segundo sistema
de memória para fatos já presentes na sessão.

## 7. Observabilidade e ferramentas

`.data/sessions/{id}/debug.jsonl` é a evidência primária de execução. Ele registra:

- `turn_input` antes da primeira chamada;
- request redigido, response, tentativa, duração e tamanho de prompt;
- tipo e representação de erros;
- marcadores de undo, compactação e restauração.

O log é append-only. Undo não apaga evidência.

Ferramentas em `tools/` ficam fora do runtime narrativo:

- `replay_llm.py`: servidor determinístico compatível com a API LLM;
- `replay_session.py`: reproduz inputs atuais contra a API real;
- `mcp_server.py`: inspeção e mutações de debug via stdio;
- `playtest_harness.py`: cenários repetíveis, fila e comparações A/B.
- `plugin_author.py`: contract, scaffold, validate, test, pack e trace de plugins;
- `plugin_hub.py`: clone limpo do hub curado e instalação por hash.

Não adicionar compatibilidade com logs sem `turn_input`. Fixtures representam somente o contrato
atual.

## 8. Frontend e deployments

O frontend é dependency-free e usa módulos ES. Comunicação entre módulos ocorre por imports e
injeção explícita de callbacks, não por variáveis globais. Config do jogo pode usar localStorage;
config e segredos de provider não podem.

Pipelines existentes vivem em:

- `.ci-cd/android/`;
- `.ci-cd/test/`;
- `.ci-cd/docker/`.

Os três arquivos em `.github/workflows/` são apenas entrypoints obrigatórios do GitHub e delegam
para composite actions em `.ci-cd`.

Todos os deployments executam o mesmo backend e o mesmo contrato de dados. Não manter stack de
dependências, config ou source alternativo para um deployment. A versão de Python e dependências
de cada pacote precisam ser compatíveis com o contrato canônico do `pyproject.toml`.

Android permanece fora do escopo desta plataforma de plugins. Não condicione decisões do SDK,
runtime, UI ou supervisor a esse deployment enquanto ele estiver em beta.

## 9. Critério de entrega

Uma mudança não está pronta apenas porque não lançou exceção.

Antes de fechar:

1. confirme ownership: a mudança está no módulo/adapter correto;
2. remova o caminho substituído, sem mantê-lo como fallback;
3. revise locks e atomicidade de toda mutação compartilhada;
4. teste sucesso, erro, input vazio/inválido e concorrência quando aplicável;
5. inspecione prompt, resposta bruta, estado persistido e debug log quando tocar LLM;
6. execute um boundary real proporcional ao risco (HTTP, stdio, frontend ou provider);
7. atualize README e mova plano/task concluído para `.plan/closed/`;
8. confirme que `.data`, segredos e artefatos locais não estão no Git;
9. não faça commit ou push sem autorização explícita e específica.

Validação padrão após alterar Python:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy src/ tools/playtest_harness.py tools/mcp_server.py tools/replay_llm.py tools/replay_session.py
uv run pytest -x
```

Para frontend, valide todos os módulos com Node, carregue o registry de adapters e faça parsing do
HTML. Para mudanças de integração, use também o smoke test HTTP ou a ferramenta real do boundary.

## 10. Referências rápidas

- `README.md`: estudo de caso e documentação detalhada.
- `src/runner.py`: orquestração e agência.
- `src/models.py`: domínio persistido.
- `src/config.py`: config canônica e redaction.
- `src/llm/adapters/`: providers backend.
- `src/static/adapters/`: providers frontend.
- `src/plugins/`: manifestos, SDK, hooks, store, runtime, Experiences e contratos.
- `src/static/plugin-runtime.js`: SDK/loader frontend.
- `src/static/plugin-center.js`: gestão Experience-first.
- `src/llm/schema.py`: contrato estruturado local.
- `src/llm/debug_log.py`: observabilidade persistida.
- `tools/README.md`: operação de replay, MCP e harness.
- `.plan/tasks/`: trabalho aberto.
- `.plan/closed/`: decisões e entregas concluídas.
