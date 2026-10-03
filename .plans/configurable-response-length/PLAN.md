# Extensão configurável de narração e personagem

Escopo autorizado: expor os números já usados nos prompts como configurações
por provider, no painel junto do modelo. Não homogeneizar unidades agora.

- `narrator_min_words`: inteiro positivo, valor inicial 150. Substitui o mínimo
  fixo no prompt de prosa, na mesma posição final.
- `character_max_sentences`: inteiro positivo, valor inicial 3. Substitui o teto
  de 1–3 frases no builder de personagem. Sugestões herdam o mesmo valor.

Configuração canônica, defaults dos adapters, UI declarativa comum, tradução e
builders são os únicos responsáveis. Tokens continuam como teto técnico. Não
adicionar contadores, cortes, retries, campos de sessão ou alterações de reasoning.

Preservar as mudanças concorrentes já existentes, especialmente reasoning nos
adapters de DeepSeek. Não editar `.data/` nem commitar. Validar propagação e erros
de configuração com testes locais e checks estáticos; sem bateria de LLM.

Implementado. Os campos estão disponíveis nos painéis de ambos os providers e
na fábrica declarativa usada por plugins; o exemplo OpenRouter inclui os defaults.
Configurações persistidas devem conter os dois campos por provider (150 e 3
preservam os valores anteriores). Não há conversão de formato nem edição de dados
locais. Nenhum campo de sessão foi alterado.

Validação: 117 testes focados passaram. A suíte ampla passou 1081 testes antes de
encontrar uma fixture de configuração sem os novos campos; a fixture foi atualizada
e os 146 testes do trecho final passaram. Lint, mypy e sintaxe dos módulos JS
alterados passaram. Não foi medida obediência da LLM aos valores configurados.
