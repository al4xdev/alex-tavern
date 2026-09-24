# Leitura de propostas de estado

Seleção fixa: até as primeiras quatro chamadas aceitas com chaves recusadas em cada uma das três fontes declaradas. Não é amostra de frequência de erro. As recusas abaixo são uma inspeção da função atual sobre o estado do pedido; não comprovam, sozinhas, o estado historicamente persistido.

Julgue o conteúdo de cada proposta recusada contra os fatos e eventos apresentados: contém mudança sustentada, repetição, conflito, ou falta contexto? Avalie também se simplesmente acrescentá-la conservaria afirmações contraditórias. Ordens não são execução. Eventos novos não precisam já existir no estado anterior.

## Caso 1

{
  "source": "77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl",
  "line": 20,
  "turn": 2,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "leitura pública de reserva em andamento, interrompida por contestação nobre",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "afericao_cristal": "cristal de Holt ainda aceso em vermelho perto de Link"
  },
  "events": [
    {
      "event_kind": "audible_speech",
      "subject_id": "C17",
      "content": "A diretora ordena que a fila continue, declara que a leitura mede sem julgar e não autoriza exclusão alguma, e manda Holt seguir com o próximo candidato.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C17",
      "content": "A diretora ergue a prancheta selada e a bate uma vez contra a plataforma de comando, marcando o fim da interrupção e o retorno da cerimônia à ordem.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "O cristal de aferição continua aceso em vermelho nas mãos de Holt, sem apagar, e a placa de nome de Link permanece virada para baixo sobre a mesa central.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    }
  ],
  "elapsed_events": "Holt retoma a leitura do próximo candidato, o cristal apaga o vermelho ao deixar Link, e a fila avança duas marcas enquanto Elowen ainda detém o mensageiro na porta leste.",
  "proposed_delta": {
    "selection_status": "leitura pública de reserva retomada por ordem da diretora; contestação nobre pendente",
    "cristal_de_afericao": "ainda aceso em vermelho, sem apagar",
    "plataforma_de_comando": "diretora em posto, mensageiro retido por Elowen na porta leste",
    "fileira_central": "alunos mantidos na posição, leitura deve prosseguir do próximo candidato"
  },
  "rejected_by_current_key_check_against_input": {
    "cristal_de_afericao": "ainda aceso em vermelho, sem apagar"
  }
}

## Caso 2

