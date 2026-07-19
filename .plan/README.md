# .plan — mapa da pasta

Uma regra: **`ROADMAP.md` é a fonte única de "onde estamos e o que vem"**.
Todo o resto é detalhe organizado por estado:

| Pasta/arquivo | O que é | Quando olhar |
|---|---|---|
| `ROADMAP.md` | Fila, estado e decisões. Atualizado a cada fechamento | Sempre primeiro |
| `para-o-dono/` | Coisas esperando **ação sua** (smoke tests, desenhos pra aceitar) | Quando você voltar |
| `tasks/` | Só tarefas **ativas** (abertas ou entregues-com-ressalva, banner no topo) | Ao trabalhar |
| `backlog/` | Futuro sem trabalho ativo (02 mídia, 06 RAG, 16 lore, New Journey, S02) | Ao planejar |
| `reference/` | Docs de arquitetura vivos (mapa 29.2, estudo narrator_hint) | Ao desenhar |
| `closed/` | Tarefas fechadas COM CONFIANÇA + explorações concluídas | Como histórico |

Convenções permanentes (também no topo do ROADMAP): só migra pra `closed/`
tarefa fechada com confiança; commits em inglês sem trailer de IA; método
curl-first (AGENTS.md §6 — a variante validada É a shippada); evidência de
benchmark em `output29/` e `plans/artifacts/` (gitignored, local).

A série de artigos científicos do projeto vive em `docs/cases/` (índice
próprio com reading paths).
