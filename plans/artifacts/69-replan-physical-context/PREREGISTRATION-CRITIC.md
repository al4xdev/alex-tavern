CLAIM 1: Registro anterior ao disparo, sessão fb62cc2f T7, replan aceito na linha 86.
VERDICT: ADVANCES
STATUS: ASSUMED
STATUS AS WRITTEN: OBSERVED
REWORD: “Registro declarado anterior ao disparo; caso selecionado: fb62cc2f T7, linha 86.”
WHAT A READER CAN NOW DO: Identificar a unidade experimental e verificar a anterioridade do registro.
FALSIFIER: Metadados mostrarem respostas experimentais anteriores ao registro ou a linha indicada pertencer a outra chamada.
STRONGEST CASE AGAINST: A data escrita no próprio documento não comprova pré-registro.
WORSE IF DELETED? yes
METRIC: Proveniência declarada de um caso; não há comprovação temporal no conteúdo.

CLAIM 2: O beat descreve Holt selando a porta; o snapshot registra a porta aberta; não há enactment confirmado nos eventos anteriores inspecionados.
VERDICT: UNSUPPORTED
STATUS: OBSERVED
STATUS AS WRITTEN: OBSERVED
FALSIFIER: Um evento anterior confirmar a ação, ou o beat apresentar o selamento como acontecimento novo.
STRONGEST CASE AGAINST: O conteúdo não reproduz o beat nem delimita os eventos inspecionados. O leitor não consegue distinguir uma falsa retrospectiva de uma ação iniciada no próprio beat.
WORSE IF DELETED? yes
METRIC: Leitura de um caso, com extensão e critérios da inspeção não especificados.

CLAIM 3: Uma porta aberta pode estar danificada; isso, isoladamente, não constitui contradição.
VERDICT: NEUTRAL
STATUS: THEORY
STATUS AS WRITTEN: THEORY
FALSIFIER: Nenhum — possibilidade lógica geral.
STRONGEST CASE AGAINST: O caso apresentado trata de selamento, não de dano. A ressalva responde a uma interpretação que o documento não expõe.
WORSE IF DELETED? no
METRIC: Não aplicável.

CLAIM 4: Omitir fatos físicos canônicos pode permitir antecedentes sem suporte; o experimento testa fornecê-los.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: THEORY
WHAT A READER CAN NOW DO: Separar a hipótese investigada de uma causa estabelecida.
FALSIFIER: A formulação “pode permitir” não tem falsificador global definido. Nesta comparação, ausência de diferença não refutaria o mecanismo geral.
STRONGEST CASE AGAINST: Inserir JSON altera também comprimento, posição relativa e saliência do contexto. Uma diferença entre braços não identificaria qual desses mecanismos atuou.
WORSE IF DELETED? yes
METRIC: Comparação proposta entre dois payloads de uma mesma chamada; quatro gerações por braço, sem resultado ainda.

CLAIM 5: A reproduz o request; B insere physical_facts de history[55].scene_snapshot; os outros campos permanecem iguais.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: Protocolo prospectivo
WHAT A READER CAN NOW DO: Construir os braços e auditar sua diferença.
FALSIFIER: Um diff revelar diferenças adicionais ou a inserção usar outro snapshot.
STRONGEST CASE AGAINST: O documento não demonstra que esse snapshot ainda representa os fatos físicos no instante do replan. Um estado pré-turno pode divergir de acontecimentos ocorridos durante o turno.
WORSE IF DELETED? yes
METRIC: Controle A declarado; unidade experimental: uma chamada selecionada. A pertinência temporal do snapshot permanece assumida.

CLAIM 6: Quatro chamadas por braço, ordem embaralhada com seed 697107, concorrência quatro, retry apenas sem resposta HTTP, preservando inválidos e faltantes.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: Protocolo prospectivo
WHAT A READER CAN NOW DO: Executar uma amostragem limitada sem esconder falhas nem repetir respostas desfavoráveis.
FALSIFIER: Logs mostrarem chamadas extras fora da regra, descarte de inválidos ou execução divergente.
STRONGEST CASE AGAINST: O seed fixa a ordem, não a amostragem do modelo. As oito saídas continuam sendo réplicas de um único contexto.
WORSE IF DELETED? yes
METRIC: Novo desenho experimental: n planejado de quatro gerações por braço, uma sessão; sem dispersão entre sessões possível.

