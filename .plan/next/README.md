# `.plan/next/` — Faxina de código para a 1.0

Revisão geral do repositório feita em **2026-07-25** sobre `9387bdc` (working tree
limpo), varrendo `src/`, `tools/`, `tests/`, `.ci-cd/android/` e a raiz.

O objetivo não é achar bug (ver `00-panorama.md` §"O que NÃO encontrei"): é
**entrar na 1.0 sem dívida estrutural**, com abstrações que o próprio código já
está pedindo (mesmo helper escrito 4-6 vezes, mesmo `if` defensivo 19 vezes,
método de 245 statements).

Vale a regra forward-only do `AGENTS.md` §2 em toda esta pasta: **nada aqui cria
retrocompatibilidade**. Onde a limpeza quebra o SDK de plugins ou o schema de
sessão, o doc diz explicitamente e trata a quebra como parte do trabalho.

## Ordem sugerida

| # | Doc | Ganho | Esforço | Quebra |
|---|---|---|---|---|
| — | [00-panorama.md](00-panorama.md) | leitura obrigatória: métricas, baseline e método | — | — |
| 1 | [01-plugin-runtime-null-object.md](01-plugin-runtime-null-object.md) | −19 `if plugins is not None`, −2 variantes de hook | S | SDK (compatível na prática) |
| 2 | [02-infra-json-e-locks.md](02-infra-json-e-locks.md) | −6 cópias de escrita atômica, −4 registries de lock | S | nenhuma |
| 3 | [03-chamada-de-agente.md](03-chamada-de-agente.md) | −18 blocos de 8 linhas idênticos | S/M | nenhuma |
| 4 | [04-debug-log-envelope.md](04-debug-log-envelope.md) | −~120 linhas, envelope único | S | formato JSONL (aditivo) |
| 5 | [05-runner-player-turn.md](05-runner-player-turn.md) | quebra o método de 245 statements / 80 branches | L | nenhuma |
| 6 | [06-forward-only-residual.md](06-forward-only-residual.md) | remove migração v1 de config e defaults mortos | M | config/sessão (previsto) |
| 7 | [07-main-api.md](07-main-api.md) | contrato de erro único, imports no topo, dedup | M | HTTP (interno) |
| 8 | [08-validacao-e-pydantic.md](08-validacao-e-pydantic.md) | −50 linhas do shim, validação em 1 lugar | M | nenhuma |
| 9 | [09-contrato-de-hooks.md](09-contrato-de-hooks.md) | fim do drift entre `contracts.py` e o runner | S/M | SDK (nomes) |
| 10 | [10-frontend-app-js.md](10-frontend-app-js.md) | quebra `app.js` (2424 linhas), fecha bypasses de i18n | M/L | nenhuma |
| 11 | [11-android-fora-do-core.md](11-android-fora-do-core.md) | tira o que é do APK de dentro de `src/` | M | HTTP (endpoint removido) |
| 12 | [12-testes-fabricas.md](12-testes-fabricas.md) | 19 arquivos param de repetir SCENE/CHARACTERS | M | nenhuma |
| 13 | [13-prompts-e-idioma.md](13-prompts-e-idioma.md) | dedup de contexto e mensagens PT no core EN | S | nenhuma |

Os itens 1-4 são independentes entre si e não tocam comportamento: dá para
fazer os quatro numa tarde e o diff do 5 já nasce menor. O 5 depende do 1.

## Convenção dos docs

Cada arquivo traz **Sintoma (com `arquivo:linha`)**, **Por que é dívida**,
**Proposta**, **Passos**, **Como validar** e **Não fazer**. Todo número citado
foi medido no repositório, não estimado — os comandos estão em `00-panorama.md`.
</content>
</invoke>
