# .plan — mapa da pasta

Não há mais `ROADMAP.md` monolítico (removido 2026-07-20): o estado vive
**distribuído** — o que está feito em `closed/`, o que está ativo em `tasks/` (com
banner de status no topo), e a narrativa/racional nos artigos de `docs/cases/`.
Organizado por estado:

| Pasta/arquivo | O que é | Quando olhar |
|---|---|---|
| `tasks/` | Tarefas **ativas** (abertas ou entregues-com-ressalva, banner no topo). Track aberto atual: **43 — substrato de disposição** (roadmap fasado, artigo Nº 15) | Ao trabalhar |
| `para-o-dono/` | Coisas esperando **ação sua** (smoke tests, desenhos pra aceitar) | Quando você voltar |
| `backlog/` | Futuro sem trabalho ativo (02 mídia, 06 RAG, 16 lore, persona pública/real, New Journey, S02) | Ao planejar |
| `reference/` | Docs de arquitetura vivos (mapa 29.2, estudo narrator_hint) | Ao desenhar |
| `closed/` | Tarefas fechadas COM CONFIANÇA + explorações concluídas | Como histórico |

Convenções permanentes: só migra pra `closed/` tarefa fechada com confiança;
commits em inglês sem trailer de IA; método curl-first (AGENTS.md §6 — a variante
validada É a shippada); evidência de benchmark em `output29/` e `plans/artifacts/`
(gitignored, local).

A série de artigos científicos do projeto vive em `docs/cases/` (índice
próprio com reading paths).
