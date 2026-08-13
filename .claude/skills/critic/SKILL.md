---
name: critic
description: Submete o conteúdo que você acabou de escrever (task, decisão, closure, relatório, entrada de roadmap) a um subagente crítico isolado que só lê o conteúdo — sem código, sem tasks, sem histórico — e devolve um veredito por afirmação (ADVANCES / NEUTRAL / WORSE THAN ABSENT / UNSUPPORTED) com falsificador e métrica. Use antes de gravar qualquer coisa em `.plan/`, ao revisar o que outro modelo produziu, ou quando precisar decidir se um achado merece existir. A doutrina completa está em `.plan/reference/critic-protocol.md`.
---

# Crítico — o conteúdo se defende sozinho ou não entra

Este projeto encontrou **todos** os seus achados reais lendo texto, e **nenhum**
por uma métrica ter apitado. Esta skill é a contraparte: antes de o texto virar
registro, alguém que não participou da escrita tenta derrubá-lo.

Leia `.plan/reference/critic-protocol.md` antes de rodar. Ele é a fonte da
verdade e é portável — vale para qualquer modelo ou ferramenta, não só Claude.
Esta skill é só o procedimento de disparo.

## 1. Extrair as afirmações

A unidade **não é a linha**. É a **afirmação**: toda frase que um leitor usaria
para decidir algo — um número, uma causa, uma recomendação, um status, um
fechamento. Um crítico segurando uma linha solta só consegue dizer se ela está
bem escrita, que é a coisa menos útil e a mais fácil de fingir.

Prosa sem afirmação (moldura, transição, transcrição citada) não vai a revisão —
não há o que estar errado nela.

Numere as afirmações do artefato. Se um artefato tem zero afirmações, ele não
precisa de crítico; precisa de justificativa para existir.

### Marque o status de cada afirmação — e mantenha a marcação viva

Ao lado do veredito, toda afirmação carrega um **status**, que diz que tipo de
coisa ela é. São eixos independentes: uma THEORY pode ser a frase mais valiosa
do documento, e um número MEASURED pode ser pior do que ausente.

| status | significa |
|---|---|
| **MEASURED** | número com método nomeado, n e controle; outra pessoa reproduz |
| **OBSERVED** | alguém leu e viu; n pequeno e declarado, sem instrumento |
| **THEORY** | mecanismo proposto; nada medido |
| **ASSUMED** | herdado de texto anterior, nunca conferido aqui |

**Teoria escrita na gramática de medição é WORSE THAN ABSENT automaticamente** —
por mais plausível que seja, porque o próximo leitor vai citar como estabelecido.
Escreva o status no texto, não só na revisão: *"não diagnosticado"*, *"lido em
seis sessões"*, *"pooled em N sessões, mediana M"* são as palavras que carregam
isso.

**Promover e despromover acontece durante o trabalho, não no fim.** Cada vez que
uma evidência chega, volte e re-etiquete o que você já escreveu:

- promoção sobe um degrau por vez — `ASSUMED → THEORY` (mecanismo explícito e
  falsificável) → `OBSERVED` (leitura real, com n e método) → `MEASURED`
  (métrica + controle + spread por sessão + regra pré-registrada **antes** dos
  números). Nada pula degrau.
- despromoção é **obrigatória** quando o instrumento falha (`MEASURED → THEORY`:
  o score 0.02 e a taxa de 34%), quando o spread mostra que o número descreve só
  as sessões vistas (`MEASURED → OBSERVED`), ou quando um controle mostra que o
  efeito é fundo (`OBSERVED → THEORY`: 36 de 39, Fisher p = 0.43).

Despromoção se escreve **onde a afirmação mora**, carregando o histórico —
*"medido, despromovido em <data> porque <o quê>"*. Retratação arquivada em outro
lugar deixa a frase errada no caminho do leitor, e sem o histórico alguém
re-promove ela em silêncio no mês seguinte.

## 2. Escolher o lote

Um artefato por disparo: um arquivo de task, uma entrada de decisão, um closure,
uma seção de relatório. O crítico precisa de contexto suficiente para julgar
"isso avança?", e um parágrafo isolado normalmente não é.

## 3. Disparar o crítico isolado

Lance um subagente `general-purpose` **novo**. Nunca `SendMessage` para um agente
existente — um crítico que assistiu ao trabalho acontecer já foi convencido.

O prompt literal está em `.claude/skills/critic/agents/critic-prompt.md`. Use-o
como está, colando o conteúdo sob revisão no lugar marcado.

**Contrato de isolamento** (violar isto invalida o veredito):

- Entregue APENAS: o conteúdo sob revisão, o texto do prompt do crítico, e —
  se houver número em jogo — `.plan/reference/metric-validity.md`.
- PROIBIDO entregar: código, arquivos de task, roadmap, histórico do git,
  vereditos anteriores, quem escreveu, ou por que você acha que está certo.