CLAIM 7: O leitor isolado avaliará oito alternativas opacas, citará evidências, preservará incerteza e salvará a leitura antes de revelar os braços.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: Protocolo prospectivo
WHAT A READER CAN NOW DO: Produzir uma leitura inicialmente independente do conhecimento dos braços e conservar seu registro.
FALSIFIER: O leitor receber rótulos dos braços antes de salvar a análise, ou a leitura não incluir evidências.
STRONGEST CASE AGAINST: “Continuidade”, “agência”, “progressão coerente” e “material” não têm critérios operacionais. O julgamento pode variar sem que as saídas variem.
WORSE IF DELETED? yes
METRIC: Novo julgamento qualitativo; um leitor, até oito saídas de uma sessão. Deve permanecer apresentado como leitura individual, não instrumento validado.

CLAIM 8: Depois de revelar os braços, comparar as alegações com a fonte completa, distinguindo plano de execução.
VERDICT: WORSE THAN ABSENT
STATUS: THEORY
STATUS AS WRITTEN: Protocolo prospectivo
FALSIFIER: Não há falsificador empírico da recomendação; o procedimento é verificável pelo registro de avaliação.
STRONGEST CASE AGAINST: A classificação decisiva é “source-checked”, mas a consulta completa ocorre depois de conhecer os braços. A leitura inicialmente cega não protege essa adjudicação posterior, que pode determinar a aprovação do candidato.
WORSE IF DELETED? no
METRIC: Adjudicação qualitativa posterior ao desmascaramento; não há regra declarada para resolver divergências com a primeira leitura.

CLAIM 9: Menos de três respostas válidas por braço torna a comparação incompleta; sem reprodução inequívoca em A, o replay não valida remédio.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: Regra prospectiva
WHAT A READER CAN NOW DO: Encerrar resultados sem material suficiente ou sem reprodução do defeito.
FALSIFIER: Nenhum — é um critério de decisão, não um resultado empírico.
STRONGEST CASE AGAINST: O limiar três não garante informação suficiente; uma ocorrência em A e nenhuma em B ainda pode decorrer da variabilidade de geração. O próprio limite a um diagnóstico reduz, mas não elimina, esse risco.
WORSE IF DELETED? yes
METRIC: Novos critérios: número de respostas schema-valid e presença de ao menos um antecedente inequívoco em A. Não constituem teste de eficácia.

CLAIM 10: Com reprodução em A, B é elegível para follow-up se nenhuma resposta válida apresentar antecedente sem suporte ou regressão material; ambiguidade não conta como melhoria.
VERDICT: UNSUPPORTED
STATUS: THEORY
STATUS AS WRITTEN: Regra prospectiva
FALSIFIER: Nenhum — regra normativa; sua aplicação pode ser auditada pelas classificações individuais.
STRONGEST CASE AGAINST: O gate exige ausência de defeito confirmado em B, mas não exige explicitamente continuidade confirmada. Um conjunto inteiramente ambíguo pode satisfazer a condição negativa; “ambiguidade não conta como melhoria” não define se esse conjunto bloqueia a elegibilidade. Tampouco está claro se a adjudicação de A deve receber a mesma checagem completa aplicada a B.
WORSE IF DELETED? yes
METRIC: Novo gate qualitativo sobre três ou quatro respostas válidas por braço. Mede elegibilidade exploratória, não correção demonstrada.

CLAIM 11: Relatar leituras individuais, sem pontuação geral ou taxa populacional; falha encerra esta inserção neste payload, sem ajustar sementes ou sinônimos até passar.
VERDICT: ADVANCES
STATUS: THEORY
STATUS AS WRITTEN: Regra prospectiva
WHAT A READER CAN NOW DO: Preservar a unidade de análise e impedir seleção oportunista de variantes.
FALSIFIER: O relatório extrapolar para a população ou repetir a inserção com modificações para obter aprovação.
STRONGEST CASE AGAINST: “Falha” não está explicitamente distinguida de comparação incompleta ou avaliação ambígua, deixando incerto qual resultado encerra o ensaio.
WORSE IF DELETED? yes
METRIC: Regra de relato e parada, sem pretensão de resultado medido.

- **DELETE**: 3, 8.
- **DEMOTE**: 1, de anterioridade aparentemente observada para anterioridade declarada, ainda não comprovada no conteúdo.
- **PROMOTE**: Nenhuma.
- **THE ONE THING**: O gate pode tratar ausência de defeito confirmado em B como elegibilidade, mesmo quando a evidência é apenas ambígua, e a classificação decisiva pode mudar depois da revelação dos braços.
