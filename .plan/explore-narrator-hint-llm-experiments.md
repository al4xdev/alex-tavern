# Explore: geração autônoma de `narrator_hint`

**Data**: 2026-07-18  
**Escopo**: experimento aberto com DeepSeek V4 Flash via `curl`, usando o
estado anterior ao hint humano do turno 10 da sessão `e5a0ca6a`.

## Objetivo e critério

O hint humano de referência foi mantido fora dos prompts:

> todo nobres riem de link, devido a cena e a sujeira dele

Uma saída foi considerada próxima quando descobriu autonomamente a consequência
social preparada: um rival hostil inicia o deboche, personagens/status alinhados
propagam uma reação pública contida e um personagem protetor pode reagir ao
excesso. Repetir o interrogatório de Maelis, controlar Link, inventar perigo ou
apenas prolongar o silêncio foi considerado falha.

As chamadas anteriores ao pedido explícito de “recomeçar do zero” e três smoke
tests do wrapper não fazem parte da série. Um timeout sem resposta também não foi
contado como chamada válida.

## Chamadas

| # | Dados de entrada | Prompt/papel | Contrato de saída | Resultado resumido | Avaliação e hipótese seguinte |
|---:|---|---|---|---|---|
| 1 | Cena e histórico mínimo, sem perfis | Gerador direto de próximo acontecimento | `{hint, motivo}` | Murmúrios na plateia, mas Maelis volta a desconfiar e interrogar | Parcial. A situação pública basta para sugerir murmúrio, mas falta relação e saturação |
| 2 | Quatro perfis contrastantes + participação | Simulação dos próximos cinco segundos | Ranking de pressão + hint | Identificou Riven=riso e Liora=desprezo; hint afirmou incorretamente que já dominaram | Ranking melhor que síntese livre |
| 3 | Mesmo input | Calculador; evento só com pressão >=70 | Scores + evento composto | Riven e Liora iniciam zombaria, outros seguem, Asword se opõe; escalou para vaias | Muito próximo, intensidade excessiva |
| 4 | Mesmo input | Escala explícita 1–5 e custo de formalidade | Scores + evento + hint | Riven/Liora em voz alta, murmúrios, Asword; inventou reação da diretora e tratou Nix como hostil | Prosa de personalidade ambígua |
| 5 | Ledger relacional estruturado | Propagação social: hostil, alinhado, protetor, pragmático | Seed + followers + counter + hint | Riven inicia; Liora e nobres propagam; Asword contrapõe | Correto e próximo ao hint humano |
| 6 | Idêntico ao #5 | Repetição de estabilidade | Mesmo | Mesmo encadeamento, com variação superficial | Correto |
| 7 | Idêntico ao #5 | Repetição de estabilidade | Mesmo | Retornou `seed=null`, alegando faltar iniciador designado | Falha conservadora; estabilidade 2/3 |
| 8 | Ledger; temperatura 0.1 | Modelo deve selecionar iniciador, `null` só sem gatilho | Mesmo | Riven → risos nobres/Liora → desconforto de Asword | Correto |
| 9 | Idêntico ao #8 | Repetição | Mesmo | Mesmo encadeamento | Correto |
| 10 | Idêntico ao #8 | Repetição | Mesmo | Mesmo encadeamento | Correto; 3/3 |
| 11 | Perfis canônicos em prosa no lugar do ledger | Mesmo mecanismo social | Mesmo | Nix foi alinhada ao bullying porque “usa piadas”; Asword duplicado | Prosa bruta não é segura sem classificação anterior |
| 12 | Perfis canônicos em prosa | Ordem estrita: classificar relação, depois simular | Relations + seed/followers/counter + hint | Classificou Riven/Liora hostis, Nix neutra, Asword protetor; evento correto | Uma chamada pode construir ledger efêmero |
| 13 | Idêntico ao #12 | Repetição | Mesmo | Nix `pragmatic_positive`; evento correto | Correto |
| 14 | Idêntico ao #12 | Repetição | Mesmo | Nix neutra; evento correto | Correto; 3/3 |
| 15 | Controle: conversa privada só Link/Maelis | Classificação em etapas | Mesmo | Maelis pragmática; `hint=null` | Controle negativo passou |
| 16 | Controle: cena pública, apenas aliados/neutros | Classificação em etapas | Mesmo | Todos protetores/neutros; `hint=null` | Plateia e constrangimento sozinhos não forçam bullying |
| 17 | Transferência: artesã derruba vinho; rival, guardiã de status e amiga | Classificação em etapas | Mesmo | Rival inicia riso, guardiã/plateia seguem, amiga contrapõe | Generalizou, mas classificou guardiã de status como protetora |
| 18 | Mesmo controle transferido | Taxonomia inclui `status_aligned` | Mesmo | Corrigiu guardiã; rival → plateia → amiga | Categoria de alinhamento social é necessária |
| 19 | Cena real completa resumida | “Leilão” de lentes física/social/institucional/agenda | Candidatos pontuados + vencedor | Gerou tosse para Link, adiamento absurdo e sarcasmo válido; errou aritmética e truncou | Uma chamada criativa + árbitro interno é instável |
| 20 | Candidatos ruins e bons do #19 | Juiz conservador | Vereditos + winner + hint | Rejeitou tosse, adiamento e expulsão; escolheu sarcasmo de Riven | Separar geração e julgamento funciona |
| 21 | Cena real | Gerador puro por cinco lentes, sem escolher | Lista de candidatos com suporte | Gerou sensação imposta a Link, Riven, Maelis, Liora e nobre | Diversidade útil, ainda com candidatos inválidos |
| 22 | Saída exata do #21 | Juiz conservador | Vereditos + winner + hint | Rejeitou ação/sensação de Link; escolheu Riven | Pipeline completo chegou ao hint social |
| 23 | Transferência institucional: seleção parada | Gerador por lentes permissivo | Lista de candidatos | Inventou tablet, luz, ritual e fatos de suporte; não iniciou anúncio | Gerador precisa suporte quase literal e estado pendente explícito |
| 24 | Mesmo controle institucional | Gerador estrito; lente de agenda procura estado pendente | Cada lente retorna candidato ou `null` | Física/social/ambiente `null`; dever e agenda iniciam anúncio | Correto, sem invenções |
| 25 | Candidatos do #24 | Juiz de menor transição | Vereditos + winner + hint | “Inicie o anúncio das equipes e ranks em cena, sem definir escolhas do protagonista” | Transferência institucional passou |

