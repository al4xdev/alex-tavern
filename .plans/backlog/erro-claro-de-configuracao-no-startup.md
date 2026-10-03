# Mensagem clara de configuração inválida no startup

Status: backlog. Não implementar agora.

Problema: ao iniciar com um campo obrigatório ausente em `.data/config.json`,
a aplicação apresenta um traceback de startup como mensagem principal. O erro
é de configuração; o JSON pode estar correto na sintaxe e inválido no contrato.

Objetivo: mostrar no terminal uma mensagem direta com o arquivo, o campo e a
correção esperada. Distinguir JSON malformado, campo ausente e valor inválido.

Exemplo para campo ausente:

> Configuração inválida em `.data/config.json`: falta
> `providers.llama_cpp.narrator_min_words`. Informe um inteiro positivo,
> por exemplo `150`.

Manter a recusa de inicializar com configuração inválida, sem preencher campos
automaticamente, converter formatos ou modificar o arquivo. Preservar o traceback
para diagnóstico, sem torná-lo a apresentação principal desse erro conhecido.
Não esconder falhas inesperadas do backend nem expor segredos ou o JSON completo.

Pontos a inspecionar: `src/config.py` (erros de leitura e validação),
`src/runtime_bootstrap.py`, lifespan em `src/main.py` e a apresentação do erro
pelo supervisor usado por `start.sh`. Definir um único responsável pela mensagem
para evitar duplicação entre processos.

Aceite: executar a fronteira real de startup com configuração temporária e
confirmar mensagem clara, saída de falha e ausência de segredos para JSON
malformado, campo obrigatório ausente e valor inválido. Uma falha inesperada
continua diagnosticável. Nenhum teste usa ou altera a `.data/` real.
