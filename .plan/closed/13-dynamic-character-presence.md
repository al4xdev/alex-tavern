# Task 13: Presença dinâmica de personagens

**Status:** Fechada — implementada em duas fases (core + plugin curado), verificada
end-to-end (backend real + navegador), quality gates completos em ambos os repositórios.
**Formato de entrega:** Plugin híbrido curado (`dev.alex-tavern.dynamic-character-presence`)
**Solicitado pelo usuário:** controle manual simples de quem participa da cena, com controle opcional pelo Narrador

## 1. Objetivo

Adicionar presença dinâmica sem criar uma segunda lista de personagens. Todos os personagens continuam
existindo em `GameState.characters`, com seus dados completos preservados, enquanto
`Scene.present_characters` passa a indicar somente quem está na cena atual.

Quando o plugin estiver ativo:

- cada personagem da interface atual de configuração recebe um toggle de presença;
- ligado significa que o personagem começa presente na cena;
- desligado significa que ele continua salvo na sessão, mas começa fora da cena;
- o Narrador pode adicionar ou retirar personagens durante o turno quando a configuração opcional
  do plugin permitir;
- personagens ausentes deixam de consumir contexto detalhado nas chamadas em que não participam.

O recurso não remove, desativa nem recria personagens. Presença é estado de cena, não estado de
cadastro.

## 2. Experiência de uso

### Toggle na interface atual de personagens

O controle deve ser incorporado ao cabeçalho de cada `.char-card` já existente no setup. Ele não
deve abrir uma tela paralela nem duplicar o editor de personagens.

O toggle usa um rótulo curto e traduzido, como `Na cena`, e precisa comunicar seu estado por texto,
aparência e semântica acessível. Clicar no rótulo também altera o valor. O controle deve funcionar
por teclado, leitor de tela e toque, com alvo mínimo apropriado para mobile.

Ao salvar um scenario ou iniciar uma sessão, os IDs ligados, seguidos do marcador interno `Player`,
formam `scene.present_characters`. Os IDs desligados permanecem em `characters` sem perda de
`mind`, `body`, notas ou histórico. Ao carregar novamente um scenario, a UI restaura os toggles a
partir da lista persistida; `Player` não recebe toggle próprio.

O personagem controlado pelo humano precisa estar presente. Se o usuário desligar o personagem
controlado, a UI deve pedir que escolha outro personagem presente antes de salvar ou iniciar. O
backend repete essa validação e nunca corrige o valor silenciosamente.

### Configuração condicional do plugin

Depois que o plugin for ativado, sua área de configuração exibe:

```json
{
  "allow_narrator_presence_changes": true
}
```

Rótulo sugerido: `Narrador pode alterar quem está na cena`.

- `true`: o Narrador pode propor entradas e saídas em sua resposta estruturada;
- `false`: somente os toggles humanos definem a presença, e o Narrador recebe a lista como contexto
  somente de leitura;
- o campo só aparece enquanto o plugin estiver ativo;
- o valor pertence à configuração do plugin e pode ser definido por uma Experience;
- a ativação inicial materializa o default `true` antes do primeiro uso;
- configuração ausente ou inválida falha de forma explícita; não existe leitura de formato antigo.

A UI dessa configuração deve usar uma contribuição frontend declarada pelo plugin. Se o SDK ainda
não oferecer um slot de configuração, esta task inclui criar um contrato genérico e
machine-readable para configurações de plugins, em vez de adicionar um branch pelo ID do plugin em
`plugin-center.js`, `setup.js` ou `index.html`.

## 3. Estado canônico e invariantes

`Scene.present_characters` continua sendo a única fonte de verdade para presença. O plugin não
mantém uma lista espelho em `plugin_state` ou em sua configuração.

Regras do contrato:

- cada item de personagem é um ID existente em `GameState.characters`;
- IDs são únicos e preservam a ordem canônica de `characters`;
- o personagem controlado está sempre presente;
- o marcador interno `Player` continua presente uma única vez no fim da lista, não vira um
  personagem adicional e nunca é exposto aos agentes como operador externo;
- adicionar ou retirar alguém não altera seu perfil, memória, humor ou corpo;
- personagens ausentes podem retornar posteriormente com o mesmo ID e estado;
- dados inválidos são rejeitados, nunca filtrados ou completados silenciosamente.

