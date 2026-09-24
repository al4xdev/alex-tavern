# Parecer de conteúdo das propostas recusadas

Fonte única lida: `plans/artifacts/69-fact-intake-read/reader.md`. Não consultei código, arquivos vinculados nem logs originais. Avalio as afirmações recusadas diante dos fatos anteriores, dos eventos e das demais propostas exibidas; não avalio a justificativa da recusa. A seleção não permite estimar frequência ou taxa de qualidade. As perdas abaixo dizem respeito ao conteúdo da proposta de estado, não à eliminação dos eventos nem à comprovação do que foi historicamente persistido.

## Caso 1 — `cristal_de_afericao`

“Ainda aceso em vermelho, sem apagar” repete `afericao_cristal` e coincide com a observação do Narrador. Entretanto, `elapsed_events` diz expressamente que “o cristal apaga o vermelho ao deixar Link”. Há incompatibilidade temporal dentro do material apresentado: sem uma cronologia inequívoca entre esses blocos, não determino qual representa o último instante; se o estado deve incluir esse avanço, manter “ainda aceso” está desatualizado.

Descartar a proposta não perde uma informação exclusiva: o vermelho já consta do estado anterior. Tampouco corrige a possível desatualização desse estado. Simplesmente acrescentá-la duplica o cristal aceso e conserva a contradição com o apagamento relatado. A proposta não contém esse apagamento.

## Caso 2 — `fila_status`

“Leitura retomada” já consta de `selection_status`; a continuação a partir do próximo candidato já consta de `fileira_central`. O gesto de Holt sustenta que a próxima marca é a referência para prosseguir e que a placa de Link permanece intocada. O material não mostra uma nova leitura efetivamente realizada neste instante; o estado anterior, porém, já registra a retomada.

Descartar perde a explicitação de que a placa de Link não foi tocada, detalhe que “placas viradas para baixo” não substitui integralmente. Simplesmente acrescentar repete a situação da leitura e da fila, mas não cria contradição direta com os fatos fornecidos. A formulação “próxima marca aguarda” é compatível com o gesto; não prova atendimento do próximo candidato.

## Caso 3 — `selecao_status`

“Sobrevivência imediata” repete `selection_status`. Já “equipes definidas pela primeira ação contra a criatura” não aparece nos eventos: eles mostram a invasão e o ataque ao baú, sem definição de equipes ou declaração desse critério.

Descartar não perde uma mudança sustentada exclusiva; perde somente esse critério adicional cuja origem falta no recorte. Simplesmente acrescentar duplica o regime de sobrevivência e registra como vigente uma regra de equipes não demonstrada. Não há contradição explícita com o estado anterior, mas ausência de contradição não fornece a sustentação que falta.

## Caso 4 — `alarm_status` e `messenger_state`

**`alarm_status: ativo`.** O sino de alarme tocar duas vezes sustenta a ocorrência de um alarme. Não demonstra que continua soando após os dois toques nem esclarece se “ativo” significa som contínuo ou emergência declarada. Descarta-se uma ocorrência nova ao remover esse conteúdo do estado proposto. Acrescentá-lo não duplica um fato anterior nem cria contradição visível, mas uma leitura de atividade sonora contínua ultrapassaria o evento.

**`messenger_state: ferido, caído de joelhos`.** O mensageiro entra coberto de sangue, cambaleia e cai de joelhos ofegante. A posição e a debilidade são diretamente sustentadas. “Ferido” é uma inferência plausível; sangue e cambaleio não identificam por si uma lesão. A mancha na manga de Cassian concerne a outra pessoa e não substitui a condição desse mensageiro.

Descartar perde a presença e a condição atual do mensageiro no estado proposto. Acrescentar não duplica os fatos sobre Cassian e não contradiz os fatos apresentados, com a ressalva sobre a inferência de ferimento. As ordens de ir à sala de guerra não provam que esse deslocamento ocorreu.

## Caso 5 — `doors_state`

“Trancadas” encontra apoio direto na observação do odor que vem “de trás das portas trancadas”. As falas sobre arrombá-las são pedidos e ofertas, sem execução. `dungeon_gates` descreve quatro arcos fechados, enquanto os eventos descrevem portas de aço das alas superiores: o recorte não permite equiparar esses objetos. Além disso, estar fechado não equivale a estar trancado.

Descartar perde o impedimento explicitamente observado nas portas de aço. Simplesmente acrescentar não conserva contradição conhecida, mas o nome genérico deixa incerto a quais portas a condição se aplica. Não se deve concluir que todos os acessos ou os quatro arcos estão trancados.