{
  "source": "77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl",
  "line": 30,
  "turn": 3,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "leitura pública de reserva retomada por ordem da diretora; contestação nobre pendente",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "afericao_cristal": "cristal de Holt ainda aceso em vermelho perto de Link",
    "plataforma_de_comando": "diretora em posto, mensageiro retido por Elowen na porta leste",
    "fileira_central": "alunos mantidos na posição, leitura deve prosseguir do próximo candidato"
  },
  "events": [
    {
      "event_kind": "audible_speech",
      "subject_id": "C19",
      "content": "Lorde Aurel exige, em voz alta, que a Diretora leia em voz alta, número por número, o registro público de quantos candidatos de reserva mínima passaram na leitura e com que resultado",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "A Diretora Maelis gira o corpo sobre o quadril rígido e encara a galeria oeste com a prancheta selada ainda apoiada na plataforma",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Um estalo fino percorre o selo de mana do arco sul atrás dos estandartes, e uma fratura fina aparece na pedra entre as runas, seguida por um sopro de ar frio vindo de baixo",
      "witness_ids": [
        "C1",
        "C6",
        "C16",
        "C8",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C18",
      "content": "O Instrutor Holt estende o cristal de aferição de volta para a mesa, mas mantém o cotovelo firme diante da marca de espera de Link, sinalizando que nenhuma mão toca a placa virada e que a leitura continua da próxima marca",
      "witness_ids": [
        "C1",
        "C2",
        "C11",
        "C13",
        "C17"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "afericao_cristal": "cristal de aferição guardado contra o peito de Holt, apagado e tremendo uma última vez na luva sem dedos",
    "selo_sul": "fratura fina visível na pedra entre as runas do arco sul, com sopro de ar frio escapando de baixo",
    "banco_marmore_rachado": "rachadura antiga no banco de mármore da extremidade inferior se alarga um fio sob o peso de Doran",
    "fila_status": "leitura retomada, próxima marca aguarda, placa de Link intocada",
    "coroa_exigencia": "registro público exigido por Lorde Aurel, pendente de resposta da Diretora"
  },
  "rejected_by_current_key_check_against_input": {
    "fila_status": "leitura retomada, próxima marca aguarda, placa de Link intocada"
  }
}

## Caso 3

{
  "source": "77-p3-input-dispatch/live/sessions/fb62cc2f/debug.jsonl",
  "line": 88,
  "turn": 7,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "leitura de reserva encerrada por ordem da Diretora; seleção declarada por sobrevivência imediata",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "afericao_cristal": "cristal de aferição abandonado sobre a mesa central, ainda marcado na luva sem dedos de Holt",
    "plataforma_de_comando": "diretora em posto, mensageiro retido por Elowen na porta leste",
    "fileira_central": "alunos deixam as marcas de espera e se movem para o depósito de equipamento e para a porta leste",
    "selo_sul": "clarão verde irrompeu do selo sul; fratura na pedra se alastrou e rachaduras finas percorrem o mármore do salão",
    "banco_marmore_rachado": "fratura antiga no banco de mármore continua visível sob a poeira levantada pela movimentação",
    "coroa_exigencia": "pedido de registro público arquivado de facto pela emergência",
    "porta_leste": "aberta de par em par, ligando o salão ao pátio interno",
    "patio_interno": "rugido de criatura grande responde pela porta leste e faz o baú do depósito vibrar",
    "feridos_no_portao_leste": "um mensageiro ferido, com perna ensanguentada e fragmento de garrilha, chegou à plataforma de comando",
    "bau_de_equipamento": "tampo destrancado e aberto por Marta Ferrolume no depósito atrás da porta leste",
    "leitura_de_cristal": "oficialmente encerrada por ordem da diretora; o cristal de aferição segue pousado na mesa central",
    "evacuacao": "ordem vigente de Garran Holt para que todos cruzem a porta leste rumo ao pátio",
    "deposito_de_equipamento": "baú destrancado por Marta Ferrolume com peças leves expostas na prateleira superior; candidatos começam a se agachar junto às ferramentas",
    "mensageiro_ferido": "chegou à plataforma de comando arrastando a perna ensanguentada e com fragmento de garrilha no peito",
    "soleira_leste": "Ysara Lua-Parda ocupa a soleira farejando o pátio"
  },
  "events": [
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "A porta leste cede de dentro para fora, a madeira racha e a barra de ferro entorta; um rastejante de carapaça com o selo sul fundido na casca irrompe pelo corredor e para entre a soleira e o baú aberto, escolhendo como primeiro alvo o baú onde Doran e Bruna estão de joelhos.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "O rastejante é do tamanho de um cão grande, com placas de garrilha sobrepostas e o selo sul fundido a brasa na carapaça; o rugido que vinha do pátio agora tem resposta dentro do salão.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "A criatura avança na direção do baú aberto e a prateleira superior de placas leves tomba, espalhando peças de metal pelo piso irregular do depósito.",
      "witness_ids": [
        "C1",
        "C2",
        "C6",
        "C8",
        "C11",
        "C14",
        "C16",
        "C20",
        "C18"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "porta_leste": "arrombada de dentro para fora: madeira rachada, barra de ferro entortada e vão bloqueado pela criatura",
    "criatura_rastejante": "cão grande de carapaça de garrilha com o selo sul fundido na casca, parado entre a soleira e o baú aberto",
    "bau_de_equipamento": "aberto e atingido; placas leves espalhadas pelo piso do depósito",
    "selecao_status": "sobrevivência imediata, equipes definidas pela primeira ação contra a criatura",
    "soleira_leste": "invadida pelo rastejante; Asword, Bram, Ysara e Téo entre a criatura e o pátio"
  },
  "rejected_by_current_key_check_against_input": {
    "selecao_status": "sobrevivência imediata, equipes definidas pela primeira ação contra a criatura"
  }
}

## Caso 4

{
  "source": "repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl",
  "line": 45,
  "turn": 4,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "suspensa",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "cassian_blood_stain": "presente na manga esquerda do manto de Lorde Cassian",
    "royal_scroll": "papiro selado visível na mão de Lorde Cassian",
    "cassian_entrance": "confirmada",
    "royal_scroll_presence": "confirmada",
    "dungeon_violation": "confirmada",
    "directora_mobile": "true"
  },
  "events": [
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "O sino de alarme toca duas vezes e a porta principal se abre com violência, revelando um mensageiro coberto de sangue.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "O mensageiro ensanguentado cambaleia alguns passos e cai de joelhos no chão, ofegante.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C17",
      "content": "A diretora Maelis anuncia que a seleção está suspensa e que todos devem se dirigir imediatamente à sala de guerra para receberem ordens.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C19",
      "content": "Lorde Cassian apoia a ordem da diretora e ressalta que a Coroa exige uma resposta coordenada e imediata, sem ações individuais.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C18",
      "content": "O instrutor Garran Holt ordena que todos se mantenham em formação e sigam-no pelo corredor lateral que leva à sala de guerra.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
    "time_of_day": "manhã da cerimônia de seleção",
    "selection_status": "suspensa",
    "alarm_status": "ativo",
    "messenger_state": "ferido, caído de joelhos",
    "cassian_blood_stain": "presente na manga esquerda do manto de Lorde Cassian",
    "royal_scroll": "escondido no manto de Lorde Cassian"
  },
  "rejected_by_current_key_check_against_input": {
    "alarm_status": "ativo",
    "messenger_state": "ferido, caído de joelhos"
  }
}

## Caso 5

{
  "source": "repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl",
  "line": 92,
  "turn": 8,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "suspensa",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "cassian_blood_stain": "presente na manga esquerda do manto de Lorde Cassian",
    "royal_scroll": "escondido no manto de Lorde Cassian",
    "cassian_entrance": "confirmada",
    "royal_scroll_presence": "confirmada",
    "dungeon_violation": "confirmada",
    "directora_mobile": "true",
    "corridor_blocked": "parcialmente obstruído, vão estreito aberto, novo deslizamento",
    "student_injured": "Cael Vesper, ferido no ombro, sendo atendido por Irmã Elowen",
    "dungeon_barrier": "rompida em novo ponto",
    "structural_integrity": "comprometida",
    "comm_system": "instável"
  },
  "events": [
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Um combustível de cheiro acre começa a escorrer por baixo de uma das portas de aço das alas superiores, formando poças que refletem a luz das lâmpadas.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "As runas gravadas nos batentes das portas de aço pulsam em vermelho, emitindo um zumbido baixo e intermitente.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Um odor de fumaça, ainda fraco, mistura-se ao cheiro do combustível, vindo de trás das portas trancadas.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C3",
      "content": "Mirella aponta que o cheiro de combustível e fumaça indica que alguém preparou uma armadilha deliberada, não um acidente estrutural.",
      "witness_ids": [
        "C1",
        "C2",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C7",
      "content": "Liora rebate que a prioridade é descobrir quem trancou as portas, não teorizar, e oferece sua reserva para arrombar uma delas.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C13",
      "content": "Riven exige que as portas sejam arrombadas imediatamente, acusando a diretoria de hesitação enquanto a fumaça se aproxima.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "combustible_puddle": "presente perto das portas de aço",
    "door_runes": "vermelhas, pulsando com zumbido",
    "smoke_smell": "fraco, vindo das alas superiores",
    "doors_state": "trancadas"
  },
  "rejected_by_current_key_check_against_input": {
    "doors_state": "trancadas"
  }
}

## Caso 6

{
  "source": "repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl",
  "line": 276,
  "turn": 22,
  "prior_facts": {
    "hall": "salão circular de pedra branca com arquibancadas e dezesseis marcas de espera no piso",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo",
    "dungeon_gates": "quatro arcos de pedra fechados conduzem a alas separadas da Masmorra do Primeiro Sino",
    "rank_banners": "estandartes provisórios D, C, B e A pendem acima dos quatro arcos",
    "mana_lamps": "lâmpadas fracas carregadas durante a noite iluminam o salão sem chama",
    "audience": "professores, funcionários e poucos representantes nobres observam em silêncio",
    "selection_status": "suspensa",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "cassian_blood_stain": "presente na manga esquerda do manto de Lorde Cassian",
    "royal_scroll": "escondido no manto de Lorde Cassian",
    "cassian_entrance": "confirmada",
    "royal_scroll_presence": "confirmada",
    "dungeon_violation": "confirmada",
    "directora_mobile": "true",
    "corridor_blocked": "passagem alternativa encontrada por Riven",
    "student_injured": "Cael Vesper, ferido no ombro, sendo atendido por Irmã Elowen",
    "dungeon_barrier": "rompida em novo ponto",
    "structural_integrity": "comprometida",
    "comm_system": "instável e com interferência crescente",
    "combustible_puddle": "presente, refletindo as chamas",
    "door_runes": "azul estável, mas pulsando em ritmo irregular com a [indistinct] da criatura",
    "smoke_smell": "intenso",
    "upper_door_open": "parcialmente aberta, encoberta por fumaça",
    "fire_upper_corridor": "ainda ativo",
    "ceiling_collapse": "novo desabamento, bloqueando o corredor central",
    "floor_crack": "alargada, com degraus visíveis descendo",
    "smell_sulfur": "intenso, vindo da fenda",
    "subterranean_passage": "descoberta",
    "fire_column": "presente, mas atenua",
    "fire_wall": "presente, separando o salão do corredor lateral",
    "monster_presence": "bloqueia parcialmente a porta superior, empurrando todos para a fenda",
    "smoke_dispersed": "parcialmente dispersa na área central",
    "lateral_passage": "revelado na fenda do piso, descendo para escadaria",
    "blockade_at_fissure": "improvisado por Bruna",
    "criatura_posicao": "descendo em direção ao grupo",
    "fenda_estado": "alargada, com degraus visíveis",
    "corredor_superior": "bloqueado pela criatura",
    "formacao": "descendo pela fenda"
  },
  "events": [
    {
      "event_kind": "physical_outcome",
      "subject_id": "C17",
      "content": "A diretora Maelis Ordan ordena descida imediata pela fenda, com Asword na retaguarda para conter a criatura enquanto o grupo desce.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C8",
      "content": "Bruna Ferrugem termina de montar o bloqueio improvisado na boca da fenda, empilhando pedras e um suporte de metal retorcido, criando uma barreira parcial que retarda a criatura.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C2",
      "content": "Asword planta os pés entre a criatura e a fenda, espada desembainhada, pronto para segurar a linha enquanto os outros descem, mas a criatura avança um passo, suas garras raspando a pedra.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "A criatura estala as mandíbulas, e um líquido escuro escorre de suas presas, queimando o piso onde cai, enquanto ela desvia o olhar de Asword para o bloqueio improvisado de Bruna.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Da escadaria descendente, os alunos sentem o ar ficar mais úmido e o som de água corrente crescer, enquanto a luz das tochas revela um corredor de pedra que se aprofunda.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C17",
      "content": "A diretora Maelis projeta a voz para o corredor lateral, chamando por Garran, mas só o eco das chamas responde.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
    "time_of_day": "manhã da cerimônia de seleção",
    "monster_proximity": "a criatura está a cerca de 8 metros da fenda, avançando lentamente",
    "blockade_at_fissure": "reforçado por Bruna, improvisado mas funcional",
    "descent_order": "grupo descendo pela fenda em fila, Asword na retaguarda",
    "upper_corridor_fire": "ainda ativo, mas parcialmente obstruído pela criatura",
    "subterranean_corridor": "confirma-se como corredor de pedra úmida, com tochas e som de água corrente"
  },
  "rejected_by_current_key_check_against_input": {
    "upper_corridor_fire": "ainda ativo, mas parcialmente obstruído pela criatura"
  }
}

## Caso 7

{
  "source": "repetition-battery/base-P3-r2/sessions/d5a2ccf0/debug.jsonl",
  "line": 398,
  "turn": 32,
  "prior_facts": {
    "floor_hole_in_stairs": "ampliado, revelando corredor oculto com criaturas se aproximando",
    "hidden_corridor": "revelado sob a escadaria, com som de criaturas",
    "clock_exploded": "true",
    "herald_present": "true",
    "criatura_posicao": "ainda no salão, a 8 metros da fenda",
    "retreat_tunnel_sealed": "true",
    "smoke_rising": "true",
    "projectile_hit": "true",
    "scream_from_east_chamber": "true"
  },
  "events": [
    {
      "event_kind": "observation",
      "subject_id": "C13",
      "content": "Riven Draven encontra uma passagem oculta atrás de uma coluna e adentra na escuridão, isolando-se do grupo.",
      "witness_ids": [
        "C2",
        "C8"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C18",
      "content": "Garran Holt grita pelo corredor chamando Riven, sem obter resposta.",
      "witness_ids": [
        "C13"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "Um projétil mágico sibila pelo ar e se estilhaça contra a parede atrás de Link, arrancando lascas de pedra.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21",
        "C2",
        "C8"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Um grito agudo ecoa da câmara leste, perfurando o ar com uma nota estridente.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21",
        "C2",
        "C8"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C19",
      "content": "O arauto de Lorde Cassian aponta para a fumaça negra que sobe das escadarias, gritando que algo se aproxima.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21",
        "C2",
        "C8"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C17",
      "content": "A diretora ordena que Asword verifique a câmara leste sem se dispersar, autoriza Mirella a selar a passagem próxima e manda todos permanecerem junto à parede sólida.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C9",
        "C10",
        "C11",
        "C12",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C21",
        "C2",
        "C8"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "projectile_hit_wall": true,
    "scream_from_east_chamber": true,
    "smoke_from_stairs": true
  },
  "rejected_by_current_key_check_against_input": {
    "projectile_hit_wall": true
  }
}

## Caso 8

{
  "source": "repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl",
  "line": 113,
  "turn": 11,
  "prior_facts": {
    "hall": "salão circular de pedra branca com marcas de espera parcialmente corroídas e novas rachaduras no arco sul",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo, uma delas deslizando para a borda",
    "dungeon_gates": "quatro arcos de pedra, o primeiro arco rachado e o arco sul rompido com vazamento de névoa",
    "rank_banners": "estandartes provisórios balançando com o fluxo de ar da névoa",
    "mana_lamps": "lâmpadas tremulando, duas delas apagadas",
    "audience": "professores e nobres agitados, alguns de pé",
    "selection_status": "adiada, diretora pede relatório de danos e nova contenção",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "névoa_verde": "recuada do centro, formando corredor ao redor do corpo, ainda ativa no arco sul e começando a surgir [indistinct] da plataforma de avaliação",
    "barreira_de_contenção": "rompida",
    "marck_damage": "cinco marcas de espera corroídas, duas rachadas",
    "alunos_em_pânico": "true",
    "manchas_de_corrosão": "marcas corroídas, área na arquibancada norte borbulhando e novas manchas próximas ao arco sul",
    "fresta_leste": "selada temporariamente por Garran, mas novas frestas surgem",
    "arco_sul": "rachado e liberando névoa",
    "marcas_danificadas": "seis marcas corroídas, três rachadas",
    "corpo_caído": "presente, parcialmente consumido, com distintivo de aluno da classe inferior",
    "sangue_verde": "poças ao redor do corpo, evaporando lentamente, agora com aparência ácida",
    "corredor_leste": "parcialmente desabado",
    "evacuação_em_andamento": "true",
    "fragmento_do_selo_antigo": "placa metálica rachada encontrada sob escombros no corredor leste"
  },
  "events": [
    {
      "event_kind": "physical_outcome",
      "subject_id": "C21",
      "content": "Irmã Elowen pressiona a placa rachada contra a fresta na passagem, e um brilho verde intenso pulsa, selando parte da abertura por um instante, antes de se apagar.",
      "witness_ids": [
        "C2",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "scene_change",
      "subject_id": "Narrator",
      "content": "No salão, a névoa verde se expande em direção à fila de evacuação, a poucos metros dos primeiros alunos, e um estrondo ecoa do corredor leste.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C18",
      "content": "Garran, vendo a passagem parcialmente selada, aponta para uma fenda menor entre as pedras e começa a limpar os detritos, abrindo espaço para uma passagem estreita.",
      "witness_ids": [
        "C2",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C2",
      "content": "Asword observa a placa escurecida e as frestas ainda vazando névoa, e seu rosto se contorce em frustração.",
      "witness_ids": [
        "C2",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C17",
      "content": "A diretora Maelis, vendo a névoa se aproximar, golpeia o chão com a bengala e ordena que a fila avance pelos escombros imediatamente.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "passagem_corredor_leste": "parcialmente desobstruída, com espaço para passagem de uma pessoa por vez",
    "névoa_verde": "avançando em direção à fila de evacuação",
    "selo_improvisado": "placa rachada pressionada contra a fresta, brilho esmeralda se apagando"
  },
  "rejected_by_current_key_check_against_input": {
    "passagem_corredor_leste": "parcialmente desobstruída, com espaço para passagem de uma pessoa por vez"
  }
}

## Caso 9

{
  "source": "repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl",
  "line": 174,
  "turn": 16,
  "prior_facts": {
    "hall": "salão circular de pedra branca com marcas de espera parcialmente corroídas, rachaduras no arco sul e novas rachaduras circulares no piso perto da passagem secreta",
    "selection_table": "mesa central com dezesseis placas de nome viradas para baixo, uma delas deslizando para a borda",
    "dungeon_gates": "quatro arcos de pedra, o primeiro arco rachado e o arco sul rompido com vazamento de névoa",
    "rank_banners": "estandartes provisórios balançando com o fluxo de ar da névoa",
    "mana_lamps": "quatro apagadas, penumbra parcial",
    "audience": "professores e nobres agitados, alguns de pé, outros recuando para o norte",
    "selection_status": "adiada, diretora pede relatório de danos e nova contenção",
    "bruma_status": "Bruma está escondida no antigo canil e não está presente no salão",
    "névoa_verde": "avançando em direção à fila de evacuação e contornando a passagem secreta",
    "barreira_de_contenção": "rompida",
    "marck_damage": "cinco marcas de espera corroídas, duas rachadas",
    "alunos_em_pânico": "true",
    "manchas_de_corrosão": "marcas corroídas, área na arquibancada norte borbulhando e novas manchas próximas ao arco sul e à passagem secreta",
    "fresta_leste": "selada temporariamente por Garran, mas novas frestas surgem, e uma língua de névoa escapa pela placa rachada",
    "arco_sul": "rachado e liberando névoa",
    "marcas_danificadas": "seis marcas corroídas, três rachadas",
    "corpo_caído": "presente, parcialmente consumido, com distintivo de aluno da classe inferior",
    "sangue_verde": "poças ao redor do corpo, evaporando lentamente, agora com aparência ácida",
    "corredor_leste": "parcialmente desabado, com fenda estreita aberta",
    "evacuação_em_andamento": "true",
    "fragmento_do_selo_antigo": "placa metálica rachada encontrada sob escombros no corredor leste, emitindo faíscas verdes",
    "selo_improvisado": "placa rachada pressionada contra a fresta, brilho esmeralda se apagando, mas uma língua de névoa escapa por ela",
    "explosion": "parede oeste rompida, fragmento em chamas no chão, agora frio e fumegante",
    "secret_passage": "aberta e iluminada com luz âmbar, brilho mais forte e pulsante, chão rachando em padrão circular perto da entrada",
    "saida_principal": "bloqueada por entulho da arquibancada norte",
    "alarme_de_emergencia": "soando",
    "teco_rachado": "fissura visível acima da arquibancada norte"
  },
  "events": [
    {
      "event_kind": "scene_change",
      "subject_id": "Narrator",
      "content": "Novas rachaduras se espalham ao redor da passagem secreta, e a luz âmbar pulsa em ondas mais rápidas.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C8",
      "content": "Bruna aponta para uma pequena fenda no piso perto da moldura, de onde emana um brilho verde fraco.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C7",
      "content": "Liora, ainda agachada, diz em tom tenso: 'Há algo ativo sob a passagem, e não é o selo antigo.'",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20",
        "C2",
        "C18",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C13",
      "content": "Riven, que havia avançado, para abruptamente ao sentir o piso tremer sob os pés, e recua um passo, com a mão na espada.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C17",
      "content": "A diretora Maelis observa a cena com a bengala firme e, com um gesto seco, ordena que todos se afastem dois passos da entrada.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "C19",
      "content": "Cassian, de longe, com o monóculo erguido, murmura para ninguém em específico: 'Mais uma peça fora do lugar. Bom saber.'",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C20"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "passagem_secreta": "luz âmbar pulsando mais forte, chão rachando em círculo, nova fenda com brilho verde perto da moldura",
    "alarme_de_emergencia": "soando",
    "marcas_danificadas": "seis marcas corroídas, três rachadas",
    "névoa_verde": "vazando por baixo da saída principal bloqueada, avançando em direção à passagem"
  },
  "rejected_by_current_key_check_against_input": {
    "passagem_secreta": "luz âmbar pulsando mais forte, chão rachando em círculo, nova fenda com brilho verde perto da moldura"
  }
}

## Caso 10

{
  "source": "repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl",
  "line": 242,
  "turn": 21,
  "prior_facts": {
    "hall": "salão circular de pedra branca com múltiplas rachaduras no piso, filetes de névoa verde emergindo de várias frestas, marcas de espera corroídas",
    "selection_table": "mesa central com dezesseis placas de nome ainda viradas para baixo, uma delas caída no chão",
    "dungeon_gates": "primeiro arco rachado, arco sul rompido, estandartes balançando com o fluxo da névoa",
    "rank_banners": "estandartes provisórios com manchas de corrosão na base",
    "mana_lamps": "quatro apagadas, penumbra parcial",
    "audience": "professores e nobres comprimidos no norte, alguns já se movendo para a passagem",
    "selection_status": "adiada, evacuação em andamento",
    "bruma_status": "Bruma escondida no antigo canil, não presente no salão",
    "névoa_verde": "avançando no salão a partir da passagem bloqueada e do corredor leste",
    "barreira_de_contenção": "rompida",
    "marck_damage": "sete marcas corroídas, três rachadas",
    "alunos_em_pânico": "false",
    "manchas_de_corrosão": "novas manchas borbulhantes perto da passagem secreta e da arquibancada norte",
    "fresta_leste": "selada temporariamente por Garran, mas uma língua de névoa escapa pela placa rachada",
    "arco_sul": "rachado e liberando névoa",
    "marcas_danificadas": "sete marcas corroídas, três rachadas",
    "corpo_caído": "removido por Elowen, não mais presente",
    "sangue_verde": "poças ácidas evaporando, ainda presentes",
    "corredor_leste": "parcialmente desabado, fenda estreita ainda aberta",
    "evacuação_em_andamento": "true",
    "fragmento_do_selo_antigo": "placa metálica rachada observada por Garran e Elowen, faíscas verdes continuam",
    "selo_improvisado": "placa rachada pressionada contra a fresta, brilho esmeralda quase extinto, língua de névoa escapa",
    "explosion": "parede oeste rompida, fragmento em chamas frio e fumegante",
    "secret_passage": "entrada bloqueada por escombros, luz âmbar apagada",
    "saida_principal": "bloqueada por entulho",
    "alarme_de_emergencia": "soando",
    "teco_rachado": "fissura visível acima da arquibancada norte",
    "rachadura_teto_norte": "nova fissura visível acima da arquibancada norte",
    "luz_âmbar": "apagada",
    "nova_fenda_corredor": "brilho verde pulsante no corredor interno",
    "corredor_interno": "desmoronado, acesso bloqueado",
    "teto_norte": "novas fissuras e uma laje caída sobre bancos"
  },
  "events": [
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "A parede acima da passagem se rompe com um estrondo, e uma língua de névoa esmeralda irrompe do corredor interno, varrendo o salão.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "O brilho verde que pulsava na fenda do corredor interno se apaga, e o chão estremece com um som grave, enquanto fumaça invade o corredor.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "Uma forte onda de névoa verde avança pelo salão, forçando todos a recuarem em direção às arquibancadas norte.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "O teto da passagem desaba atrás de Riven, bloqueando qualquer retorno ao corredor interno.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
    "time_of_day": "manhã",
    "secret_passage": "entrada bloqueada por desabamento completo, luz âmbar apagada, corredor interno inacessível",
    "nova_fenda_corredor": "brilho verde apagado",
    "nível_de_ameaça": "crítico",
    "passagem_secreta": "desmoronada"
  },
  "rejected_by_current_key_check_against_input": {
    "passagem_secreta": "desmoronada"
  }
}

## Caso 11

{
  "source": "repetition-battery/base-P1-r2/sessions/8bd4d0f1/debug.jsonl",
  "line": 430,
  "turn": 37,
  "prior_facts": {
    "névoa_verde": "jato através do buraco no teto da câmara, atingindo o pátio; línguas rasteiras alcançam a arquibancada norte",
    "barreira_de_contenção": "rompida",
    "marck_damage": "sete marcas corroídas, três rachadas",
    "alunos_em_pânico": "false",
    "manchas_de_corrosão": "novas manchas borbulhantes perto da passagem secreta e da arquibancada norte",
    "fresta_leste": "selada temporariamente por Garran, mas uma língua de névoa escapa pela placa rachada",
    "arco_sul": "rachado e liberando névoa",
    "marcas_danificadas": "sete marcas corroídas, três rachadas",
    "corpo_caído": "removido por Elowen, não mais presente",
    "sangue_verde": "poças ácidas evaporando, ainda presentes",
    "corredor_leste": "parcialmente desabado, fenda estreita ainda aberta",
    "evacuação_em_andamento": "true",
    "fragmento_do_selo_antigo": "placa metálica rachada observada por Garran e Elowen, faíscas verdes continuam",
    "selo_improvisado": "placa rachada pressionada contra a fresta, brilho esmeralda quase extinto, língua de névoa escapa",
    "explosion": "parede oeste rompida, fragmento em chamas frio e fumegante",
    "secret_passage": "totalmente bloqueada por desabamento, acesso impossível",
    "saida_principal": "bloqueada por entulho",
    "alarme_de_emergencia": "soando",
    "teco_rachado": "fissura visível acima da arquibancada norte",
    "rachadura_teto_norte": "nova fissura visível acima da arquibancada norte",
    "luz_âmbar": "apagada",
    "nova_fenda_corredor": "brilho verde apagado",
    "corredor_interno": "totalmente bloqueado, fresta estreita revela movimento",
    "teto_norte": "novas fissuras, uma seção desabou aumentando os escombros",
    "nível_de_ameaça": "crítico, colapso estrutural iminente",
    "fresta_visivel": "fresta entre pedras mostra movimento no corredor bloqueado, agora quase fechada",
    "dissolved_selo": "o selo subterrâneo se rompeu completamente",
    "fresta_entre_escombros": "reduzida a menos de um palmo, chamados de Liora quase inaudíveis",
    "gritos_abafados": "ainda audíveis, mais fracos",
    "escombros_instáveis": "true",
    "braçadeira_direita_de_Bruna": "chamuscada, faíscas verdes, ponta queimada, moldura do duto testada",
    "pilar_rachado": "desabado, bloqueando a visão do corredor interno, mas criando barreira temporária contra a névoa",
    "duto_de_ventilação": "exposto, borda testada com faísca; névoa [indistinct] pelo duto",
    "câmara_oculta": "teto desabado, entrada soterrada",
    "entrada_câmara": "soterrada por blocos, acesso impossível",
    "chamados_de_Liora": "cessaram após o grito",
    "jato_de_névoa": "visível pelo buraco, atravessando em direção ao pátio",
    "viga_do_teto": "desabada na área central, revelando um duto de onde jorra névoa",
    "novo_duto": "aberto pela [indistinct] da viga, jato de névoa esmeralda ativo",
    "feridos": "vários alunos atingidos pela névoa, precisando de remoção imediata"
  },
  "events": [
    {
      "event_kind": "physical_outcome",
      "subject_id": "Narrator",
      "content": "Uma viga do teto se solta e desaba com estrondo, abrindo um duto na parede e lançando um jato de névoa esmeralda que atinge vários alunos próximos.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "physical_outcome",
      "subject_id": "C7",
      "content": "Liora Celestria solta um grito breve antes de desabar sob os escombros, e seus chamados cessam por completo.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C17",
      "content": "Diretora Maelis ordena que todos recuem imediatamente para o pátio e que os feridos sejam removidos, em voz alta e cortante.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C3",
      "content": "Mirella, à borda do duto, anuncia que vai descer agora para selar a fonte com gelo, mesmo sem autorização, afirmando que não pode esperar mais.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "audible_speech",
      "subject_id": "C8",
      "content": "Bruna grita para Mirella não descer, avisando que a escada está viva e que a carga pode disparar, enquanto tenta aterrar a braçadeira na moldura.",
      "witness_ids": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C20",
        "C21"
      ]
    },
    {
      "event_kind": "observation",
      "subject_id": "Narrator",
      "content": "Vários alunos são atingidos pela névoa em seu avanço, exibindo marcas borbulhantes nos uniformes e recuando aos tropeços em direção à arquibancada norte.",
      "witness_ids": [
        "C1",
        "C3",
        "C4",
        "C5",
        "C6",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C19",
        "C20"
      ]
    }
  ],
  "elapsed_events": "",
  "proposed_delta": {
    "location": "Academia Real do Primeiro Sino, Salão dos Quatro Arcos",
    "time_of_day": "manhã",
    "duto_novo": "aberto na parede oeste, jato de névoa ativo",
    "feridos": "vários alunos atingidos, precisando de remoção",
    "chamados_de_Liora": "cessados",
    "viga_do_teto": "desabada na área central"
  },
  "rejected_by_current_key_check_against_input": {
    "duto_novo": "aberto na parede oeste, jato de névoa ativo"
  }
}