O caminho atual que recompõe `present_characters` com todos os personagens em
`Runner.start_session` deve ser substituído pelo contrato atual de entrada. Produtores e
consumidores mudam juntos, sem fallback para o comportamento anterior.

## 4. Controle humano durante uma sessão

Além do estado inicial no setup, o plugin deve contribuir um controle compacto para a interface da
sessão ativa. A mesma lista de personagens usa toggles `Na cena` e permite colocar ou retirar NPCs
sem editar seus perfis.

Cada alteração humana:

- usa um endpoint/contribuição do plugin que resolve a sessão por ID;
- adquire o mesmo lock da sessão usado por turno, undo, compactação e delete;
- valida a revisão esperada para não sobrescrever um turno concorrente;
- realiza uma única escrita atômica e avança a revisão uma vez;
- registra no journal a origem humana e os IDs efetivamente alterados;
- participa da política de undo/auditoria definida para mutações administrativas de sessão.

O controle humano não gera turno narrativo, não chama LLM e não adiciona mensagem ao histórico.

## 5. Controle do Narrador

Quando `allow_narrator_presence_changes` estiver ativo, a chamada normal do Narrador recebe uma
extensão estruturada opcional:

```json
{
  "presence_update": {
    "present_character_ids": ["C1", "C3"]
  }
}
```

A resposta declara a lista completa desejada. Isso evita ambiguidades de operações parciais,
duplicatas e ordem de aplicação.

O resultado é validado antes do commit e aplicado ao draft do mesmo turno. Não existe segunda
chamada LLM, parser textual, regex ou branch específico de provider. A alteração é persistida junto
com narração, fala, pensamento, snapshots e `plugin_state_snapshot`, sob o lock da sessão.

O Narrador não pode retirar o personagem controlado, inserir ID desconhecido ou selecionar um
personagem ausente como próximo falante. Uma proposta inválida é descartada e journalada sem
corromper o estado; o restante da resposta narrativa válida pode continuar.

Quando a configuração estiver desligada, o schema não oferece `presence_update` e qualquer campo
inesperado falha na validação estruturada normal.

### Gap do SDK a resolver

O plugin não deve substituir `narrator.call` inteiro apenas para acrescentar presença. Caso o SDK
ainda não tenha o contrato necessário, esta task inclui um ponto de contribuição estreito para:

- acrescentar contexto do Narrador;
- estender seu JSON Schema com saída opcional pertencente ao plugin;
- validar e aplicar o resultado no draft transacional do turno.

O contrato precisa continuar independente de provider e preservar `session_id`, `turn_number`,
`agent`, debug log, validação local, agência humana e ordem determinística dos plugins. O contrato
machine-readable, o MCP de autoria e a documentação do hub devem ser atualizados junto com o core.

## 6. Contexto e economia de tokens

O Narrador recebe os perfis completos apenas dos personagens presentes. Para ausentes, recebe uma
lista mínima e determinística contendo somente ID e nome, suficiente para saber quem pode entrar na
cena sem carregar personalidade, conhecimento, descrição física ou roupa.

Character calls continuam limitadas ao próprio personagem e só podem ocorrer para um personagem
presente. Personagens ausentes não recebem chamadas autônomas.

Resumo mundial, memórias privadas e histórico permanecem responsáveis pela continuidade. O plugin
não cria outro sistema de memória e não transforma a lista mínima de ausentes em um resumo paralelo.

## 7. Requisitos de frontend responsivo

O critério principal é preservar a densidade e o desenho atuais tanto no celular quanto no PC.
Ativar o plugin não pode deixar os cards carregados, aumentar desnecessariamente sua altura ou
quebrar o fluxo do setup.

### Desktop

- toggle alinhado no cabeçalho do card, junto às ações já existentes;
- nome continua ocupando o espaço flexível principal;
- textos não sobrepõem badge, toggle ou botão de remover;
- estados ligado/desligado continuam legíveis em tema e contraste atuais.

### Mobile

- nenhuma rolagem horizontal em larguras suportadas;
- cabeçalho pode quebrar de linha de maneira intencional, mantendo nome e ações utilizáveis;
- alvo de toque não depende apenas do pequeno indicador visual;
- toggle não reduz campos de texto a uma largura impraticável;
- safe areas, foco visível e teclado virtual continuam funcionando;
- a configuração do plugin usa o mesmo padrão responsivo do Plugin Center.

