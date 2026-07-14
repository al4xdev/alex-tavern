# Plano de remediação do `report.md`

**Data:** 2026-07-12
**Fonte exclusiva:** [`report.md`](./report.md)
**Estado:** pronto para execução autônoma
**Saída prevista:** [`report-remediation-final.md`](./report-remediation-final.md)

> **Nota de contrato (2026-07-14):** as referências a backup e restore neste plano descrevem a
> implementação auditada em 2026-07-12. O contrato atual usa checkpoints incrementais LIFO,
> preserva turnos posteriores e pode compactar automaticamente por pressão estimada de contexto.
> Consulte [Context Compaction](../../README.md#-context-compaction).

## Objetivo

Corrigir e verificar os problemas encontrados no playtest Thorn/Lyra sem incorporar o backlog
privado de tasks. O arquivo `report.md` permanece inalterado como evidência original. Ao final, será
gerado um relatório rastreável, com mudanças, testes, resultados do playtest e riscos residuais.

## Baseline confirmado

Em 2026-07-12, a suíte não-LLM passou com:

```text
101 passed, 5 deselected
```

Os cinco testes excluídos são marcados como `llm`. A inspeção do código atual confirmou:

| ID | Achado do relatório | Estado atual |
|---|---|---|
| B1 | `location` termina em `physical_facts` | Ativo em `Runner._update_scene` |
| B2 | notas da compactação podem usar chaves incompatíveis | Ativo; schema aceita qualquer chave e não há normalização |
| B3 | erro do LLM pode ser registrado como string vazia | Ativo; o log usa apenas `str(e)` |
| B4 | falante forçado pode receber contexto de outro personagem | Ativo; o override ocorre depois da chamada ao Narrador |
| B5 | log não registra o payload nem `force_speaker` | Ativo; o replay ainda precisa inferir esses dados |
| B6 | pytest usa o diretório real de sessões | Já corrigido por `ROLEPLAY_DATA_DIR` e testes de regressão |

Os comportamentos qualitativos do relatório continuam possíveis porque dependem principalmente
dos prompts e do modelo: fatos físicos sem identidade estável, mudanças excessivas de humor,
invenções promovidas a cânone, repetição, descrição da mente dos personagens, falta de consequência
e defeitos de linguagem. A relação entre tamanho de contexto e timeout continua não comprovada.

## Limites de escopo

- Não implementar itens do backlog privado, incluindo agente de correção gramatical, compactação
  automática, RAG, internacionalização ou mídia do README.
- Não alterar nem reescrever `report.md`.
- Não fazer commit, push ou outra mutação git.
- Não usar, limpar ou modificar sessões reais em `.data/` durante testes ou playtests.
- Não declarar um problema qualitativo como resolvido apenas porque um prompt foi alterado.
- Não mudar timeout ou política de compactação com base somente na correlação do playtest original.

## Regras para execução autônoma

1. Preservar mudanças preexistentes do usuário e limitar o diff aos arquivos necessários para os
   achados deste plano.
2. Usar um `ROLEPLAY_DATA_DIR` temporário para toda validação. Antes e depois da suíte completa,
   comparar o inventário/hash de `.data/` para provar que os dados reais não mudaram.
3. Manter compatibilidade com sessões e logs antigos. Novos campos de log serão aditivos, e o
   replay continuará aceitando logs sem o novo marcador de turno.
4. Quando o servidor LLM local não estiver disponível, concluir todas as correções e verificações
   determinísticas e marcar somente o playtest real como `BLOQUEADO`, com a evidência da tentativa.
5. Classificar cada achado no relatório final como `RESOLVIDO`, `MITIGADO`, `NÃO REPRODUZIDO`,
   `BLOQUEADO` ou `ADIADO`, sempre com justificativa e evidência.

## Fase 1 — Corrigir o estado da cena (B1 e fatos físicos frágeis)

### Implementação

- Tornar `location` e `time_of_day` chaves reservadas de `scene_update` no prompt/schema do
  Narrador; elas representam campos de `Scene`, nunca fatos físicos.
- Em `Runner._update_scene`, aplicar essas chaves diretamente a `game.scene.location` e
  `game.scene.time_of_day`.
- Quando a localização realmente mudar, limpar fatos físicos pertencentes à cena anterior antes
  de aplicar o delta restante. Isso impede que portas, iluminação e objetos da taverna sobrevivam
  na torre.
- Preservar o comportamento de delta para os demais campos: valor `None` remove a chave e string
  cria/atualiza o fato.
- Não permitir que `None` apague os campos obrigatórios `location` ou `time_of_day`.
- Reforçar o prompt para reutilizar uma chave estável em `snake_case` para o mesmo fato e evitar
  sinônimos simultâneos como `weather`/`weather_outside`.

### Verificação

- Testar mudança de local, mudança de horário, remoção de fato, atualização no mesmo local e
  limpeza de fatos antigos ao trocar de local.
- Testar que `physical_facts` nunca contém `location` nem `time_of_day` após a aplicação.
- Testar persistência, recarga e undo após uma troca de local.
- Verificar que a UI relê o estado e mostra a nova localização no mesmo turno.

### Critério de aceite

Uma resposta equivalente a `{"location": "The Old Watchtower", "door": "ajar"}` deixa
`Scene.location == "The Old Watchtower"`, contém apenas a porta pertinente em
`physical_facts` e pode ser revertida corretamente por undo.

## Fase 2 — Tornar as notas de compactação utilizáveis (B2)

### Implementação

- Construir o schema do Historian com os IDs reais da sessão como únicas propriedades aceitas em
  `character_notes`; as propriedades permanecem opcionais porque só notas alteradas devem voltar.
- Mudar a apresentação dos personagens no prompt para separar inequivocamente ID e nome.
- Normalizar defensivamente a resposta antes do merge:
  - aceitar a chave canônica exata (`C1`);
  - recuperar formatos observados como `C1 — Thorn`, sem confundir `C1` com `C10`;
  - ignorar chaves desconhecidas;
  - se chave canônica e alias coexistirem, a canônica vence.
- Manter compatibilidade com notas já salvas. Não migrar nem apagar dados antigos automaticamente;
  apenas novas compactações produzem o mapa canônico.

### Verificação

- Cobrir chaves exatas, alias observado no playtest, ID desconhecido, prefixos ambíguos e colisão
  entre chave canônica e alias.
- Fazer um teste integrado `compactar -> salvar -> recarregar -> chamar personagem` e afirmar que
  somente a nota do próprio personagem chega ao seu prompt.
- Confirmar que nenhuma nota de outro personagem é vazada.

### Critério de aceite

Uma saída do Historian com `"C1 — Thorn"` resulta em `game.character_notes["C1"]`, e essa nota
aparece na chamada posterior de Thorn sem aparecer na chamada de Lyra.

## Fase 3 — Corrigir roteamento e replay exato (B4 e B5)

### Implementação do falante forçado

- Validar `force_speaker` logo após carregar a sessão, antes de chamar o Narrador.
- Passar o override válido ao Narrador como uma restrição de roteamento interna, sem mencionar
  jogador ou interface.
- Quando um personagem for forçado, restringir `next_speaker` a esse ID e exigir que
  `context_for_character` seja filtrado especificamente para ele.
- Quando `Narrator` for forçado, exigir contexto vazio e não chamar Character.
- Overrides inválidos continuam equivalentes a `Auto`.

### Implementação do log de turno

- Adicionar um marcador append-only `turn_input` antes da primeira chamada LLM do turno, contendo
  `turn_number`, `speech`, `action`, valor solicitado de `force_speaker` e valor efetivo validado.
- Manter esse marcador fora dos prompts e do estado ficcional; ele existe somente no debug log.
- Fazer o driver de replay preferir `turn_input` para reconstrução exata, mantendo a inferência
  atual como fallback de logs legados.
- Garantir que loaders de fita ignorem o marcador como resposta LLM.

### Verificação

- Simular Narrador escolhendo C1 enquanto C2 é forçado e provar que o contexto recebido por C2 foi
  criado para C2.
- Cobrir override para personagem controlado, NPC, `Narrator`, inválido e ausente.
- Cobrir ordem do log, falha da primeira chamada e repetição de tentativa sem consumir marcadores
  como outputs de replay.
- Reconstruir uma pequena sessão usando apenas o novo log, sem backup auxiliar nem heurística de
  `HISTORY`.

### Critério de aceite

Nenhum Character recebe contexto destinado a outro ID, e o log sozinho contém dados suficientes
para repetir exatamente cada chamada de turno e seu override.

## Fase 4 — Melhorar observabilidade e investigar os retries finais (B3)

### Implementação

- Preservar o campo textual `error` para compatibilidade, mas usar `str(e) or repr(e)` para nunca
  gravar uma mensagem vazia.
- Acrescentar campos estruturados: tipo da exceção, `repr`, duração da tentativa, número da
  tentativa e tamanho aproximado do prompt.
- Registrar os mesmos campos de duração/tamanho nas chamadas bem-sucedidas para permitir
  comparação.
- Adicionar uma opção de timeout na configuração somente para torná-lo explícito e ajustável;
  manter o comportamento padrão atual até existir medição que justifique outro valor.

### Verificação

- Forçar `httpx.ReadTimeout` com representação textual vazia e verificar que tipo e `repr` ficam
  disponíveis no JSONL.
- Cobrir HTTP status error, JSON inválido seguido de retry e sucesso na segunda tentativa.
- Confirmar que os novos campos não quebram UI, MCP, loader de replay nem logs antigos.

### Decisão baseada em evidência

Depois da instrumentação, repetir o roteiro de 20 turnos em armazenamento temporário:

- se `ReadTimeout` for confirmado, registrar latência e tamanho do prompt e ajustar apenas a
  configuração de timeout necessária para o ambiente testado;
- se a falha for de schema/JSON ou transporte, corrigir a causa observada e adicionar regressão;
- se não houver reprodução, não inventar uma correção de performance; classificar como
  `NÃO REPRODUZIDO` e conservar a nova telemetria.

Compactação automática continua fora de escopo porque o relatório não provou que ela é a solução.

## Fase 5 — Reduzir fragilidades dos agentes

Esses itens terão correções de prompt/validação e avaliação comparativa. Eles só serão marcados
como `MITIGADOS` sem uma taxa de falha mensurável igual a zero em amostra suficiente.

### Narrador

- Exigir consequência concreta para a última ação antes de acrescentar ambientação ou abrir outro
  fio narrativo.
- Proibir afirmar pensamentos, intenções ou emoções internas como fato; usar apenas sinais
  observáveis, percepção explicitamente fornecida ou fala/pensamento já presente no histórico.
- Tratar humor como estado persistente: emitir `mood_updates` apenas após mudança emocional
  significativa, não para sinônimos de pose ou disposição momentânea.
- Tornar explícita a diferença entre fato canônico, alegação de personagem e tentativa de ação.

### Character

- Reforçar que conhecimento, notas e contexto são as únicas fontes de fatos; informação ausente
  deve ser omitida ou apresentada como dúvida, nunca como passado inventado.
- Pedir revisão breve antes da resposta e proibir repetição literal de uma frase recente do próprio
  personagem.

### Historian

- Incluir `content_type` junto de cada evento entregue à compactação.
- Tratar diálogo como alegação atribuída e ação do personagem como tentativa até confirmação do
  Narrador; preservar incerteza no resumo em vez de promovê-la a cânone.
- Preservar explicitamente fios abertos, identidades desconhecidas e fatos não confirmados.

### Linguagem e pontuação

- Remover os próprios caracteres U+2014/U+2013 das instruções e separadores dos prompts, usando
  nomes/códigos ou separadores ASCII.
- Manter o log bruto com a resposta real do modelo, mas normalizar esses dois caracteres na saída
  persistida/mostrada para garantir a regra já declarada pelo produto.
- Não criar o agente de correção gramatical opcional. Outros erros de linguagem serão medidos no
  playtest e reportados como risco residual se persistirem.

### Verificação

- Testes de prompt comprovam a presença das regras e a marcação de proveniência dos eventos.
- Testes determinísticos comprovam a normalização de pontuação sem alterar o log bruto.
- Uma avaliação do mesmo roteiro conta: atualizações de humor, repetição literal, afirmações de
  mente, fatos não sustentados, ações sem consequência e defeitos de linguagem.

## Fase 6 — Fechar as lacunas de cobertura do playtest original

- Executar ao menos um turno após a compactação e verificar uso de `story_summary` e da nota
  canônica do Character.
- Exercitar deliberadamente um override diferente da escolha livre do Narrador.
- Exercitar `undo`, `restore_compaction` e `suggest` em armazenamento temporário.
- Confirmar que nenhum prompt contém o marcador interno `Player`.
- Confirmar contagens da janela de compactação e que backups/restauração continuam íntegros.
- Se o LLM real estiver indisponível, executar equivalentes determinísticos/replay e separar essa
  evidência da validação ao vivo no relatório final.

## Fase 7 — Validação técnica final

Executar, nessa ordem:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy .
uvx pytest
```

Depois:

- executar os testes `llm` somente se o endpoint local estiver saudável;
- repetir o playtest isolado descrito acima;
- comparar hashes/inventário de `.data/` antes e depois;
- revisar o diff por escopo, compatibilidade, locks, atomicidade e caminhos de erro;
- conferir cada ID B1-B6 e cada comportamento qualitativo contra evidência concreta.

## Relatório final obrigatório

Criar `report-remediation-final.md` com:

1. resumo executivo;
2. hash/commit-base analisado e escopo do diff;
3. matriz de todos os achados de `report.md`, com status, arquivos alterados, testes e evidência;
4. resultados completos de Ruff, format check, mypy e pytest;
5. resultado do playtest real ou motivo verificável do bloqueio;
6. comparação quantitativa do playtest original versus o novo;
7. prova de que `.data/` real não foi alterado;
8. riscos residuais, itens mitigados e itens que exigem decisão humana;
9. lista explícita de qualquer etapa deste plano que não tenha sido concluída.

O relatório não deve chamar mudanças de prompt de “resolução” sem avaliação e não deve esconder
falhas, skips ou validações indisponíveis.

## Definição de concluído

O trabalho estará concluído quando:

- B1-B5 tiverem regressões automatizadas e comportamento corrigido;
- B6 tiver sido revalidado sem qualquer modificação dos dados reais;
- todas as fragilidades qualitativas tiverem evidência de mitigação ou risco residual declarado;
- a suíte determinística estiver verde;
- o playtest real estiver concluído ou formalmente marcado como bloqueado por indisponibilidade do
  endpoint, sem impedir as demais entregas;
- `report-remediation-final.md` permitir auditoria achado por achado.
