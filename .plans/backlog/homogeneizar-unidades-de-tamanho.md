# Homogeneizar unidades de tamanho dos prompts

Status: backlog. Não implementar nesta tarefa.

Problema: os prompts usam palavras, frases e instruções qualitativas para orientar
o tamanho; o painel também apresenta limites técnicos de tokens. O objetivo é
definir uma forma consistente de configurar a extensão desejada por função.

Inventário inicial: prosa (mínimo de palavras), personagem e sugestões (máximo de
frases), memória privada (máximo de palavras), drive/watcher (frases), premissa do
roteiro (frases), eventos de percepção (uma frase), gancho de abertura (palavras).

Decidir a unidade comum e a semântica de mínimo, máximo ou faixa. Manter valores
próprios para cada função. Distinguir a extensão desejada do teto técnico de
tokens e propagar a escolha pela configuração, UI e builders compartilhados.
Não cortar texto automaticamente nem acrescentar contagem/retries sem necessidade.

O dono relatou degradação com reasoning desligado em outra task e voltou a ativá-lo.
É contexto da proposta, não evidência de que reasoning faça o modelo contar palavras
ou cumprir limites melhor. Se necessário avaliar isso, registrar antes um critério
e comparar payloads reais com o mesmo prompt, variando somente reasoning.

Aceite: unidades e significado explícitos na UI, configuração validada, ausência
de instruções antigas conflitantes, sugestões usando a mesma base do personagem,
e verificação proporcional de propagação. Qualquer alegação de maior precisão de
tamanho depende de avaliação real, separada da correção do encadeamento técnico.