- PROIBIDO ao crítico: abrir qualquer arquivo além dos entregues, editar
  arquivos, ou propor implementação.

Para o que importa de verdade, **varie o crítico** — outro modelo ou outro
enquadramento. Auto-revisão do mesmo modelo tem a menor superfície de
discordância possível.

### Vários críticos: a divergência é o sinal

Quando uma afirmação decide alguma coisa, dispare mais de um crítico **em
paralelo** (chamadas independentes no mesmo bloco). E leia o resultado certo:

- **Concordância não é evidência.** Prompts iguais para modelos iguais concordam
  por construção — isso não mediu nada.
- **A divergência aponta exatamente a afirmação cujo apoio é fino**, que era a
  única coisa que você queria achar.
- **Não vote e não tire média.** Assuma o **veredito mais duro** como o que
  precisa ser respondido, e registre que os críticos divergiram e o que cada um
  viu. Afirmação que sobrevive a um crítico tentando despromovê-la vale mais que
  afirmação aprovada por três críticos agradáveis.

Enquadramentos diferentes valem mais que seeds diferentes. Um trio que funciona:
um crítico instruído a **despromover** (achar teoria vestida de medição), um a
responder só **"o registro pioraria sem isso?"**, e um que recebe **só os números
e nenhuma prosa**. Custo é real — não faça leque em tudo, só no que trava uma
decisão.

## 4. Ler o retorno

Por afirmação, o crítico devolve um veredito e três respostas obrigatórias:
o que falsificaria a afirmação, qual a leitura mais forte contra ela, e se o
registro ficaria pior sem ela.

| veredito | leitura |
|---|---|
| **ADVANCES** | um leitor consegue fazer algo que não conseguia — o crítico tem que dizer **o quê** |
| **NEUTRAL** | verdadeiro, defensável, e não adiciona nada |
| **WORSE THAN ABSENT** | o registro fica mais difícil de usar com isso dentro |
| **UNSUPPORTED** | o texto não carrega o próprio peso; volta ao autor com o falsificador junto |

O crítico **não é aprovador**. `ADVANCES` não torna a afirmação verdadeira —
torna ela digna de ser mantida enquanto alguém confere. Mudança de schema, de
grafo ou de ordem do roadmap continua sendo decisão do dono.

## 5. Métrica

Toda afirmação numérica precisa de uma métrica nomeada, vinda de uma destas três
fontes (em ordem de preferência):

1. **Métrica existente** — confira `.plan/reference/metric-validity.md` primeiro;
   ele diz quais são confiáveis, quais foram rebaixadas e quais foram medidas e
   rejeitadas.
2. **Métrica nova** — que passa a dever: um controle, o spread por sessão, uma
   regra pré-registrada e uma entrada no registro.
3. **O julgamento do próprio crítico, declarado como métrica** — legítimo e
   frequentemente o melhor disponível. *"Li seis destes e não consegui
   distinguir"* é uma medição. Reporte como o que é (n, método, incerteza do
   crítico), nunca lavado em porcentagem.

Regras que o crítico cobra e que não são preferência de estilo — cada uma está
aí porque foi violada e custou algo — estão na seção *Metric culture* do
protocolo. As três que mais aparecem: **a sessão é a unidade**, **todo número de
manchete carrega o spread por sessão**, e **nunca case um NOME com heurística de
string**.

## 6. Fechar no schema do `.plan`

O veredito decide a pasta:

| veredito | destino |
|---|---|
| ADVANCES + fecha uma pergunta | `closed/`, com a evidência que fechou |
| ADVANCES + abre trabalho desta fase | `tasks/`, mecanismo **não diagnosticado** salvo se foi medido |
| ADVANCES + real mas não desta fase | `backlog/` — **este é o padrão para achado novo** |
| ADVANCES + precisa do dono | `para-o-dono/` |
| NEUTRAL | não escreva; não existe pasta para isso |
| WORSE THAN ABSENT | apague, e registre a rejeição onde ela seria re-derivada (seção *medido-e-rejeitado* da task, ou `metric-validity.md`) |
| UNSUPPORTED | volta ao autor, não entra em pasta nenhuma |

**Uma fase não cresce enquanto ninguém olha.** Achado novo vai para `backlog/`
por padrão; promover para `tasks/` é decisão do dono.

## 7. Consolidar

Relate em um único bloco: as afirmações numeradas, o veredito **e o status** de
cada uma, o falsificador de tudo que ficou como ADVANCES, tudo que foi apagado e
por quê, tudo que foi promovido ou despromovido e com base em qual evidência, e
qual métrica sustentou cada número. Se o crítico e uma leitura humana
discordarem, **a leitura vence e o crítico ganha uma entrada em
`metric-validity.md`** — a mesma regra que vale para todo instrumento aqui.
