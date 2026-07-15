# 💬 Atalhos & Recursos

Use estas ferramentas para controlar o fluxo da narrativa:
- 💡 **Sugestão**: Peça para a IA sugerir uma próxima ação para o seu personagem.
- 📜 **Dica do Narrador**: Force um acontecimento ou detalhe do ambiente no próximo turno.
- ↩ **Desfazer (Undo)**: Reverte o último turno completo (sua ação e a reação dos NPCs).
- ⏭ **Pular (Skip)**: Pula o seu turno, permitindo ao Narrador avançar a cena ou os NPCs agirem.

## Comandos com barra

Digite `/` no campo **Fala** para abrir a paleta. A barra digitada vira o sigilo violeta ao lado do
campo, mantendo limpa a busca do comando. Ela reúne ações do Alex Tavern e contribuições dos
plugins ativos. Continue digitando para filtrar, use ↑/↓ para escolher, Tab para completar o nome
canônico e Enter para ativar. Ferramentas backend abrem um cartão bem delimitado com todos os
campos necessários.

Os built-ins incluem `/help`, `/plugins`, `/settings`, `/sessions`, `/new`, `/suggest`, `/hint`,
`/undo`, `/skip`, `/compact` e `/restore`, além de aliases em português. Ações indisponíveis
continuam visíveis e explicam o motivo. Ferramentas e ações de plugins mostram sua origem.

Comandos são utilitários, não falas do personagem. A entrada vai direto para a ferramenta e não
cria turno, não chama o Narrador, não muda o histórico de undo e não aparece no chat. Um comando
errado é interrompido com uma explicação, em vez de ser enviado como fala.

Para o personagem dizer literalmente algo começando por `/`, digite `//`. A segunda barra fecha a
paleta e o sigilo imediatamente, deixando uma única barra literal no campo de fala.

## Conversor de personagem

Com o plugin curado **Character Converter** ativo, use:

`/convert-character`

Preencha o nome do preset no campo visível. Depois, cole uma descrição ou escolha um Character
Card aberto V1/V2/V3 em PNG/JSON. Não preencha
as duas fontes. Um PNG comum de avatar não contém a ficha e recebe um erro claro. A ferramenta não
tenta adivinhar um personagem pelos pixels da imagem.

O resultado abre como rascunho editável de preset. Revise nome, personalidade, conhecimentos,
aparência, roupa, humor e avatar opcional antes de pressionar **Salvar preset**. Um nome já existente
sempre pede confirmação antes de ser substituído.