## Caso 6 — `upper_corridor_fire`

“Ainda ativo” repete `fire_upper_corridor`. A criatura bloquear o corredor superior ou parcialmente sua porta também já consta de `corredor_superior` e `monster_presence`. A nova formulação combina esses conteúdos, mas “fogo parcialmente obstruído pela criatura” é ambíguo: os fatos sustentam obstrução do acesso, não que a criatura esteja contendo as chamas. Os eventos também a mostram avançando perto da fenda; não dão geometria suficiente para resolver a posição relativa a todos os acessos.

Descartar não perde uma novidade claramente demonstrada nessa proposta. Simplesmente acrescentar duplica o fogo ativo e pode confundir bloqueio do corredor com bloqueio do fogo. Não há prova suficiente para afirmar uma nova contenção do incêndio ou uma contradição espacial definitiva.

## Caso 7 — `projectile_hit_wall`

O projétil se estilhaça contra a parede atrás de Link e arranca lascas: o acerto na parede é diretamente sustentado. `projectile_hit: true` já registra algum acerto, mas não informa o alvo. Não é possível concluir pelo recorte se é o mesmo disparo anteriormente registrado ou outro.

Descartar perde a especificação do alvo no estado proposto, embora preserve a indicação genérica de acerto. Simplesmente acrescentar repete a ocorrência de impacto e a torna mais precisa, sem contradizer o estado apresentado. A proposta booleana ainda não conserva a posição atrás de Link nem as lascas arrancadas.

## Caso 8 — `passagem_corredor_leste`

Há mudança sustentada: Garran limpa detritos, “abrindo espaço para uma passagem estreita”. Isso acrescenta uma abertura utilizável em formação ao estado anterior de corredor parcialmente desabado. Contudo, o texto também diz que ele “começa” a limpar, e não fornece medida nem mostra alguém atravessando. “Espaço para passagem de uma pessoa por vez” é mais específico que a evidência disponível; permanece dúvida sobre a conclusão e a transitabilidade efetiva.

Descartar perde o avanço concreto na desobstrução. Simplesmente acrescentar pode conservar coerentemente “parcialmente desabado” e “parcialmente desobstruída”: dano e abertura estreita podem coexistir. O problema remanescente é afirmar capacidade de passagem já assegurada. A ordem de Maelis para a fila avançar não prova travessia nem conclusão da limpeza.

## Caso 9 — `passagem_secreta`

A luz âmbar pulsante e as rachaduras circulares já aparecem em `secret_passage` e `hall`. Os eventos confirmam expansão das rachaduras e pulsação mais rápida. A pequena fenda com brilho verde junto à moldura é novidade observada por Bruna, ausente nos fatos anteriores exibidos. A explicação de Liora sobre algo ativo diferente do selo antigo continua sendo uma fala, não uma confirmação da natureza dessa fonte.

Descartar perde a fenda verde no estado proposto. Simplesmente acrescentar duplica parte da descrição da passagem e preserva a novidade sem contradição direta: luz âmbar na passagem e brilho verde numa fenda podem coexistir. A proposta não afirma a explicação de Liora e, portanto, não exige tratá-la como fato.

## Caso 10 — `passagem_secreta`

“Desmoronada” é sustentado pelo teto que desaba atrás de Riven, bloqueando o retorno. O estado anterior já descreve entrada bloqueada e corredor desmoronado; além disso, a mesma proposta inclui `secret_passage` com “desabamento completo” e corredor inacessível.

Descartar apenas `passagem_secreta` não perde conteúdo exclusivo: a atualização mais informativa já está em `secret_passage` no mesmo delta. Simplesmente acrescentá-la duplica o desabamento, sem contradição visível com essa atualização ou com o bloqueio anterior. A afirmação curta não distingue o novo colapso dos anteriores.

## Caso 11 — `duto_novo`

A abertura de um duto e seu jato ativo são sustentados pelo desabamento da viga. Esses elementos já estão em `novo_duto` e `viga_do_teto` nos fatos anteriores; não há indicação suficiente para concluir se o evento relata novamente esse duto ou abre um segundo. A localização “parede oeste” não aparece no evento, que diz apenas “na parede”. A ruptura oeste mencionada em `explosion` não estabelece identidade com esse duto.

Descartar não perde uma novidade claramente sustentada exclusiva, embora remova a localização oeste não demonstrada. Simplesmente acrescentar duplica abertura e jato se for o mesmo duto, e fixa uma parede sem sustentação no recorte. Não há contradição direta comprovada, nem base para tratar a diferença de nome como evidência de dois dutos.
