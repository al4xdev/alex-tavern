# 🗜️ Compactação da história

Uma aventura longa pode ficar maior do que a quantidade de texto que a IA consegue ler de uma vez. A compactação evita isso transformando acontecimentos antigos em lembranças menores e mantendo as cenas recentes completas.

## Um exemplo simples

Imagine uma aventura com muitos capítulos:

- os capítulos mais recentes continuam escritos por inteiro;
- os capítulos antigos viram um resumo do que aconteceu no mundo;
- cada personagem guarda uma nota separada com apenas suas próprias lembranças;
- a história continua normalmente usando essas lembranças.

A compactação não muda a cena atual, o humor dos personagens nem quem você controla.

## Compactação automática

Quando ela está **ligada**, o aplicativo observa quanto do espaço de leitura da IA será usado pela próxima cena. Se a história estiver se aproximando do limite escolhido, ele resume os acontecimentos antigos antes de chamar o Narrador.

Um turno contendo somente pensamento privado não dispara a compactação. Ela espera até a próxima fala, ação ou avanço do Narrador.

## O que o controle de porcentagem muda

A porcentagem diz quanto do espaço de leitura pode ser ocupado antes de resumir:

- **Baixar o controle:** resume mais cedo. O Historiador trabalha mais vezes, mas sobra mais espaço para a próxima cena.
- **Deixar perto de 80%:** oferece um equilíbrio confortável para a maioria das aventuras.
- **Subir o controle:** espera mais tempo. O Historiador trabalha menos vezes, mas a próxima cena fica mais próxima do limite de leitura.

Essa porcentagem é uma estimativa prática, não uma contagem exata do provedor de IA.

## Compactação manual

O botão 🗜️ no menu de ações faz a mesma operação imediatamente. A barra mostra trabalho realmente concluído: resumo do mundo, lembranças de cada personagem e gravação segura da sessão.

Se ainda não houver acontecimentos antigos suficientes, nada será alterado.

## Posso desfazer?

Sim. Cada compactação concluída cria um checkpoint numerado. O botão 🧯 desfaz primeiro a compactação mais recente e pode ser usado novamente para voltar pelas anteriores.

Turnos jogados depois da compactação são preservados. Os checkpoints ficam guardados junto da sessão até ela ser apagada.

## O que cada agente pode lembrar

- O Narrador recebe o resumo público do mundo, sem pensamentos privados.
- Cada personagem recebe apenas sua própria nota e seus próprios pensamentos antigos.
- Um personagem nunca recebe a nota ou os pensamentos privados de outro.

Se a compactação automática falhar, o aplicativo mantém o histórico como estava e continua o turno usando a janela recente disponível.