Os elementos do plugin só são montados quando ele está ativo. Desativá-lo remove os controles sem
deixar espaços vazios, listeners duplicados ou CSS que altere a interface base.

## 8. Ownership e formato do plugin

Formato esperado no hub curado:

```text
plugins/dynamic_character_presence/
├── plugin.toml
├── backend.py
├── frontend.js
└── tests/
```

Permissões esperadas:

- `session.state.write` para alterar `Scene.present_characters` sob o fluxo autorizado;
- `config.read` / `config.write` para `allow_narrator_presence_changes`;
- `frontend.dom.mount` para os toggles e a configuração condicional.

Não deve exigir `model.call`, `network` ou `unsafe`. A própria chamada existente do Narrador é
estendida pelo contrato do SDK.

## 9. Não objetivos

- apagar personagens ou remover seus dados da sessão;
- alterar automaticamente personalidade, corpo, humor, conhecimento ou notas;
- criar uma lista de presença paralela em `plugin_state`;
- manter compatibilidade com sessões que dependam da recomposição de todos os personagens;
- criar prompt ou parser específico para Llama.cpp, DeepSeek ou outro provider;
- permitir que um personagem ausente fale ou que uma LLM controle o personagem humano;
- redesenhar o editor de personagens ou adicionar um painel pesado à tela principal;
- editar `.data/plugins/hub` como fonte do plugin.

## 10. Sequência de implementação

1. Definir fixtures atuais para `present_characters`, incluindo controlado presente, IDs inválidos e
   lista parcial.
2. Remover a recomposição automática no início da sessão e validar a lista recebida no boundary.
3. Adicionar os pontos genéricos do SDK para configuração frontend e extensão estruturada do
   Narrador, caso ainda não existam.
4. Scaffoldar o plugin curado no checkout irmão pelo MCP do hub.
5. Implementar o toggle nos cards atuais do setup e a restauração em scenarios.
6. Implementar o controle compacto na sessão ativa com lock, revisão e escrita atômica.
7. Implementar configuração condicional e controle estruturado do Narrador.
8. Reduzir o contexto de ausentes e impedir Character calls/seleção de falante fora da cena.
9. Validar undo, concorrência, debug/journal, replay e falhas de plugin.
10. Executar testes frontend em desktop e mobile, boundary HTTP real, validação/empacotamento do
    plugin e os quality gates completos do core.

## 11. Critérios de aceitação

- O toggle de cada card define corretamente a presença inicial sem apagar o personagem.
- Salvar e recarregar um scenario preserva exatamente a seleção de presença.
- O backend rejeita ID desconhecido, duplicata, ordem inválida e personagem controlado ausente.
- Com o plugin inativo, não existem toggles, configuração, espaço vazio ou mudança visual na UI.
- Com o plugin ativo, a opção `Narrador pode alterar quem está na cena` aparece na configuração do
  plugin e persiste seu valor.
- Com a opção desligada, somente o humano altera presença e o schema do Narrador não aceita update.
- Com a opção ligada, uma alteração válida do Narrador é aplicada atomicamente no mesmo turno.
- O Narrador nunca retira nem assume o personagem controlado e nunca escolhe ausente como próximo
  falante.
- Um personagem ausente mantém todo o estado e pode retornar mais tarde sem perda de dados.
- Perfis completos de ausentes não entram no prompt do Narrador; a lista mínima contém apenas ID e
  nome.
- Character ausente não recebe chamada LLM.
- Uma mutação humana concorrente com turno, undo, compactação ou delete não produz lost update.
- Undo restaura a presença exata do passo e o debug/journal identifica a origem da mudança.
- O setup e o controle da sessão permanecem legíveis, acessíveis e sem overflow nas larguras mobile
  e desktop suportadas.
- Ativar/desativar repetidamente não duplica controles, listeners nem estilos.
- Testes de frontend carregam todos os módulos, registram o plugin, fazem parsing do HTML e cobrem
  teclado/toque; testes backend cobrem sucesso, erro, input vazio/inválido e concorrência.
- O plugin passa por `plugin_validate`, `plugin_test` e `plugin_pack`, e o core passa pelos quality
  gates antes de mover esta task para `.plan/closed/`.