### Ocorrências operacionais fora da contagem

| Ocorrência | Resultado |
|---|---|
| Controle privado #15, primeira tentativa | Timeout HTTP após 45 s, sem resposta; repetido sem alterar variante |
| Smoke inicial do wrapper | HTTP 400 porque DeepSeek exige a palavra “JSON” quando `json_object` é usado |
| Wrapper inicial | Substituição não recursiva deixou `$DEEPSEEK_MODEL` no body; corrigido em `/tmp` |

## Achados

### Dados que realmente mudaram o resultado

1. **Estímulo público recente**, sem prosa longa: quem fez o quê, diante de quem
   e qual consequência ainda não apareceu.
2. **Participação recente por personagem**: Maelis havia falado três vezes e os
   rivais zero. Isso reduz repetição e revela pressão acumulada.
3. **Perfis/relações dos presentes relevantes**: hostilidade, proteção, humor
   pragmático e alinhamento de status.
4. **Estado explicitamente pendente**: “equipes e ranks ainda não anunciados”.
   Sem essa forma declarativa, a lente de agenda inventou espera e ritual.
5. **Restrições de agência e canon**: não estender ação, fala, pensamento ou
   sensação do autor da última entrada; não inventar objetos ou suporte.

O estado físico completo, todas as personalidades e a história longa não foram
necessários para descobrir o hint-alvo. Fatos irrelevantes aumentaram a chance
de associação espúria.

### Contrato social de uma chamada

Este contrato obteve 3/3 na cena-alvo e passou dois controles negativos:

```json
{
  "relations": [
    {"actor": "id", "polarity": "hostile|status_aligned|protective|pragmatic_positive|neutral", "evidence": "..."}
  ],
  "seed": {"actor": "id", "reaction": "..."} ,
  "followers": [{"actor_or_group": "id|group", "reaction": "..."}],
  "counter": {"actor": "id", "reaction": "..."},
  "hint": "..."
}
```

Ordem que produziu estabilidade:

1. classificar relações;
2. escolher iniciador somente entre hostis;
3. propagar somente para hostis ou alinhados ao status;
4. selecionar oposição somente entre protetores/pragmáticos;
5. compor o hint apenas dos campos anteriores.

Esse contrato é eficiente, mas especializado em dinâmica social.

### Pipeline geral de duas chamadas

O desenho que transferiu tanto para a humilhação pública quanto para o avanço da
seleção foi:

```text
snapshot enxuto
    → gerador por lentes, sem poder escolher
    → juiz conservador de menor consequência
    → narrator_hint ou null
```

Lentes úteis:

- `physical_consequence`
- `social_reaction`
- `institutional_duty`
- `ongoing_agenda`
- `environmental_change`

O gerador precisa retornar `null` por lente quando não houver suporte e citar
fatos quase literalmente. O juiz rejeita:

- controle do autor da entrada final;
- suporte inventado;
- repetição do agente saturado;
- escalada desproporcional;
- atraso de agenda sem causa;
- evento que apenas dramatiza aparência sem mover a situação.

Entre candidatos válidos, o juiz escolhe a menor transição observável que libera
uma consequência preparada e ainda não expressa.

### Resultado para a cena real

Sem receber o hint humano, as variantes estáveis convergiram para:

> Riven inicia com riso ou sarcasmo contido; Liora e representantes nobres
> propagam olhares, cochichos ou risos abafados; Asword demonstra oposição sem
> tomar o controle de Link.

Isso é semanticamente equivalente ao impulso humano, porém preserva melhor a
formalidade do salão e diferencia os personagens em vez de fazer literalmente
“todos os nobres” reagirem igual.

## Conclusão

Uma LLM consegue simular `narrator_hint`, mas “pedir uma boa próxima ideia” não
é estável. O resultado depende mais da **representação do estado** e da
**separação entre geração e julgamento** do que de uma proibição adicional no
prompt do Diretor atual.

A opção de uma chamada é suficiente para um módulo social especializado. Para
um hint geral, o pipeline gerador + juiz foi mais robusto: tolera criatividade
na primeira chamada e impede que candidatos inválidos contaminem o Diretor.
